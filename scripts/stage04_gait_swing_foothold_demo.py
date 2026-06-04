import argparse
import csv
from pathlib import Path

import numpy as np


LEG_ORDER = ["FR", "FL", "RR", "RL"]

PHASE_OFFSETS = {
    "FR": 0.0,
    "FL": 0.5,
    "RR": 0.5,
    "RL": 0.0,
}

# Nominal standing foot positions from Stage 2 FK validation.
NOMINAL_FOOT_POS = {
    "FR": np.array([0.1881, -0.12675, 0.019]),
    "FL": np.array([0.1881,  0.12675, 0.019]),
    "RR": np.array([-0.1881, -0.12675, 0.019]),
    "RL": np.array([-0.1881,  0.12675, 0.019]),
}


def gait_phase(t, gait_period, phase_offset):
    return ((t / gait_period) + phase_offset) % 1.0


def is_stance(phase, duty_factor):
    return phase < duty_factor


def swing_phase_from_gait_phase(phase, duty_factor):
    if phase < duty_factor:
        return 0.0
    return (phase - duty_factor) / (1.0 - duty_factor)


def smoothstep(s):
    s = np.clip(s, 0.0, 1.0)
    return s * s * (3.0 - 2.0 * s)


def swing_trajectory(p_start, p_end, swing_phase, swing_height):
    s = np.clip(swing_phase, 0.0, 1.0)
    alpha = smoothstep(s)

    p = (1.0 - alpha) * p_start + alpha * p_end

    # Parabolic vertical clearance. Zero at start/end, max at mid-swing.
    p[2] += swing_height * 4.0 * s * (1.0 - s)
    return p


def raibert_foothold(nominal_foot_pos, v_body, v_cmd, stance_duration, kv):
    # Basic Raibert heuristic:
    # p_des = p_nominal + v_cmd * T_stance / 2 + kv * (v_body - v_cmd)
    p = nominal_foot_pos.copy()
    p[0] += v_cmd[0] * stance_duration * 0.5 + kv * (v_body[0] - v_cmd[0])
    p[1] += v_cmd[1] * stance_duration * 0.5 + kv * (v_body[1] - v_cmd[1])
    return p


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=2.0)
    parser.add_argument("--dt", type=float, default=0.01)
    parser.add_argument("--gait_period", type=float, default=0.5)
    parser.add_argument("--duty_factor", type=float, default=0.5)
    parser.add_argument("--swing_height", type=float, default=0.06)
    parser.add_argument("--vx_cmd", type=float, default=0.2)
    parser.add_argument("--vy_cmd", type=float, default=0.0)
    parser.add_argument("--vx_body", type=float, default=0.0)
    parser.add_argument("--vy_body", type=float, default=0.0)
    parser.add_argument("--kv", type=float, default=0.03)
    parser.add_argument("--log", default="results/logs_sample/stage04_gait_swing_foothold_log.csv")
    args = parser.parse_args()

    if not (0.0 < args.duty_factor < 1.0):
        raise ValueError("duty_factor must be in (0, 1).")

    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    v_cmd = np.array([args.vx_cmd, args.vy_cmd, 0.0])
    v_body = np.array([args.vx_body, args.vy_body, 0.0])
    stance_duration = args.gait_period * args.duty_factor

    print("=== Stage 4 Gait / Swing / Foothold Demo ===")
    print(f"duration = {args.duration}")
    print(f"dt = {args.dt}")
    print(f"gait_period = {args.gait_period}")
    print(f"duty_factor = {args.duty_factor}")
    print(f"stance_duration = {stance_duration}")
    print(f"swing_height = {args.swing_height}")
    print(f"v_cmd = {v_cmd}")
    print(f"v_body = {v_body}")
    print(f"kv = {args.kv}")

    # For this offline demo, each swing starts from nominal foot position
    # and lands at Raibert foothold.
    footholds = {
        leg: raibert_foothold(NOMINAL_FOOT_POS[leg], v_body, v_cmd, stance_duration, args.kv)
        for leg in LEG_ORDER
    }

    with log_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "time",
            "leg",
            "phase",
            "state",
            "contact",
            "swing_phase",
            "foot_x",
            "foot_y",
            "foot_z",
            "foothold_x",
            "foothold_y",
            "foothold_z",
        ])

        n_steps = int(args.duration / args.dt) + 1

        contact_counts = {leg: 0 for leg in LEG_ORDER}
        swing_counts = {leg: 0 for leg in LEG_ORDER}

        for k in range(n_steps):
            t = k * args.dt

            for leg in LEG_ORDER:
                phase = gait_phase(t, args.gait_period, PHASE_OFFSETS[leg])
                stance = is_stance(phase, args.duty_factor)
                contact = int(stance)
                state = "stance" if stance else "swing"

                if stance:
                    swing_phase = 0.0
                    foot_pos = NOMINAL_FOOT_POS[leg].copy()
                    contact_counts[leg] += 1
                else:
                    swing_phase = swing_phase_from_gait_phase(phase, args.duty_factor)
                    foot_pos = swing_trajectory(
                        NOMINAL_FOOT_POS[leg],
                        footholds[leg],
                        swing_phase,
                        args.swing_height,
                    )
                    swing_counts[leg] += 1

                writer.writerow([
                    t,
                    leg,
                    phase,
                    state,
                    contact,
                    swing_phase,
                    foot_pos[0],
                    foot_pos[1],
                    foot_pos[2],
                    footholds[leg][0],
                    footholds[leg][1],
                    footholds[leg][2],
                ])

            if k % max(1, int(0.1 / args.dt)) == 0:
                contacts = []
                for leg in LEG_ORDER:
                    phase = gait_phase(t, args.gait_period, PHASE_OFFSETS[leg])
                    contacts.append(int(is_stance(phase, args.duty_factor)))
                print(f"t={t:.2f} contacts[FR,FL,RR,RL]={contacts}")

    print(f"Log saved to: {log_path}")

    print("=== Contact/Swing count summary ===")
    for leg in LEG_ORDER:
        print(f"{leg}: stance_count={contact_counts[leg]}, swing_count={swing_counts[leg]}, foothold={footholds[leg]}")

    print("Stage 4 gait/swing/foothold demo finished.")


if __name__ == "__main__":
    main()
