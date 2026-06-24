#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


START = "<!-- STAGE20_ENTRY_DOCS_SYNC_START -->"
END = "<!-- STAGE20_ENTRY_DOCS_SYNC_END -->"


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

    s20_0_path = logs / "stage20_0_recommended_scale_reproducibility_roadmap_summary.json"
    s20_1_path = logs / "stage20_1_replay_reproducibility_preflight_summary.json"
    s20_2_path = logs / "stage20_2_replay_reproducibility_summary.json"
    s20_3_path = logs / "stage20_3_reproducibility_summary.json"

    s20_0 = load_json(s20_0_path)
    s20_1 = load_json(s20_1_path)
    s20_2 = load_json(s20_2_path)
    s20_3 = load_json(s20_3_path)

    recommended_scale = str(s20_3.get("recommended_scale", "0.010"))
    baseline_scale = str(s20_3.get("baseline_scale", "0.000"))
    regression_scale = str(s20_3.get("regression_anchor_scale", "0.020"))
    reproducibility_pass = bool(s20_3.get("reproducibility_pass", False))
    recommendation_stable = bool(s20_3.get("recommendation_stable", False))
    conclusion = str(s20_3.get(
        "conclusion",
        "Stage 20 replay reproducibility audit 通过；scale=0.010 的推荐关系在固定仿真设置下稳定复现。",
    ))

    stats = s20_3.get("per_scale_stats", [])
    rec_stats = next((x for x in stats if x.get("scale") == "0.010"), {})
    base_stats = next((x for x in stats if x.get("scale") == "0.000"), {})
    reg_stats = next((x for x in stats if x.get("scale") == "0.020"), {})

    rec_error = rec_stats.get("mean_abs_velocity_error_mean", "0.065265000000")
    base_error = base_stats.get("mean_abs_velocity_error_mean", "0.078494000000")
    reg_error = reg_stats.get("mean_abs_velocity_error_mean", "0.147469000000")

    rec_disp = rec_stats.get("forward_displacement_mean", "0.822437000000")
    base_disp = base_stats.get("forward_displacement_mean", "0.630505000000")
    reg_disp = reg_stats.get("forward_displacement_mean", "0.319838000000")

    required = [
        "README.md",
        "PROJECT_STATUS.md",
        "docs/ARTIFACT_INDEX.md",

        "docs/STAGE20_RECOMMENDED_SCALE_REPRODUCIBILITY_ROADMAP.md",
        "docs/STAGE20_1_REPLAY_REPRODUCIBILITY_PREFLIGHT.md",
        "docs/STAGE20_2_REPLAY_REPRODUCIBILITY_ROLLOUT.md",
        "docs/STAGE20_3_REPRODUCIBILITY_ANALYSIS.md",

        "scripts/stage20_0_validate_recommended_scale_reproducibility_roadmap.py",
        "scripts/stage20_1_replay_reproducibility_preflight.py",
        "scripts/stage20_2_replay_reproducibility_runner.py",
        "scripts/stage20_2_run_replay_reproducibility.py",
        "scripts/stage20_2_validate_replay_reproducibility.py",
        "scripts/stage20_3_reproducibility_analysis.py",

        "results/logs_sample/stage20_0_recommended_scale_reproducibility_roadmap_validation.csv",
        "results/logs_sample/stage20_0_recommended_scale_reproducibility_roadmap_summary.json",

        "results/logs_sample/stage20_1_replay_reproducibility_preflight_validation.csv",
        "results/logs_sample/stage20_1_replay_reproducibility_preflight_context.txt",
        "results/logs_sample/stage20_1_replay_reproducibility_output_plan.csv",
        "results/logs_sample/stage20_1_replay_reproducibility_preflight_summary.json",

        "results/logs_sample/stage20_2_replay_reproducibility_execution.csv",
        "results/logs_sample/stage20_2_replay_reproducibility_execution_summary.json",
        "results/logs_sample/stage20_2_replay_reproducibility_validation.csv",
        "results/logs_sample/stage20_2_replay_reproducibility_table.csv",
        "results/logs_sample/stage20_2_replay_reproducibility_table.md",
        "results/logs_sample/stage20_2_replay_reproducibility_summary.json",

        "results/logs_sample/stage20_3_reproducibility_per_scale_stats.csv",
        "results/logs_sample/stage20_3_reproducibility_pairwise_checks.csv",
        "results/logs_sample/stage20_3_reproducibility_analysis.md",
        "results/logs_sample/stage20_3_reproducibility_validation.csv",
        "results/logs_sample/stage20_3_reproducibility_summary.json",
    ]

    for run_id in ["run_00", "run_01", "run_02"]:
        required += [
            f"results/logs_sample/stage20_2_replay_{run_id}_0p000_baseline_log.csv",
            f"results/logs_sample/stage20_2_replay_{run_id}_0p000_baseline_summary.csv",
            f"results/logs_sample/stage20_2_replay_{run_id}_0p010_mpc_assisted_candidate_log.csv",
            f"results/logs_sample/stage20_2_replay_{run_id}_0p010_mpc_assisted_candidate_summary.csv",
            f"results/logs_sample/stage20_2_replay_{run_id}_0p020_mpc_assisted_candidate_log.csv",
            f"results/logs_sample/stage20_2_replay_{run_id}_0p020_mpc_assisted_candidate_summary.csv",
        ]

    readme_block = f"""{START}
## Stage 20：推荐 candidate scale 可复现性审计

Stage 20 用于审计 Stage 19 推荐的 `scale={recommended_scale}` 是否在固定仿真设置下可复现。该阶段不新增控制器，不修改 torque 执行链路，也不声明真实机器人部署。

当前证据支持：

  * 已对 `{baseline_scale}`、`{recommended_scale}`、`{regression_scale}` 三个锚点进行 replay reproducibility audit。
  * 每个锚点重复运行 3 次，共 9 组 simulation-only replay rollout。
  * 三个锚点的 replay 指标在重复运行中完全一致，`reproducibility_pass={reproducibility_pass}`。
  * `scale={recommended_scale}` 的推荐关系稳定复现，`recommendation_stable={recommendation_stable}`。
  * `scale={recommended_scale}` 的 mean_abs_velocity_error 低于 baseline 和 `scale={regression_scale}`。
  * `scale={recommended_scale}` 的 forward_displacement 高于 baseline 和 `scale={regression_scale}`。

关键数据：

    baseline scale={baseline_scale}, mean_abs_velocity_error={base_error}, forward_displacement={base_disp}
    recommended scale={recommended_scale}, mean_abs_velocity_error={rec_error}, forward_displacement={rec_disp}
    regression anchor scale={regression_scale}, mean_abs_velocity_error={reg_error}, forward_displacement={reg_disp}

阶段结果：

    Stage 20.0 result: {s20_0.get("result", "unknown")}
    Stage 20.1 result: {s20_1.get("result", "unknown")}
    Stage 20.2 result: {s20_2.get("result", "unknown")}
    Stage 20.3 result: {s20_3.get("result", "unknown")}

关键结论：

    {conclusion}

当前不能声明：

  * 不声明完整 MPC-WBC 速度控制器已经完成；
  * 不声明 `scale={recommended_scale}` 可以直接用于真实机器人；
  * 不声明 `scale={recommended_scale}` 对所有速度、地形和扰动都最优；
  * 不声明 MPC/WBC candidate 已全面优于 baseline；
  * 不声明真实机器人 torque 执行已经完成；
  * 不声明硬件 torque enablement 已经完成。

更准确的表述是：

> Stage 20 对 Stage 19 推荐的 scale={recommended_scale} 进行了 simulation-only replay reproducibility audit。在当前固定仿真设置下，baseline、scale={recommended_scale} 和 scale={regression_scale} 的重复运行结果完全一致；scale={recommended_scale} 相对 baseline 和 scale={regression_scale} 的速度误差优势关系稳定复现。因此，scale={recommended_scale} 可作为当前仿真证据下的 recommended candidate scale。
{END}
"""

    status_block = f"""{START}
## Stage 20 状态：recommended scale reproducibility audit

当前状态：已完成 Stage 20.0–20.3，并在 Stage 20.4 中进行证据冻结。

| 阶段 | 结果 | 证据 |
|---|---:|---|
| 20.0 | {s20_0.get("result", "unknown")} | `docs/STAGE20_RECOMMENDED_SCALE_REPRODUCIBILITY_ROADMAP.md` |
| 20.1 | {s20_1.get("result", "unknown")} | `docs/STAGE20_1_REPLAY_REPRODUCIBILITY_PREFLIGHT.md` |
| 20.2 | {s20_2.get("result", "unknown")} | `docs/STAGE20_2_REPLAY_REPRODUCIBILITY_ROLLOUT.md` |
| 20.3 | {s20_3.get("result", "unknown")} | `docs/STAGE20_3_REPRODUCIBILITY_ANALYSIS.md` |

当前证据支持：

    Stage 20 已完成 simulation-only replay reproducibility audit。
    在当前固定仿真设置下，baseline、scale={recommended_scale} 和 scale={regression_scale} 的三次 replay 结果完全一致；
    scale={recommended_scale} 相对 baseline 和 scale={regression_scale} 的速度误差优势关系稳定复现。

当前证据不支持：

  * 完整 MPC-WBC 速度控制器已经完成；
  * scale={recommended_scale} 可以直接用于真实机器人；
  * scale={recommended_scale} 对所有速度、地形和扰动都最优；
  * MPC/WBC candidate 已全面优于 baseline；
  * 真实机器人 torque 执行已经完成；
  * 硬件 torque enablement 已经完成。
{END}
"""

    artifact_block = f"""{START}
## Stage 20 Artifacts

以下 Stage 20 artifact 均为 simulation-only replay reproducibility evidence，不对应真实机器人部署。

结论边界：

  * Stage 20 只审计 Stage 19 推荐的 `scale={recommended_scale}` 在固定仿真设置下是否可复现；
  * 当前测试下 `scale={recommended_scale}` 可作为 simulation-only recommended candidate scale；
  * 当前测试下 `scale={regression_scale}` 作为 regression anchor，速度误差退化关系稳定复现；
  * 不声明完整 MPC-WBC 速度控制器完成；
  * 不声明真实机器人 torque 执行完成；
  * 不声明硬件 torque enablement 完成。

| 阶段 | Artifact | 作用 |
|---|---|---|
| 20.0 | `docs/STAGE20_RECOMMENDED_SCALE_REPRODUCIBILITY_ROADMAP.md` | 推荐 scale 可复现性审计路线图 |
| 20.0 | `results/logs_sample/stage20_0_recommended_scale_reproducibility_roadmap_summary.json` | Stage 20.0 summary |
| 20.1 | `scripts/stage20_1_replay_reproducibility_preflight.py` | replay preflight 脚本 |
| 20.1 | `docs/STAGE20_1_REPLAY_REPRODUCIBILITY_PREFLIGHT.md` | replay preflight 报告 |
| 20.2 | `scripts/stage20_2_replay_reproducibility_runner.py` | replay-specific runner |
| 20.2 | `scripts/stage20_2_run_replay_reproducibility.py` | replay 执行脚本 |
| 20.2 | `scripts/stage20_2_validate_replay_reproducibility.py` | replay 验证脚本 |
| 20.2 | `docs/STAGE20_2_REPLAY_REPRODUCIBILITY_ROLLOUT.md` | replay rollout 报告 |
| 20.2 | `results/logs_sample/stage20_2_replay_reproducibility_table.csv` | replay 结果数据表 |
| 20.2 | `results/logs_sample/stage20_2_replay_reproducibility_summary.json` | Stage 20.2 summary |
| 20.3 | `scripts/stage20_3_reproducibility_analysis.py` | 可复现性分析脚本 |
| 20.3 | `docs/STAGE20_3_REPRODUCIBILITY_ANALYSIS.md` | 可复现性分析报告 |
| 20.3 | `results/logs_sample/stage20_3_reproducibility_per_scale_stats.csv` | 每个 scale 的可复现性统计 |
| 20.3 | `results/logs_sample/stage20_3_reproducibility_pairwise_checks.csv` | 推荐关系逐 run 检查 |
| 20.3 | `results/logs_sample/stage20_3_reproducibility_summary.json` | Stage 20.3 summary |
| 20.4 | `docs/STAGE20_4_REPRODUCIBILITY_EVIDENCE_FREEZE.md` | Stage 20 证据冻结报告 |
| 20.4 | `results/logs_sample/stage20_4_reproducibility_evidence_manifest.json` | Stage 20 冻结证据 manifest |
{END}
"""

    readme.write_text(replace_marked_block(readme.read_text(encoding="utf-8"), readme_block), encoding="utf-8")
    project_status.write_text(replace_marked_block(project_status.read_text(encoding="utf-8"), status_block), encoding="utf-8")
    artifact_index.write_text(replace_marked_block(artifact_index.read_text(encoding="utf-8"), artifact_block), encoding="utf-8")

    validation_csv = logs / "stage20_4_reproducibility_evidence_freeze_validation.csv"
    hashes_csv = logs / "stage20_4_reproducibility_evidence_hashes.csv"
    manifest_json = logs / "stage20_4_reproducibility_evidence_manifest.json"
    summary_json = logs / "stage20_4_reproducibility_evidence_freeze_summary.json"
    freeze_doc = docs / "STAGE20_4_REPRODUCIBILITY_EVIDENCE_FREEZE.md"

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
        ("20.0", s20_0_path),
        ("20.1", s20_1_path),
        ("20.2", s20_2_path),
        ("20.3", s20_3_path),
    ]:
        data = load_json(path)
        check(f"summary_result_pass::{stage}", data.get("result") == "pass", f"result={data.get('result')}")

    check("stage20_3_reproducibility_pass_true", reproducibility_pass is True, str(reproducibility_pass))
    check("stage20_3_recommendation_stable_true", recommendation_stable is True, str(recommendation_stable))

    for path in [readme, project_status, artifact_index]:
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(root))
        check(f"entry_has_stage20_marker::{path.name}", START in text and END in text, rel)
        check(f"entry_mentions_reproducibility::{path.name}", "reproducibility" in text or "可复现" in text, rel)
        check(f"entry_mentions_simulation_only::{path.name}", "simulation-only" in text, rel)
        check(f"entry_mentions_scale_0p010::{path.name}", "scale=0.010" in text, rel)
        check(f"entry_mentions_scale_0p020::{path.name}", "scale=0.020" in text, rel)
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
        "stage": "20.4",
        "name": "recommended scale reproducibility evidence freeze",
        "result": result,
        "stage_results": {
            "20.0": s20_0.get("result", "unknown"),
            "20.1": s20_1.get("result", "unknown"),
            "20.2": s20_2.get("result", "unknown"),
            "20.3": s20_3.get("result", "unknown"),
        },
        "artifact_count": len(manifest_items),
        "recommended_scale": recommended_scale,
        "baseline_scale": baseline_scale,
        "regression_anchor_scale": regression_scale,
        "reproducibility_pass": reproducibility_pass,
        "recommendation_stable": recommendation_stable,
        "conclusion": conclusion,
        "artifacts": manifest_items,
        "claim_boundary": [
            "simulation-only replay reproducibility audit",
            "scale=0.010 is a current simulation-only recommended candidate scale",
            "no full MPC-WBC velocity controller claim",
            "no real robot torque execution claim",
            "no hardware torque enablement claim",
            "no multi-target-vx or terrain generalization claim",
        ],
    }
    manifest_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = {
        "stage": "20.4",
        "name": "recommended scale reproducibility evidence freeze",
        "result": result,
        "failure_count": failure_count,
        "recommended_scale": recommended_scale,
        "reproducibility_pass": reproducibility_pass,
        "recommendation_stable": recommendation_stable,
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

    freeze_doc.write_text(f"""# Stage 20.4：推荐 scale 可复现性证据冻结

## 1. 目标

Stage 20.4 将 Stage 20.0–20.3 的 recommended scale reproducibility audit 证据同步到入口文档，并生成冻结证据包。

本阶段不新增控制器，只做证据归档、入口文档同步和结论边界冻结。

## 2. 冻结阶段结果

| 阶段 | 结果 |
|---|---|
| 20.0 | {s20_0.get("result", "unknown")} |
| 20.1 | {s20_1.get("result", "unknown")} |
| 20.2 | {s20_2.get("result", "unknown")} |
| 20.3 | {s20_3.get("result", "unknown")} |

## 3. 关键结论

{conclusion}

## 4. 当前证据支持

Stage 20 证据支持以下表述：

    Stage 20 对 Stage 19 推荐的 scale={recommended_scale} 进行了 simulation-only replay reproducibility audit。
    在当前固定仿真设置下，baseline、scale={recommended_scale} 和 scale={regression_scale} 的三次 replay 结果完全一致；
    scale={recommended_scale} 相对 baseline 和 scale={regression_scale} 的速度误差优势关系稳定复现。
    因此，scale={recommended_scale} 可作为当前仿真证据下的 recommended candidate scale。

## 5. 当前证据不支持

Stage 20.4 不支持以下表述：

  * 已完成完整 MPC-WBC 速度控制器；
  * scale={recommended_scale} 可以直接用于真实机器人；
  * scale={recommended_scale} 对所有速度、地形和扰动都最优；
  * MPC/WBC candidate 已全面优于 baseline；
  * 已完成真实机器人 torque 执行；
  * 已完成硬件 torque enablement；
  * 已完成多 target_vx 或复杂地形泛化验证。

## 6. 生成证据文件

    results/logs_sample/stage20_4_reproducibility_evidence_freeze_validation.csv
    results/logs_sample/stage20_4_reproducibility_evidence_hashes.csv
    results/logs_sample/stage20_4_reproducibility_evidence_manifest.json
    results/logs_sample/stage20_4_reproducibility_evidence_freeze_summary.json
    docs/STAGE20_4_REPRODUCIBILITY_EVIDENCE_FREEZE.md

## 7. 冻结结果

    stage20_4_result: {result}
    failure_count: {failure_count}
    artifact_count: {len(manifest_items)}
    recommended_scale: {recommended_scale}
    reproducibility_pass: {reproducibility_pass}
    recommendation_stable: {recommendation_stable}
""", encoding="utf-8")

    print(f"stage20_4_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"recommended_scale: {recommended_scale}")
    print(f"reproducibility_pass: {reproducibility_pass}")
    print(f"recommendation_stable: {recommendation_stable}")
    print(f"manifest: {manifest_json.relative_to(root)}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"freeze_doc: {freeze_doc.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
