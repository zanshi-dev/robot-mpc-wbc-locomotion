#!/usr/bin/env python3
import csv
from pathlib import Path

import mujoco
import numpy as np


INPUT_CSV = "results/logs_sample/stage07_contact_schedule_wbc_qp.csv"
LOG_CSV = "results/logs_sample/stage07_contact_schedule_wbc_support_test_log.csv"
SUMMARY_CSV = "results/logs_sample/stage07_contact_schedule_wbc_support_test_summary.csv"
SCENE = "assets/go1/scene.xml"

LEG_ORDER = ["FR", "FL", "RR", "RL"]
JOINTS = ["hip", "thigh", "calf"]
STANDING_Q_PER_LEG = [0.0, 0.9, -1.8]

KP = 80.0
KD = 2.0
TORQUE_LIMIT = 23.7
SIM_STEPS = 1000


def read_tau_by_mode():
    out = {}
    with open(INPUT_CSV, "r", newline="") as f:
        for row in csv.DictReader(f):
            mode = row["mode"]
            tau = []
            for leg in LEG_ORDER:
                for joint in JOINTS:
                    tau.append(float(row[f"{leg}_tau_{joint}"]))
            out[mode] = np.array(tau, dtype=float)
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


def run_mode(mode, tau_wbc):
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
    max_tau_wbc_abs = float(np.max(np.abs(tau_wbc)))
    max_tau_total_abs = 0.0
    saturation_steps = 0

    rows = []

    for step in range(SIM_STEPS):
        tau_pd = np.zeros(model.nu)

        for act_id in range(model.nu):
            qadr = qadrs[act_id]
            dadr = dofs[act_id]
            tau_pd[act_id] = (
                KP * (q_des[qadr] - data.qpos[qadr])
                - KD * data.qvel[dadr]
            )

        tau_total_raw = tau_pd + tau_wbc
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
        max_tau_total_abs = max(max_tau_total_abs, float(np.max(np.abs(tau_total))))

        rows.append({
            "mode": mode,
            "step": step,
            "time": f"{data.time:.9f}",
            "base_z": f"{base_z:.12f}",
            "roll": f"{roll:.12f}",
            "pitch": f"{pitch:.12f}",
            "tau_pd_max_abs": f"{float(np.max(np.abs(tau_pd))):.12f}",
            "tau_wbc_max_abs": f"{max_tau_wbc_abs:.12f}",
            "tau_total_max_abs": f"{float(np.max(np.abs(tau_total))):.12f}",
            "saturated": str(saturated),
        })

    final_z = float(data.qpos[2])

    pass_test = (
        min_z > 0.22
        and max_abs_roll < 0.15
        and max_abs_pitch < 0.15
        and saturation_steps == 0
    )

    margin_roll = 0.15 - max_abs_roll
    margin_pitch = 0.15 - max_abs_pitch
    margin_z = min_z - 0.22

    pass_margin = (
        margin_roll > 0.005
        and margin_pitch > 0.005
        and margin_z > 0.02
    )

    summary = {
        "mode": mode,
        "sim_steps": SIM_STEPS,
        "kp": KP,
        "kd": KD,
        "torque_limit": TORQUE_LIMIT,
        "initial_z": f"{initial_z:.12f}",
        "final_z": f"{final_z:.12f}",
        "min_z": f"{min_z:.12f}",
        "max_z": f"{max_z:.12f}",
        "delta_z": f"{final_z - initial_z:.12f}",
        "max_abs_roll": f"{max_abs_roll:.12f}",
        "roll_margin_to_0p15": f"{margin_roll:.12f}",
        "max_abs_pitch": f"{max_abs_pitch:.12f}",
        "pitch_margin_to_0p15": f"{margin_pitch:.12f}",
        "z_margin_to_0p22": f"{margin_z:.12f}",
        "max_tau_pd_abs": f"{max_tau_pd_abs:.12f}",
        "max_tau_wbc_abs": f"{max_tau_wbc_abs:.12f}",
        "max_tau_total_abs": f"{max_tau_total_abs:.12f}",
        "saturation_steps": saturation_steps,
        "pass": str(pass_test),
        "pass_margin": str(pass_margin),
    }

    return rows, summary


def main():
    tau_by_mode = read_tau_by_mode()

    all_log_rows = []
    summary_rows = []

    for mode in ["all_stance", "trot_FR_RL", "trot_FL_RR"]:
        rows, summary = run_mode(mode, tau_by_mode[mode])
        all_log_rows.extend(rows)
        summary_rows.append(summary)

    Path(LOG_CSV).parent.mkdir(parents=True, exist_ok=True)

    with open(LOG_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_log_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_log_rows)

    with open(SUMMARY_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    print("Stage 7 contact schedule WBC support test")
    all_pass = True
    for s in summary_rows:
        all_pass = all_pass and (s["pass"] == "True")
        print(
            f"mode={s['mode']} "
            f"final_z={s['final_z']} "
            f"min_z={s['min_z']} "
            f"max_abs_roll={s['max_abs_roll']} "
            f"roll_margin={s['roll_margin_to_0p15']} "
            f"max_abs_pitch={s['max_abs_pitch']} "
            f"max_tau_total_abs={s['max_tau_total_abs']} "
            f"saturation_steps={s['saturation_steps']} "
            f"pass={s['pass']} "
            f"pass_margin={s['pass_margin']}"
        )

    print(f"all_pass={all_pass}")
    print(f"saved_log={LOG_CSV}")
    print(f"saved_summary={SUMMARY_CSV}")

    if not all_pass:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
