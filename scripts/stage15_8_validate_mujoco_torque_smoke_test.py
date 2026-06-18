#!/usr/bin/env python3
"""Validate Stage 15.8 bounded MuJoCo torque smoke test."""

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
    alpha_summaries = s.get("alpha_summaries") or []
    rows: List[Dict[str, Any]] = []

    add(rows, "mujoco_imported", s.get("mujoco_imported") is True, s.get("mujoco_import_error", ""))
    add(rows, "mujoco_model_loaded", s.get("mujoco_model_loaded") is True, f"model={s.get('mjcf_model_path')}")
    add(rows, "actuator_count_12", int(s.get("mapped_actuator_count", 0)) >= 12, f"mapped_actuator_count={s.get('mapped_actuator_count')}")
    add(rows, "mj_step_called", s.get("mj_step_called") is True, "this stage intentionally calls mj_step")
    add(rows, "actuator_command_used", s.get("mujoco_actuator_command_used") is True, "bounded actuator command path used")
    add(rows, "short_horizon_steps", int(s.get("steps_per_alpha", 0)) <= 300, f"steps_per_alpha={s.get('steps_per_alpha')}")
    add(rows, "positive_alpha_nonzero_ctrl", int(s.get("total_nonzero_ctrl_steps_positive_alpha", 0)) > 0, f"nonzero_positive_alpha={s.get('total_nonzero_ctrl_steps_positive_alpha')}")
    add(rows, "finite_dynamics", int(s.get("total_nonfinite_steps", 1)) == 0, f"total_nonfinite_steps={s.get('total_nonfinite_steps')}")
    add(rows, "no_ctrl_saturation", int(s.get("total_saturation_steps", 1)) == 0, f"total_saturation_steps={s.get('total_saturation_steps')}")
    max_ctrl = max((float(item.get("max_abs_ctrl", 0.0)) for item in alpha_summaries), default=0.0)
    add(rows, "ctrl_within_audit_limit", max_ctrl <= float(s.get("audit_ctrl_limit", 0.25)) + 1e-12, f"max_ctrl={max_ctrl}")
    add(rows, "not_stable_locomotion_claim", s.get("stable_locomotion_claimed") is False, "stable locomotion must not be claimed")
    add(rows, "smoke_test_only", s.get("torque_path_smoke_test_only") is True, "must remain smoke-test only")
    add(rows, "no_ros_publisher", boundary.get("ros_publisher_used") is False, "no ROS torque publisher")
    add(rows, "baseline_unchanged", boundary.get("frozen_mixed_baseline_modified") is False, "frozen mixed baseline unchanged")
    add(rows, "no_hardware_claim", boundary.get("hardware_deployment_claimed") is False, "no hardware claim")
    add(rows, "no_torque_enable_claim", boundary.get("torque_enable_ready_claimed") is False, "no torque-enable claim")
    add(rows, "short_horizon_only", boundary.get("short_horizon_only") is True, "short-horizon only")

    passed = all(row["passed"] for row in rows)
    result = {
        "stage": "15.8",
        "validation_pass": passed,
        "mjcf_model_path": s.get("mjcf_model_path", ""),
        "mapped_actuator_count": s.get("mapped_actuator_count", 0),
        "max_ctrl": max_ctrl,
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
    print(f"stage15_8_result: {'pass' if passed else 'fail'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
