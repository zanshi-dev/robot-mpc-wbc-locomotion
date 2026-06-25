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


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def trace_cases(logs: Path) -> list[dict[str, str]]:
    return [
        {
            "case_id": "nominal_0p010",
            "perturbation_id": "nominal",
            "perturbation_type": "none",
            "axis": "qvel_0",
            "qpos_axis": "qpos_0",
            "nominal_ref": "self",
            "trace_csv": str((logs / "stage23_2_qvel_injection_trace_nominal_0p010.csv")),
        },
        {
            "case_id": "vx_plus_0p010",
            "perturbation_id": "vx_plus",
            "perturbation_type": "base_vx",
            "axis": "qvel_0",
            "qpos_axis": "qpos_0",
            "nominal_ref": "nominal_0p010",
            "trace_csv": str((logs / "stage23_2_qvel_injection_trace_vx_plus_0p010.csv")),
        },
        {
            "case_id": "vx_minus_0p010",
            "perturbation_id": "vx_minus",
            "perturbation_type": "base_vx",
            "axis": "qvel_0",
            "qpos_axis": "qpos_0",
            "nominal_ref": "nominal_0p010",
            "trace_csv": str((logs / "stage23_2_qvel_injection_trace_vx_minus_0p010.csv")),
        },
        {
            "case_id": "vy_plus_0p010",
            "perturbation_id": "vy_plus",
            "perturbation_type": "base_vy",
            "axis": "qvel_1",
            "qpos_axis": "qpos_1",
            "nominal_ref": "nominal_0p010",
            "trace_csv": str((logs / "stage23_2_qvel_injection_trace_vy_plus_0p010.csv")),
        },
        {
            "case_id": "vy_minus_0p010",
            "perturbation_id": "vy_minus",
            "perturbation_type": "base_vy",
            "axis": "qvel_1",
            "qpos_axis": "qpos_1",
            "nominal_ref": "nominal_0p010",
            "trace_csv": str((logs / "stage23_2_qvel_injection_trace_vy_minus_0p010.csv")),
        },
        {
            "case_id": "yawrate_plus_0p010",
            "perturbation_id": "yawrate_plus",
            "perturbation_type": "base_yawrate",
            "axis": "qvel_5",
            "qpos_axis": "qpos_3",
            "nominal_ref": "nominal_0p010",
            "trace_csv": str((logs / "stage23_2_qvel_injection_trace_yawrate_plus_0p010.csv")),
        },
        {
            "case_id": "yawrate_minus_0p010",
            "perturbation_id": "yawrate_minus",
            "perturbation_type": "base_yawrate",
            "axis": "qvel_5",
            "qpos_axis": "qpos_3",
            "nominal_ref": "nominal_0p010",
            "trace_csv": str((logs / "stage23_2_qvel_injection_trace_yawrate_minus_0p010.csv")),
        },
    ]


