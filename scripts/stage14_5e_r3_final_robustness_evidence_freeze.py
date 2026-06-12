#!/usr/bin/env python3
from pathlib import Path
import csv
import datetime as dt
import json
import subprocess
from typing import Dict, List, Any

ROOT = Path.cwd()
STAGE = "14.5E-R3"

SUMMARY_E0 = ROOT / "results/logs_sample/stage14_5e_r0_candidate_robustness_envelope_preflight_summary.json"
SUMMARY_E1 = ROOT / "results/logs_sample/stage14_5e_r1_candidate_robustness_scale_sweep_summary.json"
SUMMARY_E2 = ROOT / "results/logs_sample/stage14_5e_r2_candidate_robustness_sweep_analysis_summary.json"
SUMMARY_D9 = ROOT / "results/logs_sample/stage14_5d_r9_final_simulation_only_evidence_freeze_summary.json"

TABLE_E1 = ROOT / "results/logs_sample/stage14_5e_r1_candidate_robustness_scale_sweep_table.csv"
TABLE_E2 = ROOT / "results/logs_sample/stage14_5e_r2_candidate_robustness_sweep_analysis_table.csv"

BASELINE_RUNNER = ROOT / "scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py"
R2_RUNNER = ROOT / "scripts/stage14_5d_r2_closed_loop_ab_runner_skeleton.py"
R6_RUNNER = ROOT / "scripts/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_runner.py"

OUT_SUMMARY = ROOT / "results/logs_sample/stage14_5e_r3_final_robustness_evidence_freeze_summary.json"
OUT_MANIFEST = ROOT / "results/logs_sample/stage14_5e_r3_final_robustness_evidence_manifest.json"
OUT_DOC = ROOT / "docs/stage14_5e_r3_final_robustness_evidence_freeze.md"


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


