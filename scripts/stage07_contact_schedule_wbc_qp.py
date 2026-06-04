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
OUTPUT_CSV = "results/logs_sample/stage07_contact_schedule_wbc_qp.csv"

LEG_ORDER = ["FR", "FL", "RR", "RL"]
JOINTS = ["hip", "thigh", "calf"]
STANDING_Q_PER_LEG = [0.0, 0.9, -1.8]

CONTACT_MODES = {
    "all_stance": {"FR": 1, "FL": 1, "RR": 1, "RL": 1},
    "trot_FR_RL": {"FR": 1, "FL": 0, "RR": 0, "RL": 1},
    "trot_FL_RR": {"FR": 0, "FL": 1, "RR": 1, "RL": 0},
}

MU = 0.6
FZ_MIN = 1.0
FZ_MAX = 120.0
TORQUE_LIMIT = 23.7
INACTIVE_FORCE_TOL = 1e-5

W_WRENCH = 10.0
W_FORCE_REF = 0.1
W_TAU_REF = 0.5
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

        J_act = jacp[:, dofs]

        # 已确认符号约定：tau = -J^T f
        B[:, 3 * leg_i:3 * leg_i + 3] += -J_act.T

    return B


def contact_adjusted_force_ref(f_all, contact):
    f = np.zeros(12)

    active = [leg for leg in LEG_ORDER if contact[leg] == 1]
    if not active:
        raise RuntimeError("contact mode 没有 active leg")

    total_force = np.zeros(3)
    for leg_i, leg in enumerate(LEG_ORDER):
        total_force += f_all[3 * leg_i:3 * leg_i + 3]

    per_leg = total_force / len(active)

    for leg_i, leg in enumerate(LEG_ORDER):
        if contact[leg] == 1:
            f[3 * leg_i:3 * leg_i + 3] = per_leg

    return f


def build_constraints(B, contact):
    rows = []
    lower = []
    upper = []

    for leg_i, leg in enumerate(LEG_ORDER):
        base = 3 * leg_i

        if contact[leg] == 0:
            for axis in range(3):
                row = np.zeros(12)
                row[base + axis] = 1.0
                rows.append(row)
                lower.append(0.0)
                upper.append(0.0)
            continue

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


