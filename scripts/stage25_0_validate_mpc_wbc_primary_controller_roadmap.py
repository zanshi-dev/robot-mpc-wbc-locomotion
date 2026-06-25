#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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

    roadmap = docs / "STAGE25_MPC_WBC_PRIMARY_CONTROLLER_ROADMAP.md"
    stage24_4_summary = logs / "stage24_4_short_horizon_metric_evidence_freeze_summary.json"

    validation_csv = logs / "stage25_0_mpc_wbc_primary_controller_roadmap_validation.csv"
    summary_json = logs / "stage25_0_mpc_wbc_primary_controller_roadmap_summary.json"

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
        "Stage 25",
        "MPC-WBC primary controller closure",
        "simulation-only",
        "primary_mpc_wbc",
        "baseline torque + alpha * MPC/WBC candidate torque",
        "MPC/WBC torque as primary stance controller",
        "swing leg PD",
        "torque safety filter",
        "MuJoCo simulation step",
        "source audit",
        "primary_mpc_wbc mode implementation",
        "smoke rollout",
        "baseline / candidate injection / primary_mpc_wbc comparison",
        "不继续追 observable perturbation robustness",
        "不做真实机器人闭环",
        "不做 hardware torque enablement",
        "不删除 baseline 模式",
        "不删除 candidate injection 模式",
        "Stage 25.5",
        "不支持真实机器人闭环",
        "不支持工程级 MPC-WBC 控制器完全成熟",
    ]

    for term in required_terms:
        check(f"contains::{term}", term in text, term)

    s24_4 = load_json(stage24_4_summary)

    check("stage24_4_summary_exists", stage24_4_summary.is_file() and stage24_4_summary.stat().st_size > 0, str(stage24_4_summary.relative_to(root)))
    check("stage24_4_result_pass", s24_4.get("result") == "pass", f"result={s24_4.get('result')}")
    check(
        "stage24_metric_class_expected",
        s24_4.get("metric_observability_class") == "pre_step_only_detection_no_post_step_trace_separation",
        f"metric_observability_class={s24_4.get('metric_observability_class')}",
    )

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    write_csv(validation_csv, checks, ["check", "status", "detail"])

    summary = {
        "stage": "25.0",
        "name": "MPC-WBC primary controller closure roadmap",
        "result": result,
        "failure_count": failure_count,
        "roadmap": str(roadmap.relative_to(root)),
        "stage24_4_summary": str(stage24_4_summary.relative_to(root)),
        "planned_stages": [
            "25.0 roadmap",
            "25.1 source audit",
            "25.2 primary_mpc_wbc mode implementation",
            "25.3 primary_mpc_wbc smoke rollout",
            "25.4 baseline / candidate injection / primary_mpc_wbc comparison",
            "25.5 evidence freeze",
        ],
        "target_control_mode": "primary_mpc_wbc",
        "claim_boundary": [
            "roadmap only",
            "simulation-only MPC-WBC primary controller closure target",
            "no real robot torque execution claim",
            "no hardware torque enablement claim",
            "no observable perturbation robustness claim",
            "no terrain or external-force robustness claim",
        ],
        "generated_files": [
            str(validation_csv.relative_to(root)),
            str(summary_json.relative_to(root)),
        ],
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"stage25_0_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"validation_csv: {validation_csv.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
