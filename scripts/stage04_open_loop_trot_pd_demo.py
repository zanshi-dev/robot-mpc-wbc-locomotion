import argparse
import csv
from pathlib import Path

import mujoco
import numpy as np


LEG_ORDER = ["FR", "FL", "RR", "RL"]
PHASE_OFFSETS = {
    "FR": 0.0,
    "FL": 0.5,
    "RR": 0.5,
    "RL": 0.0,
}

# MuJoCo joint order: FR, FL, RR, RL.
STAND_LEG_Q = np.array([0.0, 0.9, -1.8])

# Joint-space swing perturbation:
# keep hip fixed, move thigh/calf to shorten the leg.
SWING_DELTA_Q = np.array([0.0, -0.10, 0.18])


def quat_to_roll_pitch_yaw_wxyz(q):
    w, x, y, z = q
    roll = np.arctan2(2.0 * (w * x + y * z), 1.0 - 2.0 * (x * x + y * y))
    pitch = np.arcsin(np.clip(2.0 * (w * y - z * x), -1.0, 1.0))
    yaw = np.arctan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))
    return roll, pitch, yaw


def gait_phase(t, gait_period, phase_offset):
    return ((t / gait_period) + phase_offset) % 1.0


def is_stance(phase, duty_factor):
    return phase < duty_factor


def swing_phase(phase, duty_factor):
    if phase < duty_factor:
        return 0.0
    return (phase - duty_factor) / (1.0 - duty_factor)


def smooth_lift(s):
    s = np.clip(s, 0.0, 1.0)
    return np.sin(np.pi * s)


def build_standing_q():
    return np.tile(STAND_LEG_Q, 4)


def leg_slice(leg):
    i = LEG_ORDER.index(leg)
    return slice(3 * i, 3 * i + 3)


def compute_q_des(t, gait_period, duty_factor):
    q_des = build_standing_q()
    contact = []
    phases = []
    swing_phases = []

    for leg in LEG_ORDER:
        phase = gait_phase(t, gait_period, PHASE_OFFSETS[leg])
        stance = is_stance(phase, duty_factor)
        s = swing_phase(phase, duty_factor)

        phases.append(phase)
        swing_phases.append(s)
        contact.append(int(stance))

        if not stance:
            alpha = smooth_lift(s)
            q_des[leg_slice(leg)] = STAND_LEG_Q + alpha * SWING_DELTA_Q

    return q_des, contact, phases, swing_phases


def get_contact_pairs(model, data):
    pairs = []
    for i in range(data.ncon):
        c = data.contact[i]
        g1 = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, c.geom1) or f"geom_{c.geom1}"
        g2 = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, c.geom2) or f"geom_{c.geom2}"
        pairs.append(f"{g1}<->{g2}")
    return pairs


def initialize_standing_pose(model, data, q_stand, desired_min_foot_z=0.02):
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    data.qpos[0:7] = np.array([0.0, 0.0, 0.35, 1.0, 0.0, 0.0, 0.0])
    data.qpos[7:19] = q_stand
    mujoco.mj_forward(model, data)

    foot_z = []
    for geom_name in LEG_ORDER:
        gid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, geom_name)
        if gid < 0:
            raise RuntimeError(f"Cannot find foot geom: {geom_name}")
        foot_z.append(data.geom_xpos[gid, 2])

    min_foot_z = float(np.min(foot_z))
    data.qpos[2] += desired_min_foot_z - min_foot_z
    mujoco.mj_forward(model, data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="assets/go1/scene.xml")
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--kp", type=float, default=80.0)
    parser.add_argument("--kd", type=float, default=2.0)
    parser.add_argument("--torque_limit", type=float, default=23.7)
    parser.add_argument("--gait_period", type=float, default=1.0)
    parser.add_argument("--duty_factor", type=float, default=0.75)
    parser.add_argument("--log", default="results/logs_sample/stage04_open_loop_trot_pd_log.csv")
    args = parser.parse_args()

    model_path = Path(args.model)
    if not model_path.exists():
        raise FileNotFoundError(model_path)

    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    model = mujoco.MjModel.from_xml_path(str(model_path))
    data = mujoco.MjData(model)

    trunk_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "trunk")
    if trunk_id < 0:
        raise RuntimeError("Cannot find body: trunk")

    q_stand = build_standing_q()
    initialize_standing_pose(model, data, q_stand)

    print("=== Stage 4 Open-loop Trot PD Demo ===")
    print(f"model = {model_path}")
    print(f"steps = {args.steps}")
    print(f"kp = {args.kp}, kd = {args.kd}, torque_limit = {args.torque_limit}")
    print(f"gait_period = {args.gait_period}, duty_factor = {args.duty_factor}")
    print(f"standing q = {q_stand}")
    print(f"swing delta q = {SWING_DELTA_Q}")
    print(f"initial base_z = {data.xpos[trunk_id, 2]:.6f}")

    min_base_z = 1e9
    max_abs_roll = 0.0
    max_abs_pitch = 0.0
    torque_saturation_count = 0

    with log_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "step", "time", "base_z", "roll", "pitch", "yaw",
            "torque_norm", "torque_max_abs", "torque_saturation",
            "FR_contact_cmd", "FL_contact_cmd", "RR_contact_cmd", "RL_contact_cmd",
            "FR_phase", "FL_phase", "RR_phase", "RL_phase",
            "FR_swing_phase", "FL_swing_phase", "RR_swing_phase", "RL_swing_phase",
            "n_contact", "contact_pairs",
        ])

        for step in range(args.steps):
            t = data.time

            q_des, contact_cmd, phases, swing_phases = compute_q_des(
                t, args.gait_period, args.duty_factor
            )

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

            pairs = get_contact_pairs(model, data)

            writer.writerow([
                step, data.time, base_z, roll, pitch, yaw,
                float(np.linalg.norm(tau)), float(np.max(np.abs(tau))), int(saturated),
                *contact_cmd,
                *phases,
                *swing_phases,
                data.ncon, "|".join(pairs),
            ])

            if step % 100 == 0:
                print(
                    f"step={step:04d} "
                    f"time={data.time:.3f} "
                    f"base_z={base_z:.4f} "
                    f"roll={roll:.4f} "
                    f"pitch={pitch:.4f} "
                    f"contact_cmd={contact_cmd} "
                    f"tau_max={np.max(np.abs(tau)):.4f} "
                    f"n_contact={data.ncon}"
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

    if final_base_z > 0.18 and max_abs_roll < 0.8 and max_abs_pitch < 0.8:
        print("PASS: open-loop trot leg-lift baseline remained roughly upright.")
    else:
        print("WARN/FAIL: open-loop trot baseline unstable. Reduce swing_delta, increase duty_factor, or tune kp/kd.")


if __name__ == "__main__":
    main()