def solve_mode(mode_name, contact, A_wrench, B_tau, f_all, tau_ref):
    desired_wrench = A_wrench @ f_all
    f_mode_ref = contact_adjusted_force_ref(f_all, contact)

    H = (
        W_WRENCH * (A_wrench.T @ A_wrench)
        + W_FORCE_REF * np.eye(12)
        + W_TAU_REF * (B_tau.T @ B_tau)
        + W_REG * np.eye(12)
    )

    g = (
        -W_WRENCH * (A_wrench.T @ desired_wrench)
        -W_FORCE_REF * f_mode_ref
        -W_TAU_REF * (B_tau.T @ tau_ref)
    )

    A_con, l, u = build_constraints(B_tau, contact)

    solver = osqp.OSQP()
    solver.setup(
        P=sp.csc_matrix(2.0 * H),
        q=2.0 * g,
        A=sp.csc_matrix(A_con),
        l=l,
        u=u,
        verbose=False,
        polish=True,
    )

    result = solver.solve()

    if result.x is None:
        raise RuntimeError(f"{mode_name} OSQP failed: {result.info.status}")

    f_wbc = np.array(result.x)
    tau_wbc = B_tau @ f_wbc
    wrench_wbc = A_wrench @ f_wbc
    wrench_error = wrench_wbc - desired_wrench

    inactive_force_sq = 0.0
    active_fz_values = []
    friction_margins = []

    for leg_i, leg in enumerate(LEG_ORDER):
        f_leg = f_wbc[3 * leg_i:3 * leg_i + 3]
        fx, fy, fz = f_leg

        if contact[leg] == 0:
            inactive_force_sq += float(f_leg @ f_leg)
        else:
            active_fz_values.append(float(fz))
            friction_margins.append(float(MU * fz - abs(fx)))
            friction_margins.append(float(MU * fz - abs(fy)))

    inactive_force_norm = float(np.sqrt(inactive_force_sq))
    min_active_fz = min(active_fz_values) if active_fz_values else 0.0
    min_friction_margin = min(friction_margins) if friction_margins else 0.0

    tau_max_abs = float(np.max(np.abs(tau_wbc)))
    wrench_error_norm = float(np.linalg.norm(wrench_error))

    status_pass = result.info.status.lower() in ["solved", "solved inaccurate"]
    inactive_pass = inactive_force_norm <= INACTIVE_FORCE_TOL
    torque_pass = tau_max_abs <= TORQUE_LIMIT + 1e-9
    fz_pass = min_active_fz >= FZ_MIN - 1e-9
    friction_pass = min_friction_margin >= -1e-8

    pass_test = bool(
        status_pass
        and inactive_pass
        and torque_pass
        and fz_pass
        and friction_pass
    )

    row = {
        "mode": mode_name,
        "osqp_status": result.info.status,
        "objective": f"{result.info.obj_val:.12f}",
        "active_legs": ",".join([leg for leg in LEG_ORDER if contact[leg] == 1]),
        "inactive_legs": ",".join([leg for leg in LEG_ORDER if contact[leg] == 0]),
        "w_wrench": W_WRENCH,
        "w_force_ref": W_FORCE_REF,
        "w_tau_ref": W_TAU_REF,
        "w_reg": W_REG,
        "mu": MU,
        "fz_min": FZ_MIN,
        "fz_max": FZ_MAX,
        "torque_limit": TORQUE_LIMIT,
        "tau_max_abs": f"{tau_max_abs:.12f}",
        "inactive_force_norm": f"{inactive_force_norm:.12f}",
        "min_active_fz": f"{min_active_fz:.12f}",
        "min_friction_margin": f"{min_friction_margin:.12f}",
        "wrench_error_norm": f"{wrench_error_norm:.12f}",
        "inactive_pass": str(inactive_pass),
        "torque_pass": str(torque_pass),
        "fz_pass": str(fz_pass),
        "friction_pass": str(friction_pass),
        "pass": str(pass_test),
    }

    for i, name in enumerate(["Fx", "Fy", "Fz", "Mx", "My", "Mz"]):
        row[f"desired_{name}"] = f"{desired_wrench[i]:.12f}"
        row[f"wbc_{name}"] = f"{wrench_wbc[i]:.12f}"
        row[f"error_{name}"] = f"{wrench_error[i]:.12f}"

    for leg_i, leg in enumerate(LEG_ORDER):
        f_leg = f_wbc[3 * leg_i:3 * leg_i + 3]
        row[f"{leg}_contact"] = contact[leg]
        row[f"{leg}_fx"] = f"{f_leg[0]:.12f}"
        row[f"{leg}_fy"] = f"{f_leg[1]:.12f}"
        row[f"{leg}_fz"] = f"{f_leg[2]:.12f}"

    for leg_i, leg in enumerate(LEG_ORDER):
        tau_leg = tau_wbc[3 * leg_i:3 * leg_i + 3]
        for joint_i, joint in enumerate(JOINTS):
            row[f"{leg}_tau_{joint}"] = f"{tau_leg[joint_i]:.12f}"

    return row


def main():
    model = mujoco.MjModel.from_xml_path(SCENE)
    data = mujoco.MjData(model)

    if model.nu != 12:
        raise RuntimeError(f"期望 nu=12，实际 nu={model.nu}")

    f_all = read_force_ref()
    tau_ref = read_tau_ref()

    site_ids = set_standing_pose(model, data)
    dofs = actuator_dofs(model)

    A_wrench = build_wrench_matrix(model, data, site_ids)
    B_tau = build_tau_matrix(model, data, site_ids, dofs)

    rows = []
    for mode_name, contact in CONTACT_MODES.items():
        rows.append(
            solve_mode(
                mode_name=mode_name,
                contact=contact,
                A_wrench=A_wrench,
                B_tau=B_tau,
                f_all=f_all,
                tau_ref=tau_ref,
            )
        )

    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("Stage 7 contact schedule-aware WBC/QP")
    all_pass = True

    for row in rows:
        all_pass = all_pass and (row["pass"] == "True")
        print(
            f"mode={row['mode']} "
            f"osqp_status={row['osqp_status']} "
            f"tau_max_abs={row['tau_max_abs']} "
            f"inactive_force_norm={row['inactive_force_norm']} "
            f"min_active_fz={row['min_active_fz']} "
            f"min_friction_margin={row['min_friction_margin']} "
            f"wrench_error_norm={row['wrench_error_norm']} "
            f"pass={row['pass']}"
        )

    print(f"all_pass={all_pass}")
    print(f"saved={OUTPUT_CSV}")

    if not all_pass:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
