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

    roadmap = docs / "STAGE21_RECOMMENDED_SCALE_LOCAL_ROBUSTNESS_ROADMAP.md"
    validation_csv = logs / "stage21_0_local_robustness_roadmap_validation.csv"
    summary_json = logs / "stage21_0_local_robustness_roadmap_summary.json"

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
        "Stage 21",
        "local robustness",
        "local perturbation",
        "scale=0.010",
        "scale=0.020",
        "scale=0.000",
        "nominal",
        "x_plus",
        "x_minus",
        "y_plus",
        "y_minus",
        "yaw_plus",
        "yaw_minus",
        "target_vx",
        "mean_abs_velocity_error",
        "forward_displacement",
        "min_z",
        "max_abs_roll",
        "max_abs_pitch",
        "qp_fail_steps",
        "saturation_steps",
        "local_robustness_pass",
        "recommendation_robust",
        "不新增控制器",
        "不做真实机器人部署",
        "不做多 target_vx 泛化声明",
        "不声明",
        "Stage 21.4",
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
        "stage": "21.0",
        "name": "recommended scale local robustness roadmap",
        "result": result,
        "failure_count": failure_count,
        "roadmap": str(roadmap.relative_to(root)),
        "generated_files": [
            str(validation_csv.relative_to(root)),
            str(summary_json.relative_to(root)),
        ],
        "perturbation_cases": [
            {"perturbation_id": "nominal", "perturb_x": 0.00, "perturb_y": 0.00, "perturb_yaw": 0.00},
            {"perturbation_id": "x_plus", "perturb_x": 0.02, "perturb_y": 0.00, "perturb_yaw": 0.00},
            {"perturbation_id": "x_minus", "perturb_x": -0.02, "perturb_y": 0.00, "perturb_yaw": 0.00},
            {"perturbation_id": "y_plus", "perturb_x": 0.00, "perturb_y": 0.02, "perturb_yaw": 0.00},
            {"perturbation_id": "y_minus", "perturb_x": 0.00, "perturb_y": -0.02, "perturb_yaw": 0.00},
            {"perturbation_id": "yaw_plus", "perturb_x": 0.00, "perturb_y": 0.00, "perturb_yaw": 0.03},
            {"perturbation_id": "yaw_minus", "perturb_x": 0.00, "perturb_y": 0.00, "perturb_yaw": -0.03},
        ],
        "scale_anchors": [
            0.000,
            0.010,
            0.020,
        ],
        "planned_rollout_count": 21,
        "claim_boundary": [
            "roadmap only",
            "no new rollout generated yet",
            "no full MPC-WBC velocity controller claim",
            "no real robot torque execution claim",
            "no hardware torque enablement claim",
            "no multi-target-vx generalization claim",
            "no terrain generalization claim",
        ],
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"stage21_0_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"validation_csv: {validation_csv.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
