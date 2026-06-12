#!/usr/bin/env python3
from pathlib import Path
import csv
import datetime as dt
import json
import shutil
import subprocess
from typing import Dict, List, Any

ROOT = Path.cwd()
STAGE = "14.5E-R1"

SUMMARY_R0 = ROOT / "results/logs_sample/stage14_5e_r0_candidate_robustness_envelope_preflight_summary.json"
PLAN_CSV = ROOT / "results/logs_sample/stage14_5e_r0_candidate_robustness_scale_plan.csv"

R6_RUNNER = ROOT / "scripts/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_runner.py"
CANDIDATE_CSV = ROOT / "results/logs_sample/stage14_5b_offline_mpc_force_to_torque_candidates.csv"

R6_CANDIDATE_LOG_CSV = ROOT / "results/logs_sample/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_log.csv"
R6_CANDIDATE_SUMMARY_CSV = ROOT / "results/logs_sample/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_summary.csv"

BASELINE_SUMMARY_CSV = ROOT / "results/logs_sample/stage14_5d_r2_closed_loop_ab_baseline_skeleton_summary.csv"
BASELINE_LOG_CSV = ROOT / "results/logs_sample/stage14_5d_r2_closed_loop_ab_baseline_skeleton_log.csv"

BASELINE_RUNNER = ROOT / "scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py"
R2_RUNNER = ROOT / "scripts/stage14_5d_r2_closed_loop_ab_runner_skeleton.py"

OUT_SUMMARY = ROOT / "results/logs_sample/stage14_5e_r1_candidate_robustness_scale_sweep_summary.json"
OUT_TABLE = ROOT / "results/logs_sample/stage14_5e_r1_candidate_robustness_scale_sweep_table.csv"
OUT_DOC = ROOT / "docs/stage14_5e_r1_candidate_robustness_scale_sweep_runner.md"

TIMEOUT_SECONDS = 300


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


def parse_porcelain_paths(text: str) -> List[str]:
    paths = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.strip().split(maxsplit=1)
        if len(parts) == 2:
            paths.append(parts[1].strip())
        elif len(line) >= 4:
            paths.append(line[3:].strip())
    return paths