def main() -> int:
    root = repo_root()
    docs = root / "docs"
    logs = root / "results" / "logs_sample"
    docs.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    stage24_0_summary = logs / "stage24_0_short_horizon_metric_roadmap_summary.json"
    stage23_4_summary = logs / "stage23_4_perturbation_observability_evidence_freeze_summary.json"
    stage23_3_summary = logs / "stage23_3_perturbation_observability_root_cause_summary.json"

    validation_csv = logs / "stage24_1_short_horizon_metric_preflight_validation.csv"
    metric_design_csv = logs / "stage24_1_short_horizon_metric_design.csv"
    trace_input_plan_csv = logs / "stage24_1_short_horizon_metric_trace_input_plan.csv"
    summary_json = logs / "stage24_1_short_horizon_metric_preflight_summary.json"
    doc = docs / "STAGE24_1_SHORT_HORIZON_METRIC_PREFLIGHT.md"

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    s24_0 = load_json(stage24_0_summary)
    s23_4 = load_json(stage23_4_summary)
    s23_3 = load_json(stage23_3_summary)

    check("stage24_0_summary_exists", stage24_0_summary.is_file() and stage24_0_summary.stat().st_size > 0, str(stage24_0_summary.relative_to(root)))
    check("stage24_0_result_pass", s24_0.get("result") == "pass", f"result={s24_0.get('result')}")

    check("stage23_4_summary_exists", stage23_4_summary.is_file() and stage23_4_summary.stat().st_size > 0, str(stage23_4_summary.relative_to(root)))
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

    check("stage23_3_summary_exists", stage23_3_summary.is_file() and stage23_3_summary.stat().st_size > 0, str(stage23_3_summary.relative_to(root)))
    check("stage23_3_result_pass", s23_3.get("result") == "pass", f"result={s23_3.get('result')}")

    expected_flags = [
        ("stage23_2_all_nonzero_perturbations_written", True),
        ("stage23_2_all_after_forward_preserved", True),
        ("stage23_2_any_first_step_state_changed", True),
    ]
    for key, expected in expected_flags:
        check(f"stage23_4_flag::{key}", s23_4.get(key) is expected, f"{key}={s23_4.get(key)}")

    cases = trace_cases(logs)
    trace_plan_rows = []

    required_columns = [
        "trace_case_id",
        "perturbation_id",
        "perturbation_type",
        "perturb_vx",
        "perturb_vy",
        "perturb_yawrate",
        "scale",
        "scale_tag",
        "control_mode",
        "phase",
        "trace_step_index",
        "time",
        "qpos_0",
        "qpos_1",
        "qpos_2",
        "qpos_3",
        "qvel_0",
        "qvel_1",
        "qvel_5",
        "base_x",
        "base_y",
        "base_z",
        "base_vx_fd",
        "base_vy_fd",
    ]

    required_phases = [
        "before_injection",
        "after_injection",
        "after_mj_forward",
        "after_mj_step",
    ]

    for case in cases:
        trace_path = Path(case["trace_csv"])
        rel = trace_path.relative_to(root)

        check(f"trace_exists::{case['case_id']}", trace_path.is_file() and trace_path.stat().st_size > 0, str(rel))

        rows = read_rows(trace_path)
        check(f"trace_rows_nonempty::{case['case_id']}", len(rows) > 0, f"rows={len(rows)}")
        check(f"trace_rows_at_least_15::{case['case_id']}", len(rows) >= 15, f"rows={len(rows)}")

        cols = set(rows[0].keys()) if rows else set()
        for col in required_columns:
            check(f"trace_has::{case['case_id']}::{col}", col in cols, col)

        phases = {r.get("phase", "") for r in rows}
        for phase in required_phases:
            check(f"trace_phase::{case['case_id']}::{phase}", phase in phases, phase)

        step_rows = [r for r in rows if r.get("phase") == "after_mj_step"]
        check(f"trace_after_step_count_at_least_12::{case['case_id']}", len(step_rows) >= 12, f"after_mj_step_count={len(step_rows)}")

        trace_plan_rows.append({
            "case_id": case["case_id"],
            "perturbation_id": case["perturbation_id"],
            "perturbation_type": case["perturbation_type"],
            "axis": case["axis"],
            "qpos_axis": case["qpos_axis"],
            "nominal_ref": case["nominal_ref"],
            "trace_csv": str(rel),
            "row_count": str(len(rows)),
            "after_mj_step_count": str(len(step_rows)),
            "ready_for_stage24_2": str(trace_path.is_file() and len(rows) >= 15 and len(step_rows) >= 12),
        })

    metric_rows = [
        {
            "metric_name": "injection_written",
            "metric_group": "injection_preservation",
            "source": "stage23_3 per-case diagnostic",
            "description": "Whether qvel perturbation was written to the selected qvel axis.",
            "expected_use": "confirm perturbation injection validity",
        },
        {
            "metric_name": "after_forward_preserved",
            "metric_group": "injection_preservation",
            "source": "stage23_3 per-case diagnostic",
            "description": "Whether injected qvel perturbation was preserved after mujoco.mj_forward.",
            "expected_use": "confirm simulation-state synchronization did not erase injection",
        },
        {
            "metric_name": "written_delta",
            "metric_group": "injection_preservation",
            "source": "stage23_3 per-case diagnostic",
            "description": "Injected qvel delta relative to before_injection.",
            "expected_use": "quantify qvel injection magnitude",
        },
        {
            "metric_name": "after_forward_delta",
            "metric_group": "injection_preservation",
            "source": "stage23_3 per-case diagnostic",
            "description": "qvel delta after mj_forward relative to before_injection.",
            "expected_use": "quantify preserved qvel delta",
        },
        {
            "metric_name": "first_step_qvel_delta",
            "metric_group": "first_step_response",
            "source": "stage23_2 trace",
            "description": "Selected qvel-axis change from before_injection to first after_mj_step.",
            "expected_use": "measure immediate qvel response",
        },
        {
            "metric_name": "qpos_delta_first_step",
            "metric_group": "first_step_response",
            "source": "stage23_2 trace",
            "description": "Selected qpos-axis change from before_injection to first after_mj_step.",
            "expected_use": "measure immediate position response",
        },
        {
            "metric_name": "max_abs_qvel_axis_diff_vs_nominal",
            "metric_group": "trace_separation_vs_nominal",
            "source": "aligned early-window trace",
            "description": "Maximum absolute selected qvel-axis difference versus nominal over early-window steps.",
            "expected_use": "detect perturbation-sensitive qvel trace separation",
        },
        {
            "metric_name": "mean_abs_qvel_axis_diff_vs_nominal",
            "metric_group": "trace_separation_vs_nominal",
            "source": "aligned early-window trace",
            "description": "Mean absolute selected qvel-axis difference versus nominal over early-window steps.",
            "expected_use": "detect average qvel trace separation",
        },
        {
            "metric_name": "max_abs_qpos_axis_diff_vs_nominal",
            "metric_group": "trace_separation_vs_nominal",
            "source": "aligned early-window trace",
            "description": "Maximum absolute selected qpos-axis difference versus nominal over early-window steps.",
            "expected_use": "detect perturbation-sensitive qpos trace separation",
        },
        {
            "metric_name": "mean_abs_qpos_axis_diff_vs_nominal",
            "metric_group": "trace_separation_vs_nominal",
            "source": "aligned early-window trace",
            "description": "Mean absolute selected qpos-axis difference versus nominal over early-window steps.",
            "expected_use": "detect average qpos trace separation",
        },
        {
            "metric_name": "max_abs_base_vx_fd_diff_vs_nominal",
            "metric_group": "trace_separation_vs_nominal",
            "source": "aligned early-window trace",
            "description": "Maximum absolute base_vx_fd difference versus nominal over early-window steps.",
            "expected_use": "detect finite-difference velocity separation",
        },
        {
            "metric_name": "max_abs_base_vy_fd_diff_vs_nominal",
            "metric_group": "trace_separation_vs_nominal",
            "source": "aligned early-window trace",
            "description": "Maximum absolute base_vy_fd difference versus nominal over early-window steps.",
            "expected_use": "detect lateral finite-difference velocity separation",
        },
        {
            "metric_name": "early_window_max_abs_state_delta",
            "metric_group": "early_window_state_delta",
            "source": "aligned early-window trace",
            "description": "Maximum absolute combined state delta versus nominal using selected qvel/qpos/base velocity channels.",
            "expected_use": "single scalar for short-horizon perturbation observability",
        },
        {
            "metric_name": "early_window_mean_abs_state_delta",
            "metric_group": "early_window_state_delta",
            "source": "aligned early-window trace",
            "description": "Mean absolute combined state delta versus nominal using selected qvel/qpos/base velocity channels.",
            "expected_use": "average scalar for short-horizon perturbation observability",
        },
        {
            "metric_name": "early_window_trace_separation_detected",
            "metric_group": "early_window_state_delta",
            "source": "computed metrics",
            "description": "Boolean indicating whether early-window trace separation exceeds numerical tolerance.",
            "expected_use": "decide whether short-horizon metrics detect perturbation",
        },
    ]

    write_csv(
        trace_input_plan_csv,
        trace_plan_rows,
        [
            "case_id",
            "perturbation_id",
            "perturbation_type",
            "axis",
            "qpos_axis",
            "nominal_ref",
            "trace_csv",
            "row_count",
            "after_mj_step_count",
            "ready_for_stage24_2",
        ],
    )

    write_csv(
        metric_design_csv,
        metric_rows,
        [
            "metric_name",
            "metric_group",
            "source",
            "description",
            "expected_use",
        ],
    )

    check("trace_case_count_7", len(trace_plan_rows) == 7, f"count={len(trace_plan_rows)}")
    check("metric_design_count_at_least_10", len(metric_rows) >= 10, f"count={len(metric_rows)}")
    check("all_trace_inputs_ready_for_stage24_2", all(r["ready_for_stage24_2"] == "True" for r in trace_plan_rows), "all ready")
    check("nominal_reference_available", any(r["case_id"] == "nominal_0p010" for r in trace_plan_rows), "nominal_0p010")
    check("metric_design_includes_trace_separation", any(r["metric_group"] == "trace_separation_vs_nominal" for r in metric_rows), "trace_separation_vs_nominal")
    check("metric_design_includes_early_window_delta", any(r["metric_group"] == "early_window_state_delta" for r in metric_rows), "early_window_state_delta")
    check("metric_design_includes_injection_preservation", any(r["metric_group"] == "injection_preservation" for r in metric_rows), "injection_preservation")
    check("metric_design_includes_first_step_response", any(r["metric_group"] == "first_step_response" for r in metric_rows), "first_step_response")

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    write_csv(validation_csv, checks, ["check", "status", "detail"])

    summary = {
        "stage": "24.1",
        "name": "short-horizon metric design preflight",
        "result": result,
        "failure_count": failure_count,
        "stage23_root_cause": s23_4.get("overall_root_cause"),
        "trace_case_count": len(trace_plan_rows),
        "metric_design_count": len(metric_rows),
        "all_trace_inputs_ready_for_stage24_2": all(r["ready_for_stage24_2"] == "True" for r in trace_plan_rows),
        "trace_input_plan": trace_plan_rows,
        "metric_design": metric_rows,
        "stage24_2_requirements": [
            "read nominal trace and perturbation traces",
            "align after_mj_step rows by trace_step_index",
            "compute selected-axis qvel/qpos separation versus nominal",
            "compute base finite-difference velocity separation versus nominal",
            "compute early-window max/mean absolute state deltas",
            "produce per-case and aggregate short-horizon perturbation-sensitive metric tables",
        ],
        "claim_boundary": [
            "preflight only",
            "no new rollout generated",
            "metric design only",
            "no observable perturbation robustness claim",
            "no full MPC-WBC velocity controller claim",
            "no real robot torque execution claim",
            "no hardware torque enablement claim",
            "no terrain or external-force robustness claim",
        ],
        "generated_files": [
            str(validation_csv.relative_to(root)),
            str(metric_design_csv.relative_to(root)),
            str(trace_input_plan_csv.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(doc.relative_to(root)),
        ],
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    md_metric_lines = [
        "| metric_name | metric_group | expected_use |",
        "|---|---|---|",
    ]
    for row in metric_rows:
        md_metric_lines.append(f"| {row['metric_name']} | {row['metric_group']} | {row['expected_use']} |")

    md_trace_lines = [
        "| case_id | axis | qpos_axis | trace_csv | ready_for_stage24_2 |",
        "|---|---|---|---|---|",
    ]
    for row in trace_plan_rows:
        md_trace_lines.append(
            f"| {row['case_id']} | {row['axis']} | {row['qpos_axis']} | `{row['trace_csv']}` | {row['ready_for_stage24_2']} |"
        )

    doc.write_text(f"""# Stage 24.1：short-horizon metric design preflight

## 1. 目标

Stage 24.1 检查 Stage 23.2 的 qvel injection trace 数据是否足够支持 Stage 24.2 计算短时扰动敏感指标。

本阶段不新增 rollout，不新增控制器，只做数据字段检查和指标设计。

## 2. 结果

Stage 24.1 result: {result}

Failure count: {failure_count}

Trace case count: {len(trace_plan_rows)}

Metric design count: {len(metric_rows)}

All trace inputs ready for Stage 24.2: {all(r["ready_for_stage24_2"] == "True" for r in trace_plan_rows)}

## 3. Stage 23 根因背景

    overall_root_cause={s23_4.get("overall_root_cause")}
    root_cause_confidence={s23_4.get("root_cause_confidence")}
    stage23_2_all_nonzero_perturbations_written={s23_4.get("stage23_2_all_nonzero_perturbations_written")}
    stage23_2_all_after_forward_preserved={s23_4.get("stage23_2_all_after_forward_preserved")}
    stage23_2_any_first_step_state_changed={s23_4.get("stage23_2_any_first_step_state_changed")}

## 4. Trace 输入计划

{chr(10).join(md_trace_lines)}

## 5. 指标设计

{chr(10).join(md_metric_lines)}

## 6. Stage 24.2 计算要求

Stage 24.2 应：

  * 读取 nominal trace 和 6 个 perturbation trace；
  * 按 `trace_step_index` 对齐 `after_mj_step` 行；
  * 计算 qvel/qpos/base finite-difference velocity 相对 nominal 的短时差异；
  * 输出 per-case metric table；
  * 输出 aggregate metric summary；
  * 判断 `early_window_trace_separation_detected` 是否为 True。

## 7. 结论边界

Stage 24.1 只是 metric design preflight，不声明 observable perturbation robustness，不声明完整 MPC-WBC 速度控制器完成，不涉及真实机器人和硬件 torque enablement。
""", encoding="utf-8")

    print(f"stage24_1_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"trace_case_count: {len(trace_plan_rows)}")
    print(f"metric_design_count: {len(metric_rows)}")
    print(f"all_trace_inputs_ready_for_stage24_2: {all(r['ready_for_stage24_2'] == 'True' for r in trace_plan_rows)}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"trace_input_plan: {trace_input_plan_csv.relative_to(root)}")
    print(f"metric_design: {metric_design_csv.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
