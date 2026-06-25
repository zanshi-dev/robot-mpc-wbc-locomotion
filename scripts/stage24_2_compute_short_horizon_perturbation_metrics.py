#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean


TOL = 1e-12


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


def fval(row: dict[str, str] | None, key: str, default: float = 0.0) -> float:
    if row is None:
        return default
    try:
        return float(row.get(key, default))
    except Exception:
        return default


def bval(value) -> bool:
    return str(value).strip().lower() == "true"


def phase_row(rows: list[dict[str, str]], phase: str) -> dict[str, str] | None:
    for row in rows:
        if row.get("phase") == phase:
            return row
    return None


def after_step_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out = []
    for row in rows:
        if row.get("phase") != "after_mj_step":
            continue
        try:
            int(row.get("trace_step_index", "0"))
        except Exception:
            continue
        out.append(row)
    return sorted(out, key=lambda r: int(r.get("trace_step_index", "0")))


def rows_by_step(rows: list[dict[str, str]]) -> dict[int, dict[str, str]]:
    out = {}
    for row in after_step_rows(rows):
        out[int(row.get("trace_step_index", "0"))] = row
    return out


def abs_diff(row: dict[str, str] | None, ref: dict[str, str] | None, key: str) -> float:
    return abs(fval(row, key) - fval(ref, key))


def max_or_zero(values: list[float]) -> float:
    return max(values) if values else 0.0


def mean_or_zero(values: list[float]) -> float:
    return mean(values) if values else 0.0


def markdown_table(rows: list[dict[str, str]], cols: list[str]) -> str:
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(c, "")) for c in cols) + " |")
    return "\n".join(lines)


