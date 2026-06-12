#!/usr/bin/env python3
from pathlib import Path
import csv
import datetime as dt
import json
import subprocess
from typing import Dict, List, Any

ROOT = Path.cwd()
STAGE = "14.5D-R9"

REQUIRED_SUMMARIES = {
    "stage14_5a": ROOT / "results/logs_sample/stage14_5a_mpc_wbc_integration_preflight_summary.json",
    "stage14_5b": ROOT / "results/logs_sample/stage14_5b_offline_mpc_force_to_torque_candidate_summary.json",
    "stage14_5c": ROOT / "results/logs_sample/stage14_5c_mpc_force_reference_offline_qp_summary.json",
    "stage14_5d_r0": ROOT / "results/logs_sample/stage14_5d_r0_closed_loop_ab_anchor_inspection_summary.json",
    "stage14_5d_r1": ROOT / "results/logs_sample/stage14_5d_r1_baseline_runner_structure_inspection_summary.json",
    "stage14_5d_r2": ROOT / "results/logs_sample/stage14_5d_r2_closed_loop_ab_runner_skeleton_summary.json",
    "stage14_5d_r3": ROOT / "results/logs_sample/stage14_5d_r3_baseline_mode_derived_runner_dry_run_summary.json",
    "stage14_5d_r4": ROOT / "results/logs_sample/stage14_5d_r4_mpc_assisted_candidate_gated_negative_test_summary.json",
    "stage14_5d_r5": ROOT / "results/logs_sample/stage14_5d_r5_mpc_candidate_injection_design_inspection_summary.json",
    "stage14_5d_r6": ROOT / "results/logs_sample/stage14_5d_r6_derive_mpc_assisted_candidate_runner_summary.json",
    "stage14_5d_r7": ROOT / "results/logs_sample/stage14_5d_r7_candidate_mode_guarded_dry_run_summary.json",
    "stage14_5d_r8": ROOT / "results/logs_sample/stage14_5d_r8_closed_loop_ab_comparison_summary.json",
}

BASELINE_SUMMARY_CSV = ROOT / "results/logs_sample/stage14_5d_r2_closed_loop_ab_baseline_skeleton_summary.csv"
CANDIDATE_SUMMARY_CSV = ROOT / "results/logs_sample/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_summary.csv"
AB_TABLE_CSV = ROOT / "results/logs_sample/stage14_5d_r8_closed_loop_ab_comparison_table.csv"

OUT_SUMMARY = ROOT / "results/logs_sample/stage14_5d_r9_final_simulation_only_evidence_freeze_summary.json"
OUT_DOC = ROOT / "docs/stage14_5d_r9_final_simulation_only_evidence_freeze.md"
OUT_MANIFEST = ROOT / "results/logs_sample/stage14_5d_r9_final_simulation_only_evidence_manifest.json"


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


