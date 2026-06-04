#!/usr/bin/env python3
import csv
import mujoco
import numpy as np

SCENE = "assets/go1/scene.xml"
FORCE_CSV = "results/logs_sample/stage05_standing_contact_force_qp.csv"
OUT_CSV = "results/logs_sample/stage06_force_sign_sanity_check.csv"

LEG_ORDER = ["FR", "FL", "RR", "RL"]
STANDING_Q_PER_LEG = [0.0, 0.9, -1.8]
KP = 80.0
KD = 2.0
TORQUE_LIMIT = 23.7
SIM_STEPS = 300


def read_forces():
    forces = {}
    with open(FORCE_CSV, "r", newline="") as f:
        for row in csv.DictReader(f):
            leg = row["leg"].strip().upper()
            if leg in LEG_ORDER:
                forces[leg] = np.array([float(row["fx"]), float(row["fy"]), float(row["fz"])])
    return forces


def act_dofs(model):
    return [int(model.jnt_dofadr[int(model.actuator_trnid[i, 0])]) for i in range(model.nu)]


def set_pose(model, data):
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

    site_ids = [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, leg) for leg in LEG_ORDER]
    min_z = min(data.site_xpos[sid][2] for sid in site_ids)
    data.qpos[2] += 0.02 - min_z

    mujoco.mj_forward(model, data)
    return site_ids


def compute_jtf(model, data, site_ids, forces, sign):
    tau_full = np.zeros(model.nv)
    for leg, sid in zip(LEG_ORDER, site_ids):
        jacp = np.zeros((3, model.nv))
        jacr = np.zeros((3, model.nv))
        mujoco.mj_jacSite(model, data, jacp, jacr, sid)
        tau_full += jacp.T @ (sign * forces[leg])
    return tau_full[act_dofs(model)]


def run_case(sign_name, sign_value):
    model = mujoco.MjModel.from_xml_path(SCENE)
    data = mujoco.MjData(model)
    forces = read_forces()
    site_ids = set_pose(model, data)

    q_des = data.qpos.copy()
    tau_jtf = compute_jtf(model, data, site_ids, forces, sign_value)

    z0 = float(data.qpos[2])
    min_z = z0
    max_abs_roll = 0.0
    max_abs_pitch = 0.0
    sat_count = 0

    for _ in range(SIM_STEPS):
        q = data.qpos.copy()
        qd = data.qvel.copy()

        tau_pd = np.zeros(model.nu)
        for act_id in range(model.nu):
            jid = int(model.actuator_trnid[act_id, 0])
            qadr = int(model.jnt_qposadr[jid])
            dadr = int(model.jnt_dofadr[jid])
            tau_pd[act_id] = KP * (q_des[qadr] - q[qadr]) - KD * qd[dadr]

        tau = tau_pd + tau_jtf
        tau_clip = np.clip(tau, -TORQUE_LIMIT, TORQUE_LIMIT)
        sat_count += int(np.any(np.abs(tau) > TORQUE_LIMIT))

        data.ctrl[:] = tau_clip
        mujoco.mj_step(model, data)

        min_z = min(min_z, float(data.qpos[2]))

        quat = data.qpos[3:7]
        w, x, y, z = quat
        roll = np.arctan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
        pitch = np.arcsin(np.clip(2 * (w * y - z * x), -1.0, 1.0))
        max_abs_roll = max(max_abs_roll, abs(float(roll)))
        max_abs_pitch = max(max_abs_pitch, abs(float(pitch)))

    return {
        "sign": sign_name,
        "initial_z": z0,
        "final_z": float(data.qpos[2]),
        "min_z": min_z,
        "delta_z": float(data.qpos[2]) - z0,
        "tau_jtf_norm": float(np.linalg.norm(tau_jtf)),
        "tau_jtf_max_abs": float(np.max(np.abs(tau_jtf))),
        "max_abs_roll": max_abs_roll,
        "max_abs_pitch": max_abs_pitch,
        "saturation_steps": sat_count,
    }


def main():
    rows = [
        run_case("plus", 1.0),
        run_case("minus", -1.0),
    ]

    with open(OUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    for r in rows:
        print(r)

    print(f"saved={OUT_CSV}")


if __name__ == "__main__":
    main()