def restore_tracked_outputs() -> None:
    subprocess.run(
        [
            "git",
            "restore",
            "--",
            rel(R6_CANDIDATE_LOG_CSV),
            rel(R6_CANDIDATE_SUMMARY_CSV),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def read_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_plan(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with open(path, "r", newline="") as f:
        return list(csv.DictReader(f))


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


def scale_token(scale: float) -> str:
    return f"{scale:.2f}".replace(".", "p")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def extract_metrics(row: Dict[str, str], scale: float, evidence_source: str) -> Dict[str, Any]:
    if evidence_source == "baseline_reference":
        return {
            "control_mode": row.get("control_mode"),
            "pass": as_bool(row.get("pass", row.get("pass_test"))),
            "candidate_scale": scale,
            "candidate_row_count": 0,
            "candidate_available_in_run": False,
            "total_steps": as_int(row.get("total_steps")),
            "min_z": as_float(row.get("min_z")),
            "max_abs_roll": as_float(row.get("max_abs_roll")),
            "max_abs_pitch": as_float(row.get("max_abs_pitch")),
            "max_tau_total_abs": as_float(row.get("max_tau_total_abs")),
            "max_tau_total_raw_abs": as_float(row.get("max_tau_total_raw_abs")),
            "max_tau_candidate_abs": 0.0,
            "max_tau_candidate_scaled_abs": 0.0,
            "qp_fail_steps": as_int(row.get("qp_fail_steps")),
            "saturation_steps": as_int(row.get("saturation_steps")),
            "real_robot_torque_commanded": False,
            "ros_publisher_used": False,
            "hardware_deployment_completed": False,
            "torque_enable_ready": False,
            "torque_publisher_enabled": False,
        }

    return {
        "control_mode": row.get("control_mode"),
        "pass": as_bool(row.get("pass", row.get("pass_test"))),
        "candidate_scale": as_float(row.get("mpc_assisted_candidate_scale")),
        "candidate_row_count": as_int(row.get("candidate_row_count")),
        "candidate_available_in_run": as_bool(row.get("candidate_available_in_run")),
        "total_steps": as_int(row.get("total_steps")),
        "min_z": as_float(row.get("min_z")),
        "max_abs_roll": as_float(row.get("max_abs_roll")),
        "max_abs_pitch": as_float(row.get("max_abs_pitch")),
        "max_tau_total_abs": as_float(row.get("max_tau_total_abs")),
        "max_tau_total_raw_abs": as_float(row.get("max_tau_total_raw_abs")),
        "max_tau_candidate_abs": as_float(row.get("max_tau_candidate_abs")),
        "max_tau_candidate_scaled_abs": as_float(row.get("max_tau_candidate_scaled_abs")),
        "qp_fail_steps": as_int(row.get("qp_fail_steps")),
        "saturation_steps": as_int(row.get("saturation_steps")),
        "real_robot_torque_commanded": as_bool(row.get("real_robot_torque_commanded")),
        "ros_publisher_used": as_bool(row.get("ros_publisher_used")),
        "hardware_deployment_completed": as_bool(row.get("hardware_deployment_completed")),
        "torque_enable_ready": as_bool(row.get("torque_enable_ready")),
        "torque_publisher_enabled": as_bool(row.get("torque_publisher_enabled")),
    }


def validate_metrics(metrics: Dict[str, Any], scale: float, evidence_source: str, log_rows: int) -> List[str]:
    errors = []

    if evidence_source == "baseline_reference":
        if metrics["control_mode"] != "baseline":
            errors.append("baseline_reference_control_mode_not_baseline")
    else:
        if metrics["control_mode"] != "mpc_assisted_candidate":
            errors.append("candidate_control_mode_not_candidate")
        if metrics["candidate_scale"] != scale:
            errors.append(f"candidate_scale_mismatch:{metrics['candidate_scale']}")
        if metrics["candidate_row_count"] != 100:
            errors.append(f"candidate_row_count_not_100:{metrics['candidate_row_count']}")
        if metrics["candidate_available_in_run"] is not True:
            errors.append("candidate_available_false")

    if metrics["pass"] is not True:
        errors.append("summary_pass_false")
    if metrics["total_steps"] != 2400:
        errors.append(f"total_steps_not_2400:{metrics['total_steps']}")
    if log_rows != 2400:
        errors.append(f"log_row_count_not_2400:{log_rows}")
    if metrics["qp_fail_steps"] != 0:
        errors.append(f"qp_fail_steps_nonzero:{metrics['qp_fail_steps']}")
    if metrics["saturation_steps"] != 0:
        errors.append(f"saturation_steps_nonzero:{metrics['saturation_steps']}")
    if metrics["min_z"] is None or metrics["min_z"] <= 0.22:
        errors.append(f"min_z_not_above_0p22:{metrics['min_z']}")
    if metrics["max_abs_roll"] is None or metrics["max_abs_roll"] >= 0.20:
        errors.append(f"max_abs_roll_not_below_0p20:{metrics['max_abs_roll']}")
    if metrics["max_abs_pitch"] is None or metrics["max_abs_pitch"] >= 0.20:
        errors.append(f"max_abs_pitch_not_below_0p20:{metrics['max_abs_pitch']}")
    if metrics["max_tau_total_abs"] is None or metrics["max_tau_total_abs"] > 23.7:
        errors.append(f"max_tau_total_abs_exceeds_23p7:{metrics['max_tau_total_abs']}")

    for key in [
        "real_robot_torque_commanded",
        "ros_publisher_used",
        "hardware_deployment_completed",
        "torque_enable_ready",
        "torque_publisher_enabled",
    ]:
        if metrics[key] is not False:
            errors.append(f"{key}_true")

    if evidence_source == "candidate_run":
        if scale > 0.0:
            if metrics["max_tau_candidate_scaled_abs"] is None or metrics["max_tau_candidate_scaled_abs"] <= 0.0:
                errors.append("scaled_candidate_torque_not_positive_for_nonzero_scale")
        else:
            errors.append("candidate_runner_zero_scale_not_used_by_design")

    if evidence_source == "baseline_reference":
        if abs(metrics["max_tau_candidate_scaled_abs"] or 0.0) > 1e-12:
            errors.append("baseline_reference_scaled_candidate_torque_not_zero")

    return errors


def baseline_reference_scale_zero() -> Dict[str, Any]:
    scale = 0.0
    token = scale_token(scale)

    stdout_path = ROOT / f"results/logs_sample/stage14_5e_r1_scale_{token}_stdout.txt"
    stderr_path = ROOT / f"results/logs_sample/stage14_5e_r1_scale_{token}_stderr.txt"
    summary_copy = ROOT / f"results/logs_sample/stage14_5e_r1_scale_{token}_baseline_reference_summary.csv"
    log_copy = ROOT / f"results/logs_sample/stage14_5e_r1_scale_{token}_baseline_reference_log.csv"

    stdout_path.write_text("scale=0.00 uses existing R3/R2 baseline-reference evidence; no MuJoCo rerun in E-R1 for this reference point.\n", encoding="utf-8")
    stderr_path.write_text("", encoding="utf-8")

    if BASELINE_SUMMARY_CSV.exists():
        shutil.copy2(BASELINE_SUMMARY_CSV, summary_copy)
    if BASELINE_LOG_CSV.exists():
        shutil.copy2(BASELINE_LOG_CSV, log_copy)

    row = read_single_csv_row(BASELINE_SUMMARY_CSV)
    log_rows = csv_row_count(BASELINE_LOG_CSV)
    metrics = extract_metrics(row, scale, "baseline_reference")

    failed_checks = []
    if not BASELINE_SUMMARY_CSV.exists():
        failed_checks.append("baseline_summary_missing")
    if not BASELINE_LOG_CSV.exists():
        failed_checks.append("baseline_log_missing")
    failed_checks.extend(validate_metrics(metrics, scale, "baseline_reference", log_rows))

    return {
        "scale": scale,
        "scale_token": token,
        "evidence_source": "baseline_reference",
        "pass": len(failed_checks) == 0,
        "failed_checks": failed_checks,
        "command": [],
        "run_returncode": None,
        "run_timed_out": False,
        "stdout_path": rel(stdout_path),
        "stderr_path": rel(stderr_path),
        "summary_csv": rel(summary_copy),
        "log_csv": rel(log_copy),
        "log_row_count": log_rows,
        "metrics": metrics,
    }


def run_candidate_scale(scale: float) -> Dict[str, Any]:
    token = scale_token(scale)

    stdout_path = ROOT / f"results/logs_sample/stage14_5e_r1_scale_{token}_stdout.txt"
    stderr_path = ROOT / f"results/logs_sample/stage14_5e_r1_scale_{token}_stderr.txt"
    summary_copy = ROOT / f"results/logs_sample/stage14_5e_r1_scale_{token}_candidate_summary.csv"
    log_copy = ROOT / f"results/logs_sample/stage14_5e_r1_scale_{token}_candidate_log.csv"

    cmd = [
        "/usr/bin/python3",
        rel(R6_RUNNER),
        "--control-mode",
        "mpc_assisted_candidate",
        "--allow-mpc-assisted-candidate",
        "--mpc-assisted-candidate-scale",
        f"{scale:.2f}",
        "--candidate-csv",
        rel(CANDIDATE_CSV),
        "--candidate-step-policy",
        "repeat",
    ]

    failed_checks = []
    run_returncode = None
    run_timed_out = False
    stdout_text = ""
    stderr_text = ""

    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
        run_returncode = proc.returncode
        stdout_text = proc.stdout
        stderr_text = proc.stderr
    except subprocess.TimeoutExpired as exc:
        run_timed_out = True
        stdout_text = exc.stdout or ""
        stderr_text = exc.stderr or ""
        failed_checks.append("run_timeout")

    stdout_path.write_text(stdout_text, encoding="utf-8")
    stderr_path.write_text(stderr_text, encoding="utf-8")

    if run_returncode != 0:
        failed_checks.append(f"run_returncode_nonzero:{run_returncode}")

    row = read_single_csv_row(R6_CANDIDATE_SUMMARY_CSV)
    log_rows = csv_row_count(R6_CANDIDATE_LOG_CSV)

    if R6_CANDIDATE_SUMMARY_CSV.exists():
        shutil.copy2(R6_CANDIDATE_SUMMARY_CSV, summary_copy)
    else:
        failed_checks.append("r6_candidate_summary_missing")

    if R6_CANDIDATE_LOG_CSV.exists():
        shutil.copy2(R6_CANDIDATE_LOG_CSV, log_copy)
    else:
        failed_checks.append("r6_candidate_log_missing")

    metrics = extract_metrics(row, scale, "candidate_run")
    failed_checks.extend(validate_metrics(metrics, scale, "candidate_run", log_rows))

    return {
        "scale": scale,
        "scale_token": token,
        "evidence_source": "candidate_run",
        "pass": len(failed_checks) == 0,
        "failed_checks": failed_checks,
        "command": cmd,
        "run_returncode": run_returncode,
        "run_timed_out": run_timed_out,
        "stdout_path": rel(stdout_path),
        "stderr_path": rel(stderr_path),
        "summary_csv": rel(summary_copy),
        "log_csv": rel(log_copy),
        "log_row_count": log_rows,
        "metrics": metrics,
    }


def main() -> int:
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)

    failed_checks = []

    r0 = read_json(SUMMARY_R0)
    if not r0 or r0.get("pass") is not True:
        failed_checks.append("stage14_5e_r0_not_passed_or_missing")

    plan_rows = read_plan(PLAN_CSV)
    if not plan_rows:
        failed_checks.append("scale_plan_missing_or_empty")

    planned_scales = []
    for row in plan_rows:
        try:
            planned_scales.append(float(row["scale"]))
        except Exception:
            failed_checks.append(f"bad_scale_in_plan:{row}")

    if planned_scales != [0.0, 0.02, 0.05, 0.1]:
        failed_checks.append(f"planned_scales_unexpected:{planned_scales}")

    for path, label in [
        (R6_RUNNER, "r6_runner_missing"),
        (CANDIDATE_CSV, "candidate_csv_missing"),
        (BASELINE_SUMMARY_CSV, "baseline_summary_missing"),
        (BASELINE_LOG_CSV, "baseline_log_missing"),
    ]:
        if not path.exists():
            failed_checks.append(label)

    for source_path in [BASELINE_RUNNER, R2_RUNNER, R6_RUNNER]:
        if source_path.exists():
            diff = git(["diff", "--", rel(source_path)])
            if diff.strip():
                failed_checks.append(f"source_file_has_local_diff_before_sweep:{rel(source_path)}")

    run_results = []
    if not failed_checks:
        for scale in planned_scales:
            if scale == 0.0:
                run_results.append(baseline_reference_scale_zero())
            else:
                run_results.append(run_candidate_scale(scale))

    restore_tracked_outputs()

    for item in run_results:
        if item["pass"] is not True:
            failed_checks.append(f"scale_entry_failed:{item['scale']}:{item['failed_checks']}")

    for source_path in [BASELINE_RUNNER, R2_RUNNER, R6_RUNNER]:
        if source_path.exists():
            diff = git(["diff", "--", rel(source_path)])
            if diff.strip():
                failed_checks.append(f"source_file_has_local_diff_after_sweep:{rel(source_path)}")

    table_rows = []
    for item in run_results:
        m = item["metrics"]
        table_rows.append({
            "scale": f"{item['scale']:.2f}",
            "evidence_source": item["evidence_source"],
            "pass": item["pass"],
            "run_returncode": "" if item["run_returncode"] is None else item["run_returncode"],
            "run_timed_out": item["run_timed_out"],
            "control_mode": m["control_mode"],
            "total_steps": m["total_steps"],
            "candidate_row_count": m["candidate_row_count"],
            "min_z": m["min_z"],
            "max_abs_roll": m["max_abs_roll"],
            "max_abs_pitch": m["max_abs_pitch"],
            "max_tau_total_abs": m["max_tau_total_abs"],
            "max_tau_candidate_abs": m["max_tau_candidate_abs"],
            "max_tau_candidate_scaled_abs": m["max_tau_candidate_scaled_abs"],
            "qp_fail_steps": m["qp_fail_steps"],
            "saturation_steps": m["saturation_steps"],
            "real_robot_torque_commanded": m["real_robot_torque_commanded"],
            "ros_publisher_used": m["ros_publisher_used"],
            "summary_csv": item["summary_csv"],
            "log_csv": item["log_csv"],
            "failed_checks": json.dumps(item["failed_checks"], ensure_ascii=False),
        })

    with open(OUT_TABLE, "w", newline="") as f:
        fieldnames = [
            "scale",
            "evidence_source",
            "pass",
            "run_returncode",
            "run_timed_out",
            "control_mode",
            "total_steps",
            "candidate_row_count",
            "min_z",
            "max_abs_roll",
            "max_abs_pitch",
            "max_tau_total_abs",
            "max_tau_candidate_abs",
            "max_tau_candidate_scaled_abs",
            "qp_fail_steps",
            "saturation_steps",
            "real_robot_torque_commanded",
            "ros_publisher_used",
            "summary_csv",
            "log_csv",
            "failed_checks",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(table_rows)

    aggregate = {
        "scale_count": len(run_results),
        "candidate_run_count": sum(1 for item in run_results if item["evidence_source"] == "candidate_run"),
        "baseline_reference_count": sum(1 for item in run_results if item["evidence_source"] == "baseline_reference"),
        "pass_count": sum(1 for item in run_results if item["pass"]),
        "all_scale_entries_pass": all(item["pass"] for item in run_results) if run_results else False,
        "max_abs_roll_over_entries": max((item["metrics"]["max_abs_roll"] for item in run_results if item["metrics"]["max_abs_roll"] is not None), default=None),
        "max_abs_pitch_over_entries": max((item["metrics"]["max_abs_pitch"] for item in run_results if item["metrics"]["max_abs_pitch"] is not None), default=None),
        "min_z_over_entries": min((item["metrics"]["min_z"] for item in run_results if item["metrics"]["min_z"] is not None), default=None),
        "max_tau_total_abs_over_entries": max((item["metrics"]["max_tau_total_abs"] for item in run_results if item["metrics"]["max_tau_total_abs"] is not None), default=None),
        "max_tau_candidate_scaled_abs_over_candidate_runs": max((item["metrics"]["max_tau_candidate_scaled_abs"] for item in run_results if item["evidence_source"] == "candidate_run" and item["metrics"]["max_tau_candidate_scaled_abs"] is not None), default=None),
        "total_qp_fail_steps": sum((item["metrics"]["qp_fail_steps"] or 0) for item in run_results),
        "total_saturation_steps": sum((item["metrics"]["saturation_steps"] or 0) for item in run_results),
    }

    allowed_dirty = {
        "scripts/stage14_5e_r1_candidate_robustness_scale_sweep_runner.py",
        "docs/stage14_5e_r1_candidate_robustness_scale_sweep_runner.md",
        "results/logs_sample/stage14_5e_r1_candidate_robustness_scale_sweep_summary.json",
        "results/logs_sample/stage14_5e_r1_candidate_robustness_scale_sweep_table.csv",
    }

    for item in run_results:
        allowed_dirty.update({
            item["stdout_path"],
            item["stderr_path"],
            item["summary_csv"],
            item["log_csv"],
        })

    dirty = git(["status", "--porcelain"])
    dirty_paths = parse_porcelain_paths(dirty)
    dirty_non_stage = [p for p in dirty_paths if p not in allowed_dirty]
    if dirty_non_stage:
        failed_checks.append("unexpected_dirty_files_present")

    summary = {
        "stage": STAGE,
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "pass": len(failed_checks) == 0,
        "failed_checks": failed_checks,
        "stage14_5e_r0_pass": None if not r0 else r0.get("pass"),
        "simulation_only_project": True,
        "hardware_deployment_completed": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "real_robot_torque_commanded": False,
        "ros_publisher_used": False,
        "frozen_baseline_source_modified": False,
        "r6_runner_source_modified": False,
        "tracked_r6_generic_outputs_restored_after_sweep": True,
        "mujoco_closed_loop_candidate_sweep_executed": aggregate["candidate_run_count"] > 0,
        "mujoco_closed_loop_ab_executed": False,
        "mujoco_sim_data_ctrl_used_in_candidate_runs": aggregate["candidate_run_count"] > 0,
        "mpc_assisted_candidate_implemented": True,
        "mpc_assisted_candidate_executed": aggregate["candidate_run_count"] > 0,
        "scale_zero_policy": "baseline_reference_existing_r3_r2_evidence_no_candidate_runner_zero_scale",
        "planned_scales": planned_scales,
        "candidate_step_policy": "repeat",
        "candidate_csv": rel(CANDIDATE_CSV),
        "candidate_runner": rel(R6_RUNNER),
        "run_results": run_results,
        "aggregate": aggregate,
        "sweep_table_csv": rel(OUT_TABLE),
        "git": {
            "branch": git(["branch", "--show-current"]),
            "head": git(["rev-parse", "--short", "HEAD"]),
            "status_porcelain": dirty,
            "dirty_paths": dirty_paths,
            "dirty_non_stage14_5e_r1": dirty_non_stage,
        },
        "generated_files": [
            "scripts/stage14_5e_r1_candidate_robustness_scale_sweep_runner.py",
            "docs/stage14_5e_r1_candidate_robustness_scale_sweep_runner.md",
            "results/logs_sample/stage14_5e_r1_candidate_robustness_scale_sweep_summary.json",
            "results/logs_sample/stage14_5e_r1_candidate_robustness_scale_sweep_table.csv",
        ] + [
            item[path_key]
            for item in run_results
            for path_key in ["stdout_path", "stderr_path", "summary_csv", "log_csv"]
        ],
        "notes": [
            "Simulation-only robustness scale sweep.",
            "Scale 0.00 is represented by existing baseline-reference evidence, because the R6 candidate runner rejects zero scale.",
            "Positive scales run the R6 candidate runner in explicit mpc_assisted_candidate mode.",
            "R6 generic output files are restored after copying scale-specific artifacts.",
            "No real robot torque command is sent.",
            "No ROS torque publisher is used.",
            "No hardware readiness or torque-enable readiness is claimed.",
        ],
    }

    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    doc = [
        "# Stage 14.5E-R1 Candidate Robustness Scale Sweep Runner",
        "",
        "Scope: simulation-only candidate robustness scale sweep.",
        "",
        "This step records scale=0.00 as existing baseline-reference evidence, and runs positive candidate scales with the R6 candidate-capable runner.",
        "",
        "## Result",
        "",
        f"- pass: {summary['pass']}",
        f"- failed_checks: {summary['failed_checks']}",
        f"- planned_scales: {planned_scales}",
        f"- pass_count: {aggregate['pass_count']} / {aggregate['scale_count']}",
        f"- candidate_run_count: {aggregate['candidate_run_count']}",
        f"- baseline_reference_count: {aggregate['baseline_reference_count']}",
        f"- min_z_over_entries: {aggregate['min_z_over_entries']}",
        f"- max_abs_roll_over_entries: {aggregate['max_abs_roll_over_entries']}",
        f"- max_abs_pitch_over_entries: {aggregate['max_abs_pitch_over_entries']}",
        f"- max_tau_total_abs_over_entries: {aggregate['max_tau_total_abs_over_entries']}",
        f"- max_tau_candidate_scaled_abs_over_candidate_runs: {aggregate['max_tau_candidate_scaled_abs_over_candidate_runs']}",
        f"- total_qp_fail_steps: {aggregate['total_qp_fail_steps']}",
        f"- total_saturation_steps: {aggregate['total_saturation_steps']}",
        "",
        "## Per-scale outputs",
        "",
    ]

    for item in run_results:
        doc.extend([
            f"### scale={item['scale']:.2f}",
            f"- evidence_source: {item['evidence_source']}",
            f"- pass: {item['pass']}",
            f"- failed_checks: {item['failed_checks']}",
            f"- summary_csv: `{item['summary_csv']}`",
            f"- log_csv: `{item['log_csv']}`",
            "",
        ])

    doc += [
        "## Boundary",
        "",
        f"- simulation_only_project: {summary['simulation_only_project']}",
        f"- mujoco_closed_loop_candidate_sweep_executed: {summary['mujoco_closed_loop_candidate_sweep_executed']}",
        f"- mujoco_closed_loop_ab_executed: {summary['mujoco_closed_loop_ab_executed']}",
        f"- real_robot_torque_commanded: {summary['real_robot_torque_commanded']}",
        f"- ros_publisher_used: {summary['ros_publisher_used']}",
        f"- torque_enable_ready: {summary['torque_enable_ready']}",
        "",
        "This is simulation-only robustness evidence. It is not hardware-readiness evidence.",
        "",
        "## Evidence",
        "",
        f"- summary: `{OUT_SUMMARY.relative_to(ROOT)}`",
        f"- sweep table: `{OUT_TABLE.relative_to(ROOT)}`",
        "",
    ]

    OUT_DOC.write_text("\n".join(doc), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
