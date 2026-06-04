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
    flags = []
    for leg in LEG_ORDER:
        phase = gait_phase(t, gait_period, PHASE_OFFSETS[leg])
        flags.append(int(phase < duty_factor))
    return flags


def contact_mode_name(flags):
    if flags == [1, 1, 1, 1]:
        return "all_stance"
    if flags == [1, 0, 0, 1]:
        return "trot_FR_RL"
    if flags == [0, 1, 1, 0]:
        return "trot_FL_RR"
    return "custom_" + "".join(str(x) for x in flags)


def skew_cross_matrix(r):
    x, y, z = r
    return np.array([
        [0.0, -z, y],
        [z, 0.0, -x],
        [-y, x, 0.0],
    ])


def initialize_standing_pose(model, data, q_stand, desired_min_foot_z=0.02):
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0

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


def build_wrench_matrix(foot_positions, com):
    A = np.zeros((6, 12))

    for i, leg in enumerate(LEG_ORDER):
        col = 3 * i
        r = foot_positions[leg] - com

        A[0:3, col:col + 3] = np.eye(3)
        A[3:6, col:col + 3] = skew_cross_matrix(r)

    return A


def build_contact_constraints_for_one_knot(contact_flags, mu, fz_min, fz_max):
    rows = []
    lower = []
    upper = []

    for i, active in enumerate(contact_flags):
        col = 3 * i

        if active:
            # fz bounds
            row = np.zeros((1, 12))
            row[0, col + 2] = 1.0
            rows.append(row)
            lower.append(fz_min)
            upper.append(fz_max)

            # fx - mu*fz <= 0
            row = np.zeros((1, 12))
            row[0, col + 0] = 1.0
            row[0, col + 2] = -mu
            rows.append(row)
            lower.append(-np.inf)
            upper.append(0.0)

            # -fx - mu*fz <= 0
            row = np.zeros((1, 12))
            row[0, col + 0] = -1.0
            row[0, col + 2] = -mu
            rows.append(row)
            lower.append(-np.inf)
            upper.append(0.0)

            # fy - mu*fz <= 0
            row = np.zeros((1, 12))
            row[0, col + 1] = 1.0
            row[0, col + 2] = -mu
            rows.append(row)
            lower.append(-np.inf)
            upper.append(0.0)

            # -fy - mu*fz <= 0
            row = np.zeros((1, 12))
            row[0, col + 1] = -1.0
            row[0, col + 2] = -mu
            rows.append(row)
            lower.append(-np.inf)
            upper.append(0.0)
        else:
            # inactive leg: force must be zero
            for j in range(3):
                row = np.zeros((1, 12))
                row[0, col + j] = 1.0
                rows.append(row)
                lower.append(0.0)
                upper.append(0.0)

    A = np.vstack(rows)
    l = np.array(lower, dtype=float)
    u = np.array(upper, dtype=float)

    return sp.csc_matrix(A), l, u


def build_horizon_qp(
    A_wrench,
    desired_wrench,
    schedules,
    q_weights,
    force_reg,
    mu,
    fz_min,
    fz_max,
):
    n_per_knot = 12

    Q = np.diag(q_weights)
    R = np.eye(n_per_knot) * force_reg

    H = A_wrench.T @ Q @ A_wrench + R
    b = A_wrench.T @ Q @ desired_wrench

    # OSQP objective: 0.5 x^T P x + q^T x
    P_one = sp.csc_matrix(2.0 * H)
    q_one = -2.0 * b

    P_blocks = []
    q_blocks = []
    A_blocks = []
    l_blocks = []
    u_blocks = []

    for flags in schedules:
        A_k, l_k, u_k = build_contact_constraints_for_one_knot(
            contact_flags=flags,
            mu=mu,
            fz_min=fz_min,
            fz_max=fz_max,
        )

        P_blocks.append(P_one)
        q_blocks.append(q_one)
        A_blocks.append(A_k)
        l_blocks.append(l_k)
        u_blocks.append(u_k)

    P = sp.block_diag(P_blocks, format="csc")
    q = np.concatenate(q_blocks)

    A = sp.block_diag(A_blocks, format="csc")
    l = np.concatenate(l_blocks)
    u = np.concatenate(u_blocks)

    return P, q, A, l, u


