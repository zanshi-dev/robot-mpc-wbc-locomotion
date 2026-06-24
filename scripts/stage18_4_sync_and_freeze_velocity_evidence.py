#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


START = "<!-- STAGE18_ENTRY_DOCS_SYNC_START -->"
END = "<!-- STAGE18_ENTRY_DOCS_SYNC_END -->"


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

    stage_summaries = [
        "results/logs_sample/stage18_0_velocity_tracking_roadmap_summary.json",
        "results/logs_sample/stage18_1_velocity_source_inspection_summary.json",
        "results/logs_sample/stage18_2a_velocity_runner_patch_preflight_summary.json",
        "results/logs_sample/stage18_2_velocity_tracking_rollout_summary.json",
        "results/logs_sample/stage18_3_velocity_comparison_analysis_summary.json",
    ]

    required = [
        "README.md",
        "PROJECT_STATUS.md",
        "docs/ARTIFACT_INDEX.md",

        "docs/STAGE18_VELOCITY_TRACKING_ROADMAP.md",
        "docs/STAGE18_1_VELOCITY_SOURCE_INSPECTION.md",
        "docs/STAGE18_2A_VELOCITY_RUNNER_PATCH_PREFLIGHT.md",
        "docs/STAGE18_2_VELOCITY_TRACKING_ROLLOUT.md",
        "docs/STAGE18_3_VELOCITY_COMPARISON_ANALYSIS.md",

        "scripts/stage18_0_validate_velocity_tracking_roadmap.py",
        "scripts/stage18_1_velocity_source_inspection.py",
        "scripts/stage18_2a_velocity_runner_patch_preflight.py",
        "scripts/stage18_2_velocity_tracking_rollout_runner.py",
        "scripts/stage18_2_validate_velocity_tracking_rollout.py",
        "scripts/stage18_3_velocity_comparison_analysis.py",

        "results/logs_sample/stage18_0_velocity_tracking_roadmap_validation.csv",
        "results/logs_sample/stage18_0_velocity_tracking_roadmap_summary.json",

        "results/logs_sample/stage18_1_velocity_source_inspection.csv",
        "results/logs_sample/stage18_1_velocity_existing_csv_headers.csv",
        "results/logs_sample/stage18_1_velocity_source_anchor_report.txt",
        "results/logs_sample/stage18_1_velocity_source_inspection_validation.csv",
        "results/logs_sample/stage18_1_velocity_source_inspection_summary.json",

        "results/logs_sample/stage18_2a_velocity_runner_patch_preflight_context.txt",
        "results/logs_sample/stage18_2a_velocity_runner_patch_preflight_validation.csv",
        "results/logs_sample/stage18_2a_velocity_runner_patch_preflight_summary.json",

        "results/logs_sample/stage18_2_velocity_tracking_baseline_log.csv",
        "results/logs_sample/stage18_2_velocity_tracking_baseline_summary.csv",
        "results/logs_sample/stage18_2_velocity_tracking_mpc_assisted_candidate_log.csv",
        "results/logs_sample/stage18_2_velocity_tracking_mpc_assisted_candidate_summary.csv",
        "results/logs_sample/stage18_2_velocity_tracking_rollout_validation.csv",
        "results/logs_sample/stage18_2_velocity_tracking_rollout_comparison.csv",
        "results/logs_sample/stage18_2_velocity_tracking_rollout_summary.json",

        "results/logs_sample/stage18_3_velocity_comparison_analysis.csv",
        "results/logs_sample/stage18_3_velocity_comparison_analysis.md",
        "results/logs_sample/stage18_3_velocity_comparison_analysis_validation.csv",
        "results/logs_sample/stage18_3_velocity_comparison_analysis_summary.json",
    ]

    s18_0 = load_json(root / stage_summaries[0])
    s18_1 = load_json(root / stage_summaries[1])
    s18_2a = load_json(root / stage_summaries[2])
    s18_2 = load_json(root / stage_summaries[3])
    s18_3 = load_json(root / stage_summaries[4])

    comparison_rows = s18_2.get("comparison_rows", [])
    analysis_rows = s18_3.get("analysis_rows", [])

    conclusion_zh = (
        "Stage 18.2 的低尺度 MPC/WBC candidate 注入工况保持稳定，"
        "但不改善速度跟踪。在 target_vx=0.2 m/s 的当前测试中，"
        "baseline 的 mean_vx 更高、mean_abs_velocity_error 更低、forward_displacement 更大。"
    )

    readme_block = f"""{START}
## Stage 18：速度跟踪证据补齐

Stage 18 用于补齐 Stage 17 的主要边界：此前已有高度、姿态、QP failure 和 torque saturation 证据，但缺少速度跟踪指标。

当前证据支持：

  * 已在 simulation-only rollout 中新增 `base_x`、`base_y`、`base_vx_fd`、`target_vx`、`velocity_error`、`mean_vx`、`mean_abs_velocity_error` 和 `forward_displacement` 等速度相关指标。
  * 已完成 baseline 与低尺度 MPC/WBC candidate 注入工况的速度指标对照。
  * 已确认两组工况均通过高度、姿态、QP failure 和 torque saturation 安全边界。
  * 已明确当前低尺度 MPC/WBC candidate 不改善速度跟踪，baseline 速度跟踪优于 candidate。

阶段结果：

    Stage 18.0 result: {s18_0.get("result", "unknown")}
    Stage 18.1 result: {s18_1.get("result", "unknown")}
    Stage 18.2a result: {s18_2a.get("result", "unknown")}
    Stage 18.2 result: {s18_2.get("result", "unknown")}
    Stage 18.3 result: {s18_3.get("result", "unknown")}

关键结论：

    {conclusion_zh}

当前不能声明：

  * 不声明低尺度 MPC/WBC candidate 改善了速度跟踪；
  * 不声明已完成完整 MPC-WBC 速度控制器；
  * 不声明真实机器人 torque 执行；
  * 不声明已具备硬件 torque enablement 条件；
  * 不声明 MPC/WBC 已全面优于 baseline。

更准确的表述是：

> Stage 18 补齐了仅限仿真的速度跟踪证据。在当前 target_vx=0.2 m/s 测试中，baseline 与低尺度 MPC/WBC candidate 注入均通过稳定性和安全边界，但 baseline 的前向速度跟踪更好。
{END}
"""

    status_block = f"""{START}
## Stage 18 状态：速度跟踪证据补齐

当前状态：已完成 Stage 18.0–18.3，并在 Stage 18.4 中进行证据冻结。

| 阶段 | 结果 | 证据 |
|---|---:|---|
| 18.0 | {s18_0.get("result", "unknown")} | `docs/STAGE18_VELOCITY_TRACKING_ROADMAP.md` |
| 18.1 | {s18_1.get("result", "unknown")} | `docs/STAGE18_1_VELOCITY_SOURCE_INSPECTION.md` |
| 18.2a | {s18_2a.get("result", "unknown")} | `docs/STAGE18_2A_VELOCITY_RUNNER_PATCH_PREFLIGHT.md` |
| 18.2 | {s18_2.get("result", "unknown")} | `docs/STAGE18_2_VELOCITY_TRACKING_ROLLOUT.md` |
| 18.3 | {s18_3.get("result", "unknown")} | `docs/STAGE18_3_VELOCITY_COMPARISON_ANALYSIS.md` |

当前证据支持：

    Stage 18 已补齐 simulation-only velocity evidence。在当前 target_vx=0.2 m/s 测试中，baseline 与低尺度 MPC/WBC candidate 注入均通过稳定性和安全边界，但 baseline 的速度跟踪更好。

当前证据不支持：

  * 低尺度 MPC/WBC candidate 改善速度跟踪；
  * 完整 MPC-WBC 速度控制器已经完成；
  * 真实机器人 torque 执行已经完成；
  * 硬件 torque enablement 已经完成；
  * MPC/WBC 全面优于 baseline。
{END}
"""

    artifact_block = f"""{START}
## Stage 18 Artifacts

以下 Stage 18 artifact 均为 simulation-only velocity evidence，不对应真实机器人部署。

结论边界：

  * Stage 18 只补齐速度指标与对照证据；
  * 当前低尺度 MPC/WBC candidate 不改善速度跟踪；
  * 当前测试中 baseline 速度跟踪优于 candidate；
  * 不声明完整 MPC-WBC 速度控制器完成；
  * 不声明真实机器人 torque 执行完成。

| 阶段 | Artifact | 作用 |
|---|---|---|
| 18.0 | `docs/STAGE18_VELOCITY_TRACKING_ROADMAP.md` | 速度跟踪证据路线图与边界 |
| 18.0 | `results/logs_sample/stage18_0_velocity_tracking_roadmap_summary.json` | Stage 18.0 summary |
| 18.1 | `scripts/stage18_1_velocity_source_inspection.py` | 速度指标源脚本检查 |
| 18.1 | `docs/STAGE18_1_VELOCITY_SOURCE_INSPECTION.md` | source inspection 报告 |
| 18.2a | `scripts/stage18_2a_velocity_runner_patch_preflight.py` | runner patch 预检查 |
| 18.2a | `docs/STAGE18_2A_VELOCITY_RUNNER_PATCH_PREFLIGHT.md` | patch preflight 报告 |
| 18.2 | `scripts/stage18_2_velocity_tracking_rollout_runner.py` | 派生速度跟踪 rollout runner |
| 18.2 | `scripts/stage18_2_validate_velocity_tracking_rollout.py` | 速度 rollout 验证脚本 |
| 18.2 | `docs/STAGE18_2_VELOCITY_TRACKING_ROLLOUT.md` | 速度 rollout 报告 |
| 18.2 | `results/logs_sample/stage18_2_velocity_tracking_rollout_comparison.csv` | baseline / candidate 速度对照表 |
| 18.2 | `results/logs_sample/stage18_2_velocity_tracking_rollout_summary.json` | Stage 18.2 summary |
| 18.3 | `scripts/stage18_3_velocity_comparison_analysis.py` | 速度对照分析脚本 |
| 18.3 | `docs/STAGE18_3_VELOCITY_COMPARISON_ANALYSIS.md` | 速度对照分析报告 |
| 18.3 | `results/logs_sample/stage18_3_velocity_comparison_analysis.csv` | 机器可读速度对照分析 |
| 18.3 | `results/logs_sample/stage18_3_velocity_comparison_analysis_summary.json` | Stage 18.3 summary |
| 18.4 | `docs/STAGE18_4_VELOCITY_EVIDENCE_FREEZE.md` | Stage 18 速度证据冻结报告 |
| 18.4 | `results/logs_sample/stage18_4_velocity_evidence_manifest.json` | Stage 18 冻结证据 manifest |
{END}
"""

    readme_text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    status_text = project_status.read_text(encoding="utf-8") if project_status.is_file() else ""
    index_text = artifact_index.read_text(encoding="utf-8") if artifact_index.is_file() else ""

    readme.write_text(replace_marked_block(readme_text, readme_block), encoding="utf-8")
    project_status.write_text(replace_marked_block(status_text, status_block), encoding="utf-8")
    artifact_index.write_text(replace_marked_block(index_text, artifact_block), encoding="utf-8")

    freeze_doc = docs / "STAGE18_4_VELOCITY_EVIDENCE_FREEZE.md"
    validation_csv = logs / "stage18_4_velocity_evidence_freeze_validation.csv"
    hashes_csv = logs / "stage18_4_velocity_evidence_hashes.csv"
    manifest_json = logs / "stage18_4_velocity_evidence_manifest.json"
    summary_json = logs / "stage18_4_velocity_evidence_freeze_summary.json"

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

    for rel in stage_summaries:
        data = load_json(root / rel)
        check(f"summary_result_pass::{rel}", data.get("result") == "pass", f"result={data.get('result')}")

    not_better_terms = [
        "不改善速度跟踪",
        "baseline 速度跟踪优于 candidate",
        "baseline 的速度跟踪更好",
        "baseline 的前向速度跟踪更好",
    ]

    for path in [readme, project_status, artifact_index]:
        text = path.read_text(encoding="utf-8")
        check(f"entry_has_stage18_marker::{path.name}", START in text and END in text, str(path.relative_to(root)))
        check(f"entry_mentions_velocity::{path.name}", "速度" in text or "velocity" in text.lower(), str(path.relative_to(root)))
        check(f"entry_mentions_simulation_only::{path.name}", "simulation-only" in text, str(path.relative_to(root)))
        check(
            f"entry_mentions_candidate_not_better::{path.name}",
            any(term in text for term in not_better_terms),
            str(path.relative_to(root)),
        )

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
        "stage": "18.4",
        "name": "velocity evidence freeze",
        "result": result,
        "stage_results": {
            "18.0": s18_0.get("result", "unknown"),
            "18.1": s18_1.get("result", "unknown"),
            "18.2a": s18_2a.get("result", "unknown"),
            "18.2": s18_2.get("result", "unknown"),
            "18.3": s18_3.get("result", "unknown"),
        },
        "artifact_count": len(manifest_items),
        "artifacts": manifest_items,
        "comparison_rows": comparison_rows,
        "analysis_rows": analysis_rows,
        "conclusion": conclusion_zh,
        "claim_boundary": [
            "simulation-only velocity evidence",
            "finite-difference velocity from qpos[0]",
            "candidate remains stable but is not better on velocity tracking",
            "no real robot torque execution",
            "no hardware torque enablement",
            "no full MPC-WBC velocity controller claim",
            "no comprehensive MPC/WBC superiority claim",
        ],
    }
    manifest_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = {
        "stage": "18.4",
        "name": "velocity evidence freeze",
        "result": result,
        "failure_count": failure_count,
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
        "conclusion": conclusion_zh,
        "checks": checks,
    }
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    freeze_doc.write_text(f"""# Stage 18.4：速度跟踪证据冻结

## 1. 目标

Stage 18.4 将 Stage 18.0–18.3 的速度跟踪证据同步到入口文档，并生成冻结证据包。

本阶段不新增控制器，只做证据归档、入口文档同步和结论边界冻结。

## 2. 冻结阶段结果

| 阶段 | 结果 |
|---|---|
| 18.0 | {s18_0.get("result", "unknown")} |
| 18.1 | {s18_1.get("result", "unknown")} |
| 18.2a | {s18_2a.get("result", "unknown")} |
| 18.2 | {s18_2.get("result", "unknown")} |
| 18.3 | {s18_3.get("result", "unknown")} |

## 3. 关键结论

{conclusion_zh}

## 4. 当前证据支持

Stage 18 证据支持以下表述：

    Stage 18 补齐了 simulation-only velocity evidence。在当前 target_vx=0.2 m/s 测试中，baseline 与低尺度 MPC/WBC candidate 注入均通过稳定性和安全边界，但 baseline 速度跟踪优于 candidate。

## 5. 当前证据不支持

Stage 18.4 不支持以下表述：

  * 低尺度 MPC/WBC candidate 改善速度跟踪；
  * 已完成完整 MPC-WBC 速度控制器；
  * 已完成真实机器人 torque 执行；
  * 已完成硬件 torque enablement；
  * MPC/WBC 全面优于 baseline。

## 6. 生成证据文件

    results/logs_sample/stage18_4_velocity_evidence_freeze_validation.csv
    results/logs_sample/stage18_4_velocity_evidence_hashes.csv
    results/logs_sample/stage18_4_velocity_evidence_manifest.json
    results/logs_sample/stage18_4_velocity_evidence_freeze_summary.json
    docs/STAGE18_4_VELOCITY_EVIDENCE_FREEZE.md

## 7. 冻结结果

    stage18_4_result: {result}
    failure_count: {failure_count}
    artifact_count: {len(manifest_items)}
""", encoding="utf-8")

    print(f"stage18_4_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"manifest: {manifest_json.relative_to(root)}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"freeze_doc: {freeze_doc.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
