#!/usr/bin/env python3
import csv
from pathlib import Path

import mujoco
import numpy as np


INPUT_CSV = "results/logs_sample/stage07_online_swing_trajectory_tracking_check.csv"

LOG_CSV = "results/logs_sample/stage07_online_swing_joint_target_tracking_support_test_log.csv"
SUMMARY_CSV = "results/logs_sample/stage07_online_swing_joint_target_tracking_support_test_summary.csv"

SCENE = "assets/go1/scene.xml"

LEG_ORDER = ["FR", "FL", "RR", "RL"]
JOINTS = ["hip", "thigh", "calf"]
STANDING_Q_PER_LEG = [0.0, 0.9, -1.8]

KP = 60.0
KD = 2.0
TORQUE_LIMIT = 23.7

MIN_Z_LIMIT = 0.22
MAX_ROLL_LIMIT = 0.20
MAX_PITCH_LIMIT = 0.20
MAX_JOINT_ERROR_LIMIT = 0.08


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


def current_actuated_qd(data, dofs):
    return np.array([float(data.qvel[dof]) for dof in dofs], dtype=float)


def read_targets():
    rows = []

    with open(INPUT_CSV, "r", newline="") as f:
        for row in csv.DictReader(f):
            q_des = []
            for leg in LEG_ORDER:
                for joint in JOINTS:
                    q_des.append(float(row[f"{leg}_q_{joint}"]))

            rows.append({
                "step": int(row["step"]),
                "mode": row["mode"],
                "phase_in_mode": row["phase_in_mode"],
                "swing_progress": row["swing_progress"],
                "stance_legs": row["stance_legs"],
                "swing_legs": row["swing_legs"],
                "q_des": np.array(q_des, dtype=float),
            })

    if not rows:
        raise RuntimeError(f"empty input: {INPUT_CSV}")

    return rows


def main():
    target_rows = read_targets()

    model = mujoco.MjModel.from_xml_path(SCENE)
    data = mujoco.MjData(model)

    if model.nu != 12:
        raise RuntimeError(f"期望 nu=12，实际 nu={model.nu}")

    dofs, qadrs = actuator_indices(model)
    set_standing_pose(model, data)

    initial_z = float(data.qpos[2])
    min_z = initial_z
    max_z = initial_z
    max_abs_roll = 0.0
    max_abs_pitch = 0.0

    max_tau_raw_abs = 0.0
    max_tau_total_abs = 0.0
    max_joint_error = 0.0
    max_swing_joint_error = 0.0
    max_stance_joint_error = 0.0

    saturation_steps = 0

    rows = []

    for i, target in enumerate(target_rows):
        q_des = target["q_des"]

        q_now = current_actuated_q(data, qadrs)
        qd_now = current_actuated_qd(data, dofs)

        q_err = q_des - q_now
        tau_raw = KP * q_err - KD * qd_now
        tau = np.clip(tau_raw, -TORQUE_LIMIT, TORQUE_LIMIT)

        saturated = bool(np.any(np.abs(tau_raw) > TORQUE_LIMIT))
        saturation_steps += int(saturated)

        data.ctrl[:] = tau
        mujoco.mj_step(model, data)

        base_z = float(data.qpos[2])
        roll, pitch = quat_to_roll_pitch(data.qpos[3:7])

        min_z = min(min_z, base_z)
        max_z = max(max_z, base_z)
        max_abs_roll = max(max_abs_roll, abs(roll))
        max_abs_pitch = max(max_abs_pitch, abs(pitch))

        swing_legs = target["swing_legs"].split(",") if target["swing_legs"] else []
        stance_legs = target["stance_legs"].split(",") if target["stance_legs"] else []

        swing_indices = []
        stance_indices = []
        for leg_i, leg in enumerate(LEG_ORDER):
            inds = [3 * leg_i + j for j in range(3)]
            if leg in swing_legs:
                swing_indices.extend(inds)
            if leg in stance_legs:
                stance_indices.extend(inds)

        step_joint_error = float(np.max(np.abs(q_err)))
        step_swing_joint_error = float(np.max(np.abs(q_err[swing_indices]))) if swing_indices else 0.0
        step_stance_joint_error = float(np.max(np.abs(q_err[stance_indices]))) if stance_indices else 0.0

        max_joint_error = max(max_joint_error, step_joint_error)
        max_swing_joint_error = max(max_swing_joint_error, step_swing_joint_error)
        max_stance_joint_error = max(max_stance_joint_error, step_stance_joint_error)

        max_tau_raw_abs = max(max_tau_raw_abs, float(np.max(np.abs(tau_raw))))
        max_tau_total_abs = max(max_tau_total_abs, float(np.max(np.abs(tau))))

        rows.append({
            "step": i,
            "source_step": target["step"],
            "mode": target["mode"],
            "phase_in_mode": target["phase_in_mode"],
            "swing_progress": target["swing_progress"],
            "stance_legs": target["stance_legs"],
            "swing_legs": target["swing_legs"],
            "base_z": f"{base_z:.12f}",
            "roll": f"{roll:.12f}",
            "pitch": f"{pitch:.12f}",
            "max_joint_error": f"{step_joint_error:.12f}",
            "max_swing_joint_error": f"{step_swing_joint_error:.12f}",
            "max_stance_joint_error": f"{step_stance_joint_error:.12f}",
            "tau_raw_max_abs": f"{float(np.max(np.abs(tau_raw))):.12f}",
            "tau_max_abs": f"{float(np.max(np.abs(tau))):.12f}",
            "saturated": str(saturated),
        })

    final_z = float(data.qpos[2])
    final_roll, final_pitch = quat_to_roll_pitch(data.qpos[3:7])

    pass_test = (
        min_z > MIN_Z_LIMIT
        and max_abs_roll < MAX_ROLL_LIMIT
        and max_abs_pitch < MAX_PITCH_LIMIT
        and max_joint_error < MAX_JOINT_ERROR_LIMIT
        and saturation_steps == 0
    )

    pass_margin = (
        pass_test
        and min_z - MIN_Z_LIMIT > 0.02
        and MAX_ROLL_LIMIT - max_abs_roll > 0.01
        and MAX_PITCH_LIMIT - max_abs_pitch > 0.01
    )

    summary = {
        "input_csv": INPUT_CSV,
        "total_steps": len(target_rows),
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
        "roll_margin_to_0p20": f"{MAX_ROLL_LIMIT - max_abs_roll:.12f}",
        "max_abs_pitch": f"{max_abs_pitch:.12f}",
        "pitch_margin_to_0p20": f"{MAX_PITCH_LIMIT - max_abs_pitch:.12f}",
        "z_margin_to_0p22": f"{min_z - MIN_Z_LIMIT:.12f}",
        "max_joint_error": f"{max_joint_error:.12f}",
        "max_swing_joint_error": f"{max_swing_joint_error:.12f}",
        "max_stance_joint_error": f"{max_stance_joint_error:.12f}",
        "max_tau_raw_abs": f"{max_tau_raw_abs:.12f}",
        "max_tau_total_abs": f"{max_tau_total_abs:.12f}",
        "saturation_steps": saturation_steps,
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

    print("Stage 7 online swing joint target tracking support test")
    for k, v in summary.items():
        print(f"{k}={v}")

    print(f"saved_log={LOG_CSV}")
    print(f"saved_summary={SUMMARY_CSV}")

    if not pass_test:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
