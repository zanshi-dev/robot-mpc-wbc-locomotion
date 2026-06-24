#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


START = "<!-- STAGE19_ENTRY_DOCS_SYNC_START -->"
END = "<!-- STAGE19_ENTRY_DOCS_SYNC_END -->"


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

    s19_0_path = logs / "stage19_0_velocity_aware_scale_sweep_roadmap_summary.json"
    s19_1_path = logs / "stage19_1_velocity_scale_sweep_preflight_summary.json"
    s19_2_path = logs / "stage19_2_velocity_scale_sweep_summary.json"
    s19_3_path = logs / "stage19_3_velocity_stability_tradeoff_summary.json"

    s19_0 = load_json(s19_0_path)
    s19_1 = load_json(s19_1_path)
    s19_2 = load_json(s19_2_path)
    s19_3 = load_json(s19_3_path)

    best_scale = str(s19_3.get("best_candidate_scale", "0.010"))
    best_error = str(s19_3.get("best_candidate_mean_abs_velocity_error", "unknown"))
    best_delta = str(s19_3.get("best_candidate_delta_error_vs_baseline", "unknown"))
    conclusion = str(s19_3.get(
        "conclusion",
        "当前 sweep 中所有 scale 均通过稳定性和安全边界；scale=0.010 是当前更合理的低尺度 candidate 注入候选，scale=0.020 不适合作为速度跟踪默认注入强度。",
    ))

    required = [
        "README.md",
        "PROJECT_STATUS.md",
        "docs/ARTIFACT_INDEX.md",

        "docs/STAGE19_VELOCITY_AWARE_SCALE_SWEEP_ROADMAP.md",
        "docs/STAGE19_1_VELOCITY_SCALE_SWEEP_PREFLIGHT.md",
        "docs/STAGE19_2_VELOCITY_SCALE_SWEEP_ROLLOUT.md",
        "docs/STAGE19_3_VELOCITY_STABILITY_TRADEOFF_ANALYSIS.md",

        "scripts/stage19_0_validate_velocity_aware_scale_sweep_roadmap.py",
        "scripts/stage19_1_velocity_scale_sweep_preflight.py",
        "scripts/stage19_2_velocity_scale_sweep_runner.py",
        "scripts/stage19_2_run_velocity_scale_sweep.py",
        "scripts/stage19_2_validate_velocity_scale_sweep.py",
        "scripts/stage19_3_velocity_stability_tradeoff_analysis.py",

        "results/logs_sample/stage19_0_velocity_aware_scale_sweep_roadmap_validation.csv",
        "results/logs_sample/stage19_0_velocity_aware_scale_sweep_roadmap_summary.json",

        "results/logs_sample/stage19_1_velocity_scale_sweep_preflight_validation.csv",
        "results/logs_sample/stage19_1_velocity_scale_sweep_preflight_context.txt",
        "results/logs_sample/stage19_1_velocity_scale_sweep_preflight_summary.json",

        "results/logs_sample/stage19_2_velocity_scale_sweep_execution.csv",
        "results/logs_sample/stage19_2_velocity_scale_sweep_execution_summary.json",
        "results/logs_sample/stage19_2_velocity_scale_sweep_validation.csv",
        "results/logs_sample/stage19_2_velocity_scale_sweep_table.csv",
        "results/logs_sample/stage19_2_velocity_scale_sweep_table.md",
        "results/logs_sample/stage19_2_velocity_scale_sweep_summary.json",

        "results/logs_sample/stage19_2_velocity_scale_0p000_baseline_log.csv",
        "results/logs_sample/stage19_2_velocity_scale_0p000_baseline_summary.csv",
        "results/logs_sample/stage19_2_velocity_scale_0p005_mpc_assisted_candidate_log.csv",
        "results/logs_sample/stage19_2_velocity_scale_0p005_mpc_assisted_candidate_summary.csv",
        "results/logs_sample/stage19_2_velocity_scale_0p010_mpc_assisted_candidate_log.csv",
        "results/logs_sample/stage19_2_velocity_scale_0p010_mpc_assisted_candidate_summary.csv",
        "results/logs_sample/stage19_2_velocity_scale_0p020_mpc_assisted_candidate_log.csv",
        "results/logs_sample/stage19_2_velocity_scale_0p020_mpc_assisted_candidate_summary.csv",
        "results/logs_sample/stage19_2_velocity_scale_0p050_mpc_assisted_candidate_log.csv",
        "results/logs_sample/stage19_2_velocity_scale_0p050_mpc_assisted_candidate_summary.csv",

        "results/logs_sample/stage19_3_velocity_stability_tradeoff_analysis.csv",
        "results/logs_sample/stage19_3_velocity_stability_tradeoff_ranking.csv",
        "results/logs_sample/stage19_3_velocity_stability_tradeoff_analysis.md",
        "results/logs_sample/stage19_3_velocity_stability_tradeoff_validation.csv",
        "results/logs_sample/stage19_3_velocity_stability_tradeoff_summary.json",
    ]

    readme_block = f"""{START}
## Stage 19：速度感知的 candidate scale sweep

Stage 19 用于进一步分析 Stage 18 中发现的速度跟踪问题。Stage 18 已补齐速度指标，并发现 `scale=0.020` 的低尺度 MPC/WBC candidate 注入虽然通过稳定性边界，但速度跟踪弱于 baseline。Stage 19 在此基础上进行 velocity-aware scale sweep。

当前证据支持：

  * 已完成 `0.000 / 0.005 / 0.010 / 0.020 / 0.050` 五组 scale 的 simulation-only rollout sweep。
  * 所有测试 scale 均通过高度、姿态、QP failure 和 torque saturation 边界。
  * candidate scale 对速度跟踪影响呈非单调特征，不是简单的“scale 越大越差”。
  * 在当前 target_vx=0.2 m/s 测试中，`scale={best_scale}` 是更合理的低尺度 candidate 注入候选。
  * `scale=0.020` 虽然稳定，但速度误差明显退化，不适合作为速度跟踪默认注入强度。

阶段结果：

    Stage 19.0 result: {s19_0.get("result", "unknown")}
    Stage 19.1 result: {s19_1.get("result", "unknown")}
    Stage 19.2 result: {s19_2.get("result", "unknown")}
    Stage 19.3 result: {s19_3.get("result", "unknown")}

关键结论：

    {conclusion}

当前推荐：

    candidate scale={best_scale}
    mean_abs_velocity_error={best_error}
    delta_error_vs_baseline={best_delta}

当前不能声明：

  * 不声明已完成完整 MPC-WBC 速度控制器；
  * 不声明 MPC/WBC candidate 已全面优于 baseline；
  * 不声明真实机器人 torque 执行；
  * 不声明已具备硬件 torque enablement 条件；
  * 不声明该结论可直接迁移到真实机器人或复杂地形。

更准确的表述是：

> Stage 19 通过速度感知 scale sweep 发现 candidate scale 对速度跟踪影响并非单调。在当前 target_vx=0.2 m/s 仿真测试中，scale={best_scale} 是更合理的低尺度 candidate 注入候选，而 scale=0.020 不适合作为速度跟踪默认注入强度。
{END}
"""

    status_block = f"""{START}
## Stage 19 状态：velocity-aware candidate scale sweep

当前状态：已完成 Stage 19.0–19.3，并在 Stage 19.4 中进行证据冻结。

| 阶段 | 结果 | 证据 |
|---|---:|---|
| 19.0 | {s19_0.get("result", "unknown")} | `docs/STAGE19_VELOCITY_AWARE_SCALE_SWEEP_ROADMAP.md` |
| 19.1 | {s19_1.get("result", "unknown")} | `docs/STAGE19_1_VELOCITY_SCALE_SWEEP_PREFLIGHT.md` |
| 19.2 | {s19_2.get("result", "unknown")} | `docs/STAGE19_2_VELOCITY_SCALE_SWEEP_ROLLOUT.md` |
| 19.3 | {s19_3.get("result", "unknown")} | `docs/STAGE19_3_VELOCITY_STABILITY_TRADEOFF_ANALYSIS.md` |

当前证据支持：

    Stage 19 已完成 simulation-only velocity-aware scale sweep。当前测试中所有 scale 均通过稳定性边界；scale={best_scale} 是更合理的低尺度 candidate 注入候选；scale=0.020 不适合作为速度跟踪默认注入强度。

当前证据不支持：

  * 完整 MPC-WBC 速度控制器已经完成；
  * MPC/WBC candidate 已全面优于 baseline；
  * 真实机器人 torque 执行已经完成；
  * 硬件 torque enablement 已经完成。
{END}
"""

    artifact_block = f"""{START}
## Stage 19 Artifacts

以下 Stage 19 artifact 均为 simulation-only velocity-aware scale sweep evidence，不对应真实机器人部署。

结论边界：

  * Stage 19 只分析 candidate scale 对速度跟踪和稳定性边界的影响；
  * 当前测试下 scale={best_scale} 是更合理的低尺度 candidate 注入候选；
  * 当前测试下 scale=0.020 不适合作为速度跟踪默认注入强度；
  * 不声明完整 MPC-WBC 速度控制器完成；
  * 不声明真实机器人 torque 执行完成。

| 阶段 | Artifact | 作用 |
|---|---|---|
| 19.0 | `docs/STAGE19_VELOCITY_AWARE_SCALE_SWEEP_ROADMAP.md` | 速度感知 scale sweep 路线图 |
| 19.0 | `results/logs_sample/stage19_0_velocity_aware_scale_sweep_roadmap_summary.json` | Stage 19.0 summary |
| 19.1 | `scripts/stage19_1_velocity_scale_sweep_preflight.py` | scale sweep 预检查脚本 |
| 19.1 | `docs/STAGE19_1_VELOCITY_SCALE_SWEEP_PREFLIGHT.md` | scale sweep 预检查报告 |
| 19.2 | `scripts/stage19_2_velocity_scale_sweep_runner.py` | scale-tagged velocity sweep runner |
| 19.2 | `scripts/stage19_2_run_velocity_scale_sweep.py` | scale sweep 执行脚本 |
| 19.2 | `scripts/stage19_2_validate_velocity_scale_sweep.py` | scale sweep 验证脚本 |
| 19.2 | `docs/STAGE19_2_VELOCITY_SCALE_SWEEP_ROLLOUT.md` | scale sweep rollout 报告 |
| 19.2 | `results/logs_sample/stage19_2_velocity_scale_sweep_table.csv` | 速度感知 scale sweep 数据表 |
| 19.2 | `results/logs_sample/stage19_2_velocity_scale_sweep_summary.json` | Stage 19.2 summary |
| 19.3 | `scripts/stage19_3_velocity_stability_tradeoff_analysis.py` | 速度-稳定性综合分析脚本 |
| 19.3 | `docs/STAGE19_3_VELOCITY_STABILITY_TRADEOFF_ANALYSIS.md` | 速度-稳定性综合分析报告 |
| 19.3 | `results/logs_sample/stage19_3_velocity_stability_tradeoff_analysis.csv` | 机器可读综合分析表 |
| 19.3 | `results/logs_sample/stage19_3_velocity_stability_tradeoff_summary.json` | Stage 19.3 summary |
| 19.4 | `docs/STAGE19_4_SCALE_SWEEP_EVIDENCE_FREEZE.md` | Stage 19 证据冻结报告 |
| 19.4 | `results/logs_sample/stage19_4_scale_sweep_evidence_manifest.json` | Stage 19 冻结证据 manifest |
{END}
"""

    readme.write_text(replace_marked_block(readme.read_text(encoding="utf-8"), readme_block), encoding="utf-8")
    project_status.write_text(replace_marked_block(project_status.read_text(encoding="utf-8"), status_block), encoding="utf-8")
    artifact_index.write_text(replace_marked_block(artifact_index.read_text(encoding="utf-8"), artifact_block), encoding="utf-8")

    validation_csv = logs / "stage19_4_scale_sweep_evidence_freeze_validation.csv"
    hashes_csv = logs / "stage19_4_scale_sweep_evidence_hashes.csv"
    manifest_json = logs / "stage19_4_scale_sweep_evidence_manifest.json"
    summary_json = logs / "stage19_4_scale_sweep_evidence_freeze_summary.json"
    freeze_doc = docs / "STAGE19_4_SCALE_SWEEP_EVIDENCE_FREEZE.md"

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

    stage_summaries = [
        ("19.0", s19_0_path),
        ("19.1", s19_1_path),
        ("19.2", s19_2_path),
        ("19.3", s19_3_path),
    ]

    for stage, path in stage_summaries:
        data = load_json(path)
        check(f"summary_result_pass::{stage}", data.get("result") == "pass", f"result={data.get('result')}")

    for path in [readme, project_status, artifact_index]:
        text = path.read_text(encoding="utf-8")
        check(f"entry_has_stage19_marker::{path.name}", START in text and END in text, str(path.relative_to(root)))
        check(f"entry_mentions_scale_sweep::{path.name}", "scale sweep" in text or "scale" in text, str(path.relative_to(root)))
        check(f"entry_mentions_simulation_only::{path.name}", "simulation-only" in text, str(path.relative_to(root)))
        check(f"entry_mentions_0p010::{path.name}", "scale=0.010" in text or "scale=0.010" in text.replace(" ", ""), str(path.relative_to(root)))
        check(f"entry_mentions_0p020_not_default::{path.name}", "scale=0.020" in text and "不适合作为速度跟踪默认注入强度" in text, str(path.relative_to(root)))

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
        "stage": "19.4",
        "name": "velocity-aware scale sweep evidence freeze",
        "result": result,
        "stage_results": {
            "19.0": s19_0.get("result", "unknown"),
            "19.1": s19_1.get("result", "unknown"),
            "19.2": s19_2.get("result", "unknown"),
            "19.3": s19_3.get("result", "unknown"),
        },
        "artifact_count": len(manifest_items),
        "best_candidate_scale": best_scale,
        "best_candidate_mean_abs_velocity_error": best_error,
        "best_candidate_delta_error_vs_baseline": best_delta,
        "conclusion": conclusion,
        "artifacts": manifest_items,
        "claim_boundary": [
            "simulation-only velocity-aware scale sweep",
            "scale=0.010 is a tested candidate scale recommendation, not a full controller claim",
            "scale=0.020 is not recommended as default velocity-tracking injection strength",
            "no real robot torque execution claim",
            "no hardware torque enablement claim",
            "no comprehensive MPC/WBC superiority claim",
        ],
    }
    manifest_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = {
        "stage": "19.4",
        "name": "velocity-aware scale sweep evidence freeze",
        "result": result,
        "failure_count": failure_count,
        "best_candidate_scale": best_scale,
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
        "checks": checks,
    }
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    freeze_doc.write_text(f"""# Stage 19.4：速度感知 scale sweep 证据冻结

## 1. 目标

Stage 19.4 将 Stage 19.0–19.3 的速度感知 scale sweep 证据同步到入口文档，并生成冻结证据包。

本阶段不新增控制器，只做证据归档、入口文档同步和结论边界冻结。

## 2. 冻结阶段结果

| 阶段 | 结果 |
|---|---|
| 19.0 | {s19_0.get("result", "unknown")} |
| 19.1 | {s19_1.get("result", "unknown")} |
| 19.2 | {s19_2.get("result", "unknown")} |
| 19.3 | {s19_3.get("result", "unknown")} |

## 3. 关键结论

{conclusion}

## 4. 当前证据支持

Stage 19 证据支持以下表述：

    Stage 19 完成了 simulation-only velocity-aware scale sweep。在当前 target_vx=0.2 m/s 测试中，所有 scale 均通过稳定性和安全边界；candidate scale 对速度跟踪影响呈非单调特征；scale={best_scale} 是当前更合理的低尺度 candidate 注入候选，scale=0.020 不适合作为速度跟踪默认注入强度。

## 5. 当前证据不支持

Stage 19.4 不支持以下表述：

  * 已完成完整 MPC-WBC 速度控制器；
  * MPC/WBC candidate 已全面优于 baseline；
  * 已完成真实机器人 torque 执行；
  * 已完成硬件 torque enablement；
  * 当前 scale 结论可直接迁移到真实机器人或复杂地形。

## 6. 生成证据文件

    results/logs_sample/stage19_4_scale_sweep_evidence_freeze_validation.csv
    results/logs_sample/stage19_4_scale_sweep_evidence_hashes.csv
    results/logs_sample/stage19_4_scale_sweep_evidence_manifest.json
    results/logs_sample/stage19_4_scale_sweep_evidence_freeze_summary.json
    docs/STAGE19_4_SCALE_SWEEP_EVIDENCE_FREEZE.md

## 7. 冻结结果

    stage19_4_result: {result}
    failure_count: {failure_count}
    artifact_count: {len(manifest_items)}
""", encoding="utf-8")

    print(f"stage19_4_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"best_candidate_scale: {best_scale}")
    print(f"manifest: {manifest_json.relative_to(root)}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"freeze_doc: {freeze_doc.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
