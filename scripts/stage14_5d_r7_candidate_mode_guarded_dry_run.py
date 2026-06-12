#!/usr/bin/env python3
from pathlib import Path
import csv
import datetime as dt
import json
import subprocess
from typing import Dict, List

ROOT = Path.cwd()
STAGE = "14.5D-R7"

SUMMARY_R6 = ROOT / "results/logs_sample/stage14_5d_r6_derive_mpc_assisted_candidate_runner_summary.json"
R6_RUNNER = ROOT / "scripts/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_runner.py"
BASELINE_RUNNER = ROOT / "scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py"
R2_RUNNER = ROOT / "scripts/stage14_5d_r2_closed_loop_ab_runner_skeleton.py"

CANDIDATE_CSV = ROOT / "results/logs_sample/stage14_5b_offline_mpc_force_to_torque_candidates.csv"
CANDIDATE_SCALE = 0.05

R6_CANDIDATE_LOG_CSV = ROOT / "results/logs_sample/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_log.csv"
R6_CANDIDATE_SUMMARY_CSV = ROOT / "results/logs_sample/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_summary.csv"

OUT_SUMMARY = ROOT / "results/logs_sample/stage14_5d_r7_candidate_mode_guarded_dry_run_summary.json"
OUT_STDOUT = ROOT / "results/logs_sample/stage14_5d_r7_candidate_mode_guarded_dry_run_stdout.txt"
OUT_STDERR = ROOT / "results/logs_sample/stage14_5d_r7_candidate_mode_guarded_dry_run_stderr.txt"
OUT_DOC = ROOT / "docs/stage14_5d_r7_candidate_mode_guarded_dry_run.md"


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


def csv_row_count_and_columns(path: Path):
    if not path.exists():
        return 0, []
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        columns = list(reader.fieldnames or [])
        count = sum(1 for _ in reader)
    return count, columns


def as_bool(v) -> bool:
    return str(v).strip().lower() in {"true", "1", "yes", "y"}


def as_float(v, default=None):
    try:
        return float(v)
    except Exception:
        return default


def as_int(v, default=None):
    try:
        return int(float(v))
    except Exception:
        return default


