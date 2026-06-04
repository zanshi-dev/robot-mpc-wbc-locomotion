#!/usr/bin/env python3
import csv
from pathlib import Path

import mujoco
import numpy as np


TARGET_CSV = "results/logs_sample/stage07_swing_joint_target_sequence.csv"
WBC_CSV = "results/logs_sample/stage07_contact_schedule_wbc_qp.csv"
LOG_CSV = "results/logs_sample/stage07_swing_joint_target_tracking_with_wbc_test_log.csv"
SUMMARY_CSV = "results/logs_sample/stage07_swing_joint_target_tracking_with_wbc_test_summary.csv"
SCENE = "assets/go1/scene.xml"

MODE = "trot_FR_RL"
WBC_SCALE = 0.6

LEG_ORDER = ["FR", "FL", "RR", "RL"]
JOINTS = ["hip", "thigh", "calf"]
STANDING_Q_PER_LEG = [0.0, 0.9, -1.8]

KP = 80.0
KD = 2.0
TORQUE_LIMIT = 23.7
KNOT_HOLD_STEPS = 80

MAX_ROLL_LIMIT = 0.15
MAX_PITCH_LIMIT = 0.15
MIN_Z_LIMIT = 0.22
MAX_JOINT_ERROR_LIMIT = 0.10


def read_targets():
    rows = []

    with open(TARGET_CSV, "r", newline="") as f:
        for row in csv.DictReader(f):
            if row["mode"] != MODE:
                continue

            q_target = []
            for leg in LEG_ORDER:
                for joint in JOINTS:
                    q_target.append(float(row[f"{leg}_q_{joint}"]))

            rows.append({
                "mode": row["mode"],
                "knot": int(row["knot"]),
                "swing_legs": row["swing_legs"],
                "stance_legs": row["stance_legs"],
                "q_target": np.array(q_target, dtype=float),
            })

    if not rows:
        raise RuntimeError(f"找不到 mode={MODE} 的 q_target")

    rows.sort(key=lambda r: r["knot"])
    return rows


def read_wbc_tau():
    with open(WBC_CSV, "r", newline="") as f:
        for row in csv.DictReader(f):
            if row["mode"] != MODE:
                tau = []
                continue

            tau = []
            for leg in LEG_ORDER:
                for joint in JOINTS:
                    tau.append(float(row[f"{leg}_tau_{joint}"]))

            return WBC_SCALE * np.array(tau, dtype=float)

    raise RuntimeError(f"找不到 mode={MODE} 的 WBC torque")


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
    return site_ids


def quat_to_roll_pitch(q):
    w, x, y, z = q

    roll = np.arctan2(
        2.0 * (w * x + y * z),
        1.0 - 2.0 * (x * x + y * y),
    )

    pitch = np.arcsin(np.clip(2.0 * (w * y - z * x), -1.0, 1.0))

    return float(roll), float(pitch)


def current_actuated_q(data, qadrs):
    return np.array([float(data.qpos[qadr]) for qadr in qadrs], dtype=float)


