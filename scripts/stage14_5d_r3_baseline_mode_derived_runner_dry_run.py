#!/usr/bin/env python3
from pathlib import Path
import csv
import datetime as dt
import json
import subprocess
from typing import Dict, List

ROOT = Path.cwd()
STAGE = "14.5D-R3"

SUMMARY_R2 = ROOT / "results/logs_sample/stage14_5d_r2_closed_loop_ab_runner_skeleton_summary.json"
BASELINE_RUNNER = ROOT / "scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py"
DERIVED_RUNNER = ROOT / "scripts/stage14_5d_r2_closed_loop_ab_runner_skeleton.py"

DERIVED_LOG_CSV = ROOT / "results/logs_sample/stage14_5d_r2_closed_loop_ab_baseline_skeleton_log.csv"
DERIVED_SUMMARY_CSV = ROOT / "results/logs_sample/stage14_5d_r2_closed_loop_ab_baseline_skeleton_summary.csv"

OUT_SUMMARY = ROOT / "results/logs_sample/stage14_5d_r3_baseline_mode_derived_runner_dry_run_summary.json"
OUT_STDOUT = ROOT / "results/logs_sample/stage14_5d_r3_baseline_mode_derived_runner_stdout.txt"
OUT_STDERR = ROOT / "results/logs_sample/stage14_5d_r3_baseline_mode_derived_runner_stderr.txt"
OUT_DOC = ROOT / "docs/stage14_5d_r3_baseline_mode_derived_runner_dry_run.md"


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

    r2 = read_json(SUMMARY_R2)
    if not r2 or r2.get("pass") is not True:
        failed_checks.append("stage14_5d_r2_not_passed_or_missing")

    if not DERIVED_RUNNER.exists():
        failed_checks.append("derived_runner_missing")

    if not BASELINE_RUNNER.exists():
        failed_checks.append("baseline_runner_missing")

    baseline_diff_before = git(["diff", "--", str(BASELINE_RUNNER.relative_to(ROOT))])
    if baseline_diff_before.strip():
        failed_checks.append("baseline_runner_has_local_diff_before_run")

    derived_diff_before = git(["diff", "--", str(DERIVED_RUNNER.relative_to(ROOT))])
    if derived_diff_before.strip():
        failed_checks.append("derived_runner_has_local_diff_before_run")

    cmd = [
        "/usr/bin/python3",
        str(DERIVED_RUNNER.relative_to(ROOT)),
        "--control-mode",
        "baseline",
    ]

    run_returncode = None
    run_timed_out = False

    if "derived_runner_missing" not in failed_checks:
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
            failed_checks.append("derived_runner_baseline_mode_timeout")
    else:
        stdout_text = ""
        stderr_text = ""

    OUT_STDOUT.write_text(stdout_text, encoding="utf-8")
    OUT_STDERR.write_text(stderr_text, encoding="utf-8")

    if run_returncode != 0:
        failed_checks.append(f"derived_runner_returncode_nonzero:{run_returncode}")

    if run_timed_out:
        failed_checks.append("derived_runner_timed_out")

    derived_summary_row = read_single_csv_row(DERIVED_SUMMARY_CSV)
    if not derived_summary_row:
        failed_checks.append("derived_summary_csv_missing_or_empty")

    derived_log_exists = DERIVED_LOG_CSV.exists()
    if not derived_log_exists:
        failed_checks.append("derived_log_csv_missing")

    log_row_count = 0
    log_columns = []
    if DERIVED_LOG_CSV.exists():
        with open(DERIVED_LOG_CSV, "r", newline="") as f:
            reader = csv.DictReader(f)
            log_columns = list(reader.fieldnames or [])
            for _ in reader:
                log_row_count += 1

    total_steps = as_int(derived_summary_row.get("total_steps"))
    if total_steps is not None and log_row_count != total_steps:
        failed_checks.append("log_row_count_mismatch_total_steps")

    pass_value = derived_summary_row.get("pass_test", derived_summary_row.get("pass"))
    baseline_mode_pass = as_bool(pass_value)
    if not baseline_mode_pass:
        failed_checks.append("baseline_mode_summary_pass_false")

    if derived_summary_row.get("stage") != "14.5D-R2":
        failed_checks.append("derived_summary_stage_unexpected")

    if derived_summary_row.get("control_mode") != "baseline":
        failed_checks.append("derived_summary_control_mode_not_baseline")

    for key in [
        "hardware_deployment_completed",
        "torque_enable_ready",
        "torque_publisher_enabled",
        "control_law_changed",
        "mixed_baseline_modified",
        "mpc_assisted_candidate_executed",
    ]:
        if key in derived_summary_row and as_bool(derived_summary_row.get(key)):
            failed_checks.append(f"derived_summary_safety_flag_true:{key}")

    if derived_summary_row.get("mpc_assisted_candidate_scale") not in {"0.0", "0", "0.000000"}:
        failed_checks.append("mpc_assisted_candidate_scale_not_zero")

    baseline_diff_after = git(["diff", "--", str(BASELINE_RUNNER.relative_to(ROOT))])
    if baseline_diff_after.strip():
        failed_checks.append("baseline_runner_has_local_diff_after_run")

    derived_diff_after = git(["diff", "--", str(DERIVED_RUNNER.relative_to(ROOT))])
    if derived_diff_after.strip():
        failed_checks.append("derived_runner_has_local_diff_after_run")

    allowed_dirty = {
        "scripts/stage14_5d_r3_baseline_mode_derived_runner_dry_run.py",
        "docs/stage14_5d_r3_baseline_mode_derived_runner_dry_run.md",
        "results/logs_sample/stage14_5d_r3_baseline_mode_derived_runner_dry_run_summary.json",
        "results/logs_sample/stage14_5d_r3_baseline_mode_derived_runner_stdout.txt",
        "results/logs_sample/stage14_5d_r3_baseline_mode_derived_runner_stderr.txt",
        "results/logs_sample/stage14_5d_r2_closed_loop_ab_baseline_skeleton_log.csv",
        "results/logs_sample/stage14_5d_r2_closed_loop_ab_baseline_skeleton_summary.csv",
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
        "derived_runner_source_modified": False,
        "mujoco_closed_loop_baseline_mode_executed": run_returncode == 0,
        "mujoco_closed_loop_ab_executed": False,
        "mujoco_sim_data_ctrl_used": run_returncode == 0,
        "mpc_assisted_candidate_executed": False,
        "stage14_5d_r2_pass": None if not r2 else r2.get("pass"),
        "command": cmd,
        "run_returncode": run_returncode,
        "run_timed_out": run_timed_out,
        "baseline_runner": str(BASELINE_RUNNER.relative_to(ROOT)),
        "derived_runner": str(DERIVED_RUNNER.relative_to(ROOT)),
        "derived_log_csv": str(DERIVED_LOG_CSV.relative_to(ROOT)),
        "derived_summary_csv": str(DERIVED_SUMMARY_CSV.relative_to(ROOT)),
        "derived_summary_row": derived_summary_row,
        "baseline_mode_pass": baseline_mode_pass,
        "total_steps": total_steps,
        "log_row_count": log_row_count,
        "log_columns": log_columns,
        "key_metrics": {
            "qp_fail_steps": as_int(derived_summary_row.get("qp_fail_steps")),
            "saturation_steps": as_int(derived_summary_row.get("saturation_steps")),
            "min_z": as_float(derived_summary_row.get("min_z")),
            "max_abs_roll": as_float(derived_summary_row.get("max_abs_roll")),
            "max_abs_pitch": as_float(derived_summary_row.get("max_abs_pitch")),
            "max_tau_total_abs": as_float(derived_summary_row.get("max_tau_total_abs")),
            "max_tau_total_raw_abs": as_float(derived_summary_row.get("max_tau_total_raw_abs")),
        },
        "git": {},
        "generated_files": [
            "scripts/stage14_5d_r3_baseline_mode_derived_runner_dry_run.py",
            "docs/stage14_5d_r3_baseline_mode_derived_runner_dry_run.md",
            "results/logs_sample/stage14_5d_r3_baseline_mode_derived_runner_dry_run_summary.json",
            "results/logs_sample/stage14_5d_r3_baseline_mode_derived_runner_stdout.txt",
            "results/logs_sample/stage14_5d_r3_baseline_mode_derived_runner_stderr.txt",
            "results/logs_sample/stage14_5d_r2_closed_loop_ab_baseline_skeleton_log.csv",
            "results/logs_sample/stage14_5d_r2_closed_loop_ab_baseline_skeleton_summary.csv",
        ],
        "notes": [
            "Baseline-mode dry run of the derived skeleton only.",
            "No A/B comparison is executed.",
            "No MPC-assisted candidate mode is executed.",
            "MuJoCo simulation control is used only inside simulation.",
            "No real robot torque command is sent.",
            "No ROS torque publisher is used.",
        ],
    }

    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    doc = [
        "# Stage 14.5D-R3 Baseline-mode Derived Runner Dry Run",
        "",
        "Scope: simulation-only baseline-mode run of the derived Stage 14.5D runner skeleton.",
        "",
        "This step runs the derived runner in explicit baseline mode. It does not execute A/B comparison, does not execute MPC-assisted candidate mode, does not modify the original baseline runner, and does not use ROS torque publishing.",
        "",
        "## Evidence",
        "",
        f"- Summary JSON: `{OUT_SUMMARY.relative_to(ROOT)}`",
        f"- Runner stdout: `{OUT_STDOUT.relative_to(ROOT)}`",
        f"- Runner stderr: `{OUT_STDERR.relative_to(ROOT)}`",
        f"- Derived baseline log CSV: `{DERIVED_LOG_CSV.relative_to(ROOT)}`",
        f"- Derived baseline summary CSV: `{DERIVED_SUMMARY_CSV.relative_to(ROOT)}`",
        "",
        "## Result",
        "",
        f"- pass: {summary['pass']}",
        f"- failed_checks: {summary['failed_checks']}",
        f"- run_returncode: {run_returncode}",
        f"- baseline_mode_pass: {baseline_mode_pass}",
        f"- total_steps: {total_steps}",
        f"- log_row_count: {log_row_count}",
        "",
        "## Safety boundary",
        "",
        f"- simulation_only_project: {summary['simulation_only_project']}",
        f"- hardware_deployment_completed: {summary['hardware_deployment_completed']}",
        f"- torque_enable_ready: {summary['torque_enable_ready']}",
        f"- torque_publisher_enabled: {summary['torque_publisher_enabled']}",
        f"- real_robot_torque_commanded: {summary['real_robot_torque_commanded']}",
        f"- ros_publisher_used: {summary['ros_publisher_used']}",
        f"- mujoco_closed_loop_baseline_mode_executed: {summary['mujoco_closed_loop_baseline_mode_executed']}",
        f"- mujoco_closed_loop_ab_executed: {summary['mujoco_closed_loop_ab_executed']}",
        f"- mujoco_sim_data_ctrl_used: {summary['mujoco_sim_data_ctrl_used']}",
        f"- mpc_assisted_candidate_executed: {summary['mpc_assisted_candidate_executed']}",
        "",
        "This is not MPC-assisted closed-loop evidence and not hardware-readiness evidence.",
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
        "dirty_non_stage14_5d_r3": dirty_non_stage,
    }

    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Refresh doc result after final pass value.
    doc = [line for line in doc]
    doc = [
        line.replace("- pass: False", f"- pass: {summary['pass']}")
            .replace("- failed_checks: []", f"- failed_checks: {summary['failed_checks']}")
        for line in doc
    ]
    OUT_DOC.write_text("\n".join(doc), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
