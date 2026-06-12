#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List


DOC_PATH = Path("docs/stage14_4c_mpc_scope_explanation.md")
SUMMARY_14_4A_PATH = Path("results/logs_sample/stage14_4_base_velocity_tracking_mpc_summary.json")
SUMMARY_14_4B_PATH = Path("results/logs_sample/stage14_4b_base_velocity_tracking_mpc_validation_summary.json")

CHECK_CSV_PATH = Path("results/logs_sample/stage14_4c_mpc_scope_explanation_checks.csv")
SUMMARY_PATH = Path("results/logs_sample/stage14_4c_mpc_scope_explanation_summary.json")


REQUIRED_PHRASES = [
    "Stage 14.4 是一个独立的、简化的 3D base velocity tracking receding-horizon MPC demo",
    "不是 WBC",
    "不直接输出 joint torque",
    "不接 ROS torque publisher",
    "不接 MuJoCo torque",
    "不改变 mixed baseline 控制律",
    "Stage 5",
    "z-MPC prototype",
    "Stage 7",
    "WBC feedforward",
    "Stage 14.4A",
    "Stage 14.4B",
    "receding-horizon",
    "只应用 u0",
    "simulation_only_project=true",
    "hardware_deployment_completed=false",
    "torque_enable_ready=false",
    "torque_publisher_enabled=false",
    "control_law_changed=false",
    "mixed_baseline_modified=false",
    "mujoco_torque_used=false",
    "ros_publisher_used=false",
]

PROHIBITED_POSITIVE_CLAIMS = [
    "项目已完成硬件部署",
    "硬件部署已经完成",
    "执行器使能已经完成并可用",
    "真实机器人力矩执行已经完成",
    "实时硬件控制器已经完成",
    "MPC 已经接入真实机器人",
    "ROS torque publisher 已经启用并用于控制",
]


def load_json(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(f"missing required summary: {path}")
    return json.loads(path.read_text())


def main() -> None:
    failed_checks: List[str] = []

    if not DOC_PATH.exists():
        failed_checks.append(f"missing document: {DOC_PATH}")
        text = ""
    else:
        text = DOC_PATH.read_text()

    summary_a = load_json(SUMMARY_14_4A_PATH)
    summary_b = load_json(SUMMARY_14_4B_PATH)

    rows = []

    for phrase in REQUIRED_PHRASES:
        passed = phrase in text
        rows.append({
            "check_type": "required_phrase",
            "item": phrase,
            "pass": passed,
        })
        if not passed:
            failed_checks.append(f"missing required phrase: {phrase}")

    for claim in PROHIBITED_POSITIVE_CLAIMS:
        passed = claim not in text
        rows.append({
            "check_type": "prohibited_positive_claim_scan",
            "item": claim,
            "pass": passed,
        })
        if not passed:
            failed_checks.append(f"prohibited positive claim appears: {claim}")

    chinese_chars = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    total_non_space_chars = sum(1 for ch in text if not ch.isspace())
    chinese_ratio = chinese_chars / max(total_non_space_chars, 1)

    rows.append({
        "check_type": "language",
        "item": "Chinese character ratio >= 0.35",
        "pass": chinese_ratio >= 0.35,
    })
    if chinese_ratio < 0.35:
        failed_checks.append(f"document does not appear to be primarily Chinese, chinese_ratio={chinese_ratio:.3f}")

    if summary_a.get("pass") is not True:
        failed_checks.append("Stage 14.4A summary pass must be true")
    if summary_b.get("pass") is not True:
        failed_checks.append("Stage 14.4B summary pass must be true")

    for source_name, summary in [
        ("14.4A", summary_a),
        ("14.4B", summary_b),
    ]:
        if summary.get("simulation_only_project") is not True:
            failed_checks.append(f"Stage {source_name} simulation_only_project must be true")
        for key in [
            "hardware_deployment_completed",
            "torque_enable_ready",
            "torque_publisher_enabled",
            "control_law_changed",
        ]:
            if summary.get(key) is not False:
                failed_checks.append(f"Stage {source_name} {key} must be false")

    CHECK_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CHECK_CSV_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check_type", "item", "pass"])
        writer.writeheader()
        writer.writerows(rows)

    result = {
        "stage": "14.4C",
        "description": "Chinese explanation document for MPC scope and relationship to Stage 5 z-MPC and Stage 7 WBC feedforward",
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
        "document": str(DOC_PATH),
        "check_csv": str(CHECK_CSV_PATH),
        "summary_json": str(SUMMARY_PATH),
        "input_stage14_4a_summary": str(SUMMARY_14_4A_PATH),
        "input_stage14_4b_summary": str(SUMMARY_14_4B_PATH),
        "required_phrase_count": len(REQUIRED_PHRASES),
        "prohibited_positive_claim_count": len(PROHIBITED_POSITIVE_CLAIMS),
        "chinese_character_ratio": chinese_ratio,
    }

    SUMMARY_PATH.write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, indent=2, sort_keys=True))

    if not result["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
