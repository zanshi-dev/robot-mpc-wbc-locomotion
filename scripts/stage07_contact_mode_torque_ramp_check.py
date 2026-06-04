#!/usr/bin/env python3
import csv
from pathlib import Path

import numpy as np


INPUT_CSV = "results/logs_sample/stage07_contact_schedule_wbc_qp.csv"
OUTPUT_CSV = "results/logs_sample/stage07_contact_mode_torque_ramp_check.csv"

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

RAMP_STEPS_LIST = [5, 10, 20, 40]

JUMP_NORM_THRESHOLD = 8.0
JUMP_MAX_THRESHOLD = 5.0


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
        direct_jump = tau_dst - tau_src

        direct_jump_norm = float(np.linalg.norm(direct_jump))
        direct_jump_max_abs = float(np.max(np.abs(direct_jump)))

        for ramp_steps in RAMP_STEPS_LIST:
            step_jump = direct_jump / ramp_steps
            step_jump_norm = float(np.linalg.norm(step_jump))
            step_jump_max_abs = float(np.max(np.abs(step_jump)))

            pass_step = (
                step_jump_norm <= JUMP_NORM_THRESHOLD
                and step_jump_max_abs <= JUMP_MAX_THRESHOLD
            )

            row = {
                "src_mode": src,
                "dst_mode": dst,
                "src_scale": MODE_SCALES.get(src, 1.0),
                "dst_scale": MODE_SCALES.get(dst, 1.0),
                "ramp_steps": ramp_steps,
                "direct_jump_norm": f"{direct_jump_norm:.12f}",
                "direct_jump_max_abs": f"{direct_jump_max_abs:.12f}",
                "step_jump_norm": f"{step_jump_norm:.12f}",
                "step_jump_max_abs": f"{step_jump_max_abs:.12f}",
                "jump_norm_threshold": JUMP_NORM_THRESHOLD,
                "jump_max_threshold": JUMP_MAX_THRESHOLD,
                "pass": str(pass_step),
            }

            rows.append(row)

    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("Stage 7 contact mode torque ramp check")

    recommended = None

    for ramp_steps in RAMP_STEPS_LIST:
        subset = [r for r in rows if int(r["ramp_steps"]) == ramp_steps]
        all_pass = all(r["pass"] == "True" for r in subset)

        max_step_jump_norm = max(float(r["step_jump_norm"]) for r in subset)
        max_step_jump_abs = max(float(r["step_jump_max_abs"]) for r in subset)

        print(
            f"ramp_steps={ramp_steps} "
            f"all_pass={all_pass} "
            f"max_step_jump_norm={max_step_jump_norm:.12f} "
            f"max_step_jump_abs={max_step_jump_abs:.12f}"
        )

        if all_pass and recommended is None:
            recommended = ramp_steps

    print(f"recommended_ramp_steps={recommended}")
    print(f"saved={OUTPUT_CSV}")

    if recommended is None:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
