#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


START = "<!-- STAGE22_ENTRY_DOCS_SYNC_START -->"
END = "<!-- STAGE22_ENTRY_DOCS_SYNC_END -->"

PERTURBATION_IDS = [
    "nominal",
    "vx_plus",
    "vx_minus",
    "vy_plus",
    "vy_minus",
    "yawrate_plus",
    "yawrate_minus",
]

SCALE_CASES = [
    ("0.000", "0p000", "baseline"),
    ("0.010", "0p010", "mpc_assisted_candidate"),
    ("0.020", "0p020", "mpc_assisted_candidate"),
]


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

    s22_0_path = logs / "stage22_0_observable_perturbation_roadmap_summary.json"
    s22_1_path = logs / "stage22_1_qvel_perturbation_preflight_summary.json"
    s22_2_path = logs / "stage22_2_observable_perturbation_summary.json"
    s22_3_path = logs / "stage22_3_observable_robustness_summary.json"

    s22_0 = load_json(s22_0_path)
    s22_1 = load_json(s22_1_path)
    s22_2 = load_json(s22_2_path)
    s22_3 = load_json(s22_3_path)

    recommended_scale = str(s22_3.get("recommended_scale", "0.010"))
    baseline_scale = str(s22_3.get("baseline_scale", "0.000"))
    regression_scale = str(s22_3.get("regression_anchor_scale", "0.020"))

    observable_perturbation_pass = bool(s22_3.get("observable_perturbation_pass", False))
    perturbation_metric_variability_detected = bool(s22_3.get("perturbation_metric_variability_detected", False))
    recommendation_relation_stable = bool(s22_3.get("recommendation_relation_stable", False))
    recommendation_observable_robust = bool(s22_3.get("recommendation_observable_robust", False))

    conclusion = str(s22_3.get(
        "conclusion",
        "Stage 22.3 analysis passed, but observable perturbation robustness was not established.",
    ))
    claim_support = str(s22_3.get(
        "claim_support",
        "Current evidence does not support upgrading scale=0.010 to observable-perturbation-tested recommended candidate scale.",
    ))

    required = [
        "README.md",
        "PROJECT_STATUS.md",
        "docs/ARTIFACT_INDEX.md",

        "docs/STAGE22_OBSERVABLE_PERTURBATION_ROBUSTNESS_ROADMAP.md",
        "docs/STAGE22_1_QVEL_PERTURBATION_PREFLIGHT.md",
        "docs/STAGE22_2_OBSERVABLE_PERTURBATION_ROLLOUT.md",
        "docs/STAGE22_3_OBSERVABLE_ROBUSTNESS_ANALYSIS.md",

        "scripts/stage22_0_validate_observable_perturbation_roadmap.py",
        "scripts/stage22_1_qvel_perturbation_preflight.py",
        "scripts/stage22_2_observable_perturbation_runner.py",
        "scripts/stage22_2_run_observable_perturbation_rollouts.py",
        "scripts/stage22_2_validate_observable_perturbation_rollouts.py",
        "scripts/stage22_3_observable_robustness_analysis.py",

        "results/logs_sample/stage22_0_observable_perturbation_roadmap_validation.csv",
        "results/logs_sample/stage22_0_observable_perturbation_roadmap_summary.json",

        "results/logs_sample/stage22_1_qvel_perturbation_preflight_validation.csv",
        "results/logs_sample/stage22_1_qvel_perturbation_preflight_context.txt",
        "results/logs_sample/stage22_1_qvel_perturbation_output_plan.csv",
        "results/logs_sample/stage22_1_qvel_perturbation_preflight_summary.json",

        "results/logs_sample/stage22_2_observable_perturbation_execution.csv",
        "results/logs_sample/stage22_2_observable_perturbation_execution_summary.json",
        "results/logs_sample/stage22_2_observable_perturbation_validation.csv",
        "results/logs_sample/stage22_2_observable_perturbation_table.csv",
        "results/logs_sample/stage22_2_observable_perturbation_table.md",
        "results/logs_sample/stage22_2_observable_perturbation_summary.json",

        "results/logs_sample/stage22_3_observable_robustness_per_perturbation_checks.csv",
        "results/logs_sample/stage22_3_observable_robustness_per_scale_stats.csv",
        "results/logs_sample/stage22_3_observable_perturbation_variability.csv",
        "results/logs_sample/stage22_3_observable_robustness_validation.csv",
        "results/logs_sample/stage22_3_observable_robustness_analysis.md",
        "results/logs_sample/stage22_3_observable_robustness_summary.json",
    ]

    for pid in PERTURBATION_IDS:
        for _, tag, mode in SCALE_CASES:
            required += [
                f"results/logs_sample/stage22_2_observable_perturb_{pid}_{tag}_{mode}_log.csv",
                f"results/logs_sample/stage22_2_observable_perturb_{pid}_{tag}_{mode}_summary.csv",
            ]

    readme_block = f"""{START}
## Stage 22：observable qvel perturbation audit attempt

Stage 22 在 Stage 21 的基础上尝试引入 qvel 初始速度扰动，用于检查扰动是否能对 rollout summary 指标产生可观测变化。

当前阶段结果：

  * Stage 22.0 result: {s22_0.get("result", "unknown")}
  * Stage 22.1 result: {s22_1.get("result", "unknown")}
  * Stage 22.2 result: {s22_2.get("result", "unknown")}
  * Stage 22.3 result: {s22_3.get("result", "unknown")}

核心指标：

  * `observable_perturbation_pass={observable_perturbation_pass}`
  * `perturbation_metric_variability_detected={perturbation_metric_variability_detected}`
  * `recommendation_relation_stable={recommendation_relation_stable}`
  * `recommendation_observable_robust={recommendation_observable_robust}`

结论：

    {conclusion}

    {claim_support}

当前可以声明：

  * Stage 22 完成了 simulation-only qvel initial perturbation injection attempt。
  * 21 组 rollout 均通过稳定性边界。
  * `scale={recommended_scale}` 的推荐关系在当前记录指标中未被破坏。
  * 由于 `perturbation_metric_variability_detected=False`，Stage 22 不能声明完成 observable perturbation robustness audit。

当前不能声明：

  * 不能声明 `scale={recommended_scale}` 已升级为 observable-perturbation-tested recommended candidate scale；
  * 不能声明完整 MPC-WBC 速度控制器已经完成；
  * 不能声明 `scale={recommended_scale}` 可以直接用于真实机器人；
  * 不能声明 `scale={recommended_scale}` 对所有速度、地形、扰动和外力冲击都最优；
  * 不能声明真实机器人 torque 执行或硬件 torque enablement 已完成；
  * 不能声明复杂地形或外力冲击鲁棒性已完成。

更准确的表述是：

> Stage 22 尝试通过 qvel 初始速度扰动构造 observable perturbation audit。21 组 simulation-only rollout 均通过稳定性边界，且 scale={recommended_scale} 的推荐关系在当前记录指标中未被破坏；但扰动没有造成 summary 指标的可观测变化，因此 Stage 22 不能支持 observable perturbation robustness 结论。
{END}
"""

    status_block = f"""{START}
## Stage 22 状态：qvel observable perturbation attempt

当前状态：已完成 Stage 22.0–22.3，并在 Stage 22.4 冻结证据。

| 阶段 | 结果 | 证据 |
|---|---:|---|
| 22.0 | {s22_0.get("result", "unknown")} | `docs/STAGE22_OBSERVABLE_PERTURBATION_ROBUSTNESS_ROADMAP.md` |
| 22.1 | {s22_1.get("result", "unknown")} | `docs/STAGE22_1_QVEL_PERTURBATION_PREFLIGHT.md` |
| 22.2 | {s22_2.get("result", "unknown")} | `docs/STAGE22_2_OBSERVABLE_PERTURBATION_ROLLOUT.md` |
| 22.3 | {s22_3.get("result", "unknown")} | `docs/STAGE22_3_OBSERVABLE_ROBUSTNESS_ANALYSIS.md` |

结论：

    observable_perturbation_pass={observable_perturbation_pass}
    perturbation_metric_variability_detected={perturbation_metric_variability_detected}
    recommendation_relation_stable={recommendation_relation_stable}
    recommendation_observable_robust={recommendation_observable_robust}

    Stage 22 是一次 qvel observable perturbation attempt。
    由于扰动没有造成 summary 指标可观测变化，不支持 observable perturbation robustness 结论。
{END}
"""

    artifact_block = f"""{START}
## Stage 22 Artifacts

Stage 22 artifact 记录 qvel observable perturbation attempt。注意：Stage 22 的结果是 negative evidence，不支持 observable perturbation robustness claim。

结论边界：

  * `observable_perturbation_pass={observable_perturbation_pass}`
  * `perturbation_metric_variability_detected={perturbation_metric_variability_detected}`
  * `recommendation_relation_stable={recommendation_relation_stable}`
  * `recommendation_observable_robust={recommendation_observable_robust}`
  * 当前不将 `scale={recommended_scale}` 升级为 observable-perturbation-tested recommended candidate scale。

| 阶段 | Artifact | 作用 |
|---|---|---|
| 22.0 | `docs/STAGE22_OBSERVABLE_PERTURBATION_ROBUSTNESS_ROADMAP.md` | 可观测扰动审计路线图 |
| 22.1 | `docs/STAGE22_1_QVEL_PERTURBATION_PREFLIGHT.md` | qvel 扰动注入预检查 |
| 22.2 | `docs/STAGE22_2_OBSERVABLE_PERTURBATION_ROLLOUT.md` | 21 组 qvel perturbation rollout 报告 |
| 22.2 | `results/logs_sample/stage22_2_observable_perturbation_table.csv` | 21 组 rollout 汇总表 |
| 22.3 | `docs/STAGE22_3_OBSERVABLE_ROBUSTNESS_ANALYSIS.md` | 可观测扰动分析报告 |
| 22.3 | `results/logs_sample/stage22_3_observable_perturbation_variability.csv` | 扰动指标变化检查 |
| 22.3 | `results/logs_sample/stage22_3_observable_robustness_summary.json` | Stage 22.3 summary |
| 22.4 | `docs/STAGE22_4_OBSERVABLE_PERTURBATION_EVIDENCE_FREEZE.md` | Stage 22 证据冻结报告 |
| 22.4 | `results/logs_sample/stage22_4_observable_perturbation_evidence_manifest.json` | Stage 22 证据 manifest |
{END}
"""

    for p, block in [
        (readme, readme_block),
        (project_status, status_block),
        (artifact_index, artifact_block),
    ]:
        p.write_text(replace_marked_block(p.read_text(encoding="utf-8"), block), encoding="utf-8")

    validation_csv = logs / "stage22_4_observable_perturbation_evidence_freeze_validation.csv"
    hashes_csv = logs / "stage22_4_observable_perturbation_evidence_hashes.csv"
    manifest_json = logs / "stage22_4_observable_perturbation_evidence_manifest.json"
    summary_json = logs / "stage22_4_observable_perturbation_evidence_freeze_summary.json"
    freeze_doc = docs / "STAGE22_4_OBSERVABLE_PERTURBATION_EVIDENCE_FREEZE.md"

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail})

    for rel in required:
        path = root / rel
        check(f"required_exists::{rel}", path.is_file() and path.stat().st_size > 0, rel)

    for stage, path in [
        ("22.0", s22_0_path),
        ("22.1", s22_1_path),
        ("22.2", s22_2_path),
        ("22.3", s22_3_path),
    ]:
        data = load_json(path)
        check(f"summary_result_pass::{stage}", data.get("result") == "pass", f"result={data.get('result')}")

    check("observable_perturbation_pass_false_recorded", observable_perturbation_pass is False, str(observable_perturbation_pass))
    check("perturbation_metric_variability_false_recorded", perturbation_metric_variability_detected is False, str(perturbation_metric_variability_detected))
    check("recommendation_relation_stable_true_recorded", recommendation_relation_stable is True, str(recommendation_relation_stable))
    check("recommendation_observable_robust_false_recorded", recommendation_observable_robust is False, str(recommendation_observable_robust))

    for path in [readme, project_status, artifact_index]:
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(root))
        check(f"entry_has_stage22_marker::{path.name}", START in text and END in text, rel)
        check(f"entry_mentions_negative_result::{path.name}", "negative evidence" in text or "不能声明" in text or "不支持" in text, rel)
        check(f"entry_mentions_observable_false::{path.name}", "perturbation_metric_variability_detected=False" in text, rel)
        check(f"entry_mentions_recommendation_false::{path.name}", "recommendation_observable_robust=False" in text, rel)
        check(f"entry_mentions_no_real_robot::{path.name}", "真实机器人" in text or "real robot" in text, rel)

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
        "stage": "22.4",
        "name": "observable qvel perturbation evidence freeze",
        "result": result,
        "failure_count": failure_count,
        "artifact_count": len(manifest_items),
        "recommended_scale": recommended_scale,
        "baseline_scale": baseline_scale,
        "regression_anchor_scale": regression_scale,
        "observable_perturbation_pass": observable_perturbation_pass,
        "perturbation_metric_variability_detected": perturbation_metric_variability_detected,
        "recommendation_relation_stable": recommendation_relation_stable,
        "recommendation_observable_robust": recommendation_observable_robust,
        "conclusion": conclusion,
        "claim_support": claim_support,
        "artifacts": manifest_items,
        "claim_boundary": [
            "simulation-only qvel perturbation attempt",
            "negative evidence: no observable summary metric variability",
            "scale=0.010 is not upgraded to observable-perturbation-tested recommended candidate scale",
            "Stage 21 local-perturbation-tested recommendation remains the stronger supported wording",
            "no full MPC-WBC velocity controller claim",
            "no real robot torque execution claim",
            "no hardware torque enablement claim",
            "no terrain or external-force robustness claim",
        ],
    }

    manifest_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = {
        "stage": "22.4",
        "name": "observable qvel perturbation evidence freeze",
        "result": result,
        "failure_count": failure_count,
        "artifact_count": len(manifest_items),
        "observable_perturbation_pass": observable_perturbation_pass,
        "perturbation_metric_variability_detected": perturbation_metric_variability_detected,
        "recommendation_relation_stable": recommendation_relation_stable,
        "recommendation_observable_robust": recommendation_observable_robust,
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
        "claim_support": claim_support,
        "checks": checks,
    }
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    freeze_doc.write_text(f"""# Stage 22.4：observable qvel perturbation evidence freeze

## 1. 目标

Stage 22.4 冻结 Stage 22.0–22.3 的 qvel observable perturbation attempt 证据。

本阶段不新增控制器，不新增 rollout，只同步入口文档、生成 manifest，并冻结结论边界。

## 2. 阶段结果

| 阶段 | 结果 |
|---|---|
| 22.0 | {s22_0.get("result", "unknown")} |
| 22.1 | {s22_1.get("result", "unknown")} |
| 22.2 | {s22_2.get("result", "unknown")} |
| 22.3 | {s22_3.get("result", "unknown")} |

## 3. 核心结论

    observable_perturbation_pass: {observable_perturbation_pass}
    perturbation_metric_variability_detected: {perturbation_metric_variability_detected}
    recommendation_relation_stable: {recommendation_relation_stable}
    recommendation_observable_robust: {recommendation_observable_robust}

{conclusion}

{claim_support}

## 4. 当前证据支持

Stage 22 支持：

  * 完成 simulation-only qvel initial perturbation injection attempt；
  * 21 组 rollout 均通过稳定性边界；
  * `scale={recommended_scale}` 的推荐关系在当前记录指标中未被破坏；
  * 记录了 qvel 扰动未造成 summary 指标可观测变化这一 negative evidence。

## 5. 当前证据不支持

Stage 22 不支持：

  * 不支持 `scale={recommended_scale}` 升级为 observable-perturbation-tested recommended candidate scale；
  * 不支持 observable perturbation robustness claim；
  * 不支持完整 MPC-WBC 速度控制器已经完成；
  * 不支持 `scale={recommended_scale}` 可以直接用于真实机器人；
  * 不支持真实机器人 torque 执行或硬件 torque enablement 已完成；
  * 不支持复杂地形或外力冲击鲁棒性已完成。

## 6. 冻结结果

    stage22_4_result: {result}
    failure_count: {failure_count}
    artifact_count: {len(manifest_items)}
""", encoding="utf-8")

    print(f"stage22_4_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"observable_perturbation_pass: {observable_perturbation_pass}")
    print(f"perturbation_metric_variability_detected: {perturbation_metric_variability_detected}")
    print(f"recommendation_relation_stable: {recommendation_relation_stable}")
    print(f"recommendation_observable_robust: {recommendation_observable_robust}")
    print(f"manifest: {manifest_json.relative_to(root)}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"freeze_doc: {freeze_doc.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
