#!/usr/bin/env python3
import csv
from pathlib import Path

import mujoco
import numpy as np
import osqp
import scipy.sparse as sp


SCENE = "assets/go1/scene.xml"
INPUT_CSV = "results/logs_sample/stage07_online_swing_trajectory_memory_proto.csv"
OUTPUT_CSV = "results/logs_sample/stage07_online_swing_trajectory_tracking_check.csv"
SUMMARY_CSV = "results/logs_sample/stage07_online_swing_trajectory_tracking_check_summary.csv"

LEG_ORDER = ["FR", "FL", "RR", "RL"]
JOINTS = ["hip", "thigh", "calf"]
STANDING_Q_PER_LEG = [0.0, 0.9, -1.8]

MAX_DQ_STEP = 0.015
MAX_Q_DELTA_FROM_STANDING = 0.35

W_SWING = 200.0
W_STANCE = 50.0
W_REG = 1e-3
W_SMOOTH = 10.0

FOOT_ERROR_TOL = 0.006
MAX_DQ_STEP_TOL = 0.016
MAX_Q_DELTA_TOL = 0.36


def actuator_indices(model):
    dofs = []
    qadrs = []

    for act_id in range(model.nu):
        jid = int(model.actuator_trnid[act_id, 0])
        dofs.append(int(model.jnt_dofadr[jid]))
        qadrs.append(int(model.jnt_qposadr[jid]))

    return dofs, qadrs


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

    nominal_feet = {
        leg: np.array(data.site_xpos[site_ids[leg]], dtype=float).copy()
        for leg in LEG_ORDER
    }

    q_standing = np.array([float(data.qpos[qadr]) for qadr in qadrs_global], dtype=float)

    return site_ids, nominal_feet, q_standing


def foot_jacobian(model, data, site_id):
    jacp = np.zeros((3, model.nv))
    jacr = np.zeros((3, model.nv))
    mujoco.mj_jacSite(model, data, jacp, jacr, site_id)
    return jacp


def all_foot_jacobian_actuated(model, data, site_ids, dofs):
    blocks = []
    for leg in LEG_ORDER:
        J = foot_jacobian(model, data, site_ids[leg])
        blocks.append(J[:, dofs])
    return np.vstack(blocks)


def parse_targets(row):
    targets = {}
    for leg in LEG_ORDER:
        targets[leg] = np.array([
            float(row[f"{leg}_target_x"]),
            float(row[f"{leg}_target_y"]),
            float(row[f"{leg}_target_z"]),
        ], dtype=float)
    return targets


def solve_dq(J_all, current_feet, target_feet, swing_legs, dq_prev):
    rows = []
    b = []
    weights = []

    for leg_i, leg in enumerate(LEG_ORDER):
        J = J_all[3 * leg_i:3 * leg_i + 3, :]
        err = target_feet[leg] - current_feet[leg]

        rows.append(J)
        b.append(err)

        if leg in swing_legs:
            weights.extend([W_SWING, W_SWING, W_SWING])
        else:
            weights.extend([W_STANCE, W_STANCE, W_STANCE])

    A_task = np.vstack(rows)
    b_task = np.concatenate(b)
    W = np.diag(weights)

    H = A_task.T @ W @ A_task
    g = -A_task.T @ W @ b_task

    H += W_REG * np.eye(12)
    H += W_SMOOTH * np.eye(12)
    g += -W_SMOOTH * dq_prev

    P = sp.csc_matrix(2.0 * H)
    q = 2.0 * g

    A = sp.eye(12, format="csc")
    l = -MAX_DQ_STEP * np.ones(12)
    u = MAX_DQ_STEP * np.ones(12)

    solver = osqp.OSQP()
    solver.setup(
        P=P,
        q=q,
        A=A,
        l=l,
        u=u,
        verbose=False,
        polish=False,
        eps_abs=1e-8,
        eps_rel=1e-8,
        max_iter=10000,
    )

    result = solver.solve()

    if result.x is None:
        raise RuntimeError(f"OSQP failed: {result.info.status}")

    return np.array(result.x, dtype=float), result.info.status


def read_input_rows():
    with open(INPUT_CSV, "r", newline="") as f:
        return list(csv.DictReader(f))


