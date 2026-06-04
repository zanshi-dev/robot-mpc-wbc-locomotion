#!/usr/bin/env python3
import csv
from pathlib import Path

import mujoco
import numpy as np


TARGET_CSV = "results/logs_sample/stage07_swing_joint_target_sequence.csv"
LOG_CSV = "results/logs_sample/stage07_swing_tracking_mode_sequence_test_log.csv"
SUMMARY_CSV = "results/logs_sample/stage07_swing_tracking_mode_sequence_test_summary.csv"
SCENE = "assets/go1/scene.xml"

MODE_SEQUENCE = ["trot_FR_RL", "trot_FL_RR", "trot_FR_RL"]

LEG_ORDER = ["FR", "FL", "RR", "RL"]
JOINTS = ["hip", "thigh", "calf"]
STANDING_Q_PER_LEG = [0.0, 0.9, -1.8]

TARGET_SCALE = 0.25
WBC_SCALE = 0.0

KP = 60.0
KD = 2.0
TORQUE_LIMIT = 23.7
KNOT_HOLD_STEPS = 80

MAX_ROLL_LIMIT = 0.15
MAX_PITCH_LIMIT = 0.15
MIN_Z_LIMIT = 0.22
MAX_JOINT_ERROR_LIMIT = 0.10


def standing_q_vector():
    q = []
    for _leg in LEG_ORDER:
        q.extend(STANDING_Q_PER_LEG)
    return np.array(q, dtype=float)


def read_targets_by_mode():
    q_standing = standing_q_vector()
    out = {}

    with open(TARGET_CSV, "r", newline="") as f:
        for row in csv.DictReader(f):
            mode = row["mode"]

            q_target = []
            for leg in LEG_ORDER:
                for joint in JOINTS:
                    q_target.append(float(row[f"{leg}_q_{joint}"]))

            q_target = np.array(q_target, dtype=float)
            q_target = q_standing + TARGET_SCALE * (q_target - q_standing)

            out.setdefault(mode, []).append({
                "mode": mode,
                "knot": int(row["knot"]),
                "swing_legs": row["swing_legs"],
                "stance_legs": row["stance_legs"],
                "q_target": q_target,
            })

    for mode in out:
        out[mode].sort(key=lambda r: r["knot"])

    missing = [m for m in MODE_SEQUENCE if m not in out]
    if missing:
        raise RuntimeError(f"缺少这些 mode 的 target sequence: {missing}")

    return out


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


def indices_for_legs(legs):
    idx = []
    for leg in legs:
        leg_i = LEG_ORDER.index(leg)
        idx.extend([3 * leg_i + 0, 3 * leg_i + 1, 3 * leg_i + 2])
    return idx


def main():
    targets_by_mode = read_targets_by_mode()

    model = mujoco.MjModel.from_xml_path(SCENE)
    data = mujoco.MjData(model)

    if model.nu != 12:
        raise RuntimeError(f"期望 nu=12，实际 nu={model.nu}")

    dofs, qadrs = actuator_indices(model)
    site_ids = set_standing_pose(model, data)

    initial_z = float(data.qpos[2])
    min_z = initial_z
    max_z = initial_z
    max_abs_roll = 0.0
    max_abs_pitch = 0.0
    max_tau_total_abs = 0.0
    saturation_steps = 0
    max_joint_error = 0.0
    max_swing_joint_error = 0.0
    max_stance_joint_error = 0.0
    max_swing_foot_z = -1e9
    min_swing_foot_z = 1e9

    rows = []
    global_step = 0

    prev_target = current_actuated_q(data, qadrs)
    previous_mode = ""

    for segment_i, mode in enumerate(MODE_SEQUENCE):
        target_rows = targets_by_mode[mode]

        swing_legs = [x.strip() for x in target_rows[0]["swing_legs"].split(",")]
        stance_legs = [x.strip() for x in target_rows[0]["stance_legs"].split(",")]

        swing_indices = indices_for_legs(swing_legs)
        stance_indices = indices_for_legs(stance_legs)

        if previous_mode and previous_mode != mode:
            prev_target = current_actuated_q(data, qadrs)

        for target_row in target_rows:
            knot = target_row["knot"]
            q_target_end = target_row["q_target"]

            for local_step in range(KNOT_HOLD_STEPS):
                alpha = float(local_step + 1) / float(KNOT_HOLD_STEPS)
                q_des = (1.0 - alpha) * prev_target + alpha * q_target_end

                q_now = current_actuated_q(data, qadrs)
                qd_now = np.array([float(data.qvel[dof]) for dof in dofs], dtype=float)

                q_error = q_des - q_now
                tau_raw = KP * q_error - KD * qd_now
                tau_total = np.clip(tau_raw, -TORQUE_LIMIT, TORQUE_LIMIT)

                saturated = bool(np.any(np.abs(tau_raw) > TORQUE_LIMIT))
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
                    "segment_i": segment_i,
                    "mode": mode,
                    "knot": knot,
                    "knot_step": local_step,
                    "target_scale": TARGET_SCALE,
                    "wbc_scale": WBC_SCALE,
                    "time": f"{data.time:.9f}",
                    "base_z": f"{base_z:.12f}",
                    "roll": f"{roll:.12f}",
                    "pitch": f"{pitch:.12f}",
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

        previous_mode = mode

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
        pass_test
        and min_z - MIN_Z_LIMIT > 0.02
        and MAX_ROLL_LIMIT - max_abs_roll > 0.005
        and MAX_PITCH_LIMIT - max_abs_pitch > 0.005
    )

    summary = {
        "mode_sequence": "->".join(MODE_SEQUENCE),
        "target_scale": TARGET_SCALE,
        "wbc_scale": WBC_SCALE,
        "num_segments": len(MODE_SEQUENCE),
        "num_knots_per_segment": 9,
        "knot_hold_steps": KNOT_HOLD_STEPS,
        "total_steps": global_step,
        "kp": KP,
        "kd": KD,
        "torque_limit": TORQUE_LIMIT,
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

    print("Stage 7 swing tracking mode sequence test")
    for k, v in summary.items():
        print(f"{k}={v}")

    print(f"saved_log={LOG_CSV}")
    print(f"saved_summary={SUMMARY_CSV}")

    if not pass_test:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
