#!/usr/bin/env python3
import csv
from pathlib import Path


INPUT_CSV = "results/logs_sample/stage07_swing_trajectory_qp_k9.csv"
OUTPUT_CSV = "results/logs_sample/stage07_swing_joint_target_sequence.csv"

LEG_ORDER = ["FR", "FL", "RR", "RL"]
JOINTS = ["hip", "thigh", "calf"]

STANDING_Q = {
    "hip": 0.0,
    "thigh": 0.9,
    "calf": -1.8,
}

# 保守检查范围，只用于离线 sanity check
JOINT_LIMITS = {
    "hip": (-1.2, 1.2),
    "thigh": (-0.8, 2.2),
    "calf": (-2.8, -0.4),
}


def read_rows():
    with open(INPUT_CSV, "r", newline="") as f:
        return list(csv.DictReader(f))


def parse_float(row, key):
    return float(row[key])


def main():
    input_rows = read_rows()

    modes = []
    for row in input_rows:
        mode = row["mode"]
        if mode not in modes:
            modes.append(mode)

    output_rows = []
    all_pass = True

    for mode in modes:
        mode_rows = [r for r in input_rows if r["mode"] == mode]
        mode_rows.sort(key=lambda r: int(r["knot"]))

        q = {}
        for leg in LEG_ORDER:
            q[leg] = {
                "hip": STANDING_Q["hip"],
                "thigh": STANDING_Q["thigh"],
                "calf": STANDING_Q["calf"],
            }

        for row in mode_rows:
            knot = int(row["knot"])

            out = {
                "mode": mode,
                "knot": knot,
                "swing_legs": row["swing_legs"],
                "stance_legs": row["stance_legs"],
                "source_knot_pass": row["pass"],
                "source_mode_pass": row["mode_pass"],
            }

            knot_pass = True
            max_abs_delta_from_standing = 0.0

            for leg in LEG_ORDER:
                for joint in JOINTS:
                    dq_key = f"{leg}_dq_{joint}"
                    q[leg][joint] += parse_float(row, dq_key)

                    q_value = q[leg][joint]
                    lo, hi = JOINT_LIMITS[joint]
                    in_limit = lo <= q_value <= hi

                    delta_from_standing = abs(q_value - STANDING_Q[joint])
                    max_abs_delta_from_standing = max(
                        max_abs_delta_from_standing,
                        delta_from_standing,
                    )

                    out[f"{leg}_q_{joint}"] = f"{q_value:.12f}"
                    out[f"{leg}_q_{joint}_in_limit"] = str(in_limit)

                    knot_pass = knot_pass and in_limit

            out["max_abs_delta_from_standing"] = f"{max_abs_delta_from_standing:.12f}"
            out["joint_limit_pass"] = str(knot_pass)
            out["pass"] = str(knot_pass and row["pass"] == "True")

            all_pass = all_pass and (out["pass"] == "True")
            output_rows.append(out)

    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(output_rows[0].keys()))
        writer.writeheader()
        writer.writerows(output_rows)

    print("Stage 7 swing joint target sequence")
    print(f"modes={','.join(modes)}")
    print(f"num_rows={len(output_rows)}")
    print(f"all_pass={all_pass}")
    print(f"saved={OUTPUT_CSV}")

    for mode in modes:
        rows = [r for r in output_rows if r["mode"] == mode]
        last = rows[-1]
        print(
            f"mode={mode} "
            f"last_knot={last['knot']} "
            f"max_abs_delta_from_standing={last['max_abs_delta_from_standing']} "
            f"last_pass={last['pass']}"
        )

    if not all_pass:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
