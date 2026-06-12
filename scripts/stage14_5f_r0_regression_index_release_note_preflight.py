#!/usr/bin/env python3
from pathlib import Path
import csv
import datetime as dt
import json
import subprocess
from typing import Dict, List, Any

ROOT = Path.cwd()
STAGE = "14.5F-R0"

SUMMARY_ITEMS = [
    ("14.5A", "results/logs_sample/stage14_5a_mpc_wbc_integration_preflight_summary.json"),
    ("14.5B", "results/logs_sample/stage14_5b_offline_mpc_force_to_torque_candidate_summary.json"),
    ("14.5C", "results/logs_sample/stage14_5c_mpc_force_reference_offline_qp_summary.json"),
    ("14.5D-R0", "results/logs_sample/stage14_5d_r0_closed_loop_ab_anchor_inspection_summary.json"),
    ("14.5D-R1", "results/logs_sample/stage14_5d_r1_baseline_runner_structure_inspection_summary.json"),
    ("14.5D-R2", "results/logs_sample/stage14_5d_r2_closed_loop_ab_runner_skeleton_summary.json"),
    ("14.5D-R3", "results/logs_sample/stage14_5d_r3_baseline_mode_derived_runner_dry_run_summary.json"),
    ("14.5D-R4", "results/logs_sample/stage14_5d_r4_mpc_assisted_candidate_gated_negative_test_summary.json"),
    ("14.5D-R5", "results/logs_sample/stage14_5d_r5_mpc_candidate_injection_design_inspection_summary.json"),
    ("14.5D-R6", "results/logs_sample/stage14_5d_r6_derive_mpc_assisted_candidate_runner_summary.json"),
    ("14.5D-R7", "results/logs_sample/stage14_5d_r7_candidate_mode_guarded_dry_run_summary.json"),
    ("14.5D-R8", "results/logs_sample/stage14_5d_r8_closed_loop_ab_comparison_summary.json"),
    ("14.5D-R9", "results/logs_sample/stage14_5d_r9_final_simulation_only_evidence_freeze_summary.json"),
    ("14.5E-R0", "results/logs_sample/stage14_5e_r0_candidate_robustness_envelope_preflight_summary.json"),
    ("14.5E-R1", "results/logs_sample/stage14_5e_r1_candidate_robustness_scale_sweep_summary.json"),
    ("14.5E-R2", "results/logs_sample/stage14_5e_r2_candidate_robustness_sweep_analysis_summary.json"),
    ("14.5E-R3", "results/logs_sample/stage14_5e_r3_final_robustness_evidence_freeze_summary.json"),
]

DOC_ITEMS = [
    ("14.5A", "docs/stage14_5a_mpc_wbc_integration_preflight.md"),
    ("14.5B", "docs/stage14_5b_offline_mpc_force_to_torque_candidate_check.md"),
    ("14.5C", "docs/stage14_5c_mpc_force_reference_offline_qp_check.md"),
    ("14.5D-R0", "docs/stage14_5d_r0_closed_loop_ab_anchor_inspection.md"),
    ("14.5D-R1", "docs/stage14_5d_r1_baseline_runner_structure_inspection.md"),
    ("14.5D-R2", "docs/stage14_5d_r2_closed_loop_ab_runner_skeleton.md"),
    ("14.5D-R3", "docs/stage14_5d_r3_baseline_mode_derived_runner_dry_run.md"),
    ("14.5D-R4", "docs/stage14_5d_r4_mpc_assisted_candidate_gated_negative_test.md"),
    ("14.5D-R5", "docs/stage14_5d_r5_mpc_candidate_injection_design_inspection.md"),
    ("14.5D-R6", "docs/stage14_5d_r6_derive_mpc_assisted_candidate_runner.md"),
    ("14.5D-R7", "docs/stage14_5d_r7_candidate_mode_guarded_dry_run.md"),
    ("14.5D-R8", "docs/stage14_5d_r8_closed_loop_ab_packaging.md"),
    ("14.5D-R9", "docs/stage14_5d_r9_final_simulation_only_evidence_freeze.md"),
    ("14.5E-R0", "docs/stage14_5e_r0_candidate_robustness_envelope_preflight.md"),
    ("14.5E-R1", "docs/stage14_5e_r1_candidate_robustness_scale_sweep_runner.md"),
    ("14.5E-R2", "docs/stage14_5e_r2_candidate_robustness_sweep_analysis_packaging.md"),
    ("14.5E-R3", "docs/stage14_5e_r3_final_robustness_evidence_freeze.md"),
]

