#!/usr/bin/env python3
"""Validate Stage 15.7 MuJoCo compatibility audit outputs."""

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
    compat = s.get("torque_candidate_compatibility") or {}
    rows: List[Dict[str, Any]] = []

    add(rows, "mujoco_imported", s.get("mujoco_imported") is True, s.get("mujoco_import_error", ""))
    add(rows, "mujoco_model_loaded", s.get("mujoco_model_loaded") is True, f"model={s.get('mjcf_model_path')}")
    add(rows, "mujoco_dimensions_positive", int(s.get("nq", 0)) > 0 and int(s.get("nv", 0)) > 0, f"nq={s.get('nq')}, nv={s.get('nv')}, nu={s.get('nu')}")
    add(rows, "mapped_joint_count_12", int(s.get("mapped_joint_count", 0)) >= 12, f"mapped_joint_count={s.get('mapped_joint_count')}")
    add(rows, "mapped_actuator_count_nonzero", int(s.get("mapped_actuator_count", 0)) > 0, f"mapped_actuator_count={s.get('mapped_actuator_count')}")
    add(rows, "kinematic_forward_steps_2400", int(s.get("kinematic_forward_steps", 0)) == 2400, f"steps={s.get('kinematic_forward_steps')}")
    add(rows, "mj_forward_called", s.get("mj_forward_called") is True, "mj_forward should be used for kinematic compatibility")
    add(rows, "mj_step_not_called", s.get("mj_step_called") is False, "mj_step must not be called in this stage")
    add(rows, "qpos_finite", s.get("qpos_finite") is True, "qpos finite over audit")
    add(rows, "qvel_finite", s.get("qvel_finite") is True, "qvel finite over audit")
    add(rows, "zero_ctrl", int(s.get("nonzero_ctrl_steps", 1)) == 0, f"nonzero_ctrl_steps={s.get('nonzero_ctrl_steps')}")
    add(rows, "alpha_0_10_compatible", compat.get("alpha_0_10_within_limit") is True, f"alpha_0.10={compat.get('stage15_6_alpha_max_tau_abs', {}).get('0.10')}")
    add(rows, "alpha_0_20_compatible", compat.get("alpha_0_20_within_limit") is True, f"alpha_0.20={compat.get('stage15_6_alpha_max_tau_abs', {}).get('0.20')}")
    add(rows, "no_mujoco_torque", boundary.get("mujoco_torque_used") is False, "no MuJoCo torque")
    add(rows, "no_mujoco_dynamics_step", boundary.get("mujoco_dynamics_step_used") is False, "no MuJoCo dynamics step")
    add(rows, "no_ros_publisher", boundary.get("ros_publisher_used") is False, "no ROS torque publisher")
    add(rows, "baseline_unchanged", boundary.get("frozen_mixed_baseline_modified") is False, "frozen mixed baseline unchanged")
    add(rows, "dry_run_only", boundary.get("dry_run_only") is True, "dry-run only")
    add(rows, "no_hardware_claim", boundary.get("hardware_deployment_claimed") is False, "no hardware claim")
    add(rows, "no_torque_enable_claim", boundary.get("torque_enable_ready_claimed") is False, "no torque-enable claim")

    passed = all(row["passed"] for row in rows)
    result = {
        "stage": "15.7",
        "validation_pass": passed,
        "mjcf_model_path": s.get("mjcf_model_path", ""),
        "mapped_joint_count": s.get("mapped_joint_count", 0),
        "mapped_actuator_count": s.get("mapped_actuator_count", 0),
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
    print(f"stage15_7_result: {'pass' if passed else 'fail'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
