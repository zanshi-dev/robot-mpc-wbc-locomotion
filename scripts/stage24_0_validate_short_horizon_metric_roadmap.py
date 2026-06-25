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

    roadmap = docs / "STAGE24_SHORT_HORIZON_PERTURBATION_METRIC_ROADMAP.md"
    s23_4_summary = logs / "stage23_4_perturbation_observability_evidence_freeze_summary.json"

    validation_csv = logs / "stage24_0_short_horizon_metric_roadmap_validation.csv"
    summary_json = logs / "stage24_0_short_horizon_metric_roadmap_summary.json"

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
        "Stage 24",
        "短时扰动敏感指标",
        "short-horizon",
        "perturbation-sensitive metrics",
        "Stage 22",
        "Stage 23",
        "C_summary_metrics_insensitive_to_short_horizon_trace_change",
        "all_nonzero_perturbations_written=True",
        "all_after_forward_preserved=True",
        "any_first_step_state_changed=True",
        "summary 指标对短时初始 qvel 扰动不敏感",
        "injection_written",
        "after_forward_preserved",
        "first_step_qvel_delta",
        "qpos_delta_first_step",
        "early_window_trace_separation_detected",
        "max_abs_qvel_axis_diff_vs_nominal",
        "mean_abs_qvel_axis_diff_vs_nominal",
        "early_window_max_abs_state_delta",
        "不新增控制器",
        "不重新声明 observable perturbation robustness",
        "不做真实机器人部署",
        "不声明 scale=0.010",
        "Stage 24.4",
    ]

    for term in required_terms:
        check(f"contains::{term}", term in text, term)

    s23_4 = load_json(s23_4_summary)

    check("stage23_4_summary_exists", s23_4_summary.is_file() and s23_4_summary.stat().st_size > 0, str(s23_4_summary.relative_to(root)))
    check("stage23_4_result_pass", s23_4.get("result") == "pass", f"result={s23_4.get('result')}")
    check(
        "stage23_4_root_cause_expected",
        s23_4.get("overall_root_cause") == "C_summary_metrics_insensitive_to_short_horizon_trace_change",
        f"overall_root_cause={s23_4.get('overall_root_cause')}",
    )
    check(
        "stage23_4_confidence_high",
        s23_4.get("root_cause_confidence") == "high",
        f"root_cause_confidence={s23_4.get('root_cause_confidence')}",
    )

    trace_files = [
        logs / "stage23_2_qvel_injection_trace_nominal_0p010.csv",
        logs / "stage23_2_qvel_injection_trace_vx_plus_0p010.csv",
        logs / "stage23_2_qvel_injection_trace_vx_minus_0p010.csv",
        logs / "stage23_2_qvel_injection_trace_vy_plus_0p010.csv",
        logs / "stage23_2_qvel_injection_trace_vy_minus_0p010.csv",
        logs / "stage23_2_qvel_injection_trace_yawrate_plus_0p010.csv",
        logs / "stage23_2_qvel_injection_trace_yawrate_minus_0p010.csv",
    ]

    for path in trace_files:
        check(f"trace_exists::{path.name}", path.is_file() and path.stat().st_size > 0, str(path.relative_to(root)))

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    write_csv(validation_csv, checks, ["check", "status", "detail"])

    summary = {
        "stage": "24.0",
        "name": "short-horizon perturbation-sensitive metric roadmap",
        "result": result,
        "failure_count": failure_count,
        "roadmap": str(roadmap.relative_to(root)),
        "stage23_4_summary": str(s23_4_summary.relative_to(root)),
        "stage23_root_cause": s23_4.get("overall_root_cause"),
        "planned_stages": [
            "24.0 roadmap",
            "24.1 metric design preflight",
            "24.2 compute short-horizon perturbation-sensitive metrics",
            "24.3 analyze short-horizon metric observability",
            "24.4 evidence freeze",
        ],
        "planned_metric_groups": [
            "injection preservation metrics",
            "first-step response metrics",
            "trace separation versus nominal",
            "early-window state delta metrics",
        ],
        "claim_boundary": [
            "roadmap only",
            "no new rollout generated yet",
            "metric audit only",
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

    print(f"stage24_0_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"validation_csv: {validation_csv.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
