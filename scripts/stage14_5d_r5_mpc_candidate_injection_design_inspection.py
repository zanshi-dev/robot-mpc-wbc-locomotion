#!/usr/bin/env python3
from pathlib import Path
import csv
import datetime as dt
import json
import re
import subprocess
from typing import Dict, List

ROOT = Path.cwd()
STAGE = "14.5D-R5"

SUMMARY_R4 = ROOT / "results/logs_sample/stage14_5d_r4_mpc_assisted_candidate_gated_negative_test_summary.json"
SUMMARY_R3 = ROOT / "results/logs_sample/stage14_5d_r3_baseline_mode_derived_runner_dry_run_summary.json"
SUMMARY_14_5B = ROOT / "results/logs_sample/stage14_5b_offline_mpc_force_to_torque_candidate_summary.json"
SUMMARY_14_5C = ROOT / "results/logs_sample/stage14_5c_mpc_force_reference_offline_qp_summary.json"

DERIVED_RUNNER = ROOT / "scripts/stage14_5d_r2_closed_loop_ab_runner_skeleton.py"
BASELINE_RUNNER = ROOT / "scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py"

CANDIDATE_CSV = ROOT / "results/logs_sample/stage14_5b_offline_mpc_force_to_torque_candidates.csv"
QP_CSV = ROOT / "results/logs_sample/stage14_5c_mpc_force_reference_offline_qp_check.csv"
BASELINE_MODE_LOG_CSV = ROOT / "results/logs_sample/stage14_5d_r2_closed_loop_ab_baseline_skeleton_log.csv"
BASELINE_MODE_SUMMARY_CSV = ROOT / "results/logs_sample/stage14_5d_r2_closed_loop_ab_baseline_skeleton_summary.csv"

OUT_SUMMARY = ROOT / "results/logs_sample/stage14_5d_r5_mpc_candidate_injection_design_inspection_summary.json"
OUT_DOC = ROOT / "docs/stage14_5d_r5_mpc_candidate_injection_design_inspection.md"
OUT_ANCHORS = ROOT / "results/logs_sample/stage14_5d_r5_mpc_candidate_injection_design_anchors.txt"


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


def csv_info(path: Path) -> Dict:
    if not path.exists():
        return {
            "exists": False,
            "row_count": 0,
            "columns": [],
            "first_row": {},
        }
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        columns = list(reader.fieldnames or [])
        first_row = {}
        row_count = 0
        for row in reader:
            row_count += 1
            if not first_row:
                first_row = dict(row)
    return {
        "exists": True,
        "row_count": row_count,
        "columns": columns,
        "first_row": first_row,
    }


def find_lines(text: str, patterns: Dict[str, List[str]]) -> Dict[str, List[Dict]]:
    lines = text.splitlines()
    out = {k: [] for k in patterns}
    for i, line in enumerate(lines, start=1):
        for key, pats in patterns.items():
            if any(re.search(p, line) for p in pats):
                out[key].append({"lineno": i, "text": line.rstrip()})
    return out


def snippet(text: str, lineno: int, radius: int = 4) -> List[str]:
    lines = text.splitlines()
    start = max(1, lineno - radius)
    end = min(len(lines), lineno + radius)
    return [f"{i}: {lines[i - 1]}" for i in range(start, end + 1)]


