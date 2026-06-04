#!/usr/bin/env python3
import csv
from pathlib import Path

import numpy as np


INPUT_CSV = "results/logs_sample/stage07_contact_schedule_wbc_qp.csv"
OUTPUT_CSV = "results/logs_sample/stage07_contact_mode_transition_check.csv"

LEG_ORDER = ["FR", "FL", "RR", "RL"]
JOINTS = ["hip", "thigh", "calf"]

MODE_SCALES = {
    "all_stance": 1.0,
    "trot_FR_RL": 0.6,
    "trot_FL_RR": 1.0,
}

TRANSITIONS = [
    ("all_stance", "trot_FR_RL"),
    ("trot_FR_RL", "all_stance"),
    ("all_stance", "trot_FL_RR"),
    ("trot_FL_RR", "all_stance"),
    ("trot_FR_RL", "trot_FL_RR"),
    ("trot_FL_RR", "trot_FR_RL"),
]

TORQUE_JUMP_NORM_WARN = 8.0
TORQUE_JUMP_MAX_WARN = 5.0


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

    return out


def main():
    tau_by_mode = read_tau_by_mode()

    rows = []

    for src, dst in TRANSITIONS:
        tau_src = tau_by_mode[src]
        tau_dst = tau_by_mode[dst]
        jump = tau_dst - tau_src

        jump_norm = float(np.linalg.norm(jump))
        jump_max_abs = float(np.max(np.abs(jump)))
        jump_mean_abs = float(np.mean(np.abs(jump)))

        need_smoothing = (
            jump_norm > TORQUE_JUMP_NORM_WARN
            or jump_max_abs > TORQUE_JUMP_MAX_WARN
        )

        row = {
            "src_mode": src,
            "dst_mode": dst,
            "src_scale": MODE_SCALES.get(src, 1.0),
            "dst_scale": MODE_SCALES.get(dst, 1.0),
            "jump_norm": f"{jump_norm:.12f}",
            "jump_max_abs": f"{jump_max_abs:.12f}",
            "jump_mean_abs": f"{jump_mean_abs:.12f}",
            "jump_norm_warn_threshold": TORQUE_JUMP_NORM_WARN,
            "jump_max_warn_threshold": TORQUE_JUMP_MAX_WARN,
            "need_smoothing": str(need_smoothing),
        }

        for i, leg in enumerate(LEG_ORDER):
            j = jump[3 * i:3 * i + 3]
            row[f"{leg}_jump_hip"] = f"{j[0]:.12f}"
            row[f"{leg}_jump_thigh"] = f"{j[1]:.12f}"
            row[f"{leg}_jump_calf"] = f"{j[2]:.12f}"

        rows.append(row)

    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("Stage 7 contact mode transition check")

    any_need_smoothing = False

    for row in rows:
        any_need_smoothing = any_need_smoothing or (row["need_smoothing"] == "True")
        print(
            f"{row['src_mode']} -> {row['dst_mode']} "
            f"jump_norm={row['jump_norm']} "
            f"jump_max_abs={row['jump_max_abs']} "
            f"need_smoothing={row['need_smoothing']}"
        )

    print(f"any_need_smoothing={any_need_smoothing}")
    print(f"saved={OUTPUT_CSV}")

    if any_need_smoothing:
        print("recommendation=add torque ramp or low-pass smoothing before dynamic contact switching")
    else:
        print("recommendation=direct switching acceptable for next short test")


if __name__ == "__main__":
    main()
