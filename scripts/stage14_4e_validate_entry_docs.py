#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List


UPDATE_SUMMARY = Path("results/logs_sample/stage14_4e_entry_docs_update_summary.json")
CHECK_CSV = Path("results/logs_sample/stage14_4e_entry_docs_checks.csv")
VALIDATION_SUMMARY = Path("results/logs_sample/stage14_4e_entry_docs_validation_summary.json")

REQUIRED_PHRASES = [
    "standalone simplified 3D base velocity tracking receding-horizon MPC demo",
    "planning-layer",
    "contact-force MPC",
    "不是 WBC",
    "不直接输出 joint torque",
    "不接 ROS torque publisher",
    "不接 MuJoCo torque",
    "不改变 frozen mixed baseline 控制律",
    "simulation-only",
]

PROHIBITED_POSITIVE_CLAIMS = [
    "项目已完成硬件部署",
    "硬件部署已经完成",
    "执行器使能已经完成并可用",
    "真实机器人力矩执行已有完成证据",
    "实时硬件控制器已有完成证据",
    "MPC 已经接入真实机器人",
    "ROS torque publisher 已经启用并用于控制",
    "MPC 已经输出真实 joint torque",
    "MPC-WBC integrated controller 已完成",
    "Stage 14.4D0",
    "中文说明",
    "中文边界审计",
]


def load_json(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(f"missing summary: {path}")
    return json.loads(path.read_text())


def main() -> None:
    update_summary = load_json(UPDATE_SUMMARY)
    failed_checks: List[str] = []
    rows: List[Dict[str, object]] = []

    if update_summary.get("pass") is not True:
        failed_checks.append("update summary pass must be true")

    updated_files = [Path(p) for p in update_summary.get("updated_files", [])]
    if not updated_files:
        failed_checks.append("updated_files must not be empty")

    for path in updated_files:
        if not path.exists():
            failed_checks.append(f"missing updated file: {path}")
            continue

        text = path.read_text()

        for phrase in REQUIRED_PHRASES:
            passed = phrase in text
            rows.append({
                "file": str(path),
                "check_type": "required_phrase",
                "item": phrase,
                "pass": passed,
            })
            if not passed:
                failed_checks.append(f"{path}: missing required phrase: {phrase}")

        for claim in PROHIBITED_POSITIVE_CLAIMS:
            passed = claim not in text
            rows.append({
                "file": str(path),
                "check_type": "prohibited_positive_claim",
                "item": claim,
                "pass": passed,
            })
            if not passed:
                failed_checks.append(f"{path}: prohibited positive claim appears: {claim}")

    CHECK_CSV.parent.mkdir(parents=True, exist_ok=True)
    with CHECK_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "check_type", "item", "pass"])
        writer.writeheader()
        writer.writerows(rows)

    result = {
        "stage": "14.4E",
        "description": "validate Stage 14.4 MPC entry documentation update",
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
        "updated_files": [str(p) for p in updated_files],
        "check_csv": str(CHECK_CSV),
        "summary_json": str(VALIDATION_SUMMARY),
        "input_update_summary": str(UPDATE_SUMMARY),
    }

    VALIDATION_SUMMARY.write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, indent=2, sort_keys=True))

    if not result["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
