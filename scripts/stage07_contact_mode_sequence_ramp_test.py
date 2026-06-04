#!/usr/bin/env python3
import csv
from pathlib import Path

import mujoco
import numpy as np


INPUT_CSV = "results/logs_sample/stage07_contact_schedule_wbc_qp.csv"
LOG_CSV = "results/logs_sample/stage07_contact_mode_sequence_ramp_test_log.csv"
SUMMARY_CSV = "results/logs_sample/stage07_contact_mode_sequence_ramp_test_summary.csv"
SCENE = "assets/go1/scene.xml"

LEG_ORDER = ["FR", "FL", "RR", "RL"]
JOINTS = ["hip", "thigh", "calf"]
STANDING_Q_PER_LEG = [0.0, 0.9, -1.8]

MODE_SCALES = {
    "all_stance": 1.0,
    "trot_FR_RL": 0.6,
    "trot_FL_RR": 1.0,
}

SEQUENCE = [
    ("all_stance", 300),
    ("trot_FR_RL", 300),
    ("all_stance", 300),
    ("trot_FL_RR", 300),
    ("all_stance", 300),
]

KP = 80.0
KD = 2.0
TORQUE_LIMIT = 23.7
RAMP_STEPS = 5


def read_tau_by_mode():
    out = {}

    with open(INPUT_CSV, "r", newline="") as f:
        for row in csv.DictReader(f):
            mode = row["mode"]
            tau = []

            for leg in LEG_ORDER:
                for joint in JOINTS:
                    tau.append(float(row[f"{leg}_tau_{joint}"]))

            scale = MODE_SCALES.get(mode, 1.0)
            out[mode] = scale * np.array(tau, dtype=float)

    missing = [mode for mode, _ in SEQUENCE if mode not in out]
    if missing:
        raise RuntimeError(f"缺少这些 mode 的 torque: {missing}")

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

    site_ids = []
    for leg in LEG_ORDER:
        sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, leg)
        if sid < 0:
            raise RuntimeError(f"找不到 foot site: {leg}")
        site_ids.append(sid)

    min_foot_z = min(float(data.site_xpos[sid][2]) for sid in site_ids)
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