KEY_CSV_ITEMS = [
    ("14.5B", "results/logs_sample/stage14_5b_offline_mpc_force_to_torque_candidates.csv"),
    ("14.5C", "results/logs_sample/stage14_5c_mpc_force_reference_offline_qp_check.csv"),
    ("14.5D-R3", "results/logs_sample/stage14_5d_r2_closed_loop_ab_baseline_skeleton_log.csv"),
    ("14.5D-R3", "results/logs_sample/stage14_5d_r2_closed_loop_ab_baseline_skeleton_summary.csv"),
    ("14.5D-R7", "results/logs_sample/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_log.csv"),
    ("14.5D-R7", "results/logs_sample/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_summary.csv"),
    ("14.5D-R8", "results/logs_sample/stage14_5d_r8_closed_loop_ab_comparison_table.csv"),
    ("14.5E-R0", "results/logs_sample/stage14_5e_r0_candidate_robustness_scale_plan.csv"),
    ("14.5E-R1", "results/logs_sample/stage14_5e_r1_candidate_robustness_scale_sweep_table.csv"),
    ("14.5E-R2", "results/logs_sample/stage14_5e_r2_candidate_robustness_sweep_analysis_table.csv"),
]

RUNNER_ITEMS = [
    "scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py",
    "scripts/stage14_5d_r2_closed_loop_ab_runner_skeleton.py",
    "scripts/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_runner.py",
]

OUT_SUMMARY = ROOT / "results/logs_sample/stage14_5f_r0_regression_index_release_note_preflight_summary.json"
OUT_INDEX_CSV = ROOT / "results/logs_sample/stage14_5f_r0_release_evidence_index.csv"
OUT_MANIFEST = ROOT / "results/logs_sample/stage14_5f_r0_release_evidence_manifest.json"
OUT_DOC = ROOT / "docs/stage14_5f_r0_regression_index_release_note_preflight.md"


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


def csv_row_count(path: Path) -> int:
    if not path.exists():
        return 0
    with open(path, "r", newline="") as f:
        return sum(1 for _ in csv.DictReader(f))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def classify_artifact(path: str) -> str:
    if path.endswith(".json"):
        return "summary_or_manifest_json"
    if path.endswith(".csv"):
        return "table_or_log_csv"
    if path.endswith(".md"):
        return "doc"
    if path.endswith(".py"):
        return "runner_or_script"
    return "other"


