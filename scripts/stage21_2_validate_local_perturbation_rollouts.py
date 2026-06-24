#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_rows(path: Path):
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def fval(row, key, default=0.0):
    try:
        return float(row.get(key, default))
    except Exception:
        return default


def bval(row, key):
    return str(row.get(key, "")).strip().lower() == "true"


def write_csv(path: Path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def perturbation_cases():
    return [
        {"id": "nominal", "type": "none", "x": 0.00, "y": 0.00, "yaw": 0.00},
        {"id": "x_plus", "type": "base_x", "x": 0.02, "y": 0.00, "yaw": 0.00},
        {"id": "x_minus", "type": "base_x", "x": -0.02, "y": 0.00, "yaw": 0.00},
        {"id": "y_plus", "type": "base_y", "x": 0.00, "y": 0.02, "yaw": 0.00},
        {"id": "y_minus", "type": "base_y", "x": 0.00, "y": -0.02, "yaw": 0.00},
        {"id": "yaw_plus", "type": "base_yaw", "x": 0.00, "y": 0.00, "yaw": 0.03},
        {"id": "yaw_minus", "type": "base_yaw", "x": 0.00, "y": 0.00, "yaw": -0.03},
    ]


def scale_cases():
    return [
        {"scale": 0.000, "tag": "0p000", "mode": "baseline"},
        {"scale": 0.010, "tag": "0p010", "mode": "mpc_assisted_candidate"},
        {"scale": 0.020, "tag": "0p020", "mode": "mpc_assisted_candidate"},
    ]


def main() -> int:
    root = repo_root()
    logs = root / "results" / "logs_sample"
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)

    runner = root / "scripts" / "stage21_2_local_perturbation_runner.py"
    executor = root / "scripts" / "stage21_2_run_local_perturbation_rollouts.py"
    execution_summary = logs / "stage21_2_local_perturbation_execution_summary.json"

    validation_csv = logs / "stage21_2_local_perturbation_validation.csv"
    table_csv = logs / "stage21_2_local_perturbation_table.csv"
    table_md = logs / "stage21_2_local_perturbation_table.md"
    summary_json = logs / "stage21_2_local_perturbation_summary.json"
    doc = docs / "STAGE21_2_LOCAL_PERTURBATION_ROLLOUT.md"

    checks = []

    def check(name, ok, detail):
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
        "perturbation_id",
        "perturbation_type",
        "perturb_x",
        "perturb_y",
        "perturb_yaw",
    ]

    required_summary_cols = [
        "stage",
        "perturbation_id",
        "perturbation_type",
        "perturb_x",
        "perturb_y",
        "perturb_yaw",
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

    table_rows = []

    for pert in perturbation_cases():
        pid = pert["id"]
        ptype = pert["type"]
        px = float(pert["x"])
        py = float(pert["y"])
        pyaw = float(pert["yaw"])

        for scale_case in scale_cases():
            scale = float(scale_case["scale"])
            tag = scale_case["tag"]
            mode = scale_case["mode"]

            log_csv = logs / f"stage21_2_local_perturb_{pid}_{tag}_{mode}_log.csv"
            summary_csv = logs / f"stage21_2_local_perturb_{pid}_{tag}_{mode}_summary.csv"

            log_rows = read_rows(log_csv)
            summary_rows = read_rows(summary_csv)
            summary = summary_rows[0] if summary_rows else {}

            case_name = f"{pid}_{tag}"

            check(f"{case_name}_log_exists", log_csv.is_file() and log_csv.stat().st_size > 0, str(log_csv.relative_to(root)))
            check(f"{case_name}_summary_exists", summary_csv.is_file() and summary_csv.stat().st_size > 0, str(summary_csv.relative_to(root)))
            check(f"{case_name}_log_rows_2400", len(log_rows) == 2400, f"rows={len(log_rows)}")
            check(f"{case_name}_summary_one_row", len(summary_rows) == 1, f"rows={len(summary_rows)}")

            log_cols = set(log_rows[0].keys()) if log_rows else set()
            summary_cols = set(summary.keys())

            for col in required_log_cols:
                check(f"{case_name}_log_has::{col}", col in log_cols, col)

            for col in required_summary_cols:
                check(f"{case_name}_summary_has::{col}", col in summary_cols, col)

            recorded_scale = fval(summary, "mpc_assisted_candidate_scale", -1.0)

            check(f"{case_name}_target_vx_0p2", abs(fval(summary, "target_vx", -1.0) - 0.2) < 1e-9, f"target_vx={summary.get('target_vx')}")
            check(f"{case_name}_scale_matches_plan", abs(recorded_scale - scale) < 1e-9, f"recorded_scale={recorded_scale}, planned={scale}")
            check(f"{case_name}_perturbation_id_matches", summary.get("perturbation_id") == pid, f"perturbation_id={summary.get('perturbation_id')}")
            check(f"{case_name}_perturb_x_matches", abs(fval(summary, "perturb_x") - px) < 1e-9, f"perturb_x={summary.get('perturb_x')}")
            check(f"{case_name}_perturb_y_matches", abs(fval(summary, "perturb_y") - py) < 1e-9, f"perturb_y={summary.get('perturb_y')}")
            check(f"{case_name}_perturb_yaw_matches", abs(fval(summary, "perturb_yaw") - pyaw) < 1e-9, f"perturb_yaw={summary.get('perturb_yaw')}")

            table_rows.append({
                "perturbation_id": pid,
                "perturbation_type": ptype,
                "perturb_x": f"{px:.6f}",
                "perturb_y": f"{py:.6f}",
                "perturb_yaw": f"{pyaw:.6f}",
                "scale": f"{scale:.3f}",
                "scale_tag": tag,
                "control_mode": mode,
                "target_vx": f"{fval(summary, 'target_vx'):.6f}",
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

    check("all_planned_cases_present", len(table_rows) == 21, f"rows={len(table_rows)}")
    check("all_cases_pass_stability", all(r["pass"] == "True" for r in table_rows), "all pass=True")

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    table_fields = [
        "perturbation_id",
        "perturbation_type",
        "perturb_x",
        "perturb_y",
        "perturb_yaw",
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
        "perturbation_id",
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
        "stage": "21.2",
        "name": "recommended scale local perturbation rollout",
        "result": result,
        "failure_count": failure_count,
        "target_vx": 0.2,
        "planned_perturbation_count": 7,
        "planned_scale_count": 3,
        "case_count": len(table_rows),
        "stable_pass_count": stable_count,
        "table_rows": table_rows,
        "generated_files": [
            str(validation_csv.relative_to(root)),
            str(table_csv.relative_to(root)),
            str(table_md.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(doc.relative_to(root)),
        ],
        "claim_boundary": [
            "simulation-only local perturbation rollout",
            "small initial base_x/base_y/yaw perturbations only",
            "finite-difference velocity from qpos[0]",
            "no real robot perturbation claim",
            "no full MPC-WBC velocity controller claim",
            "no hardware torque enablement claim",
            "no terrain or external-force robustness claim",
        ],
        "checks": checks,
    }
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    doc.write_text(f"""# Stage 21.2：局部扰动 rollout 证据

## 1. 目标

Stage 21.2 基于 Stage 20.2 replay runner 派生 local perturbation runner，并运行以下组合：

  * perturbation cases: nominal / x_plus / x_minus / y_plus / y_minus / yaw_plus / yaw_minus
  * scale anchors: 0.000 / 0.010 / 0.020

共 21 组 simulation-only rollout。

## 2. 结果

Stage 21.2 result: {result}

Failure count: {failure_count}

Target vx: 0.2 m/s

Case count: {len(table_rows)}

Stability pass count: {stable_count}

## 3. Local perturbation 表

{table_md_text}

## 4. 生成文件

    scripts/stage21_2_local_perturbation_runner.py
    scripts/stage21_2_run_local_perturbation_rollouts.py
    scripts/stage21_2_validate_local_perturbation_rollouts.py
    results/logs_sample/stage21_2_local_perturbation_execution.csv
    results/logs_sample/stage21_2_local_perturbation_execution_summary.json
    results/logs_sample/stage21_2_local_perturbation_validation.csv
    results/logs_sample/stage21_2_local_perturbation_table.csv
    results/logs_sample/stage21_2_local_perturbation_table.md
    results/logs_sample/stage21_2_local_perturbation_summary.json

## 5. 结论边界

Stage 21.2 只生成 simulation-only local perturbation rollout 数据。是否确认 scale=0.010 的推荐关系在局部扰动下仍然成立，需要在 Stage 21.3 中基于速度误差、前向位移和稳定性边界进一步分析。
""", encoding="utf-8")

    print(f"stage21_2_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"table: {table_csv.relative_to(root)}")
    print(f"summary: {summary_json.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
