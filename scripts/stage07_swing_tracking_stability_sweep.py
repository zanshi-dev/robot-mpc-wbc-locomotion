#!/usr/bin/env python3
import csv
from pathlib import Path

import mujoco
import numpy as np


TARGET_CSV = "results/logs_sample/stage07_swing_joint_target_sequence.csv"
WBC_CSV = "results/logs_sample/stage07_contact_schedule_wbc_qp.csv"
OUTPUT_CSV = "results/logs_sample/stage07_swing_tracking_stability_sweep.csv"
SCENE = "assets/go1/scene.xml"

MODE = "trot_FR_RL"

LEG_ORDER = ["FR", "FL", "RR", "RL"]
JOINTS = ["hip", "thigh", "calf"]
STANDING_Q_PER_LEG = [0.0, 0.9, -1.8]

KP_LIST = [60.0, 80.0]
KD_LIST = [2.0, 4.0, 6.0]
WBC_SCALE_LIST = [0.0, 0.2, 0.4, 0.6]
TARGET_SCALE_LIST = [0.25, 0.5, 0.75, 1.0]

TORQUE_LIMIT = 23.7
KNOT_HOLD_STEPS = 80

MAX_ROLL_LIMIT = 0.15
MAX_PITCH_LIMIT = 0.15
MIN_Z_LIMIT = 0.22
MAX_JOINT_ERROR_LIMIT = 0.10


def standing_q_vector():
    out = []
    for _leg in LEG_ORDER:
        out.extend(STANDING_Q_PER_LEG)
    return np.array(out, dtype=float)


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
                continue

            tau = []
            for leg in LEG_ORDER:
                for joint in JOINTS:
                    tau.append(float(row[f"{leg}_tau_{joint}"]))

            return np.array(tau, dtype=float)

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


def run_case(target_rows, tau_wbc_base, kp, kd, wbc_scale, target_scale):
    model = mujoco.MjModel.from_xml_path(SCENE)
    data = mujoco.MjData(model)

    if model.nu != 12:
        raise RuntimeError(f"期望 nu=12，实际 nu={model.nu}")

    dofs, qadrs = actuator_indices(model)
    site_ids = set_standing_pose(model, data)

    q_standing = standing_q_vector()
    tau_wbc = wbc_scale * tau_wbc_base

    scaled_targets = []
    for r in target_rows:
        scaled_targets.append({
            **r,
            "q_target": q_standing + target_scale * (r["q_target"] - q_standing),
        })

    prev_target = current_actuated_q(data, qadrs)

    swing_legs = [x.strip() for x in scaled_targets[0]["swing_legs"].split(",")]
    stance_legs = [x.strip() for x in scaled_targets[0]["stance_legs"].split(",")]

    swing_indices = []
    stance_indices = []

    for leg in swing_legs:
        leg_i = LEG_ORDER.index(leg)
        swing_indices.extend([3 * leg_i + 0, 3 * leg_i + 1, 3 * leg_i + 2])

    for leg in stance_legs:
        leg_i = LEG_ORDER.index(leg)
        stance_indices.extend([3 * leg_i + 0, 3 * leg_i + 1, 3 * leg_i + 2])

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

    total_steps = 0

    for target_row in scaled_targets:
        q_target_end = target_row["q_target"]

        for local_step in range(KNOT_HOLD_STEPS):
            alpha = float(local_step + 1) / float(KNOT_HOLD_STEPS)
            q_des = (1.0 - alpha) * prev_target + alpha * q_target_end

            q_now = current_actuated_q(data, qadrs)
            qd_now = np.array([float(data.qvel[dof]) for dof in dofs], dtype=float)

            q_error = q_des - q_now

            tau_pd = kp * q_error - kd * qd_now
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

            for leg in swing_legs:
                z = float(data.site_xpos[site_ids[leg]][2])
                max_swing_foot_z = max(max_swing_foot_z, z)
                min_swing_foot_z = min(min_swing_foot_z, z)

            total_steps += 1

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

    return {
        "mode": MODE,
        "target_scale": target_scale,
        "wbc_scale": wbc_scale,
        "kp": kp,
        "kd": kd,
        "num_knots": len(target_rows),
        "knot_hold_steps": KNOT_HOLD_STEPS,
        "total_steps": total_steps,
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


def score_row(row):
    # 用于推荐：优先 pass_margin，其次 pass，再最小 roll/pitch，再较大 target_scale
    return (
        row["pass_margin"] == "True",
        row["pass"] == "True",
        -float(row["max_abs_roll"]),
        -float(row["max_abs_pitch"]),
        float(row["target_scale"]),
        -float(row["max_joint_error"]),
    )


def main():
    target_rows = read_targets()
    tau_wbc_base = read_wbc_tau()

    rows = []

    for target_scale in TARGET_SCALE_LIST:
        for wbc_scale in WBC_SCALE_LIST:
            for kp in KP_LIST:
                for kd in KD_LIST:
                    rows.append(
                        run_case(
                            target_rows=target_rows,
                            tau_wbc_base=tau_wbc_base,
                            kp=kp,
                            kd=kd,
                            wbc_scale=wbc_scale,
                            target_scale=target_scale,
                        )
                    )

    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    pass_rows = [r for r in rows if r["pass"] == "True"]
    pass_margin_rows = [r for r in rows if r["pass_margin"] == "True"]

    print("Stage 7 swing tracking stability sweep")
    print(f"num_cases={len(rows)}")
    print(f"pass_cases={len(pass_rows)}")
    print(f"pass_margin_cases={len(pass_margin_rows)}")
    print(f"saved={OUTPUT_CSV}")

    if pass_rows:
        recommended = sorted(pass_rows, key=score_row, reverse=True)[0]
        print("recommended:")
        for k in [
            "target_scale",
            "wbc_scale",
            "kp",
            "kd",
            "max_abs_roll",
            "max_abs_pitch",
            "min_z",
            "max_joint_error",
            "max_tau_total_abs",
            "pass",
            "pass_margin",
        ]:
            print(f"{k}={recommended[k]}")
    else:
        best = sorted(rows, key=score_row, reverse=True)[0]
        print("no pass case; best candidate:")
        for k in [
            "target_scale",
            "wbc_scale",
            "kp",
            "kd",
            "max_abs_roll",
            "max_abs_pitch",
            "min_z",
            "max_joint_error",
            "max_tau_total_abs",
            "pass",
            "pass_margin",
        ]:
            print(f"{k}={best[k]}")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
