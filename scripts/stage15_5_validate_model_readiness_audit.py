#!/usr/bin/env python3
"""Validate Stage 15.5 model readiness audit outputs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


def add_check(rows: List[Dict[str, Any]], name: str, passed: bool, details: str) -> None:
    rows.append({"check": name, "passed": bool(passed), "details": details})


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args(argv)

    report = json.loads(args.report_json.read_text(encoding="utf-8"))
    selected = report.get("selected_model") or {}
    readiness = report.get("readiness") or {}
    boundary = report.get("boundary") or {}

    rows: List[Dict[str, Any]] = []
    add_check(rows, "audit_completed", report.get("audit_completed") is True, "audit script finished")
    add_check(rows, "model_file_count_positive", report.get("model_file_count", 0) > 0, f"model_file_count={report.get('model_file_count', 0)}")
    add_check(rows, "selected_model_exists", bool(selected.get("path")), f"selected_model={selected.get('path', '')}")
    add_check(rows, "controlled_joint_count_at_least_12", len(selected.get("controlled_joint_names", [])) >= 12, f"controlled_joint_count={len(selected.get('controlled_joint_names', []))}")
    add_check(rows, "foot_candidates_at_least_4", len(selected.get("foot_frame_candidates", [])) >= 4, f"foot_candidate_count={len(selected.get('foot_frame_candidates', []))}")
    mapped_joint_count = sum(1 for leg in selected.get("inferred_joint_order", {}).values() for value in leg.values() if value)
    mapped_foot_count = sum(1 for value in selected.get("inferred_foot_frames", {}).values() if value)
    add_check(rows, "inferred_joint_order_nonempty", mapped_joint_count > 0, f"mapped_joint_count={mapped_joint_count}")
    add_check(rows, "inferred_foot_mapping_nonempty", mapped_foot_count > 0, f"mapped_foot_count={mapped_foot_count}")
    add_check(rows, "audit_only_boundary", boundary.get("audit_only") is True, "audit_only must remain true")
    add_check(rows, "no_mujoco_torque", boundary.get("mujoco_torque_used") is False, "MuJoCo torque must not be used")
    add_check(rows, "no_ros_publisher", boundary.get("ros_publisher_used") is False, "ROS torque publisher must not be used")
    add_check(rows, "baseline_not_modified", boundary.get("frozen_mixed_baseline_modified") is False, "frozen mixed baseline must remain untouched")
    add_check(rows, "no_hardware_claim", boundary.get("hardware_deployment_claimed") is False, "no hardware deployment claim")
    add_check(rows, "no_torque_enable_claim", boundary.get("torque_enable_ready_claimed") is False, "no torque-enable claim")

    passed = all(row["passed"] for row in rows)
    summary = {
        "stage": "15.5",
        "validation_pass": passed,
        "selected_model": selected.get("path", ""),
        "model_type": selected.get("model_type", ""),
        "controlled_joint_count": len(selected.get("controlled_joint_names", [])),
        "foot_candidate_count": len(selected.get("foot_frame_candidates", [])),
        "mapped_joint_count": mapped_joint_count,
        "mapped_foot_count": mapped_foot_count,
        "ready_for_real_model_jacobian_stage": readiness.get("ready_for_real_model_jacobian_stage", False),
        "checks": rows,
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    with args.output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "passed", "details"])
        writer.writeheader()
        writer.writerows(rows)

    for row in rows:
        status = "PASS" if row["passed"] else "FAIL"
        print(f"{status}: {row['check']} -- {row['details']}")
    print(f"stage15_5_result: {'pass' if passed else 'fail'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
