import argparse
import csv
from pathlib import Path

import mujoco
import numpy as np
import osqp
import scipy.sparse as sp


LEG_ORDER = ["FR", "FL", "RR", "RL"]
STAND_LEG_Q = np.array([0.0, 0.9, -1.8])

CONTACT_MODES = {
    "all_stance": [1, 1, 1, 1],
    "trot_FR_RL": [1, 0, 0, 1],
    "trot_FL_RR": [0, 1, 1, 0],
}


def build_standing_q():
    return np.tile(STAND_LEG_Q, 4)


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


def build_contact_constraints(contact_flags, mu, fz_min, fz_max):
    rows = []
    lower = []
    upper = []

    for i, active in enumerate(contact_flags):
        col = 3 * i

        if active:
            # fz bounds.
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
            # Inactive contact: fx = fy = fz = 0.
            for j in range(3):
                row = np.zeros((1, 12))
                row[0, col + j] = 1.0
                rows.append(row)
                lower.append(0.0)
                upper.append(0.0)

    A = np.vstack(rows)
    l = np.array(lower, dtype=float)
    u = np.array(upper, dtype=float)

    return A, l, u


def solve_wrench_tracking_qp(
    A_wrench,
    desired_wrench,
    A_constraint,
    l,
    u,
    q_weights,
    force_reg,
):
    n = 12

    Q = np.diag(q_weights)
    R = np.eye(n) * force_reg

    P_dense = A_wrench.T @ Q @ A_wrench + R
    q_dense = -A_wrench.T @ Q @ desired_wrench

    # OSQP expects 0.5 x^T P x + q^T x.
    P = sp.csc_matrix((P_dense + P_dense.T) * 0.5)
    q = q_dense

    A = sp.csc_matrix(A_constraint)

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

    return solver.solve()


def summarize_solution(mode_name, contact_flags, result, A_wrench, desired_wrench, mu):
    print(f"=== Mode: {mode_name} ===")
    print(f"contact_flags [FR,FL,RR,RL] = {contact_flags}")
    print(f"OSQP status = {result.info.status}")

    if result.x is None:
        print("FAIL: no solution")
        return None

    f = result.x.reshape(4, 3)
    achieved_wrench = A_wrench @ result.x
    wrench_error = achieved_wrench - desired_wrench

    print("Contact forces:")
    for i, leg in enumerate(LEG_ORDER):
        fx, fy, fz = f[i]
        margin_x = mu * fz - abs(fx)
        margin_y = mu * fz - abs(fy)

        print(
            f"  {leg}: active={contact_flags[i]} "
            f"fx={fx: .6f}, fy={fy: .6f}, fz={fz: .6f}, "
            f"mu*fz-|fx|={margin_x: .6f}, "
            f"mu*fz-|fy|={margin_y: .6f}"
        )

    print(f"achieved_wrench = {achieved_wrench}")
    print(f"desired_wrench  = {desired_wrench}")
    print(f"wrench_error    = {wrench_error}")
    print(f"wrench_error_norm = {np.linalg.norm(wrench_error):.12f}")
    print(f"vertical_force_error = {achieved_wrench[2] - desired_wrench[2]:.12f}")
    print()

    return f, achieved_wrench, wrench_error


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="assets/go1/scene.xml")
    parser.add_argument("--mu", type=float, default=0.6)
    parser.add_argument("--fz_min", type=float, default=1.0)
    parser.add_argument("--fz_max", type=float, default=200.0)
    parser.add_argument("--force_reg", type=float, default=1e-5)
    parser.add_argument(
        "--q_weights",
        type=float,
        nargs=6,
        default=[10.0, 10.0, 100.0, 50.0, 50.0, 10.0],
        help="Weights for [Fx,Fy,Fz,Mx,My,Mz] wrench tracking.",
    )
    parser.add_argument("--log", default="results/logs_sample/stage05_contact_schedule_force_qp.csv")
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

    desired_wrench = np.array([0.0, 0.0, mg, 0.0, 0.0, 0.0])
    A_wrench = build_wrench_matrix(foot_positions, com)

    print("=== Stage 5 Contact Schedule-aware Force QP ===")
    print(f"model = {model_path}")
    print(f"total_mass = {total_mass:.6f} kg")
    print(f"mg = {mg:.6f} N")
    print(f"COM = {com}")
    print(f"mu = {args.mu}")
    print(f"fz_min = {args.fz_min}")
    print(f"fz_max = {args.fz_max}")
    print(f"force_reg = {args.force_reg}")
    print(f"q_weights [Fx,Fy,Fz,Mx,My,Mz] = {args.q_weights}")
    print()

    rows_for_csv = []

    all_pass = True

    for mode_name, contact_flags in CONTACT_MODES.items():
        A_constraint, l, u = build_contact_constraints(
            contact_flags=contact_flags,
            mu=args.mu,
            fz_min=args.fz_min,
            fz_max=args.fz_max,
        )

        result = solve_wrench_tracking_qp(
            A_wrench=A_wrench,
            desired_wrench=desired_wrench,
            A_constraint=A_constraint,
            l=l,
            u=u,
            q_weights=np.array(args.q_weights, dtype=float),
            force_reg=args.force_reg,
        )

        summary = summarize_solution(
            mode_name=mode_name,
            contact_flags=contact_flags,
            result=result,
            A_wrench=A_wrench,
            desired_wrench=desired_wrench,
            mu=args.mu,
        )

        if summary is None:
            all_pass = False
            continue

        f, achieved_wrench, wrench_error = summary

        solved = result.info.status.lower() in ["solved", "solved inaccurate"]
        inactive_ok = True
        friction_ok = True
        fz_ok = True

        for i, active in enumerate(contact_flags):
            fx, fy, fz = f[i]

            if active:
                if fz < args.fz_min - 1e-6 or fz > args.fz_max + 1e-6:
                    fz_ok = False
                if abs(fx) > args.mu * fz + 1e-6:
                    friction_ok = False
                if abs(fy) > args.mu * fz + 1e-6:
                    friction_ok = False
            else:
                if np.linalg.norm(f[i]) > 1e-6:
                    inactive_ok = False

        # For all stance, expect near-exact wrench tracking.
        # For diagonal stance, allow small torque residual because exact static equilibrium
        # may not be feasible depending on COM projection.
        if mode_name == "all_stance":
            wrench_ok = np.linalg.norm(wrench_error) < 1e-5
        else:
            wrench_ok = abs(wrench_error[2]) < 1e-3 and np.linalg.norm(wrench_error) < 1.0

        mode_pass = solved and inactive_ok and friction_ok and fz_ok and wrench_ok
        all_pass = all_pass and mode_pass

        print(f"{mode_name} PASS = {mode_pass}")
        print()

        for i, leg in enumerate(LEG_ORDER):
            rows_for_csv.append([
                mode_name,
                leg,
                contact_flags[i],
                f[i, 0],
                f[i, 1],
                f[i, 2],
                args.mu * f[i, 2] - abs(f[i, 0]),
                args.mu * f[i, 2] - abs(f[i, 1]),
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
                np.linalg.norm(wrench_error),
                mode_pass,
            ])

    with log_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
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
            "mode_pass",
        ])
        writer.writerows(rows_for_csv)

    print(f"Log saved to: {log_path}")

    if all_pass:
        print("PASS: contact schedule-aware force QP works for all tested contact modes.")
    else:
        print("WARN/FAIL: at least one contact mode failed. Inspect wrench errors and constraints.")


if __name__ == "__main__":
    main()
