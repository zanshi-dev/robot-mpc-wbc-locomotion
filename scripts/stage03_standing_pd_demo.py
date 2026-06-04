import argparse
import csv
from pathlib import Path

import mujoco
import numpy as np


FOOT_GEOMS = ["FR", "FL", "RR", "RL"]


def quat_to_roll_pitch_yaw_wxyz(q):
    w, x, y, z = q
    sinr_cosp = 2.0 * (w * x + y * z)
    cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
    roll = np.arctan2(sinr_cosp, cosr_cosp)

    sinp = 2.0 * (w * y - z * x)
    sinp = np.clip(sinp, -1.0, 1.0)
    pitch = np.arcsin(sinp)

    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    yaw = np.arctan2(siny_cosp, cosy_cosp)
    return roll, pitch, yaw


def get_contact_pairs(model, data):
    pairs = []
    for i in range(data.ncon):
        c = data.contact[i]
        g1 = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, c.geom1) or f"geom_{c.geom1}"
        g2 = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, c.geom2) or f"geom_{c.geom2}"
        pairs.append(f"{g1}<->{g2}")
    return pairs


def initialize_standing_pose(model, data, q_des, desired_min_foot_z=0.02):
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0

    # Floating base: x, y, z, qw, qx, qy, qz.
    data.qpos[0:7] = np.array([0.0, 0.0, 0.35, 1.0, 0.0, 0.0, 0.0])
    data.qpos[7:19] = q_des

    mujoco.mj_forward(model, data)

    foot_z = []
    for geom_name in FOOT_GEOMS:
        gid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, geom_name)
        if gid < 0:
            raise RuntimeError(f"Cannot find foot geom: {geom_name}")
        foot_z.append(data.geom_xpos[gid, 2])

    min_foot_z = float(np.min(foot_z))
    data.qpos[2] += desired_min_foot_z - min_foot_z

    mujoco.mj_forward(model, data)

    return np.array(foot_z), min_foot_z


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="assets/go1/scene.xml")
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--kp", type=float, default=80.0)
    parser.add_argument("--kd", type=float, default=2.0)
    parser.add_argument("--torque_limit", type=float, default=23.7)
    parser.add_argument("--log", default="results/logs_sample/stage03_standing_pd_log.csv")
    args = parser.parse_args()

    model_path = Path(args.model)
    if not model_path.exists():
        raise FileNotFoundError(model_path)

    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    model = mujoco.MjModel.from_xml_path(str(model_path))
    data = mujoco.MjData(model)

    if model.nu != 12:
        raise RuntimeError(f"Expected Go1 nu=12, got {model.nu}")

    trunk_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "trunk")
    if trunk_id < 0:
        raise RuntimeError("Cannot find body: trunk")

    # MuJoCo actuator/joint order: FR, FL, RR, RL.
    q_des = np.array([
        0.0, 0.9, -1.8,
        0.0, 0.9, -1.8,
        0.0, 0.9, -1.8,
        0.0, 0.9, -1.8,
    ])

    foot_z_before, min_foot_z_before = initialize_standing_pose(model, data, q_des)

    print("=== Stage 3 Standing PD v2 ===")
    print(f"model = {model_path}")
    print(f"nq={model.nq}, nv={model.nv}, nu={model.nu}")
    print(f"q_des = {q_des}")
    print(f"initial trunk z = {data.xpos[trunk_id, 2]:.6f}")
    print(f"foot_z_before_height_shift = {foot_z_before}")
    print(f"min_foot_z_before_height_shift = {min_foot_z_before:.6f}")
    print(f"kp={args.kp}, kd={args.kd}, torque_limit={args.torque_limit}")

    min_base_z = 1e9
    max_abs_roll = 0.0
    max_abs_pitch = 0.0
    torque_saturation_count = 0

    with log_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "step",
            "time",
            "base_x",
            "base_y",
            "base_z",
            "roll",
            "pitch",
            "yaw",
            "torque_norm",
            "torque_max_abs",
            "torque_saturation",
            "n_contact",
            "contact_pairs",
        ])

        for step in range(args.steps):
            q = data.qpos[7:19].copy()
            qd = data.qvel[6:18].copy()

            tau = args.kp * (q_des - q) - args.kd * qd
            tau = np.clip(tau, -args.torque_limit, args.torque_limit)

            saturated = bool(np.any(np.abs(tau) >= args.torque_limit - 1e-9))
            torque_saturation_count += int(saturated)

            data.ctrl[:] = tau
            mujoco.mj_step(model, data)

            roll, pitch, yaw = quat_to_roll_pitch_yaw_wxyz(data.qpos[3:7])
            base_z = float(data.xpos[trunk_id, 2])
            min_base_z = min(min_base_z, base_z)
            max_abs_roll = max(max_abs_roll, abs(float(roll)))
            max_abs_pitch = max(max_abs_pitch, abs(float(pitch)))

            contacts = get_contact_pairs(model, data)

            writer.writerow([
                step,
                data.time,
                data.xpos[trunk_id, 0],
                data.xpos[trunk_id, 1],
                base_z,
                roll,
                pitch,
                yaw,
                float(np.linalg.norm(tau)),
                float(np.max(np.abs(tau))),
                int(saturated),
                data.ncon,
                "|".join(contacts),
            ])

            if step % 100 == 0:
                print(
                    f"step={step:04d} "
                    f"time={data.time:.3f} "
                    f"base_z={base_z:.4f} "
                    f"roll={roll:.4f} "
                    f"pitch={pitch:.4f} "
                    f"tau_norm={np.linalg.norm(tau):.4f} "
                    f"tau_max={np.max(np.abs(tau)):.4f} "
                    f"contacts={data.ncon}"
                )

    final_base_z = float(data.xpos[trunk_id, 2])
    final_roll, final_pitch, _ = quat_to_roll_pitch_yaw_wxyz(data.qpos[3:7])

    print(f"Log saved to: {log_path}")
    print("=== Final summary ===")
    print(f"final_base_z = {final_base_z:.6f}")
    print(f"final_roll = {final_roll:.6f}")
    print(f"final_pitch = {final_pitch:.6f}")
    print(f"min_base_z = {min_base_z:.6f}")
    print(f"max_abs_roll = {max_abs_roll:.6f}")
    print(f"max_abs_pitch = {max_abs_pitch:.6f}")
    print(f"torque_saturation_count = {torque_saturation_count}")

    if final_base_z > 0.20 and max_abs_roll < 0.6 and max_abs_pitch < 0.6:
        print("PASS: robot remains roughly upright for 1000 steps.")
    else:
        print("WARN/FAIL: robot did not remain upright. Tune standing pose, kp/kd, or add gravity/feedforward support.")


if __name__ == "__main__":
    main()
