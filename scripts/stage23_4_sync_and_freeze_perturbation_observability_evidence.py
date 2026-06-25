#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


START = "<!-- STAGE23_ENTRY_DOCS_SYNC_START -->"
END = "<!-- STAGE23_ENTRY_DOCS_SYNC_END -->"


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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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

    s23_0_path = logs / "stage23_0_perturbation_observability_roadmap_summary.json"
    s23_1_path = logs / "stage23_1_qvel_injection_trace_preflight_summary.json"
    s23_2_path = logs / "stage23_2_qvel_injection_trace_summary.json"
    s23_3_path = logs / "stage23_3_perturbation_observability_root_cause_summary.json"

    s23_0 = load_json(s23_0_path)
    s23_1 = load_json(s23_1_path)
    s23_2 = load_json(s23_2_path)
    s23_3 = load_json(s23_3_path)

    overall_root_cause = str(s23_3.get("overall_root_cause", "unknown"))
    root_cause_confidence = str(s23_3.get("root_cause_confidence", "unknown"))
    conclusion = str(s23_3.get("conclusion", "Stage 23 root-cause conclusion unavailable."))
    supported_claim = str(s23_3.get("supported_claim", "Stage 23 supported claim unavailable."))

    stage22_observable_pass = bool(s23_3.get("stage22_observable_perturbation_pass", False))
    stage22_variability = bool(s23_3.get("stage22_perturbation_metric_variability_detected", False))
    stage22_recommendation_stable = bool(s23_3.get("stage22_recommendation_relation_stable", False))
    stage22_recommendation_observable = bool(s23_3.get("stage22_recommendation_observable_robust", False))

    all_nonzero_written = bool(s23_3.get("stage23_2_all_nonzero_perturbations_written", False))
    all_after_forward_preserved = bool(s23_3.get("stage23_2_all_after_forward_preserved", False))
    any_first_step_state_changed = bool(s23_3.get("stage23_2_any_first_step_state_changed", False))

    execution_rows = read_rows(logs / "stage23_2_qvel_injection_trace_execution.csv")

    required = [
        "README.md",
        "PROJECT_STATUS.md",
        "docs/ARTIFACT_INDEX.md",

        "docs/STAGE23_PERTURBATION_OBSERVABILITY_ROOT_CAUSE_ROADMAP.md",
        "docs/STAGE23_1_QVEL_INJECTION_TRACE_PREFLIGHT.md",
        "docs/STAGE23_2_QVEL_INJECTION_TRACE_DIAGNOSTIC.md",
        "docs/STAGE23_3_PERTURBATION_OBSERVABILITY_ROOT_CAUSE_ANALYSIS.md",

        "scripts/stage23_0_validate_perturbation_observability_roadmap.py",
        "scripts/stage23_1_qvel_injection_trace_preflight.py",
        "scripts/stage23_2_qvel_injection_trace_runner.py",
        "scripts/stage23_2_run_qvel_injection_trace_diagnostic.py",
        "scripts/stage23_2_validate_qvel_injection_trace_diagnostic.py",
        "scripts/stage23_3_perturbation_observability_root_cause_analysis.py",

        "results/logs_sample/stage23_0_perturbation_observability_roadmap_validation.csv",
        "results/logs_sample/stage23_0_perturbation_observability_roadmap_summary.json",

        "results/logs_sample/stage23_1_qvel_injection_trace_preflight_validation.csv",
        "results/logs_sample/stage23_1_qvel_injection_trace_preflight_context.txt",
        "results/logs_sample/stage23_1_qvel_injection_trace_plan.csv",
        "results/logs_sample/stage23_1_qvel_injection_trace_preflight_summary.json",

        "results/logs_sample/stage23_2_qvel_injection_trace_execution.csv",
        "results/logs_sample/stage23_2_qvel_injection_trace_execution_summary.json",
        "results/logs_sample/stage23_2_qvel_injection_trace_validation.csv",
        "results/logs_sample/stage23_2_qvel_injection_trace_diagnostic_table.csv",
        "results/logs_sample/stage23_2_qvel_injection_trace_diagnostic_table.md",
        "results/logs_sample/stage23_2_qvel_injection_trace_summary.json",

        "results/logs_sample/stage23_3_perturbation_observability_root_cause_per_case.csv",
        "results/logs_sample/stage23_3_perturbation_observability_root_cause_validation.csv",
        "results/logs_sample/stage23_3_perturbation_observability_root_cause_analysis.md",
        "results/logs_sample/stage23_3_perturbation_observability_root_cause_summary.json",
    ]

    for row in execution_rows:
        for key in ["trace_csv", "case_summary_json", "normal_log_csv", "normal_summary_csv"]:
            rel = row.get(key, "")
            if rel and rel not in required:
                required.append(rel)

    readme_block = f"""{START}
## Stage 23：perturbation observability root-cause audit

Stage 23 对 Stage 22 的 qvel perturbation negative evidence 进行了根因审计。

Stage 22 的冻结结果是：

  * `observable_perturbation_pass=False`
  * `perturbation_metric_variability_detected=False`
  * `recommendation_relation_stable=True`
  * `recommendation_observable_robust=False`

Stage 23 的 trace diagnostic 结果是：

  * `all_nonzero_perturbations_written={all_nonzero_written}`
  * `all_after_forward_preserved={all_after_forward_preserved}`
  * `any_first_step_state_changed={any_first_step_state_changed}`

Stage 23.3 root-cause conclusion:

  * `overall_root_cause={overall_root_cause}`
  * `root_cause_confidence={root_cause_confidence}`

结论：

    {conclusion}

    {supported_claim}

当前可以声明：

  * Stage 23 解释了 Stage 22 的 qvel perturbation negative evidence；
  * qvel 扰动确实写入并在 `mj_forward` 后保持；
  * qvel 扰动能在短时 trace 中产生状态差异；
  * Stage 22 summary 指标没有变化的根因是 summary 指标对短时初始 qvel 扰动不敏感。

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
## Stage 23 状态：perturbation observability root-cause audit

当前状态：已完成 Stage 23.0–23.3，并在 Stage 23.4 冻结证据。

| 阶段 | 结果 | 证据 |
|---|---:|---|
| 23.0 | {s23_0.get("result", "unknown")} | `docs/STAGE23_PERTURBATION_OBSERVABILITY_ROOT_CAUSE_ROADMAP.md` |
| 23.1 | {s23_1.get("result", "unknown")} | `docs/STAGE23_1_QVEL_INJECTION_TRACE_PREFLIGHT.md` |
| 23.2 | {s23_2.get("result", "unknown")} | `docs/STAGE23_2_QVEL_INJECTION_TRACE_DIAGNOSTIC.md` |
| 23.3 | {s23_3.get("result", "unknown")} | `docs/STAGE23_3_PERTURBATION_OBSERVABILITY_ROOT_CAUSE_ANALYSIS.md` |

核心结论：

    overall_root_cause={overall_root_cause}
    root_cause_confidence={root_cause_confidence}
    all_nonzero_perturbations_written={all_nonzero_written}
    all_after_forward_preserved={all_after_forward_preserved}
    any_first_step_state_changed={any_first_step_state_changed}

解释：

    Stage 22 的 qvel perturbation negative evidence 不是因为 qvel 没有写入；
    而是因为短时 qvel 扰动没有反映到 Stage 22 的长期 summary 指标变化中。
    更准确地说，Stage 22 的 summary 指标对短时初始 qvel 扰动不敏感。

结论边界：

    不能声明 `scale=0.010` 升级为 observable-perturbation-tested recommended candidate scale。
    不能将 Stage 23 解释为 observable perturbation robustness 验证成功。
{END}
"""

    artifact_block = f"""{START}
## Stage 23 Artifacts

Stage 23 artifact 记录 perturbation observability root-cause audit。

结论边界：

  * `overall_root_cause={overall_root_cause}`
  * `root_cause_confidence={root_cause_confidence}`
  * `stage22_perturbation_metric_variability_detected={stage22_variability}`
  * 当前不将 `scale=0.010` 升级为 observable-perturbation-tested recommended candidate scale。
  * Stage 22 的 summary 指标对短时初始 qvel 扰动不敏感。

| 阶段 | Artifact | 作用 |
|---|---|---|
| 23.0 | `docs/STAGE23_PERTURBATION_OBSERVABILITY_ROOT_CAUSE_ROADMAP.md` | 根因审计路线图 |
| 23.1 | `docs/STAGE23_1_QVEL_INJECTION_TRACE_PREFLIGHT.md` | qvel trace 预检查 |
| 23.2 | `docs/STAGE23_2_QVEL_INJECTION_TRACE_DIAGNOSTIC.md` | qvel injection trace diagnostic |
| 23.2 | `results/logs_sample/stage23_2_qvel_injection_trace_diagnostic_table.csv` | trace 诊断表 |
| 23.3 | `docs/STAGE23_3_PERTURBATION_OBSERVABILITY_ROOT_CAUSE_ANALYSIS.md` | 根因分析报告 |
| 23.3 | `results/logs_sample/stage23_3_perturbation_observability_root_cause_summary.json` | 根因分析 summary |
| 23.4 | `docs/STAGE23_4_PERTURBATION_OBSERVABILITY_EVIDENCE_FREEZE.md` | Stage 23 证据冻结报告 |
| 23.4 | `results/logs_sample/stage23_4_perturbation_observability_evidence_manifest.json` | Stage 23 manifest |
{END}
"""

    for p, block in [
        (readme, readme_block),
        (project_status, status_block),
        (artifact_index, artifact_block),
    ]:
        p.write_text(replace_marked_block(p.read_text(encoding="utf-8"), block), encoding="utf-8")

    validation_csv = logs / "stage23_4_perturbation_observability_evidence_freeze_validation.csv"
    hashes_csv = logs / "stage23_4_perturbation_observability_evidence_hashes.csv"
    manifest_json = logs / "stage23_4_perturbation_observability_evidence_manifest.json"
    summary_json = logs / "stage23_4_perturbation_observability_evidence_freeze_summary.json"
    freeze_doc = docs / "STAGE23_4_PERTURBATION_OBSERVABILITY_EVIDENCE_FREEZE.md"

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail})

    for rel in required:
        path = root / rel
        check(f"required_exists::{rel}", path.is_file() and path.stat().st_size > 0, rel)

    for stage, path in [
        ("23.0", s23_0_path),
        ("23.1", s23_1_path),
        ("23.2", s23_2_path),
        ("23.3", s23_3_path),
    ]:
        data = load_json(path)
        check(f"summary_result_pass::{stage}", data.get("result") == "pass", f"result={data.get('result')}")

    check("overall_root_cause_recorded", overall_root_cause == "C_summary_metrics_insensitive_to_short_horizon_trace_change", overall_root_cause)
    check("root_cause_confidence_high_recorded", root_cause_confidence == "high", root_cause_confidence)
    check("all_nonzero_perturbations_written_true", all_nonzero_written is True, str(all_nonzero_written))
    check("all_after_forward_preserved_true", all_after_forward_preserved is True, str(all_after_forward_preserved))
    check("any_first_step_state_changed_true", any_first_step_state_changed is True, str(any_first_step_state_changed))

    check("stage22_observable_pass_false", stage22_observable_pass is False, str(stage22_observable_pass))
    check("stage22_variability_false", stage22_variability is False, str(stage22_variability))
    check("stage22_recommendation_stable_true", stage22_recommendation_stable is True, str(stage22_recommendation_stable))
    check("stage22_recommendation_observable_false", stage22_recommendation_observable is False, str(stage22_recommendation_observable))

    for path in [readme, project_status, artifact_index]:
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(root))
        check(f"entry_has_stage23_marker::{path.name}", START in text and END in text, rel)
        check(f"entry_mentions_root_cause::{path.name}", overall_root_cause in text, rel)
        check(f"entry_mentions_not_upgrade_scale::{path.name}", "不将 `scale=0.010` 升级" in text or "不能声明 `scale=0.010` 升级" in text, rel)
        check(f"entry_mentions_no_real_robot::{path.name}", "真实机器人" in text or "real robot" in text, rel)
        check(f"entry_mentions_summary_insensitive::{path.name}", "summary" in text and "不敏感" in text, rel)

    hash_rows = []
    manifest_items = []

    for rel in required:
        path = root / rel
        exists = path.is_file()
        digest = sha256_file(path) if exists else ""
        size = path.stat().st_size if exists else 0
        hash_rows.append({"path": rel, "sha256": digest, "size_bytes": str(size)})
        manifest_items.append({"path": rel, "sha256": digest, "size_bytes": size, "exists": exists})

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    write_csv(validation_csv, checks, ["check", "status", "detail"])
    write_csv(hashes_csv, hash_rows, ["path", "sha256", "size_bytes"])

    manifest = {
        "stage": "23.4",
        "name": "perturbation observability root-cause evidence freeze",
        "result": result,
        "failure_count": failure_count,
        "artifact_count": len(manifest_items),
        "overall_root_cause": overall_root_cause,
        "root_cause_confidence": root_cause_confidence,
        "conclusion": conclusion,
        "supported_claim": supported_claim,
        "stage22_observable_perturbation_pass": stage22_observable_pass,
        "stage22_perturbation_metric_variability_detected": stage22_variability,
        "stage22_recommendation_relation_stable": stage22_recommendation_stable,
        "stage22_recommendation_observable_robust": stage22_recommendation_observable,
        "stage23_2_all_nonzero_perturbations_written": all_nonzero_written,
        "stage23_2_all_after_forward_preserved": all_after_forward_preserved,
        "stage23_2_any_first_step_state_changed": any_first_step_state_changed,
        "artifacts": manifest_items,
        "claim_boundary": [
            "root-cause evidence freeze only",
            "explains Stage 22 negative evidence",
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
        "stage": "23.4",
        "name": "perturbation observability root-cause evidence freeze",
        "result": result,
        "failure_count": failure_count,
        "artifact_count": len(manifest_items),
        "overall_root_cause": overall_root_cause,
        "root_cause_confidence": root_cause_confidence,
        "stage23_2_all_nonzero_perturbations_written": all_nonzero_written,
        "stage23_2_all_after_forward_preserved": all_after_forward_preserved,
        "stage23_2_any_first_step_state_changed": any_first_step_state_changed,
        "generated_files": [
            str(validation_csv.relative_to(root)),
            str(hashes_csv.relative_to(root)),
            str(manifest_json.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(freeze_doc.relative_to(root)),
        ],
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

    freeze_doc.write_text(f"""# Stage 23.4：perturbation observability evidence freeze

## 1. 目标

Stage 23.4 冻结 Stage 23.0–23.3 的扰动可观测性根因审计证据。

本阶段不新增控制器，不新增 rollout，不新增真实机器人实验，只同步入口文档、生成 manifest，并冻结结论边界。

## 2. 阶段结果

| 阶段 | 结果 |
|---|---|
| 23.0 | {s23_0.get("result", "unknown")} |
| 23.1 | {s23_1.get("result", "unknown")} |
| 23.2 | {s23_2.get("result", "unknown")} |
| 23.3 | {s23_3.get("result", "unknown")} |

## 3. 核心结论

    overall_root_cause: {overall_root_cause}
    root_cause_confidence: {root_cause_confidence}

    all_nonzero_perturbations_written: {all_nonzero_written}
    all_after_forward_preserved: {all_after_forward_preserved}
    any_first_step_state_changed: {any_first_step_state_changed}

{conclusion}

{supported_claim}

## 4. 当前证据支持

Stage 23 支持：

  * 对 Stage 22 qvel perturbation negative evidence 进行了 root-cause audit；
  * qvel 扰动确实写入 MuJoCo `data.qvel`；
  * qvel 扰动在 `mujoco.mj_forward` 后保持；
  * qvel 扰动能在短时 trace 中产生状态差异；
  * Stage 22 summary 指标未变化的根因是 summary 指标对短时初始 qvel 扰动不敏感。

## 5. 当前证据不支持

Stage 23 不支持：

  * 不支持 `scale=0.010` 已通过 observable perturbation robustness 验证；
  * 不支持 `scale=0.010` 升级为 observable-perturbation-tested recommended candidate scale；
  * 不支持完整 MPC-WBC 速度控制器已经完成；
  * 不支持 `scale=0.010` 可以直接用于真实机器人；
  * 不支持真实机器人 torque 执行或硬件 torque enablement 已完成；
  * 不支持复杂地形或外力冲击鲁棒性已完成。

## 6. 冻结结果

    stage23_4_result: {result}
    failure_count: {failure_count}
    artifact_count: {len(manifest_items)}
""", encoding="utf-8")

    print(f"stage23_4_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"overall_root_cause: {overall_root_cause}")
    print(f"root_cause_confidence: {root_cause_confidence}")
    print(f"stage23_2_all_nonzero_perturbations_written: {all_nonzero_written}")
    print(f"stage23_2_all_after_forward_preserved: {all_after_forward_preserved}")
    print(f"stage23_2_any_first_step_state_changed: {any_first_step_state_changed}")
    print(f"manifest: {manifest_json.relative_to(root)}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"freeze_doc: {freeze_doc.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