def read_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with open(path, "r", newline="") as f:
        return list(csv.DictReader(f))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def main() -> int:
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)

    failed_checks = []

    d9 = read_json(SUMMARY_D9)
    e0 = read_json(SUMMARY_E0)
    e1 = read_json(SUMMARY_E1)
    e2 = read_json(SUMMARY_E2)

    stage_pass_map = {
        "stage14_5d_r9": None if d9 is None else d9.get("pass"),
        "stage14_5e_r0": None if e0 is None else e0.get("pass"),
        "stage14_5e_r1": None if e1 is None else e1.get("pass"),
        "stage14_5e_r2": None if e2 is None else e2.get("pass"),
    }

    for key, val in stage_pass_map.items():
        if val is not True:
            failed_checks.append(f"{key}_not_passed_or_missing")

    e1_rows = read_csv(TABLE_E1)
    e2_rows = read_csv(TABLE_E2)

    if len(e1_rows) != 4:
        failed_checks.append(f"e1_table_row_count_not_4:{len(e1_rows)}")
    if len(e2_rows) != 4:
        failed_checks.append(f"e2_table_row_count_not_4:{len(e2_rows)}")

    e1_aggregate = {} if not e1 else e1.get("aggregate", {})
    e2_aggregate = {} if not e2 else e2.get("aggregate", {})

    if e1_aggregate.get("scale_count") != 4:
        failed_checks.append("e1_scale_count_not_4")
    if e1_aggregate.get("candidate_run_count") != 3:
        failed_checks.append("e1_candidate_run_count_not_3")
    if e1_aggregate.get("baseline_reference_count") != 1:
        failed_checks.append("e1_baseline_reference_count_not_1")
    if e1_aggregate.get("all_scale_entries_pass") is not True:
        failed_checks.append("e1_all_scale_entries_pass_false")

    if e2.get("validated_candidate_scale_max_simulation_only") != 0.1:
        failed_checks.append(f"validated_candidate_scale_max_not_0p1:{None if not e2 else e2.get('validated_candidate_scale_max_simulation_only')}")
    if e2_aggregate.get("all_entries_pass_limits") is not True:
        failed_checks.append("e2_all_entries_pass_limits_false")
    if e2_aggregate.get("total_qp_fail_steps") != 0:
        failed_checks.append("e2_total_qp_fail_steps_nonzero")
    if e2_aggregate.get("total_saturation_steps") != 0:
        failed_checks.append("e2_total_saturation_steps_nonzero")
    if not (e2_aggregate.get("min_z_min_over_entries", 0.0) > 0.22):
        failed_checks.append("e2_min_z_min_not_above_0p22")
    if not (e2_aggregate.get("max_abs_roll_max_over_entries", 999.0) < 0.20):
        failed_checks.append("e2_roll_max_not_below_0p20")
    if not (e2_aggregate.get("max_abs_pitch_max_over_entries", 999.0) < 0.20):
        failed_checks.append("e2_pitch_max_not_below_0p20")
    if not (e2_aggregate.get("max_tau_total_abs_max_over_entries", 999.0) <= 23.7):
        failed_checks.append("e2_tau_max_not_below_limit")

    boundary = {
        "simulation_only_project": True,
        "hardware_deployment_completed": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "real_robot_torque_commanded": False,
        "ros_publisher_used": False,
        "frozen_baseline_source_modified": False,
        "r6_runner_source_modified": False,
        "mujoco_rollout_executed_in_r3": False,
        "mujoco_sim_data_ctrl_used_in_r3": False,
        "mujoco_closed_loop_ab_executed_in_r3": False,
        "analysis_freeze_only": True,
    }

    for key in [
        "hardware_deployment_completed",
        "torque_enable_ready",
        "torque_publisher_enabled",
        "real_robot_torque_commanded",
        "ros_publisher_used",
        "frozen_baseline_source_modified",
        "r6_runner_source_modified",
        "mujoco_rollout_executed_in_r3",
        "mujoco_sim_data_ctrl_used_in_r3",
        "mujoco_closed_loop_ab_executed_in_r3",
    ]:
        if boundary[key] is not False:
            failed_checks.append(f"boundary_{key}_true")

    for source_path in [BASELINE_RUNNER, R2_RUNNER, R6_RUNNER]:
        if source_path.exists():
            diff = git(["diff", "--", rel(source_path)])
            if diff.strip():
                failed_checks.append(f"source_file_has_local_diff:{rel(source_path)}")

    manifest = {
        "stage": STAGE,
        "summaries": {
            "stage14_5d_r9": rel(SUMMARY_D9),
            "stage14_5e_r0": rel(SUMMARY_E0),
            "stage14_5e_r1": rel(SUMMARY_E1),
            "stage14_5e_r2": rel(SUMMARY_E2),
        },
        "tables": {
            "stage14_5e_r1_sweep_table": rel(TABLE_E1),
            "stage14_5e_r2_analysis_table": rel(TABLE_E2),
        },
        "runners": [
            rel(BASELINE_RUNNER),
            rel(R2_RUNNER),
            rel(R6_RUNNER),
        ],
        "scale_specific_artifacts": [] if not e1 else [
            path for path in e1.get("generated_files", [])
            if "stage14_5e_r1_scale_" in path
        ],
        "docs": [
            "docs/stage14_5e_r0_candidate_robustness_envelope_preflight.md",
            "docs/stage14_5e_r1_candidate_robustness_scale_sweep_runner.md",
            "docs/stage14_5e_r2_candidate_robustness_sweep_analysis_packaging.md",
            "docs/stage14_5e_r3_final_robustness_evidence_freeze.md",
        ],
    }

    for group_name, value in [
        ("summaries", manifest["summaries"].values()),
        ("tables", manifest["tables"].values()),
        ("runners", manifest["runners"]),
    ]:
        for path in value:
            if not Path(path).exists():
                failed_checks.append(f"manifest_missing_{group_name}:{path}")

    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    allowed_dirty = {
        "scripts/stage14_5e_r3_final_robustness_evidence_freeze.py",
        "docs/stage14_5e_r3_final_robustness_evidence_freeze.md",
        "results/logs_sample/stage14_5e_r3_final_robustness_evidence_freeze_summary.json",
        "results/logs_sample/stage14_5e_r3_final_robustness_evidence_manifest.json",
    }

    dirty = git(["status", "--porcelain"])
    dirty_paths = parse_porcelain_paths(dirty)
    dirty_non_stage = [p for p in dirty_paths if p not in allowed_dirty]
    if dirty_non_stage:
        failed_checks.append("unexpected_dirty_files_present")

    freeze_metrics = {
        "validated_candidate_scale_max_simulation_only": None if not e2 else e2.get("validated_candidate_scale_max_simulation_only"),
        "planned_scales": None if not e1 else e1.get("planned_scales"),
        "scale_zero_policy": None if not e1 else e1.get("scale_zero_policy"),
        "scale_count": e1_aggregate.get("scale_count"),
        "candidate_run_count": e1_aggregate.get("candidate_run_count"),
        "baseline_reference_count": e1_aggregate.get("baseline_reference_count"),
        "all_scale_entries_pass": e1_aggregate.get("all_scale_entries_pass"),
        "all_entries_pass_limits": e2_aggregate.get("all_entries_pass_limits"),
        "min_z_min_over_entries": e2_aggregate.get("min_z_min_over_entries"),
        "max_abs_roll_max_over_entries": e2_aggregate.get("max_abs_roll_max_over_entries"),
        "max_abs_pitch_max_over_entries": e2_aggregate.get("max_abs_pitch_max_over_entries"),
        "max_tau_total_abs_max_over_entries": e2_aggregate.get("max_tau_total_abs_max_over_entries"),
        "max_tau_candidate_scaled_abs_max_over_candidate_runs": e2_aggregate.get("max_tau_candidate_scaled_abs_max_over_candidate_runs"),
        "total_qp_fail_steps": e2_aggregate.get("total_qp_fail_steps"),
        "total_saturation_steps": e2_aggregate.get("total_saturation_steps"),
    }

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
        "r6_runner_source_modified": False,
        "analysis_freeze_only": True,
        "mujoco_rollout_executed_in_r3": False,
        "mujoco_sim_data_ctrl_used_in_r3": False,
        "mujoco_closed_loop_ab_executed_in_r3": False,
        "validated_candidate_scale_max_simulation_only": freeze_metrics["validated_candidate_scale_max_simulation_only"],
        "freeze_metrics": freeze_metrics,
        "boundary": boundary,
        "evidence_manifest_json": rel(OUT_MANIFEST),
        "git": {
            "branch": git(["branch", "--show-current"]),
            "head": git(["rev-parse", "--short", "HEAD"]),
            "status_porcelain": dirty,
            "dirty_paths": dirty_paths,
            "dirty_non_stage14_5e_r3": dirty_non_stage,
        },
        "generated_files": [
            "scripts/stage14_5e_r3_final_robustness_evidence_freeze.py",
            "docs/stage14_5e_r3_final_robustness_evidence_freeze.md",
            "results/logs_sample/stage14_5e_r3_final_robustness_evidence_freeze_summary.json",
            "results/logs_sample/stage14_5e_r3_final_robustness_evidence_manifest.json",
        ],
        "notes": [
            "Final Stage 14.5E robustness evidence freeze.",
            "No MuJoCo rollout is executed in R3.",
            "Validated scale max is simulation-only and only for the E-R1/E-R2 evidence chain.",
            "No real robot torque command is sent.",
            "No ROS torque publisher is used.",
            "No hardware readiness or torque-enable readiness is claimed.",
        ],
    }

    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    doc = [
        "# Stage 14.5E-R3 Final Robustness Evidence Freeze",
        "",
        "Scope: final freeze of Stage 14.5E robustness evidence.",
        "",
        "This step freezes the E-R0/E-R1/E-R2 robustness evidence chain. It does not run MuJoCo and does not modify any runner.",
        "",
        "## Result",
        "",
        f"- pass: {summary['pass']}",
        f"- failed_checks: {summary['failed_checks']}",
        f"- validated_candidate_scale_max_simulation_only: {freeze_metrics['validated_candidate_scale_max_simulation_only']}",
        f"- planned_scales: {freeze_metrics['planned_scales']}",
        f"- scale_zero_policy: {freeze_metrics['scale_zero_policy']}",
        f"- all_scale_entries_pass: {freeze_metrics['all_scale_entries_pass']}",
        f"- all_entries_pass_limits: {freeze_metrics['all_entries_pass_limits']}",
        "",
        "## Frozen metrics",
        "",
        f"- min_z_min_over_entries: {freeze_metrics['min_z_min_over_entries']}",
        f"- max_abs_roll_max_over_entries: {freeze_metrics['max_abs_roll_max_over_entries']}",
        f"- max_abs_pitch_max_over_entries: {freeze_metrics['max_abs_pitch_max_over_entries']}",
        f"- max_tau_total_abs_max_over_entries: {freeze_metrics['max_tau_total_abs_max_over_entries']}",
        f"- max_tau_candidate_scaled_abs_max_over_candidate_runs: {freeze_metrics['max_tau_candidate_scaled_abs_max_over_candidate_runs']}",
        f"- total_qp_fail_steps: {freeze_metrics['total_qp_fail_steps']}",
        f"- total_saturation_steps: {freeze_metrics['total_saturation_steps']}",
        "",
        "## Stage pass map",
        "",
    ]

    for key, val in stage_pass_map.items():
        doc.append(f"- {key}: {val}")

    doc += [
        "",
        "## Boundary",
        "",
        f"- analysis_freeze_only: {summary['analysis_freeze_only']}",
        f"- mujoco_rollout_executed_in_r3: {summary['mujoco_rollout_executed_in_r3']}",
        f"- mujoco_closed_loop_ab_executed_in_r3: {summary['mujoco_closed_loop_ab_executed_in_r3']}",
        f"- real_robot_torque_commanded: {summary['real_robot_torque_commanded']}",
        f"- ros_publisher_used: {summary['ros_publisher_used']}",
        f"- torque_enable_ready: {summary['torque_enable_ready']}",
        "",
        "This is simulation-only robustness evidence. It is not hardware-readiness evidence.",
        "",
        "## Evidence manifest",
        "",
        f"- `{OUT_MANIFEST.relative_to(ROOT)}`",
        f"- `{OUT_SUMMARY.relative_to(ROOT)}`",
        "",
    ]

    OUT_DOC.write_text("\n".join(doc), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
