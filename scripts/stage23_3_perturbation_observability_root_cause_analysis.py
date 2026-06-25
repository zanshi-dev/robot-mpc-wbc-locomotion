#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


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


def bval(value) -> bool:
    return str(value).strip().lower() == "true"


def fval(row: dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default))
    except Exception:
        return default


def markdown_table(rows: list[dict[str, str]], cols: list[str]) -> str:
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(c, "")) for c in cols) + " |")
    return "\n".join(lines)


def classify_case(row: dict[str, str], stage22_variability_detected: bool) -> tuple[str, str]:
    if row.get("perturbation_type") == "none":
        return (
            "nominal_reference",
            "nominal case has no nonzero perturbation and is used as a reference trace.",
        )

    injection_written = bval(row.get("injection_written"))
    after_forward_preserved = bval(row.get("after_forward_preserved"))
    first_step_state_changed = bval(row.get("first_step_state_changed"))

    if not injection_written:
        return (
            "A_injection_not_written",
            "qvel perturbation was not actually written to the selected qvel axis.",
        )

    if not after_forward_preserved:
        return (
            "B_mj_forward_did_not_preserve_injected_qvel",
            "qvel perturbation was written but was not preserved after mujoco.mj_forward.",
        )

    if not first_step_state_changed:
        return (
            "B2_no_short_horizon_state_change",
            "qvel perturbation was written and preserved, but first-step qvel/qpos trace did not change on the selected axis.",
        )

    if not stage22_variability_detected:
        return (
            "C_summary_metrics_insensitive_to_short_horizon_trace_change",
            "qvel perturbation was written, preserved, and affected short-horizon trace, but Stage 22 summary metrics remained unchanged.",
        )

    return (
        "D_observable_metric_variability_detected",
        "qvel perturbation affected trace and Stage 22 summary metrics showed variability.",
    )


