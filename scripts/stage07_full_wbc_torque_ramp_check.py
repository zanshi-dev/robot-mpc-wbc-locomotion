#!/usr/bin/env python3
import csv
from pathlib import Path

import numpy as np


INPUT_CSV = "results/logs_sample/stage07_full_wbc_torque_reconstruction_check.csv"
OUTPUT_CSV = "results/logs_sample/stage07_full_wbc_torque_ramp_check.csv"

LEG_ORDER = ["FR", "FL", "RR", "RL"]
JOINTS = ["hip", "thigh", "calf"]

RAMP_STEPS_LIST = [3, 5, 10, 20, 40]

TORQUE_JUMP_NORM_WARN = 8.0
TORQUE_JUMP_MAX_WARN = 5.0


def read_mode_torque():
    out = {}

    with open(INPUT_CSV, "r", newline="") as f:
        for row in csv.DictReader(f):
            if row["row_type"] != "mode":
                continue

            tau = []
            for leg in LEG_ORDER:
                for joint in JOINTS:
                    tau.append(float(row[f"{leg}_tau_{joint}"]))

            out[row["mode"]] = np.array(tau, dtype=float)

    required = ["trot_FR_RL", "trot_FL_RR"]
    missing = [m for m in required if m not in out]
    if missing:
        raise RuntimeError(f"缺少 mode torque: {missing}")

    return out


def main():
    tau_by_mode = read_mode_torque()

    transitions = [
        ("trot_FR_RL", "trot_FL_RR"),
        ("trot_FL_RR", "trot_FR_RL"),
    ]

    rows = []

    for ramp_steps in RAMP_STEPS_LIST:
        ramp_all_pass = True
        ramp_max_step_jump_norm = 0.0
        ramp_max_step_jump_abs = 0.0

        for from_mode, to_mode in transitions:
            direct_jump = tau_by_mode[to_mode] - tau_by_mode[from_mode]
            direct_jump_norm = float(np.linalg.norm(direct_jump))
            direct_jump_abs = float(np.max(np.abs(direct_jump)))

            step_jump = direct_jump / float(ramp_steps)
            step_jump_norm = float(np.linalg.norm(step_jump))
            step_jump_abs = float(np.max(np.abs(step_jump)))

            pass_test = (
                step_jump_norm <= TORQUE_JUMP_NORM_WARN
                and step_jump_abs <= TORQUE_JUMP_MAX_WARN
            )

            ramp_all_pass = ramp_all_pass and pass_test
            ramp_max_step_jump_norm = max(ramp_max_step_jump_norm, step_jump_norm)
            ramp_max_step_jump_abs = max(ramp_max_step_jump_abs, step_jump_abs)

            rows.append({
                "ramp_steps": ramp_steps,
                "transition": f"{from_mode}->{to_mode}",
                "direct_jump_norm": f"{direct_jump_norm:.12f}",
                "direct_jump_max_abs": f"{direct_jump_abs:.12f}",
                "step_jump_norm": f"{step_jump_norm:.12f}",
                "step_jump_max_abs": f"{step_jump_abs:.12f}",
                "threshold_jump_norm": TORQUE_JUMP_NORM_WARN,
                "threshold_jump_max_abs": TORQUE_JUMP_MAX_WARN,
                "pass": str(pass_test),
                "ramp_all_pass": str(ramp_all_pass),
            })

        for row in rows:
            if int(row["ramp_steps"]) == ramp_steps:
                row["ramp_max_step_jump_norm"] = f"{ramp_max_step_jump_norm:.12f}"
                row["ramp_max_step_jump_abs"] = f"{ramp_max_step_jump_abs:.12f}"
                row["ramp_all_pass"] = str(ramp_all_pass)

    passing_ramps = []
    for ramp_steps in RAMP_STEPS_LIST:
        ramp_rows = [r for r in rows if int(r["ramp_steps"]) == ramp_steps]
        if all(r["pass"] == "True" for r in ramp_rows):
            passing_ramps.append(ramp_steps)

    recommended_ramp_steps = min(passing_ramps) if passing_ramps else None

    for row in rows:
        row["recommended_ramp_steps"] = (
            str(recommended_ramp_steps)
            if recommended_ramp_steps is not None
            else ""
        )

    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(rows[0].keys())
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("Stage 7 full WBC torque ramp check")
    print(f"saved={OUTPUT_CSV}")
    print(f"recommended_ramp_steps={recommended_ramp_steps}")

    for ramp_steps in RAMP_STEPS_LIST:
        ramp_rows = [r for r in rows if int(r["ramp_steps"]) == ramp_steps]
        ramp_all_pass = all(r["pass"] == "True" for r in ramp_rows)
        max_step_jump_norm = max(float(r["step_jump_norm"]) for r in ramp_rows)
        max_step_jump_abs = max(float(r["step_jump_max_abs"]) for r in ramp_rows)

        print(
            f"ramp_steps={ramp_steps} "
            f"ramp_all_pass={ramp_all_pass} "
            f"max_step_jump_norm={max_step_jump_norm:.12f} "
            f"max_step_jump_abs={max_step_jump_abs:.12f}"
        )

    if recommended_ramp_steps is None:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
