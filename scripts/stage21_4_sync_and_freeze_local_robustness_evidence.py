#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


START = "<!-- STAGE21_ENTRY_DOCS_SYNC_START -->"
END = "<!-- STAGE21_ENTRY_DOCS_SYNC_END -->"


PERTURBATION_IDS = [
    "nominal",
    "x_plus",
    "x_minus",
    "y_plus",
    "y_minus",
    "yaw_plus",
    "yaw_minus",
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


def replace_marked_block(text: str, block: str) -> str:
    if START in text and END in text:
        before = text.split(START)[0].rstrip()
        after = text.split(END, 1)[1].lstrip()
        return before + "\n\n" + block.rstrip() + "\n\n" + after
    return text.rstrip() + "\n\n" + block.rstrip() + "\n"


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
    docs.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    readme = root / "README.md"
    project_status = root / "PROJECT_STATUS.md"
    artifact_index = docs / "ARTIFACT_INDEX.md"

    s21_0_path = logs / "stage21_0_local_robustness_roadmap_summary.json"
    s21_1_path = logs / "stage21_1_local_perturbation_preflight_summary.json"
    s21_2_path = logs / "stage21_2_local_perturbation_summary.json"
    s21_3_path = logs / "stage21_3_local_robustness_summary.json"

    s21_0 = load_json(s21_0_path)
    s21_1 = load_json(s21_1_path)
    s21_2 = load_json(s21_2_path)
    s21_3 = load_json(s21_3_path)

    recommended_scale = str(s21_3.get("recommended_scale", "0.010"))
    baseline_scale = str(s21_3.get("baseline_scale", "0.000"))
    regression_scale = str(s21_3.get("regression_anchor_scale", "0.020"))

    local_robustness_pass = bool(s21_3.get("local_robustness_pass", False))
    recommendation_robust = bool(s21_3.get("recommendation_robust", False))
    perturbation_metric_variability_detected = bool(s21_3.get("perturbation_metric_variability_detected", False))

    conclusion = str(s21_3.get(
        "conclusion",
        "Stage 21.3 local robustness analysis 通过；scale=0.010 在当前小范围初始状态扰动工况下保持推荐关系。",
    ))
    perturbation_note = str(s21_3.get(
        "perturbation_note",
        "当前扰动设置下 summary 指标未出现可观测变化，因此不能扩展为广义扰动鲁棒性结论。",
    ))

    required = [
        "README.md",
        "PROJECT_STATUS.md",
        "docs/ARTIFACT_INDEX.md",

        "docs/STAGE21_RECOMMENDED_SCALE_LOCAL_ROBUSTNESS_ROADMAP.md",
        "docs/STAGE21_1_LOCAL_PERTURBATION_PREFLIGHT.md",
        "docs/STAGE21_2_LOCAL_PERTURBATION_ROLLOUT.md",
        "docs/STAGE21_3_LOCAL_ROBUSTNESS_ANALYSIS.md",

        "scripts/stage21_0_validate_local_robustness_roadmap.py",
        "scripts/stage21_1_local_perturbation_preflight.py",
        "scripts/stage21_2_local_perturbation_runner.py",
        "scripts/stage21_2_run_local_perturbation_rollouts.py",
        "scripts/stage21_2_validate_local_perturbation_rollouts.py",
        "scripts/stage21_3_local_robustness_analysis.py",

        "results/logs_sample/stage21_0_local_robustness_roadmap_validation.csv",
        "results/logs_sample/stage21_0_local_robustness_roadmap_summary.json",

        "results/logs_sample/stage21_1_local_perturbation_preflight_validation.csv",
        "results/logs_sample/stage21_1_local_perturbation_preflight_context.txt",
        "results/logs_sample/stage21_1_local_perturbation_output_plan.csv",
        "results/logs_sample/stage21_1_local_perturbation_preflight_summary.json",

        "results/logs_sample/stage21_2_local_perturbation_execution.csv",
        "results/logs_sample/stage21_2_local_perturbation_execution_summary.json",
        "results/logs_sample/stage21_2_local_perturbation_validation.csv",
        "results/logs_sample/stage21_2_local_perturbation_table.csv",
        "results/logs_sample/stage21_2_local_perturbation_table.md",
        "results/logs_sample/stage21_2_local_perturbation_summary.json",

        "results/logs_sample/stage21_3_local_robustness_per_perturbation_checks.csv",
        "results/logs_sample/stage21_3_local_robustness_per_scale_stats.csv",
        "results/logs_sample/stage21_3_local_robustness_analysis.md",
        "results/logs_sample/stage21_3_local_robustness_validation.csv",
        "results/logs_sample/stage21_3_local_robustness_summary.json",
    ]

    for pid in PERTURBATION_IDS:
        for _, tag, mode in SCALE_CASES:
            required += [
                f"results/logs_sample/stage21_2_local_perturb_{pid}_{tag}_{mode}_log.csv",
                f"results/logs_sample/stage21_2_local_perturb_{pid}_{tag}_{mode}_summary.csv",
            ]

    readme_block = f"""{START}
## Stage 21：推荐 candidate scale 局部扰动鲁棒性审计

Stage 21 在 Stage 20 推荐 `scale={recommended_scale}` 的基础上，进行了 simulation-only local perturbation robustness audit。

当前证据支持：

  * 已测试 7 个小范围初始状态扰动工况：nominal、x_plus、x_minus、y_plus、y_minus、yaw_plus、yaw_minus。
  * 每个扰动工况测试 3 个 scale anchor：baseline `scale={baseline_scale}`、recommended candidate `scale={recommended_scale}`、regression anchor `scale={regression_scale}`。
  * 共生成 21 组 simulation-only rollout evidence。
  * `scale={recommended_scale}` 在所有扰动工况中均通过稳定性边界。
  * `scale={recommended_scale}` 在所有扰动工况中均保持低于 baseline 和 `scale={regression_scale}` 的 mean_abs_velocity_error。
  * `scale={recommended_scale}` 在所有扰动工况中均保持高于 baseline 和 `scale={regression_scale}` 的 forward_displacement。
  * `local_robustness_pass={local_robustness_pass}`。
  * `recommendation_robust={recommendation_robust}`。

重要边界：

  * `perturbation_metric_variability_detected={perturbation_metric_variability_detected}`。
  * {perturbation_note}

阶段结果：

    Stage 21.0 result: {s21_0.get("result", "unknown")}
    Stage 21.1 result: {s21_1.get("result", "unknown")}
    Stage 21.2 result: {s21_2.get("result", "unknown")}
    Stage 21.3 result: {s21_3.get("result", "unknown")}

关键结论：

    {conclusion}

当前不能声明：

  * 不声明完整 MPC-WBC 速度控制器已经完成；
  * 不声明 `scale={recommended_scale}` 可以直接用于真实机器人；
  * 不声明 `scale={recommended_scale}` 对所有速度、地形、扰动和外力冲击都最优；
  * 不声明 MPC/WBC candidate 已全面优于 baseline；
  * 不声明真实机器人 torque 执行已经完成；
  * 不声明硬件 torque enablement 已经完成；
  * 不声明复杂地形或外力扰动鲁棒性已经完成。

更准确的表述是：

> Stage 21 对 Stage 20 推荐的 scale={recommended_scale} 进行了 simulation-only local perturbation robustness audit。在当前小范围初始状态扰动设置下，scale={recommended_scale} 均通过稳定性边界，并在所有扰动工况中保持低于 baseline 和 scale={regression_scale} 的速度误差。因此，scale={recommended_scale} 可作为当前仿真证据下的 local-perturbation-tested recommended candidate scale。
{END}
"""

    status_block = f"""{START}
## Stage 21 状态：recommended scale local robustness audit

当前状态：已完成 Stage 21.0–21.3，并在 Stage 21.4 中进行证据冻结。

| 阶段 | 结果 | 证据 |
|---|---:|---|
| 21.0 | {s21_0.get("result", "unknown")} | `docs/STAGE21_RECOMMENDED_SCALE_LOCAL_ROBUSTNESS_ROADMAP.md` |
| 21.1 | {s21_1.get("result", "unknown")} | `docs/STAGE21_1_LOCAL_PERTURBATION_PREFLIGHT.md` |
| 21.2 | {s21_2.get("result", "unknown")} | `docs/STAGE21_2_LOCAL_PERTURBATION_ROLLOUT.md` |
| 21.3 | {s21_3.get("result", "unknown")} | `docs/STAGE21_3_LOCAL_ROBUSTNESS_ANALYSIS.md` |

当前证据支持：

    Stage 21 已完成 simulation-only local perturbation robustness audit。
    在当前 7 个小范围初始状态扰动工况下，scale={recommended_scale} 均通过稳定性边界；
    scale={recommended_scale} 相对 baseline 和 scale={regression_scale} 的速度误差优势关系保持成立。

边界说明：

    perturbation_metric_variability_detected={perturbation_metric_variability_detected}
    {perturbation_note}

当前证据不支持：

  * 完整 MPC-WBC 速度控制器已经完成；
  * scale={recommended_scale} 可以直接用于真实机器人；
  * scale={recommended_scale} 对所有速度、地形、扰动和外力冲击都最优；
  * MPC/WBC candidate 已全面优于 baseline；
  * 真实机器人 torque 执行已经完成；
  * 硬件 torque enablement 已经完成。
{END}
"""

    artifact_block = f"""{START}
## Stage 21 Artifacts

以下 Stage 21 artifact 均为 simulation-only local perturbation robustness evidence，不对应真实机器人部署。

结论边界：

  * Stage 21 只审计 Stage 20 推荐的 `scale={recommended_scale}` 在小范围初始状态扰动下是否保持推荐关系；
  * 当前测试下 `scale={recommended_scale}` 可作为 simulation-only local-perturbation-tested recommended candidate scale；
  * 当前测试下 `scale={regression_scale}` 作为 regression anchor，速度误差退化关系仍保持；
  * `perturbation_metric_variability_detected={perturbation_metric_variability_detected}`，因此不声明广义扰动鲁棒性；
  * 不声明完整 MPC-WBC 速度控制器完成；
  * 不声明真实机器人 torque 执行完成；
  * 不声明硬件 torque enablement 完成。

| 阶段 | Artifact | 作用 |
|---|---|---|
| 21.0 | `docs/STAGE21_RECOMMENDED_SCALE_LOCAL_ROBUSTNESS_ROADMAP.md` | 局部扰动鲁棒性审计路线图 |
| 21.0 | `results/logs_sample/stage21_0_local_robustness_roadmap_summary.json` | Stage 21.0 summary |
| 21.1 | `scripts/stage21_1_local_perturbation_preflight.py` | 扰动注入预检查脚本 |
| 21.1 | `docs/STAGE21_1_LOCAL_PERTURBATION_PREFLIGHT.md` | 扰动注入预检查报告 |
| 21.2 | `scripts/stage21_2_local_perturbation_runner.py` | local perturbation runner |
| 21.2 | `scripts/stage21_2_run_local_perturbation_rollouts.py` | 21 组扰动 rollout 执行脚本 |
| 21.2 | `scripts/stage21_2_validate_local_perturbation_rollouts.py` | 21 组扰动 rollout 验证脚本 |
| 21.2 | `docs/STAGE21_2_LOCAL_PERTURBATION_ROLLOUT.md` | local perturbation rollout 报告 |
| 21.2 | `results/logs_sample/stage21_2_local_perturbation_table.csv` | 21 组扰动 rollout 结果表 |
| 21.2 | `results/logs_sample/stage21_2_local_perturbation_summary.json` | Stage 21.2 summary |
| 21.3 | `scripts/stage21_3_local_robustness_analysis.py` | 局部扰动鲁棒性分析脚本 |
| 21.3 | `docs/STAGE21_3_LOCAL_ROBUSTNESS_ANALYSIS.md` | 局部扰动鲁棒性分析报告 |
| 21.3 | `results/logs_sample/stage21_3_local_robustness_per_perturbation_checks.csv` | 每个扰动工况下的推荐关系检查 |
| 21.3 | `results/logs_sample/stage21_3_local_robustness_per_scale_stats.csv` | 每个 scale 的扰动统计 |
| 21.3 | `results/logs_sample/stage21_3_local_robustness_summary.json` | Stage 21.3 summary |
| 21.4 | `docs/STAGE21_4_LOCAL_ROBUSTNESS_EVIDENCE_FREEZE.md` | Stage 21 证据冻结报告 |
| 21.4 | `results/logs_sample/stage21_4_local_robustness_evidence_manifest.json` | Stage 21 冻结证据 manifest |
{END}
"""

    readme.write_text(replace_marked_block(readme.read_text(encoding="utf-8"), readme_block), encoding="utf-8")
    project_status.write_text(replace_marked_block(project_status.read_text(encoding="utf-8"), status_block), encoding="utf-8")
    artifact_index.write_text(replace_marked_block(artifact_index.read_text(encoding="utf-8"), artifact_block), encoding="utf-8")

    validation_csv = logs / "stage21_4_local_robustness_evidence_freeze_validation.csv"
    hashes_csv = logs / "stage21_4_local_robustness_evidence_hashes.csv"
    manifest_json = logs / "stage21_4_local_robustness_evidence_manifest.json"
    summary_json = logs / "stage21_4_local_robustness_evidence_freeze_summary.json"
    freeze_doc = docs / "STAGE21_4_LOCAL_ROBUSTNESS_EVIDENCE_FREEZE.md"

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
        ("21.0", s21_0_path),
        ("21.1", s21_1_path),
        ("21.2", s21_2_path),
        ("21.3", s21_3_path),
    ]:
        data = load_json(path)
        check(f"summary_result_pass::{stage}", data.get("result") == "pass", f"result={data.get('result')}")

    check("stage21_3_local_robustness_pass_true", local_robustness_pass is True, str(local_robustness_pass))
    check("stage21_3_recommendation_robust_true", recommendation_robust is True, str(recommendation_robust))
    check(
        "stage21_3_perturbation_metric_variability_recorded",
        "perturbation_metric_variability_detected" in s21_3,
        f"perturbation_metric_variability_detected={s21_3.get('perturbation_metric_variability_detected')}",
    )

    for path in [readme, project_status, artifact_index]:
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(root))
        check(f"entry_has_stage21_marker::{path.name}", START in text and END in text, rel)
        check(f"entry_mentions_local_robustness::{path.name}", "local" in text and ("robustness" in text or "鲁棒" in text), rel)
        check(f"entry_mentions_simulation_only::{path.name}", "simulation-only" in text, rel)
        check(f"entry_mentions_scale_0p010::{path.name}", "scale=0.010" in text, rel)
        check(f"entry_mentions_scale_0p020::{path.name}", "scale=0.020" in text, rel)
        check(f"entry_mentions_variability_boundary::{path.name}", "perturbation_metric_variability_detected" in text, rel)
        check(f"entry_mentions_no_real_robot::{path.name}", "真实机器人" in text or "real robot" in text, rel)

    hash_rows = []
    manifest_items = []
    for rel in required:
        path = root / rel
        exists = path.is_file()
        digest = sha256_file(path) if exists else ""
        size = path.stat().st_size if exists else 0
        hash_rows.append({
            "path": rel,
            "sha256": digest,
            "size_bytes": str(size),
        })
        manifest_items.append({
            "path": rel,
            "sha256": digest,
            "size_bytes": size,
            "exists": exists,
        })

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    write_csv(validation_csv, checks, ["check", "status", "detail"])
    write_csv(hashes_csv, hash_rows, ["path", "sha256", "size_bytes"])

    manifest = {
        "stage": "21.4",
        "name": "recommended scale local robustness evidence freeze",
        "result": result,
        "stage_results": {
            "21.0": s21_0.get("result", "unknown"),
            "21.1": s21_1.get("result", "unknown"),
            "21.2": s21_2.get("result", "unknown"),
            "21.3": s21_3.get("result", "unknown"),
        },
        "artifact_count": len(manifest_items),
        "recommended_scale": recommended_scale,
        "baseline_scale": baseline_scale,
        "regression_anchor_scale": regression_scale,
        "local_robustness_pass": local_robustness_pass,
        "recommendation_robust": recommendation_robust,
        "perturbation_metric_variability_detected": perturbation_metric_variability_detected,
        "conclusion": conclusion,
        "perturbation_note": perturbation_note,
        "artifacts": manifest_items,
        "claim_boundary": [
            "simulation-only local perturbation robustness audit",
            "small initial base_x/base_y/yaw perturbations only",
            "scale=0.010 is a current local-perturbation-tested recommended candidate scale",
            "perturbation_metric_variability_detected is recorded and must be considered in external claims",
            "no full MPC-WBC velocity controller claim",
            "no real robot torque execution claim",
            "no hardware torque enablement claim",
            "no terrain or external-force robustness claim",
        ],
    }
    manifest_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = {
        "stage": "21.4",
        "name": "recommended scale local robustness evidence freeze",
        "result": result,
        "failure_count": failure_count,
        "recommended_scale": recommended_scale,
        "local_robustness_pass": local_robustness_pass,
        "recommendation_robust": recommendation_robust,
        "perturbation_metric_variability_detected": perturbation_metric_variability_detected,
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
        "perturbation_note": perturbation_note,
        "checks": checks,
    }
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    freeze_doc.write_text(f"""# Stage 21.4：局部扰动鲁棒性证据冻结

## 1. 目标

Stage 21.4 将 Stage 21.0–21.3 的 recommended scale local robustness audit 证据同步到入口文档，并生成冻结证据包。

本阶段不新增控制器，只做证据归档、入口文档同步和结论边界冻结。

## 2. 冻结阶段结果

| 阶段 | 结果 |
|---|---|
| 21.0 | {s21_0.get("result", "unknown")} |
| 21.1 | {s21_1.get("result", "unknown")} |
| 21.2 | {s21_2.get("result", "unknown")} |
| 21.3 | {s21_3.get("result", "unknown")} |

## 3. 关键结论

{conclusion}

## 4. 扰动敏感性边界

    perturbation_metric_variability_detected: {perturbation_metric_variability_detected}

{perturbation_note}

这意味着 Stage 21 可以作为当前 runner 与当前扰动设置下的 local perturbation audit evidence，但不能扩展为广义扰动鲁棒性、复杂地形鲁棒性或外力冲击鲁棒性结论。

## 5. 当前证据支持

Stage 21 证据支持以下表述：

    Stage 21 对 Stage 20 推荐的 scale={recommended_scale} 进行了 simulation-only local perturbation robustness audit。
    在当前小范围初始状态扰动设置下，scale={recommended_scale} 均通过稳定性边界；
    scale={recommended_scale} 在所有扰动工况中保持低于 baseline 和 scale={regression_scale} 的速度误差。
    因此，scale={recommended_scale} 可作为当前仿真证据下的 local-perturbation-tested recommended candidate scale。

## 6. 当前证据不支持

Stage 21.4 不支持以下表述：

  * 已完成完整 MPC-WBC 速度控制器；
  * scale={recommended_scale} 可以直接用于真实机器人；
  * scale={recommended_scale} 对所有速度、地形、扰动和外力冲击都最优；
  * MPC/WBC candidate 已全面优于 baseline；
  * 已完成真实机器人 torque 执行；
  * 已完成硬件 torque enablement；
  * 已完成复杂地形鲁棒性验证；
  * 已完成外力冲击鲁棒性验证。

## 7. 生成证据文件

    results/logs_sample/stage21_4_local_robustness_evidence_freeze_validation.csv
    results/logs_sample/stage21_4_local_robustness_evidence_hashes.csv
    results/logs_sample/stage21_4_local_robustness_evidence_manifest.json
    results/logs_sample/stage21_4_local_robustness_evidence_freeze_summary.json
    docs/STAGE21_4_LOCAL_ROBUSTNESS_EVIDENCE_FREEZE.md

## 8. 冻结结果

    stage21_4_result: {result}
    failure_count: {failure_count}
    artifact_count: {len(manifest_items)}
    recommended_scale: {recommended_scale}
    local_robustness_pass: {local_robustness_pass}
    recommendation_robust: {recommendation_robust}
    perturbation_metric_variability_detected: {perturbation_metric_variability_detected}
""", encoding="utf-8")

    print(f"stage21_4_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"recommended_scale: {recommended_scale}")
    print(f"local_robustness_pass: {local_robustness_pass}")
    print(f"recommendation_robust: {recommendation_robust}")
    print(f"perturbation_metric_variability_detected: {perturbation_metric_variability_detected}")
    print(f"manifest: {manifest_json.relative_to(root)}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"freeze_doc: {freeze_doc.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
