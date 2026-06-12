#!/usr/bin/env python3
from pathlib import Path
import csv
import datetime as dt
import json
import subprocess
from typing import Dict, List, Any

ROOT = Path.cwd()
STAGE = "14.5E-R2"

SUMMARY_R1 = ROOT / "results/logs_sample/stage14_5e_r1_candidate_robustness_scale_sweep_summary.json"
SWEEP_TABLE_R1 = ROOT / "results/logs_sample/stage14_5e_r1_candidate_robustness_scale_sweep_table.csv"

BASELINE_RUNNER = ROOT / "scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py"
R2_RUNNER = ROOT / "scripts/stage14_5d_r2_closed_loop_ab_runner_skeleton.py"
R6_RUNNER = ROOT / "scripts/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_runner.py"

OUT_SUMMARY = ROOT / "results/logs_sample/stage14_5e_r2_candidate_robustness_sweep_analysis_summary.json"
OUT_TABLE = ROOT / "results/logs_sample/stage14_5e_r2_candidate_robustness_sweep_analysis_table.csv"
OUT_DOC = ROOT / "docs/stage14_5e_r2_candidate_robustness_sweep_analysis_packaging.md"

LIMITS = {
    "min_z_gt": 0.22,
    "max_abs_roll_lt": 0.20,
    "max_abs_pitch_lt": 0.20,
    "max_tau_total_abs_le": 23.7,
    "qp_fail_steps_eq": 0,
    "saturation_steps_eq": 0,
}


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


def margin_metrics(row: Dict[str, str]) -> Dict[str, Any]:
    min_z = as_float(row.get("min_z"))
    max_abs_roll = as_float(row.get("max_abs_roll"))
    max_abs_pitch = as_float(row.get("max_abs_pitch"))
    max_tau_total_abs = as_float(row.get("max_tau_total_abs"))
    qp_fail_steps = as_int(row.get("qp_fail_steps"))
    saturation_steps = as_int(row.get("saturation_steps"))

    return {
        "z_margin_to_0p22": None if min_z is None else min_z - LIMITS["min_z_gt"],
        "roll_margin_to_0p20": None if max_abs_roll is None else LIMITS["max_abs_roll_lt"] - max_abs_roll,
        "pitch_margin_to_0p20": None if max_abs_pitch is None else LIMITS["max_abs_pitch_lt"] - max_abs_pitch,
        "tau_margin_to_23p7": None if max_tau_total_abs is None else LIMITS["max_tau_total_abs_le"] - max_tau_total_abs,
        "qp_fail_steps": qp_fail_steps,
        "saturation_steps": saturation_steps,
    }


def row_passes_limits(row: Dict[str, str]) -> bool:
    margins = margin_metrics(row)
    values_ok = [
        margins["z_margin_to_0p22"] is not None and margins["z_margin_to_0p22"] > 0.0,
        margins["roll_margin_to_0p20"] is not None and margins["roll_margin_to_0p20"] > 0.0,
        margins["pitch_margin_to_0p20"] is not None and margins["pitch_margin_to_0p20"] > 0.0,
        margins["tau_margin_to_23p7"] is not None and margins["tau_margin_to_23p7"] >= 0.0,
        margins["qp_fail_steps"] == 0,
        margins["saturation_steps"] == 0,
        as_bool(row.get("pass")) is True,
        as_bool(row.get("real_robot_torque_commanded")) is False,
        as_bool(row.get("ros_publisher_used")) is False,
    ]
    return all(values_ok)


