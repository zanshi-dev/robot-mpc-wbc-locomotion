import argparse
import csv
from pathlib import Path

import mujoco
import numpy as np
import osqp
import scipy.sparse as sp


LEG_ORDER = ["FR", "FL", "RR", "RL"]
STAND_LEG_Q = np.array([0.0, 0.9, -1.8])

PHASE_OFFSETS = {
    "FR": 0.0,
    "FL": 0.5,
    "RR": 0.5,
    "RL": 0.0,
}


def build_standing_q():
    return np.tile(STAND_LEG_Q, 4)


def gait_phase(t, gait_period, phase_offset):
    return ((t / gait_period) + phase_offset) % 1.0


def contact_schedule(t, gait_period, duty_factor):
    return [
        int(gait_phase(t, gait_period, PHASE_OFFSETS[leg]) < duty_factor)
        for leg in LEG_ORDER
    ]


def contact_mode_name(flags):
    if flags == [1, 1, 1, 1]:
        return "all_stance"
    if flags == [1, 0, 0, 1]:
        return "trot_FR_RL"
    if flags == [0, 1, 1, 0]:
        return "trot_FL_RR"
    return "custom_" + "".join(str(x) for x in flags)


def initialize_standing_pose(model, data, q_stand, desired_min_foot_z=0.02):
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0

    # MuJoCo free joint qpos: x, y, z, qw, qx, qy, qz.
    data.qpos[0:7] = np.array([0.0, 0.0, 0.35, 1.0, 0.0, 0.0, 0.0])
    data.qpos[7:19] = q_stand

    mujoco.mj_forward(model, data)

    foot_z = []
    for geom_name in LEG_ORDER:
        gid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, geom_name)
        if gid < 0:
            raise RuntimeError(f"Cannot find foot geom: {geom_name}")
        foot_z.append(data.geom_xpos[gid, 2])

    min_foot_z = float(np.min(foot_z))
    data.qpos[2] += desired_min_foot_z - min_foot_z

    mujoco.mj_forward(model, data)


def compute_total_mass_and_com(model, data):
    masses = np.asarray(model.body_mass)[1:]
    xipos = np.asarray(data.xipos)[1:]

    total_mass = float(np.sum(masses))
    com = np.sum(xipos * masses[:, None], axis=0) / total_mass
    return total_mass, com


class VariableIndex:
    def __init__(self, horizon):
        self.N = horizon
        self.n_state = 2 * (horizon + 1)
        self.n_force = 12 * horizon
        self.n_total = self.n_state + self.n_force

    def z(self, k):
        return 2 * k

    def vz(self, k):
        return 2 * k + 1

    def f(self, k, leg_index, axis):
        # axis: 0=fx, 1=fy, 2=fz
        return self.n_state + 12 * k + 3 * leg_index + axis