def read_table(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with open(path, "r", newline="") as f:
        return list(csv.DictReader(f))


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


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def main() -> int:
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)

    failed_checks = []

    summaries: Dict[str, Any] = {}
    stage_pass_map: Dict[str, Any] = {}

    for key, path in REQUIRED_SUMMARIES.items():
        item = read_json(path)
        summaries[key] = item
        if item is None:
            failed_checks.append(f"missing_summary:{key}")
            stage_pass_map[key] = None
        else:
            stage_pass_map[key] = item.get("pass")
            if item.get("pass") is not True:
                failed_checks.append(f"summary_not_passed:{key}")

    baseline_row = read_single_csv_row(BASELINE_SUMMARY_CSV)
    candidate_row = read_single_csv_row(CANDIDATE_SUMMARY_CSV)
    ab_table = read_table(AB_TABLE_CSV)

    if not baseline_row:
        failed_checks.append("missing_baseline_summary_csv")
    if not candidate_row:
        failed_checks.append("missing_candidate_summary_csv")
    if not ab_table:
        failed_checks.append("missing_ab_table_csv")

    r8 = summaries.get("stage14_5d_r8") or {}
    r7 = summaries.get("stage14_5d_r7") or {}
    r6 = summaries.get("stage14_5d_r6") or {}
    r3 = summaries.get("stage14_5d_r3") or {}

    boundary_flags = {
        "simulation_only_project": True,
        "hardware_deployment_completed": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "real_robot_torque_commanded": False,
        "ros_publisher_used": False,
        "frozen_baseline_source_modified": False,
        "mujoco_closed_loop_baseline_mode_evidence_available": r8.get("mujoco_closed_loop_baseline_mode_evidence_available") is True,
        "mujoco_closed_loop_candidate_mode_evidence_available": r8.get("mujoco_closed_loop_candidate_mode_evidence_available") is True,
        "mujoco_closed_loop_ab_packaged_from_existing_runs": r8.get("mujoco_closed_loop_ab_packaged_from_existing_runs") is True,
        "mujoco_closed_loop_ab_rerun_executed_in_r9": False,
        "mpc_assisted_candidate_implemented": r8.get("mpc_assisted_candidate_implemented") is True,
        "mpc_assisted_candidate_executed_in_prior_run": r8.get("mpc_assisted_candidate_executed_in_prior_run") is True,
    }

    if boundary_flags["hardware_deployment_completed"]:
        failed_checks.append("hardware_deployment_completed_true")
    if boundary_flags["torque_enable_ready"]:
        failed_checks.append("torque_enable_ready_true")
    if boundary_flags["torque_publisher_enabled"]:
        failed_checks.append("torque_publisher_enabled_true")
    if boundary_flags["real_robot_torque_commanded"]:
        failed_checks.append("real_robot_torque_commanded_true")
    if boundary_flags["ros_publisher_used"]:
        failed_checks.append("ros_publisher_used_true")
    if boundary_flags["frozen_baseline_source_modified"]:
        failed_checks.append("frozen_baseline_source_modified_true")

    for key in [
        "mujoco_closed_loop_baseline_mode_evidence_available",
        "mujoco_closed_loop_candidate_mode_evidence_available",
        "mujoco_closed_loop_ab_packaged_from_existing_runs",
        "mpc_assisted_candidate_implemented",
        "mpc_assisted_candidate_executed_in_prior_run",
    ]:
        if boundary_flags[key] is not True:
            failed_checks.append(f"boundary_flag_not_true:{key}")

    baseline_metrics = {
        "control_mode": baseline_row.get("control_mode"),
        "total_steps": as_int(baseline_row.get("total_steps")),
        "pass": as_bool(baseline_row.get("pass", baseline_row.get("pass_test"))),
        "min_z": as_float(baseline_row.get("min_z")),
        "max_abs_roll": as_float(baseline_row.get("max_abs_roll")),
        "max_abs_pitch": as_float(baseline_row.get("max_abs_pitch")),
        "max_tau_total_abs": as_float(baseline_row.get("max_tau_total_abs")),
        "qp_fail_steps": as_int(baseline_row.get("qp_fail_steps")),
        "saturation_steps": as_int(baseline_row.get("saturation_steps")),
    }

    candidate_metrics = {
        "control_mode": candidate_row.get("control_mode"),
        "total_steps": as_int(candidate_row.get("total_steps")),
        "pass": as_bool(candidate_row.get("pass", candidate_row.get("pass_test"))),
        "candidate_scale": as_float(candidate_row.get("mpc_assisted_candidate_scale")),
        "candidate_row_count": as_int(candidate_row.get("candidate_row_count")),
        "candidate_available_in_run": as_bool(candidate_row.get("candidate_available_in_run")),
        "min_z": as_float(candidate_row.get("min_z")),
        "max_abs_roll": as_float(candidate_row.get("max_abs_roll")),
        "max_abs_pitch": as_float(candidate_row.get("max_abs_pitch")),
        "max_tau_total_abs": as_float(candidate_row.get("max_tau_total_abs")),
        "max_tau_candidate_abs": as_float(candidate_row.get("max_tau_candidate_abs")),
        "max_tau_candidate_scaled_abs": as_float(candidate_row.get("max_tau_candidate_scaled_abs")),
        "qp_fail_steps": as_int(candidate_row.get("qp_fail_steps")),
        "saturation_steps": as_int(candidate_row.get("saturation_steps")),
    }

    if baseline_metrics["control_mode"] != "baseline":
        failed_checks.append("baseline_control_mode_not_baseline")
    if candidate_metrics["control_mode"] != "mpc_assisted_candidate":
        failed_checks.append("candidate_control_mode_not_mpc_assisted_candidate")
    if baseline_metrics["total_steps"] != 2400:
        failed_checks.append("baseline_total_steps_not_2400")
    if candidate_metrics["total_steps"] != 2400:
        failed_checks.append("candidate_total_steps_not_2400")
    if baseline_metrics["pass"] is not True:
        failed_checks.append("baseline_pass_false")
    if candidate_metrics["pass"] is not True:
        failed_checks.append("candidate_pass_false")
    if candidate_metrics["candidate_scale"] != 0.05:
        failed_checks.append("candidate_scale_not_0p05")
    if candidate_metrics["candidate_row_count"] != 100:
        failed_checks.append("candidate_row_count_not_100")
    if candidate_metrics["candidate_available_in_run"] is not True:
        failed_checks.append("candidate_available_false")

    stability_freeze = {
        "baseline_qp_fail_steps_zero": baseline_metrics["qp_fail_steps"] == 0,
        "candidate_qp_fail_steps_zero": candidate_metrics["qp_fail_steps"] == 0,
        "baseline_saturation_steps_zero": baseline_metrics["saturation_steps"] == 0,
        "candidate_saturation_steps_zero": candidate_metrics["saturation_steps"] == 0,
        "baseline_min_z_gt_0p22": (baseline_metrics["min_z"] or 0.0) > 0.22,
        "candidate_min_z_gt_0p22": (candidate_metrics["min_z"] or 0.0) > 0.22,
        "baseline_roll_lt_0p20": (baseline_metrics["max_abs_roll"] or 999.0) < 0.20,
        "candidate_roll_lt_0p20": (candidate_metrics["max_abs_roll"] or 999.0) < 0.20,
        "baseline_pitch_lt_0p20": (baseline_metrics["max_abs_pitch"] or 999.0) < 0.20,
        "candidate_pitch_lt_0p20": (candidate_metrics["max_abs_pitch"] or 999.0) < 0.20,
        "baseline_tau_abs_le_23p7": (baseline_metrics["max_tau_total_abs"] or 999.0) <= 23.7,
        "candidate_tau_abs_le_23p7": (candidate_metrics["max_tau_total_abs"] or 999.0) <= 23.7,
        "candidate_scaled_torque_positive": (candidate_metrics["max_tau_candidate_scaled_abs"] or 0.0) > 0.0,
    }

    for key, ok in stability_freeze.items():
        if ok is not True:
            failed_checks.append(f"stability_freeze_failed:{key}")

    evidence_manifest = {
        "required_summaries": {key: rel(path) for key, path in REQUIRED_SUMMARIES.items()},
        "baseline_summary_csv": rel(BASELINE_SUMMARY_CSV),
        "candidate_summary_csv": rel(CANDIDATE_SUMMARY_CSV),
        "ab_table_csv": rel(AB_TABLE_CSV),
        "runners": [
            "scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py",
            "scripts/stage14_5d_r2_closed_loop_ab_runner_skeleton.py",
            "scripts/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_runner.py",
        ],
        "docs": [
            "docs/stage14_5a_mpc_wbc_integration_preflight.md",
            "docs/stage14_5b_offline_mpc_force_to_torque_candidate_check.md",
            "docs/stage14_5c_mpc_force_reference_offline_qp_check.md",
            "docs/stage14_5d_r0_closed_loop_ab_anchor_inspection.md",
            "docs/stage14_5d_r1_baseline_runner_structure_inspection.md",
            "docs/stage14_5d_r2_closed_loop_ab_runner_skeleton.md",
            "docs/stage14_5d_r3_baseline_mode_derived_runner_dry_run.md",
            "docs/stage14_5d_r4_mpc_assisted_candidate_gated_negative_test.md",
            "docs/stage14_5d_r5_mpc_candidate_injection_design_inspection.md",
            "docs/stage14_5d_r6_derive_mpc_assisted_candidate_runner.md",
            "docs/stage14_5d_r7_candidate_mode_guarded_dry_run.md",
            "docs/stage14_5d_r8_closed_loop_ab_packaging.md",
        ],
    }

    OUT_MANIFEST.write_text(json.dumps(evidence_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for item in evidence_manifest["runners"]:
        proc = subprocess.run(
            ["git", "diff", "--", item],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if proc.stdout.strip():
            failed_checks.append(f"runner_has_local_diff:{item}")

    allowed_dirty = {
        "scripts/stage14_5d_r9_final_simulation_only_evidence_freeze.py",
        "docs/stage14_5d_r9_final_simulation_only_evidence_freeze.md",
        "results/logs_sample/stage14_5d_r9_final_simulation_only_evidence_freeze_summary.json",
        "results/logs_sample/stage14_5d_r9_final_simulation_only_evidence_manifest.json",
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
        "stage_pass_map": stage_pass_map,
        "simulation_only_project": True,
        "hardware_deployment_completed": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "real_robot_torque_commanded": False,
        "ros_publisher_used": False,
        "frozen_baseline_source_modified": False,
        "mujoco_closed_loop_ab_final_evidence_packaged": True,
        "mujoco_closed_loop_ab_rerun_executed_in_r9": False,
        "mujoco_sim_data_ctrl_used_in_prior_runs_only": True,
        "mpc_assisted_candidate_implemented": True,
        "mpc_assisted_candidate_executed_in_prior_run": True,
        "boundary_flags": boundary_flags,
        "baseline_metrics": baseline_metrics,
        "candidate_metrics": candidate_metrics,
        "stability_freeze": stability_freeze,
        "evidence_manifest_json": rel(OUT_MANIFEST),
        "ab_table_csv": rel(AB_TABLE_CSV),
        "git": {
            "branch": git(["branch", "--show-current"]),
            "head": git(["rev-parse", "--short", "HEAD"]),
            "status_porcelain": dirty,
            "dirty_non_stage14_5d_r9": dirty_non_stage,
        },
        "generated_files": [
            "scripts/stage14_5d_r9_final_simulation_only_evidence_freeze.py",
            "docs/stage14_5d_r9_final_simulation_only_evidence_freeze.md",
            "results/logs_sample/stage14_5d_r9_final_simulation_only_evidence_freeze_summary.json",
            "results/logs_sample/stage14_5d_r9_final_simulation_only_evidence_manifest.json",
        ],
        "notes": [
            "Final Stage 14.5D simulation-only evidence freeze.",
            "No MuJoCo rerun is executed in R9.",
            "Closed-loop A/B evidence is packaged from existing R3 baseline and R7 candidate simulation runs.",
            "No real robot torque command is sent.",
            "No ROS torque publisher is used.",
            "No hardware readiness or torque-enable readiness is claimed.",
        ],
    }

    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    doc = [
        "# Stage 14.5D-R9 Final Simulation-only Evidence Freeze",
        "",
        "Scope: final evidence freeze for Stage 14.5D.",
        "",
        "This document freezes the simulation-only MPC-to-WBC closed-loop evidence chain. It does not rerun MuJoCo and does not modify any runner.",
        "",
        "## Result",
        "",
        f"- pass: {summary['pass']}",
        f"- failed_checks: {summary['failed_checks']}",
        "",
        "## Stage pass map",
        "",
    ]

    for key, val in stage_pass_map.items():
        doc.append(f"- {key}: {val}")

    doc += [
        "",
        "## Baseline vs candidate evidence",
        "",
        f"- baseline control mode: {baseline_metrics['control_mode']}",
        f"- baseline total steps: {baseline_metrics['total_steps']}",
        f"- candidate control mode: {candidate_metrics['control_mode']}",
        f"- candidate total steps: {candidate_metrics['total_steps']}",
        f"- candidate scale: {candidate_metrics['candidate_scale']}",
        f"- candidate row count: {candidate_metrics['candidate_row_count']}",
        f"- candidate max scaled torque candidate abs: {candidate_metrics['max_tau_candidate_scaled_abs']}",
        "",
        "## Key stability metrics",
        "",
        f"- baseline min_z: {baseline_metrics['min_z']}",
        f"- candidate min_z: {candidate_metrics['min_z']}",
        f"- baseline max_abs_roll: {baseline_metrics['max_abs_roll']}",
        f"- candidate max_abs_roll: {candidate_metrics['max_abs_roll']}",
        f"- baseline max_abs_pitch: {baseline_metrics['max_abs_pitch']}",
        f"- candidate max_abs_pitch: {candidate_metrics['max_abs_pitch']}",
        f"- baseline max_tau_total_abs: {baseline_metrics['max_tau_total_abs']}",
        f"- candidate max_tau_total_abs: {candidate_metrics['max_tau_total_abs']}",
        f"- baseline qp_fail_steps: {baseline_metrics['qp_fail_steps']}",
        f"- candidate qp_fail_steps: {candidate_metrics['qp_fail_steps']}",
        f"- baseline saturation_steps: {baseline_metrics['saturation_steps']}",
        f"- candidate saturation_steps: {candidate_metrics['saturation_steps']}",
        "",
        "## Boundary",
        "",
        f"- simulation_only_project: {summary['simulation_only_project']}",
        f"- hardware_deployment_completed: {summary['hardware_deployment_completed']}",
        f"- torque_enable_ready: {summary['torque_enable_ready']}",
        f"- torque_publisher_enabled: {summary['torque_publisher_enabled']}",
        f"- real_robot_torque_commanded: {summary['real_robot_torque_commanded']}",
        f"- ros_publisher_used: {summary['ros_publisher_used']}",
        f"- frozen_baseline_source_modified: {summary['frozen_baseline_source_modified']}",
        f"- mujoco_closed_loop_ab_final_evidence_packaged: {summary['mujoco_closed_loop_ab_final_evidence_packaged']}",
        f"- mujoco_closed_loop_ab_rerun_executed_in_r9: {summary['mujoco_closed_loop_ab_rerun_executed_in_r9']}",
        "",
        "This is simulation-only evidence. It is not hardware-readiness evidence and does not claim torque-enable readiness.",
        "",
        "## Evidence manifest",
        "",
        f"- `{rel(OUT_MANIFEST)}`",
        f"- `{rel(OUT_SUMMARY)}`",
        f"- `{rel(AB_TABLE_CSV)}`",
        "",
    ]

    OUT_DOC.write_text("\n".join(doc), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
