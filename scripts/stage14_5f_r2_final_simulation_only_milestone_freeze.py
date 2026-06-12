#!/usr/bin/env python3
from pathlib import Path
import csv
import datetime as dt
import json
import subprocess
from typing import Any, Dict, List

ROOT = Path.cwd()
STAGE = "14.5F-R2"

F0_SUMMARY = ROOT / "results/logs_sample/stage14_5f_r0_regression_index_release_note_preflight_summary.json"
F0_INDEX = ROOT / "results/logs_sample/stage14_5f_r0_release_evidence_index.csv"
F0_MANIFEST = ROOT / "results/logs_sample/stage14_5f_r0_release_evidence_manifest.json"
F1_SUMMARY = ROOT / "results/logs_sample/stage14_5f_r1_simulation_only_milestone_release_note_draft_summary.json"
F1_KEY_METRICS = ROOT / "results/logs_sample/stage14_5f_r1_release_note_key_metrics.json"
F1_DOC = ROOT / "docs/stage14_5f_r1_simulation_only_milestone_release_note_draft.md"
D9_SUMMARY = ROOT / "results/logs_sample/stage14_5d_r9_final_simulation_only_evidence_freeze_summary.json"
E3_SUMMARY = ROOT / "results/logs_sample/stage14_5e_r3_final_robustness_evidence_freeze_summary.json"

RUNNER_ITEMS = [
    "scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py",
    "scripts/stage14_5d_r2_closed_loop_ab_runner_skeleton.py",
    "scripts/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_runner.py",
]

