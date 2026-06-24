#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


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


def planned_cases() -> list[dict[str, object]]:
    return [
        {"scale": 0.000, "tag": "0p000", "mode": "baseline"},
        {"scale": 0.005, "tag": "0p005", "mode": "mpc_assisted_candidate"},
        {"scale": 0.010, "tag": "0p010", "mode": "mpc_assisted_candidate"},
        {"scale": 0.020, "tag": "0p020", "mode": "mpc_assisted_candidate"},
        {"scale": 0.050, "tag": "0p050", "mode": "mpc_assisted_candidate"},
    ]


def main() -> int:
    root = repo_root()
    logs = root / "results" / "logs_sample"
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)

    runner = root / "scripts" / "stage19_2_velocity_scale_sweep_runner.py"
    executor = root / "scripts" / "stage19_2_run_velocity_scale_sweep.py"
    execution_summary = logs / "stage19_2_velocity_scale_sweep_execution_summary.json"

    validation_csv = logs / "stage19_2_velocity_scale_sweep_validation.csv"
    table_csv = logs / "stage19_2_velocity_scale_sweep_table.csv"
    table_md = logs / "stage19_2_velocity_scale_sweep_table.md"
    summary_json = logs / "stage19_2_velocity_scale_sweep_summary.json"
    doc = docs / "STAGE19_2_VELOCITY_SCALE_SWEEP_ROLLOUT.md"

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    check("runner_exists", runner.is_file() and runner.stat().st_size > 0, str(runner.relative_to(root)))
    check("executor_exists", executor.is_file() and executor.stat().st_size > 0, str(executor.relative_to(root)))
    check("execution_summary_exists", execution_summary.is_file() and execution_summary.stat().st_size > 0, str(execution_summary.relative_to(root)))

    required_log_cols = [
        "base_x",
        "base_y",
        "base_vx_fd",
        "target_vx",
        "velocity_error",
        "base_z",
        "roll",
        "pitch",
        "candidate_scale",
        "tau_total_abs",
        "tau_candidate_scaled_abs",
        "saturated",
    ]

    required_summary_cols = [
        "stage",
        "scale_tag",
        "control_mode",
        "target_vx",
        "mean_vx",
        "mean_abs_velocity_error",
        "max_abs_velocity_error",
        "forward_displacement",
        "min_z",
        "max_abs_roll",
        "max_abs_pitch",
        "qp_fail_steps",
        "saturation_steps",
        "max_tau_total_abs",
        "max_tau_candidate_scaled_abs",
        "pass",
    ]

    table_rows: list[dict[str, str]] = []

    for case in planned_cases():
        scale = float(case["scale"])
        tag = str(case["tag"])
        mode = str(case["mode"])

        log_csv = logs / f"stage19_2_velocity_scale_{tag}_{mode}_log.csv"
        summary_csv = logs / f"stage19_2_velocity_scale_{tag}_{mode}_summary.csv"

        log_rows = read_rows(log_csv)
        summary_rows = read_rows(summary_csv)
        summary = summary_rows[0] if summary_rows else {}

        check(f"{tag}_log_exists", log_csv.is_file() and log_csv.stat().st_size > 0, str(log_csv.relative_to(root)))
        check(f"{tag}_summary_exists", summary_csv.is_file() and summary_csv.stat().st_size > 0, str(summary_csv.relative_to(root)))
        check(f"{tag}_log_rows_2400", len(log_rows) == 2400, f"rows={len(log_rows)}")
        check(f"{tag}_summary_one_row", len(summary_rows) == 1, f"rows={len(summary_rows)}")

        log_cols = set(log_rows[0].keys()) if log_rows else set()
        summary_cols = set(summary.keys())

        for col in required_log_cols:
            check(f"{tag}_log_has::{col}", col in log_cols, col)

        for col in required_summary_cols:
            check(f"{tag}_summary_has::{col}", col in summary_cols, col)

        target_vx = fval(summary, "target_vx", -1.0)
        recorded_scale = fval(summary, "mpc_assisted_candidate_scale", -1.0)

        check(f"{tag}_target_vx_0p2", abs(target_vx - 0.2) < 1e-9, f"target_vx={target_vx}")
        check(f"{tag}_scale_matches_plan", abs(recorded_scale - scale) < 1e-9, f"recorded_scale={recorded_scale}, planned={scale}")

        table_rows.append({
            "scale": f"{scale:.3f}",
            "scale_tag": tag,
            "control_mode": mode,
            "target_vx": f"{target_vx:.6f}",
            "mean_vx": f"{fval(summary, 'mean_vx'):.6f}",
            "mean_abs_velocity_error": f"{fval(summary, 'mean_abs_velocity_error'):.6f}",
            "max_abs_velocity_error": f"{fval(summary, 'max_abs_velocity_error'):.6f}",
            "forward_displacement": f"{fval(summary, 'forward_displacement'):.6f}",
            "min_z": f"{fval(summary, 'min_z'):.6f}",
            "max_abs_roll": f"{fval(summary, 'max_abs_roll'):.6f}",
            "max_abs_pitch": f"{fval(summary, 'max_abs_pitch'):.6f}",
            "qp_fail_steps": str(int(fval(summary, "qp_fail_steps"))),
            "saturation_steps": str(int(fval(summary, "saturation_steps"))),
            "max_tau_total_abs": f"{fval(summary, 'max_tau_total_abs'):.6f}",
            "max_tau_candidate_scaled_abs": f"{fval(summary, 'max_tau_candidate_scaled_abs'):.6f}",
            "pass": str(bval(summary, "pass")),
            "log_csv": str(log_csv.relative_to(root)),
            "summary_csv": str(summary_csv.relative_to(root)),
        })

    expected_tags = [str(c["tag"]) for c in planned_cases()]
    actual_tags = [r["scale_tag"] for r in table_rows]
    check("all_planned_tags_present", actual_tags == expected_tags, f"actual={actual_tags}")

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    table_fields = [
        "scale",
        "scale_tag",
        "control_mode",
        "target_vx",
        "mean_vx",
        "mean_abs_velocity_error",
        "max_abs_velocity_error",
        "forward_displacement",
        "min_z",
        "max_abs_roll",
        "max_abs_pitch",
        "qp_fail_steps",
        "saturation_steps",
        "max_tau_total_abs",
        "max_tau_candidate_scaled_abs",
        "pass",
        "log_csv",
        "summary_csv",
    ]

    write_csv(validation_csv, checks, ["check", "status", "detail"])
    write_csv(table_csv, table_rows, table_fields)

    md_cols = [
        "scale",
        "mean_vx",
        "mean_abs_velocity_error",
        "forward_displacement",
        "min_z",
        "max_abs_roll",
        "max_abs_pitch",
        "qp_fail_steps",
        "saturation_steps",
        "pass",
    ]

    md_lines = [
        "| " + " | ".join(md_cols) + " |",
        "| " + " | ".join(["---"] * len(md_cols)) + " |",
    ]
    for row in table_rows:
        md_lines.append("| " + " | ".join(row[c] for c in md_cols) + " |")
    table_md_text = "\n".join(md_lines)
    table_md.write_text(table_md_text + "\n", encoding="utf-8")

    stable_count = sum(1 for r in table_rows if r["pass"] == "True")
    summary = {
        "stage": "19.2",
        "name": "velocity-aware candidate scale sweep rollout",
        "result": result,
        "failure_count": failure_count,
        "target_vx": 0.2,
        "planned_scales": [float(c["scale"]) for c in planned_cases()],
        "stable_pass_count": stable_count,
        "case_count": len(table_rows),
        "table_rows": table_rows,
        "generated_files": [
            str(validation_csv.relative_to(root)),
            str(table_csv.relative_to(root)),
            str(table_md.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(doc.relative_to(root)),
        ],
        "claim_boundary": [
            "simulation-only velocity-aware scale sweep",
            "finite-difference velocity from qpos[0]",
            "no candidate velocity improvement claim in Stage 19.2",
            "no full MPC-WBC velocity controller claim",
            "no real robot torque execution claim",
            "no hardware torque enablement claim",
        ],
        "checks": checks,
    }
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    doc.write_text(f"""# Stage 19.2：速度感知 candidate scale sweep rollout

## 1. 目标

Stage 19.2 基于 Stage 18.2 的 velocity tracking runner，派生带 scale tag 的 rollout runner，并运行不同 MPC/WBC candidate scale 的速度感知 sweep。

本阶段用于生成数据，不直接声明 candidate 改善速度跟踪。

## 2. 结果

Stage 19.2 result: {result}

Failure count: {failure_count}

Target vx: 0.2 m/s

Case count: {len(table_rows)}

Stability pass count: {stable_count}

## 3. Sweep 表

{table_md_text}

## 4. 生成文件

    scripts/stage19_2_velocity_scale_sweep_runner.py
    scripts/stage19_2_run_velocity_scale_sweep.py
    scripts/stage19_2_validate_velocity_scale_sweep.py
    results/logs_sample/stage19_2_velocity_scale_sweep_execution.csv
    results/logs_sample/stage19_2_velocity_scale_sweep_execution_summary.json
    results/logs_sample/stage19_2_velocity_scale_sweep_table.csv
    results/logs_sample/stage19_2_velocity_scale_sweep_table.md
    results/logs_sample/stage19_2_velocity_scale_sweep_validation.csv
    results/logs_sample/stage19_2_velocity_scale_sweep_summary.json

## 5. 结论边界

Stage 19.2 只生成 simulation-only velocity-aware scale sweep 数据。是否存在推荐 scale 区间，需要在 Stage 19.3 中基于速度误差、前向位移和稳定性边界进一步分析。
""", encoding="utf-8")

    print(f"stage19_2_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"table: {table_csv.relative_to(root)}")
    print(f"summary: {summary_json.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
