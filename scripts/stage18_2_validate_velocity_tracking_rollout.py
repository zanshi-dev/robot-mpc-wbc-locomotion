#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def fval(row: dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default))
    except Exception:
        return default


def bval(row: dict[str, str], key: str) -> bool:
    return str(row.get(key, "")).strip().lower() == "true"


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    root = repo_root()
    logs = root / "results" / "logs_sample"
    docs = root / "docs"

    runner = root / "scripts" / "stage18_2_velocity_tracking_rollout_runner.py"

    baseline_log = logs / "stage18_2_velocity_tracking_baseline_log.csv"
    baseline_summary = logs / "stage18_2_velocity_tracking_baseline_summary.csv"
    candidate_log = logs / "stage18_2_velocity_tracking_mpc_assisted_candidate_log.csv"
    candidate_summary = logs / "stage18_2_velocity_tracking_mpc_assisted_candidate_summary.csv"

    validation_csv = logs / "stage18_2_velocity_tracking_rollout_validation.csv"
    comparison_csv = logs / "stage18_2_velocity_tracking_rollout_comparison.csv"
    summary_json = logs / "stage18_2_velocity_tracking_rollout_summary.json"
    doc = docs / "STAGE18_2_VELOCITY_TRACKING_ROLLOUT.md"

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    required_files = [
        runner,
        baseline_log,
        baseline_summary,
        candidate_log,
        candidate_summary,
    ]

    for path in required_files:
        check(f"exists::{path.name}", path.is_file() and path.stat().st_size > 0, str(path.relative_to(root)))

    baseline_log_rows = read_rows(baseline_log)
    baseline_summary_rows = read_rows(baseline_summary)
    candidate_log_rows = read_rows(candidate_log)
    candidate_summary_rows = read_rows(candidate_summary)

    check("baseline_log_rows_2400", len(baseline_log_rows) == 2400, f"rows={len(baseline_log_rows)}")
    check("candidate_log_rows_2400", len(candidate_log_rows) == 2400, f"rows={len(candidate_log_rows)}")
    check("baseline_summary_one_row", len(baseline_summary_rows) == 1, f"rows={len(baseline_summary_rows)}")
    check("candidate_summary_one_row", len(candidate_summary_rows) == 1, f"rows={len(candidate_summary_rows)}")

    required_log_cols = [
        "base_x",
        "base_y",
        "base_vx_fd",
        "base_vy_fd",
        "base_vx_qvel",
        "target_vx",
        "velocity_error",
        "base_z",
        "roll",
        "pitch",
    ]
    required_summary_cols = [
        "target_vx",
        "initial_x",
        "final_x",
        "forward_displacement",
        "mean_vx",
        "mean_abs_velocity_error",
        "max_abs_velocity_error",
        "min_z",
        "max_abs_roll",
        "max_abs_pitch",
        "qp_fail_steps",
        "saturation_steps",
        "pass",
    ]

    baseline_log_cols = set(baseline_log_rows[0].keys()) if baseline_log_rows else set()
    candidate_log_cols = set(candidate_log_rows[0].keys()) if candidate_log_rows else set()
    baseline_summary_cols = set(baseline_summary_rows[0].keys()) if baseline_summary_rows else set()
    candidate_summary_cols = set(candidate_summary_rows[0].keys()) if candidate_summary_rows else set()

    for col in required_log_cols:
        check(f"baseline_log_has::{col}", col in baseline_log_cols, col)
        check(f"candidate_log_has::{col}", col in candidate_log_cols, col)

    for col in required_summary_cols:
        check(f"baseline_summary_has::{col}", col in baseline_summary_cols, col)
        check(f"candidate_summary_has::{col}", col in candidate_summary_cols, col)

    comparison_rows: list[dict[str, str]] = []
    for name, rows, summary_rows in [
        ("baseline", baseline_log_rows, baseline_summary_rows),
        ("mpc_assisted_candidate", candidate_log_rows, candidate_summary_rows),
    ]:
        summary = summary_rows[0] if summary_rows else {}

        min_z = fval(summary, "min_z", -1.0)
        max_abs_roll = fval(summary, "max_abs_roll", 999.0)
        max_abs_pitch = fval(summary, "max_abs_pitch", 999.0)
        qp_fail_steps = fval(summary, "qp_fail_steps", 999.0)
        saturation_steps = fval(summary, "saturation_steps", 999.0)
        mean_vx = fval(summary, "mean_vx", 0.0)
        mean_abs_velocity_error = fval(summary, "mean_abs_velocity_error", 0.0)
        forward_displacement = fval(summary, "forward_displacement", 0.0)
        target_vx = fval(summary, "target_vx", 0.0)

        check(f"{name}_summary_pass_true", bval(summary, "pass"), str(summary.get("pass")))
        check(f"{name}_min_z_above_0p22", min_z > 0.22, f"min_z={min_z}")
        check(f"{name}_roll_under_0p20", max_abs_roll < 0.20, f"max_abs_roll={max_abs_roll}")
        check(f"{name}_pitch_under_0p20", max_abs_pitch < 0.20, f"max_abs_pitch={max_abs_pitch}")
        check(f"{name}_qp_fail_zero", qp_fail_steps == 0, f"qp_fail_steps={qp_fail_steps}")
        check(f"{name}_saturation_zero", saturation_steps == 0, f"saturation_steps={saturation_steps}")
        check(f"{name}_target_vx_recorded", abs(target_vx - 0.2) < 1e-9, f"target_vx={target_vx}")

        comparison_rows.append({
            "control_mode": name,
            "target_vx": f"{target_vx:.6f}",
            "mean_vx": f"{mean_vx:.6f}",
            "mean_abs_velocity_error": f"{mean_abs_velocity_error:.6f}",
            "forward_displacement": f"{forward_displacement:.6f}",
            "min_z": f"{min_z:.6f}",
            "max_abs_roll": f"{max_abs_roll:.6f}",
            "max_abs_pitch": f"{max_abs_pitch:.6f}",
            "qp_fail_steps": str(int(qp_fail_steps)),
            "saturation_steps": str(int(saturation_steps)),
            "pass": str(bval(summary, "pass")),
        })

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    write_csv(validation_csv, checks, ["check", "status", "detail"])
    write_csv(
        comparison_csv,
        comparison_rows,
        [
            "control_mode",
            "target_vx",
            "mean_vx",
            "mean_abs_velocity_error",
            "forward_displacement",
            "min_z",
            "max_abs_roll",
            "max_abs_pitch",
            "qp_fail_steps",
            "saturation_steps",
            "pass",
        ],
    )

    summary = {
        "stage": "18.2",
        "name": "velocity tracking rollout",
        "result": result,
        "failure_count": failure_count,
        "source_runner": "scripts/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_runner.py",
        "derived_runner": "scripts/stage18_2_velocity_tracking_rollout_runner.py",
        "target_vx": 0.2,
        "comparison_rows": comparison_rows,
        "generated_files": [
            str(validation_csv.relative_to(root)),
            str(comparison_csv.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(doc.relative_to(root)),
        ],
        "claim_boundary": [
            "simulation-only velocity evidence",
            "finite-difference base velocity from qpos[0]",
            "no real robot torque execution",
            "no hardware torque enablement",
            "no claim that MPC/WBC comprehensively outperforms baseline",
        ],
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    doc.write_text(f"""# Stage 18.2: Velocity Tracking Rollout

## 1. Goal

Stage 18.2 derives a velocity-tracking evidence runner from the Stage 14.5d MPC-assisted candidate runner.

The derived runner adds per-step velocity evidence:

    base_x
    base_y
    base_vx_fd
    base_vy_fd
    base_vx_qvel
    target_vx
    velocity_error

It also adds summary metrics:

    mean_vx
    mean_abs_velocity_error
    max_abs_velocity_error
    final_x
    forward_displacement

## 2. Result

Stage 18.2 result: {result}

Failure count: {failure_count}

## 3. Comparison Table

See:

    results/logs_sample/stage18_2_velocity_tracking_rollout_comparison.csv

## 4. Claim Boundary

Stage 18.2 provides simulation-only velocity evidence. It does not claim hardware torque execution, real robot deployment, or comprehensive MPC/WBC superiority over the baseline.
""", encoding="utf-8")

    print(f"stage18_2_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"comparison: {comparison_csv.relative_to(root)}")
    print(f"summary: {summary_json.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