def main() -> int:
    root = repo_root()
    logs = root / "results" / "logs_sample"
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    s24_1_path = logs / "stage24_1_short_horizon_metric_preflight_summary.json"
    s23_4_path = logs / "stage23_4_perturbation_observability_evidence_freeze_summary.json"
    trace_plan_path = logs / "stage24_1_short_horizon_metric_trace_input_plan.csv"
    stage23_diag_path = logs / "stage23_3_perturbation_observability_root_cause_per_case.csv"

    per_case_csv = logs / "stage24_2_short_horizon_perturbation_metrics_per_case.csv"
    aggregate_csv = logs / "stage24_2_short_horizon_perturbation_metrics_aggregate.csv"
    validation_csv = logs / "stage24_2_short_horizon_perturbation_metrics_validation.csv"
    metrics_md = logs / "stage24_2_short_horizon_perturbation_metrics.md"
    summary_json = logs / "stage24_2_short_horizon_perturbation_metrics_summary.json"
    doc = docs / "STAGE24_2_SHORT_HORIZON_PERTURBATION_METRICS.md"

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    s24_1 = load_json(s24_1_path)
    s23_4 = load_json(s23_4_path)

    check("stage24_1_summary_exists", s24_1_path.is_file() and s24_1_path.stat().st_size > 0, str(s24_1_path.relative_to(root)))
    check("stage24_1_result_pass", s24_1.get("result") == "pass", f"result={s24_1.get('result')}")
    check("stage24_1_inputs_ready", s24_1.get("all_trace_inputs_ready_for_stage24_2") is True, f"ready={s24_1.get('all_trace_inputs_ready_for_stage24_2')}")

    check("stage23_4_summary_exists", s23_4_path.is_file() and s23_4_path.stat().st_size > 0, str(s23_4_path.relative_to(root)))
    check("stage23_4_result_pass", s23_4.get("result") == "pass", f"result={s23_4.get('result')}")
    check(
        "stage23_4_root_cause_expected",
        s23_4.get("overall_root_cause") == "C_summary_metrics_insensitive_to_short_horizon_trace_change",
        f"overall_root_cause={s23_4.get('overall_root_cause')}",
    )

    check("trace_plan_exists", trace_plan_path.is_file() and trace_plan_path.stat().st_size > 0, str(trace_plan_path.relative_to(root)))
    check("stage23_diag_exists", stage23_diag_path.is_file() and stage23_diag_path.stat().st_size > 0, str(stage23_diag_path.relative_to(root)))

    trace_plan = read_rows(trace_plan_path)
    diag_rows = read_rows(stage23_diag_path)
    diag_by_case = {r.get("trace_case_id", ""): r for r in diag_rows}

    check("trace_plan_count_7", len(trace_plan) == 7, f"count={len(trace_plan)}")
    check("stage23_diag_count_7", len(diag_rows) == 7, f"count={len(diag_rows)}")

    trace_by_case: dict[str, list[dict[str, str]]] = {}
    for case in trace_plan:
        case_id = case["case_id"]
        trace_path = root / case["trace_csv"]
        rows = read_rows(trace_path)
        trace_by_case[case_id] = rows
        check(f"{case_id}_trace_exists", trace_path.is_file() and trace_path.stat().st_size > 0, str(trace_path.relative_to(root)))
        check(f"{case_id}_trace_rows_at_least_15", len(rows) >= 15, f"rows={len(rows)}")
        check(f"{case_id}_after_step_count_at_least_12", len(after_step_rows(rows)) >= 12, f"after_step_count={len(after_step_rows(rows))}")

    nominal_rows = trace_by_case.get("nominal_0p010", [])
    nominal_steps = rows_by_step(nominal_rows)

    check("nominal_trace_available", len(nominal_rows) >= 15, "nominal_0p010")
    check("nominal_after_step_count_at_least_12", len(nominal_steps) >= 12, f"count={len(nominal_steps)}")

    per_case_rows: list[dict[str, str]] = []

    for case in trace_plan:
        case_id = case["case_id"]
        perturbation_type = case["perturbation_type"]
        axis = case["axis"]
        qpos_axis = case["qpos_axis"]
        rows = trace_by_case.get(case_id, [])
        case_steps = rows_by_step(rows)

        nominal_for_compare = nominal_rows if case_id != "nominal_0p010" else rows
        nominal_compare_steps = rows_by_step(nominal_for_compare)

        diag = diag_by_case.get(case_id, {})

        before = phase_row(rows, "before_injection")
        after_injection = phase_row(rows, "after_injection")
        after_forward = phase_row(rows, "after_mj_forward")

        nominal_before = phase_row(nominal_for_compare, "before_injection")
        nominal_after_injection = phase_row(nominal_for_compare, "after_injection")
        nominal_after_forward = phase_row(nominal_for_compare, "after_mj_forward")

        pre_step_qvel_axis_diffs = [
            abs_diff(before, nominal_before, axis),
            abs_diff(after_injection, nominal_after_injection, axis),
            abs_diff(after_forward, nominal_after_forward, axis),
        ]
        pre_step_qpos_axis_diffs = [
            abs_diff(before, nominal_before, qpos_axis),
            abs_diff(after_injection, nominal_after_injection, qpos_axis),
            abs_diff(after_forward, nominal_after_forward, qpos_axis),
        ]

        qvel_diffs = []
        qpos_diffs = []
        base_vx_fd_diffs = []
        base_vy_fd_diffs = []
        combined_diffs = []

        common_steps = sorted(set(case_steps.keys()) & set(nominal_compare_steps.keys()))

        for step in common_steps:
            row = case_steps[step]
            ref = nominal_compare_steps[step]

            dqvel = abs_diff(row, ref, axis)
            dqpos = abs_diff(row, ref, qpos_axis)
            dbvx = abs_diff(row, ref, "base_vx_fd")
            dbvy = abs_diff(row, ref, "base_vy_fd")

            qvel_diffs.append(dqvel)
            qpos_diffs.append(dqpos)
            base_vx_fd_diffs.append(dbvx)
            base_vy_fd_diffs.append(dbvy)

            combined_diffs += [dqvel, dqpos, dbvx, dbvy]

        all_state_diffs = (
            pre_step_qvel_axis_diffs
            + pre_step_qpos_axis_diffs
            + qvel_diffs
            + qpos_diffs
            + base_vx_fd_diffs
            + base_vy_fd_diffs
        )

        post_step_state_diffs = qvel_diffs + qpos_diffs + base_vx_fd_diffs + base_vy_fd_diffs

        pre_step_trace_separation_detected = max_or_zero(pre_step_qvel_axis_diffs + pre_step_qpos_axis_diffs) > TOL
        post_step_trace_separation_detected = max_or_zero(post_step_state_diffs) > TOL
        early_window_trace_separation_detected = max_or_zero(all_state_diffs) > TOL

        row = {
            "case_id": case_id,
            "perturbation_id": case["perturbation_id"],
            "perturbation_type": perturbation_type,
            "axis": axis,
            "qpos_axis": qpos_axis,
            "nominal_ref": case["nominal_ref"],

            "injection_written": diag.get("injection_written", ""),
            "after_forward_preserved": diag.get("after_forward_preserved", ""),
            "written_delta": diag.get("written_delta", ""),
            "after_forward_delta": diag.get("after_forward_delta", ""),
            "first_step_qvel_delta": diag.get("first_step_qvel_delta", ""),
            "qpos_delta_first_step": diag.get("qpos_delta_first_step", ""),
            "first_step_base_vx_fd": diag.get("first_step_base_vx_fd", ""),
            "first_step_base_vy_fd": diag.get("first_step_base_vy_fd", ""),

            "aligned_after_step_count": str(len(common_steps)),

            "max_abs_pre_step_qvel_axis_diff_vs_nominal": f"{max_or_zero(pre_step_qvel_axis_diffs):.12f}",
            "mean_abs_pre_step_qvel_axis_diff_vs_nominal": f"{mean_or_zero(pre_step_qvel_axis_diffs):.12f}",
            "max_abs_pre_step_qpos_axis_diff_vs_nominal": f"{max_or_zero(pre_step_qpos_axis_diffs):.12f}",
            "mean_abs_pre_step_qpos_axis_diff_vs_nominal": f"{mean_or_zero(pre_step_qpos_axis_diffs):.12f}",

            "max_abs_qvel_axis_diff_vs_nominal": f"{max_or_zero(qvel_diffs):.12f}",
            "mean_abs_qvel_axis_diff_vs_nominal": f"{mean_or_zero(qvel_diffs):.12f}",
            "max_abs_qpos_axis_diff_vs_nominal": f"{max_or_zero(qpos_diffs):.12f}",
            "mean_abs_qpos_axis_diff_vs_nominal": f"{mean_or_zero(qpos_diffs):.12f}",
            "max_abs_base_vx_fd_diff_vs_nominal": f"{max_or_zero(base_vx_fd_diffs):.12f}",
            "mean_abs_base_vx_fd_diff_vs_nominal": f"{mean_or_zero(base_vx_fd_diffs):.12f}",
            "max_abs_base_vy_fd_diff_vs_nominal": f"{max_or_zero(base_vy_fd_diffs):.12f}",
            "mean_abs_base_vy_fd_diff_vs_nominal": f"{mean_or_zero(base_vy_fd_diffs):.12f}",

            "post_step_max_abs_state_delta": f"{max_or_zero(post_step_state_diffs):.12f}",
            "post_step_mean_abs_state_delta": f"{mean_or_zero(post_step_state_diffs):.12f}",
            "early_window_max_abs_state_delta": f"{max_or_zero(all_state_diffs):.12f}",
            "early_window_mean_abs_state_delta": f"{mean_or_zero(all_state_diffs):.12f}",

            "pre_step_trace_separation_detected": str(pre_step_trace_separation_detected),
            "post_step_trace_separation_detected": str(post_step_trace_separation_detected),
            "early_window_trace_separation_detected": str(early_window_trace_separation_detected),

            "trace_csv": case["trace_csv"],
        }
        per_case_rows.append(row)

    non_nominal_rows = [r for r in per_case_rows if r["perturbation_type"] != "none"]

    any_pre_step_detected = any(bval(r["pre_step_trace_separation_detected"]) for r in non_nominal_rows)
    any_post_step_detected = any(bval(r["post_step_trace_separation_detected"]) for r in non_nominal_rows)
    any_early_window_detected = any(bval(r["early_window_trace_separation_detected"]) for r in non_nominal_rows)

    all_pre_step_detected = all(bval(r["pre_step_trace_separation_detected"]) for r in non_nominal_rows) if non_nominal_rows else False
    all_early_window_detected = all(bval(r["early_window_trace_separation_detected"]) for r in non_nominal_rows) if non_nominal_rows else False

    max_early_window_delta = max_or_zero([float(r["early_window_max_abs_state_delta"]) for r in non_nominal_rows])
    mean_early_window_delta = mean_or_zero([float(r["early_window_mean_abs_state_delta"]) for r in non_nominal_rows])

    aggregate_rows = [
        {
            "metric": "non_nominal_case_count",
            "value": str(len(non_nominal_rows)),
            "interpretation": "number of perturbation cases compared with nominal",
        },
        {
            "metric": "any_pre_step_trace_separation_detected",
            "value": str(any_pre_step_detected),
            "interpretation": "whether any perturbation is visible before/at mj_forward trace",
        },
        {
            "metric": "all_pre_step_trace_separation_detected",
            "value": str(all_pre_step_detected),
            "interpretation": "whether all non-nominal perturbations are visible before/at mj_forward trace",
        },
        {
            "metric": "any_post_step_trace_separation_detected",
            "value": str(any_post_step_detected),
            "interpretation": "whether any perturbation remains separated from nominal during after_mj_step rows",
        },
        {
            "metric": "any_early_window_trace_separation_detected",
            "value": str(any_early_window_detected),
            "interpretation": "whether short-horizon metric set can detect perturbation effect",
        },
        {
            "metric": "all_early_window_trace_separation_detected",
            "value": str(all_early_window_detected),
            "interpretation": "whether all perturbation cases are detected by short-horizon metric set",
        },
        {
            "metric": "max_early_window_max_abs_state_delta",
            "value": f"{max_early_window_delta:.12f}",
            "interpretation": "largest detected short-horizon state separation",
        },
        {
            "metric": "mean_early_window_mean_abs_state_delta",
            "value": f"{mean_early_window_delta:.12f}",
            "interpretation": "average detected short-horizon state separation",
        },
    ]

    check("per_case_metric_rows_generated", len(per_case_rows) == 7, f"rows={len(per_case_rows)}")
    check("non_nominal_metric_rows_6", len(non_nominal_rows) == 6, f"rows={len(non_nominal_rows)}")
    check("aggregate_rows_generated", len(aggregate_rows) >= 6, f"rows={len(aggregate_rows)}")
    check("metric_has_early_window_detection_flag", all("early_window_trace_separation_detected" in r for r in per_case_rows), "flag present")
    check("metric_has_post_step_detection_flag", all("post_step_trace_separation_detected" in r for r in per_case_rows), "flag present")
    check("metric_has_pre_step_detection_flag", all("pre_step_trace_separation_detected" in r for r in per_case_rows), "flag present")
    check("short_horizon_detection_recorded", isinstance(any_early_window_detected, bool), str(any_early_window_detected))

    # Stage 24.2 is a computation stage. Detection may be true or false; either result is valid.
    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    per_case_fields = list(per_case_rows[0].keys()) if per_case_rows else ["case_id"]
    write_csv(per_case_csv, per_case_rows, per_case_fields)
    write_csv(aggregate_csv, aggregate_rows, ["metric", "value", "interpretation"])
    write_csv(validation_csv, checks, ["check", "status", "detail"])

    display_cols = [
        "case_id",
        "axis",
        "written_delta",
        "after_forward_delta",
        "max_abs_pre_step_qvel_axis_diff_vs_nominal",
        "max_abs_qvel_axis_diff_vs_nominal",
        "max_abs_qpos_axis_diff_vs_nominal",
        "post_step_max_abs_state_delta",
        "early_window_max_abs_state_delta",
        "pre_step_trace_separation_detected",
        "post_step_trace_separation_detected",
        "early_window_trace_separation_detected",
    ]
    metrics_table_md = markdown_table(per_case_rows, display_cols)
    aggregate_table_md = markdown_table(aggregate_rows, ["metric", "value", "interpretation"])

    metrics_md.write_text(
        "# Stage 24.2 short-horizon perturbation-sensitive metrics\n\n"
        "## Per-case metrics\n\n"
        + metrics_table_md
        + "\n\n## Aggregate metrics\n\n"
        + aggregate_table_md
        + "\n",
        encoding="utf-8",
    )

    summary = {
        "stage": "24.2",
        "name": "compute short-horizon perturbation-sensitive metrics",
        "result": result,
        "failure_count": failure_count,
        "case_count": len(per_case_rows),
        "non_nominal_case_count": len(non_nominal_rows),
        "any_pre_step_trace_separation_detected": any_pre_step_detected,
        "all_pre_step_trace_separation_detected": all_pre_step_detected,
        "any_post_step_trace_separation_detected": any_post_step_detected,
        "any_early_window_trace_separation_detected": any_early_window_detected,
        "all_early_window_trace_separation_detected": all_early_window_detected,
        "max_early_window_max_abs_state_delta": max_early_window_delta,
        "mean_early_window_mean_abs_state_delta": mean_early_window_delta,
        "stage23_root_cause": s23_4.get("overall_root_cause"),
        "per_case_metrics": per_case_rows,
        "aggregate_metrics": aggregate_rows,
        "generated_files": [
            str(per_case_csv.relative_to(root)),
            str(aggregate_csv.relative_to(root)),
            str(validation_csv.relative_to(root)),
            str(metrics_md.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(doc.relative_to(root)),
        ],
        "claim_boundary": [
            "metric computation only",
            "no new rollout generated",
            "does not upgrade scale=0.010 to observable-perturbation-tested recommended candidate scale",
            "no observable perturbation robustness claim",
            "no full MPC-WBC velocity controller claim",
            "no real robot torque execution claim",
            "no hardware torque enablement claim",
            "no terrain or external-force robustness claim",
        ],
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    doc.write_text(f"""# Stage 24.2：short-horizon perturbation-sensitive metrics

## 1. 目标

Stage 24.2 基于 Stage 23.2 的 qvel injection trace 数据，计算短时扰动敏感指标。

本阶段不新增 rollout，不新增控制器，只计算 metrics。

## 2. 结果

Stage 24.2 result: {result}

Failure count: {failure_count}

Case count: {len(per_case_rows)}

Non-nominal case count: {len(non_nominal_rows)}

any_pre_step_trace_separation_detected: {any_pre_step_detected}

all_pre_step_trace_separation_detected: {all_pre_step_detected}

any_post_step_trace_separation_detected: {any_post_step_detected}

any_early_window_trace_separation_detected: {any_early_window_detected}

all_early_window_trace_separation_detected: {all_early_window_detected}

max_early_window_max_abs_state_delta: {max_early_window_delta:.12f}

mean_early_window_mean_abs_state_delta: {mean_early_window_delta:.12f}

## 3. Stage 23 根因背景

    overall_root_cause={s23_4.get("overall_root_cause")}
    root_cause_confidence={s23_4.get("root_cause_confidence")}

Stage 23 已确认 qvel 扰动写入、mj_forward 后保持，并在短时 trace 中产生状态差异。Stage 24.2 的作用是把这种短时差异量化为 metrics。

## 4. Per-case metrics

{metrics_table_md}

## 5. Aggregate metrics

{aggregate_table_md}

## 6. 当前支持的表述

Stage 24.2 支持：

    基于 Stage 23 trace 数据，已计算短时 perturbation-sensitive metrics。
    这些 metrics 可用于分析 Stage 22 长期 summary 指标为什么没有捕捉短时 qvel 初始扰动。

## 7. 当前不支持的表述

Stage 24.2 不支持：

  * 不支持 scale=0.010 已通过 observable perturbation robustness 验证；
  * 不支持 scale=0.010 升级为 observable-perturbation-tested recommended candidate scale；
  * 不支持完整 MPC-WBC 速度控制器已经完成；
  * 不支持 scale=0.010 可以直接用于真实机器人；
  * 不支持真实机器人 torque 执行或硬件 torque enablement 已完成；
  * 不支持复杂地形或外力冲击鲁棒性已完成。
""", encoding="utf-8")

    print(f"stage24_2_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"any_pre_step_trace_separation_detected: {any_pre_step_detected}")
    print(f"all_pre_step_trace_separation_detected: {all_pre_step_detected}")
    print(f"any_post_step_trace_separation_detected: {any_post_step_detected}")
    print(f"any_early_window_trace_separation_detected: {any_early_window_detected}")
    print(f"all_early_window_trace_separation_detected: {all_early_window_detected}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"per_case_csv: {per_case_csv.relative_to(root)}")
    print(f"aggregate_csv: {aggregate_csv.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
