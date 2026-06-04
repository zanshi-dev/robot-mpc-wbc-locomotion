#!/usr/bin/env python3
import csv
from pathlib import Path

import mujoco
import numpy as np
import osqp
import scipy.sparse as sp


SCENE = "assets/go1/scene.xml"
FORCE_CSV = "results/logs_sample/stage05_standing_contact_force_qp.csv"
TAU_REF_CSV = "results/logs_sample/stage06_qp_force_to_actuator_torque.csv"
OUTPUT_CSV = "results/logs_sample/stage07_wbc_base_wrench_qp.csv"

LEG_ORDER = ["FR", "FL", "RR", "RL"]
JOINTS = ["hip", "thigh", "calf"]
STANDING_Q_PER_LEG = [0.0, 0.9, -1.8]

MU = 0.6
FZ_MIN = 1.0
FZ_MAX = 120.0
TORQUE_LIMIT = 23.7

W_WRENCH = 10.0
W_FORCE_REF = 1.0
W_TAU_REF = 1.0
W_REG = 1e-6


def read_force_ref():
    forces = {}
    with open(FORCE_CSV, "r", newline="") as f:
        for row in csv.DictReader(f):
            leg = row["leg"].strip().upper()
            if leg in LEG_ORDER:
                forces[leg] = np.array([
                    float(row["fx"]),
                    float(row["fy"]),
                    float(row["fz"]),
                ])

    missing = [leg for leg in LEG_ORDER if leg not in forces]
    if missing:
        raise RuntimeError(f"缺少接触力: {missing}")

    return np.concatenate([forces[leg] for leg in LEG_ORDER])


def read_tau_ref():
    with open(TAU_REF_CSV, "r", newline="") as f:
        row = next(csv.DictReader(f))

    tau = []
    for leg in LEG_ORDER:
        for joint in JOINTS:
            tau.append(float(row[f"{leg}_tau_{joint}"]))

    return np.array(tau)


def actuator_dofs(model):
    dofs = []
    for act_id in range(model.nu):
        jid = int(model.actuator_trnid[act_id, 0])
        dofs.append(int(model.jnt_dofadr[jid]))
    return dofs


def set_standing_pose(model, data):
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    data.ctrl[:] = 0.0

    data.qpos[0:3] = [0.0, 0.0, 0.32]
    data.qpos[3:7] = [1.0, 0.0, 0.0, 0.0]

    for act_id in range(model.nu):
        jid = int(model.actuator_trnid[act_id, 0])
        qadr = int(model.jnt_qposadr[jid])
        data.qpos[qadr] = STANDING_Q_PER_LEG[act_id % 3]

    mujoco.mj_forward(model, data)

    site_ids = {}
    for leg in LEG_ORDER:
        sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, leg)
        if sid < 0:
            raise RuntimeError(f"找不到 foot site: {leg}")
        site_ids[leg] = sid

    min_foot_z = min(float(data.site_xpos[site_ids[leg]][2]) for leg in LEG_ORDER)
    data.qpos[2] += 0.02 - min_foot_z

    mujoco.mj_forward(model, data)
    return site_ids


def build_wrench_matrix(model, data, site_ids):
    com = np.array(data.subtree_com[1], dtype=float)
    A = np.zeros((6, 12))

    for leg_i, leg in enumerate(LEG_ORDER):
        p = np.array(data.site_xpos[site_ids[leg]], dtype=float)
        r = p - com

        block = np.zeros((6, 3))
        block[0:3, 0:3] = np.eye(3)
        block[3:6, 0:3] = np.array([
            [0.0, -r[2], r[1]],
            [r[2], 0.0, -r[0]],
            [-r[1], r[0], 0.0],
        ])

        A[:, 3 * leg_i:3 * leg_i + 3] = block

    return A


def build_tau_matrix(model, data, site_ids, dofs):
    B = np.zeros((12, 12))

    for leg_i, leg in enumerate(LEG_ORDER):
        jacp = np.zeros((3, model.nv))
        jacr = np.zeros((3, model.nv))
        mujoco.mj_jacSite(model, data, jacp, jacr, site_ids[leg])

        # 已确认符号约定：tau = -J^T f
        J_act = jacp[:, dofs]
        B[:, 3 * leg_i:3 * leg_i + 3] += -J_act.T

    return B


def build_constraints(B):
    rows = []
    lower = []
    upper = []

    for leg_i in range(4):
        base = 3 * leg_i

        row = np.zeros(12)
        row[base + 2] = 1.0
        rows.append(row)
        lower.append(FZ_MIN)
        upper.append(FZ_MAX)

        row = np.zeros(12)
        row[base + 0] = 1.0
        row[base + 2] = -MU
        rows.append(row)
        lower.append(-np.inf)
        upper.append(0.0)

        row = np.zeros(12)
        row[base + 0] = -1.0
        row[base + 2] = -MU
        rows.append(row)
        lower.append(-np.inf)
        upper.append(0.0)

        row = np.zeros(12)
        row[base + 1] = 1.0
        row[base + 2] = -MU
        rows.append(row)
        lower.append(-np.inf)
        upper.append(0.0)

        row = np.zeros(12)
        row[base + 1] = -1.0
        row[base + 2] = -MU
        rows.append(row)
        lower.append(-np.inf)
        upper.append(0.0)

    for i in range(12):
        rows.append(B[i].copy())
        lower.append(-TORQUE_LIMIT)
        upper.append(TORQUE_LIMIT)

    return np.vstack(rows), np.array(lower), np.array(upper)


