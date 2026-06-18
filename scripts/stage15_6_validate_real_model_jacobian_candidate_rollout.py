#!/usr/bin/env python3
"""Validate Stage 15.6 real-model Jacobian candidate rollout outputs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


def add(rows: List[Dict[str, Any]], name: str, passed: bool, details: str) -> None:
    rows.append({"check": name, "passed": bool(passed), "details": details})


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args(argv)

    s = json.loads(args.summary_json.read_text(encoding="utf-8"))
    boundary = s.get("boundary") or {}
    rows: List[Dict[str, Any]] = []

    add(rows, "pinocchio_imported", s.get("pinocchio_imported") is True, s.get("pinocchio_import_error", ""))
    add(rows, "pinocchio_model_loaded", s.get("pinocchio_model_loaded") is True, f"model_source={s.get('model_source')}")
    add(rows, "real_model_candidate_used", s.get("real_model_candidate_used") is True, f"selected_model={s.get('selected_model_path')}")
    add(rows, "selected_model_nonempty", bool(s.get("selected_model_path")), f"selected_model={s.get('selected_model_path')}")
    add(rows, "controlled_joint_count_at_least_12", int(s.get("controlled_joint_count", 0)) >= 12, f"controlled_joint_count={s.get('controlled_joint_count')}")
    add(rows, "foot_frame_count_at_least_4", int(s.get("foot_frame_count", 0)) >= 4, f"foot_frame_count={s.get('foot_frame_count')}")
    add(rows, "total_steps_2400", int(s.get("total_steps", 0)) == 2400, f"total_steps={s.get('total_steps')}")
    add(rows, "jacobian_norm_positive", float(s.get("jacobian_norm_min", 0.0)) > 1e-8, f"jacobian_norm_min={s.get('jacobian_norm_min')}")
    add(rows, "tau_candidate_finite", int(s.get("nonfinite_tau_steps", 0)) == 0, f"nonfinite_tau_steps={s.get('nonfinite_tau_steps')}")
    add(rows, "swing_force_zero", float(s.get("swing_force_max", 1.0)) <= 1e-12, f"swing_force_max={s.get('swing_force_max')}")
    alpha_sat = s.get("alpha_saturation_steps") or {}
    add(rows, "alpha_0_10_no_saturation", int(alpha_sat.get("0.10", 999)) == 0, f"alpha_0.10_saturation_steps={alpha_sat.get('0.10')}")
    add(rows, "alpha_0_20_no_saturation", int(alpha_sat.get("0.20", 999)) == 0, f"alpha_0.20_saturation_steps={alpha_sat.get('0.20')}")
    add(rows, "no_mujoco_torque", boundary.get("mujoco_torque_used") is False, "MuJoCo torque must remain disabled")
    add(rows, "no_ros_publisher", boundary.get("ros_publisher_used") is False, "ROS torque publisher must remain disabled")
    add(rows, "baseline_unchanged", boundary.get("frozen_mixed_baseline_modified") is False, "frozen mixed baseline must remain unchanged")
    add(rows, "dry_run_only", boundary.get("dry_run_only") is True, "stage must remain dry-run only")
    add(rows, "no_hardware_claim", boundary.get("hardware_deployment_claimed") is False, "no hardware claim")
    add(rows, "no_torque_enable_claim", boundary.get("torque_enable_ready_claimed") is False, "no torque-enable claim")

    passed = all(row["passed"] for row in rows)
    result = {
        "stage": "15.6",
        "validation_pass": passed,
        "selected_model_path": s.get("selected_model_path", ""),
        "model_source": s.get("model_source", ""),
        "real_geometry_loaded": s.get("real_geometry_loaded", False),
        "checks": rows,
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    with args.output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "passed", "details"])
        writer.writeheader()
        writer.writerows(rows)

    for row in rows:
        print(f"{'PASS' if row['passed'] else 'FAIL'}: {row['check']} -- {row['details']}")
    print(f"stage15_6_result: {'pass' if passed else 'fail'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
