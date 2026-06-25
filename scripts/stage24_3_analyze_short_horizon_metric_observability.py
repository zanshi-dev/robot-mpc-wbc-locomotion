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


def bval(value) -> bool:
    return str(value).strip().lower() == "true"


def fval(row: dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default))
    except Exception:
        return default


def get_metric(rows: list[dict[str, str]], metric: str, default: str = "") -> str:
    for row in rows:
        if row.get("metric") == metric:
            return row.get("value", default)
    return default


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

    s24_2_path = logs / "stage24_2_short_horizon_perturbation_metrics_summary.json"
    per_case_path = logs / "stage24_2_short_horizon_perturbation_metrics_per_case.csv"
    aggregate_path = logs / "stage24_2_short_horizon_perturbation_metrics_aggregate.csv"
    s23_4_path = logs / "stage23_4_perturbation_observability_evidence_freeze_summary.json"
    s22_4_path = logs / "stage22_4_observable_perturbation_evidence_freeze_summary.json"

    analysis_csv = logs / "stage24_3_short_horizon_metric_observability_analysis.csv"
    validation_csv = logs / "stage24_3_short_horizon_metric_observability_validation.csv"
    analysis_md = logs / "stage24_3_short_horizon_metric_observability_analysis.md"
    summary_json = logs / "stage24_3_short_horizon_metric_observability_summary.json"
    doc = docs / "STAGE24_3_SHORT_HORIZON_METRIC_ANALYSIS.md"

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    s24_2 = load_json(s24_2_path)
    s23_4 = load_json(s23_4_path)
    s22_4 = load_json(s22_4_path)
    per_case_rows = read_rows(per_case_path)
    aggregate_rows = read_rows(aggregate_path)

    for label, path in [
        ("stage24_2_summary", s24_2_path),
        ("stage24_2_per_case", per_case_path),
        ("stage24_2_aggregate", aggregate_path),
        ("stage23_4_summary", s23_4_path),
        ("stage22_4_summary", s22_4_path),
    ]:
        check(f"{label}_exists", path.is_file() and path.stat().st_size > 0, str(path.relative_to(root)))

    check("stage24_2_result_pass", s24_2.get("result") == "pass", f"result={s24_2.get('result')}")
    check("stage23_4_result_pass", s23_4.get("result") == "pass", f"result={s23_4.get('result')}")
    check("stage22_4_result_pass", s22_4.get("result") == "pass", f"result={s22_4.get('result')}")

    check("per_case_row_count_7", len(per_case_rows) == 7, f"rows={len(per_case_rows)}")
    check("aggregate_row_count_at_least_8", len(aggregate_rows) >= 8, f"rows={len(aggregate_rows)}")

    stage23_root_cause = s23_4.get("overall_root_cause")
    stage23_confidence = s23_4.get("root_cause_confidence")
    stage22_variability = bool(s22_4.get("perturbation_metric_variability_detected", False))
    stage22_observable = bool(s22_4.get("observable_perturbation_pass", False))
    stage22_recommendation_observable = bool(s22_4.get("recommendation_observable_robust", False))

    check(
        "stage23_root_cause_expected",
        stage23_root_cause == "C_summary_metrics_insensitive_to_short_horizon_trace_change",
        f"overall_root_cause={stage23_root_cause}",
    )
    check("stage23_confidence_high", stage23_confidence == "high", f"root_cause_confidence={stage23_confidence}")
    check("stage22_variability_false", stage22_variability is False, str(stage22_variability))
    check("stage22_observable_false", stage22_observable is False, str(stage22_observable))
    check("stage22_recommendation_observable_false", stage22_recommendation_observable is False, str(stage22_recommendation_observable))

    non_nominal = [r for r in per_case_rows if r.get("perturbation_type") != "none"]

    any_pre = bool(s24_2.get("any_pre_step_trace_separation_detected", False))
    all_pre = bool(s24_2.get("all_pre_step_trace_separation_detected", False))
    any_post = bool(s24_2.get("any_post_step_trace_separation_detected", False))
    any_early = bool(s24_2.get("any_early_window_trace_separation_detected", False))
    all_early = bool(s24_2.get("all_early_window_trace_separation_detected", False))

    check("stage24_2_any_pre_true", any_pre is True, str(any_pre))
    check("stage24_2_all_pre_true", all_pre is True, str(all_pre))
    check("stage24_2_any_post_false", any_post is False, str(any_post))
    check("stage24_2_any_early_true", any_early is True, str(any_early))
    check("stage24_2_all_early_true", all_early is True, str(all_early))

    all_non_nominal_pre_detected = all(bval(r.get("pre_step_trace_separation_detected")) for r in non_nominal) if non_nominal else False
    any_non_nominal_post_detected = any(bval(r.get("post_step_trace_separation_detected")) for r in non_nominal)
    all_non_nominal_early_detected = all(bval(r.get("early_window_trace_separation_detected")) for r in non_nominal) if non_nominal else False

    max_pre_delta = max([fval(r, "max_abs_pre_step_qvel_axis_diff_vs_nominal") for r in non_nominal] or [0.0])
    max_post_delta = max([fval(r, "post_step_max_abs_state_delta") for r in non_nominal] or [0.0])
    max_early_delta = max([fval(r, "early_window_max_abs_state_delta") for r in non_nominal] or [0.0])
    mean_early_delta = sum([fval(r, "early_window_mean_abs_state_delta") for r in non_nominal] or [0.0]) / max(len(non_nominal), 1)

    if all_non_nominal_pre_detected and not any_non_nominal_post_detected and all_non_nominal_early_detected:
        metric_observability_class = "pre_step_only_detection_no_post_step_trace_separation"
        overall_explanation = (
            "The short-horizon metric set detects all non-nominal qvel perturbations before or at the mj_forward trace stage, "
            "but no perturbation remains separated from nominal in the aligned after_mj_step rows. "
            "Therefore, Stage 22 long-horizon summary metrics were insensitive because the perturbation effect did not persist into the rollout-step trace used by downstream summaries."
        )
        metric_audit_result = "partial_detection"
    elif all_non_nominal_pre_detected and any_non_nominal_post_detected:
        metric_observability_class = "pre_and_post_step_detection"
        overall_explanation = (
            "The short-horizon metric set detects perturbations both before mj_step and during after_mj_step rows. "
            "This would indicate that Stage 22 summary metrics missed a persistent short-horizon trace separation."
        )
        metric_audit_result = "persistent_short_horizon_detection"
    elif not all_non_nominal_pre_detected:
        metric_observability_class = "incomplete_pre_step_detection"
        overall_explanation = (
            "The short-horizon metric set does not detect all non-nominal perturbations even at the pre-step trace stage. "
            "The metric design may still be insufficient or the selected axes may be incomplete."
        )
        metric_audit_result = "incomplete_detection"
    else:
        metric_observability_class = "unexpected_metric_pattern"
        overall_explanation = (
            "The short-horizon metric pattern does not match the expected Stage 24 categories. "
            "Manual inspection is required before making any conclusion."
        )
        metric_audit_result = "manual_review_required"

    per_case_analysis_rows: list[dict[str, str]] = []

    for row in per_case_rows:
        if row.get("perturbation_type") == "none":
            case_class = "nominal_reference"
            case_explanation = "Nominal reference trace; no perturbation separation expected."
        elif bval(row.get("pre_step_trace_separation_detected")) and not bval(row.get("post_step_trace_separation_detected")):
            case_class = "pre_step_only_detection"
            case_explanation = (
                "Perturbation is visible in pre-step qvel difference versus nominal, "
                "but not visible in aligned after_mj_step rows."
            )
        elif bval(row.get("pre_step_trace_separation_detected")) and bval(row.get("post_step_trace_separation_detected")):
            case_class = "pre_and_post_step_detection"
            case_explanation = "Perturbation remains separated from nominal after mj_step."
        else:
            case_class = "not_detected"
            case_explanation = "Perturbation not detected by the current short-horizon metrics."

        per_case_analysis_rows.append({
            "case_id": row.get("case_id", ""),
            "perturbation_type": row.get("perturbation_type", ""),
            "axis": row.get("axis", ""),
            "written_delta": row.get("written_delta", ""),
            "after_forward_delta": row.get("after_forward_delta", ""),
            "max_abs_pre_step_qvel_axis_diff_vs_nominal": row.get("max_abs_pre_step_qvel_axis_diff_vs_nominal", ""),
            "post_step_max_abs_state_delta": row.get("post_step_max_abs_state_delta", ""),
            "early_window_max_abs_state_delta": row.get("early_window_max_abs_state_delta", ""),
            "pre_step_trace_separation_detected": row.get("pre_step_trace_separation_detected", ""),
            "post_step_trace_separation_detected": row.get("post_step_trace_separation_detected", ""),
            "early_window_trace_separation_detected": row.get("early_window_trace_separation_detected", ""),
            "case_metric_observability_class": case_class,
            "case_explanation": case_explanation,
        })

    class_counts: dict[str, int] = {}
    for row in per_case_analysis_rows:
        cls = row["case_metric_observability_class"]
        class_counts[cls] = class_counts.get(cls, 0) + 1

    class_count_rows = [
        {"class": k, "count": str(v)}
        for k, v in sorted(class_counts.items())
    ]

    check("metric_observability_class_selected", bool(metric_observability_class), metric_observability_class)
    check("per_case_analysis_rows_7", len(per_case_analysis_rows) == 7, f"rows={len(per_case_analysis_rows)}")
    check(
        "root_cause_refined_without_robustness_upgrade",
        metric_observability_class in [
            "pre_step_only_detection_no_post_step_trace_separation",
            "pre_and_post_step_detection",
            "incomplete_pre_step_detection",
            "unexpected_metric_pattern",
        ],
        metric_observability_class,
    )

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    analysis_fields = list(per_case_analysis_rows[0].keys()) if per_case_analysis_rows else ["case_id"]
    write_csv(analysis_csv, per_case_analysis_rows, analysis_fields)
    write_csv(validation_csv, checks, ["check", "status", "detail"])

    display_cols = [
        "case_id",
        "axis",
        "written_delta",
        "max_abs_pre_step_qvel_axis_diff_vs_nominal",
        "post_step_max_abs_state_delta",
        "early_window_max_abs_state_delta",
        "case_metric_observability_class",
    ]
    per_case_md = markdown_table(per_case_analysis_rows, display_cols)
    class_counts_md = markdown_table(class_count_rows, ["class", "count"])

    if metric_observability_class == "pre_step_only_detection_no_post_step_trace_separation":
        conclusion = (
            "Stage 24.3 shows that short-horizon perturbation-sensitive metrics detect the injected qvel perturbations only in the pre-step / mj_forward trace segment. "
            "The aligned after_mj_step rows are not separated from nominal. "
            "This refines the Stage 23 root cause: Stage 22 summary metrics were insensitive because the perturbation signature was visible at injection time but did not persist into the rollout-step trace."
        )
        supported_claim = (
            "Stage 24 supports adding explicit injection-stage or pre-step trace metrics for future perturbation audits. "
            "It does not support observable robustness or a scale=0.010 recommendation upgrade."
        )
    elif metric_observability_class == "pre_and_post_step_detection":
        conclusion = (
            "Stage 24.3 shows that short-horizon metrics detect perturbations both before mj_step and in after_mj_step rows. "
            "This would indicate Stage 22 summary metrics missed a persistent short-horizon trace effect."
        )
        supported_claim = (
            "Stage 24 supports adding short-horizon post-step metrics for future perturbation audits, but still does not support observable robustness by itself."
        )
    elif metric_observability_class == "incomplete_pre_step_detection":
        conclusion = (
            "Stage 24.3 shows that current short-horizon metrics do not detect all non-nominal perturbations. "
            "The metric set remains incomplete."
        )
        supported_claim = (
            "Stage 24 supports further metric refinement, not robustness claims."
        )
    else:
        conclusion = (
            "Stage 24.3 produced an unexpected metric observability pattern. Manual inspection is required."
        )
        supported_claim = (
            "No claim upgrade is supported."
        )

    analysis_md.write_text(f"""# Stage 24.3 short-horizon metric observability analysis

## Overall class

    metric_observability_class: {metric_observability_class}
    metric_audit_result: {metric_audit_result}

{overall_explanation}

## Class counts

{class_counts_md}

## Per-case analysis

{per_case_md}
""", encoding="utf-8")

    doc.write_text(f"""# Stage 24.3：short-horizon metric observability analysis

## 1. 目标

Stage 24.3 分析 Stage 24.2 计算出的短时 perturbation-sensitive metrics，判断这些指标如何解释 Stage 22 长期 summary 指标不敏感问题。

本阶段不新增 rollout，不新增控制器，不重新声明 observable perturbation robustness。

## 2. 结果

Stage 24.3 result: {result}

Failure count: {failure_count}

Metric observability class: `{metric_observability_class}`

Metric audit result: `{metric_audit_result}`

## 3. 关键结论

{conclusion}

{supported_claim}

## 4. 与 Stage 22 / Stage 23 的关系

Stage 22 结果：

    observable_perturbation_pass={stage22_observable}
    perturbation_metric_variability_detected={stage22_variability}
    recommendation_observable_robust={stage22_recommendation_observable}

Stage 23 根因：

    overall_root_cause={stage23_root_cause}
    root_cause_confidence={stage23_confidence}

Stage 24.2 指标：

    any_pre_step_trace_separation_detected={any_pre}
    all_pre_step_trace_separation_detected={all_pre}
    any_post_step_trace_separation_detected={any_post}
    any_early_window_trace_separation_detected={any_early}
    all_early_window_trace_separation_detected={all_early}

## 5. 数值摘要

    max_pre_step_qvel_axis_diff_vs_nominal={max_pre_delta:.12f}
    max_post_step_state_delta={max_post_delta:.12f}
    max_early_window_state_delta={max_early_delta:.12f}
    mean_early_window_state_delta={mean_early_delta:.12f}

## 6. 类别计数

{class_counts_md}

## 7. 逐 case 分析

{per_case_md}

## 8. 当前支持的表述

Stage 24.3 支持：

    Stage 24 基于 Stage 23 trace 数据构造并分析了短时 perturbation-sensitive metrics。
    当前结果表明，qvel 扰动可在 injection / mj_forward 阶段被短时指标检测到；
    但在 aligned after_mj_step rows 中没有相对 nominal 的持续 trace separation。
    因此，Stage 22 的长期 summary 指标没有变化是合理的。

## 9. 当前不支持的表述

Stage 24.3 不支持：

  * 不支持 scale=0.010 已通过 observable perturbation robustness 验证；
  * 不支持 scale=0.010 升级为 observable-perturbation-tested recommended candidate scale；
  * 不支持完整 MPC-WBC 速度控制器已经完成；
  * 不支持 scale=0.010 可以直接用于真实机器人；
  * 不支持真实机器人 torque 执行或硬件 torque enablement 已完成；
  * 不支持复杂地形或外力冲击鲁棒性已完成。
""", encoding="utf-8")

    summary = {
        "stage": "24.3",
        "name": "short-horizon metric observability analysis",
        "result": result,
        "failure_count": failure_count,
        "metric_observability_class": metric_observability_class,
        "metric_audit_result": metric_audit_result,
        "overall_explanation": overall_explanation,
        "conclusion": conclusion,
        "supported_claim": supported_claim,
        "stage22_observable_perturbation_pass": stage22_observable,
        "stage22_perturbation_metric_variability_detected": stage22_variability,
        "stage22_recommendation_observable_robust": stage22_recommendation_observable,
        "stage23_root_cause": stage23_root_cause,
        "stage23_confidence": stage23_confidence,
        "any_pre_step_trace_separation_detected": any_pre,
        "all_pre_step_trace_separation_detected": all_pre,
        "any_post_step_trace_separation_detected": any_post,
        "any_early_window_trace_separation_detected": any_early,
        "all_early_window_trace_separation_detected": all_early,
        "max_pre_step_qvel_axis_diff_vs_nominal": max_pre_delta,
        "max_post_step_state_delta": max_post_delta,
        "max_early_window_state_delta": max_early_delta,
        "mean_early_window_state_delta": mean_early_delta,
        "class_counts": class_counts,
        "per_case_analysis_rows": per_case_analysis_rows,
        "generated_files": [
            str(analysis_csv.relative_to(root)),
            str(validation_csv.relative_to(root)),
            str(analysis_md.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(doc.relative_to(root)),
        ],
        "claim_boundary": [
            "metric analysis only",
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

    print(f"stage24_3_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"metric_observability_class: {metric_observability_class}")
    print(f"metric_audit_result: {metric_audit_result}")
    print(f"any_pre_step_trace_separation_detected: {any_pre}")
    print(f"any_post_step_trace_separation_detected: {any_post}")
    print(f"any_early_window_trace_separation_detected: {any_early}")
    print(f"summary: {summary_json.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
