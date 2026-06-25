#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


START = "<!-- STAGE24_ENTRY_DOCS_SYNC_START -->"
END = "<!-- STAGE24_ENTRY_DOCS_SYNC_END -->"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def replace_marked_block(text: str, block: str) -> str:
    if START in text and END in text:
        before = text.split(START)[0].rstrip()
        after = text.split(END, 1)[1].lstrip()
        return before + "\n\n" + block.rstrip() + "\n\n" + after
    return text.rstrip() + "\n\n" + block.rstrip() + "\n"


def main() -> int:
    root = repo_root()
    docs = root / "docs"
    logs = root / "results" / "logs_sample"
    docs.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    readme = root / "README.md"
    project_status = root / "PROJECT_STATUS.md"
    artifact_index = docs / "ARTIFACT_INDEX.md"

    s24_0_path = logs / "stage24_0_short_horizon_metric_roadmap_summary.json"
    s24_1_path = logs / "stage24_1_short_horizon_metric_preflight_summary.json"
    s24_2_path = logs / "stage24_2_short_horizon_perturbation_metrics_summary.json"
    s24_3_path = logs / "stage24_3_short_horizon_metric_observability_summary.json"
    s23_4_path = logs / "stage23_4_perturbation_observability_evidence_freeze_summary.json"
    s22_4_path = logs / "stage22_4_observable_perturbation_evidence_freeze_summary.json"

    s24_0 = load_json(s24_0_path)
    s24_1 = load_json(s24_1_path)
    s24_2 = load_json(s24_2_path)
    s24_3 = load_json(s24_3_path)
    s23_4 = load_json(s23_4_path)
    s22_4 = load_json(s22_4_path)

    metric_observability_class = str(s24_3.get("metric_observability_class", "unknown"))
    metric_audit_result = str(s24_3.get("metric_audit_result", "unknown"))
    conclusion = str(s24_3.get("conclusion", "Stage 24.3 conclusion unavailable."))
    supported_claim = str(s24_3.get("supported_claim", "Stage 24.3 supported claim unavailable."))

    any_pre = bool(s24_3.get("any_pre_step_trace_separation_detected", False))
    all_pre = bool(s24_3.get("all_pre_step_trace_separation_detected", False))
    any_post = bool(s24_3.get("any_post_step_trace_separation_detected", False))
    any_early = bool(s24_3.get("any_early_window_trace_separation_detected", False))
    all_early = bool(s24_3.get("all_early_window_trace_separation_detected", False))

    max_pre = float(s24_3.get("max_pre_step_qvel_axis_diff_vs_nominal", 0.0))
    max_post = float(s24_3.get("max_post_step_state_delta", 0.0))
    max_early = float(s24_3.get("max_early_window_state_delta", 0.0))
    mean_early = float(s24_3.get("mean_early_window_state_delta", 0.0))

    stage23_root_cause = str(s23_4.get("overall_root_cause", "unknown"))
    stage23_confidence = str(s23_4.get("root_cause_confidence", "unknown"))

    stage22_observable = bool(s22_4.get("observable_perturbation_pass", False))
    stage22_variability = bool(s22_4.get("perturbation_metric_variability_detected", False))
    stage22_recommendation_observable = bool(s22_4.get("recommendation_observable_robust", False))

    required = [
        "README.md",
        "PROJECT_STATUS.md",
        "docs/ARTIFACT_INDEX.md",

        "docs/STAGE24_SHORT_HORIZON_PERTURBATION_METRIC_ROADMAP.md",
        "docs/STAGE24_1_SHORT_HORIZON_METRIC_PREFLIGHT.md",
        "docs/STAGE24_2_SHORT_HORIZON_PERTURBATION_METRICS.md",
        "docs/STAGE24_3_SHORT_HORIZON_METRIC_ANALYSIS.md",

        "scripts/stage24_0_validate_short_horizon_metric_roadmap.py",
        "scripts/stage24_1_short_horizon_metric_design_preflight.py",
        "scripts/stage24_2_compute_short_horizon_perturbation_metrics.py",
        "scripts/stage24_3_analyze_short_horizon_metric_observability.py",

        "results/logs_sample/stage24_0_short_horizon_metric_roadmap_validation.csv",
        "results/logs_sample/stage24_0_short_horizon_metric_roadmap_summary.json",

        "results/logs_sample/stage24_1_short_horizon_metric_preflight_validation.csv",
        "results/logs_sample/stage24_1_short_horizon_metric_design.csv",
        "results/logs_sample/stage24_1_short_horizon_metric_trace_input_plan.csv",
        "results/logs_sample/stage24_1_short_horizon_metric_preflight_summary.json",

        "results/logs_sample/stage24_2_short_horizon_perturbation_metrics_per_case.csv",
        "results/logs_sample/stage24_2_short_horizon_perturbation_metrics_aggregate.csv",
        "results/logs_sample/stage24_2_short_horizon_perturbation_metrics_validation.csv",
        "results/logs_sample/stage24_2_short_horizon_perturbation_metrics.md",
        "results/logs_sample/stage24_2_short_horizon_perturbation_metrics_summary.json",

        "results/logs_sample/stage24_3_short_horizon_metric_observability_analysis.csv",
        "results/logs_sample/stage24_3_short_horizon_metric_observability_validation.csv",
        "results/logs_sample/stage24_3_short_horizon_metric_observability_analysis.md",
        "results/logs_sample/stage24_3_short_horizon_metric_observability_summary.json",
    ]

    readme_block = f"""{START}
## Stage 24：short-horizon perturbation-sensitive metric audit

Stage 24 基于 Stage 23 的 qvel trace 数据，构造并分析短时 perturbation-sensitive metrics，用于解释 Stage 22 的长期 summary 指标为什么没有捕捉短时 qvel 初始扰动。

Stage 24.3 metric conclusion:

  * `metric_observability_class={metric_observability_class}`
  * `metric_audit_result={metric_audit_result}`
  * `any_pre_step_trace_separation_detected={any_pre}`
  * `all_pre_step_trace_separation_detected={all_pre}`
  * `any_post_step_trace_separation_detected={any_post}`
  * `any_early_window_trace_separation_detected={any_early}`
  * `all_early_window_trace_separation_detected={all_early}`

数值摘要：

  * `max_pre_step_qvel_axis_diff_vs_nominal={max_pre:.12f}`
  * `max_post_step_state_delta={max_post:.12f}`
  * `max_early_window_state_delta={max_early:.12f}`
  * `mean_early_window_state_delta={mean_early:.12f}`

结论：

    {conclusion}

    {supported_claim}

当前可以声明：

  * Stage 24 构造并分析了短时 perturbation-sensitive metrics；
  * qvel 扰动在 injection / mj_forward 阶段能被短时指标检测到；
  * aligned after_mj_step rows 中没有相对 nominal 的持续 trace separation；
  * Stage 22 的长期 summary 指标没有变化是合理的；
  * 后续扰动审计应显式加入 injection-stage 或 pre-step trace metrics。

当前不能声明：

  * 不能声明 `scale=0.010` 已通过 observable perturbation robustness 验证；
  * 不能声明 `scale=0.010` 升级为 observable-perturbation-tested recommended candidate scale；
  * 不能声明完整 MPC-WBC 速度控制器已经完成；
  * 不能声明 `scale=0.010` 可以直接用于真实机器人；
  * 不能声明真实机器人 torque 执行或硬件 torque enablement 已完成；
  * 不能声明复杂地形或外力冲击鲁棒性已完成。
{END}
"""

    status_block = f"""{START}
## Stage 24 状态：short-horizon perturbation-sensitive metric audit

当前状态：已完成 Stage 24.0–24.3，并在 Stage 24.4 冻结证据。

| 阶段 | 结果 | 证据 |
|---|---:|---|
| 24.0 | {s24_0.get("result", "unknown")} | `docs/STAGE24_SHORT_HORIZON_PERTURBATION_METRIC_ROADMAP.md` |
| 24.1 | {s24_1.get("result", "unknown")} | `docs/STAGE24_1_SHORT_HORIZON_METRIC_PREFLIGHT.md` |
| 24.2 | {s24_2.get("result", "unknown")} | `docs/STAGE24_2_SHORT_HORIZON_PERTURBATION_METRICS.md` |
| 24.3 | {s24_3.get("result", "unknown")} | `docs/STAGE24_3_SHORT_HORIZON_METRIC_ANALYSIS.md` |

核心结论：

    metric_observability_class={metric_observability_class}
    metric_audit_result={metric_audit_result}
    any_pre_step_trace_separation_detected={any_pre}
    any_post_step_trace_separation_detected={any_post}
    any_early_window_trace_separation_detected={any_early}

解释：

    qvel 扰动在 injection / mj_forward 阶段可被检测到；
    aligned after_mj_step rows 中没有相对 nominal 的持续 trace separation；
    因此 Stage 22 的长期 summary 指标没有变化是合理的。
    该结论只支持短时指标审计，不支持 observable perturbation robustness。
    不能声明 `scale=0.010` 升级为 observable-perturbation-tested recommended candidate scale。
{END}
"""

    artifact_block = f"""{START}
## Stage 24 Artifacts

Stage 24 artifact 记录 short-horizon perturbation-sensitive metric audit。

结论边界：

  * `metric_observability_class={metric_observability_class}`
  * `metric_audit_result={metric_audit_result}`
  * `any_pre_step_trace_separation_detected={any_pre}`
  * `any_post_step_trace_separation_detected={any_post}`
  * `any_early_window_trace_separation_detected={any_early}`
  * 当前不将 `scale=0.010` 升级为 observable-perturbation-tested recommended candidate scale。
  * Stage 24 只支持短时指标审计，不支持 observable perturbation robustness。
  * aligned after_mj_step rows 中没有持续 trace separation。

| 阶段 | Artifact | 作用 |
|---|---|---|
| 24.0 | `docs/STAGE24_SHORT_HORIZON_PERTURBATION_METRIC_ROADMAP.md` | 短时扰动敏感指标路线图 |
| 24.1 | `docs/STAGE24_1_SHORT_HORIZON_METRIC_PREFLIGHT.md` | 短时指标设计预检查 |
| 24.2 | `docs/STAGE24_2_SHORT_HORIZON_PERTURBATION_METRICS.md` | 短时扰动敏感指标计算 |
| 24.2 | `results/logs_sample/stage24_2_short_horizon_perturbation_metrics_per_case.csv` | per-case 指标表 |
| 24.2 | `results/logs_sample/stage24_2_short_horizon_perturbation_metrics_aggregate.csv` | aggregate 指标表 |
| 24.3 | `docs/STAGE24_3_SHORT_HORIZON_METRIC_ANALYSIS.md` | 短时指标可观测性分析 |
| 24.3 | `results/logs_sample/stage24_3_short_horizon_metric_observability_summary.json` | Stage 24.3 summary |
| 24.4 | `docs/STAGE24_4_SHORT_HORIZON_METRIC_EVIDENCE_FREEZE.md` | Stage 24 证据冻结报告 |
| 24.4 | `results/logs_sample/stage24_4_short_horizon_metric_evidence_manifest.json` | Stage 24 manifest |
{END}
"""

    for p, block in [
        (readme, readme_block),
        (project_status, status_block),
        (artifact_index, artifact_block),
    ]:
        p.write_text(replace_marked_block(p.read_text(encoding="utf-8"), block), encoding="utf-8")

    validation_csv = logs / "stage24_4_short_horizon_metric_evidence_freeze_validation.csv"
    hashes_csv = logs / "stage24_4_short_horizon_metric_evidence_hashes.csv"
    manifest_json = logs / "stage24_4_short_horizon_metric_evidence_manifest.json"
    summary_json = logs / "stage24_4_short_horizon_metric_evidence_freeze_summary.json"
    freeze_doc = docs / "STAGE24_4_SHORT_HORIZON_METRIC_EVIDENCE_FREEZE.md"

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    for rel in required:
        path = root / rel
        check(f"required_exists::{rel}", path.is_file() and path.stat().st_size > 0, rel)

    for stage, path in [
        ("24.0", s24_0_path),
        ("24.1", s24_1_path),
        ("24.2", s24_2_path),
        ("24.3", s24_3_path),
    ]:
        data = load_json(path)
        check(f"summary_result_pass::{stage}", data.get("result") == "pass", f"result={data.get('result')}")

    check(
        "metric_observability_class_expected",
        metric_observability_class == "pre_step_only_detection_no_post_step_trace_separation",
        metric_observability_class,
    )
    check("metric_audit_result_partial_detection", metric_audit_result == "partial_detection", metric_audit_result)
    check("any_pre_step_trace_separation_true", any_pre is True, str(any_pre))
    check("all_pre_step_trace_separation_true", all_pre is True, str(all_pre))
    check("any_post_step_trace_separation_false", any_post is False, str(any_post))
    check("any_early_window_trace_separation_true", any_early is True, str(any_early))
    check("all_early_window_trace_separation_true", all_early is True, str(all_early))
    check("max_pre_delta_positive", max_pre > 0.0, f"{max_pre:.12f}")
    check("max_post_delta_zero", abs(max_post) <= 1e-12, f"{max_post:.12f}")
    check("max_early_delta_positive", max_early > 0.0, f"{max_early:.12f}")

    check(
        "stage23_root_cause_expected",
        stage23_root_cause == "C_summary_metrics_insensitive_to_short_horizon_trace_change",
        stage23_root_cause,
    )
    check("stage23_confidence_high", stage23_confidence == "high", stage23_confidence)
    check("stage22_observable_false", stage22_observable is False, str(stage22_observable))
    check("stage22_variability_false", stage22_variability is False, str(stage22_variability))
    check("stage22_recommendation_observable_false", stage22_recommendation_observable is False, str(stage22_recommendation_observable))

    for path in [readme, project_status, artifact_index]:
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(root))
        check(f"entry_has_stage24_marker::{path.name}", START in text and END in text, rel)
        check(f"entry_mentions_metric_class::{path.name}", metric_observability_class in text, rel)
        check(f"entry_mentions_pre_step::{path.name}", "pre-step" in text or "pre_step" in text, rel)
        check(f"entry_mentions_after_mj_step::{path.name}", "after_mj_step" in text, rel)
        check(f"entry_mentions_no_upgrade_scale::{path.name}", "不将 `scale=0.010` 升级" in text or "不能声明 `scale=0.010` 升级" in text, rel)
        check(f"entry_mentions_no_real_robot::{path.name}", "真实机器人" in text or "real robot" in text, rel)
        check(f"entry_mentions_no_observable_robustness::{path.name}", "不支持 observable perturbation robustness" in text or "不能声明 `scale=0.010` 已通过 observable perturbation robustness" in text, rel)

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    write_csv(validation_csv, checks, ["check", "status", "detail"])

    freeze_doc.write_text(f"""# Stage 24.4：short-horizon metric evidence freeze

## 1. 目标

Stage 24.4 冻结 Stage 24.0–24.3 的短时扰动敏感指标审计证据。

本阶段不新增控制器，不新增 rollout，不新增真实机器人实验，只同步入口文档、生成 manifest，并冻结结论边界。

## 2. 阶段结果

| 阶段 | 结果 |
|---|---|
| 24.0 | {s24_0.get("result", "unknown")} |
| 24.1 | {s24_1.get("result", "unknown")} |
| 24.2 | {s24_2.get("result", "unknown")} |
| 24.3 | {s24_3.get("result", "unknown")} |

## 3. 核心结论

    metric_observability_class: {metric_observability_class}
    metric_audit_result: {metric_audit_result}

    any_pre_step_trace_separation_detected: {any_pre}
    all_pre_step_trace_separation_detected: {all_pre}
    any_post_step_trace_separation_detected: {any_post}
    any_early_window_trace_separation_detected: {any_early}
    all_early_window_trace_separation_detected: {all_early}

    max_pre_step_qvel_axis_diff_vs_nominal: {max_pre:.12f}
    max_post_step_state_delta: {max_post:.12f}
    max_early_window_state_delta: {max_early:.12f}
    mean_early_window_state_delta: {mean_early:.12f}

{conclusion}

{supported_claim}

## 4. 当前证据支持

Stage 24 支持：

  * 构造并分析短时 perturbation-sensitive metrics；
  * qvel 扰动在 injection / mj_forward 阶段可被短时指标检测到；
  * aligned after_mj_step rows 中没有相对 nominal 的持续 trace separation；
  * Stage 22 的长期 summary 指标没有变化是合理的；
  * 后续扰动审计应加入 injection-stage 或 pre-step trace metrics。

## 5. 当前证据不支持

Stage 24 不支持：

  * 不支持 `scale=0.010` 已通过 observable perturbation robustness 验证；
  * 不支持 `scale=0.010` 升级为 observable-perturbation-tested recommended candidate scale；
  * 不支持完整 MPC-WBC 速度控制器已经完成；
  * 不支持 `scale=0.010` 可以直接用于真实机器人；
  * 不支持真实机器人 torque 执行或硬件 torque enablement 已完成；
  * 不支持复杂地形或外力冲击鲁棒性已完成。

## 6. 冻结结果

    stage24_4_result: {result}
    failure_count: {failure_count}
""", encoding="utf-8")

    generated = [
        str(validation_csv.relative_to(root)),
        str(hashes_csv.relative_to(root)),
        str(manifest_json.relative_to(root)),
        str(summary_json.relative_to(root)),
        str(freeze_doc.relative_to(root)),
    ]

    artifact_rels = required + [
        str(validation_csv.relative_to(root)),
        str(freeze_doc.relative_to(root)),
    ]

    hash_rows = []
    manifest_items = []
    for rel in artifact_rels:
        path = root / rel
        exists = path.is_file()
        digest = sha256_file(path) if exists else ""
        size = path.stat().st_size if exists else 0
        hash_rows.append({"path": rel, "sha256": digest, "size_bytes": str(size)})
        manifest_items.append({"path": rel, "sha256": digest, "size_bytes": size, "exists": exists})

    write_csv(hashes_csv, hash_rows, ["path", "sha256", "size_bytes"])

    manifest = {
        "stage": "24.4",
        "name": "short-horizon perturbation-sensitive metric evidence freeze",
        "result": result,
        "failure_count": failure_count,
        "artifact_count": len(manifest_items),
        "metric_observability_class": metric_observability_class,
        "metric_audit_result": metric_audit_result,
        "conclusion": conclusion,
        "supported_claim": supported_claim,
        "any_pre_step_trace_separation_detected": any_pre,
        "all_pre_step_trace_separation_detected": all_pre,
        "any_post_step_trace_separation_detected": any_post,
        "any_early_window_trace_separation_detected": any_early,
        "all_early_window_trace_separation_detected": all_early,
        "max_pre_step_qvel_axis_diff_vs_nominal": max_pre,
        "max_post_step_state_delta": max_post,
        "max_early_window_state_delta": max_early,
        "mean_early_window_state_delta": mean_early,
        "stage23_root_cause": stage23_root_cause,
        "stage23_confidence": stage23_confidence,
        "stage22_observable_perturbation_pass": stage22_observable,
        "stage22_perturbation_metric_variability_detected": stage22_variability,
        "stage22_recommendation_observable_robust": stage22_recommendation_observable,
        "artifacts": manifest_items,
        "claim_boundary": [
            "short-horizon metric audit only",
            "no new rollout generated",
            "does not upgrade scale=0.010 to observable-perturbation-tested recommended candidate scale",
            "no observable perturbation robustness claim",
            "no full MPC-WBC velocity controller claim",
            "no real robot torque execution claim",
            "no hardware torque enablement claim",
            "no terrain or external-force robustness claim",
        ],
    }
    manifest_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = {
        "stage": "24.4",
        "name": "short-horizon perturbation-sensitive metric evidence freeze",
        "result": result,
        "failure_count": failure_count,
        "metric_observability_class": metric_observability_class,
        "metric_audit_result": metric_audit_result,
        "any_pre_step_trace_separation_detected": any_pre,
        "all_pre_step_trace_separation_detected": all_pre,
        "any_post_step_trace_separation_detected": any_post,
        "any_early_window_trace_separation_detected": any_early,
        "all_early_window_trace_separation_detected": all_early,
        "max_pre_step_qvel_axis_diff_vs_nominal": max_pre,
        "max_post_step_state_delta": max_post,
        "max_early_window_state_delta": max_early,
        "mean_early_window_state_delta": mean_early,
        "generated_files": generated,
        "updated_files": [
            "README.md",
            "PROJECT_STATUS.md",
            "docs/ARTIFACT_INDEX.md",
        ],
        "conclusion": conclusion,
        "supported_claim": supported_claim,
        "checks": checks,
    }
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"stage24_4_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"metric_observability_class: {metric_observability_class}")
    print(f"metric_audit_result: {metric_audit_result}")
    print(f"any_pre_step_trace_separation_detected: {any_pre}")
    print(f"any_post_step_trace_separation_detected: {any_post}")
    print(f"any_early_window_trace_separation_detected: {any_early}")
    print(f"manifest: {manifest_json.relative_to(root)}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"freeze_doc: {freeze_doc.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
