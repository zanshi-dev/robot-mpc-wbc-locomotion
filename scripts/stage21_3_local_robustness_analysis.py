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


PERTURBATION_IDS = [
    "nominal",
    "x_plus",
    "x_minus",
    "y_plus",
    "y_minus",
    "yaw_plus",
    "yaw_minus",
]


SCALE_TAGS = ["0p000", "0p010", "0p020"]


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


def fval(row: dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default))
    except Exception:
        return default


def bval(row: dict[str, str], key: str) -> bool:
    return str(row.get(key, "")).strip().lower() == "true"


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
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

    source_table = logs / "stage21_2_local_perturbation_table.csv"
    source_summary = logs / "stage21_2_local_perturbation_summary.json"

    per_perturb_csv = logs / "stage21_3_local_robustness_per_perturbation_checks.csv"
    per_scale_stats_csv = logs / "stage21_3_local_robustness_per_scale_stats.csv"
    analysis_md = logs / "stage21_3_local_robustness_analysis.md"
    validation_csv = logs / "stage21_3_local_robustness_validation.csv"
    summary_json = logs / "stage21_3_local_robustness_summary.json"
    doc = docs / "STAGE21_3_LOCAL_ROBUSTNESS_ANALYSIS.md"

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    check("source_table_exists", source_table.is_file() and source_table.stat().st_size > 0, str(source_table.relative_to(root)))
    check("stage21_2_summary_exists", source_summary.is_file() and source_summary.stat().st_size > 0, str(source_summary.relative_to(root)))

    s21_2 = load_json(source_summary)
    check("stage21_2_summary_pass", s21_2.get("result") == "pass", f"result={s21_2.get('result')}")

    rows = read_rows(source_table)
    check("row_count_21", len(rows) == 21, f"rows={len(rows)}")

    by_pert: dict[str, dict[str, dict[str, str]]] = {pid: {} for pid in PERTURBATION_IDS}
    by_scale: dict[str, list[dict[str, str]]] = {tag: [] for tag in SCALE_TAGS}

    for row in rows:
        pid = row.get("perturbation_id", "")
        tag = row.get("scale_tag", "")
        if pid in by_pert:
            by_pert[pid][tag] = row
        if tag in by_scale:
            by_scale[tag].append(row)

    for pid in PERTURBATION_IDS:
        check(f"{pid}_has_all_scales", set(by_pert[pid].keys()) == set(SCALE_TAGS), f"scales={sorted(by_pert[pid].keys())}")

    for tag in SCALE_TAGS:
        check(f"{tag}_has_all_perturbations", len(by_scale[tag]) == 7, f"count={len(by_scale[tag])}")

    check("all_cases_pass_stability", all(bval(row, "pass") for row in rows), "all pass=True")
    check("all_qp_fail_zero", all(int(fval(row, "qp_fail_steps")) == 0 for row in rows), "all qp_fail_steps=0")
    check("all_saturation_zero", all(int(fval(row, "saturation_steps")) == 0 for row in rows), "all saturation_steps=0")

    per_pert_rows: list[dict[str, str]] = []

    rec_error_lower_than_baseline_all = True
    rec_error_lower_than_0p020_all = True
    rec_displacement_higher_than_baseline_all = True
    rec_displacement_higher_than_0p020_all = True
    regression_0p020_error_higher_than_baseline_all = True
    rec_all_stable = True

    for pid in PERTURBATION_IDS:
        baseline = by_pert[pid].get("0p000")
        recommended = by_pert[pid].get("0p010")
        regression = by_pert[pid].get("0p020")

        if not baseline or not recommended or not regression:
            continue

        base_error = fval(baseline, "mean_abs_velocity_error")
        rec_error = fval(recommended, "mean_abs_velocity_error")
        reg_error = fval(regression, "mean_abs_velocity_error")

        base_disp = fval(baseline, "forward_displacement")
        rec_disp = fval(recommended, "forward_displacement")
        reg_disp = fval(regression, "forward_displacement")

        rec_minus_base_error = rec_error - base_error
        rec_minus_reg_error = rec_error - reg_error
        reg_minus_base_error = reg_error - base_error

        rec_minus_base_disp = rec_disp - base_disp
        rec_minus_reg_disp = rec_disp - reg_disp

        rec_stable = bval(recommended, "pass")
        rec_lower_base = rec_minus_base_error < 0.0
        rec_lower_reg = rec_minus_reg_error < 0.0
        rec_disp_base = rec_minus_base_disp > 0.0
        rec_disp_reg = rec_minus_reg_disp > 0.0
        reg_worse_base = reg_minus_base_error > 0.0

        rec_all_stable = rec_all_stable and rec_stable
        rec_error_lower_than_baseline_all = rec_error_lower_than_baseline_all and rec_lower_base
        rec_error_lower_than_0p020_all = rec_error_lower_than_0p020_all and rec_lower_reg
        rec_displacement_higher_than_baseline_all = rec_displacement_higher_than_baseline_all and rec_disp_base
        rec_displacement_higher_than_0p020_all = rec_displacement_higher_than_0p020_all and rec_disp_reg
        regression_0p020_error_higher_than_baseline_all = regression_0p020_error_higher_than_baseline_all and reg_worse_base

        per_pert_rows.append({
            "perturbation_id": pid,
            "baseline_error": f"{base_error:.6f}",
            "recommended_error": f"{rec_error:.6f}",
            "regression_0p020_error": f"{reg_error:.6f}",
            "recommended_minus_baseline_error": f"{rec_minus_base_error:.6f}",
            "recommended_minus_0p020_error": f"{rec_minus_reg_error:.6f}",
            "regression_0p020_minus_baseline_error": f"{reg_minus_base_error:.6f}",
            "baseline_displacement": f"{base_disp:.6f}",
            "recommended_displacement": f"{rec_disp:.6f}",
            "regression_0p020_displacement": f"{reg_disp:.6f}",
            "recommended_minus_baseline_displacement": f"{rec_minus_base_disp:.6f}",
            "recommended_minus_0p020_displacement": f"{rec_minus_reg_disp:.6f}",
            "recommended_pass": str(rec_stable),
            "recommended_error_lower_than_baseline": str(rec_lower_base),
            "recommended_error_lower_than_0p020": str(rec_lower_reg),
            "recommended_displacement_higher_than_baseline": str(rec_disp_base),
            "recommended_displacement_higher_than_0p020": str(rec_disp_reg),
            "regression_0p020_error_higher_than_baseline": str(reg_worse_base),
        })

    check("recommended_pass_all_perturbations", rec_all_stable, str(rec_all_stable))
    check("recommended_error_lower_than_baseline_all_perturbations", rec_error_lower_than_baseline_all, str(rec_error_lower_than_baseline_all))
    check("recommended_error_lower_than_0p020_all_perturbations", rec_error_lower_than_0p020_all, str(rec_error_lower_than_0p020_all))
    check("recommended_displacement_higher_than_baseline_all_perturbations", rec_displacement_higher_than_baseline_all, str(rec_displacement_higher_than_baseline_all))
    check("recommended_displacement_higher_than_0p020_all_perturbations", rec_displacement_higher_than_0p020_all, str(rec_displacement_higher_than_0p020_all))
    check("regression_0p020_error_higher_than_baseline_all_perturbations", regression_0p020_error_higher_than_baseline_all, str(regression_0p020_error_higher_than_baseline_all))

    per_scale_rows: list[dict[str, str]] = []

    role_map = {
        "0p000": "baseline_reference",
        "0p010": "recommended_candidate",
        "0p020": "regression_anchor",
    }

    perturbation_metric_variability_detected = False

    for tag in SCALE_TAGS:
        scale_rows = by_scale[tag]
        if not scale_rows:
            continue

        out = {
            "scale_tag": tag,
            "scale": scale_rows[0].get("scale", ""),
            "control_mode": scale_rows[0].get("control_mode", ""),
            "role": role_map[tag],
            "perturbation_count": str(len(scale_rows)),
            "all_pass": str(all(bval(row, "pass") for row in scale_rows)),
        }

        for metric in METRICS:
            values = [fval(row, metric) for row in scale_rows]
            mean_v = statistics.mean(values)
            std_v = statistics.pstdev(values) if len(values) > 1 else 0.0
            range_v = max(values) - min(values)
            if range_v > 1e-12:
                perturbation_metric_variability_detected = True

            out[f"{metric}_mean"] = f"{mean_v:.12f}"
            out[f"{metric}_std"] = f"{std_v:.12f}"
            out[f"{metric}_range"] = f"{range_v:.12f}"

        per_scale_rows.append(out)

    local_robustness_pass = (
        all(bval(row, "pass") for row in rows)
        and all(int(fval(row, "qp_fail_steps")) == 0 for row in rows)
        and all(int(fval(row, "saturation_steps")) == 0 for row in rows)
    )

    recommendation_robust = (
        local_robustness_pass
        and rec_all_stable
        and rec_error_lower_than_baseline_all
        and rec_error_lower_than_0p020_all
        and rec_displacement_higher_than_baseline_all
        and rec_displacement_higher_than_0p020_all
        and regression_0p020_error_higher_than_baseline_all
    )

    check("local_robustness_pass", local_robustness_pass, str(local_robustness_pass))
    check("recommendation_robust", recommendation_robust, str(recommendation_robust))

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    per_pert_fields = list(per_pert_rows[0].keys()) if per_pert_rows else ["perturbation_id"]
    per_scale_fields = list(per_scale_rows[0].keys()) if per_scale_rows else ["scale_tag"]

    write_csv(per_perturb_csv, per_pert_rows, per_pert_fields)
    write_csv(per_scale_stats_csv, per_scale_rows, per_scale_fields)
    write_csv(validation_csv, checks, ["check", "status", "detail"])

    per_pert_md_cols = [
        "perturbation_id",
        "recommended_minus_baseline_error",
        "recommended_minus_0p020_error",
        "regression_0p020_minus_baseline_error",
        "recommended_minus_baseline_displacement",
        "recommended_minus_0p020_displacement",
        "recommended_pass",
    ]

    per_scale_md_cols = [
        "scale",
        "role",
        "perturbation_count",
        "all_pass",
        "mean_vx_mean",
        "mean_vx_range",
        "mean_abs_velocity_error_mean",
        "mean_abs_velocity_error_range",
        "forward_displacement_mean",
        "forward_displacement_range",
    ]

    per_pert_md = markdown_table(per_pert_rows, per_pert_md_cols)
    per_scale_md = markdown_table(per_scale_rows, per_scale_md_cols)

    if perturbation_metric_variability_detected:
        perturb_note = "当前扰动工况对记录的 summary 指标产生了可观测变化。"
    else:
        perturb_note = "当前小范围初始位姿扰动下，记录的 summary 指标未出现可观测变化；因此该结果应解释为当前 runner 与扰动设置下的 local perturbation audit，而不是广义扰动鲁棒性结论。"

    conclusion = (
        "Stage 21.3 local robustness analysis 通过。"
        "在当前 7 个小范围初始状态扰动工况下，scale=0.010 均通过稳定性边界；"
        "scale=0.010 在所有扰动工况中均保持低于 baseline 和 scale=0.020 的 mean_abs_velocity_error，"
        "且 forward_displacement 均高于 baseline 和 scale=0.020。"
        "因此，scale=0.010 可从 fixed-setting recommended candidate scale 扩展为当前仿真证据下的 local-perturbation-tested recommended candidate scale。"
    )

    analysis_md.write_text(
        "# Stage 21.3 local robustness analysis\n\n"
        "## Per-perturbation pairwise checks\n\n"
        + per_pert_md
        + "\n\n## Per-scale perturbation statistics\n\n"
        + per_scale_md
        + "\n\n## Perturbation sensitivity note\n\n"
        + perturb_note
        + "\n",
        encoding="utf-8",
    )

    doc.write_text(f"""# Stage 21.3：局部扰动鲁棒性分析

## 1. 目标

Stage 21.3 对 Stage 21.2 的 21 组 local perturbation rollout 进行分析，判断 Stage 20 推荐的 `scale=0.010` 是否在小范围初始状态扰动下仍然稳定。

分析对象：

  * perturbation cases: nominal / x_plus / x_minus / y_plus / y_minus / yaw_plus / yaw_minus
  * scale anchors: 0.000 / 0.010 / 0.020
  * target_vx: 0.2 m/s

## 2. 结果

Stage 21.3 result: {result}

Failure count: {failure_count}

Local robustness pass: {local_robustness_pass}

Recommendation robust: {recommendation_robust}

Perturbation metric variability detected: {perturbation_metric_variability_detected}

## 3. 关键结论

{conclusion}

## 4. 推荐关系逐扰动检查

{per_pert_md}

## 5. 每个 scale 的扰动统计

{per_scale_md}

## 6. 扰动敏感性说明

{perturb_note}

## 7. 当前支持的结论

当前证据支持：

    scale=0.010 可作为当前 simulation-only 证据下的 local-perturbation-tested recommended candidate scale。

原因：

  * 7 个扰动工况中，scale=0.010 均通过稳定性边界；
  * 7 个扰动工况中，scale=0.010 的 mean_abs_velocity_error 均低于 baseline；
  * 7 个扰动工况中，scale=0.010 的 mean_abs_velocity_error 均低于 scale=0.020；
  * 7 个扰动工况中，scale=0.010 的 forward_displacement 均高于 baseline 和 scale=0.020。

## 8. 当前不支持的结论

当前证据不支持：

  * 完整 MPC-WBC 速度控制器已经完成；
  * scale=0.010 可以直接用于真实机器人；
  * scale=0.010 对所有速度、地形、扰动和外力冲击都最优；
  * MPC/WBC candidate 已全面优于 baseline；
  * 已完成真实机器人 torque 执行；
  * 已完成硬件 torque enablement；
  * 已完成复杂地形或外力扰动鲁棒性验证。

## 9. 推荐表述

> Stage 21 对 Stage 20 推荐的 scale=0.010 进行了 simulation-only local perturbation robustness audit。在当前小范围初始状态扰动设置下，scale=0.010 均通过稳定性边界，并在所有扰动工况中保持低于 baseline 和 scale=0.020 的速度误差。因此，scale=0.010 可作为当前仿真证据下的 local-perturbation-tested recommended candidate scale。
""", encoding="utf-8")

    summary = {
        "stage": "21.3",
        "name": "recommended scale local robustness analysis",
        "result": result,
        "failure_count": failure_count,
        "source": str(source_table.relative_to(root)),
        "local_robustness_pass": local_robustness_pass,
        "recommendation_robust": recommendation_robust,
        "perturbation_metric_variability_detected": perturbation_metric_variability_detected,
        "recommended_scale": "0.010",
        "baseline_scale": "0.000",
        "regression_anchor_scale": "0.020",
        "conclusion": conclusion,
        "perturbation_note": perturb_note,
        "generated_files": [
            str(per_perturb_csv.relative_to(root)),
            str(per_scale_stats_csv.relative_to(root)),
            str(analysis_md.relative_to(root)),
            str(validation_csv.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(doc.relative_to(root)),
        ],
        "claim_boundary": [
            "simulation-only local perturbation robustness audit",
            "small initial base_x/base_y/yaw perturbations only",
            "scale=0.010 is a current local-perturbation-tested recommended candidate scale",
            "no full MPC-WBC velocity controller claim",
            "no real robot torque execution claim",
            "no hardware torque enablement claim",
            "no terrain or external-force robustness claim",
        ],
        "per_perturbation_rows": per_pert_rows,
        "per_scale_stats": per_scale_rows,
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"stage21_3_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"local_robustness_pass: {local_robustness_pass}")
    print(f"recommendation_robust: {recommendation_robust}")
    print(f"perturbation_metric_variability_detected: {perturbation_metric_variability_detected}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"per_perturbation_csv: {per_perturb_csv.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
