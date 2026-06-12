#!/usr/bin/env python3
from pathlib import Path
import csv
import datetime as dt
import json
import subprocess
from typing import Any, Dict, List

ROOT = Path.cwd()
STAGE = "14.5F-R1"

F0_SUMMARY = ROOT / "results/logs_sample/stage14_5f_r0_regression_index_release_note_preflight_summary.json"
F0_INDEX = ROOT / "results/logs_sample/stage14_5f_r0_release_evidence_index.csv"
F0_MANIFEST = ROOT / "results/logs_sample/stage14_5f_r0_release_evidence_manifest.json"
D9_SUMMARY = ROOT / "results/logs_sample/stage14_5d_r9_final_simulation_only_evidence_freeze_summary.json"
E3_SUMMARY = ROOT / "results/logs_sample/stage14_5e_r3_final_robustness_evidence_freeze_summary.json"

BASELINE_RUNNER = ROOT / "scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py"
R2_RUNNER = ROOT / "scripts/stage14_5d_r2_closed_loop_ab_runner_skeleton.py"
R6_RUNNER = ROOT / "scripts/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_runner.py"

OUT_SUMMARY = ROOT / "results/logs_sample/stage14_5f_r1_simulation_only_milestone_release_note_draft_summary.json"
OUT_KEY_METRICS = ROOT / "results/logs_sample/stage14_5f_r1_release_note_key_metrics.json"
OUT_DOC = ROOT / "docs/stage14_5f_r1_simulation_only_milestone_release_note_draft.md"


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


def metric_line(name: str, value: Any) -> str:
    return f"- {name}: {value}"


