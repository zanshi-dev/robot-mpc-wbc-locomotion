#!/usr/bin/env python3
from pathlib import Path
import csv
import datetime as dt
import json
import subprocess
from typing import Dict, List, Any

ROOT = Path.cwd()
STAGE = "14.5D-R8"

SUMMARY_R3 = ROOT / "results/logs_sample/stage14_5d_r3_baseline_mode_derived_runner_dry_run_summary.json"
SUMMARY_R7 = ROOT / "results/logs_sample/stage14_5d_r7_candidate_mode_guarded_dry_run_summary.json"

BASELINE_SUMMARY_CSV = ROOT / "results/logs_sample/stage14_5d_r2_closed_loop_ab_baseline_skeleton_summary.csv"
BASELINE_LOG_CSV = ROOT / "results/logs_sample/stage14_5d_r2_closed_loop_ab_baseline_skeleton_log.csv"

CANDIDATE_SUMMARY_CSV = ROOT / "results/logs_sample/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_summary.csv"
CANDIDATE_LOG_CSV = ROOT / "results/logs_sample/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_log.csv"

BASELINE_RUNNER = ROOT / "scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py"
R2_RUNNER = ROOT / "scripts/stage14_5d_r2_closed_loop_ab_runner_skeleton.py"
R6_RUNNER = ROOT / "scripts/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_runner.py"

OUT_SUMMARY = ROOT / "results/logs_sample/stage14_5d_r8_closed_loop_ab_comparison_summary.json"
OUT_TABLE = ROOT / "results/logs_sample/stage14_5d_r8_closed_loop_ab_comparison_table.csv"
OUT_DOC = ROOT / "docs/stage14_5d_r8_closed_loop_ab_packaging.md"


METRIC_KEYS = [
    "initial_z",
    "final_z",
    "min_z",
    "max_z",
    "delta_z",
    "max_abs_roll",
    "max_abs_pitch",
    "max_joint_error",
    "max_swing_joint_error",
    "max_stance_joint_error",
    "max_tau_total_abs",
    "max_tau_total_raw_abs",
    "max_cmd_step_jump_norm",
    "max_cmd_step_jump_abs",
    "max_dyn_res_norm",
    "max_stance_acc_res_norm",
    "max_swing_acc_error_norm",
    "qp_fail_steps",
    "saturation_steps",
]


