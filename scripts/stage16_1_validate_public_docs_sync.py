#!/usr/bin/env python3
"""Validate Stage 16.1 public docs sync."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

START = "<!-- STAGE16_1_PUBLIC_DOCS_SYNC_START -->"
END = "<!-- STAGE16_1_PUBLIC_DOCS_SYNC_END -->"


def add(rows: List[Dict[str, Any]], name: str, passed: bool, details: str) -> None:
    rows.append({"check": name, "passed": bool(passed), "details": details})


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--summary-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    summary = json.loads(args.summary_json.read_text(encoding="utf-8"))
    readme = text(repo_root / "README.md")
    one_page = text(repo_root / "docs/ONE_PAGE_TECHNICAL_REPORT.md")
    status = text(repo_root / "PROJECT_STATUS.md")
    stage_doc = text(repo_root / "docs/STAGE16_1_PUBLIC_DOCS_SYNC.md")
    all_text = "\n".join([readme, one_page, status])
    boundary = summary.get("boundary") or {}

    rows: List[Dict[str, Any]] = []
    add(rows, "readme_marker", START in readme and END in readme, "README marker block")
    add(rows, "one_page_marker", START in one_page and END in one_page, "one-page marker block")
    add(rows, "status_marker", START in status and END in status, "PROJECT_STATUS marker block")
    add(rows, "stage_doc_exists", bool(stage_doc), "docs/STAGE16_1_PUBLIC_DOCS_SYNC.md")
    add(rows, "stage15_summary_referenced", "docs/STAGE15_UPGRADE_SUMMARY.md" in all_text, "Stage 15 summary referenced")
    add(rows, "ros2_cpp_evidence", "ROS2/C++" in all_text and "GTest" in all_text, "ROS2/C++ and GTest evidence")
    add(rows, "pinocchio_jtf_evidence", "Pinocchio" in all_text and "J^T f" in all_text, "Pinocchio J^T f evidence")
    add(rows, "mujoco_smoke_evidence", "MuJoCo" in all_text and "smoke" in all_text.lower(), "MuJoCo smoke-test evidence")
    add(rows, "no_stable_locomotion_claim", "不声明稳定行走" in all_text, "stable walking explicitly not claimed")
    add(rows, "no_hardware_claim", "不声明真实机器人部署" in all_text, "hardware explicitly not claimed")
    add(rows, "no_torque_enable_claim_text", "不声明 `torque_enable_ready=True`" in all_text or "不声明 torque_enable_ready=True" in all_text, "torque-enable explicitly not claimed")
    add(rows, "boundary_no_stable", boundary.get("stable_locomotion_claimed") is False, "summary boundary")
    add(rows, "boundary_no_mpc_wbc", boundary.get("full_mpc_wbc_closed_loop_claimed") is False, "summary boundary")
    add(rows, "boundary_no_hardware", boundary.get("hardware_deployment_claimed") is False, "summary boundary")
    add(rows, "boundary_no_torque_enable", boundary.get("torque_enable_ready_claimed") is False, "summary boundary")

    passed = all(row["passed"] for row in rows)
    result = {
        "stage": "16.1",
        "validation_pass": passed,
        "files_checked": ["README.md", "docs/ONE_PAGE_TECHNICAL_REPORT.md", "PROJECT_STATUS.md", "docs/STAGE16_1_PUBLIC_DOCS_SYNC.md"],
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
    print(f"stage16_1_result: {'pass' if passed else 'fail'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
