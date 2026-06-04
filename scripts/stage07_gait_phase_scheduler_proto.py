#!/usr/bin/env python3
import csv
from pathlib import Path


OUTPUT_CSV = "results/logs_sample/stage07_gait_phase_scheduler_proto.csv"
SUMMARY_CSV = "results/logs_sample/stage07_gait_phase_scheduler_proto_summary.csv"

DT = 0.002
TOTAL_STEPS = 1200

PERIOD_STEPS = 400
HALF_PERIOD_STEPS = PERIOD_STEPS // 2

MODES = {
    "trot_FR_RL": {
        "stance": ["FR", "RL"],
        "swing": ["FL", "RR"],
    },
    "trot_FL_RR": {
        "stance": ["FL", "RR"],
        "swing": ["FR", "RL"],
    },
}

EXPECTED_MODE_STEPS = {
    "trot_FR_RL": HALF_PERIOD_STEPS,
    "trot_FL_RR": HALF_PERIOD_STEPS,
}


def mode_from_phase_step(phase_step):
    if phase_step < HALF_PERIOD_STEPS:
        mode = "trot_FR_RL"
        phase_in_mode = phase_step / float(HALF_PERIOD_STEPS)
        mode_step = phase_step
    else:
        mode = "trot_FL_RR"
        mode_step = phase_step - HALF_PERIOD_STEPS
        phase_in_mode = mode_step / float(HALF_PERIOD_STEPS)

    return mode, mode_step, phase_in_mode


def main():
    rows = []
    mode_counts = {m: 0 for m in MODES}
    transitions = []
    prev_mode = None

    for step in range(TOTAL_STEPS):
        phase_step = step % PERIOD_STEPS
        cycle_i = step // PERIOD_STEPS
        phase = phase_step / float(PERIOD_STEPS)

        mode, mode_step, phase_in_mode = mode_from_phase_step(phase_step)

        if prev_mode is not None and mode != prev_mode:
            transitions.append((step, prev_mode, mode))

        prev_mode = mode
        mode_counts[mode] += 1

        rows.append({
            "step": step,
            "time": f"{step * DT:.9f}",
            "cycle_i": cycle_i,
            "phase": f"{phase:.12f}",
            "phase_step": phase_step,
            "mode": mode,
            "mode_step": mode_step,
            "phase_in_mode": f"{phase_in_mode:.12f}",
            "stance_legs": ",".join(MODES[mode]["stance"]),
            "swing_legs": ",".join(MODES[mode]["swing"]),
            "swing_progress": f"{phase_in_mode:.12f}",
            "is_transition": str(
                step == 0 or any(t[0] == step for t in transitions)
            ),
        })

    transition_count = len(transitions)

    duration_pass = all(
        mode_counts[mode] == EXPECTED_MODE_STEPS[mode] * (TOTAL_STEPS // PERIOD_STEPS)
        for mode in MODES
    )

    expected_transitions = (TOTAL_STEPS // HALF_PERIOD_STEPS) - 1
    transition_pass = transition_count == expected_transitions

    pass_test = duration_pass and transition_pass

    summary = {
        "dt": DT,
        "total_steps": TOTAL_STEPS,
        "period_steps": PERIOD_STEPS,
        "half_period_steps": HALF_PERIOD_STEPS,
        "num_cycles": TOTAL_STEPS // PERIOD_STEPS,
        "trot_FR_RL_steps": mode_counts["trot_FR_RL"],
        "trot_FL_RR_steps": mode_counts["trot_FL_RR"],
        "transition_count": transition_count,
        "expected_transitions": expected_transitions,
        "duration_pass": str(duration_pass),
        "transition_pass": str(transition_pass),
        "pass": str(pass_test),
    }

    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    with open(SUMMARY_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary.keys()))
        writer.writeheader()
        writer.writerow(summary)

    print("Stage 7 gait phase scheduler proto")
    for k, v in summary.items():
        print(f"{k}={v}")

    print(f"saved={OUTPUT_CSV}")
    print(f"saved_summary={SUMMARY_CSV}")

    if not pass_test:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