def main() -> int:
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)

    failed_checks: List[str] = []

    f0 = read_json(F0_SUMMARY)
    f0_manifest = read_json(F0_MANIFEST)
    d9 = read_json(D9_SUMMARY)
    e3 = read_json(E3_SUMMARY)
    index_rows = read_csv_rows(F0_INDEX)

    required_inputs = [F0_SUMMARY, F0_INDEX, F0_MANIFEST, D9_SUMMARY, E3_SUMMARY]
    for path in required_inputs:
        if not path.exists():
            failed_checks.append(f"missing_required_input:{rel(path)}")

    if f0.get("pass") is not True:
        failed_checks.append(f"f0_not_passed:{f0.get('pass')}")
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

    for runner in [BASELINE_RUNNER, R2_RUNNER, R6_RUNNER]:
        if not runner.exists():
            failed_checks.append(f"missing_runner:{rel(runner)}")
        else:
            diff = git(["diff", "--", rel(runner)])
            if diff.strip():
                failed_checks.append(f"runner_has_local_diff:{rel(runner)}")

    d9_baseline = d9.get("baseline_metrics", {})
    d9_candidate = d9.get("candidate_metrics", {})
    e3_metrics = e3.get("freeze_metrics", {})

    key_metrics = {
        "stage14_5a_to_f0_summary_count": f0.get("summary_count"),
        "stage14_5a_to_f0_doc_count": f0.get("doc_count"),
        "stage14_5a_to_f0_key_csv_count": f0.get("key_csv_count"),
        "stage14_5a_to_f0_indexed_artifact_count": f0.get("indexed_artifact_count"),
        "baseline_2400_step_metrics": d9_baseline,
        "candidate_scale_0p05_2400_step_metrics": d9_candidate,
        "candidate_robustness_envelope_metrics": e3_metrics,
        "validated_candidate_scale_max_simulation_only": e3.get("validated_candidate_scale_max_simulation_only"),
        "release_index_csv": rel(F0_INDEX),
        "release_manifest_json": rel(F0_MANIFEST),
    }

    if key_metrics["validated_candidate_scale_max_simulation_only"] != 0.1:
        failed_checks.append("validated_candidate_scale_max_not_0p1")

    if e3_metrics.get("total_qp_fail_steps") != 0:
        failed_checks.append("robustness_total_qp_fail_steps_nonzero")
    if e3_metrics.get("total_saturation_steps") != 0:
        failed_checks.append("robustness_total_saturation_steps_nonzero")
    if not (e3_metrics.get("min_z_min_over_entries", 0.0) > 0.22):
        failed_checks.append("robustness_min_z_not_above_0p22")
    if not (e3_metrics.get("max_abs_roll_max_over_entries", 999.0) < 0.20):
        failed_checks.append("robustness_roll_not_below_0p20")
    if not (e3_metrics.get("max_abs_pitch_max_over_entries", 999.0) < 0.20):
        failed_checks.append("robustness_pitch_not_below_0p20")
    if not (e3_metrics.get("max_tau_total_abs_max_over_entries", 999.0) <= 23.7):
        failed_checks.append("robustness_tau_not_below_limit")

    boundary = {
        "simulation_only_project": True,
        "hardware_deployment_completed": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "real_robot_torque_commanded": False,
        "ros_publisher_used": False,
        "release_note_draft_only": True,
        "mujoco_rollout_executed_in_f1": False,
        "mujoco_sim_data_ctrl_used_in_f1": False,
        "runner_modified_in_f1": False,
    }

    for key in [
        "hardware_deployment_completed",
        "torque_enable_ready",
        "torque_publisher_enabled",
        "real_robot_torque_commanded",
        "ros_publisher_used",
        "mujoco_rollout_executed_in_f1",
        "mujoco_sim_data_ctrl_used_in_f1",
        "runner_modified_in_f1",
    ]:
        if boundary[key] is not False:
            failed_checks.append(f"boundary_{key}_true")

    OUT_KEY_METRICS.write_text(json.dumps(key_metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    release_note_lines = [
        "# Stage 14.5 Simulation-Only MPC/WBC Milestone Release Note Draft",
        "",
        "Status: draft release note generated from frozen local evidence.",
        "",
        "## Scope",
        "",
        "Stage 14.5 connects the offline MPC contact-force reference evidence to simulation-only WBC/QP-side candidate evaluation and robustness packaging.",
        "",
        "The evidence is simulation-only. It does not claim hardware deployment, torque-enable readiness, ROS torque publishing, or real robot torque execution.",
        "",
        "## Completed evidence chain",
        "",
        "- Stage 14.5A: MPC/WBC integration preflight inventory.",
        "- Stage 14.5B: offline MPC contact-force to joint-torque candidate evidence through the robot model mapping layer.",
        "- Stage 14.5C: offline MPC force-reference QP check.",
        "- Stage 14.5D: explicit closed-loop baseline/candidate simulation-only evidence packaging.",
        "- Stage 14.5E: candidate robustness envelope evidence through scale 0.10.",
        "- Stage 14.5F-R0: release evidence index preflight.",
        "",
        "## Baseline closed-loop evidence",
        "",
        metric_line("control_mode", d9_baseline.get("control_mode")),
        metric_line("total_steps", d9_baseline.get("total_steps")),
        metric_line("pass", d9_baseline.get("pass")),
        metric_line("min_z", d9_baseline.get("min_z")),
        metric_line("max_abs_roll", d9_baseline.get("max_abs_roll")),
        metric_line("max_abs_pitch", d9_baseline.get("max_abs_pitch")),
        metric_line("max_tau_total_abs", d9_baseline.get("max_tau_total_abs")),
        metric_line("qp_fail_steps", d9_baseline.get("qp_fail_steps")),
        metric_line("saturation_steps", d9_baseline.get("saturation_steps")),
        "",
        "## MPC-assisted candidate closed-loop evidence",
        "",
        metric_line("control_mode", d9_candidate.get("control_mode")),
        metric_line("total_steps", d9_candidate.get("total_steps")),
        metric_line("candidate_scale", d9_candidate.get("candidate_scale")),
        metric_line("candidate_row_count", d9_candidate.get("candidate_row_count")),
        metric_line("pass", d9_candidate.get("pass")),
        metric_line("min_z", d9_candidate.get("min_z")),
        metric_line("max_abs_roll", d9_candidate.get("max_abs_roll")),
        metric_line("max_abs_pitch", d9_candidate.get("max_abs_pitch")),
        metric_line("max_tau_total_abs", d9_candidate.get("max_tau_total_abs")),
        metric_line("max_tau_candidate_abs", d9_candidate.get("max_tau_candidate_abs")),
        metric_line("max_tau_candidate_scaled_abs", d9_candidate.get("max_tau_candidate_scaled_abs")),
        metric_line("qp_fail_steps", d9_candidate.get("qp_fail_steps")),
        metric_line("saturation_steps", d9_candidate.get("saturation_steps")),
        "",
        "## Robustness envelope evidence",
        "",
        metric_line("planned_scales", e3_metrics.get("planned_scales")),
        metric_line("scale_zero_policy", e3_metrics.get("scale_zero_policy")),
        metric_line("validated_candidate_scale_max_simulation_only", e3_metrics.get("validated_candidate_scale_max_simulation_only")),
        metric_line("scale_count", e3_metrics.get("scale_count")),
        metric_line("candidate_run_count", e3_metrics.get("candidate_run_count")),
        metric_line("baseline_reference_count", e3_metrics.get("baseline_reference_count")),
        metric_line("all_scale_entries_pass", e3_metrics.get("all_scale_entries_pass")),
        metric_line("all_entries_pass_limits", e3_metrics.get("all_entries_pass_limits")),
        metric_line("min_z_min_over_entries", e3_metrics.get("min_z_min_over_entries")),
        metric_line("max_abs_roll_max_over_entries", e3_metrics.get("max_abs_roll_max_over_entries")),
        metric_line("max_abs_pitch_max_over_entries", e3_metrics.get("max_abs_pitch_max_over_entries")),
        metric_line("max_tau_total_abs_max_over_entries", e3_metrics.get("max_tau_total_abs_max_over_entries")),
        metric_line("max_tau_candidate_scaled_abs_max_over_candidate_runs", e3_metrics.get("max_tau_candidate_scaled_abs_max_over_candidate_runs")),
        metric_line("total_qp_fail_steps", e3_metrics.get("total_qp_fail_steps")),
        metric_line("total_saturation_steps", e3_metrics.get("total_saturation_steps")),
        "",
        "## Release evidence index",
        "",
        metric_line("summary_count", f0.get("summary_count")),
        metric_line("doc_count", f0.get("doc_count")),
        metric_line("key_csv_count", f0.get("key_csv_count")),
        metric_line("indexed_artifact_count", f0.get("indexed_artifact_count")),
        metric_line("release_evidence_index_csv", rel(F0_INDEX)),
        metric_line("release_evidence_manifest_json", rel(F0_MANIFEST)),
        "",
        "## Boundary statements",
        "",
        "- simulation_only_project: true",
        "- hardware_deployment_completed: false",
        "- torque_enable_ready: false",
        "- torque_publisher_enabled: false",
        "- real_robot_torque_commanded: false",
        "- ros_publisher_used: false",
        "- mujoco_rollout_executed_in_f1: false",
        "- runner_modified_in_f1: false",
        "",
        "## Safe conclusion text",
        "",
        "Stage 14.5 completed simulation-only MPC/WBC candidate evidence packaging and robustness indexing up to candidate scale 0.10.",
        "",
        "Do not rewrite this as hardware readiness, torque-enable readiness, real robot torque execution, or direct MPC joint-torque output.",
        "",
    ]

    OUT_DOC.write_text("\n".join(release_note_lines), encoding="utf-8")

    allowed_dirty = {
        "scripts/stage14_5f_r1_simulation_only_milestone_release_note_draft.py",
        "docs/stage14_5f_r1_simulation_only_milestone_release_note_draft.md",
        "results/logs_sample/stage14_5f_r1_simulation_only_milestone_release_note_draft_summary.json",
        "results/logs_sample/stage14_5f_r1_release_note_key_metrics.json",
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
        "source_inputs": {
            "f0_summary": rel(F0_SUMMARY),
            "f0_index": rel(F0_INDEX),
            "f0_manifest": rel(F0_MANIFEST),
            "d9_summary": rel(D9_SUMMARY),
            "e3_summary": rel(E3_SUMMARY),
        },
        "stage14_5_release_note_draft_generated": True,
        "summary_count": f0.get("summary_count"),
        "doc_count": f0.get("doc_count"),
        "key_csv_count": f0.get("key_csv_count"),
        "indexed_artifact_count": f0.get("indexed_artifact_count"),
        "validated_candidate_scale_max_simulation_only": e3.get("validated_candidate_scale_max_simulation_only"),
        "key_metrics_json": rel(OUT_KEY_METRICS),
        "release_note_draft_md": rel(OUT_DOC),
        "simulation_only_project": True,
        "hardware_deployment_completed": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "real_robot_torque_commanded": False,
        "ros_publisher_used": False,
        "release_note_draft_only": True,
        "mujoco_rollout_executed_in_f1": False,
        "mujoco_sim_data_ctrl_used_in_f1": False,
        "runner_modified_in_f1": False,
        "boundary": boundary,
        "key_metrics": key_metrics,
        "safe_conclusion_text": "Stage 14.5 completed simulation-only MPC/WBC candidate evidence packaging and robustness indexing up to candidate scale 0.10.",
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
            "dirty_non_stage14_5f_r1": dirty_non_stage,
        },
        "generated_files": [
            "scripts/stage14_5f_r1_simulation_only_milestone_release_note_draft.py",
            "docs/stage14_5f_r1_simulation_only_milestone_release_note_draft.md",
            "results/logs_sample/stage14_5f_r1_simulation_only_milestone_release_note_draft_summary.json",
            "results/logs_sample/stage14_5f_r1_release_note_key_metrics.json",
        ],
        "notes": [
            "Release note draft only.",
            "No MuJoCo rollout is executed in F-R1.",
            "No source runner is modified.",
            "No real robot torque command is sent.",
            "No ROS torque publisher is used.",
            "No hardware readiness or torque-enable readiness is claimed.",
        ],
    }

    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
