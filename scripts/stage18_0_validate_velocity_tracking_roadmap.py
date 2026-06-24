#!/usr/bin/env python3
from pathlib import Path
import csv
import json


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    root = repo_root()
    doc = root / "docs" / "STAGE18_VELOCITY_TRACKING_ROADMAP.md"
    log_dir = root / "results" / "logs_sample"
    log_dir.mkdir(parents=True, exist_ok=True)

    validation_csv = log_dir / "stage18_0_velocity_tracking_roadmap_validation.csv"
    summary_json = log_dir / "stage18_0_velocity_tracking_roadmap_summary.json"

    checks = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    check("roadmap_exists", doc.is_file() and doc.stat().st_size > 0, str(doc.relative_to(root)))

    text = doc.read_text(encoding="utf-8") if doc.is_file() else ""

    required_terms = [
        "velocity tracking evidence",
        "base_x",
        "base_vx",
        "target_vx",
        "mean_vx",
        "mean_abs_velocity_error",
        "baseline vs candidate",
        "simulation-only",
        "finite difference",
        "Stage 18.1",
        "Stage 18.4",
    ]

    for term in required_terms:
        check(f"contains::{term}", term in text, term)

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    with validation_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "status", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    summary = {
        "stage": "18.0",
        "name": "velocity tracking roadmap validation",
        "result": result,
        "failure_count": failure_count,
        "roadmap": str(doc.relative_to(root)),
        "generated_files": [
            str(validation_csv.relative_to(root)),
            str(summary_json.relative_to(root)),
        ],
        "claim_boundary": [
            "roadmap only",
            "no velocity tracking runner implemented yet",
            "no real robot control claim",
            "no hardware torque enablement claim",
            "no comprehensive MPC/WBC superiority claim",
        ],
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"stage18_0_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"validation_csv: {validation_csv.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