def main():
    tau_by_mode = read_tau_by_mode()

    model = mujoco.MjModel.from_xml_path(SCENE)
    data = mujoco.MjData(model)

    if model.nu != 12:
        raise RuntimeError(f"期望 nu=12，实际 nu={model.nu}")

    dofs, qadrs = actuator_indices(model)
    set_standing_pose(model, data)
    q_des = data.qpos.copy()

    initial_z = float(data.qpos[2])
    min_z = initial_z
    max_z = initial_z
    max_abs_roll = 0.0
    max_abs_pitch = 0.0
    max_tau_pd_abs = 0.0
    max_tau_wbc_cmd_abs = 0.0
    max_tau_total_abs = 0.0
    saturation_steps = 0

    max_cmd_step_jump_norm = 0.0
    max_cmd_step_jump_abs = 0.0

    rows = []

    global_step = 0
    prev_mode = None
    tau_cmd = None
    tau_prev_cmd = None

    for segment_i, (mode, segment_steps) in enumerate(SEQUENCE):
        tau_target = tau_by_mode[mode]

        if tau_cmd is None:
            tau_cmd = tau_target.copy()
            ramp_start = tau_target.copy()
            ramping = False
        elif mode != prev_mode:
            ramp_start = tau_cmd.copy()
            ramping = True
        else:
            ramp_start = tau_target.copy()
            ramping = False

        for local_step in range(segment_steps):
            if ramping and local_step < RAMP_STEPS:
                alpha = float(local_step + 1) / float(RAMP_STEPS)
                tau_wbc_cmd = (1.0 - alpha) * ramp_start + alpha * tau_target
                ramp_active = True
            else:
                tau_wbc_cmd = tau_target.copy()
                ramp_active = False

            if tau_prev_cmd is not None:
                cmd_jump = tau_wbc_cmd - tau_prev_cmd
                max_cmd_step_jump_norm = max(
                    max_cmd_step_jump_norm,
                    float(np.linalg.norm(cmd_jump)),
                )
                max_cmd_step_jump_abs = max(
                    max_cmd_step_jump_abs,
                    float(np.max(np.abs(cmd_jump))),
                )

            tau_prev_cmd = tau_wbc_cmd.copy()
            tau_cmd = tau_wbc_cmd.copy()

            tau_pd = np.zeros(model.nu)

            for act_id in range(model.nu):
                qadr = qadrs[act_id]
                dadr = dofs[act_id]
                tau_pd[act_id] = (
                    KP * (q_des[qadr] - data.qpos[qadr])
                    - KD * data.qvel[dadr]
                )

            tau_total_raw = tau_pd + tau_wbc_cmd
            tau_total = np.clip(tau_total_raw, -TORQUE_LIMIT, TORQUE_LIMIT)

            saturated = bool(np.any(np.abs(tau_total_raw) > TORQUE_LIMIT))
            saturation_steps += int(saturated)

            data.ctrl[:] = tau_total
            mujoco.mj_step(model, data)

            base_z = float(data.qpos[2])
            roll, pitch = quat_to_roll_pitch(data.qpos[3:7])

            min_z = min(min_z, base_z)
            max_z = max(max_z, base_z)
            max_abs_roll = max(max_abs_roll, abs(roll))
            max_abs_pitch = max(max_abs_pitch, abs(pitch))
            max_tau_pd_abs = max(max_tau_pd_abs, float(np.max(np.abs(tau_pd))))
            max_tau_wbc_cmd_abs = max(max_tau_wbc_cmd_abs, float(np.max(np.abs(tau_wbc_cmd))))
            max_tau_total_abs = max(max_tau_total_abs, float(np.max(np.abs(tau_total))))

            rows.append({
                "step": global_step,
                "segment_i": segment_i,
                "segment_step": local_step,
                "mode": mode,
                "mode_scale": MODE_SCALES.get(mode, 1.0),
                "ramp_active": str(ramp_active),
                "time": f"{data.time:.9f}",
                "base_z": f"{base_z:.12f}",
                "roll": f"{roll:.12f}",
                "pitch": f"{pitch:.12f}",
                "tau_pd_max_abs": f"{float(np.max(np.abs(tau_pd))):.12f}",
                "tau_wbc_cmd_max_abs": f"{float(np.max(np.abs(tau_wbc_cmd))):.12f}",
                "tau_total_max_abs": f"{float(np.max(np.abs(tau_total))):.12f}",
                "saturated": str(saturated),
            })

            global_step += 1

        prev_mode = mode

    final_z = float(data.qpos[2])
    final_roll, final_pitch = quat_to_roll_pitch(data.qpos[3:7])

    pass_test = (
        min_z > 0.22
        and max_abs_roll < 0.15
        and max_abs_pitch < 0.15
        and saturation_steps == 0
    )

    pass_margin = (
        0.15 - max_abs_roll > 0.005
        and 0.15 - max_abs_pitch > 0.005
        and min_z - 0.22 > 0.02
    )

    summary = {
        "sequence": "all_stance->trot_FR_RL->all_stance->trot_FL_RR->all_stance",
        "segment_steps": 300,
        "total_steps": global_step,
        "ramp_steps": RAMP_STEPS,
        "kp": KP,
        "kd": KD,
        "torque_limit": TORQUE_LIMIT,
        "scale_all_stance": MODE_SCALES["all_stance"],
        "scale_trot_FR_RL": MODE_SCALES["trot_FR_RL"],
        "scale_trot_FL_RR": MODE_SCALES["trot_FL_RR"],
        "initial_z": f"{initial_z:.12f}",
        "final_z": f"{final_z:.12f}",
        "min_z": f"{min_z:.12f}",
        "max_z": f"{max_z:.12f}",
        "delta_z": f"{final_z - initial_z:.12f}",
        "final_roll": f"{final_roll:.12f}",
        "final_pitch": f"{final_pitch:.12f}",
        "max_abs_roll": f"{max_abs_roll:.12f}",
        "roll_margin_to_0p15": f"{0.15 - max_abs_roll:.12f}",
        "max_abs_pitch": f"{max_abs_pitch:.12f}",
        "pitch_margin_to_0p15": f"{0.15 - max_abs_pitch:.12f}",
        "z_margin_to_0p22": f"{min_z - 0.22:.12f}",
        "max_tau_pd_abs": f"{max_tau_pd_abs:.12f}",
        "max_tau_wbc_cmd_abs": f"{max_tau_wbc_cmd_abs:.12f}",
        "max_tau_total_abs": f"{max_tau_total_abs:.12f}",
        "max_cmd_step_jump_norm": f"{max_cmd_step_jump_norm:.12f}",
        "max_cmd_step_jump_abs": f"{max_cmd_step_jump_abs:.12f}",
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

    print("Stage 7 contact mode sequence ramp test")
    for k, v in summary.items():
        print(f"{k}={v}")

    print(f"saved_log={LOG_CSV}")
    print(f"saved_summary={SUMMARY_CSV}")

    if not pass_test:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