def main():
    global qadrs_global

    rows_in = read_input_rows()

    model = mujoco.MjModel.from_xml_path(SCENE)
    data = mujoco.MjData(model)

    dofs, qadrs = actuator_indices(model)
    qadrs_global = qadrs

    site_ids, nominal_feet, q_standing = set_standing_pose(model, data)

    q_cmd = q_standing.copy()
    dq_prev = np.zeros(12)

    rows_out = []

    max_foot_error_norm = 0.0
    max_swing_foot_error_norm = 0.0
    max_stance_foot_error_norm = 0.0
    max_abs_dq_step = 0.0
    max_q_delta_from_standing = 0.0
    qp_fail_steps = 0

    for row in rows_in:
        step = int(row["step"])
        mode = row["mode"]
        swing_legs = row["swing_legs"].split(",") if row["swing_legs"] else []
        stance_legs = row["stance_legs"].split(",") if row["stance_legs"] else []

        for i, qadr in enumerate(qadrs):
            data.qpos[qadr] = q_cmd[i]
        mujoco.mj_forward(model, data)

        current_feet = {
            leg: np.array(data.site_xpos[site_ids[leg]], dtype=float).copy()
            for leg in LEG_ORDER
        }

        target_feet = parse_targets(row)
        J_all = all_foot_jacobian_actuated(model, data, site_ids, dofs)

        try:
            dq, osqp_status = solve_dq(
                J_all=J_all,
                current_feet=current_feet,
                target_feet=target_feet,
                swing_legs=swing_legs,
                dq_prev=dq_prev,
            )
        except RuntimeError as e:
            qp_fail_steps += 1
            dq = np.zeros(12)
            osqp_status = str(e)

        q_cmd = q_cmd + dq
        dq_prev = dq.copy()

        q_cmd = np.clip(
            q_cmd,
            q_standing - MAX_Q_DELTA_FROM_STANDING,
            q_standing + MAX_Q_DELTA_FROM_STANDING,
        )

        for i, qadr in enumerate(qadrs):
            data.qpos[qadr] = q_cmd[i]
        mujoco.mj_forward(model, data)

        achieved_feet = {
            leg: np.array(data.site_xpos[site_ids[leg]], dtype=float).copy()
            for leg in LEG_ORDER
        }

        foot_errors = {
            leg: achieved_feet[leg] - target_feet[leg]
            for leg in LEG_ORDER
        }

        step_max_foot_error = max(float(np.linalg.norm(foot_errors[leg])) for leg in LEG_ORDER)
        step_max_swing_error = max(
            float(np.linalg.norm(foot_errors[leg]))
            for leg in swing_legs
        )
        step_max_stance_error = max(
            float(np.linalg.norm(foot_errors[leg]))
            for leg in stance_legs
        )

        step_max_abs_dq = float(np.max(np.abs(dq)))
        step_max_q_delta = float(np.max(np.abs(q_cmd - q_standing)))

        max_foot_error_norm = max(max_foot_error_norm, step_max_foot_error)
        max_swing_foot_error_norm = max(max_swing_foot_error_norm, step_max_swing_error)
        max_stance_foot_error_norm = max(max_stance_foot_error_norm, step_max_stance_error)
        max_abs_dq_step = max(max_abs_dq_step, step_max_abs_dq)
        max_q_delta_from_standing = max(max_q_delta_from_standing, step_max_q_delta)

        out = {
            "step": step,
            "mode": mode,
            "phase_in_mode": row["phase_in_mode"],
            "swing_progress": row["swing_progress"],
            "stance_legs": row["stance_legs"],
            "swing_legs": row["swing_legs"],
            "osqp_status": osqp_status,
            "max_foot_error_norm": f"{step_max_foot_error:.12f}",
            "max_swing_foot_error_norm": f"{step_max_swing_error:.12f}",
            "max_stance_foot_error_norm": f"{step_max_stance_error:.12f}",
            "max_abs_dq_step": f"{step_max_abs_dq:.12f}",
            "max_q_delta_from_standing": f"{step_max_q_delta:.12f}",
        }

        for leg_i, leg in enumerate(LEG_ORDER):
            out[f"{leg}_foot_error_norm"] = f"{float(np.linalg.norm(foot_errors[leg])):.12f}"

        for leg_i, leg in enumerate(LEG_ORDER):
            for joint_i, joint in enumerate(JOINTS):
                idx = 3 * leg_i + joint_i
                out[f"{leg}_q_{joint}"] = f"{q_cmd[idx]:.12f}"

        rows_out.append(out)

    foot_error_pass = max_foot_error_norm < FOOT_ERROR_TOL
    swing_error_pass = max_swing_foot_error_norm < FOOT_ERROR_TOL
    dq_step_pass = max_abs_dq_step <= MAX_DQ_STEP_TOL
    q_delta_pass = max_q_delta_from_standing <= MAX_Q_DELTA_TOL
    qp_pass = qp_fail_steps == 0

    pass_test = foot_error_pass and swing_error_pass and dq_step_pass and q_delta_pass and qp_pass

    summary = {
        "input_csv": INPUT_CSV,
        "total_steps": len(rows_in),
        "max_foot_error_norm": f"{max_foot_error_norm:.12f}",
        "max_swing_foot_error_norm": f"{max_swing_foot_error_norm:.12f}",
        "max_stance_foot_error_norm": f"{max_stance_foot_error_norm:.12f}",
        "max_abs_dq_step": f"{max_abs_dq_step:.12f}",
        "max_q_delta_from_standing": f"{max_q_delta_from_standing:.12f}",
        "qp_fail_steps": qp_fail_steps,
        "foot_error_tol": FOOT_ERROR_TOL,
        "max_dq_step_tol": MAX_DQ_STEP_TOL,
        "max_q_delta_tol": MAX_Q_DELTA_TOL,
        "foot_error_pass": str(foot_error_pass),
        "swing_error_pass": str(swing_error_pass),
        "dq_step_pass": str(dq_step_pass),
        "q_delta_pass": str(q_delta_pass),
        "qp_pass": str(qp_pass),
        "pass": str(pass_test),
    }

    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        writer.writeheader()
        writer.writerows(rows_out)

    with open(SUMMARY_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary.keys()))
        writer.writeheader()
        writer.writerow(summary)

    print("Stage 7 online swing trajectory tracking check")
    for k, v in summary.items():
        print(f"{k}={v}")

    print(f"saved={OUTPUT_CSV}")
    print(f"saved_summary={SUMMARY_CSV}")

    if not pass_test:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
