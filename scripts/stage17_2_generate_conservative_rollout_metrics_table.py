#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def to_float(row: dict[str, str], key: str) -> float:
    return float(row[key])


def to_int(row: dict[str, str], key: str) -> int:
    return int(float(row[key]))


def fmt_float(x: float, ndigits: int = 6) -> str:
    return f"{x:.{ndigits}f}"


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise RuntimeError("No rows to write.")
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(row.get(c, "")) for c in columns) + " |")
    return "\n".join([header, sep] + body)


def main() -> int:
    root = repo_root()
    log_dir = root / "results" / "logs_sample"
    docs_dir = root / "docs"

    source_csv = log_dir / "stage14_5e_r1_candidate_robustness_scale_sweep_table.csv"
    stage17_1_summary = log_dir / "stage17_1_conservative_closed_loop_rollout_summary.json"

    out_csv = log_dir / "stage17_2_conservative_rollout_metrics_table.csv"
    out_md = log_dir / "stage17_2_conservative_rollout_metrics_table.md"
    out_summary = log_dir / "stage17_2_conservative_rollout_metrics_summary.json"
    out_doc = docs_dir / "STAGE17_2_CONSERVATIVE_ROLLOUT_METRICS_TABLE.md"

    if not source_csv.is_file():
        raise FileNotFoundError(source_csv)
    if not stage17_1_summary.is_file():
        raise FileNotFoundError(stage17_1_summary)

    source_rows = read_csv(source_csv)

    expected_scales = {"0.00", "0.02", "0.05", "0.10"}
    seen_scales = {f"{to_float(row, 'scale'):.2f}" for row in source_rows}

    rows: list[dict[str, str]] = []
    for row in source_rows:
        scale = to_float(row, "scale")
        min_z = to_float(row, "min_z")
        max_abs_roll = to_float(row, "max_abs_roll")
        max_abs_pitch = to_float(row, "max_abs_pitch")
        max_tau_total_abs = to_float(row, "max_tau_total_abs")
        max_tau_candidate_abs = to_float(row, "max_tau_candidate_abs")
        max_tau_candidate_scaled_abs = to_float(row, "max_tau_candidate_scaled_abs")

        rows.append({
            "scale": f"{scale:.2f}",
            "control_mode": row.get("control_mode", ""),
            "pass": row.get("pass", ""),
            "total_steps": str(to_int(row, "total_steps")),
            "min_z": fmt_float(min_z),
            "z_margin_to_0p22": fmt_float(min_z - 0.22),
            "max_abs_roll": fmt_float(max_abs_roll),
            "roll_margin_to_0p20": fmt_float(0.20 - max_abs_roll),
            "max_abs_pitch": fmt_float(max_abs_pitch),
            "pitch_margin_to_0p20": fmt_float(0.20 - max_abs_pitch),
            "max_tau_total_abs": fmt_float(max_tau_total_abs),
            "max_tau_candidate_abs": fmt_float(max_tau_candidate_abs),
            "max_tau_candidate_scaled_abs": fmt_float(max_tau_candidate_scaled_abs),
            "qp_fail_steps": str(to_int(row, "qp_fail_steps")),
            "saturation_steps": str(to_int(row, "saturation_steps")),
            "summary_csv": row.get("summary_csv", ""),
            "log_csv": row.get("log_csv", ""),
        })

    pass_rows = [r for r in rows if r["pass"].lower() == "true"]
    conservative = next((r for r in rows if r["scale"] == "0.02"), None)

    checks = [
        {
            "check": "source_csv_exists",
            "status": "PASS" if source_csv.is_file() else "FAIL",
            "detail": str(source_csv.relative_to(root)),
        },
        {
            "check": "stage17_1_summary_exists",
            "status": "PASS" if stage17_1_summary.is_file() else "FAIL",
            "detail": str(stage17_1_summary.relative_to(root)),
        },
        {
            "check": "expected_scales_present",
            "status": "PASS" if expected_scales.issubset(seen_scales) else "FAIL",
            "detail": f"seen={sorted(seen_scales)}",
        },
        {
            "check": "all_rows_pass",
            "status": "PASS" if len(pass_rows) == len(rows) and len(rows) > 0 else "FAIL",
            "detail": f"pass_rows={len(pass_rows)}, total_rows={len(rows)}",
        },
        {
            "check": "conservative_0p02_row_present",
            "status": "PASS" if conservative is not None else "FAIL",
            "detail": "scale=0.02",
        },
    ]

    result = "pass" if all(c["status"] == "PASS" for c in checks) else "fail"

    write_csv(out_csv, rows)

    table_columns = [
        "scale",
        "control_mode",
        "pass",
        "total_steps",
        "min_z",
        "z_margin_to_0p22",
        "max_abs_roll",
        "roll_margin_to_0p20",
        "max_abs_pitch",
        "pitch_margin_to_0p20",
        "max_tau_total_abs",
        "max_tau_candidate_scaled_abs",
        "qp_fail_steps",
        "saturation_steps",
    ]

    table_md = markdown_table(rows, table_columns)

    doc_text = f"""# Stage 17.2: Conservative Rollout Metrics Table

## 1. 目标

Stage 17.2 将 Stage 14.5e 的 candidate robustness scale sweep 结果整理为可读指标表，用于 README、项目答辩和技术说明。

本阶段不新增控制器，不重新声明闭环性能，只做已有 simulation-only 证据的结构化整理。

## 2. 数据来源

```text
results/logs_sample/stage14_5e_r1_candidate_robustness_scale_sweep_table.csv
results/logs_sample/stage17_1_conservative_closed_loop_rollout_summary.json
```

## 3. 指标表

{table_md}

## 4. 结论边界

可以声明：

- 已整理 `scale=0.00 / 0.02 / 0.05 / 0.10` 的 conservative candidate rollout 指标；
- 已记录高度、姿态、力矩、QP failure、saturation 等安全边界；
- `scale=0.02` 可作为 Stage 17.1 的 conservative candidate injection 代表工况；
- 该证据属于 simulation-only closed-loop rollout evidence。

不能声明：

- 已完成真实机器人控制；
- 已完成硬件 torque enablement；
- 已完成速度跟踪性能评估；
- 已证明 MPC/WBC 全面优于 baseline；
- 已完成高性能 MPC-WBC locomotion controller。

## 5. 技术表述

推荐表述：

> 项目没有直接声明 MPC/WBC 已经全面替代 baseline，而是先做 conservative candidate injection sweep。结果表明，在 simulation-only 环境下，低尺度 candidate 注入没有破坏高度、姿态、QP 求解和力矩饱和边界；其中 scale=0.02 作为最保守工况被封装为 Stage 17.1 evidence。

"""

    out_md.write_text(table_md + "\n", encoding="utf-8")
    out_doc.write_text(doc_text, encoding="utf-8")

    summary = {
        "stage": "17.2",
        "name": "conservative rollout metrics table",
        "result": result,
        "source_csv": str(source_csv.relative_to(root)),
        "stage17_1_summary": str(stage17_1_summary.relative_to(root)),
        "generated_files": [
            str(out_csv.relative_to(root)),
            str(out_md.relative_to(root)),
            str(out_summary.relative_to(root)),
            str(out_doc.relative_to(root)),
        ],
        "row_count": len(rows),
        "seen_scales": sorted(seen_scales),
        "expected_scales": sorted(expected_scales),
        "conservative_scale": "0.02",
        "claim_boundary": [
            "simulation-only metrics packaging",
            "no velocity tracking metric in this evidence table",
            "no hardware torque execution claim",
            "no comprehensive MPC/WBC superiority claim",
        ],
        "checks": checks,
    }

    out_summary.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"stage17_2_result: {result}")
    print(f"rows: {len(rows)}")
    print(f"output_csv: {out_csv.relative_to(root)}")
    print(f"output_doc: {out_doc.relative_to(root)}")
    print(f"summary: {out_summary.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
