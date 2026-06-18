#!/usr/bin/env python3
"""Validate Stage 15.10 MuJoCo torque-smoke policy comparison."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

EXPECTED = {"zero_ctrl", "deterministic_waveform", "jtf_candidate"}


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
    policies = {item.get("policy"): item for item in s.get("policy_summaries", [])}
    rows: List[Dict[str, Any]] = []

    add(rows, "mujoco_imported", s.get("mujoco_imported") is True, s.get("mujoco_import_error", ""))
    add(rows, "mujoco_model_loaded", s.get("mujoco_model_loaded") is True, f"model={s.get('mjcf_model_path')}")
    add(rows, "actuator_count_12", int(s.get("mapped_actuator_count", 0)) >= 12, f"mapped_actuator_count={s.get('mapped_actuator_count')}")
    add(rows, "all_expected_policies", set(policies.keys()) == EXPECTED, f"policies={sorted(policies.keys())}")
    add(rows, "zero_ctrl_present", "zero_ctrl" in policies, "zero_ctrl baseline exists")
    add(rows, "deterministic_present", "deterministic_waveform" in policies, "deterministic waveform comparison exists")
    add(rows, "jtf_present", "jtf_candidate" in policies, "J^T f candidate comparison exists")

    for name in EXPECTED:
        item = policies.get(name, {})
        add(rows, f"{name}_steps", int(item.get("steps", 0)) == int(s.get("steps_per_policy", 0)), f"steps={item.get('steps')}")
        add(rows, f"{name}_finite", int(item.get("nonfinite_steps", 1)) == 0, f"nonfinite={item.get('nonfinite_steps')}")
        add(rows, f"{name}_no_saturation", int(item.get("saturation_steps", 1)) == 0, f"saturation={item.get('saturation_steps')}")
        add(rows, f"{name}_ctrl_within_target", float(item.get("max_abs_ctrl", 999.0)) <= float(s.get("target_max_ctrl", 0.08)) + 1e-9, f"max_ctrl={item.get('max_abs_ctrl')}")

    add(rows, "zero_ctrl_zero_command", int(policies.get("zero_ctrl", {}).get("nonzero_ctrl_steps", 1)) == 0, f"nonzero={policies.get('zero_ctrl', {}).get('nonzero_ctrl_steps')}")
    add(rows, "deterministic_nonzero_command", int(policies.get("deterministic_waveform", {}).get("nonzero_ctrl_steps", 0)) > 0, f"nonzero={policies.get('deterministic_waveform', {}).get('nonzero_ctrl_steps')}")
    add(rows, "jtf_nonzero_command", int(policies.get("jtf_candidate", {}).get("nonzero_ctrl_steps", 0)) > 0, f"nonzero={policies.get('jtf_candidate', {}).get('nonzero_ctrl_steps')}")
    add(rows, "jtf_candidate_used", s.get("jtf_candidate_used") is True, "J^T f candidate used")
    add(rows, "comparison_only", s.get("comparison_type") == "short_horizon_safety_and_compatibility_only", s.get("comparison_type", ""))
    add(rows, "not_stable_locomotion_claim", s.get("stable_locomotion_claimed") is False, "stable locomotion not claimed")
    add(rows, "baseline_unchanged", boundary.get("frozen_mixed_baseline_modified") is False, "frozen mixed baseline unchanged")
    add(rows, "no_ros_publisher", boundary.get("ros_publisher_used") is False, "no ROS torque publisher")
    add(rows, "no_hardware_claim", boundary.get("hardware_deployment_claimed") is False, "no hardware claim")
    add(rows, "no_torque_enable_claim", boundary.get("torque_enable_ready_claimed") is False, "no torque-enable claim")
    add(rows, "short_horizon_only", boundary.get("short_horizon_only") is True, "short-horizon only")

    passed = all(row["passed"] for row in rows)
    result = {
        "stage": "15.10",
        "validation_pass": passed,
        "mjcf_model_path": s.get("mjcf_model_path", ""),
        "policy_summaries": s.get("policy_summaries", []),
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
    print(f"stage15_10_result: {'pass' if passed else 'fail'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
