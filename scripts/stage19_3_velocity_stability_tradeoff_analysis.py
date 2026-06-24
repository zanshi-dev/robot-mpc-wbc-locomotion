#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


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

    source_table = logs / "stage19_2_velocity_scale_sweep_table.csv"
    stage19_2_summary = logs / "stage19_2_velocity_scale_sweep_summary.json"

    analysis_csv = logs / "stage19_3_velocity_stability_tradeoff_analysis.csv"
    ranking_csv = logs / "stage19_3_velocity_stability_tradeoff_ranking.csv"
    analysis_md = logs / "stage19_3_velocity_stability_tradeoff_analysis.md"
    validation_csv = logs / "stage19_3_velocity_stability_tradeoff_validation.csv"
    summary_json = logs / "stage19_3_velocity_stability_tradeoff_summary.json"
    doc = docs / "STAGE19_3_VELOCITY_STABILITY_TRADEOFF_ANALYSIS.md"

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    check("source_table_exists", source_table.is_file() and source_table.stat().st_size > 0, str(source_table.relative_to(root)))
    check("stage19_2_summary_exists", stage19_2_summary.is_file() and stage19_2_summary.stat().st_size > 0, str(stage19_2_summary.relative_to(root)))

    rows = read_rows(source_table) if source_table.is_file() else []
    by_scale = {row["scale"]: row for row in rows}

    expected_scales = ["0.000", "0.005", "0.010", "0.020", "0.050"]
    check("expected_scale_count", len(rows) == len(expected_scales), f"rows={len(rows)}")
    check("expected_scales_present", list(by_scale.keys()) == expected_scales, f"scales={list(by_scale.keys())}")

    baseline = by_scale.get("0.000")

    analysis_rows: list[dict[str, str]] = []
    stable_rows: list[dict[str, str]] = []

    if baseline:
        baseline_error = f(baseline, "mean_abs_velocity_error")
        baseline_mean_vx = f(baseline, "mean_vx")
        baseline_disp = f(baseline, "forward_displacement")

        for row in rows:
            scale = row["scale"]
            mean_vx = f(row, "mean_vx")
            error = f(row, "mean_abs_velocity_error")
            disp = f(row, "forward_displacement")
            min_z = f(row, "min_z")
            max_roll = f(row, "max_abs_roll")
            max_pitch = f(row, "max_abs_pitch")
            qp_fail = int(float(row["qp_fail_steps"]))
            saturation = int(float(row["saturation_steps"]))
            passed = b(row, "pass")

            delta_error = error - baseline_error
            delta_mean_vx = mean_vx - baseline_mean_vx
            delta_disp = disp - baseline_disp

            if not passed:
                recommendation = "not_recommended_unstable"
            elif scale == "0.000":
                recommendation = "baseline_reference"
            elif delta_error < 0:
                recommendation = "recommended_candidate"
            elif scale == "0.020":
                recommendation = "not_recommended_velocity_regression"
            else:
                recommendation = "stable_but_not_best"

            analysis_row = {
                "scale": scale,
                "scale_tag": row["scale_tag"],
                "control_mode": row["control_mode"],
                "pass": row["pass"],
                "mean_vx": f"{mean_vx:.6f}",
                "mean_abs_velocity_error": f"{error:.6f}",
                "forward_displacement": f"{disp:.6f}",
                "delta_error_vs_baseline": f"{delta_error:.6f}",
                "delta_mean_vx_vs_baseline": f"{delta_mean_vx:.6f}",
                "delta_displacement_vs_baseline": f"{delta_disp:.6f}",
                "min_z": f"{min_z:.6f}",
                "max_abs_roll": f"{max_roll:.6f}",
                "max_abs_pitch": f"{max_pitch:.6f}",
                "qp_fail_steps": str(qp_fail),
                "saturation_steps": str(saturation),
                "recommendation": recommendation,
            }
            analysis_rows.append(analysis_row)
            if passed:
                stable_rows.append(analysis_row)

        candidate_rows = [r for r in analysis_rows if r["scale"] != "0.000" and r["pass"] == "True"]
        best_candidate = min(candidate_rows, key=lambda r: float(r["mean_abs_velocity_error"])) if candidate_rows else None
        worst_candidate = max(candidate_rows, key=lambda r: float(r["mean_abs_velocity_error"])) if candidate_rows else None

        candidate_errors = [float(r["mean_abs_velocity_error"]) for r in candidate_rows]
        non_monotonic = False
        if len(candidate_errors) >= 3:
            # A monotonic increasing sequence would have every next error >= previous error.
            # A monotonic decreasing sequence would have every next error <= previous error.
            inc = all(candidate_errors[i + 1] >= candidate_errors[i] for i in range(len(candidate_errors) - 1))
            dec = all(candidate_errors[i + 1] <= candidate_errors[i] for i in range(len(candidate_errors) - 1))
            non_monotonic = not (inc or dec)

        check("all_cases_stability_pass", all(r["pass"] == "True" for r in analysis_rows), "all pass=True")
        check("best_candidate_exists", best_candidate is not None, str(best_candidate["scale"] if best_candidate else None))
        check("best_candidate_is_0p010", best_candidate is not None and best_candidate["scale"] == "0.010", str(best_candidate["scale"] if best_candidate else None))
        check("best_candidate_error_below_baseline", best_candidate is not None and float(best_candidate["delta_error_vs_baseline"]) < 0.0, str(best_candidate["delta_error_vs_baseline"] if best_candidate else None))
        check("scale_0p020_is_velocity_regression", by_scale.get("0.020") is not None and f(by_scale["0.020"], "mean_abs_velocity_error") > baseline_error, f"0p020_error={f(by_scale['0.020'], 'mean_abs_velocity_error') if '0.020' in by_scale else None}")
        check("candidate_error_non_monotonic", non_monotonic, f"errors={candidate_errors}")

    else:
        best_candidate = None
        worst_candidate = None
        non_monotonic = False
        check("baseline_row_exists", False, "scale=0.000 missing")

    ranking_rows = sorted(
        analysis_rows,
        key=lambda r: (
            r["pass"] != "True",
            float(r["mean_abs_velocity_error"]),
            -float(r["forward_displacement"]),
        ),
    )

    ranking_out = []
    for idx, row in enumerate(ranking_rows, start=1):
        ranking_out.append({
            "rank": str(idx),
            "scale": row["scale"],
            "mean_abs_velocity_error": row["mean_abs_velocity_error"],
            "mean_vx": row["mean_vx"],
            "forward_displacement": row["forward_displacement"],
            "pass": row["pass"],
            "recommendation": row["recommendation"],
        })

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    analysis_fields = [
        "scale",
        "scale_tag",
        "control_mode",
        "pass",
        "mean_vx",
        "mean_abs_velocity_error",
        "forward_displacement",
        "delta_error_vs_baseline",
        "delta_mean_vx_vs_baseline",
        "delta_displacement_vs_baseline",
        "min_z",
        "max_abs_roll",
        "max_abs_pitch",
        "qp_fail_steps",
        "saturation_steps",
        "recommendation",
    ]

    ranking_fields = [
        "rank",
        "scale",
        "mean_abs_velocity_error",
        "mean_vx",
        "forward_displacement",
        "pass",
        "recommendation",
    ]

    write_csv(analysis_csv, analysis_rows, analysis_fields)
    write_csv(ranking_csv, ranking_out, ranking_fields)
    write_csv(validation_csv, checks, ["check", "status", "detail"])

    md_cols = [
        "scale",
        "mean_vx",
        "mean_abs_velocity_error",
        "forward_displacement",
        "delta_error_vs_baseline",
        "pass",
        "recommendation",
    ]
    analysis_table_md = markdown_table(analysis_rows, md_cols)

    ranking_md_cols = [
        "rank",
        "scale",
        "mean_abs_velocity_error",
        "mean_vx",
        "forward_displacement",
        "recommendation",
    ]
    ranking_table_md = markdown_table(ranking_out, ranking_md_cols)

    best_scale = best_candidate["scale"] if best_candidate else "unknown"
    best_error = best_candidate["mean_abs_velocity_error"] if best_candidate else "unknown"
    best_delta_error = best_candidate["delta_error_vs_baseline"] if best_candidate else "unknown"

    conclusion = (
        f"当前 sweep 中所有 scale 均通过稳定性和安全边界；"
        f"速度误差随 scale 变化呈非单调特征。"
        f"在已测试 candidate scale 中，scale={best_scale} 的 mean_abs_velocity_error 最低，"
        f"相对 baseline 的 delta_error={best_delta_error}，可作为当前更合理的低尺度 candidate 注入候选。"
        f"scale=0.020 出现明显速度退化，不建议作为速度跟踪默认注入强度。"
    )

    analysis_md.write_text(
        "# Stage 19.3 velocity-stability tradeoff analysis\n\n"
        "## Analysis table\n\n"
        + analysis_table_md
        + "\n\n## Ranking by velocity error\n\n"
        + ranking_table_md
        + "\n",
        encoding="utf-8",
    )

    doc.write_text(f"""# Stage 19.3：速度-稳定性综合分析

## 1. 目标

Stage 19.3 对 Stage 19.2 的 velocity-aware candidate scale sweep 结果进行综合分析。

分析目标不是证明 MPC/WBC candidate 全面优于 baseline，而是判断不同 candidate scale 对速度跟踪和稳定性边界的影响。

## 2. 结果

Stage 19.3 result: {result}

Failure count: {failure_count}

## 3. 关键结论

{conclusion}

## 4. 速度-稳定性分析表

{analysis_table_md}

## 5. 速度误差排序

{ranking_table_md}

## 6. 当前推荐

当前可推荐的候选注入强度：

    scale={best_scale}

推荐理由：

    在当前 target_vx=0.2 m/s 的 simulation-only sweep 中，scale={best_scale} 通过稳定性边界，且 mean_abs_velocity_error={best_error}，优于 baseline 的速度误差。

## 7. 当前不推荐

当前不推荐将 scale=0.020 作为速度跟踪默认注入强度。

原因：

    scale=0.020 虽然通过稳定性边界，但 mean_abs_velocity_error 明显高于 baseline 和 scale=0.010，对前向速度跟踪不利。

## 8. 结论边界

Stage 19.3 仍然只支持 simulation-only 证据结论。

不能声明：

  * 已完成完整 MPC-WBC 速度控制器；
  * MPC/WBC candidate 已全面优于 baseline；
  * 已完成真实机器人 torque 执行；
  * 已完成硬件 torque enablement。

更准确的表述是：

> Stage 19 通过速度感知 scale sweep 发现 candidate scale 对速度跟踪影响并非单调。在当前 target_vx=0.2 m/s 仿真测试中，scale=0.010 是更合理的低尺度 candidate 注入候选，而 scale=0.020 不适合作为速度跟踪默认注入强度。
""", encoding="utf-8")

    summary = {
        "stage": "19.3",
        "name": "velocity-stability tradeoff analysis",
        "result": result,
        "failure_count": failure_count,
        "source": str(source_table.relative_to(root)),
        "best_candidate_scale": best_scale,
        "best_candidate_mean_abs_velocity_error": best_error,
        "best_candidate_delta_error_vs_baseline": best_delta_error,
        "non_monotonic_candidate_error": non_monotonic,
        "conclusion": conclusion,
        "generated_files": [
            str(analysis_csv.relative_to(root)),
            str(ranking_csv.relative_to(root)),
            str(analysis_md.relative_to(root)),
            str(validation_csv.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(doc.relative_to(root)),
        ],
        "claim_boundary": [
            "simulation-only velocity-stability tradeoff analysis",
            "scale=0.010 is a tested candidate scale recommendation, not a full controller claim",
            "scale=0.020 is not recommended as default velocity-tracking injection strength",
            "no real robot torque execution claim",
            "no hardware torque enablement claim",
            "no comprehensive MPC/WBC superiority claim",
        ],
        "analysis_rows": analysis_rows,
        "ranking_rows": ranking_out,
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"stage19_3_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"best_candidate_scale: {best_scale}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"analysis_csv: {analysis_csv.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
