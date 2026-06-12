#!/usr/bin/env python3
from pathlib import Path
import csv
import datetime as dt
import json
import subprocess
from typing import Dict, List, Any

ROOT = Path.cwd()
STAGE = "14.5E-R0"

SUMMARY_R6 = ROOT / "results/logs_sample/stage14_5d_r6_derive_mpc_assisted_candidate_runner_summary.json"
SUMMARY_R7 = ROOT / "results/logs_sample/stage14_5d_r7_candidate_mode_guarded_dry_run_summary.json"
SUMMARY_R8 = ROOT / "results/logs_sample/stage14_5d_r8_closed_loop_ab_comparison_summary.json"
SUMMARY_R9 = ROOT / "results/logs_sample/stage14_5d_r9_final_simulation_only_evidence_freeze_summary.json"

R6_RUNNER = ROOT / "scripts/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_runner.py"
CANDIDATE_CSV = ROOT / "results/logs_sample/stage14_5b_offline_mpc_force_to_torque_candidates.csv"

BASELINE_RUNNER = ROOT / "scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py"
R2_RUNNER = ROOT / "scripts/stage14_5d_r2_closed_loop_ab_runner_skeleton.py"

OUT_SUMMARY = ROOT / "results/logs_sample/stage14_5e_r0_candidate_robustness_envelope_preflight_summary.json"
OUT_PLAN_CSV = ROOT / "results/logs_sample/stage14_5e_r0_candidate_robustness_scale_plan.csv"
OUT_DOC = ROOT / "docs/stage14_5e_r0_candidate_robustness_envelope_preflight.md"

PLANNED_SCALES = [0.00, 0.02, 0.05, 0.10]
PLANNED_STEP_POLICY = "repeat"
SCALE_MAX_ALLOWED = 0.25


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


def csv_count_and_columns(path: Path):
    if not path.exists():
        return 0, []
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        columns = list(reader.fieldnames or [])
        count = sum(1 for _ in reader)
    return count, columns


