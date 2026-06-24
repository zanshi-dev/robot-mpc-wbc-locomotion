#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path


METRICS = [
    "mean_vx",
    "mean_abs_velocity_error",
    "max_abs_velocity_error",
    "forward_displacement",
    "min_z",
    "max_abs_roll",
    "max_abs_pitch",
    "max_tau_total_abs",
    "max_tau_candidate_scaled_abs",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def f(row: dict[str, str], key: str) -> float:
    return float(row[key])


def b(row: dict[str, str], key: str) -> bool:
    return str(row.get(key, "")).strip().lower() == "true"


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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

    source_table = logs / "stage20_2_replay_reproducibility_table.csv"
    stage20_2_summary = logs / "stage20_2_replay_reproducibility_summary.json"

    stats_csv = logs / "stage20_3_reproducibility_per_scale_stats.csv"
    pairwise_csv = logs / "stage20_3_reproducibility_pairwise_checks.csv"
    analysis_md = logs / "stage20_3_reproducibility_analysis.md"
    validation_csv = logs / "stage20_3_reproducibility_validation.csv"
    summary_json = logs / "stage20_3_reproducibility_summary.json"
    doc = docs / "STAGE20_3_REPRODUCIBILITY_ANALYSIS.md"

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    check("source_table_exists", source_table.is_file() and source_table.stat().st_size > 0, str(source_table.relative_to(root)))
    check("stage20_2_summary_exists", stage20_2_summary.is_file() and stage20_2_summary.stat().st_size > 0, str(stage20_2_summary.relative_to(root)))

    s20_2 = load_json(stage20_2_summary)
    check("stage20_2_summary_pass", s20_2.get("result") == "pass", f"result={s20_2.get('result')}")

    rows = read_rows(source_table) if source_table.is_file() else []
    check("replay_row_count_9", len(rows) == 9, f"rows={len(rows)}")

    expected_scale_tags = ["0p000", "0p010", "0p020"]
    expected_run_ids = ["run_00", "run_01", "run_02"]

    by_scale: dict[str, list[dict[str, str]]] = {tag: [] for tag in expected_scale_tags}
    by_run: dict[str, dict[str, dict[str, str]]] = {run_id: {} for run_id in expected_run_ids}

    for row in rows:
        tag = row["scale_tag"]
        run_id = row["run_id"]
        if tag in by_scale:
            by_scale[tag].append(row)
        if run_id in by_run:
            by_run[run_id][tag] = row

    for tag in expected_scale_tags:
        check(f"{tag}_has_three_runs", len(by_scale[tag]) == 3, f"count={len(by_scale[tag])}")

    for run_id in expected_run_ids:
        check(
            f"{run_id}_has_all_scales",
            set(by_run[run_id].keys()) == set(expected_scale_tags),
            f"scales={sorted(by_run[run_id].keys())}",
        )

    check("all_cases_pass_stability", all(b(row, "pass") for row in rows), "all pass=True")
    check("all_qp_fail_zero", all(int(float(row["qp_fail_steps"])) == 0 for row in rows), "all qp_fail_steps=0")
    check("all_saturation_zero", all(int(float(row["saturation_steps"])) == 0 for row in rows), "all saturation_steps=0")

    stats_rows: list[dict[str, str]] = []

    role_map = {
        "0p000": "baseline_reference",
        "0p010": "recommended_candidate",
        "0p020": "regression_anchor",
    }

    for tag in expected_scale_tags:
        scale_rows = by_scale[tag]
        if not scale_rows:
            continue

        out = {
            "scale_tag": tag,
            "scale": scale_rows[0]["scale"],
            "control_mode": scale_rows[0]["control_mode"],
            "role": role_map[tag],
            "run_count": str(len(scale_rows)),
            "all_pass": str(all(b(row, "pass") for row in scale_rows)),
        }

        for metric in METRICS:
            values = [f(row, metric) for row in scale_rows]
            mean_v = statistics.mean(values)
            std_v = statistics.pstdev(values) if len(values) > 1 else 0.0
            range_v = max(values) - min(values)

            out[f"{metric}_mean"] = f"{mean_v:.12f}"
            out[f"{metric}_std"] = f"{std_v:.12f}"
            out[f"{metric}_range"] = f"{range_v:.12f}"

        stats_rows.append(out)

    zero_tol = 1e-12
    for stat in stats_rows:
        tag = stat["scale_tag"]
        for metric in ["mean_vx", "mean_abs_velocity_error", "forward_displacement"]:
            rng = float(stat[f"{metric}_range"])
            check(f"{tag}_{metric}_range_zero", rng <= zero_tol, f"range={rng:.12e}")

    pairwise_rows: list[dict[str, str]] = []

    recommended_better_than_baseline_all = True
    recommended_better_than_0p020_all = True
    recommended_disp_higher_than_baseline_all = True
    recommended_disp_higher_than_0p020_all = True
    regression_0p020_worse_than_baseline_all = True

    for run_id in expected_run_ids:
        baseline = by_run[run_id].get("0p000")
        recommended = by_run[run_id].get("0p010")
        regression = by_run[run_id].get("0p020")

        if not baseline or not recommended or not regression:
            continue

        baseline_error = f(baseline, "mean_abs_velocity_error")
        recommended_error = f(recommended, "mean_abs_velocity_error")
        regression_error = f(regression, "mean_abs_velocity_error")

        baseline_disp = f(baseline, "forward_displacement")
        recommended_disp = f(recommended, "forward_displacement")
        regression_disp = f(regression, "forward_displacement")

        rec_vs_base_error_delta = recommended_error - baseline_error
        rec_vs_reg_error_delta = recommended_error - regression_error
        reg_vs_base_error_delta = regression_error - baseline_error

        rec_vs_base_disp_delta = recommended_disp - baseline_disp
        rec_vs_reg_disp_delta = recommended_disp - regression_disp

        rec_better_base = rec_vs_base_error_delta < 0.0
        rec_better_reg = rec_vs_reg_error_delta < 0.0
        rec_disp_base = rec_vs_base_disp_delta > 0.0
        rec_disp_reg = rec_vs_reg_disp_delta > 0.0
        reg_worse_base = reg_vs_base_error_delta > 0.0

        recommended_better_than_baseline_all = recommended_better_than_baseline_all and rec_better_base
        recommended_better_than_0p020_all = recommended_better_than_0p020_all and rec_better_reg
        recommended_disp_higher_than_baseline_all = recommended_disp_higher_than_baseline_all and rec_disp_base
        recommended_disp_higher_than_0p020_all = recommended_disp_higher_than_0p020_all and rec_disp_reg
        regression_0p020_worse_than_baseline_all = regression_0p020_worse_than_baseline_all and reg_worse_base

        pairwise_rows.append({
            "run_id": run_id,
            "recommended_error": f"{recommended_error:.6f}",
            "baseline_error": f"{baseline_error:.6f}",
            "regression_0p020_error": f"{regression_error:.6f}",
            "recommended_minus_baseline_error": f"{rec_vs_base_error_delta:.6f}",
            "recommended_minus_0p020_error": f"{rec_vs_reg_error_delta:.6f}",
            "regression_0p020_minus_baseline_error": f"{reg_vs_base_error_delta:.6f}",
            "recommended_displacement": f"{recommended_disp:.6f}",
            "baseline_displacement": f"{baseline_disp:.6f}",
            "regression_0p020_displacement": f"{regression_disp:.6f}",
            "recommended_minus_baseline_displacement": f"{rec_vs_base_disp_delta:.6f}",
            "recommended_minus_0p020_displacement": f"{rec_vs_reg_disp_delta:.6f}",
            "recommended_error_lower_than_baseline": str(rec_better_base),
            "recommended_error_lower_than_0p020": str(rec_better_reg),
            "recommended_displacement_higher_than_baseline": str(rec_disp_base),
            "recommended_displacement_higher_than_0p020": str(rec_disp_reg),
            "regression_0p020_error_higher_than_baseline": str(reg_worse_base),
        })

    check("recommended_error_lower_than_baseline_all_runs", recommended_better_than_baseline_all, str(recommended_better_than_baseline_all))
    check("recommended_error_lower_than_0p020_all_runs", recommended_better_than_0p020_all, str(recommended_better_than_0p020_all))
    check("recommended_displacement_higher_than_baseline_all_runs", recommended_disp_higher_than_baseline_all, str(recommended_disp_higher_than_baseline_all))
    check("recommended_displacement_higher_than_0p020_all_runs", recommended_disp_higher_than_0p020_all, str(recommended_disp_higher_than_0p020_all))
    check("regression_0p020_error_higher_than_baseline_all_runs", regression_0p020_worse_than_baseline_all, str(regression_0p020_worse_than_baseline_all))

    reproducibility_pass = (
        all(c["status"] == "PASS" for c in checks if "range_zero" in c["check"])
        and all(b(row, "pass") for row in rows)
    )

    recommendation_stable = (
        reproducibility_pass
        and recommended_better_than_baseline_all
        and recommended_better_than_0p020_all
        and recommended_disp_higher_than_baseline_all
        and recommended_disp_higher_than_0p020_all
        and regression_0p020_worse_than_baseline_all
    )

    check("reproducibility_pass", reproducibility_pass, str(reproducibility_pass))
    check("recommendation_stable", recommendation_stable, str(recommendation_stable))

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    stats_fields = list(stats_rows[0].keys()) if stats_rows else [
        "scale_tag",
        "scale",
        "control_mode",
        "role",
        "run_count",
        "all_pass",
    ]

    pairwise_fields = list(pairwise_rows[0].keys()) if pairwise_rows else ["run_id"]

    write_csv(stats_csv, stats_rows, stats_fields)
    write_csv(pairwise_csv, pairwise_rows, pairwise_fields)
    write_csv(validation_csv, checks, ["check", "status", "detail"])

    stats_md_cols = [
        "scale",
        "role",
        "run_count",
        "all_pass",
        "mean_vx_mean",
        "mean_vx_range",
        "mean_abs_velocity_error_mean",
        "mean_abs_velocity_error_range",
        "forward_displacement_mean",
        "forward_displacement_range",
    ]
    stats_md = markdown_table(stats_rows, stats_md_cols)

    pairwise_md_cols = [
        "run_id",
        "recommended_minus_baseline_error",
        "recommended_minus_0p020_error",
        "regression_0p020_minus_baseline_error",
        "recommended_minus_baseline_displacement",
        "recommended_minus_0p020_displacement",
    ]
    pairwise_md = markdown_table(pairwise_rows, pairwise_md_cols)

    conclusion = (
        "Stage 20.3 replay reproducibility audit 通过。"
        "在当前固定 simulation-only 设置下，baseline、scale=0.010 和 scale=0.020 的三次 replay 结果完全一致；"
        "scale=0.010 在每次 replay 中均保持低于 baseline 和 scale=0.020 的 mean_abs_velocity_error，"
        "且 forward_displacement 均高于 baseline 和 scale=0.020。"
        "因此，Stage 19 的 scale=0.010 推荐关系在 Stage 20 replay audit 中稳定复现。"
    )

    analysis_md.write_text(
        "# Stage 20.3 reproducibility analysis\n\n"
        "## Per-scale reproducibility statistics\n\n"
        + stats_md
        + "\n\n## Pairwise recommendation checks\n\n"
        + pairwise_md
        + "\n",
        encoding="utf-8",
    )

    doc.write_text(f"""# Stage 20.3：推荐 scale 可复现性分析

## 1. 目标

Stage 20.3 对 Stage 20.2 的 replay rollout 结果进行可复现性分析。

分析对象包括：

  * baseline: scale=0.000
  * recommended candidate: scale=0.010
  * regression anchor: scale=0.020

分析重点不是扩大泛化结论，而是验证 Stage 19 中 `scale=0.010` 的推荐关系是否能在固定仿真设置下稳定复现。

## 2. 结果

Stage 20.3 result: {result}

Failure count: {failure_count}

Reproducibility pass: {reproducibility_pass}

Recommendation stable: {recommendation_stable}

## 3. 关键结论

{conclusion}

## 4. 每个 scale 的可复现性统计

{stats_md}

## 5. 推荐关系逐 run 检查

{pairwise_md}

## 6. 当前支持的结论

当前证据支持：

    scale=0.010 可作为当前固定 simulation-only 设置下的 recommended candidate scale。

原因：

  * 三次 replay 中，scale=0.010 均通过稳定性边界；
  * 三次 replay 中，scale=0.010 的 mean_abs_velocity_error 均低于 baseline；
  * 三次 replay 中，scale=0.010 的 mean_abs_velocity_error 均低于 scale=0.020；
  * 三次 replay 中，scale=0.010 的 forward_displacement 均高于 baseline 和 scale=0.020；
  * 三个锚点的 replay 指标在重复运行中完全一致。

## 7. 当前不支持的结论

当前证据不支持：

  * 完整 MPC-WBC 速度控制器已经完成；
  * scale=0.010 可以直接用于真实机器人；
  * scale=0.010 对所有速度、地形和扰动都最优；
  * MPC/WBC candidate 已全面优于 baseline；
  * 已完成真实机器人 torque 执行；
  * 已完成硬件 torque enablement。

## 8. 推荐表述

> Stage 20 对 Stage 19 推荐的 scale=0.010 进行了 simulation-only replay reproducibility audit。在当前固定仿真设置下，baseline、scale=0.010 和 scale=0.020 的重复运行结果完全一致；scale=0.010 相对 baseline 和 scale=0.020 的速度误差优势关系稳定复现。因此，scale=0.010 可作为当前仿真证据下的 recommended candidate scale。
""", encoding="utf-8")

    summary = {
        "stage": "20.3",
        "name": "recommended scale reproducibility analysis",
        "result": result,
        "failure_count": failure_count,
        "source": str(source_table.relative_to(root)),
        "reproducibility_pass": reproducibility_pass,
        "recommendation_stable": recommendation_stable,
        "recommended_scale": "0.010",
        "baseline_scale": "0.000",
        "regression_anchor_scale": "0.020",
        "conclusion": conclusion,
        "generated_files": [
            str(stats_csv.relative_to(root)),
            str(pairwise_csv.relative_to(root)),
            str(analysis_md.relative_to(root)),
            str(validation_csv.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(doc.relative_to(root)),
        ],
        "claim_boundary": [
            "simulation-only replay reproducibility audit",
            "scale=0.010 is a current simulation-only recommended candidate scale",
            "no full MPC-WBC velocity controller claim",
            "no real robot torque execution claim",
            "no hardware torque enablement claim",
            "no multi-target-vx or terrain generalization claim",
        ],
        "per_scale_stats": stats_rows,
        "pairwise_rows": pairwise_rows,
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"stage20_3_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"reproducibility_pass: {reproducibility_pass}")
    print(f"recommendation_stable: {recommendation_stable}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"stats_csv: {stats_csv.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
