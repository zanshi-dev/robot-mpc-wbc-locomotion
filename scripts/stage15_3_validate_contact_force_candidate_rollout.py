#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Dict, List

SUMMARY_PATH = Path("results/logs_sample/stage15_3_contact_force_candidate_rollout_summary.json")
ROLLOUT_CSV_PATH = Path("results/logs_sample/stage15_3_contact_force_candidate_rollout.csv")
SOURCE_SCRIPT_PATH = Path("scripts/stage15_3_contact_force_candidate_rollout.py")
VALIDATION_SUMMARY_PATH = Path("results/logs_sample/stage15_3_contact_force_candidate_rollout_validation_summary.json")
VALIDATION_CSV_PATH = Path("results/logs_sample/stage15_3_contact_force_candidate_rollout_validation.csv")

FOOT_NAMES = ["FR", "FL", "RR", "RL"]
AXIS_NAMES = ["fx", "fy", "fz"]
ALPHA_KEYS = ["0p0", "0p02", "0p05", "0p1", "0p2"]


def load_json(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return json.loads(path.read_text())


def load_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def is_finite_float(value: str) -> bool:
    try:
        return math.isfinite(float(value))
    except Exception:
        return False


def required_columns() -> List[str]:
    columns = [
        "step", "contact_mode", "px", "pz", "vx", "vz", "desired_ax", "desired_az",
        "sum_fx", "sum_fy", "sum_fz", "max_swing_force_norm", "min_stance_fz",
        "max_stance_fz", "max_friction_violation", "max_normal_force_violation",
        "max_tau_candidate_abs", "max_tau_candidate_delta_abs",
    ]
    for foot in FOOT_NAMES:
        for axis in AXIS_NAMES:
            columns.append(f"force_{foot}_{axis}")
    for i in range(12):
        columns.append(f"tau_candidate_{i:02d}")
    for alpha_key in ALPHA_KEYS:
        columns.append(f"max_tau_scaled_abs_alpha_{alpha_key}")
        columns.append(f"max_tau_scaled_delta_abs_alpha_{alpha_key}")
    return columns


def validate_source_contract(source_text: str) -> List[str]:
    required = [
        "nominal_jacobian_transpose_force_map",
        "not a Pinocchio-derived robot Jacobian",
        "torque_publisher_enabled",
        "mujoco_torque_used",
        "pinocchio_jacobian_used",
        "frozen_mixed_baseline_modified",
    ]
    return [snippet for snippet in required if snippet not in source_text]


def validate() -> Dict:
    summary = load_json(SUMMARY_PATH)
    rows = load_csv(ROLLOUT_CSV_PATH)
    source_text = SOURCE_SCRIPT_PATH.read_text() if SOURCE_SCRIPT_PATH.exists() else ""

    missing_columns: List[str] = []
    if rows:
        observed = set(rows[0].keys())
        missing_columns = [column for column in required_columns() if column not in observed]
    else:
        missing_columns = required_columns()

    failed_checks: List[str] = []
    validation_rows: List[Dict[str, object]] = []

    def fail(label: str) -> None:
        failed_checks.append(label)

    if summary.get("pass") is not True:
        fail("stage15_3 summary pass must be true")

    for key in [
        "simulation_only_project",
        "nominal_jacobian_transpose_candidate_map_used",
    ]:
        if summary.get(key) is not True:
            fail(f"{key} must be true")

    for key in [
        "hardware_deployment_completed",
        "torque_enable_ready",
        "torque_publisher_enabled",
        "real_robot_torque_execution_completed",
        "mixed_baseline_modified",
        "frozen_mixed_baseline_modified",
        "ros_publisher_used",
        "mujoco_torque_used",
        "pinocchio_jacobian_used",
    ]:
        if summary.get(key) is not False:
            fail(f"{key} must be false")

    source_missing = validate_source_contract(source_text)
    if source_missing:
        fail("source safety contract snippets missing: " + ", ".join(source_missing))

    if missing_columns:
        fail("missing CSV columns: " + ", ".join(missing_columns))

    cfg = summary.get("config", {})
    expected_rows = int(cfg.get("total_steps", summary.get("total_steps", -1)))
    torque_limit = float(cfg.get("torque_limit", 23.7))
    target_vx = float(cfg.get("target_vx", 0.30))
    target_z = float(cfg.get("target_z", 0.30))

    if len(rows) != expected_rows:
        fail(f"row count mismatch: expected {expected_rows}, got {len(rows)}")

    max_swing = 0.0
    max_friction = 0.0
    max_normal = 0.0
    max_tau_scaled = 0.0
    max_abs_z_error = 0.0
    final_vx_error = math.nan
    final_z_error = math.nan

    numeric_columns = [c for c in required_columns() if c not in {"contact_mode"}]

    for index, row in enumerate(rows):
        row_failures: List[str] = []
        finite_pass = all((column in row and is_finite_float(row[column])) for column in numeric_columns if column != "step")
        if not finite_pass:
            row_failures.append("non_finite_numeric_value")
        if finite_pass:
            swing = float(row["max_swing_force_norm"])
            friction = float(row["max_friction_violation"])
            normal = float(row["max_normal_force_violation"])
            z_error = abs(float(row["pz"]) - target_z)
            max_swing = max(max_swing, swing)
            max_friction = max(max_friction, friction)
            max_normal = max(max_normal, normal)
            max_abs_z_error = max(max_abs_z_error, z_error)
            for alpha_key in ALPHA_KEYS:
                max_tau_scaled = max(max_tau_scaled, float(row[f"max_tau_scaled_abs_alpha_{alpha_key}"]))
            if swing > 1e-9:
                row_failures.append("swing_force_not_zero")
            if friction > 1e-9:
                row_failures.append("friction_violation")
            if normal > 1e-9:
                row_failures.append("normal_force_violation")
            if max_tau_scaled > torque_limit + 1e-9:
                row_failures.append("scaled_torque_above_limit")
        validation_rows.append({
            "step": int(row.get("step", index)),
            "contact_mode": row.get("contact_mode", ""),
            "finite_pass": finite_pass,
            "row_pass": len(row_failures) == 0,
            "failures": ";".join(row_failures),
        })

    if validation_rows and any(not row["row_pass"] for row in validation_rows):
        fail("one or more rows failed validation")

    if rows:
        final_vx_error = abs(float(rows[-1]["vx"]) - target_vx)
        final_z_error = abs(float(rows[-1]["pz"]) - target_z)
        if final_vx_error > 0.03:
            fail("final vx error must be <= 0.03 m/s")
        if final_z_error > 0.02:
            fail("final z error must be <= 0.02 m")

    alpha_results = summary.get("alpha_results", {})
    for alpha_key in ["0p1", "0p2"]:
        if alpha_results.get(alpha_key, {}).get("pass") is not True:
            fail(f"alpha {alpha_key} must pass scaled torque limit")

    if float(summary.get("validated_candidate_scale_max_simulation_only", 0.0)) < 0.20:
        fail("validated candidate scale max must be >= 0.20")

    VALIDATION_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with VALIDATION_CSV_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["step", "contact_mode", "finite_pass", "row_pass", "failures"])
        writer.writeheader()
        writer.writerows(validation_rows)

    validation_summary = {
        "stage": "15.3_validation",
        "description": "independent validation for Stage 15.3 contact-force-to-torque candidate rollout",
        "pass": len(failed_checks) == 0,
        "failed_checks": failed_checks,
        "simulation_only_project": True,
        "hardware_deployment_completed": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "real_robot_torque_execution_completed": False,
        "mixed_baseline_modified": False,
        "frozen_mixed_baseline_modified": False,
        "ros_publisher_used": False,
        "mujoco_torque_used": False,
        "pinocchio_jacobian_used": False,
        "input_summary_json": str(SUMMARY_PATH),
        "input_rollout_csv": str(ROLLOUT_CSV_PATH),
        "validation_csv": str(VALIDATION_CSV_PATH),
        "validation_summary_json": str(VALIDATION_SUMMARY_PATH),
        "rows": len(rows),
        "missing_columns": missing_columns,
        "source_missing_contract_snippets": source_missing,
        "max_swing_force_norm": max_swing,
        "max_friction_violation": max_friction,
        "max_normal_force_violation": max_normal,
        "max_tau_scaled_abs": max_tau_scaled,
        "max_abs_z_error": max_abs_z_error,
        "final_vx_error_abs": final_vx_error,
        "final_z_error_abs": final_z_error,
        "validated_candidate_scale_max_simulation_only": summary.get("validated_candidate_scale_max_simulation_only"),
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
