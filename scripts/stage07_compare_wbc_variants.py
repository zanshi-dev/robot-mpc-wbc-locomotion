#!/usr/bin/env python3
import csv
from pathlib import Path


VARIANTS = [
    {
        "name": "base_wrench_qp",
        "qp": "results/logs_sample/stage07_wbc_base_wrench_qp.csv",
        "summary": "results/logs_sample/stage07_wbc_base_wrench_support_test_summary.csv",
        "margin": "results/logs_sample/stage07_wbc_base_wrench_support_test_margin_check.csv",
    },
    {
        "name": "posture_regularized_qp",
        "qp": "results/logs_sample/stage07_wbc_posture_regularized_qp.csv",
        "summary": "results/logs_sample/stage07_wbc_posture_regularized_support_test_summary.csv",
        "margin": "results/logs_sample/stage07_wbc_posture_regularized_support_test_margin_check.csv",
    },
]

OUT = "results/logs_sample/stage07_wbc_variant_comparison.csv"


def read_one(path):
    with open(path, "r", newline="") as f:
        return next(csv.DictReader(f))


def as_float(row, key):
    return float(row[key])


def main():
    rows = []

    for v in VARIANTS:
        qp = read_one(v["qp"])
        summary = read_one(v["summary"])
        margin = read_one(v["margin"])

        pass_main = summary["pass"] == "True"
        pass_margin = margin["pass_margin"] == "True"

        row = {
            "variant": v["name"],
            "qp_pass": qp.get("pass", ""),
            "support_pass": summary["pass"],
            "margin_pass": margin["pass_margin"],
            "tau_max_abs": qp.get("tau_max_abs", ""),
            "max_tau_total_abs": summary["max_tau_total_abs"],
            "max_abs_roll": summary["max_abs_roll"],
            "roll_margin_to_0p15": margin["roll_margin_to_0p15"],
            "max_abs_pitch": summary["max_abs_pitch"],
            "pitch_margin_to_0p15": margin["pitch_margin_to_0p15"],
            "min_z": summary["min_z"],
            "z_margin_to_0p22": margin["z_margin_to_0p22"],
            "saturation_steps": summary["saturation_steps"],
            "accepted_baseline": "False",
            "reject_reason": "",
        }

        if not pass_main:
            row["reject_reason"] = "support_test_failed"
        elif not pass_margin:
            row["reject_reason"] = "margin_check_failed"
        else:
            row["reject_reason"] = ""

        rows.append(row)

    accepted = [
        r for r in rows
        if r["support_pass"] == "True"
        and r["margin_pass"] == "True"
        and int(r["saturation_steps"]) == 0
    ]

    if not accepted:
        raise RuntimeError("没有可接受的 WBC variant")

    accepted.sort(
        key=lambda r: (
            -float(r["roll_margin_to_0p15"]),
            float(r["max_tau_total_abs"]),
        )
    )

    accepted[0]["accepted_baseline"] = "True"

    Path(OUT).parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("Stage 7 WBC variant comparison")
    for r in rows:
        print(r)

    print(f"accepted_baseline={accepted[0]['variant']}")
    print(f"saved={OUT}")


if __name__ == "__main__":
    main()