def check_one_knot_solution(f, flags, A_wrench, desired_wrench, mu, fz_min, fz_max):
    achieved_wrench = A_wrench @ f.reshape(12)
    wrench_error = achieved_wrench - desired_wrench

    inactive_ok = True
    active_bounds_ok = True
    friction_ok = True

    f_mat = f.reshape(4, 3)

    for i, active in enumerate(flags):
        fx, fy, fz = f_mat[i]

        if active:
            if fz < fz_min - 1e-6 or fz > fz_max + 1e-6:
                active_bounds_ok = False
            if abs(fx) > mu * fz + 1e-6:
                friction_ok = False
            if abs(fy) > mu * fz + 1e-6:
                friction_ok = False
        else:
            if np.linalg.norm(f_mat[i]) > 1e-6:
                inactive_ok = False

    vertical_ok = abs(wrench_error[2]) < 1e-3
    wrench_tracking_ok = np.linalg.norm(wrench_error) < 1.0

    knot_pass = inactive_ok and active_bounds_ok and friction_ok and vertical_ok and wrench_tracking_ok

    return achieved_wrench, wrench_error, knot_pass


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
    parser.add_argument("--force_reg", type=float, default=1e-5)
    parser.add_argument(
        "--q_weights",
        type=float,
        nargs=6,
        default=[10.0, 10.0, 100.0, 50.0, 50.0, 10.0],
        help="Weights for [Fx,Fy,Fz,Mx,My,Mz].",
    )
    parser.add_argument("--log", default="results/logs_sample/stage05_horizon_force_qp.csv")
    args = parser.parse_args()

    model_path = Path(args.model)
    if not model_path.exists():
        raise FileNotFoundError(model_path)

    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    model = mujoco.MjModel.from_xml_path(str(model_path))
    data = mujoco.MjData(model)

    initialize_standing_pose(model, data, build_standing_q())

    total_mass, com = compute_total_mass_and_com(model, data)
    g = abs(float(model.opt.gravity[2]))
    mg = total_mass * g

    foot_positions = {}
    for leg in LEG_ORDER:
        gid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, leg)
        if gid < 0:
            raise RuntimeError(f"Cannot find foot geom: {leg}")
        foot_positions[leg] = data.geom_xpos[gid].copy()

    A_wrench = build_wrench_matrix(foot_positions, com)
    desired_wrench = np.array([0.0, 0.0, mg, 0.0, 0.0, 0.0])

    times = [args.t0 + k * args.dt for k in range(args.horizon)]
    schedules = [
        contact_schedule(t, args.gait_period, args.duty_factor)
        for t in times
    ]

    P, q, A, l, u = build_horizon_qp(
        A_wrench=A_wrench,
        desired_wrench=desired_wrench,
        schedules=schedules,
        q_weights=np.array(args.q_weights, dtype=float),
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

    print("=== Stage 5 N-step Horizon Force QP ===")
    print(f"model = {model_path}")
    print(f"OSQP status = {result.info.status}")
    print(f"horizon = {args.horizon}")
    print(f"dt = {args.dt}")
    print(f"t0 = {args.t0}")
    print(f"gait_period = {args.gait_period}")
    print(f"duty_factor = {args.duty_factor}")
    print(f"total_mass = {total_mass:.6f} kg")
    print(f"mg = {mg:.6f} N")
    print(f"COM = {com}")
    print(f"decision_variables = {args.horizon * 12}")
    print(f"constraint_rows = {A.shape[0]}")
    print()

    if result.x is None:
        print("FAIL: OSQP did not return a solution.")
        return

    solved = result.info.status.lower() in ["solved", "solved inaccurate"]

    forces = result.x.reshape(args.horizon, 4, 3)

    all_knot_pass = True
    max_wrench_error_norm = 0.0
    max_vertical_force_error = 0.0

    rows = []

    for k in range(args.horizon):
        t = times[k]
        flags = schedules[k]
        mode = contact_mode_name(flags)

        f_k = forces[k]
        achieved_wrench, wrench_error, knot_pass = check_one_knot_solution(
            f=f_k,
            flags=flags,
            A_wrench=A_wrench,
            desired_wrench=desired_wrench,
            mu=args.mu,
            fz_min=args.fz_min,
            fz_max=args.fz_max,
        )

        wrench_error_norm = float(np.linalg.norm(wrench_error))
        vertical_force_error = float(wrench_error[2])

        max_wrench_error_norm = max(max_wrench_error_norm, wrench_error_norm)
        max_vertical_force_error = max(max_vertical_force_error, abs(vertical_force_error))
        all_knot_pass = all_knot_pass and knot_pass

        print(
            f"k={k:02d} "
            f"t={t:.3f} "
            f"mode={mode} "
            f"flags={flags} "
            f"Fz={achieved_wrench[2]:.6f} "
            f"vertical_err={vertical_force_error:.9f} "
            f"wrench_err_norm={wrench_error_norm:.9f} "
            f"pass={knot_pass}"
        )

        for i, leg in enumerate(LEG_ORDER):
            fx, fy, fz = f_k[i]
            rows.append([
                k,
                t,
                mode,
                leg,
                flags[i],
                fx,
                fy,
                fz,
                args.mu * fz - abs(fx),
                args.mu * fz - abs(fy),
                achieved_wrench[0],
                achieved_wrench[1],
                achieved_wrench[2],
                achieved_wrench[3],
                achieved_wrench[4],
                achieved_wrench[5],
                wrench_error[0],
                wrench_error[1],
                wrench_error[2],
                wrench_error[3],
                wrench_error[4],
                wrench_error[5],
                wrench_error_norm,
                knot_pass,
            ])

    with log_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "knot",
            "time",
            "mode",
            "leg",
            "active",
            "fx",
            "fy",
            "fz",
            "mu_fz_minus_abs_fx",
            "mu_fz_minus_abs_fy",
            "achieved_Fx",
            "achieved_Fy",
            "achieved_Fz",
            "achieved_Mx",
            "achieved_My",
            "achieved_Mz",
            "error_Fx",
            "error_Fy",
            "error_Fz",
            "error_Mx",
            "error_My",
            "error_Mz",
            "wrench_error_norm",
            "knot_pass",
        ])
        writer.writerows(rows)

    print()
    print(f"max_wrench_error_norm = {max_wrench_error_norm:.12f}")
    print(f"max_abs_vertical_force_error = {max_vertical_force_error:.12f}")
    print(f"Log saved to: {log_path}")

    if solved and all_knot_pass:
        print("PASS: N-step horizon force QP solved for the full contact schedule.")
    else:
        print("WARN/FAIL: horizon force QP failed at one or more knots.")


if __name__ == "__main__":
    main()