def main():
    target_rows = read_targets()
    tau_wbc = read_wbc_tau()

    model = mujoco.MjModel.from_xml_path(SCENE)
    data = mujoco.MjData(model)

    if model.nu != 12:
        raise RuntimeError(f"期望 nu=12，实际 nu={model.nu}")

    dofs, qadrs = actuator_indices(model)
    site_ids = set_standing_pose(model, data)

    initial_q = current_actuated_q(data, qadrs)
    prev_target = initial_q.copy()

    initial_z = float(data.qpos[2])
    min_z = initial_z
    max_z = initial_z
    max_abs_roll = 0.0
    max_abs_pitch = 0.0
    max_tau_pd_abs = 0.0
    max_tau_wbc_abs = float(np.max(np.abs(tau_wbc)))
    max_tau_total_abs = 0.0
    saturation_steps = 0
    max_joint_error = 0.0
    max_swing_joint_error = 0.0
    max_stance_joint_error = 0.0
    max_swing_foot_z = -1e9
    min_swing_foot_z = 1e9

    rows = []
    global_step = 0

    swing_legs = [x.strip() for x in target_rows[0]["swing_legs"].split(",")]
    stance_legs = [x.strip() for x in target_rows[0]["stance_legs"].split(",")]

    swing_indices = []
    stance_indices = []

    for leg in swing_legs:
        leg_i = LEG_ORDER.index(leg)
        swing_indices.extend([3 * leg_i + 0, 3 * leg_i + 1, 3 * leg_i + 2])

    for leg in stance_legs:
        leg_i = LEG_ORDER.index(leg)
        stance_indices.extend([3 * leg_i + 0, 3 * leg_i + 1, 3 * leg_i + 2])

    for target_row in target_rows:
        knot = target_row["knot"]
        q_target_end = target_row["q_target"]

        for local_step in range(KNOT_HOLD_STEPS):
            alpha = float(local_step + 1) / float(KNOT_HOLD_STEPS)
            q_des = (1.0 - alpha) * prev_target + alpha * q_target_end

            q_now = current_actuated_q(data, qadrs)
            qd_now = np.array([float(data.qvel[dof]) for dof in dofs], dtype=float)

            q_error = q_des - q_now

            tau_pd = KP * q_error - KD * qd_now
            tau_total_raw = tau_pd + tau_wbc
            tau_total = np.clip(tau_total_raw, -TORQUE_LIMIT, TORQUE_LIMIT)

            saturated = bool(np.any(np.abs(tau_total_raw) > TORQUE_LIMIT))
            saturation_steps += int(saturated)

            data.ctrl[:] = tau_total
            mujoco.mj_step(model, data)

            q_now_after = current_actuated_q(data, qadrs)
            q_error_after = q_des - q_now_after

            roll, pitch = quat_to_roll_pitch(data.qpos[3:7])
            base_z = float(data.qpos[2])

            min_z = min(min_z, base_z)
            max_z = max(max_z, base_z)
            max_abs_roll = max(max_abs_roll, abs(roll))
            max_abs_pitch = max(max_abs_pitch, abs(pitch))
            max_tau_pd_abs = max(max_tau_pd_abs, float(np.max(np.abs(tau_pd))))
            max_tau_total_abs = max(max_tau_total_abs, float(np.max(np.abs(tau_total))))

            joint_error_abs = np.abs(q_error_after)
            max_joint_error = max(max_joint_error, float(np.max(joint_error_abs)))
            max_swing_joint_error = max(
                max_swing_joint_error,
                float(np.max(joint_error_abs[swing_indices])),
            )
            max_stance_joint_error = max(
                max_stance_joint_error,
                float(np.max(joint_error_abs[stance_indices])),
            )

            swing_foot_z_values = []
            for leg in swing_legs:
                z = float(data.site_xpos[site_ids[leg]][2])
                swing_foot_z_values.append(z)
                max_swing_foot_z = max(max_swing_foot_z, z)
                min_swing_foot_z = min(min_swing_foot_z, z)

            rows.append({
                "step": global_step,
                "knot": knot,
                "knot_step": local_step,
                "mode": MODE,
                "time": f"{data.time:.9f}",
                "base_z": f"{base_z:.12f}",
                "roll": f"{roll:.12f}",
                "pitch": f"{pitch:.12f}",
                "tau_pd_max_abs": f"{float(np.max(np.abs(tau_pd))):.12f}",
                "tau_wbc_max_abs": f"{max_tau_wbc_abs:.12f}",
                "tau_total_max_abs": f"{float(np.max(np.abs(tau_total))):.12f}",
                "joint_error_max_abs": f"{float(np.max(joint_error_abs)):.12f}",
                "swing_joint_error_max_abs": f"{float(np.max(joint_error_abs[swing_indices])):.12f}",
                "stance_joint_error_max_abs": f"{float(np.max(joint_error_abs[stance_indices])):.12f}",
                "swing_foot_z_min": f"{min(swing_foot_z_values):.12f}",
                "swing_foot_z_max": f"{max(swing_foot_z_values):.12f}",
                "saturated": str(saturated),
            })

            global_step += 1

        prev_target = q_target_end.copy()

    final_z = float(data.qpos[2])
    final_roll, final_pitch = quat_to_roll_pitch(data.qpos[3:7])

    pass_test = (
        min_z > MIN_Z_LIMIT
        and max_abs_roll < MAX_ROLL_LIMIT
        and max_abs_pitch < MAX_PITCH_LIMIT
        and saturation_steps == 0
        and max_joint_error < MAX_JOINT_ERROR_LIMIT
    )

    pass_margin = (
        min_z - MIN_Z_LIMIT > 0.02
        and MAX_ROLL_LIMIT - max_abs_roll > 0.005
        and MAX_PITCH_LIMIT - max_abs_pitch > 0.005
    )

    summary = {
        "mode": MODE,
        "swing_legs": ",".join(swing_legs),
        "stance_legs": ",".join(stance_legs),
        "num_knots": len(target_rows),
        "knot_hold_steps": KNOT_HOLD_STEPS,
        "total_steps": global_step,
        "kp": KP,
        "kd": KD,
        "torque_limit": TORQUE_LIMIT,
        "wbc_scale": WBC_SCALE,
        "initial_z": f"{initial_z:.12f}",
        "final_z": f"{final_z:.12f}",
        "min_z": f"{min_z:.12f}",
        "max_z": f"{max_z:.12f}",
        "delta_z": f"{final_z - initial_z:.12f}",
        "final_roll": f"{final_roll:.12f}",
        "final_pitch": f"{final_pitch:.12f}",
        "max_abs_roll": f"{max_abs_roll:.12f}",
        "roll_margin_to_0p15": f"{MAX_ROLL_LIMIT - max_abs_roll:.12f}",
        "max_abs_pitch": f"{max_abs_pitch:.12f}",
        "pitch_margin_to_0p15": f"{MAX_PITCH_LIMIT - max_abs_pitch:.12f}",
        "z_margin_to_0p22": f"{min_z - MIN_Z_LIMIT:.12f}",
        "max_tau_pd_abs": f"{max_tau_pd_abs:.12f}",
        "max_tau_wbc_abs": f"{max_tau_wbc_abs:.12f}",
        "max_tau_total_abs": f"{max_tau_total_abs:.12f}",
        "saturation_steps": saturation_steps,
        "max_joint_error": f"{max_joint_error:.12f}",
        "max_swing_joint_error": f"{max_swing_joint_error:.12f}",
        "max_stance_joint_error": f"{max_stance_joint_error:.12f}",
        "min_swing_foot_z": f"{min_swing_foot_z:.12f}",
        "max_swing_foot_z": f"{max_swing_foot_z:.12f}",
        "pass": str(pass_test),
        "pass_margin": str(pass_margin),
    }

    Path(LOG_CSV).parent.mkdir(parents=True, exist_ok=True)

    with open(LOG_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    with open(SUMMARY_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary.keys()))
        writer.writeheader()
        writer.writerow(summary)

    print("Stage 7 swing joint target tracking with WBC test")
    for k, v in summary.items():
        print(f"{k}={v}")

    print(f"saved_log={LOG_CSV}")
    print(f"saved_summary={SUMMARY_CSV}")

    if not pass_test:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