def main() -> int:
    root = repo_root()
    logs = root / "results" / "logs_sample"
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    s22_3_path = logs / "stage22_3_observable_robustness_summary.json"
    s22_4_path = logs / "stage22_4_observable_perturbation_evidence_freeze_summary.json"
    s23_2_path = logs / "stage23_2_qvel_injection_trace_summary.json"
    diag_path = logs / "stage23_2_qvel_injection_trace_diagnostic_table.csv"

    per_case_csv = logs / "stage23_3_perturbation_observability_root_cause_per_case.csv"
    validation_csv = logs / "stage23_3_perturbation_observability_root_cause_validation.csv"
    analysis_md = logs / "stage23_3_perturbation_observability_root_cause_analysis.md"
    summary_json = logs / "stage23_3_perturbation_observability_root_cause_summary.json"
    doc = docs / "STAGE23_3_PERTURBATION_OBSERVABILITY_ROOT_CAUSE_ANALYSIS.md"

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    for label, path in [
        ("stage22_3_summary", s22_3_path),
        ("stage22_4_summary", s22_4_path),
        ("stage23_2_summary", s23_2_path),
        ("stage23_2_diagnostic_table", diag_path),
    ]:
        check(f"{label}_exists", path.is_file() and path.stat().st_size > 0, str(path.relative_to(root)))

    s22_3 = load_json(s22_3_path)
    s22_4 = load_json(s22_4_path)
    s23_2 = load_json(s23_2_path)
    diag_rows = read_rows(diag_path)

    check("stage22_3_result_pass", s22_3.get("result") == "pass", f"result={s22_3.get('result')}")
    check("stage22_4_result_pass", s22_4.get("result") == "pass", f"result={s22_4.get('result')}")
    check("stage23_2_result_pass", s23_2.get("result") == "pass", f"result={s23_2.get('result')}")
    check("diagnostic_row_count_7", len(diag_rows) == 7, f"rows={len(diag_rows)}")

    stage22_variability_detected = bool(s22_4.get("perturbation_metric_variability_detected", False))
    stage22_observable_pass = bool(s22_4.get("observable_perturbation_pass", False))
    stage22_recommendation_observable_robust = bool(s22_4.get("recommendation_observable_robust", False))
    stage22_recommendation_relation_stable = bool(s22_4.get("recommendation_relation_stable", False))

    all_nonzero_written = bool(s23_2.get("all_nonzero_perturbations_written", False))
    all_after_forward_preserved = bool(s23_2.get("all_after_forward_preserved", False))
    any_first_step_state_changed = bool(s23_2.get("any_first_step_state_changed", False))

    check("stage22_variability_false_recorded", stage22_variability_detected is False, str(stage22_variability_detected))
    check("stage22_observable_pass_false_recorded", stage22_observable_pass is False, str(stage22_observable_pass))
    check("stage22_recommendation_observable_false_recorded", stage22_recommendation_observable_robust is False, str(stage22_recommendation_observable_robust))
    check("stage22_recommendation_relation_stable_true_recorded", stage22_recommendation_relation_stable is True, str(stage22_recommendation_relation_stable))

    per_case_rows: list[dict[str, str]] = []
    classification_counts: dict[str, int] = {}

    for row in diag_rows:
        root_cause_class, explanation = classify_case(row, stage22_variability_detected)
        classification_counts[root_cause_class] = classification_counts.get(root_cause_class, 0) + 1

        per_case_rows.append({
            "trace_case_id": row.get("trace_case_id", ""),
            "perturbation_id": row.get("perturbation_id", ""),
            "perturbation_type": row.get("perturbation_type", ""),
            "axis": row.get("axis", ""),
            "expected_delta": row.get("expected_delta", ""),
            "written_delta": row.get("written_delta", ""),
            "after_forward_delta": row.get("after_forward_delta", ""),
            "first_step_qvel_delta": row.get("first_step_qvel_delta", ""),
            "qpos_delta_first_step": row.get("qpos_delta_first_step", ""),
            "first_step_base_vx_fd": row.get("first_step_base_vx_fd", ""),
            "first_step_base_vy_fd": row.get("first_step_base_vy_fd", ""),
            "injection_written": row.get("injection_written", ""),
            "after_forward_preserved": row.get("after_forward_preserved", ""),
            "first_step_state_changed": row.get("first_step_state_changed", ""),
            "root_cause_class": root_cause_class,
            "root_cause_explanation": explanation,
            "trace_csv": row.get("trace_csv", ""),
        })

    non_nominal_classes = [
        row["root_cause_class"]
        for row in per_case_rows
        if row["perturbation_type"] != "none"
    ]

    if not all_nonzero_written:
        overall_root_cause = "A_injection_not_written"
        overall_explanation = (
            "At least one nonzero qvel perturbation was not actually written to the selected MuJoCo qvel axis. "
            "Stage 22 summary invariance is therefore explained by ineffective perturbation injection."
        )
    elif not all_after_forward_preserved:
        overall_root_cause = "B_mj_forward_did_not_preserve_injected_qvel"
        overall_explanation = (
            "Nonzero qvel perturbations were written, but at least one was not preserved after mujoco.mj_forward. "
            "Stage 22 summary invariance is therefore explained by state synchronization or model update behavior."
        )
    elif not any_first_step_state_changed:
        overall_root_cause = "B2_no_short_horizon_state_change"
        overall_explanation = (
            "Nonzero qvel perturbations were written and preserved after mj_forward, but the first-step qvel/qpos trace did not change. "
            "The current runner is not sensitive to these qvel anchors over the recorded short horizon."
        )
    elif not stage22_variability_detected:
        overall_root_cause = "C_summary_metrics_insensitive_to_short_horizon_trace_change"
        overall_explanation = (
            "Nonzero qvel perturbations were written, preserved after mj_forward, and produced short-horizon state differences. "
            "However, Stage 22 summary metrics remained identical across perturbation cases. "
            "Thus the Stage 22 negative evidence is best explained by summary-metric insensitivity to short-horizon initial qvel changes."
        )
    else:
        overall_root_cause = "D_observable_metric_variability_detected"
        overall_explanation = (
            "Trace diagnostics and Stage 22 summary metrics both showed perturbation effects. "
            "This would support observable perturbation evidence, but it is not the recorded Stage 22 result."
        )

    root_cause_confidence = "high"
    if len(set(non_nominal_classes)) > 1:
        root_cause_confidence = "mixed"

    check("overall_root_cause_selected", bool(overall_root_cause), overall_root_cause)
    check("per_case_root_cause_rows_generated", len(per_case_rows) == 7, f"rows={len(per_case_rows)}")
    check("root_cause_explains_stage22_negative_evidence", overall_root_cause.startswith(("A_", "B_", "C_")), overall_root_cause)

    # This is an analysis stage: negative conclusions are valid and should not fail the script.
    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    per_case_fields = list(per_case_rows[0].keys()) if per_case_rows else ["trace_case_id"]
    write_csv(per_case_csv, per_case_rows, per_case_fields)
    write_csv(validation_csv, checks, ["check", "status", "detail"])

    md_cols = [
        "trace_case_id",
        "axis",
        "expected_delta",
        "written_delta",
        "after_forward_delta",
        "first_step_qvel_delta",
        "qpos_delta_first_step",
        "injection_written",
        "after_forward_preserved",
        "first_step_state_changed",
        "root_cause_class",
    ]

    per_case_md = markdown_table(per_case_rows, md_cols)

    count_rows = [
        {"root_cause_class": k, "count": str(v)}
        for k, v in sorted(classification_counts.items())
    ]
    count_md = markdown_table(count_rows, ["root_cause_class", "count"])

    if overall_root_cause == "C_summary_metrics_insensitive_to_short_horizon_trace_change":
        conclusion = (
            "Stage 23.3 root-cause analysis indicates that the Stage 22 qvel perturbations were injected and visible in short-horizon trace data, "
            "but the Stage 22 rollout summary metrics did not vary. The root cause is therefore summary-metric insensitivity to short-horizon initial qvel perturbations."
        )
        supported_claim = (
            "Stage 23 supports explaining Stage 22 negative evidence as a metric/observability limitation, not as a successful observable robustness validation."
        )
    elif overall_root_cause.startswith("A_"):
        conclusion = (
            "Stage 23.3 root-cause analysis indicates that Stage 22 qvel perturbations were not reliably written. "
            "The Stage 22 negative evidence is therefore explained by ineffective perturbation injection."
        )
        supported_claim = (
            "Stage 23 supports treating Stage 22 as an injection-attempt audit, not as an observable perturbation audit."
        )
    elif overall_root_cause.startswith("B_"):
        conclusion = (
            "Stage 23.3 root-cause analysis indicates that qvel perturbations were written but did not propagate reliably into the evaluated short-horizon state trace. "
            "The Stage 22 negative evidence is therefore explained by runner or simulation-state insensitivity before summary metrics are evaluated."
        )
        supported_claim = (
            "Stage 23 supports treating Stage 22 as a diagnostic negative result, not as an observable robustness validation."
        )
    else:
        conclusion = (
            "Stage 23.3 produced an unexpected classification. Review trace diagnostics before making any robustness claim."
        )
        supported_claim = (
            "No upgrade of the Stage 22 claim is supported without manual review."
        )

    analysis_text = f"""# Stage 23.3 perturbation observability root-cause analysis

## Overall root cause

    overall_root_cause: {overall_root_cause}
    root_cause_confidence: {root_cause_confidence}

{overall_explanation}

## Classification counts

{count_md}

## Per-case classification

{per_case_md}
"""
    analysis_md.write_text(analysis_text, encoding="utf-8")

    doc.write_text(f"""# Stage 23.3：扰动可观测性根因分析

## 1. 目标

Stage 23.3 基于 Stage 23.2 的 qvel injection trace diagnostic，解释 Stage 22 中 qvel 初始速度扰动没有造成 summary 指标变化的原因。

本阶段不新增控制器，不新增真实机器人实验，不重新声明 observable perturbation robustness。

## 2. 结果

Stage 23.3 result: {result}

Failure count: {failure_count}

Overall root cause: `{overall_root_cause}`

Root-cause confidence: `{root_cause_confidence}`

## 3. 关键结论

{conclusion}

{supported_claim}

## 4. Stage 22 negative evidence 背景

    observable_perturbation_pass={stage22_observable_pass}
    perturbation_metric_variability_detected={stage22_variability_detected}
    recommendation_relation_stable={stage22_recommendation_relation_stable}
    recommendation_observable_robust={stage22_recommendation_observable_robust}

## 5. Stage 23.2 trace flags

    all_nonzero_perturbations_written={all_nonzero_written}
    all_after_forward_preserved={all_after_forward_preserved}
    any_first_step_state_changed={any_first_step_state_changed}

## 6. 根因类别计数

{count_md}

## 7. 逐 case 根因分析

{per_case_md}

## 8. 当前支持的表述

Stage 23 支持：

    Stage 23 对 Stage 22 的 qvel perturbation negative evidence 进行了 root-cause audit。
    当前结果解释了 Stage 22 为什么没有形成 observable perturbation robustness evidence。

## 9. 当前不支持的表述

Stage 23 不支持：

  * 不支持 `scale=0.010` 已通过 observable perturbation robustness 验证；
  * 不支持 `scale=0.010` 升级为 observable-perturbation-tested recommended candidate scale；
  * 不支持完整 MPC-WBC 速度控制器已经完成；
  * 不支持 `scale=0.010` 可以直接用于真实机器人；
  * 不支持真实机器人 torque 执行或硬件 torque enablement 已完成；
  * 不支持复杂地形或外力冲击鲁棒性已完成。
""", encoding="utf-8")

    summary = {
        "stage": "23.3",
        "name": "perturbation observability root-cause analysis",
        "result": result,
        "failure_count": failure_count,
        "overall_root_cause": overall_root_cause,
        "overall_explanation": overall_explanation,
        "root_cause_confidence": root_cause_confidence,
        "stage22_observable_perturbation_pass": stage22_observable_pass,
        "stage22_perturbation_metric_variability_detected": stage22_variability_detected,
        "stage22_recommendation_relation_stable": stage22_recommendation_relation_stable,
        "stage22_recommendation_observable_robust": stage22_recommendation_observable_robust,
        "stage23_2_all_nonzero_perturbations_written": all_nonzero_written,
        "stage23_2_all_after_forward_preserved": all_after_forward_preserved,
        "stage23_2_any_first_step_state_changed": any_first_step_state_changed,
        "classification_counts": classification_counts,
        "conclusion": conclusion,
        "supported_claim": supported_claim,
        "generated_files": [
            str(per_case_csv.relative_to(root)),
            str(validation_csv.relative_to(root)),
            str(analysis_md.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(doc.relative_to(root)),
        ],
        "claim_boundary": [
            "root-cause analysis only",
            "explains Stage 22 negative evidence",
            "does not upgrade scale=0.010 to observable-perturbation-tested recommended candidate scale",
            "no observable perturbation robustness claim",
            "no full MPC-WBC velocity controller claim",
            "no real robot torque execution claim",
            "no hardware torque enablement claim",
            "no terrain or external-force robustness claim",
        ],
        "per_case_rows": per_case_rows,
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"stage23_3_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"overall_root_cause: {overall_root_cause}")
    print(f"root_cause_confidence: {root_cause_confidence}")
    print(f"summary: {summary_json.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
