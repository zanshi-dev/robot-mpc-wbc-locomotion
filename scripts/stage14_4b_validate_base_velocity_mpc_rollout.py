#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple


SUMMARY_PATH = Path("results/logs_sample/stage14_4_base_velocity_tracking_mpc_summary.json")
ROLLOUT_CSV_PATH = Path("results/logs_sample/stage14_4_base_velocity_tracking_mpc_rollout.csv")
SOURCE_SCRIPT_PATH = Path("scripts/stage14_4_base_velocity_tracking_mpc_demo.py")

VALIDATION_CSV_PATH = Path("results/logs_sample/stage14_4b_base_velocity_tracking_mpc_validation.csv")
VALIDATION_SUMMARY_PATH = Path("results/logs_sample/stage14_4b_base_velocity_tracking_mpc_validation_summary.json")

FOOT_NAMES = ["FR", "FL", "RR", "RL"]
AXIS_NAMES = ["fx", "fy", "fz"]
OK_STATUSES = {"solved", "solved inaccurate"}


def load_json(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return json.loads(path.read_text())


def load_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def as_float(row: Dict[str, str], key: str) -> float:
    return float(row[key])


def is_finite_float(value: str) -> bool:
    try:
        return math.isfinite(float(value))
    except Exception:
        return False


def required_columns() -> List[str]:
    force_columns = [f"u0_{foot}_{axis}" for foot in FOOT_NAMES for axis in AXIS_NAMES]
    return [
        "step",
        "contact_mode",
        "px",
        "py",
        "pz",
        "vx",
        "vy",
        "vz",
        *force_columns,
        "sum_fx",
        "sum_fy",
        "sum_fz",
        "max_swing_force_norm",
        "min_stance_fz",
        "max_stance_fz",
        "max_friction_violation",
        "status",
        "solve_time",
        "total_fz_upper_violation",
        "force_delta_norm",
    ]


def validate_source_receding_horizon_pattern(source_text: str) -> Tuple[bool, List[str]]:
    missing = []

    required_snippets = [
        "for step in range(cfg.rollout_steps)",
        "solve_mpc(x, prev_u, step, cfg)",
        "x = step_dynamics(x, u0, cfg)",
        "prev_u = u0.copy()",
        "contact_schedule(rollout_step + k, cfg)",
    ]

    for snippet in required_snippets:
        if snippet not in source_text:
            missing.append(snippet)

    return len(missing) == 0, missing


def validate() -> Dict:
    summary = load_json(SUMMARY_PATH)
    rows = load_csv(ROLLOUT_CSV_PATH)

    if not SOURCE_SCRIPT_PATH.exists():
        source_text = ""
        source_pattern_pass = False
        missing_source_patterns = ["source script missing"]
    else:
        source_text = SOURCE_SCRIPT_PATH.read_text()
        source_pattern_pass, missing_source_patterns = validate_source_receding_horizon_pattern(source_text)

    cfg = summary.get("config", {})
    rollout_steps_expected = int(cfg.get("rollout_steps", summary.get("total_steps", -1)))
    vx_ref = float(cfg.get("vx_ref", 0.35))
    z_ref = float(cfg.get("z_ref", 0.30))
    fz_min = float(cfg.get("fz_min", 5.0))
    fz_max = float(cfg.get("fz_max", 120.0))
    total_fz_max = float(cfg.get("total_fz_max", 240.0))

    missing_columns = []
    if rows:
        observed_columns = set(rows[0].keys())
        missing_columns = [c for c in required_columns() if c not in observed_columns]
    else:
        missing_columns = required_columns()

    validation_rows: List[Dict[str, object]] = []
    failed_checks: List[str] = []

    max_swing_force_norm = 0.0
    min_stance_fz_observed = math.inf
    max_stance_fz_observed = -math.inf
    max_friction_violation = 0.0
    max_total_fz_violation = 0.0
    max_abs_vy = 0.0
    max_abs_z_error = 0.0
    max_force_delta_norm = 0.0
    max_solve_time = 0.0
    statuses = []

    for index, row in enumerate(rows):
        row_failures: List[str] = []

        if missing_columns:
            row_failures.append("missing_required_columns")

        step = int(row.get("step", index))
        status = str(row.get("status", "")).lower()
        statuses.append(status)

        numeric_keys = [
            "px", "py", "pz", "vx", "vy", "vz",
            "sum_fx", "sum_fy", "sum_fz",
            "max_swing_force_norm",
            "min_stance_fz",
            "max_stance_fz",
            "max_friction_violation",
            "solve_time",
            "total_fz_upper_violation",
            "force_delta_norm",
        ]
        numeric_keys += [f"u0_{foot}_{axis}" for foot in FOOT_NAMES for axis in AXIS_NAMES]

        finite_pass = all((key in row and is_finite_float(row[key])) for key in numeric_keys)

        if status not in OK_STATUSES:
            row_failures.append("bad_solver_status")
        if not finite_pass:
            row_failures.append("non_finite_numeric_value")

        if finite_pass:
            swing = as_float(row, "max_swing_force_norm")
            min_fz = as_float(row, "min_stance_fz")
            max_fz = as_float(row, "max_stance_fz")
            friction = as_float(row, "max_friction_violation")
            total_fz_upper_violation = as_float(row, "total_fz_upper_violation")
            vy_abs = abs(as_float(row, "vy"))
            z_error = abs(as_float(row, "pz") - z_ref)
            force_delta = as_float(row, "force_delta_norm")
            solve_time = as_float(row, "solve_time")

            max_swing_force_norm = max(max_swing_force_norm, swing)
            min_stance_fz_observed = min(min_stance_fz_observed, min_fz)
            max_stance_fz_observed = max(max_stance_fz_observed, max_fz)
            max_friction_violation = max(max_friction_violation, friction)
            max_total_fz_violation = max(max_total_fz_violation, total_fz_upper_violation)
            max_abs_vy = max(max_abs_vy, vy_abs)
            max_abs_z_error = max(max_abs_z_error, z_error)
            max_force_delta_norm = max(max_force_delta_norm, force_delta)
            max_solve_time = max(max_solve_time, solve_time)

            if swing > 1.0e-6:
                row_failures.append("swing_force_not_zero")
            if min_fz < fz_min - 1.0e-5:
                row_failures.append("stance_fz_below_min")
            if max_fz > fz_max + 1.0e-5:
                row_failures.append("stance_fz_above_max")
            if friction > 1.0e-5:
                row_failures.append("friction_violation")
            if total_fz_upper_violation > 1.0e-5:
                row_failures.append("total_fz_violation")
            if as_float(row, "sum_fz") > total_fz_max + 1.0e-5:
                row_failures.append("sum_fz_above_total_limit")

        validation_rows.append({
            "step": step,
            "contact_mode": row.get("contact_mode", ""),
            "status": status,
            "finite_pass": finite_pass,
            "row_pass": len(row_failures) == 0,
            "failures": ";".join(row_failures),
        })

    if summary.get("pass") is not True:
        failed_checks.append("Stage 14.4A summary pass must be true")
    if summary.get("simulation_only_project") is not True:
        failed_checks.append("simulation_only_project must be true")
    for key in [
        "hardware_deployment_completed",
        "torque_enable_ready",
        "torque_publisher_enabled",
        "control_law_changed",
        "mixed_baseline_modified",
        "mujoco_torque_used",
        "ros_publisher_used",
    ]:
        if summary.get(key) is not False:
            failed_checks.append(f"{key} must be false")

    if len(rows) != rollout_steps_expected:
        failed_checks.append(f"rollout row count mismatch: expected {rollout_steps_expected}, got {len(rows)}")
    if missing_columns:
        failed_checks.append("missing required rollout CSV columns: " + ", ".join(missing_columns))
    if any(status not in OK_STATUSES for status in statuses):
        failed_checks.append("all OSQP statuses must be solved or solved inaccurate")
    if any(not row["finite_pass"] for row in validation_rows):
        failed_checks.append("all numeric state and force values must be finite")
    if any(not row["row_pass"] for row in validation_rows):
        failed_checks.append("one or more rollout rows failed per-step validation")
    if not source_pattern_pass:
        failed_checks.append("source script does not show expected receding-horizon solve/apply/update pattern")

    if rows:
        initial_vx_error = abs(as_float(rows[0], "vx") - vx_ref)
        final_vx = as_float(rows[-1], "vx")
        final_vx_error = abs(final_vx - vx_ref)
        final_vy = as_float(rows[-1], "vy")
        final_z = as_float(rows[-1], "pz")
        final_z_error = abs(final_z - z_ref)
    else:
        initial_vx_error = math.nan
        final_vx = math.nan
        final_vx_error = math.nan
        final_vy = math.nan
        final_z = math.nan
        final_z_error = math.nan
        failed_checks.append("rollout CSV must contain rows")

    if rows and not (final_vx_error < initial_vx_error):
        failed_checks.append("final vx error must be lower than initial vx error")
    if rows and final_vx_error > 0.08:
        failed_checks.append("final vx error must be <= 0.08 m/s")
    if rows and abs(final_vy) > 0.03:
        failed_checks.append("final |vy| must be <= 0.03 m/s")
    if rows and final_z_error > 0.03:
        failed_checks.append("final z error must be <= 0.03 m")

    VALIDATION_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with VALIDATION_CSV_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["step", "contact_mode", "status", "finite_pass", "row_pass", "failures"],
        )
        writer.writeheader()
        writer.writerows(validation_rows)

    validation_summary = {
        "stage": "14.4B",
        "description": "independent validation of Stage 14.4A base velocity tracking MPC rollout",
        "pass": len(failed_checks) == 0,
        "failed_checks": failed_checks,
        "simulation_only_project": True,
        "hardware_deployment_completed": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "control_law_changed": False,
        "mixed_baseline_modified": False,
        "mujoco_torque_used": False,
        "ros_publisher_used": False,
        "input_summary_json": str(SUMMARY_PATH),
        "input_rollout_csv": str(ROLLOUT_CSV_PATH),
        "validation_csv": str(VALIDATION_CSV_PATH),
        "validation_summary_json": str(VALIDATION_SUMMARY_PATH),
        "rollout_rows": len(rows),
        "expected_rollout_rows": rollout_steps_expected,
        "status_counts": {status: statuses.count(status) for status in sorted(set(statuses))},
        "missing_columns": missing_columns,
        "source_receding_horizon_pattern_pass": source_pattern_pass,
        "missing_source_patterns": missing_source_patterns,
        "max_swing_force_norm": max_swing_force_norm,
        "min_stance_fz": min_stance_fz_observed,
        "max_stance_fz": max_stance_fz_observed,
        "max_friction_violation": max_friction_violation,
        "max_total_fz_violation": max_total_fz_violation,
        "max_abs_vy": max_abs_vy,
        "max_abs_z_error": max_abs_z_error,
        "max_force_delta_norm": max_force_delta_norm,
        "max_solve_time_s": max_solve_time,
        "initial_vx_error_abs": initial_vx_error,
        "final_vx": final_vx,
        "final_vx_error_abs": final_vx_error,
        "final_vy": final_vy,
        "final_z": final_z,
        "final_z_error_abs": final_z_error,
    }

    VALIDATION_SUMMARY_PATH.write_text(json.dumps(validation_summary, indent=2, sort_keys=True))
    return validation_summary


def main() -> None:
    result = validate()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result.get("pass", False):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
