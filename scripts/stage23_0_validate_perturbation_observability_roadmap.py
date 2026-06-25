#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    root = repo_root()
    docs = root / "docs"
    logs = root / "results" / "logs_sample"
    logs.mkdir(parents=True, exist_ok=True)

    roadmap = docs / "STAGE23_PERTURBATION_OBSERVABILITY_ROOT_CAUSE_ROADMAP.md"
    s22_4_summary = logs / "stage22_4_observable_perturbation_evidence_freeze_summary.json"
    validation_csv = logs / "stage23_0_perturbation_observability_roadmap_validation.csv"
    summary_json = logs / "stage23_0_perturbation_observability_roadmap_summary.json"

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    check("roadmap_exists", roadmap.is_file() and roadmap.stat().st_size > 0, str(roadmap.relative_to(root)))

    text = roadmap.read_text(encoding="utf-8") if roadmap.is_file() else ""

    required_terms = [
        "Stage 23",
        "扰动可观测性",
        "根因审计",
        "Stage 22",
        "observable_perturbation_pass=False",
        "perturbation_metric_variability_detected=False",
        "recommendation_observable_robust=False",
        "qvel",
        "data.qvel",
        "mujoco.mj_forward",
        "mujoco.mj_step",
        "qpos",
        "base_vx_fd",
        "base_vy_fd",
        "qvel_before_injection",
        "qvel_after_injection",
        "qvel_after_mj_forward",
        "qvel_after_first_step",
        "summary 指标",
        "不新增控制器",
        "不做真实机器人部署",
        "不重新声明 observable perturbation robustness",
        "不声明 scale=0.010",
        "Stage 23.4",
    ]

    for term in required_terms:
        check(f"contains::{term}", term in text, term)

    if s22_4_summary.is_file():
        s22_4 = json.loads(s22_4_summary.read_text(encoding="utf-8"))
    else:
        s22_4 = {}

    check("stage22_4_summary_exists", s22_4_summary.is_file() and s22_4_summary.stat().st_size > 0, str(s22_4_summary.relative_to(root)))
    check("stage22_4_result_pass", s22_4.get("result") == "pass", f"result={s22_4.get('result')}")
    check(
        "stage22_4_observable_false",
        s22_4.get("perturbation_metric_variability_detected") is False,
        f"perturbation_metric_variability_detected={s22_4.get('perturbation_metric_variability_detected')}",
    )
    check(
        "stage22_4_recommendation_observable_false",
        s22_4.get("recommendation_observable_robust") is False,
        f"recommendation_observable_robust={s22_4.get('recommendation_observable_robust')}",
    )

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    write_csv(validation_csv, checks, ["check", "status", "detail"])

    summary = {
        "stage": "23.0",
        "name": "perturbation observability root-cause roadmap",
        "result": result,
        "failure_count": failure_count,
        "roadmap": str(roadmap.relative_to(root)),
        "stage22_4_summary": str(s22_4_summary.relative_to(root)),
        "planned_stages": [
            "23.0 roadmap",
            "23.1 qvel injection trace preflight",
            "23.2 qvel injection trace diagnostic",
            "23.3 perturbation observability root-cause analysis",
            "23.4 evidence freeze",
        ],
        "root_cause_hypotheses": [
            "qvel perturbation was not actually written",
            "qvel perturbation was written but overwritten or absorbed before rollout metrics",
            "qvel perturbation caused short-horizon changes but summary metrics were insensitive",
        ],
        "claim_boundary": [
            "roadmap only",
            "no new rollout generated yet",
            "no observable perturbation robustness claim",
            "no full MPC-WBC velocity controller claim",
            "no real robot torque execution claim",
            "no hardware torque enablement claim",
            "no terrain or external-force robustness claim",
        ],
        "generated_files": [
            str(validation_csv.relative_to(root)),
            str(summary_json.relative_to(root)),
        ],
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"stage23_0_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"validation_csv: {validation_csv.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
