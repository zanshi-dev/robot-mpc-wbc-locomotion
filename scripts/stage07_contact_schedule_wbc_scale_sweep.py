#!/usr/bin/env python3
import csv
from pathlib import Path

import mujoco
import numpy as np


INPUT_CSV = "results/logs_sample/stage07_contact_schedule_wbc_qp.csv"
OUT_CSV = "results/logs_sample/stage07_contact_schedule_wbc_scale_sweep.csv"
SCENE = "assets/go1/scene.xml"

MODE = "trot_FR_RL"
SCALES = [0.6, 0.7, 0.8, 0.9, 1.0]

LEG_ORDER = ["FR", "FL", "RR", "RL"]
JOINTS = ["hip", "thigh", "calf"]
STANDING_Q_PER_LEG = [0.0, 0.9, -1.8]

KP = 80.0
KD = 2.0
TORQUE_LIMIT = 23.7
SIM_STEPS = 1000


def read_tau(mode):
    with open(INPUT_CSV, "r", newline="") as f:
        for row in csv.DictReader(f):
            if row["mode"] == mode:
                tau = []
                for leg in LEG_ORDER:
                    for joint in JOINTS:
                        tau.append(float(row[f"{leg}_tau_{joint}"]))
                return np.array(tau, dtype=float)
    raise RuntimeError(f"找不到 mode: {mode}")


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


def run_scale(tau_base, scale):
    model = mujoco.MjModel.from_xml_path(SCENE)
    data = mujoco.MjData(model)

    dofs, qadrs = actuator_indices(model)
    set_standing_pose(model, data)
    q_des = data.qpos.copy()

    tau_wbc = scale * tau_base

    initial_z = float(data.qpos[2])
    min_z = initial_z
    max_z = initial_z
    max_abs_roll = 0.0
    max_abs_pitch = 0.0
    max_tau_pd_abs = 0.0
    max_tau_wbc_abs = float(np.max(np.abs(tau_wbc)))
    max_tau_total_abs = 0.0
    saturation_steps = 0

    for _ in range(SIM_STEPS):
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

    final_z = float(data.qpos[2])

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

    return {
        "mode": MODE,
        "scale": scale,
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
        "roll_margin_to_0p15": f"{0.15 - max_abs_roll:.12f}",
        "max_abs_pitch": f"{max_abs_pitch:.12f}",
        "pitch_margin_to_0p15": f"{0.15 - max_abs_pitch:.12f}",
        "z_margin_to_0p22": f"{min_z - 0.22:.12f}",
        "max_tau_pd_abs": f"{max_tau_pd_abs:.12f}",
        "max_tau_wbc_abs": f"{max_tau_wbc_abs:.12f}",
        "max_tau_total_abs": f"{max_tau_total_abs:.12f}",
        "saturation_steps": saturation_steps,
        "pass": str(pass_test),
        "pass_margin": str(pass_margin),
    }


def main():
    tau_base = read_tau(MODE)

    rows = [run_scale(tau_base, scale) for scale in SCALES]

    with open(OUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("Stage 7 contact schedule WBC scale sweep")
    accepted = []

    for row in rows:
        print(
            f"scale={row['scale']} "
            f"max_abs_roll={row['max_abs_roll']} "
            f"roll_margin={row['roll_margin_to_0p15']} "
            f"max_abs_pitch={row['max_abs_pitch']} "
            f"max_tau_total_abs={row['max_tau_total_abs']} "
            f"pass={row['pass']} "
            f"pass_margin={row['pass_margin']}"
        )

        if row["pass"] == "True" and row["pass_margin"] == "True":
            accepted.append(row)

    if accepted:
        best = sorted(
            accepted,
            key=lambda r: (
                -float(r["roll_margin_to_0p15"]),
                float(r["max_tau_total_abs"]),
            )
        )[0]
        print(f"recommended_scale={best['scale']}")
    else:
        print("recommended_scale=None")

    print(f"saved={OUT_CSV}")


if __name__ == "__main__":
    main()
