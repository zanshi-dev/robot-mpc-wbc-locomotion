#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path


PERTURBATION_IDS = [
    "nominal",
    "vx_plus",
    "vx_minus",
    "vy_plus",
    "vy_minus",
    "yawrate_plus",
    "yawrate_minus",
]

SCALE_TAGS = ["0p000", "0p010", "0p020"]

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

    source_table = logs / "stage22_2_observable_perturbation_table.csv"
    source_summary = logs / "stage22_2_observable_perturbation_summary.json"

    per_perturb_csv = logs / "stage22_3_observable_robustness_per_perturbation_checks.csv"
    per_scale_csv = logs / "stage22_3_observable_robustness_per_scale_stats.csv"
    variability_csv = logs / "stage22_3_observable_perturbation_variability.csv"
    validation_csv = logs / "stage22_3_observable_robustness_validation.csv"
    analysis_md = logs / "stage22_3_observable_robustness_analysis.md"
    summary_json = logs / "stage22_3_observable_robustness_summary.json"
    doc = docs / "STAGE22_3_OBSERVABLE_ROBUSTNESS_ANALYSIS.md"

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    check("source_table_exists", source_table.is_file() and source_table.stat().st_size > 0, str(source_table.relative_to(root)))
    check("source_summary_exists", source_summary.is_file() and source_summary.stat().st_size > 0, str(source_summary.relative_to(root)))

    s22_2 = load_json(source_summary)
    check("stage22_2_result_pass", s22_2.get("result") == "pass", f"result={s22_2.get('result')}")

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

    all_cases_pass = all(bval(row, "pass") for row in rows)
    all_qp_zero = all(int(fval(row, "qp_fail_steps")) == 0 for row in rows)
    all_saturation_zero = all(int(fval(row, "saturation_steps")) == 0 for row in rows)

    check("all_cases_pass_stability", all_cases_pass, "all pass=True")
    check("all_qp_fail_zero", all_qp_zero, "all qp_fail_steps=0")
    check("all_saturation_zero", all_saturation_zero, "all saturation_steps=0")

    per_perturb_rows: list[dict[str, str]] = []

    rec_all_stable = True
    rec_error_lower_than_baseline_all = True
    rec_error_lower_than_0p020_all = True
    rec_displacement_higher_than_baseline_all = True
    rec_displacement_higher_than_0p020_all = True

    rec_error_lower_than_baseline_count = 0
    rec_error_lower_than_0p020_count = 0

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
        rec_minus_base_disp = rec_disp - base_disp
        rec_minus_reg_disp = rec_disp - reg_disp

        rec_stable = bval(recommended, "pass")
        rec_lower_base = rec_minus_base_error < 0.0
        rec_lower_reg = rec_minus_reg_error < 0.0
        rec_disp_base = rec_minus_base_disp > 0.0
        rec_disp_reg = rec_minus_reg_disp > 0.0

        rec_all_stable = rec_all_stable and rec_stable
        rec_error_lower_than_baseline_all = rec_error_lower_than_baseline_all and rec_lower_base
        rec_error_lower_than_0p020_all = rec_error_lower_than_0p020_all and rec_lower_reg
        rec_displacement_higher_than_baseline_all = rec_displacement_higher_than_baseline_all and rec_disp_base
        rec_displacement_higher_than_0p020_all = rec_displacement_higher_than_0p020_all and rec_disp_reg

        rec_error_lower_than_baseline_count += int(rec_lower_base)
        rec_error_lower_than_0p020_count += int(rec_lower_reg)

        per_perturb_rows.append({
            "perturbation_id": pid,
            "baseline_error": f"{base_error:.6f}",
            "recommended_error": f"{rec_error:.6f}",
            "regression_0p020_error": f"{reg_error:.6f}",
            "recommended_minus_baseline_error": f"{rec_minus_base_error:.6f}",
            "recommended_minus_0p020_error": f"{rec_minus_reg_error:.6f}",
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
        })

    check("recommended_pass_all_perturbations", rec_all_stable, str(rec_all_stable))
    check("recommended_error_lower_than_baseline_all_perturbations", rec_error_lower_than_baseline_all, str(rec_error_lower_than_baseline_all))
    check("recommended_error_lower_than_0p020_all_perturbations", rec_error_lower_than_0p020_all, str(rec_error_lower_than_0p020_all))
    check("recommended_displacement_higher_than_baseline_all_perturbations", rec_displacement_higher_than_baseline_all, str(rec_displacement_higher_than_baseline_all))
    check("recommended_displacement_higher_than_0p020_all_perturbations", rec_displacement_higher_than_0p020_all, str(rec_displacement_higher_than_0p020_all))

    role_map = {
        "0p000": "baseline_reference",
        "0p010": "recommended_candidate",
        "0p020": "regression_anchor",
    }

    per_scale_rows: list[dict[str, str]] = []
    variability_rows: list[dict[str, str]] = []
    perturbation_metric_variability_detected = False

    for tag in SCALE_TAGS:
        scale_rows = by_scale[tag]
        if not scale_rows:
            continue

        scale_out = {
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

            variability_rows.append({
                "scale_tag": tag,
                "metric": metric,
                "min": f"{min(values):.12f}",
                "max": f"{max(values):.12f}",
                "range": f"{range_v:.12f}",
                "std": f"{std_v:.12f}",
                "observable_variability": str(range_v > 1e-12),
            })

            if range_v > 1e-12:
                perturbation_metric_variability_detected = True

            scale_out[f"{metric}_mean"] = f"{mean_v:.12f}"
            scale_out[f"{metric}_std"] = f"{std_v:.12f}"
            scale_out[f"{metric}_range"] = f"{range_v:.12f}"

        per_scale_rows.append(scale_out)

    observable_perturbation_pass = (
        all_cases_pass
        and all_qp_zero
        and all_saturation_zero
        and perturbation_metric_variability_detected
    )

    recommendation_relation_stable = (
        rec_all_stable
        and rec_error_lower_than_baseline_all
        and rec_error_lower_than_0p020_all
        and rec_displacement_higher_than_baseline_all
        and rec_displacement_higher_than_0p020_all
    )

    recommendation_observable_robust = (
        observable_perturbation_pass
        and recommendation_relation_stable
    )

    # 注意：这里不把 perturbation_metric_variability_detected=False 判为脚本失败。
    # Stage 22.3 的职责是如实分析；如果扰动不可观测，应输出 pass + recommendation_observable_robust=False。
    check("analysis_completed", True, "analysis generated")
    check("observable_variability_recorded", isinstance(perturbation_metric_variability_detected, bool), str(perturbation_metric_variability_detected))
    check("recommendation_relation_evaluated", isinstance(recommendation_relation_stable, bool), str(recommendation_relation_stable))

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    per_perturb_fields = list(per_perturb_rows[0].keys()) if per_perturb_rows else ["perturbation_id"]
    per_scale_fields = list(per_scale_rows[0].keys()) if per_scale_rows else ["scale_tag"]
    variability_fields = list(variability_rows[0].keys()) if variability_rows else ["scale_tag", "metric"]

    write_csv(per_perturb_csv, per_perturb_rows, per_perturb_fields)
    write_csv(per_scale_csv, per_scale_rows, per_scale_fields)
    write_csv(variability_csv, variability_rows, variability_fields)
    write_csv(validation_csv, checks, ["check", "status", "detail"])

    per_perturb_md_cols = [
        "perturbation_id",
        "recommended_minus_baseline_error",
        "recommended_minus_0p020_error",
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

    variability_md_cols = [
        "scale_tag",
        "metric",
        "range",
        "std",
        "observable_variability",
    ]

    per_perturb_md = markdown_table(per_perturb_rows, per_perturb_md_cols)
    per_scale_md = markdown_table(per_scale_rows, per_scale_md_cols)
    variability_md = markdown_table(variability_rows, variability_md_cols)

    if perturbation_metric_variability_detected:
        conclusion = (
            "Stage 22.3 observable robustness analysis 通过。当前 qvel 初始速度扰动使 summary 指标产生了可观测变化；"
            "scale=0.010 在扰动工况下保持稳定，并完成了与 baseline 和 scale=0.020 的推荐关系对比。"
        )
        claim_support = (
            "当前证据支持将 scale=0.010 表述为 simulation-only observable-perturbation-tested recommended candidate scale。"
        )
    else:
        conclusion = (
            "Stage 22.3 analysis 通过，但 observable perturbation robustness 不成立。"
            "当前 qvel 初始速度扰动没有使 summary 指标产生可观测变化；"
            "因此 Stage 22 不能声明完成 observable perturbation robustness audit，只能记录为 qvel perturbation injection attempt。"
        )
        claim_support = (
            "当前证据不支持将 scale=0.010 升级为 observable-perturbation-tested recommended candidate scale；"
            "仍只能沿用 Stage 21 的 local-perturbation-tested recommended candidate scale 表述。"
        )

    analysis_md.write_text(
        "# Stage 22.3 observable robustness analysis\n\n"
        "## Per-perturbation recommendation checks\n\n"
        + per_perturb_md
        + "\n\n## Per-scale statistics\n\n"
        + per_scale_md
        + "\n\n## Perturbation metric variability\n\n"
        + variability_md
        + "\n",
        encoding="utf-8",
    )

    doc.write_text(f"""# Stage 22.3：可观测扰动鲁棒性分析

## 1. 目标

Stage 22.3 分析 Stage 22.2 生成的 21 组 qvel 初始速度扰动 rollout，判断：

  * qvel 初始速度扰动是否造成 summary 指标的可观测变化；
  * `scale=0.010` 是否仍然通过稳定性边界；
  * `scale=0.010` 是否仍然低于 baseline 和 `scale=0.020` 的速度误差；
  * 当前推荐是否可以升级为 observable-perturbation-tested recommended candidate scale。

## 2. 结果

Stage 22.3 result: {result}

Failure count: {failure_count}

Observable perturbation pass: {observable_perturbation_pass}

Perturbation metric variability detected: {perturbation_metric_variability_detected}

Recommendation relation stable: {recommendation_relation_stable}

Recommendation observable robust: {recommendation_observable_robust}

## 3. 关键结论

{conclusion}

{claim_support}

## 4. 推荐关系逐扰动检查

{per_perturb_md}

## 5. 每个 scale 的扰动统计

{per_scale_md}

## 6. 可观测扰动指标变化检查

{variability_md}

## 7. 当前支持的结论

如果 `perturbation_metric_variability_detected=False`，当前证据只支持：

    Stage 22 完成了 qvel 初始速度扰动注入尝试；
    21 组 rollout 均通过稳定性边界；
    scale=0.010 的推荐关系在当前记录指标中未被破坏；
    但由于 summary 指标没有出现可观测变化，不能声明 observable perturbation robustness。

如果 `perturbation_metric_variability_detected=True` 且 `recommendation_observable_robust=True`，才支持：

    scale=0.010 可作为当前 simulation-only 证据下的 observable-perturbation-tested recommended candidate scale。

## 8. 当前不支持的结论

当前证据不支持：

  * 完整 MPC-WBC 速度控制器已经完成；
  * `scale=0.010` 可以直接用于真实机器人；
  * `scale=0.010` 对所有速度、地形、扰动和外力冲击都最优；
  * MPC/WBC candidate 已全面优于 baseline；
  * 已完成真实机器人 torque 执行；
  * 已完成硬件 torque enablement；
  * 已完成复杂地形或外力冲击鲁棒性验证。
""", encoding="utf-8")

    summary = {
        "stage": "22.3",
        "name": "observable qvel perturbation robustness analysis",
        "result": result,
        "failure_count": failure_count,
        "source": str(source_table.relative_to(root)),
        "observable_perturbation_pass": observable_perturbation_pass,
        "perturbation_metric_variability_detected": perturbation_metric_variability_detected,
        "recommendation_relation_stable": recommendation_relation_stable,
        "recommendation_observable_robust": recommendation_observable_robust,
        "recommended_scale": "0.010",
        "baseline_scale": "0.000",
        "regression_anchor_scale": "0.020",
        "recommended_error_lower_than_baseline_count": rec_error_lower_than_baseline_count,
        "recommended_error_lower_than_0p020_count": rec_error_lower_than_0p020_count,
        "perturbation_count": len(PERTURBATION_IDS),
        "conclusion": conclusion,
        "claim_support": claim_support,
        "generated_files": [
            str(per_perturb_csv.relative_to(root)),
            str(per_scale_csv.relative_to(root)),
            str(variability_csv.relative_to(root)),
            str(validation_csv.relative_to(root)),
            str(analysis_md.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(doc.relative_to(root)),
        ],
        "claim_boundary": [
            "simulation-only qvel initial perturbation analysis",
            "initial qvel perturbations only",
            "if perturbation_metric_variability_detected is false, no observable robustness claim is supported",
            "no full MPC-WBC velocity controller claim",
            "no real robot torque execution claim",
            "no hardware torque enablement claim",
            "no terrain or external-force robustness claim",
        ],
        "per_perturbation_rows": per_perturb_rows,
        "per_scale_stats": per_scale_rows,
        "variability_rows": variability_rows,
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"stage22_3_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"observable_perturbation_pass: {observable_perturbation_pass}")
    print(f"perturbation_metric_variability_detected: {perturbation_metric_variability_detected}")
    print(f"recommendation_relation_stable: {recommendation_relation_stable}")
    print(f"recommendation_observable_robust: {recommendation_observable_robust}")
    print(f"summary: {summary_json.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
