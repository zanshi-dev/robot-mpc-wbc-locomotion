#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    root = repo_root()
    docs = root / "docs"
    logs = root / "results" / "logs_sample"
    logs.mkdir(parents=True, exist_ok=True)

    roadmap = docs / "STAGE20_RECOMMENDED_SCALE_REPRODUCIBILITY_ROADMAP.md"
    validation_csv = logs / "stage20_0_recommended_scale_reproducibility_roadmap_validation.csv"
    summary_json = logs / "stage20_0_recommended_scale_reproducibility_roadmap_summary.json"

    checks = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    check("roadmap_exists", roadmap.is_file() and roadmap.stat().st_size > 0, str(roadmap.relative_to(root)))

    text = roadmap.read_text(encoding="utf-8") if roadmap.is_file() else ""

    required_terms = [
        "Stage 20",
        "scale=0.010",
        "scale=0.020",
        "scale=0.000",
        "reproducibility",
        "replay",
        "simulation-only",
        "mean_abs_velocity_error",
        "forward_displacement",
        "min_z",
        "max_abs_roll",
        "max_abs_pitch",
        "qp_fail_steps",
        "saturation_steps",
        "reproducibility_pass",
        "recommendation_stable",
        "不新增控制器",
        "不做真实机器人部署",
        "不做多 target_vx 泛化声明",
        "不声明",
        "Stage 20.4",
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
        "stage": "20.0",
        "name": "recommended candidate scale reproducibility roadmap",
        "result": result,
        "failure_count": failure_count,
        "roadmap": str(roadmap.relative_to(root)),
        "generated_files": [
            str(validation_csv.relative_to(root)),
            str(summary_json.relative_to(root)),
        ],
        "replay_anchor_scales": [
            0.000,
            0.010,
            0.020,
        ],
        "planned_run_ids": [
            "run_00",
            "run_01",
            "run_02",
        ],
        "claim_boundary": [
            "roadmap only",
            "no new rollout generated yet",
            "no full MPC-WBC velocity controller claim",
            "no real robot torque execution claim",
            "no hardware torque enablement claim",
            "no multi-target-vx generalization claim",
        ],
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"stage20_0_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"validation_csv: {validation_csv.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