def main() -> int:
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)

    failed_checks = []

    stage_pass_map: Dict[str, Any] = {}
    indexed_rows: List[Dict[str, Any]] = []

    for stage, path_str in SUMMARY_ITEMS:
        path = ROOT / path_str
        data = read_json(path)
        exists = path.exists()
        passed = None if data is None else data.get("pass")
        stage_pass_map[stage] = passed

        if not exists:
            failed_checks.append(f"missing_summary:{stage}:{path_str}")
        elif passed is not True:
            failed_checks.append(f"summary_not_passed:{stage}:{passed}")

        indexed_rows.append({
            "stage": stage,
            "artifact_role": "stage_summary",
            "artifact_type": classify_artifact(path_str),
            "path": path_str,
            "exists": exists,
            "pass": passed,
            "row_count": "",
            "notes": "required pass-bearing summary",
        })

    for stage, path_str in DOC_ITEMS:
        path = ROOT / path_str
        exists = path.exists()
        if not exists:
            failed_checks.append(f"missing_doc:{stage}:{path_str}")

        indexed_rows.append({
            "stage": stage,
            "artifact_role": "stage_doc",
            "artifact_type": classify_artifact(path_str),
            "path": path_str,
            "exists": exists,
            "pass": "",
            "row_count": "",
            "notes": "stage documentation",
        })

    for stage, path_str in KEY_CSV_ITEMS:
        path = ROOT / path_str
        exists = path.exists()
        rows = csv_row_count(path) if exists else 0
        if not exists:
            failed_checks.append(f"missing_key_csv:{stage}:{path_str}")
        if exists and rows <= 0:
            failed_checks.append(f"empty_key_csv:{stage}:{path_str}")

        indexed_rows.append({
            "stage": stage,
            "artifact_role": "key_csv_evidence",
            "artifact_type": classify_artifact(path_str),
            "path": path_str,
            "exists": exists,
            "pass": "",
            "row_count": rows,
            "notes": "key CSV evidence for release index",
        })

    for path_str in RUNNER_ITEMS:
        path = ROOT / path_str
        exists = path.exists()
        if not exists:
            failed_checks.append(f"missing_runner:{path_str}")
        else:
            diff = git(["diff", "--", path_str])
            if diff.strip():
                failed_checks.append(f"runner_has_local_diff:{path_str}")

        indexed_rows.append({
            "stage": "runner",
            "artifact_role": "source_runner",
            "artifact_type": classify_artifact(path_str),
            "path": path_str,
            "exists": exists,
            "pass": "",
            "row_count": "",
            "notes": "must remain unmodified in F-R0",
        })

    d9 = read_json(ROOT / "results/logs_sample/stage14_5d_r9_final_simulation_only_evidence_freeze_summary.json") or {}
    e3 = read_json(ROOT / "results/logs_sample/stage14_5e_r3_final_robustness_evidence_freeze_summary.json") or {}

    frozen_metrics = {
        "stage14_5d_complete": d9.get("pass") is True,
        "stage14_5e_complete": e3.get("pass") is True,
        "validated_candidate_scale_max_simulation_only": e3.get("validated_candidate_scale_max_simulation_only"),
        "robustness_freeze_metrics": e3.get("freeze_metrics", {}),
        "d9_baseline_metrics": d9.get("baseline_metrics", {}),
        "d9_candidate_metrics": d9.get("candidate_metrics", {}),
    }

    if frozen_metrics["stage14_5d_complete"] is not True:
        failed_checks.append("stage14_5d_final_freeze_not_complete")
    if frozen_metrics["stage14_5e_complete"] is not True:
        failed_checks.append("stage14_5e_final_freeze_not_complete")
    if frozen_metrics["validated_candidate_scale_max_simulation_only"] != 0.1:
        failed_checks.append("validated_candidate_scale_max_not_0p1")

    boundary = {
        "simulation_only_project": True,
        "hardware_deployment_completed": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "real_robot_torque_commanded": False,
        "ros_publisher_used": False,
        "release_index_preflight_only": True,
        "mujoco_rollout_executed_in_f0": False,
        "mujoco_sim_data_ctrl_used_in_f0": False,
        "runner_modified_in_f0": False,
    }

    for key in [
        "hardware_deployment_completed",
        "torque_enable_ready",
        "torque_publisher_enabled",
        "real_robot_torque_commanded",
        "ros_publisher_used",
        "mujoco_rollout_executed_in_f0",
        "mujoco_sim_data_ctrl_used_in_f0",
        "runner_modified_in_f0",
    ]:
        if boundary[key] is not False:
            failed_checks.append(f"boundary_{key}_true")

    with open(OUT_INDEX_CSV, "w", newline="") as f:
        fieldnames = ["stage", "artifact_role", "artifact_type", "path", "exists", "pass", "row_count", "notes"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(indexed_rows)

    manifest = {
        "stage": STAGE,
        "summary_items": [{"stage": s, "path": p} for s, p in SUMMARY_ITEMS],
        "doc_items": [{"stage": s, "path": p} for s, p in DOC_ITEMS],
        "key_csv_items": [{"stage": s, "path": p} for s, p in KEY_CSV_ITEMS],
        "runner_items": RUNNER_ITEMS,
        "release_evidence_index_csv": rel(OUT_INDEX_CSV),
        "frozen_metrics": frozen_metrics,
        "boundary": boundary,
    }

    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    allowed_dirty = {
        "scripts/stage14_5f_r0_regression_index_release_note_preflight.py",
        "docs/stage14_5f_r0_regression_index_release_note_preflight.md",
        "results/logs_sample/stage14_5f_r0_regression_index_release_note_preflight_summary.json",
        "results/logs_sample/stage14_5f_r0_release_evidence_index.csv",
        "results/logs_sample/stage14_5f_r0_release_evidence_manifest.json",
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
        "summary_count": len(SUMMARY_ITEMS),
        "doc_count": len(DOC_ITEMS),
        "key_csv_count": len(KEY_CSV_ITEMS),
        "runner_count": len(RUNNER_ITEMS),
        "indexed_artifact_count": len(indexed_rows),
        "simulation_only_project": True,
        "hardware_deployment_completed": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "real_robot_torque_commanded": False,
        "ros_publisher_used": False,
        "release_index_preflight_only": True,
        "mujoco_rollout_executed_in_f0": False,
        "mujoco_sim_data_ctrl_used_in_f0": False,
        "runner_modified_in_f0": False,
        "frozen_metrics": frozen_metrics,
        "boundary": boundary,
        "release_evidence_index_csv": rel(OUT_INDEX_CSV),
        "release_evidence_manifest_json": rel(OUT_MANIFEST),
        "git": {
            "branch": git(["branch", "--show-current"]),
            "head": git(["rev-parse", "--short", "HEAD"]),
            "status_porcelain": dirty,
            "dirty_paths": dirty_paths,
            "dirty_non_stage14_5f_r0": dirty_non_stage,
        },
        "generated_files": [
            "scripts/stage14_5f_r0_regression_index_release_note_preflight.py",
            "docs/stage14_5f_r0_regression_index_release_note_preflight.md",
            "results/logs_sample/stage14_5f_r0_regression_index_release_note_preflight_summary.json",
            "results/logs_sample/stage14_5f_r0_release_evidence_index.csv",
            "results/logs_sample/stage14_5f_r0_release_evidence_manifest.json",
        ],
        "notes": [
            "Release index preflight only.",
            "No MuJoCo rollout is executed in F-R0.",
            "No source runner is modified.",
            "No real robot torque command is sent.",
            "No ROS torque publisher is used.",
            "No hardware readiness or torque-enable readiness is claimed.",
        ],
    }

    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    doc = [
        "# Stage 14.5F-R0 Regression Index and Release Note Preflight",
        "",
        "Scope: simulation-only release evidence index preflight.",
        "",
        "This step indexes Stage 14.5A-E summaries, docs, key CSV outputs, and runner sources. It does not run MuJoCo and does not modify any runner.",
        "",
        "## Result",
        "",
        f"- pass: {summary['pass']}",
        f"- failed_checks: {summary['failed_checks']}",
        f"- summary_count: {summary['summary_count']}",
        f"- doc_count: {summary['doc_count']}",
        f"- key_csv_count: {summary['key_csv_count']}",
        f"- indexed_artifact_count: {summary['indexed_artifact_count']}",
        "",
        "## Frozen release metrics",
        "",
        f"- stage14_5d_complete: {frozen_metrics['stage14_5d_complete']}",
        f"- stage14_5e_complete: {frozen_metrics['stage14_5e_complete']}",
        f"- validated_candidate_scale_max_simulation_only: {frozen_metrics['validated_candidate_scale_max_simulation_only']}",
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
        f"- release_index_preflight_only: {summary['release_index_preflight_only']}",
        f"- mujoco_rollout_executed_in_f0: {summary['mujoco_rollout_executed_in_f0']}",
        f"- mujoco_sim_data_ctrl_used_in_f0: {summary['mujoco_sim_data_ctrl_used_in_f0']}",
        f"- runner_modified_in_f0: {summary['runner_modified_in_f0']}",
        f"- real_robot_torque_commanded: {summary['real_robot_torque_commanded']}",
        f"- ros_publisher_used: {summary['ros_publisher_used']}",
        f"- torque_enable_ready: {summary['torque_enable_ready']}",
        "",
        "This is an index/preflight artifact only. It is not hardware-readiness evidence.",
        "",
        "## Evidence",
        "",
        f"- release evidence index: `{OUT_INDEX_CSV.relative_to(ROOT)}`",
        f"- release evidence manifest: `{OUT_MANIFEST.relative_to(ROOT)}`",
        f"- summary: `{OUT_SUMMARY.relative_to(ROOT)}`",
        "",
    ]

    OUT_DOC.write_text("\n".join(doc), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
