#!/usr/bin/env python3
"""Validate Stage 16.2 artifact index."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

REQUIRED_STAGES = {f"15.{i}" for i in range(1, 12)} | {"16.1", "16.2"}
README_START = "<!-- STAGE16_2_ARTIFACT_INDEX_START -->"
README_END = "<!-- STAGE16_2_ARTIFACT_INDEX_END -->"


def add(rows: List[Dict[str, Any]], name: str, passed: bool, details: str) -> None:
    rows.append({"check": name, "passed": bool(passed), "details": details})


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--summary-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    summary = json.loads(args.summary_json.read_text(encoding="utf-8"))
    rows_data = summary.get("rows") or []
    stages = set(summary.get("stages") or [])
    md_path = repo_root / "docs/ARTIFACT_INDEX.md"
    readme_path = repo_root / "README.md"
    md_text = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    readme_text = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    checks: List[Dict[str, Any]] = []

    add(checks, "artifact_count_positive", int(summary.get("artifact_count", 0)) > 0, f"count={summary.get('artifact_count')}")
    add(checks, "required_stage_coverage", REQUIRED_STAGES.issubset(stages), f"missing={sorted(REQUIRED_STAGES - stages)}")
    add(checks, "artifact_index_exists", md_path.exists(), str(md_path))
    add(checks, "artifact_index_has_stage_coverage", "## Stage Coverage" in md_text, "Stage Coverage section")
    add(checks, "artifact_index_has_details", "## Detailed Artifacts" in md_text, "Detailed Artifacts section")
    add(checks, "readme_link_marker", README_START in readme_text and README_END in readme_text, "README marker block")
    add(checks, "readme_links_artifact_index", "docs/ARTIFACT_INDEX.md" in readme_text, "README artifact index link")
    missing_paths = [row["path"] for row in rows_data if not (repo_root / row["path"]).exists()]
    add(checks, "all_indexed_paths_exist", not missing_paths, f"missing={missing_paths[:5]}")
    rel_abs = [row["path"] for row in rows_data if str(row["path"]).startswith("/")]
    add(checks, "all_paths_relative", not rel_abs, f"absolute_paths={rel_abs[:5]}")
    categories = {row.get("category") for row in rows_data}
    add(checks, "has_scripts", "script" in categories, f"categories={sorted(categories)}")
    add(checks, "has_docs", "doc" in categories, f"categories={sorted(categories)}")
    add(checks, "has_results", "result" in categories, f"categories={sorted(categories)}")
    add(checks, "has_logs", "log" in categories, f"categories={sorted(categories)}")

    passed = all(row["passed"] for row in checks)
    result = {
        "stage": "16.2",
        "validation_pass": passed,
        "artifact_count": summary.get("artifact_count", 0),
        "stage_count": summary.get("stage_count", 0),
        "checks": checks,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    with args.output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "passed", "details"])
        writer.writeheader()
        writer.writerows(checks)

    for row in checks:
        print(f"{'PASS' if row['passed'] else 'FAIL'}: {row['check']} -- {row['details']}")
    print(f"stage16_2_result: {'pass' if passed else 'fail'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