def main() -> int:
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)

    failed_checks = []

    r6 = read_json(SUMMARY_R6)
    if not r6 or r6.get("pass") is not True:
        failed_checks.append("stage14_5d_r6_not_passed_or_missing")

    if not R6_RUNNER.exists():
        failed_checks.append("r6_runner_missing")

    if not CANDIDATE_CSV.exists():
        failed_checks.append("candidate_csv_missing")

    for source_path in [R6_RUNNER, BASELINE_RUNNER, R2_RUNNER]:
        if source_path.exists():
            diff = git(["diff", "--", str(source_path.relative_to(ROOT))])
            if diff.strip():
                failed_checks.append(f"source_file_has_local_diff_before_run:{source_path.relative_to(ROOT)}")

    cmd = [
        "/usr/bin/python3",
        str(R6_RUNNER.relative_to(ROOT)),
        "--control-mode",
        "mpc_assisted_candidate",
        "--allow-mpc-assisted-candidate",
        "--mpc-assisted-candidate-scale",
        str(CANDIDATE_SCALE),
        "--candidate-csv",
        str(CANDIDATE_CSV.relative_to(ROOT)),
        "--candidate-step-policy",
        "repeat",
    ]

    run_returncode = None
    run_timed_out = False
    stdout_text = ""
    stderr_text = ""

    if "r6_runner_missing" not in failed_checks and "candidate_csv_missing" not in failed_checks:
        try:
            proc = subprocess.run(
                cmd,
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=240,
                check=False,
            )
            run_returncode = proc.returncode
            stdout_text = proc.stdout
            stderr_text = proc.stderr
        except subprocess.TimeoutExpired as exc:
            run_timed_out = True
            run_returncode = None
            stdout_text = exc.stdout or ""
            stderr_text = exc.stderr or ""
            failed_checks.append("candidate_mode_run_timeout")

    OUT_STDOUT.write_text(stdout_text, encoding="utf-8")
    OUT_STDERR.write_text(stderr_text, encoding="utf-8")

    if run_returncode != 0:
        failed_checks.append(f"candidate_mode_returncode_nonzero:{run_returncode}")

    if run_timed_out:
        failed_checks.append("candidate_mode_timed_out")

    row = read_single_csv_row(R6_CANDIDATE_SUMMARY_CSV)
    if not row:
        failed_checks.append("candidate_summary_csv_missing_or_empty")

    log_row_count, log_columns = csv_row_count_and_columns(R6_CANDIDATE_LOG_CSV)
    if log_row_count != 2400:
        failed_checks.append(f"candidate_log_row_count_not_2400:{log_row_count}")

    if row:
        if row.get("stage") != "14.5D-R6":
            failed_checks.append("candidate_summary_stage_unexpected")
        if row.get("control_mode") != "mpc_assisted_candidate":
            failed_checks.append("candidate_summary_control_mode_unexpected")
        if not as_bool(row.get("mpc_assisted_candidate_executed")):
            failed_checks.append("candidate_summary_candidate_executed_false")
        if not as_bool(row.get("candidate_available_in_run")):
            failed_checks.append("candidate_summary_candidate_available_false")
        if as_bool(row.get("hardware_deployment_completed")):
            failed_checks.append("candidate_summary_hardware_deployment_true")
        if as_bool(row.get("torque_enable_ready")):
            failed_checks.append("candidate_summary_torque_enable_ready_true")
        if as_bool(row.get("torque_publisher_enabled")):
            failed_checks.append("candidate_summary_torque_publisher_enabled_true")
        if as_bool(row.get("real_robot_torque_commanded")):
            failed_checks.append("candidate_summary_real_robot_torque_true")
        if as_bool(row.get("ros_publisher_used")):
            failed_checks.append("candidate_summary_ros_publisher_used_true")

    baseline_mode_pass = as_bool(row.get("pass", row.get("pass_test"))) if row else False
    if not baseline_mode_pass:
        failed_checks.append("candidate_summary_pass_false")

    total_steps = as_int(row.get("total_steps")) if row else None
    if total_steps != 2400:
        failed_checks.append(f"candidate_summary_total_steps_not_2400:{total_steps}")

    candidate_row_count = as_int(row.get("candidate_row_count")) if row else None
    if candidate_row_count != 100:
        failed_checks.append(f"candidate_row_count_not_100:{candidate_row_count}")

    candidate_scale = as_float(row.get("mpc_assisted_candidate_scale")) if row else None
    if candidate_scale != CANDIDATE_SCALE:
        failed_checks.append(f"candidate_scale_unexpected:{candidate_scale}")

    required_log_columns = {
        "control_mode",
        "candidate_available",
        "candidate_source_step",
        "candidate_scale",
        "tau_baseline_raw_abs",
        "tau_candidate_abs",
        "tau_candidate_scaled_abs",
        "tau_total_raw_abs",
        "tau_total_abs",
        "saturated",
    }
    missing_log_columns = sorted(required_log_columns - set(log_columns))
    if missing_log_columns:
        failed_checks.append(f"candidate_log_missing_columns:{missing_log_columns}")

    key_metrics = {
        "qp_fail_steps": as_int(row.get("qp_fail_steps")) if row else None,
        "saturation_steps": as_int(row.get("saturation_steps")) if row else None,
        "min_z": as_float(row.get("min_z")) if row else None,
        "max_abs_roll": as_float(row.get("max_abs_roll")) if row else None,
        "max_abs_pitch": as_float(row.get("max_abs_pitch")) if row else None,
        "max_tau_total_abs": as_float(row.get("max_tau_total_abs")) if row else None,
        "max_tau_total_raw_abs": as_float(row.get("max_tau_total_raw_abs")) if row else None,
        "max_tau_baseline_raw_abs": as_float(row.get("max_tau_baseline_raw_abs")) if row else None,
        "max_tau_candidate_abs": as_float(row.get("max_tau_candidate_abs")) if row else None,
        "max_tau_candidate_scaled_abs": as_float(row.get("max_tau_candidate_scaled_abs")) if row else None,
    }

    if key_metrics["qp_fail_steps"] != 0:
        failed_checks.append("qp_fail_steps_nonzero")
    if key_metrics["saturation_steps"] != 0:
        failed_checks.append("saturation_steps_nonzero")
    if key_metrics["min_z"] is None or key_metrics["min_z"] <= 0.22:
        failed_checks.append("min_z_not_above_limit")
    if key_metrics["max_abs_roll"] is None or key_metrics["max_abs_roll"] >= 0.20:
        failed_checks.append("max_abs_roll_not_below_limit")
    if key_metrics["max_abs_pitch"] is None or key_metrics["max_abs_pitch"] >= 0.20:
        failed_checks.append("max_abs_pitch_not_below_limit")
    if key_metrics["max_tau_total_abs"] is None or key_metrics["max_tau_total_abs"] > 23.7:
        failed_checks.append("max_tau_total_abs_exceeds_limit")
    if key_metrics["max_tau_candidate_scaled_abs"] is None or key_metrics["max_tau_candidate_scaled_abs"] <= 0.0:
        failed_checks.append("candidate_scaled_abs_not_positive")

    for source_path in [R6_RUNNER, BASELINE_RUNNER, R2_RUNNER]:
        if source_path.exists():
            diff = git(["diff", "--", str(source_path.relative_to(ROOT))])
            if diff.strip():
                failed_checks.append(f"source_file_has_local_diff_after_run:{source_path.relative_to(ROOT)}")

    allowed_dirty = {
        "scripts/stage14_5d_r7_candidate_mode_guarded_dry_run.py",
        "docs/stage14_5d_r7_candidate_mode_guarded_dry_run.md",
        "results/logs_sample/stage14_5d_r7_candidate_mode_guarded_dry_run_summary.json",
        "results/logs_sample/stage14_5d_r7_candidate_mode_guarded_dry_run_stdout.txt",
        "results/logs_sample/stage14_5d_r7_candidate_mode_guarded_dry_run_stderr.txt",
        "results/logs_sample/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_log.csv",
        "results/logs_sample/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_summary.csv",
    }

    dirty = git(["status", "--porcelain"])
    dirty_paths = [line[3:].strip() for line in dirty.splitlines() if line.strip()]
    dirty_non_stage = [p for p in dirty_paths if p not in allowed_dirty]
    if dirty_non_stage:
        failed_checks.append("unexpected_dirty_files_present")

    summary = {
        "stage": STAGE,
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "pass": len(failed_checks) == 0,
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
        "mujoco_closed_loop_candidate_mode_executed": run_returncode == 0,
        "mujoco_closed_loop_ab_executed": False,
        "mujoco_sim_data_ctrl_used": run_returncode == 0,
        "mpc_assisted_candidate_implemented": True,
        "mpc_assisted_candidate_executed": run_returncode == 0,
        "stage14_5d_r6_pass": None if not r6 else r6.get("pass"),
        "command": cmd,
        "run_returncode": run_returncode,
        "run_timed_out": run_timed_out,
        "candidate_scale": CANDIDATE_SCALE,
        "candidate_step_policy": "repeat",
        "candidate_csv": str(CANDIDATE_CSV.relative_to(ROOT)),
        "candidate_summary_csv": str(R6_CANDIDATE_SUMMARY_CSV.relative_to(ROOT)),
        "candidate_log_csv": str(R6_CANDIDATE_LOG_CSV.relative_to(ROOT)),
        "candidate_summary_row": row,
        "candidate_mode_pass": baseline_mode_pass,
        "candidate_row_count": candidate_row_count,
        "total_steps": total_steps,
        "log_row_count": log_row_count,
        "log_columns": log_columns,
        "missing_log_columns": missing_log_columns,
        "key_metrics": key_metrics,
        "git": {
            "branch": git(["branch", "--show-current"]),
            "head": git(["rev-parse", "--short", "HEAD"]),
            "status_porcelain": dirty,
            "dirty_non_stage14_5d_r7": dirty_non_stage,
        },
        "generated_files": [
            "scripts/stage14_5d_r7_candidate_mode_guarded_dry_run.py",
            "docs/stage14_5d_r7_candidate_mode_guarded_dry_run.md",
            "results/logs_sample/stage14_5d_r7_candidate_mode_guarded_dry_run_summary.json",
            "results/logs_sample/stage14_5d_r7_candidate_mode_guarded_dry_run_stdout.txt",
            "results/logs_sample/stage14_5d_r7_candidate_mode_guarded_dry_run_stderr.txt",
            "results/logs_sample/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_log.csv",
            "results/logs_sample/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_summary.csv",
        ],
        "notes": [
            "Candidate-mode guarded dry run only.",
            "This is not A/B comparison.",
            "MuJoCo simulation control is used only inside simulation.",
            "No real robot torque command is sent.",
            "No ROS torque publisher is used.",
            "Frozen baseline source is not modified.",
        ],
    }

    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    doc = [
        "# Stage 14.5D-R7 Candidate-mode Guarded Dry Run",
        "",
        "Scope: simulation-only candidate-mode dry run.",
        "",
        "This step runs the R6 candidate-capable runner in explicit `mpc_assisted_candidate` mode with a conservative scale of 0.05.",
        "",
        "It does not execute A/B comparison, does not send real robot torque, does not use ROS torque publishing, and does not modify the frozen baseline source.",
        "",
        "## Evidence",
        "",
        f"- Summary JSON: `{OUT_SUMMARY.relative_to(ROOT)}`",
        f"- stdout: `{OUT_STDOUT.relative_to(ROOT)}`",
        f"- stderr: `{OUT_STDERR.relative_to(ROOT)}`",
        f"- Candidate log CSV: `{R6_CANDIDATE_LOG_CSV.relative_to(ROOT)}`",
        f"- Candidate summary CSV: `{R6_CANDIDATE_SUMMARY_CSV.relative_to(ROOT)}`",
        "",
        "## Result",
        "",
        f"- pass: {summary['pass']}",
        f"- failed_checks: {summary['failed_checks']}",
        f"- run_returncode: {run_returncode}",
        f"- candidate_mode_pass: {baseline_mode_pass}",
        f"- total_steps: {total_steps}",
        f"- log_row_count: {log_row_count}",
        f"- candidate_scale: {CANDIDATE_SCALE}",
        "",
        "## Safety boundary",
        "",
        f"- mujoco_closed_loop_candidate_mode_executed: {summary['mujoco_closed_loop_candidate_mode_executed']}",
        f"- mujoco_closed_loop_ab_executed: {summary['mujoco_closed_loop_ab_executed']}",
        f"- mujoco_sim_data_ctrl_used: {summary['mujoco_sim_data_ctrl_used']}",
        f"- real_robot_torque_commanded: {summary['real_robot_torque_commanded']}",
        f"- ros_publisher_used: {summary['ros_publisher_used']}",
        "",
        "This is candidate-mode simulation evidence only, not A/B evidence and not hardware-readiness evidence.",
        "",
    ]
    OUT_DOC.write_text("\n".join(doc), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
