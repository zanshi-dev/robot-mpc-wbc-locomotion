#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def file_nonempty(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 0


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def fval(row: dict[str, str], key: str, default: float | None = None) -> float | None:
    try:
        return float(row[key])
    except Exception:
        return default


def bval(row: dict[str, str], key: str) -> bool:
    return str(row.get(key, "")).strip().lower() == "true"


def write_validation_csv(path: Path, checks: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "status", "detail"])
        writer.writeheader()
        writer.writerows(checks)


def main() -> int:
    root = repo_root()
    log_dir = root / "results" / "logs_sample"
    log_dir.mkdir(parents=True, exist_ok=True)

    candidate_log = log_dir / "stage14_5e_r1_scale_0p02_candidate_log.csv"
    candidate_summary = log_dir / "stage14_5e_r1_scale_0p02_candidate_summary.csv"
    baseline_summary = log_dir / "stage14_5e_r1_scale_0p00_baseline_reference_summary.csv"
    sweep_table = log_dir / "stage14_5e_r1_candidate_robustness_scale_sweep_table.csv"
    ab_summary = log_dir / "stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_summary.csv"

    validation_csv = log_dir / "stage17_1_conservative_closed_loop_rollout_validation.csv"
    summary_json = log_dir / "stage17_1_conservative_closed_loop_rollout_summary.json"
    validation_log = log_dir / "stage17_1_conservative_closed_loop_rollout_validation.log"

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    source_files = [
        candidate_log,
        candidate_summary,
        baseline_summary,
        sweep_table,
        ab_summary,
    ]

    for path in source_files:
        check(
            f"source_exists::{path.name}",
            file_nonempty(path),
            str(path.relative_to(root)),
        )

    candidate_log_rows = read_csv_rows(candidate_log)
    candidate_summary_rows = read_csv_rows(candidate_summary)
    baseline_summary_rows = read_csv_rows(baseline_summary)
    sweep_rows = read_csv_rows(sweep_table)

    check("candidate_log_has_rows", len(candidate_log_rows) == 2400, f"rows={len(candidate_log_rows)}")
    check("candidate_summary_has_one_row", len(candidate_summary_rows) == 1, f"rows={len(candidate_summary_rows)}")
    check("baseline_summary_has_one_row", len(baseline_summary_rows) == 1, f"rows={len(baseline_summary_rows)}")
    check("sweep_table_has_four_rows", len(sweep_rows) == 4, f"rows={len(sweep_rows)}")

    candidate = candidate_summary_rows[0] if candidate_summary_rows else {}
    baseline = baseline_summary_rows[0] if baseline_summary_rows else {}

    total_steps = fval(candidate, "total_steps", -1)
    scale = fval(candidate, "mpc_assisted_candidate_scale", -1)
    min_z = fval(candidate, "min_z", -1)
    max_abs_roll = fval(candidate, "max_abs_roll", 999)
    max_abs_pitch = fval(candidate, "max_abs_pitch", 999)
    max_tau_total_abs = fval(candidate, "max_tau_total_abs", -1)
    max_tau_candidate_scaled_abs = fval(candidate, "max_tau_candidate_scaled_abs", -1)
    torque_limit = fval(candidate, "torque_limit", -1)
    qp_fail_steps = fval(candidate, "qp_fail_steps", 999)
    saturation_steps = fval(candidate, "saturation_steps", 999)

    baseline_min_z = fval(baseline, "min_z", -1)
    baseline_max_abs_roll = fval(baseline, "max_abs_roll", 999)
    baseline_max_abs_pitch = fval(baseline, "max_abs_pitch", 999)

    check(
        "control_mode_is_candidate",
        candidate.get("control_mode") == "mpc_assisted_candidate",
        f"control_mode={candidate.get('control_mode')}",
    )
    check(
        "simulation_only_project",
        bval(candidate, "simulation_only_project") is True,
        f"simulation_only_project={candidate.get('simulation_only_project')}",
    )
    check(
        "no_hardware_torque_commanded",
        bval(candidate, "real_robot_torque_commanded") is False,
        f"real_robot_torque_commanded={candidate.get('real_robot_torque_commanded')}",
    )
    check(
        "no_ros_publisher_used",
        bval(candidate, "ros_publisher_used") is False,
        f"ros_publisher_used={candidate.get('ros_publisher_used')}",
    )
    check(
        "candidate_executed",
        bval(candidate, "mpc_assisted_candidate_executed") is True,
        f"mpc_assisted_candidate_executed={candidate.get('mpc_assisted_candidate_executed')}",
    )
    check(
        "candidate_scale_is_conservative_0p02",
        abs(scale - 0.02) < 1e-9,
        f"scale={scale}",
    )
    check(
        "total_steps_2400",
        total_steps == 2400,
        f"total_steps={total_steps}",
    )
    check(
        "height_margin_min_z_above_0p22",
        min_z is not None and min_z > 0.22,
        f"min_z={min_z}",
    )
    check(
        "roll_bounded_under_0p20",
        max_abs_roll is not None and max_abs_roll < 0.20,
        f"max_abs_roll={max_abs_roll}",
    )
    check(
        "pitch_bounded_under_0p20",
        max_abs_pitch is not None and max_abs_pitch < 0.20,
        f"max_abs_pitch={max_abs_pitch}",
    )
    check(
        "qp_fail_steps_zero",
        qp_fail_steps == 0,
        f"qp_fail_steps={qp_fail_steps}",
    )
    check(
        "saturation_steps_zero",
        saturation_steps == 0,
        f"saturation_steps={saturation_steps}",
    )
    check(
        "candidate_summary_pass_true",
        bval(candidate, "pass") is True,
        f"pass={candidate.get('pass')}",
    )
    check(
        "torque_metric_available",
        max_tau_total_abs is not None and max_tau_total_abs >= 0,
        f"max_tau_total_abs={max_tau_total_abs}",
    )
    check(
        "candidate_scaled_torque_available",
        max_tau_candidate_scaled_abs is not None and max_tau_candidate_scaled_abs >= 0,
        f"max_tau_candidate_scaled_abs={max_tau_candidate_scaled_abs}",
    )
    check(
        "torque_limit_available",
        torque_limit is not None and torque_limit > 0,
        f"torque_limit={torque_limit}",
    )

    fail_count = sum(1 for item in checks if item["status"] != "PASS")
    result = "pass" if fail_count == 0 else "fail"

    summary = {
        "stage": "17.1",
        "name": "conservative closed-loop rollout evidence validation",
        "result": result,
        "failure_count": fail_count,
        "source_basis": "Stage 14.5e scale=0.02 conservative MPC-assisted candidate rollout evidence",
        "source_files": [str(p.relative_to(root)) for p in source_files],
        "generated_files": [
            str(validation_csv.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(validation_log.relative_to(root)),
        ],
        "candidate_metrics": {
            "total_steps": total_steps,
            "candidate_scale": scale,
            "min_z": min_z,
            "max_abs_roll": max_abs_roll,
            "max_abs_pitch": max_abs_pitch,
            "max_tau_total_abs": max_tau_total_abs,
            "max_tau_candidate_scaled_abs": max_tau_candidate_scaled_abs,
            "torque_limit": torque_limit,
            "qp_fail_steps": qp_fail_steps,
            "saturation_steps": saturation_steps,
        },
        "baseline_reference_metrics": {
            "min_z": baseline_min_z,
            "max_abs_roll": baseline_max_abs_roll,
            "max_abs_pitch": baseline_max_abs_pitch,
        },
        "claim_boundary": [
            "simulation-only evidence",
            "conservative low-scale candidate validation",
            "stability and torque-injection evidence only",
            "no velocity tracking metric in this Stage 14.5e evidence file",
            "not a real robot controller",
            "not a high-performance MPC-WBC locomotion claim",
            "not proof that MPC/WBC comprehensively outperforms baseline",
        ],
        "checks": checks,
    }

    write_validation_csv(validation_csv, checks)
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    with validation_log.open("w", encoding="utf-8") as f:
        f.write("[Stage 17.1] Conservative closed-loop rollout validation\n")
        f.write(f"repo_root: {root}\n")
        f.write(f"result: {result}\n")
        f.write(f"failure_count: {fail_count}\n")
        f.write("\n== checks ==\n")
        for item in checks:
            f.write(f"{item['status']}: {item['check']} -- {item['detail']}\n")
        f.write("\n== generated ==\n")
        f.write(str(validation_csv.relative_to(root)) + "\n")
        f.write(str(summary_json.relative_to(root)) + "\n")
        f.write(str(validation_log.relative_to(root)) + "\n")

    print(f"stage17_1_result: {result}")
    print(f"failure_count: {fail_count}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"validation_csv: {validation_csv.relative_to(root)}")
    print(f"validation_log: {validation_log.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
