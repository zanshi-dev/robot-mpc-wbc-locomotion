#!/usr/bin/env python3
"""Validate Stage 16.4 README rewrite."""

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
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    readme_path = repo_root / "README.md"
    text = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    rows: List[Dict[str, Any]] = []

    add(rows, "readme_exists", readme_path.exists(), str(readme_path))
    add(rows, "project_title", text.startswith("# robot-mpc-wbc-locomotion"), "title present")
    add(rows, "chinese_primary_positioning", "仅限仿真验证" in text, "Chinese positioning")
    add(rows, "standard_terms_mpc_wbc_qp_pd", all(term in text for term in ["MPC", "WBC", "QP", "PD"]), "standard control terms")
    add(rows, "standard_tools", all(term in text for term in ["MuJoCo", "Pinocchio", "ROS2", "OSQP", "C++", "Python"]), "standard tool terms")
    add(rows, "first_appearance_examples", "Model Predictive Control, MPC" in text and "Whole-Body Control, WBC" in text and "Quadratic Programming, QP" in text, "Chinese + English + abbreviation examples")
    add(rows, "artifact_index_link", "docs/ARTIFACT_INDEX.md" in text, "artifact index link")
    add(rows, "stage15_summary_link", "docs/STAGE15_UPGRADE_SUMMARY.md" in text, "Stage 15 summary link")
    add(rows, "ros2_cpp_evidence", "ROS2/C++" in text and "GTest" in text, "ROS2/C++ evidence")
    add(rows, "pinocchio_jtf_evidence", "Pinocchio" in text and "J^T f" in text, "Pinocchio JTF evidence")
    add(rows, "mujoco_smoke_evidence", "MuJoCo" in text and "smoke test" in text.lower(), "MuJoCo smoke test evidence")
    add(rows, "no_stage16_3_public_material", "STAGE16_3" not in text and "面试防御材料" not in text, "16.3 personal material not linked")
    add(rows, "no_hardware_claim", "不声明真实机器人部署" in text, "hardware boundary")
    add(rows, "no_torque_enable_claim", "不声明 `torque_enable_ready=True`" in text or "不声明 torque_enable_ready=True" in text, "torque-enable boundary")
    add(rows, "no_stable_locomotion_claim", "不声明稳定行走" in text or "不声明 Stage 15 的 bounded torque smoke test 证明了稳定行走" in text, "stable locomotion boundary")
    add(rows, "no_full_mpc_wbc_claim", "不声明完整 MPC-WBC" in text, "full MPC-WBC boundary")
    add(rows, "no_old_mixed_phrases", "simulation-only locomotion baseline" not in text and "hardware deployment completed" not in text and "torque-enable ready" not in text, "old mixed phrases removed")

    passed = all(row["passed"] for row in rows)
    result = {
        "stage": "16.4",
        "validation_pass": passed,
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
    print(f"stage16_4_result: {'pass' if passed else 'fail'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