def main() -> int:
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)

    failed_checks = []

    r4 = read_json(SUMMARY_R4)
    r3 = read_json(SUMMARY_R3)
    s14_5b = read_json(SUMMARY_14_5B)
    s14_5c = read_json(SUMMARY_14_5C)

    if not r4 or r4.get("pass") is not True:
        failed_checks.append("stage14_5d_r4_not_passed_or_missing")
    if not r3 or r3.get("pass") is not True:
        failed_checks.append("stage14_5d_r3_not_passed_or_missing")
    if not s14_5b or s14_5b.get("pass") is not True:
        failed_checks.append("stage14_5b_not_passed_or_missing")
    if not s14_5c or s14_5c.get("pass") is not True:
        failed_checks.append("stage14_5c_not_passed_or_missing")

    if not DERIVED_RUNNER.exists():
        failed_checks.append("derived_runner_missing")
        derived_text = ""
    else:
        derived_text = DERIVED_RUNNER.read_text(encoding="utf-8", errors="ignore")

    if not BASELINE_RUNNER.exists():
        failed_checks.append("baseline_runner_missing")

    patterns = {
        "candidate_gate": [
            r"CONTROL_MODE_MPC_ASSISTED_CANDIDATE",
            r"--allow-mpc-assisted-candidate",
            r"NotImplementedError",
        ],
        "argparse_entry": [
            r"argparse\.ArgumentParser",
            r"parser\.add_argument",
            r"args = parser\.parse_args",
        ],
        "simulation_loop": [
            r"for step in range\(total_steps\):",
        ],
        "torque_composition": [
            r"tau_total_raw = tau_stance_pd \+ tau_stance_wbc \+ tau_swing_pd",
        ],
        "torque_clip": [
            r"tau_total = np\.clip\(tau_total_raw, -TORQUE_LIMIT, TORQUE_LIMIT\)",
        ],
        "mujoco_ctrl_write": [
            r"data\.ctrl\[:\] = tau_total",
            r"data\.ctrl",
        ],
        "mujoco_step": [
            r"mujoco\.mj_step\(model, data\)",
        ],
        "summary_fields": [
            r"mpc_assisted_candidate_switch_present",
            r"mpc_assisted_candidate_executed",
            r"control_mode",
            r"summary = \{",
        ],
    }

    hits = find_lines(derived_text, patterns)
    hit_counts = {k: len(v) for k, v in hits.items()}

    for key, count in hit_counts.items():
        if count <= 0:
            failed_checks.append(f"missing_derived_runner_anchor:{key}")

    candidate_info = csv_info(CANDIDATE_CSV)
    qp_info = csv_info(QP_CSV)
    baseline_log_info = csv_info(BASELINE_MODE_LOG_CSV)
    baseline_summary_info = csv_info(BASELINE_MODE_SUMMARY_CSV)

    if not candidate_info["exists"]:
        failed_checks.append("candidate_csv_missing")
    if candidate_info["row_count"] <= 0:
        failed_checks.append("candidate_csv_empty")

    if not qp_info["exists"]:
        failed_checks.append("qp_csv_missing")
    if qp_info["row_count"] <= 0:
        failed_checks.append("qp_csv_empty")

    if not baseline_log_info["exists"]:
        failed_checks.append("baseline_mode_log_csv_missing")
    if baseline_log_info["row_count"] != 2400:
        failed_checks.append("baseline_mode_log_csv_row_count_not_2400")

    if not baseline_summary_info["exists"]:
        failed_checks.append("baseline_mode_summary_csv_missing")
    if baseline_summary_info["row_count"] != 1:
        failed_checks.append("baseline_mode_summary_csv_row_count_not_1")

    candidate_columns = candidate_info["columns"]
    candidate_tau_columns = [
        c for c in candidate_columns
        if re.search(r"(tau|torque)", c, re.IGNORECASE)
    ]
    candidate_step_columns = [
        c for c in candidate_columns
        if c in {"step", "k", "index"} or re.search(r"step", c, re.IGNORECASE)
    ]
    candidate_contact_columns = [
        c for c in candidate_columns
        if re.search(r"contact|mode|stance|swing", c, re.IGNORECASE)
    ]

    if not candidate_tau_columns:
        failed_checks.append("candidate_csv_has_no_tau_or_torque_columns")
    if not candidate_step_columns:
        failed_checks.append("candidate_csv_has_no_step_column")

    baseline_log_columns = baseline_log_info["columns"]
    required_baseline_log_columns = {
        "step",
        "mode",
        "stance_legs",
        "swing_legs",
        "tau_total_raw_abs",
        "tau_total_abs",
        "saturated",
        "base_z",
        "roll",
        "pitch",
    }
    missing_baseline_log_columns = sorted(required_baseline_log_columns - set(baseline_log_columns))
    if missing_baseline_log_columns:
        failed_checks.append("baseline_log_missing_required_columns")

    source_diff_checks = {}
    for source_path in [
        DERIVED_RUNNER,
        BASELINE_RUNNER,
    ]:
        if source_path.exists():
            rel = str(source_path.relative_to(ROOT))
            diff = git(["diff", "--", rel])
            source_diff_checks[rel] = {
                "local_diff_empty": diff.strip() == "",
                "diff_len": len(diff),
            }
            if diff.strip():
                failed_checks.append(f"source_file_has_local_diff:{rel}")

    injection_design = {
        "future_step": "R6_or_later",
        "candidate_source_csv": str(CANDIDATE_CSV.relative_to(ROOT)),
        "candidate_source_summary": str(SUMMARY_14_5B.relative_to(ROOT)),
        "qp_reference_summary": str(SUMMARY_14_5C.relative_to(ROOT)),
        "baseline_mode_log_csv": str(BASELINE_MODE_LOG_CSV.relative_to(ROOT)),
        "derived_runner": str(DERIVED_RUNNER.relative_to(ROOT)),
        "recommended_injection_location": "after tau_total_raw baseline composition and before torque clipping",
        "recommended_anchor_before": "tau_total_raw = tau_stance_pd + tau_stance_wbc + tau_swing_pd",
        "recommended_anchor_after": "tau_total = np.clip(tau_total_raw, -TORQUE_LIMIT, TORQUE_LIMIT)",
        "future_candidate_rule": [
            "Keep default control_mode=baseline.",
            "Require --control-mode mpc_assisted_candidate and --allow-mpc-assisted-candidate.",
            "Read offline torque candidate table by step index.",
            "Apply candidate only inside MuJoCo simulation.",
            "Use explicit scale and keep candidate scale bounded.",
            "Clip final tau_total to TORQUE_LIMIT.",
            "Log tau_baseline_raw, tau_candidate, tau_candidate_scaled, tau_total_raw, tau_total.",
            "Preserve baseline runner source unchanged.",
            "Do not create or use ROS torque publisher.",
            "Do not claim real robot torque readiness.",
        ],
        "not_implemented_in_r5": True,
    }

    anchor_lines = [
        "Stage 14.5D-R5 MPC candidate injection source design inspection",
        f"timestamp_utc: {dt.datetime.now(dt.timezone.utc).isoformat()}",
        "",
        f"derived_runner: {DERIVED_RUNNER.relative_to(ROOT)}",
        "",
        "== derived runner anchors ==",
    ]

    for key, values in hits.items():
        anchor_lines.append("")
        anchor_lines.append(f"[{key}] count={len(values)}")
        for item in values[:8]:
            anchor_lines.extend(snippet(derived_text, item["lineno"], radius=3))
            anchor_lines.append("")

    anchor_lines += [
        "",
        "== candidate csv ==",
        f"path: {CANDIDATE_CSV.relative_to(ROOT)}",
        f"exists: {candidate_info['exists']}",
        f"row_count: {candidate_info['row_count']}",
        f"columns: {candidate_columns}",
        f"tau_or_torque_columns: {candidate_tau_columns}",
        f"step_columns: {candidate_step_columns}",
        f"contact_columns: {candidate_contact_columns}",
        "",
        "== qp csv ==",
        f"path: {QP_CSV.relative_to(ROOT)}",
        f"exists: {qp_info['exists']}",
        f"row_count: {qp_info['row_count']}",
        f"columns: {qp_info['columns']}",
        "",
        "== baseline-mode log csv ==",
        f"path: {BASELINE_MODE_LOG_CSV.relative_to(ROOT)}",
        f"exists: {baseline_log_info['exists']}",
        f"row_count: {baseline_log_info['row_count']}",
        f"missing_required_columns: {missing_baseline_log_columns}",
        "",
        "== recommended future injection design ==",
        json.dumps(injection_design, indent=2, ensure_ascii=False),
        "",
    ]

    OUT_ANCHORS.write_text("\n".join(anchor_lines), encoding="utf-8")

    allowed_dirty = {
        "scripts/stage14_5d_r5_mpc_candidate_injection_design_inspection.py",
        "docs/stage14_5d_r5_mpc_candidate_injection_design_inspection.md",
        "results/logs_sample/stage14_5d_r5_mpc_candidate_injection_design_inspection_summary.json",
        "results/logs_sample/stage14_5d_r5_mpc_candidate_injection_design_anchors.txt",
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
        "derived_runner_source_modified": False,
        "mujoco_closed_loop_baseline_mode_executed": False,
        "mujoco_closed_loop_ab_executed": False,
        "mujoco_sim_data_ctrl_used": False,
        "mpc_assisted_candidate_implemented": False,
        "mpc_assisted_candidate_executed": False,
        "stage14_5d_r4_pass": None if not r4 else r4.get("pass"),
        "stage14_5d_r3_pass": None if not r3 else r3.get("pass"),
        "stage14_5b_pass": None if not s14_5b else s14_5b.get("pass"),
        "stage14_5c_pass": None if not s14_5c else s14_5c.get("pass"),
        "derived_runner": str(DERIVED_RUNNER.relative_to(ROOT)),
        "baseline_runner": str(BASELINE_RUNNER.relative_to(ROOT)),
        "derived_runner_anchor_counts": hit_counts,
        "candidate_csv": {
            "path": str(CANDIDATE_CSV.relative_to(ROOT)),
            "exists": candidate_info["exists"],
            "row_count": candidate_info["row_count"],
            "columns": candidate_columns,
            "tau_or_torque_columns": candidate_tau_columns,
            "step_columns": candidate_step_columns,
            "contact_columns": candidate_contact_columns,
        },
        "qp_csv": {
            "path": str(QP_CSV.relative_to(ROOT)),
            "exists": qp_info["exists"],
            "row_count": qp_info["row_count"],
            "columns": qp_info["columns"],
        },
        "baseline_mode_log_csv": {
            "path": str(BASELINE_MODE_LOG_CSV.relative_to(ROOT)),
            "exists": baseline_log_info["exists"],
            "row_count": baseline_log_info["row_count"],
            "columns": baseline_log_columns,
            "missing_required_columns": missing_baseline_log_columns,
        },
        "baseline_mode_summary_csv": {
            "path": str(BASELINE_MODE_SUMMARY_CSV.relative_to(ROOT)),
            "exists": baseline_summary_info["exists"],
            "row_count": baseline_summary_info["row_count"],
        },
        "source_diff_checks": source_diff_checks,
        "injection_design": injection_design,
        "git": {
            "branch": git(["branch", "--show-current"]),
            "head": git(["rev-parse", "--short", "HEAD"]),
            "status_porcelain": dirty,
            "dirty_non_stage14_5d_r5": dirty_non_stage,
        },
        "generated_files": [
            "scripts/stage14_5d_r5_mpc_candidate_injection_design_inspection.py",
            "docs/stage14_5d_r5_mpc_candidate_injection_design_inspection.md",
            "results/logs_sample/stage14_5d_r5_mpc_candidate_injection_design_inspection_summary.json",
            "results/logs_sample/stage14_5d_r5_mpc_candidate_injection_design_anchors.txt",
        ],
        "notes": [
            "Design inspection only.",
            "No runner source is modified.",
            "No MPC-assisted candidate implementation is added in R5.",
            "No MuJoCo rollout is executed.",
            "No A/B comparison is executed.",
            "No real robot torque command is sent.",
        ],
    }

    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    doc = [
        "# Stage 14.5D-R5 MPC Candidate Injection Source Design Inspection",
        "",
        "Scope: simulation-only source and artifact design inspection.",
        "",
        "This step identifies the future injection anchors for MPC torque candidates but does not implement candidate injection and does not run MuJoCo.",
        "",
        "## Evidence",
        "",
        f"- Summary JSON: `{OUT_SUMMARY.relative_to(ROOT)}`",
        f"- Anchor notes: `{OUT_ANCHORS.relative_to(ROOT)}`",
        "",
        "## Result",
        "",
        f"- pass: {summary['pass']}",
        f"- failed_checks: {summary['failed_checks']}",
        f"- derived_runner: `{summary['derived_runner']}`",
        f"- candidate_csv_rows: {candidate_info['row_count']}",
        f"- qp_csv_rows: {qp_info['row_count']}",
        f"- baseline_log_rows: {baseline_log_info['row_count']}",
        "",
        "## Recommended future injection location",
        "",
        f"- before: `{injection_design['recommended_anchor_before']}`",
        f"- after: `{injection_design['recommended_anchor_after']}`",
        f"- location: {injection_design['recommended_injection_location']}",
        "",
        "## Boundary",
        "",
        f"- mpc_assisted_candidate_implemented: {summary['mpc_assisted_candidate_implemented']}",
        f"- mpc_assisted_candidate_executed: {summary['mpc_assisted_candidate_executed']}",
        f"- mujoco_closed_loop_ab_executed: {summary['mujoco_closed_loop_ab_executed']}",
        f"- mujoco_sim_data_ctrl_used: {summary['mujoco_sim_data_ctrl_used']}",
        f"- real_robot_torque_commanded: {summary['real_robot_torque_commanded']}",
        "",
        "This is design inspection evidence only, not MPC-assisted closed-loop evidence.",
        "",
    ]

    OUT_DOC.write_text("\n".join(doc), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