def solve_qp(A_wrench, B_tau, f_ref, tau_ref):
    desired_wrench = A_wrench @ f_ref

    H = (
        W_WRENCH * (A_wrench.T @ A_wrench)
        + W_FORCE_REF * np.eye(12)
        + W_TAU_REF * (B_tau.T @ B_tau)
        + W_REG * np.eye(12)
    )

    g = (
        -W_WRENCH * (A_wrench.T @ desired_wrench)
        -W_FORCE_REF * f_ref
        -W_TAU_REF * (B_tau.T @ tau_ref)
    )

    P = sp.csc_matrix(2.0 * H)
    q = 2.0 * g

    A_con, l, u = build_constraints(B_tau)

    solver = osqp.OSQP()
    solver.setup(
        P=P,
        q=q,
        A=sp.csc_matrix(A_con),
        l=l,
        u=u,
        verbose=False,
        polish=True,
    )
    result = solver.solve()

    if result.x is None:
        raise RuntimeError(f"OSQP failed: {result.info.status}")

    return result, desired_wrench


def main():
    model = mujoco.MjModel.from_xml_path(SCENE)
    data = mujoco.MjData(model)

    f_ref = read_force_ref()
    tau_ref = read_tau_ref()

    site_ids = set_standing_pose(model, data)
    dofs = actuator_dofs(model)

    A_wrench = build_wrench_matrix(model, data, site_ids)
    B_tau = build_tau_matrix(model, data, site_ids, dofs)

    result, desired_wrench = solve_qp(A_wrench, B_tau, f_ref, tau_ref)

    f_wbc = np.array(result.x)
    tau_wbc = B_tau @ f_wbc
    wrench_wbc = A_wrench @ f_wbc

    force_diff = f_wbc - f_ref
    tau_diff = tau_wbc - tau_ref
    wrench_error = wrench_wbc - desired_wrench

    tau_max_abs = float(np.max(np.abs(tau_wbc)))
    force_diff_norm = float(np.linalg.norm(force_diff))
    tau_diff_norm = float(np.linalg.norm(tau_diff))
    wrench_error_norm = float(np.linalg.norm(wrench_error))

    min_fz = min(float(f_wbc[3 * i + 2]) for i in range(4))

    status_pass = result.info.status.lower() in ["solved", "solved inaccurate"]
    torque_pass = tau_max_abs <= TORQUE_LIMIT + 1e-9
    fz_pass = min_fz >= FZ_MIN - 1e-9
    pass_test = bool(status_pass and torque_pass and fz_pass)

    row = {
        "osqp_status": result.info.status,
        "objective": f"{result.info.obj_val:.12f}",
        "w_wrench": W_WRENCH,
        "w_force_ref": W_FORCE_REF,
        "w_tau_ref": W_TAU_REF,
        "w_reg": W_REG,
        "mu": MU,
        "fz_min": FZ_MIN,
        "fz_max": FZ_MAX,
        "torque_limit": TORQUE_LIMIT,
        "tau_max_abs": f"{tau_max_abs:.12f}",
        "min_fz": f"{min_fz:.12f}",
        "force_diff_norm": f"{force_diff_norm:.12f}",
        "tau_diff_norm": f"{tau_diff_norm:.12f}",
        "wrench_error_norm": f"{wrench_error_norm:.12f}",
        "torque_pass": str(torque_pass),
        "fz_pass": str(fz_pass),
        "pass": str(pass_test),
    }

    for i, name in enumerate(["Fx", "Fy", "Fz", "Mx", "My", "Mz"]):
        row[f"desired_{name}"] = f"{desired_wrench[i]:.12f}"
        row[f"wbc_{name}"] = f"{wrench_wbc[i]:.12f}"
        row[f"error_{name}"] = f"{wrench_error[i]:.12f}"

    for leg_i, leg in enumerate(LEG_ORDER):
        f = f_wbc[3 * leg_i:3 * leg_i + 3]
        row[f"{leg}_fx"] = f"{f[0]:.12f}"
        row[f"{leg}_fy"] = f"{f[1]:.12f}"
        row[f"{leg}_fz"] = f"{f[2]:.12f}"

    for leg_i, leg in enumerate(LEG_ORDER):
        t = tau_wbc[3 * leg_i:3 * leg_i + 3]
        for j_i, joint in enumerate(JOINTS):
            row[f"{leg}_tau_{joint}"] = f"{t[j_i]:.12f}"

    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)

    print("Stage 7 WBC base wrench QP")
    for k in [
        "osqp_status",
        "tau_max_abs",
        "min_fz",
        "force_diff_norm",
        "tau_diff_norm",
        "wrench_error_norm",
        "torque_pass",
        "fz_pass",
        "pass",
    ]:
        print(f"{k}={row[k]}")

    print(f"saved={OUTPUT_CSV}")

    if not pass_test:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
