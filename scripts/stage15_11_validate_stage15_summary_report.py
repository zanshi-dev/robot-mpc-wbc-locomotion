#!/usr/bin/env python3
"""Validate Stage 15.11 Stage 15 summary report."""

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
    parser.add_argument("--report-json", type=Path, required=True)
    parser.add_argument("--report-md", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args(argv)

    report = json.loads(args.report_json.read_text(encoding="utf-8"))
    md_text = args.report_md.read_text(encoding="utf-8") if args.report_md.exists() else ""
    boundary = report.get("boundary") or {}
    stages = report.get("stages") or []
    rows: List[Dict[str, Any]] = []

    add(rows, "stage_count_10", int(report.get("total_stage_count", 0)) == 10, f"total={report.get('total_stage_count')}")
    add(rows, "completed_count_10", int(report.get("completed_stage_count", 0)) == 10, f"completed={report.get('completed_stage_count')}")
    add(rows, "all_stage15_completed", report.get("all_stage15_1_to_15_10_completed") is True, str(report.get("all_stage15_1_to_15_10_completed")))
    add(rows, "all_stage_rows_completed", all(row.get("completed") is True for row in stages), "each stage row completed")
    add(rows, "markdown_exists", args.report_md.exists(), str(args.report_md))
    add(rows, "markdown_has_claim_section", "What can be claimed" in md_text, "claim section")
    add(rows, "markdown_has_nonclaim_section", "What cannot be claimed" in md_text, "non-claim section")
    add(rows, "markdown_mentions_simulation_only", "simulation-only" in md_text or "simulation_only" in json.dumps(report), "simulation-only boundary")
    add(rows, "no_hardware_claim", boundary.get("hardware_deployment_claimed") is False, "hardware_deployment_claimed false")
    add(rows, "no_torque_enable_claim", boundary.get("torque_enable_ready_claimed") is False, "torque_enable_ready_claimed false")
    add(rows, "no_stable_locomotion_claim", boundary.get("stable_locomotion_from_stage15_claimed") is False, "stable_locomotion_from_stage15_claimed false")
    add(rows, "no_full_mpc_wbc_claim", boundary.get("full_mpc_wbc_closed_loop_claimed") is False, "full_mpc_wbc_closed_loop_claimed false")
    add(rows, "claimable_items_present", len(report.get("claimable_items", [])) >= 5, f"count={len(report.get('claimable_items', []))}")
    add(rows, "non_claimable_items_present", len(report.get("non_claimable_items", [])) >= 5, f"count={len(report.get('non_claimable_items', []))}")

    passed = all(row["passed"] for row in rows)
    result = {
        "stage": "15.11",
        "validation_pass": passed,
        "completed_stage_count": report.get("completed_stage_count", 0),
        "total_stage_count": report.get("total_stage_count", 0),
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
    print(f"stage15_11_result: {'pass' if passed else 'fail'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
