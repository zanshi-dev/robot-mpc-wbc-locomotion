import argparse
import csv
from pathlib import Path

import mujoco
import numpy as np
import osqp
import scipy.sparse as sp


LEG_ORDER = ["FR", "FL", "RR", "RL"]
STAND_LEG_Q = np.array([0.0, 0.9, -1.8])


def build_standing_q():
    return np.tile(STAND_LEG_Q, 4)


def skew_cross_matrix(r):
    # Returns S(r) such that S(r) @ f = r x f.
    x, y, z = r
    return np.array([
        [0.0, -z, y],
        [z, 0.0, -x],
        [-y, x, 0.0],
    ])


def initialize_standing_pose(model, data, q_stand, desired_min_foot_z=0.02):
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0

    # MuJoCo free-joint qpos: x, y, z, qw, qx, qy, qz.
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
    masses = np.asarray(model.body_mass)
    xipos = np.asarray(data.xipos)

    # Ignore world body at index 0.
    masses = masses[1:]
    xipos = xipos[1:]

    total_mass = float(np.sum(masses))
    com = np.sum(xipos * masses[:, None], axis=0) / total_mass
    return total_mass, com


def build_wrench_matrix(foot_positions, com):
    # wrench = [sum force; sum torque about COM]
    # force_i is expressed in world frame.
    A = np.zeros((6, 12))

    for i, leg in enumerate(LEG_ORDER):
        col = 3 * i
        r = foot_positions[leg] - com

        A[0:3, col:col + 3] = np.eye(3)
        A[3:6, col:col + 3] = skew_cross_matrix(r)

    return A


def build_constraint_matrix(A_wrench, desired_wrench, mu, fz_min, fz_max):
    rows = []
    lower = []
    upper = []

    # Equality wrench constraint.
    rows.append(A_wrench)
    lower.extend(desired_wrench.tolist())
    upper.extend(desired_wrench.tolist())

    # Per-foot inequality constraints.
    for i, leg in enumerate(LEG_ORDER):
        col = 3 * i

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

    A = np.vstack(rows)
    l = np.array(lower, dtype=float)
    u = np.array(upper, dtype=float)

    return A, l, u


def solve_contact_force_qp(A_constraint, l, u, force_weight):
    n = 12

    # Minimum-norm contact force subject to wrench and friction constraints.
    P = sp.eye(n, format="csc") * force_weight
    q = np.zeros(n)

    A = sp.csc_matrix(A_constraint)

    solver = osqp.OSQP()
    solver.setup(
        P=P,
        q=q,
        A=A,
        l=l,
        u=u,
        verbose=False,
        eps_abs=1e-9,
        eps_rel=1e-9,
        max_iter=10000,
        polish=True,
    )

    result = solver.solve()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="assets/go1/scene.xml")
    parser.add_argument("--mu", type=float, default=0.6)
    parser.add_argument("--fz_min", type=float, default=1.0)
    parser.add_argument("--fz_max", type=float, default=200.0)
    parser.add_argument("--force_weight", type=float, default=1.0)
    parser.add_argument("--log", default="results/logs_sample/stage05_standing_contact_force_qp.csv")
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
    A_constraint, l, u = build_constraint_matrix(
        A_wrench=A_wrench,
        desired_wrench=desired_wrench,
        mu=args.mu,
        fz_min=args.fz_min,
        fz_max=args.fz_max,
    )

    result = solve_contact_force_qp(
        A_constraint=A_constraint,
        l=l,
        u=u,
        force_weight=args.force_weight,
    )

    print("=== Stage 5 Standing Contact Force QP ===")
    print(f"model = {model_path}")
    print(f"OSQP status = {result.info.status}")
    print(f"total_mass = {total_mass:.6f} kg")
    print(f"gravity = {g:.6f} m/s^2")
    print(f"mg = {mg:.6f} N")
    print(f"mg / 4 = {mg / 4.0:.6f} N")
    print(f"COM = {com}")
    print()

    print("Foot positions:")
    for leg in LEG_ORDER:
        print(f"  {leg}: {foot_positions[leg]}")
    print()

    if result.x is None:
        print("FAIL: OSQP did not return a solution.")
        return

    f = result.x.reshape(4, 3)

    achieved_wrench = A_wrench @ result.x
    wrench_error = achieved_wrench - desired_wrench

    print("Contact forces:")
    for i, leg in enumerate(LEG_ORDER):
        fx, fy, fz = f[i]
        friction_margin_x = args.mu * fz - abs(fx)
        friction_margin_y = args.mu * fz - abs(fy)
        print(
            f"  {leg}: "
            f"fx={fx: .6f}, fy={fy: .6f}, fz={fz: .6f}, "
            f"mu*fz-|fx|={friction_margin_x: .6f}, "
            f"mu*fz-|fy|={friction_margin_y: .6f}"
        )

    print()
    print(f"achieved_wrench = {achieved_wrench}")
    print(f"desired_wrench  = {desired_wrench}")
    print(f"wrench_error    = {wrench_error}")
    print(f"wrench_error_norm = {np.linalg.norm(wrench_error):.12f}")

    fz_values = f[:, 2]
    fz_error_from_mg4 = fz_values - mg / 4.0

    print()
    print(f"fz_values = {fz_values}")
    print(f"fz_error_from_mg4 = {fz_error_from_mg4}")
    print(f"max_abs_fz_error_from_mg4 = {np.max(np.abs(fz_error_from_mg4)):.12f}")

    with log_path.open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "leg", "fx", "fy", "fz",
            "mu_fz_minus_abs_fx",
            "mu_fz_minus_abs_fy",
        ])

        for i, leg in enumerate(LEG_ORDER):
            fx, fy, fz = f[i]
            writer.writerow([
                leg,
                fx,
                fy,
                fz,
                args.mu * fz - abs(fx),
                args.mu * fz - abs(fy),
            ])

    print(f"Log saved to: {log_path}")

    solved = result.info.status.lower() in ["solved", "solved inaccurate"]
    wrench_ok = np.linalg.norm(wrench_error) < 1e-6
    fz_ok = np.max(np.abs(fz_error_from_mg4)) < 5.0
    friction_ok = np.all(np.abs(f[:, 0]) <= args.mu * f[:, 2] + 1e-8) and np.all(
        np.abs(f[:, 1]) <= args.mu * f[:, 2] + 1e-8
    )

    if solved and wrench_ok and fz_ok and friction_ok:
        print("PASS: standing contact force QP solved and force distribution is valid.")
    else:
        print("WARN/FAIL: check OSQP status, wrench error, fz distribution, or friction constraints.")


if __name__ == "__main__":
    main()