def build_centroidal_z_mpc_qp(
    horizon,
    dt,
    mass,
    gravity,
    z0,
    vz0,
    z_ref,
    schedules,
    wz,
    wvz,
    force_reg,
    mu,
    fz_min,
    fz_max,
):
    idx = VariableIndex(horizon)
    n = idx.n_total

    P_diag = np.zeros(n)
    q = np.zeros(n)

    # State tracking cost: sum wz*(z-z_ref)^2 + wvz*vz^2.
    # OSQP objective is 0.5*x'Px + q'x.
    for k in range(horizon + 1):
        P_diag[idx.z(k)] += 2.0 * wz
        q[idx.z(k)] += -2.0 * wz * z_ref

        P_diag[idx.vz(k)] += 2.0 * wvz
        q[idx.vz(k)] += 0.0

    # Force regularization.
    for k in range(horizon):
        for leg_i in range(4):
            for axis in range(3):
                P_diag[idx.f(k, leg_i, axis)] += 2.0 * force_reg

    P = sp.diags(P_diag, format="csc")

    rows = []
    lower = []
    upper = []

    def add_row(coeffs, lo, up):
        row = np.zeros(n)
        for j, value in coeffs:
            row[j] = value
        rows.append(row)
        lower.append(lo)
        upper.append(up)

    # Initial state equality.
    add_row([(idx.z(0), 1.0)], z0, z0)
    add_row([(idx.vz(0), 1.0)], vz0, vz0)

    # Dynamics equality.
    for k in range(horizon):
        # z_{k+1} - z_k - dt*vz_k = 0
        add_row([
            (idx.z(k + 1), 1.0),
            (idx.z(k), -1.0),
            (idx.vz(k), -dt),
        ], 0.0, 0.0)

        # vz_{k+1} - vz_k - dt/mass * sum_fz = -dt*g
        coeffs = [
            (idx.vz(k + 1), 1.0),
            (idx.vz(k), -1.0),
        ]
        for leg_i in range(4):
            coeffs.append((idx.f(k, leg_i, 2), -dt / mass))
        add_row(coeffs, -dt * gravity, -dt * gravity)

    # Contact force constraints.
    for k, flags in enumerate(schedules):
        for leg_i, active in enumerate(flags):
            fx = idx.f(k, leg_i, 0)
            fy = idx.f(k, leg_i, 1)
            fz = idx.f(k, leg_i, 2)

            if active:
                # fz bounds
                add_row([(fz, 1.0)], fz_min, fz_max)

                # friction pyramid
                # fx - mu*fz <= 0
                add_row([(fx, 1.0), (fz, -mu)], -np.inf, 0.0)
                # -fx - mu*fz <= 0
                add_row([(fx, -1.0), (fz, -mu)], -np.inf, 0.0)
                # fy - mu*fz <= 0
                add_row([(fy, 1.0), (fz, -mu)], -np.inf, 0.0)
                # -fy - mu*fz <= 0
                add_row([(fy, -1.0), (fz, -mu)], -np.inf, 0.0)
            else:
                # inactive leg force = 0
                add_row([(fx, 1.0)], 0.0, 0.0)
                add_row([(fy, 1.0)], 0.0, 0.0)
                add_row([(fz, 1.0)], 0.0, 0.0)

    A = sp.csc_matrix(np.vstack(rows))
    l = np.array(lower, dtype=float)
    u = np.array(upper, dtype=float)

    return P, q, A, l, u, idx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="assets/go1/scene.xml")
    parser.add_argument("--horizon", type=int, default=10)
    parser.add_argument("--dt", type=float, default=0.02)
    parser.add_argument("--t0", type=float, default=0.12)
    parser.add_argument("--gait_period", type=float, default=0.4)
    parser.add_argument("--duty_factor", type=float, default=0.5)
    parser.add_argument("--mu", type=float, default=0.6)
    parser.add_argument("--fz_min", type=float, default=1.0)
    parser.add_argument("--fz_max", type=float, default=200.0)
    parser.add_argument("--wz", type=float, default=100000.0)
    parser.add_argument("--wvz", type=float, default=10000.0)
    parser.add_argument("--force_reg", type=float, default=1e-5)
    parser.add_argument("--log", default="results/logs_sample/stage05_centroidal_z_mpc.csv")
    args = parser.parse_args()

    model_path = Path(args.model)
    if not model_path.exists():
        raise FileNotFoundError(model_path)

    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    model = mujoco.MjModel.from_xml_path(str(model_path))
    data = mujoco.MjData(model)

    initialize_standing_pose(model, data, build_standing_q())

    mass, com = compute_total_mass_and_com(model, data)
    gravity = abs(float(model.opt.gravity[2]))

    z0 = float(com[2])
    vz0 = 0.0
    z_ref = z0

    times = [args.t0 + k * args.dt for k in range(args.horizon)]
    schedules = [
        contact_schedule(t, args.gait_period, args.duty_factor)
        for t in times
    ]

    P, q, A, l, u, idx = build_centroidal_z_mpc_qp(
        horizon=args.horizon,
        dt=args.dt,
        mass=mass,
        gravity=gravity,
        z0=z0,
        vz0=vz0,
        z_ref=z_ref,
        schedules=schedules,
        wz=args.wz,
        wvz=args.wvz,
        force_reg=args.force_reg,
        mu=args.mu,
        fz_min=args.fz_min,
        fz_max=args.fz_max,
    )

    solver = osqp.OSQP()
    solver.setup(
        P=P,
        q=q,
        A=A,
        l=l,
        u=u,
        verbose=False,
        eps_abs=1e-8,
        eps_rel=1e-8,
        max_iter=10000,
        polish=True,
    )

    result = solver.solve()

    print("=== Stage 5 Centroidal Z MPC ===")
    print(f"model = {model_path}")
    print(f"OSQP status = {result.info.status}")
    print(f"horizon = {args.horizon}")
    print(f"dt = {args.dt}")
    print(f"t0 = {args.t0}")
    print(f"gait_period = {args.gait_period}")
    print(f"duty_factor = {args.duty_factor}")
    print(f"mass = {mass:.6f} kg")
    print(f"gravity = {gravity:.6f}")
    print(f"z0 = {z0:.9f}")
    print(f"z_ref = {z_ref:.9f}")
    print(f"decision_variables = {idx.n_total}")
    print(f"constraint_rows = {A.shape[0]}")
    print()

    if result.x is None:
        print("FAIL: OSQP did not return a solution.")
        return

    x = result.x

    max_z_error = 0.0
    max_abs_vz = 0.0
    max_dynamics_residual = 0.0
    max_inactive_force_norm = 0.0
    max_abs_vertical_accel = 0.0

    rows = []

    for k in range(args.horizon):
        t = times[k]
        flags = schedules[k]
        mode = contact_mode_name(flags)

        z_k = x[idx.z(k)]
        vz_k = x[idx.vz(k)]
        z_next = x[idx.z(k + 1)]
        vz_next = x[idx.vz(k + 1)]

        f_mat = np.zeros((4, 3))
        for leg_i in range(4):
            for axis in range(3):
                f_mat[leg_i, axis] = x[idx.f(k, leg_i, axis)]

        sum_fz = float(np.sum(f_mat[:, 2]))
        vertical_accel = sum_fz / mass - gravity

        dyn_z_res = z_next - z_k - args.dt * vz_k
        dyn_vz_res = vz_next - vz_k - args.dt * vertical_accel

        z_error = z_k - z_ref

        max_z_error = max(max_z_error, abs(float(z_error)))
        max_abs_vz = max(max_abs_vz, abs(float(vz_k)))
        max_dynamics_residual = max(
            max_dynamics_residual,
            abs(float(dyn_z_res)),
            abs(float(dyn_vz_res)),
        )
        max_abs_vertical_accel = max(max_abs_vertical_accel, abs(float(vertical_accel)))

        inactive_force_norm = 0.0
        active_constraints_ok = True
        friction_ok = True

        for leg_i, active in enumerate(flags):
            fx, fy, fz = f_mat[leg_i]

            if active:
                if fz < args.fz_min - 1e-6 or fz > args.fz_max + 1e-6:
                    active_constraints_ok = False
                if abs(fx) > args.mu * fz + 1e-6:
                    friction_ok = False
                if abs(fy) > args.mu * fz + 1e-6:
                    friction_ok = False
            else:
                inactive_force_norm = max(inactive_force_norm, float(np.linalg.norm(f_mat[leg_i])))

        max_inactive_force_norm = max(max_inactive_force_norm, inactive_force_norm)

        knot_pass = (
            abs(z_error) < 1e-4
            and abs(vz_k) < 1e-3
            and abs(dyn_z_res) < 1e-6
            and abs(dyn_vz_res) < 1e-6
            and inactive_force_norm < 1e-6
            and active_constraints_ok
            and friction_ok
        )

        print(
            f"k={k:02d} "
            f"t={t:.3f} "
            f"mode={mode} "
            f"flags={flags} "
            f"z={z_k:.9f} "
            f"vz={vz_k:.9f} "
            f"sum_fz={sum_fz:.6f} "
            f"az={vertical_accel:.9f} "
            f"pass={knot_pass}"
        )

        for leg_i, leg in enumerate(LEG_ORDER):
            fx, fy, fz = f_mat[leg_i]
            rows.append([
                k,
                t,
                mode,
                leg,
                flags[leg_i],
                z_k,
                vz_k,
                z_next,
                vz_next,
                fx,
                fy,
                fz,
                sum_fz,
                vertical_accel,
                dyn_z_res,
                dyn_vz_res,
                z_error,
                inactive_force_norm,
                knot_pass,
            ])

    final_z = x[idx.z(args.horizon)]
    final_vz = x[idx.vz(args.horizon)]

    max_z_error = max(max_z_error, abs(float(final_z - z_ref)))
    max_abs_vz = max(max_abs_vz, abs(float(final_vz)))

    with log_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "knot",
            "time",
            "mode",
            "leg",
            "active",
            "z",
            "vz",
            "z_next",
            "vz_next",
            "fx",
            "fy",
            "fz",
            "sum_fz",
            "vertical_accel",
            "dyn_z_residual",
            "dyn_vz_residual",
            "z_error",
            "inactive_force_norm",
            "knot_pass",
        ])
        writer.writerows(rows)

    solved = result.info.status.lower() in ["solved", "solved inaccurate"]
    pass_all = (
        solved
        and max_z_error < 1e-4
        and max_abs_vz < 1e-3
        and max_dynamics_residual < 1e-6
        and max_inactive_force_norm < 1e-6
    )

    print()
    print(f"final_z = {final_z:.9f}")
    print(f"final_vz = {final_vz:.9f}")
    print(f"max_z_error = {max_z_error:.12f}")
    print(f"max_abs_vz = {max_abs_vz:.12f}")
    print(f"max_dynamics_residual = {max_dynamics_residual:.12f}")
    print(f"max_inactive_force_norm = {max_inactive_force_norm:.12f}")
    print(f"max_abs_vertical_accel = {max_abs_vertical_accel:.12f}")
    print(f"Log saved to: {log_path}")

    if pass_all:
        print("PASS: centroidal z MPC solved and tracks height/vertical velocity.")
    else:
        print("WARN/FAIL: centroidal z MPC did not meet tracking or constraint tolerance.")


if __name__ == "__main__":
    main()