def git(args: List[str]) -> str:
    proc = subprocess.run(
        ["git"] + args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def read_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_single_csv_row(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    with open(path, "r", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 1:
        return {"__row_count__": str(len(rows))}
    rows[0]["__row_count__"] = "1"
    return rows[0]


def csv_row_count(path: Path) -> int:
    if not path.exists():
        return 0
    with open(path, "r", newline="") as f:
        return sum(1 for _ in csv.DictReader(f))


def as_bool(v) -> bool:
    return str(v).strip().lower() in {"true", "1", "yes", "y"}


def as_float(v):
    try:
        return float(v)
    except Exception:
        return None


def as_int(v):
    try:
        return int(float(v))
    except Exception:
        return None


def metric_value(row: Dict[str, str], key: str):
    if key in {"qp_fail_steps", "saturation_steps"}:
        return as_int(row.get(key))
    return as_float(row.get(key))


def main() -> int:
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)

    failed_checks = []

    r3 = read_json(SUMMARY_R3)
    r7 = read_json(SUMMARY_R7)

    if not r3 or r3.get("pass") is not True:
        failed_checks.append("stage14_5d_r3_not_passed_or_missing")
    if not r7 or r7.get("pass") is not True:
        failed_checks.append("stage14_5d_r7_not_passed_or_missing")

    baseline_row = read_single_csv_row(BASELINE_SUMMARY_CSV)
    candidate_row = read_single_csv_row(CANDIDATE_SUMMARY_CSV)

    if not baseline_row:
        failed_checks.append("baseline_summary_csv_missing_or_empty")
    if not candidate_row:
        failed_checks.append("candidate_summary_csv_missing_or_empty")

    baseline_log_rows = csv_row_count(BASELINE_LOG_CSV)
    candidate_log_rows = csv_row_count(CANDIDATE_LOG_CSV)

    if baseline_log_rows != 2400:
        failed_checks.append(f"baseline_log_row_count_not_2400:{baseline_log_rows}")
    if candidate_log_rows != 2400:
        failed_checks.append(f"candidate_log_row_count_not_2400:{candidate_log_rows}")

    if baseline_row:
        if baseline_row.get("control_mode") != "baseline":
            failed_checks.append("baseline_control_mode_not_baseline")
        if not as_bool(baseline_row.get("pass", baseline_row.get("pass_test"))):
            failed_checks.append("baseline_pass_false")
        if as_bool(baseline_row.get("mpc_assisted_candidate_executed")):
            failed_checks.append("baseline_candidate_executed_true")

    if candidate_row:
        if candidate_row.get("control_mode") != "mpc_assisted_candidate":
            failed_checks.append("candidate_control_mode_not_candidate")
        if not as_bool(candidate_row.get("pass", candidate_row.get("pass_test"))):
            failed_checks.append("candidate_pass_false")
        if not as_bool(candidate_row.get("mpc_assisted_candidate_executed")):
            failed_checks.append("candidate_executed_false")
        if candidate_row.get("mpc_assisted_candidate_scale") != "0.05":
            failed_checks.append("candidate_scale_not_0p05")

    for label, row in [("baseline", baseline_row), ("candidate", candidate_row)]:
        if row:
            for key in [
                "hardware_deployment_completed",
                "torque_enable_ready",
                "torque_publisher_enabled",
                "real_robot_torque_commanded",
                "ros_publisher_used",
            ]:
                if as_bool(row.get(key)):
                    failed_checks.append(f"{label}_{key}_true")

    comparison_rows = []
    metric_comparison: Dict[str, Dict[str, Any]] = {}

    for key in METRIC_KEYS:
        b = metric_value(baseline_row, key)
        c = metric_value(candidate_row, key)
        delta = None if b is None or c is None else c - b
        metric_comparison[key] = {
            "baseline": b,
            "candidate": c,
            "candidate_minus_baseline": delta,
        }
        comparison_rows.append({
            "metric": key,
            "baseline": "" if b is None else b,
            "candidate": "" if c is None else c,
            "candidate_minus_baseline": "" if delta is None else delta,
        })

    candidate_specific = {
        "candidate_scale": as_float(candidate_row.get("mpc_assisted_candidate_scale")) if candidate_row else None,
        "candidate_row_count": as_int(candidate_row.get("candidate_row_count")) if candidate_row else None,
        "max_tau_candidate_abs": as_float(candidate_row.get("max_tau_candidate_abs")) if candidate_row else None,
        "max_tau_candidate_scaled_abs": as_float(candidate_row.get("max_tau_candidate_scaled_abs")) if candidate_row else None,
        "candidate_available_in_run": as_bool(candidate_row.get("candidate_available_in_run")) if candidate_row else False,
    }

    if candidate_specific["candidate_row_count"] != 100:
        failed_checks.append("candidate_row_count_not_100")
    if candidate_specific["max_tau_candidate_scaled_abs"] is None or candidate_specific["max_tau_candidate_scaled_abs"] <= 0.0:
        failed_checks.append("candidate_scaled_torque_not_positive")

    stability_checks = {
        "baseline_qp_fail_steps_zero": metric_comparison["qp_fail_steps"]["baseline"] == 0,
        "candidate_qp_fail_steps_zero": metric_comparison["qp_fail_steps"]["candidate"] == 0,
        "baseline_saturation_steps_zero": metric_comparison["saturation_steps"]["baseline"] == 0,
        "candidate_saturation_steps_zero": metric_comparison["saturation_steps"]["candidate"] == 0,
        "baseline_min_z_gt_0p22": (metric_comparison["min_z"]["baseline"] or 0.0) > 0.22,
        "candidate_min_z_gt_0p22": (metric_comparison["min_z"]["candidate"] or 0.0) > 0.22,
        "baseline_roll_lt_0p20": (metric_comparison["max_abs_roll"]["baseline"] or 999.0) < 0.20,
        "candidate_roll_lt_0p20": (metric_comparison["max_abs_roll"]["candidate"] or 999.0) < 0.20,
        "baseline_pitch_lt_0p20": (metric_comparison["max_abs_pitch"]["baseline"] or 999.0) < 0.20,
        "candidate_pitch_lt_0p20": (metric_comparison["max_abs_pitch"]["candidate"] or 999.0) < 0.20,
        "baseline_tau_abs_le_23p7": (metric_comparison["max_tau_total_abs"]["baseline"] or 999.0) <= 23.7,
        "candidate_tau_abs_le_23p7": (metric_comparison["max_tau_total_abs"]["candidate"] or 999.0) <= 23.7,
    }

    for key, ok in stability_checks.items():
        if not ok:
            failed_checks.append(f"stability_check_failed:{key}")

    with open(OUT_TABLE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "baseline", "candidate", "candidate_minus_baseline"])
        writer.writeheader()
        writer.writerows(comparison_rows)

    for source_path in [BASELINE_RUNNER, R2_RUNNER, R6_RUNNER]:
        if source_path.exists():
            diff = git(["diff", "--", str(source_path.relative_to(ROOT))])
            if diff.strip():
                failed_checks.append(f"source_file_has_local_diff:{source_path.relative_to(ROOT)}")

    allowed_dirty = {
        "scripts/stage14_5d_r8_closed_loop_ab_packaging.py",
        "docs/stage14_5d_r8_closed_loop_ab_packaging.md",
        "results/logs_sample/stage14_5d_r8_closed_loop_ab_comparison_summary.json",
        "results/logs_sample/stage14_5d_r8_closed_loop_ab_comparison_table.csv",
    }

    summary = {
        "stage": STAGE,
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "pass": False,
        "failed_checks": failed_checks,
        "simulation_only_project": True,
        "hardware_deployment_completed": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "real_robot_torque_commanded": False,
        "ros_publisher_used": False,
        "baseline_source_modified": False,
        "r2_runner_source_modified": False,
        "r6_runner_source_modified": False,
        "mujoco_closed_loop_baseline_mode_evidence_available": r3.get("mujoco_closed_loop_baseline_mode_executed") is True if r3 else False,
        "mujoco_closed_loop_candidate_mode_evidence_available": r7.get("mujoco_closed_loop_candidate_mode_executed") is True if r7 else False,
        "mujoco_closed_loop_ab_packaged_from_existing_runs": True,
        "mujoco_closed_loop_ab_rerun_executed": False,
        "mujoco_sim_data_ctrl_used_in_prior_runs": True,
        "mpc_assisted_candidate_implemented": True,
        "mpc_assisted_candidate_executed_in_prior_run": True,
        "stage14_5d_r3_pass": None if not r3 else r3.get("pass"),
        "stage14_5d_r7_pass": None if not r7 else r7.get("pass"),
        "baseline_summary_csv": str(BASELINE_SUMMARY_CSV.relative_to(ROOT)),
        "baseline_log_csv": str(BASELINE_LOG_CSV.relative_to(ROOT)),
        "candidate_summary_csv": str(CANDIDATE_SUMMARY_CSV.relative_to(ROOT)),
        "candidate_log_csv": str(CANDIDATE_LOG_CSV.relative_to(ROOT)),
        "baseline_log_rows": baseline_log_rows,
        "candidate_log_rows": candidate_log_rows,
        "baseline_control_mode": baseline_row.get("control_mode"),
        "candidate_control_mode": candidate_row.get("control_mode"),
        "candidate_specific": candidate_specific,
        "metric_comparison": metric_comparison,
        "stability_checks": stability_checks,
        "comparison_table_csv": str(OUT_TABLE.relative_to(ROOT)),
        "git": {},
        "generated_files": [
            "scripts/stage14_5d_r8_closed_loop_ab_packaging.py",
            "docs/stage14_5d_r8_closed_loop_ab_packaging.md",
            "results/logs_sample/stage14_5d_r8_closed_loop_ab_comparison_summary.json",
            "results/logs_sample/stage14_5d_r8_closed_loop_ab_comparison_table.csv",
        ],
        "notes": [
            "Packaging/comparison step only.",
            "No MuJoCo rerun is executed in R8.",
            "A/B comparison is packaged from existing R3 baseline and R7 candidate closed-loop simulation runs.",
            "No real robot torque command is sent.",
            "No ROS torque publisher is used.",
            "Frozen baseline source is not modified.",
        ],
    }

    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    doc = [
        "# Stage 14.5D-R8 Closed-loop A/B Packaging",
        "",
        "Scope: simulation-only A/B evidence packaging from existing runs.",
        "",
        "This step compares the existing R3 baseline-mode closed-loop run and R7 MPC-assisted candidate-mode closed-loop run. It does not rerun MuJoCo.",
        "",
        "## Evidence",
        "",
        f"- Summary JSON: `{OUT_SUMMARY.relative_to(ROOT)}`",
        f"- Comparison table CSV: `{OUT_TABLE.relative_to(ROOT)}`",
        f"- Baseline summary CSV: `{BASELINE_SUMMARY_CSV.relative_to(ROOT)}`",
        f"- Candidate summary CSV: `{CANDIDATE_SUMMARY_CSV.relative_to(ROOT)}`",
        "",
        "## Result",
        "",
        f"- pass: {len(failed_checks) == 0}",
        f"- failed_checks: {failed_checks}",
        f"- baseline_log_rows: {baseline_log_rows}",
        f"- candidate_log_rows: {candidate_log_rows}",
        f"- candidate_scale: {candidate_specific['candidate_scale']}",
        f"- candidate_max_tau_candidate_scaled_abs: {candidate_specific['max_tau_candidate_scaled_abs']}",
        "",
        "## Key comparison",
        "",
    ]

    for key in ["min_z", "max_abs_roll", "max_abs_pitch", "max_tau_total_abs", "qp_fail_steps", "saturation_steps"]:
        item = metric_comparison[key]
        doc.append(f"- {key}: baseline={item['baseline']}, candidate={item['candidate']}, delta={item['candidate_minus_baseline']}")

    doc += [
        "",
        "## Boundary",
        "",
        f"- mujoco_closed_loop_ab_packaged_from_existing_runs: {summary['mujoco_closed_loop_ab_packaged_from_existing_runs']}",
        f"- mujoco_closed_loop_ab_rerun_executed: {summary['mujoco_closed_loop_ab_rerun_executed']}",
        f"- real_robot_torque_commanded: {summary['real_robot_torque_commanded']}",
        f"- ros_publisher_used: {summary['ros_publisher_used']}",
        "",
        "This is simulation-only A/B packaging evidence, not hardware-readiness evidence.",
        "",
    ]

    OUT_DOC.write_text("\n".join(doc), encoding="utf-8")

    dirty = git(["status", "--porcelain"])
    dirty_paths = [line[3:].strip() for line in dirty.splitlines() if line.strip()]
    dirty_non_stage = [p for p in dirty_paths if p not in allowed_dirty]
    if dirty_non_stage:
        failed_checks.append("unexpected_dirty_files_present")

    summary["failed_checks"] = failed_checks
    summary["pass"] = len(failed_checks) == 0
    summary["git"] = {
        "branch": git(["branch", "--show-current"]),
        "head": git(["rev-parse", "--short", "HEAD"]),
        "status_porcelain": dirty,
        "dirty_non_stage14_5d_r8": dirty_non_stage,
    }

    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