def main() -> int:
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)

    failed_checks = []

    r6 = read_json(SUMMARY_R6)
    r7 = read_json(SUMMARY_R7)
    r8 = read_json(SUMMARY_R8)
    r9 = read_json(SUMMARY_R9)

    previous_stage_pass_map = {
        "stage14_5d_r6": None if r6 is None else r6.get("pass"),
        "stage14_5d_r7": None if r7 is None else r7.get("pass"),
        "stage14_5d_r8": None if r8 is None else r8.get("pass"),
        "stage14_5d_r9": None if r9 is None else r9.get("pass"),
    }

    for key, value in previous_stage_pass_map.items():
        if value is not True:
            failed_checks.append(f"{key}_not_passed_or_missing")

    if not R6_RUNNER.exists():
        failed_checks.append("r6_candidate_runner_missing")

    if not CANDIDATE_CSV.exists():
        failed_checks.append("candidate_csv_missing")

    candidate_row_count, candidate_columns = csv_count_and_columns(CANDIDATE_CSV)
    if candidate_row_count != 100:
        failed_checks.append(f"candidate_csv_row_count_not_100:{candidate_row_count}")

    required_candidate_columns = {
        "step",
        "FR_hip_tau_candidate",
        "FR_thigh_tau_candidate",
        "FR_calf_tau_candidate",
        "FL_hip_tau_candidate",
        "FL_thigh_tau_candidate",
        "FL_calf_tau_candidate",
        "RR_hip_tau_candidate",
        "RR_thigh_tau_candidate",
        "RR_calf_tau_candidate",
        "RL_hip_tau_candidate",
        "RL_thigh_tau_candidate",
        "RL_calf_tau_candidate",
        "tau_abs_max",
        "torque_limit_violation",
    }
    missing_candidate_columns = sorted(required_candidate_columns - set(candidate_columns))
    if missing_candidate_columns:
        failed_checks.append(f"candidate_csv_missing_columns:{missing_candidate_columns}")

    runner_text = R6_RUNNER.read_text(encoding="utf-8") if R6_RUNNER.exists() else ""
    required_runner_tokens = [
        "--control-mode",
        "mpc_assisted_candidate",
        "--allow-mpc-assisted-candidate",
        "--mpc-assisted-candidate-scale",
        "--candidate-csv",
        "--candidate-step-policy",
        "MPC_ASSISTED_CANDIDATE_SCALE_MAX",
        "np.clip",
        "real_robot_torque_commanded",
        "ros_publisher_used",
    ]

    missing_runner_tokens = [token for token in required_runner_tokens if token not in runner_text]
    if missing_runner_tokens:
        failed_checks.append(f"r6_runner_missing_tokens:{missing_runner_tokens}")

    if any(scale < 0.0 for scale in PLANNED_SCALES):
        failed_checks.append("planned_scale_negative")

    if any(scale > SCALE_MAX_ALLOWED for scale in PLANNED_SCALES):
        failed_checks.append("planned_scale_exceeds_max_allowed")

    if PLANNED_SCALES != sorted(PLANNED_SCALES):
        failed_checks.append("planned_scales_not_monotonic")

    if 0.05 not in PLANNED_SCALES:
        failed_checks.append("r7_validated_scale_0p05_missing_from_plan")

    for source_path in [BASELINE_RUNNER, R2_RUNNER, R6_RUNNER]:
        if source_path.exists():
            diff = git(["diff", "--", str(source_path.relative_to(ROOT))])
            if diff.strip():
                failed_checks.append(f"source_file_has_local_diff:{source_path.relative_to(ROOT)}")

    planned_runs = []
    for scale in PLANNED_SCALES:
        planned_runs.append({
            "stage": "14.5E-R1-planned",
            "control_mode": "mpc_assisted_candidate",
            "scale": f"{scale:.2f}",
            "candidate_step_policy": PLANNED_STEP_POLICY,
            "candidate_csv": str(CANDIDATE_CSV.relative_to(ROOT)),
            "expected_total_steps": "2400",
            "execution_status": "planned_not_executed_in_r0",
            "mujoco_execution_in_r0": "False",
            "real_robot_torque_commanded": "False",
            "ros_publisher_used": "False",
            "acceptance_min_z_gt": "0.22",
            "acceptance_abs_roll_lt": "0.20",
            "acceptance_abs_pitch_lt": "0.20",
            "acceptance_max_tau_total_abs_le": "23.7",
            "acceptance_qp_fail_steps_eq": "0",
            "acceptance_saturation_steps_eq": "0",
        })

    with open(OUT_PLAN_CSV, "w", newline="") as f:
        fieldnames = [
            "stage",
            "control_mode",
            "scale",
            "candidate_step_policy",
            "candidate_csv",
            "expected_total_steps",
            "execution_status",
            "mujoco_execution_in_r0",
            "real_robot_torque_commanded",
            "ros_publisher_used",
            "acceptance_min_z_gt",
            "acceptance_abs_roll_lt",
            "acceptance_abs_pitch_lt",
            "acceptance_max_tau_total_abs_le",
            "acceptance_qp_fail_steps_eq",
            "acceptance_saturation_steps_eq",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(planned_runs)

    allowed_dirty = {
        "scripts/stage14_5e_r0_candidate_robustness_envelope_preflight.py",
        "docs/stage14_5e_r0_candidate_robustness_envelope_preflight.md",
        "results/logs_sample/stage14_5e_r0_candidate_robustness_envelope_preflight_summary.json",
        "results/logs_sample/stage14_5e_r0_candidate_robustness_scale_plan.csv",
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
        "previous_stage_pass_map": previous_stage_pass_map,
        "simulation_only_project": True,
        "hardware_deployment_completed": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "real_robot_torque_commanded": False,
        "ros_publisher_used": False,
        "frozen_baseline_source_modified": False,
        "r6_runner_source_modified": False,
        "mujoco_closed_loop_sweep_executed_in_r0": False,
        "mujoco_sim_data_ctrl_used_in_r0": False,
        "mpc_assisted_candidate_implemented": True,
        "mpc_assisted_candidate_executed_in_r0": False,
        "candidate_runner": str(R6_RUNNER.relative_to(ROOT)),
        "candidate_csv": str(CANDIDATE_CSV.relative_to(ROOT)),
        "candidate_csv_row_count": candidate_row_count,
        "candidate_csv_columns": candidate_columns,
        "missing_candidate_columns": missing_candidate_columns,
        "missing_runner_tokens": missing_runner_tokens,
        "planned_scales": PLANNED_SCALES,
        "scale_max_allowed": SCALE_MAX_ALLOWED,
        "candidate_step_policy": PLANNED_STEP_POLICY,
        "planned_run_count": len(planned_runs),
        "scale_plan_csv": str(OUT_PLAN_CSV.relative_to(ROOT)),
        "acceptance_criteria": {
            "total_steps": 2400,
            "qp_fail_steps": 0,
            "saturation_steps": 0,
            "min_z_gt": 0.22,
            "max_abs_roll_lt": 0.20,
            "max_abs_pitch_lt": 0.20,
            "max_tau_total_abs_le": 23.7,
            "real_robot_torque_commanded": False,
            "ros_publisher_used": False,
        },
        "git": {
            "branch": git(["branch", "--show-current"]),
            "head": git(["rev-parse", "--short", "HEAD"]),
            "status_porcelain": dirty,
            "dirty_non_stage14_5e_r0": dirty_non_stage,
        },
        "generated_files": [
            "scripts/stage14_5e_r0_candidate_robustness_envelope_preflight.py",
            "docs/stage14_5e_r0_candidate_robustness_envelope_preflight.md",
            "results/logs_sample/stage14_5e_r0_candidate_robustness_envelope_preflight_summary.json",
            "results/logs_sample/stage14_5e_r0_candidate_robustness_scale_plan.csv",
        ],
        "notes": [
            "Preflight only.",
            "No MuJoCo rollout is executed in R0.",
            "No source runner is modified.",
            "Scale envelope is planned for a future simulation-only robustness sweep.",
            "No real robot torque command is sent.",
            "No ROS torque publisher is used.",
            "No hardware readiness or torque-enable readiness is claimed.",
        ],
    }

    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    doc = [
        "# Stage 14.5E-R0 Candidate Robustness Envelope Preflight",
        "",
        "Scope: simulation-only robustness sweep preflight.",
        "",
        "This step freezes the candidate robustness envelope plan. It does not run MuJoCo and does not modify any runner.",
        "",
        "## Result",
        "",
        f"- pass: {summary['pass']}",
        f"- failed_checks: {summary['failed_checks']}",
        "",
        "## Planned scale envelope",
        "",
    ]

    for scale in PLANNED_SCALES:
        doc.append(f"- scale={scale:.2f}")

    doc += [
        "",
        "## Acceptance criteria for future sweep",
        "",
        "- total_steps = 2400",
        "- qp_fail_steps = 0",
        "- saturation_steps = 0",
        "- min_z > 0.22",
        "- max_abs_roll < 0.20",
        "- max_abs_pitch < 0.20",
        "- max_tau_total_abs <= 23.7",
        "- real_robot_torque_commanded = False",
        "- ros_publisher_used = False",
        "",
        "## Boundary",
        "",
        f"- mujoco_closed_loop_sweep_executed_in_r0: {summary['mujoco_closed_loop_sweep_executed_in_r0']}",
        f"- mujoco_sim_data_ctrl_used_in_r0: {summary['mujoco_sim_data_ctrl_used_in_r0']}",
        f"- real_robot_torque_commanded: {summary['real_robot_torque_commanded']}",
        f"- ros_publisher_used: {summary['ros_publisher_used']}",
        f"- torque_enable_ready: {summary['torque_enable_ready']}",
        "",
        "This is a planning/preflight artifact only. It is not hardware-readiness evidence.",
        "",
        "## Evidence",
        "",
        f"- summary: `{OUT_SUMMARY.relative_to(ROOT)}`",
        f"- scale plan: `{OUT_PLAN_CSV.relative_to(ROOT)}`",
        "",
    ]

    OUT_DOC.write_text("\n".join(doc), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