OUT_SUMMARY = ROOT / "results/logs_sample/stage14_5f_r2_final_simulation_only_milestone_freeze_summary.json"
OUT_MANIFEST = ROOT / "results/logs_sample/stage14_5f_r2_final_simulation_only_milestone_manifest.json"
OUT_DOC = ROOT / "docs/stage14_5f_r2_final_simulation_only_milestone_freeze.md"


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


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with open(path, "r", newline="") as f:
        return list(csv.DictReader(f))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def main() -> int:
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)

    failed_checks: List[str] = []

    f0 = read_json(F0_SUMMARY)
    f1 = read_json(F1_SUMMARY)
    f1_key_metrics = read_json(F1_KEY_METRICS)
    d9 = read_json(D9_SUMMARY)
    e3 = read_json(E3_SUMMARY)
    index_rows = read_csv_rows(F0_INDEX)

    required_inputs = [
        F0_SUMMARY,
        F0_INDEX,
        F0_MANIFEST,
        F1_SUMMARY,
        F1_KEY_METRICS,
        F1_DOC,
        D9_SUMMARY,
        E3_SUMMARY,
    ]

    for path in required_inputs:
        if not path.exists():
            failed_checks.append(f"missing_required_input:{rel(path)}")

    if f0.get("pass") is not True:
        failed_checks.append(f"f0_not_passed:{f0.get('pass')}")
    if f1.get("pass") is not True:
        failed_checks.append(f"f1_not_passed:{f1.get('pass')}")
    if d9.get("pass") is not True:
        failed_checks.append(f"d9_not_passed:{d9.get('pass')}")
    if e3.get("pass") is not True:
        failed_checks.append(f"e3_not_passed:{e3.get('pass')}")

    if len(index_rows) != 47:
        failed_checks.append(f"f0_index_row_count_not_47:{len(index_rows)}")

    missing_index_paths = [row.get("path", "") for row in index_rows if row.get("exists") != "True"]
    if missing_index_paths:
        failed_checks.append("f0_index_has_missing_paths")

    nonpass_summaries = [
        row.get("path", "")
        for row in index_rows
        if row.get("artifact_role") == "stage_summary" and row.get("pass") != "True"
    ]
    if nonpass_summaries:
        failed_checks.append("f0_index_has_nonpass_summaries")

    stage_pass_map = f0.get("stage_pass_map", {})
    if len(stage_pass_map) != 17:
        failed_checks.append(f"stage_pass_map_count_not_17:{len(stage_pass_map)}")
    for key, val in stage_pass_map.items():
        if val is not True:
            failed_checks.append(f"stage_not_passed:{key}:{val}")

    expected_counts = {
        "summary_count": 17,
        "doc_count": 17,
        "key_csv_count": 10,
        "indexed_artifact_count": 47,
    }
    for key, expected in expected_counts.items():
        if f0.get(key) != expected:
            failed_checks.append(f"f0_{key}_unexpected:{f0.get(key)}")
        if f1.get(key) != expected:
            failed_checks.append(f"f1_{key}_unexpected:{f1.get(key)}")

    d9_baseline = d9.get("baseline_metrics", {})
    d9_candidate = d9.get("candidate_metrics", {})
    e3_metrics = e3.get("freeze_metrics", {})

    if d9_baseline.get("total_steps") != 2400 or d9_baseline.get("pass") is not True:
        failed_checks.append("d9_baseline_metrics_invalid")
    if d9_candidate.get("total_steps") != 2400 or d9_candidate.get("pass") is not True:
        failed_checks.append("d9_candidate_metrics_invalid")
    if d9_candidate.get("candidate_scale") != 0.05:
        failed_checks.append(f"d9_candidate_scale_not_0p05:{d9_candidate.get('candidate_scale')}")

    if e3.get("validated_candidate_scale_max_simulation_only") != 0.1:
        failed_checks.append(f"e3_validated_scale_not_0p1:{e3.get('validated_candidate_scale_max_simulation_only')}")
    if f1.get("validated_candidate_scale_max_simulation_only") != 0.1:
        failed_checks.append(f"f1_validated_scale_not_0p1:{f1.get('validated_candidate_scale_max_simulation_only')}")
    if f1_key_metrics.get("validated_candidate_scale_max_simulation_only") != 0.1:
        failed_checks.append("f1_key_metrics_validated_scale_not_0p1")

    robustness_expected = {
        "scale_count": 4,
        "candidate_run_count": 3,
        "baseline_reference_count": 1,
        "all_scale_entries_pass": True,
        "all_entries_pass_limits": True,
        "total_qp_fail_steps": 0,
        "total_saturation_steps": 0,
    }
    for key, expected in robustness_expected.items():
        if e3_metrics.get(key) != expected:
            failed_checks.append(f"e3_metrics_{key}_unexpected:{e3_metrics.get(key)}")

    if not (e3_metrics.get("min_z_min_over_entries", 0.0) > 0.22):
        failed_checks.append("e3_min_z_not_above_0p22")
    if not (e3_metrics.get("max_abs_roll_max_over_entries", 999.0) < 0.20):
        failed_checks.append("e3_roll_not_below_0p20")
    if not (e3_metrics.get("max_abs_pitch_max_over_entries", 999.0) < 0.20):
        failed_checks.append("e3_pitch_not_below_0p20")
    if not (e3_metrics.get("max_tau_total_abs_max_over_entries", 999.0) <= 23.7):
        failed_checks.append("e3_tau_not_below_limit")

    safe_conclusion_text = "Stage 14.5 completed simulation-only MPC/WBC candidate evidence packaging and robustness indexing up to candidate scale 0.10."
    if f1.get("safe_conclusion_text") != safe_conclusion_text:
        failed_checks.append("f1_safe_conclusion_text_mismatch")

    f1_doc_text = F1_DOC.read_text(encoding="utf-8") if F1_DOC.exists() else ""
    for phrase in [
        "simulation-only",
        "hardware_deployment_completed: false",
        "torque_enable_ready: false",
        "real_robot_torque_commanded: false",
        "ros_publisher_used: false",
        "Do not rewrite this as hardware readiness",
        safe_conclusion_text,
    ]:
        if phrase not in f1_doc_text:
            failed_checks.append(f"f1_doc_missing_phrase:{phrase}")

    for runner in RUNNER_ITEMS:
        path = ROOT / runner
        if not path.exists():
            failed_checks.append(f"missing_runner:{runner}")
        else:
            diff = git(["diff", "--", runner])
            if diff.strip():
                failed_checks.append(f"runner_has_local_diff:{runner}")

    boundary = {
        "simulation_only_project": True,
        "hardware_deployment_completed": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "real_robot_torque_commanded": False,
        "ros_publisher_used": False,
        "final_milestone_freeze_only": True,
        "mujoco_rollout_executed_in_f2": False,
        "mujoco_sim_data_ctrl_used_in_f2": False,
        "mujoco_closed_loop_ab_executed_in_f2": False,
        "runner_modified_in_f2": False,
    }

    for key in [
        "hardware_deployment_completed",
        "torque_enable_ready",
        "torque_publisher_enabled",
        "real_robot_torque_commanded",
        "ros_publisher_used",
        "mujoco_rollout_executed_in_f2",
        "mujoco_sim_data_ctrl_used_in_f2",
        "mujoco_closed_loop_ab_executed_in_f2",
        "runner_modified_in_f2",
    ]:
        if boundary[key] is not False:
            failed_checks.append(f"boundary_{key}_true")

    final_metrics = {
        "summary_count": f0.get("summary_count"),
        "doc_count": f0.get("doc_count"),
        "key_csv_count": f0.get("key_csv_count"),
        "indexed_artifact_count": f0.get("indexed_artifact_count"),
        "baseline_2400_step_metrics": d9_baseline,
        "candidate_scale_0p05_2400_step_metrics": d9_candidate,
        "validated_candidate_scale_max_simulation_only": e3.get("validated_candidate_scale_max_simulation_only"),
        "robustness_envelope_metrics": e3_metrics,
        "safe_conclusion_text": safe_conclusion_text,
    }

    manifest = {
        "stage": STAGE,
        "frozen_input_summaries": {
            "f0_summary": rel(F0_SUMMARY),
            "f1_summary": rel(F1_SUMMARY),
            "d9_summary": rel(D9_SUMMARY),
            "e3_summary": rel(E3_SUMMARY),
        },
        "frozen_release_inputs": {
            "f0_index": rel(F0_INDEX),
            "f0_manifest": rel(F0_MANIFEST),
            "f1_key_metrics": rel(F1_KEY_METRICS),
            "f1_release_note_draft": rel(F1_DOC),
        },
        "runner_items": RUNNER_ITEMS,
        "stage_pass_map": stage_pass_map,
        "final_metrics": final_metrics,
        "boundary": boundary,
    }

    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    allowed_dirty = {
        "scripts/stage14_5f_r2_final_simulation_only_milestone_freeze.py",
        "docs/stage14_5f_r2_final_simulation_only_milestone_freeze.md",
        "results/logs_sample/stage14_5f_r2_final_simulation_only_milestone_freeze_summary.json",
        "results/logs_sample/stage14_5f_r2_final_simulation_only_milestone_manifest.json",
    }

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
        "stage_pass_map": stage_pass_map,
        "stage14_5_final_simulation_only_milestone_freeze": True,
        "summary_count": f0.get("summary_count"),
        "doc_count": f0.get("doc_count"),
        "key_csv_count": f0.get("key_csv_count"),
        "indexed_artifact_count": f0.get("indexed_artifact_count"),
        "validated_candidate_scale_max_simulation_only": e3.get("validated_candidate_scale_max_simulation_only"),
        "simulation_only_project": True,
        "hardware_deployment_completed": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "real_robot_torque_commanded": False,
        "ros_publisher_used": False,
        "final_milestone_freeze_only": True,
        "mujoco_rollout_executed_in_f2": False,
        "mujoco_sim_data_ctrl_used_in_f2": False,
        "mujoco_closed_loop_ab_executed_in_f2": False,
        "runner_modified_in_f2": False,
        "final_metrics": final_metrics,
        "boundary": boundary,
        "final_manifest_json": rel(OUT_MANIFEST),
        "final_doc_md": rel(OUT_DOC),
        "safe_conclusion_text": safe_conclusion_text,
        "forbidden_claims": [
            "hardware ready",
            "torque enable ready",
            "real robot torque execution",
            "MPC directly outputs joint torque",
        ],
        "git": {
            "branch": git(["branch", "--show-current"]),
            "head": git(["rev-parse", "--short", "HEAD"]),
            "status_porcelain": dirty,
            "dirty_paths": dirty_paths,
            "dirty_non_stage14_5f_r2": dirty_non_stage,
        },
        "generated_files": [
            "scripts/stage14_5f_r2_final_simulation_only_milestone_freeze.py",
            "docs/stage14_5f_r2_final_simulation_only_milestone_freeze.md",
            "results/logs_sample/stage14_5f_r2_final_simulation_only_milestone_freeze_summary.json",
            "results/logs_sample/stage14_5f_r2_final_simulation_only_milestone_manifest.json",
        ],
        "notes": [
            "Final Stage 14.5 simulation-only milestone freeze.",
            "No MuJoCo rollout is executed in F-R2.",
            "No source runner is modified.",
            "No real robot torque command is sent.",
            "No ROS torque publisher is used.",
            "No hardware readiness or torque-enable readiness is claimed.",
        ],
    }

    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    doc_lines = [
        "# Stage 14.5F-R2 Final Simulation-Only Milestone Freeze",
        "",
        "Scope: final freeze of Stage 14.5 simulation-only MPC/WBC candidate evidence.",
        "",
        "This step freezes the Stage 14.5A-F-R1 evidence chain. It does not run MuJoCo, does not modify any runner, and does not claim hardware readiness.",
        "",
        "## Result",
        "",
        f"- pass: {summary['pass']}",
        f"- failed_checks: {summary['failed_checks']}",
        f"- stage14_5_final_simulation_only_milestone_freeze: {summary['stage14_5_final_simulation_only_milestone_freeze']}",
        f"- validated_candidate_scale_max_simulation_only: {summary['validated_candidate_scale_max_simulation_only']}",
        "",
        "## Evidence index counts",
        "",
        f"- summary_count: {summary['summary_count']}",
        f"- doc_count: {summary['doc_count']}",
        f"- key_csv_count: {summary['key_csv_count']}",
        f"- indexed_artifact_count: {summary['indexed_artifact_count']}",
        "",
        "## Baseline evidence",
        "",
        f"- control_mode: {d9_baseline.get('control_mode')}",
        f"- total_steps: {d9_baseline.get('total_steps')}",
        f"- pass: {d9_baseline.get('pass')}",
        f"- min_z: {d9_baseline.get('min_z')}",
        f"- max_abs_roll: {d9_baseline.get('max_abs_roll')}",
        f"- max_abs_pitch: {d9_baseline.get('max_abs_pitch')}",
        f"- max_tau_total_abs: {d9_baseline.get('max_tau_total_abs')}",
        f"- qp_fail_steps: {d9_baseline.get('qp_fail_steps')}",
        f"- saturation_steps: {d9_baseline.get('saturation_steps')}",
        "",
        "## MPC-assisted candidate evidence",
        "",
        f"- control_mode: {d9_candidate.get('control_mode')}",
        f"- total_steps: {d9_candidate.get('total_steps')}",
        f"- candidate_scale: {d9_candidate.get('candidate_scale')}",
        f"- candidate_row_count: {d9_candidate.get('candidate_row_count')}",
        f"- pass: {d9_candidate.get('pass')}",
        f"- min_z: {d9_candidate.get('min_z')}",
        f"- max_abs_roll: {d9_candidate.get('max_abs_roll')}",
        f"- max_abs_pitch: {d9_candidate.get('max_abs_pitch')}",
        f"- max_tau_total_abs: {d9_candidate.get('max_tau_total_abs')}",
        f"- max_tau_candidate_abs: {d9_candidate.get('max_tau_candidate_abs')}",
        f"- max_tau_candidate_scaled_abs: {d9_candidate.get('max_tau_candidate_scaled_abs')}",
        f"- qp_fail_steps: {d9_candidate.get('qp_fail_steps')}",
        f"- saturation_steps: {d9_candidate.get('saturation_steps')}",
        "",
        "## Robustness envelope evidence",
        "",
        f"- planned_scales: {e3_metrics.get('planned_scales')}",
        f"- scale_zero_policy: {e3_metrics.get('scale_zero_policy')}",
        f"- validated_candidate_scale_max_simulation_only: {e3_metrics.get('validated_candidate_scale_max_simulation_only')}",
        f"- scale_count: {e3_metrics.get('scale_count')}",
        f"- candidate_run_count: {e3_metrics.get('candidate_run_count')}",
        f"- baseline_reference_count: {e3_metrics.get('baseline_reference_count')}",
        f"- min_z_min_over_entries: {e3_metrics.get('min_z_min_over_entries')}",
        f"- max_abs_roll_max_over_entries: {e3_metrics.get('max_abs_roll_max_over_entries')}",
        f"- max_abs_pitch_max_over_entries: {e3_metrics.get('max_abs_pitch_max_over_entries')}",
        f"- max_tau_total_abs_max_over_entries: {e3_metrics.get('max_tau_total_abs_max_over_entries')}",
        f"- max_tau_candidate_scaled_abs_max_over_candidate_runs: {e3_metrics.get('max_tau_candidate_scaled_abs_max_over_candidate_runs')}",
        f"- total_qp_fail_steps: {e3_metrics.get('total_qp_fail_steps')}",
        f"- total_saturation_steps: {e3_metrics.get('total_saturation_steps')}",
        "",
        "## Boundary",
        "",
        "- simulation_only_project: true",
        "- hardware_deployment_completed: false",
        "- torque_enable_ready: false",
        "- torque_publisher_enabled: false",
        "- real_robot_torque_commanded: false",
        "- ros_publisher_used: false",
        "- final_milestone_freeze_only: true",
        "- mujoco_rollout_executed_in_f2: false",
        "- mujoco_sim_data_ctrl_used_in_f2: false",
        "- mujoco_closed_loop_ab_executed_in_f2: false",
        "- runner_modified_in_f2: false",
        "",
        "## Safe final conclusion",
        "",
        safe_conclusion_text,
        "",
        "Do not rewrite this as hardware readiness, torque-enable readiness, real robot torque execution, or direct MPC joint-torque output.",
        "",
        "## Frozen artifacts",
        "",
        f"- final summary: `{OUT_SUMMARY.relative_to(ROOT)}`",
        f"- final manifest: `{OUT_MANIFEST.relative_to(ROOT)}`",
        f"- final doc: `{OUT_DOC.relative_to(ROOT)}`",
        "",
    ]

    OUT_DOC.write_text("\n".join(doc_lines), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