def main() -> int:
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)

    failed_checks = []

    r1 = read_json(SUMMARY_R1)
    if not r1 or r1.get("pass") is not True:
        failed_checks.append("stage14_5e_r1_not_passed_or_missing")

    rows = read_csv(SWEEP_TABLE_R1)
    if len(rows) != 4:
        failed_checks.append(f"r1_sweep_table_row_count_not_4:{len(rows)}")

    scales = [as_float(row.get("scale")) for row in rows]
    if scales != [0.0, 0.02, 0.05, 0.10]:
        failed_checks.append(f"unexpected_scales:{scales}")

    baseline_rows = [row for row in rows if as_float(row.get("scale")) == 0.0]
    candidate_rows = [row for row in rows if as_float(row.get("scale")) in [0.02, 0.05, 0.10]]

    if len(baseline_rows) != 1:
        failed_checks.append("baseline_reference_row_count_not_1")
    if len(candidate_rows) != 3:
        failed_checks.append("candidate_run_row_count_not_3")

    baseline = baseline_rows[0] if baseline_rows else {}

    if baseline:
        if baseline.get("evidence_source") != "baseline_reference":
            failed_checks.append("scale_0p00_not_baseline_reference")
        if baseline.get("control_mode") != "baseline":
            failed_checks.append("scale_0p00_control_mode_not_baseline")

    for row in candidate_rows:
        scale = as_float(row.get("scale"))
        if row.get("evidence_source") != "candidate_run":
            failed_checks.append(f"scale_{scale}_not_candidate_run")
        if row.get("control_mode") != "mpc_assisted_candidate":
            failed_checks.append(f"scale_{scale}_control_mode_not_candidate")
        if as_int(row.get("candidate_row_count")) != 100:
            failed_checks.append(f"scale_{scale}_candidate_row_count_not_100")
        if as_int(row.get("run_returncode")) != 0:
            failed_checks.append(f"scale_{scale}_returncode_not_0")

    analysis_rows = []
    baseline_numeric = {
        "min_z": as_float(baseline.get("min_z")),
        "max_abs_roll": as_float(baseline.get("max_abs_roll")),
        "max_abs_pitch": as_float(baseline.get("max_abs_pitch")),
        "max_tau_total_abs": as_float(baseline.get("max_tau_total_abs")),
    }

    for row in rows:
        scale = as_float(row.get("scale"))
        margins = margin_metrics(row)
        item = {
            "scale": row.get("scale"),
            "evidence_source": row.get("evidence_source"),
            "control_mode": row.get("control_mode"),
            "entry_pass": row.get("pass"),
            "limits_pass": row_passes_limits(row),
            "total_steps": row.get("total_steps"),
            "min_z": row.get("min_z"),
            "max_abs_roll": row.get("max_abs_roll"),
            "max_abs_pitch": row.get("max_abs_pitch"),
            "max_tau_total_abs": row.get("max_tau_total_abs"),
            "max_tau_candidate_scaled_abs": row.get("max_tau_candidate_scaled_abs"),
            "qp_fail_steps": row.get("qp_fail_steps"),
            "saturation_steps": row.get("saturation_steps"),
            "z_margin_to_0p22": margins["z_margin_to_0p22"],
            "roll_margin_to_0p20": margins["roll_margin_to_0p20"],
            "pitch_margin_to_0p20": margins["pitch_margin_to_0p20"],
            "tau_margin_to_23p7": margins["tau_margin_to_23p7"],
            "delta_min_z_vs_baseline": None if baseline_numeric["min_z"] is None or as_float(row.get("min_z")) is None else as_float(row.get("min_z")) - baseline_numeric["min_z"],
            "delta_max_abs_roll_vs_baseline": None if baseline_numeric["max_abs_roll"] is None or as_float(row.get("max_abs_roll")) is None else as_float(row.get("max_abs_roll")) - baseline_numeric["max_abs_roll"],
            "delta_max_abs_pitch_vs_baseline": None if baseline_numeric["max_abs_pitch"] is None or as_float(row.get("max_abs_pitch")) is None else as_float(row.get("max_abs_pitch")) - baseline_numeric["max_abs_pitch"],
            "delta_max_tau_total_abs_vs_baseline": None if baseline_numeric["max_tau_total_abs"] is None or as_float(row.get("max_tau_total_abs")) is None else as_float(row.get("max_tau_total_abs")) - baseline_numeric["max_tau_total_abs"],
            "real_robot_torque_commanded": row.get("real_robot_torque_commanded"),
            "ros_publisher_used": row.get("ros_publisher_used"),
        }
        analysis_rows.append(item)

        if item["limits_pass"] is not True:
            failed_checks.append(f"scale_limits_not_passed:{scale}")

    passing_candidate_scales = [
        as_float(row["scale"])
        for row in analysis_rows
        if row["evidence_source"] == "candidate_run" and row["limits_pass"] is True
    ]

    validated_candidate_scale_max = max(passing_candidate_scales) if passing_candidate_scales else None

    aggregate = {
        "analysis_row_count": len(analysis_rows),
        "validated_candidate_scale_max": validated_candidate_scale_max,
        "baseline_reference_count": len(baseline_rows),
        "candidate_run_count": len(candidate_rows),
        "all_entries_pass_limits": all(row["limits_pass"] for row in analysis_rows) if analysis_rows else False,
        "min_z_min_over_entries": min((as_float(row["min_z"]) for row in rows if as_float(row.get("min_z")) is not None), default=None),
        "max_abs_roll_max_over_entries": max((as_float(row["max_abs_roll"]) for row in rows if as_float(row.get("max_abs_roll")) is not None), default=None),
        "max_abs_pitch_max_over_entries": max((as_float(row["max_abs_pitch"]) for row in rows if as_float(row.get("max_abs_pitch")) is not None), default=None),
        "max_tau_total_abs_max_over_entries": max((as_float(row["max_tau_total_abs"]) for row in rows if as_float(row.get("max_tau_total_abs")) is not None), default=None),
        "max_tau_candidate_scaled_abs_max_over_candidate_runs": max((as_float(row["max_tau_candidate_scaled_abs"]) for row in rows if row.get("evidence_source") == "candidate_run" and as_float(row.get("max_tau_candidate_scaled_abs")) is not None), default=None),
        "total_qp_fail_steps": sum((as_int(row.get("qp_fail_steps")) or 0) for row in rows),
        "total_saturation_steps": sum((as_int(row.get("saturation_steps")) or 0) for row in rows),
    }

    if aggregate["validated_candidate_scale_max"] != 0.10:
        failed_checks.append(f"validated_candidate_scale_max_not_0p10:{aggregate['validated_candidate_scale_max']}")

    if aggregate["all_entries_pass_limits"] is not True:
        failed_checks.append("not_all_entries_pass_limits")

    if aggregate["total_qp_fail_steps"] != 0:
        failed_checks.append("total_qp_fail_steps_nonzero")

    if aggregate["total_saturation_steps"] != 0:
        failed_checks.append("total_saturation_steps_nonzero")

    with open(OUT_TABLE, "w", newline="") as f:
        fieldnames = [
            "scale",
            "evidence_source",
            "control_mode",
            "entry_pass",
            "limits_pass",
            "total_steps",
            "min_z",
            "max_abs_roll",
            "max_abs_pitch",
            "max_tau_total_abs",
            "max_tau_candidate_scaled_abs",
            "qp_fail_steps",
            "saturation_steps",
            "z_margin_to_0p22",
            "roll_margin_to_0p20",
            "pitch_margin_to_0p20",
            "tau_margin_to_23p7",
            "delta_min_z_vs_baseline",
            "delta_max_abs_roll_vs_baseline",
            "delta_max_abs_pitch_vs_baseline",
            "delta_max_tau_total_abs_vs_baseline",
            "real_robot_torque_commanded",
            "ros_publisher_used",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(analysis_rows)

    for source_path in [BASELINE_RUNNER, R2_RUNNER, R6_RUNNER]:
        if source_path.exists():
            diff = git(["diff", "--", rel(source_path)])
            if diff.strip():
                failed_checks.append(f"source_file_has_local_diff:{rel(source_path)}")

    allowed_dirty = {
        "scripts/stage14_5e_r2_candidate_robustness_sweep_analysis_packaging.py",
        "docs/stage14_5e_r2_candidate_robustness_sweep_analysis_packaging.md",
        "results/logs_sample/stage14_5e_r2_candidate_robustness_sweep_analysis_summary.json",
        "results/logs_sample/stage14_5e_r2_candidate_robustness_sweep_analysis_table.csv",
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
        "stage14_5e_r1_pass": None if not r1 else r1.get("pass"),
        "simulation_only_project": True,
        "hardware_deployment_completed": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "real_robot_torque_commanded": False,
        "ros_publisher_used": False,
        "frozen_baseline_source_modified": False,
        "r6_runner_source_modified": False,
        "mujoco_rollout_executed_in_r2": False,
        "mujoco_sim_data_ctrl_used_in_r2": False,
        "mujoco_closed_loop_ab_executed_in_r2": False,
        "analysis_only_packaging": True,
        "scale_zero_policy": None if not r1 else r1.get("scale_zero_policy"),
        "limits": LIMITS,
        "analysis_rows": analysis_rows,
        "aggregate": aggregate,
        "validated_candidate_scale_max_simulation_only": validated_candidate_scale_max,
        "analysis_table_csv": rel(OUT_TABLE),
        "git": {
            "branch": git(["branch", "--show-current"]),
            "head": git(["rev-parse", "--short", "HEAD"]),
            "status_porcelain": dirty,
            "dirty_paths": dirty_paths,
            "dirty_non_stage14_5e_r2": dirty_non_stage,
        },
        "generated_files": [
            "scripts/stage14_5e_r2_candidate_robustness_sweep_analysis_packaging.py",
            "docs/stage14_5e_r2_candidate_robustness_sweep_analysis_packaging.md",
            "results/logs_sample/stage14_5e_r2_candidate_robustness_sweep_analysis_summary.json",
            "results/logs_sample/stage14_5e_r2_candidate_robustness_sweep_analysis_table.csv",
        ],
        "notes": [
            "Analysis packaging only.",
            "No MuJoCo rollout is executed in R2.",
            "Validated scale max is simulation-only and only for this candidate sweep evidence.",
            "No real robot torque command is sent.",
            "No ROS torque publisher is used.",
            "No hardware readiness or torque-enable readiness is claimed.",
        ],
    }

    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    doc = [
        "# Stage 14.5E-R2 Candidate Robustness Sweep Analysis Packaging",
        "",
        "Scope: analysis-only packaging of E-R1 robustness sweep results.",
        "",
        "This step analyzes the existing E-R1 sweep table. It does not rerun MuJoCo and does not modify any runner.",
        "",
        "## Result",
        "",
        f"- pass: {summary['pass']}",
        f"- failed_checks: {summary['failed_checks']}",
        f"- validated_candidate_scale_max_simulation_only: {validated_candidate_scale_max}",
        f"- all_entries_pass_limits: {aggregate['all_entries_pass_limits']}",
        f"- min_z_min_over_entries: {aggregate['min_z_min_over_entries']}",
        f"- max_abs_roll_max_over_entries: {aggregate['max_abs_roll_max_over_entries']}",
        f"- max_abs_pitch_max_over_entries: {aggregate['max_abs_pitch_max_over_entries']}",
        f"- max_tau_total_abs_max_over_entries: {aggregate['max_tau_total_abs_max_over_entries']}",
        f"- max_tau_candidate_scaled_abs_max_over_candidate_runs: {aggregate['max_tau_candidate_scaled_abs_max_over_candidate_runs']}",
        f"- total_qp_fail_steps: {aggregate['total_qp_fail_steps']}",
        f"- total_saturation_steps: {aggregate['total_saturation_steps']}",
        "",
        "## Per-scale analysis",
        "",
    ]

    for row in analysis_rows:
        doc.extend([
            f"### scale={row['scale']}",
            f"- evidence_source: {row['evidence_source']}",
            f"- limits_pass: {row['limits_pass']}",
            f"- min_z: {row['min_z']}",
            f"- max_abs_roll: {row['max_abs_roll']}",
            f"- max_abs_pitch: {row['max_abs_pitch']}",
            f"- max_tau_total_abs: {row['max_tau_total_abs']}",
            f"- max_tau_candidate_scaled_abs: {row['max_tau_candidate_scaled_abs']}",
            f"- qp_fail_steps: {row['qp_fail_steps']}",
            f"- saturation_steps: {row['saturation_steps']}",
            "",
        ])

    doc += [
        "## Boundary",
        "",
        f"- analysis_only_packaging: {summary['analysis_only_packaging']}",
        f"- mujoco_rollout_executed_in_r2: {summary['mujoco_rollout_executed_in_r2']}",
        f"- mujoco_closed_loop_ab_executed_in_r2: {summary['mujoco_closed_loop_ab_executed_in_r2']}",
        f"- real_robot_torque_commanded: {summary['real_robot_torque_commanded']}",
        f"- ros_publisher_used: {summary['ros_publisher_used']}",
        f"- torque_enable_ready: {summary['torque_enable_ready']}",
        "",
        "This is simulation-only analysis evidence. It is not hardware-readiness evidence.",
        "",
        "## Evidence",
        "",
        f"- summary: `{OUT_SUMMARY.relative_to(ROOT)}`",
        f"- analysis table: `{OUT_TABLE.relative_to(ROOT)}`",
        f"- source sweep table: `{SWEEP_TABLE_R1.relative_to(ROOT)}`",
        "",
    ]

    OUT_DOC.write_text("\n".join(doc), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
