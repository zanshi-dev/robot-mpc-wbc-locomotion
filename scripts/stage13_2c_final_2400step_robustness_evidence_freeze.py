#!/usr/bin/env /usr/bin/python3
from pathlib import Path
import hashlib
import json
from datetime import datetime

ROOT = Path.cwd()
OUT = ROOT / "results/logs_sample"
DOCS = ROOT / "docs"
PROJECT_STATUS = ROOT / "PROJECT_STATUS.md"

OUT.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)

R1 = OUT / "stage13_2b_r1_derive_contact_schedule_and_rerun_2400step_summary.json"
A_R2 = OUT / "stage13_2a_r2_create_2400step_derived_runner_summary.json"
STAGE13_1B = OUT / "stage13_1b_rerun_1200step_simulation_only_mixed_baseline_summary.json"
STAGE12_22 = OUT / "stage12_22_simulation_only_scope_freeze_summary.json"

SUMMARY = OUT / "stage13_2c_final_2400step_robustness_evidence_freeze_summary.json"
DOC = DOCS / "stage13_2c_final_2400step_robustness_evidence_freeze.md"
RESULTS_DOC = DOCS / "SIMULATION_ONLY_RESULTS_SUMMARY.md"

def read_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))

def sha256_file(path):
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()

def file_status(path):
    p = Path(path)
    return {
        "path": str(p),
        "exists": p.exists(),
        "size": p.stat().st_size if p.exists() else None,
        "sha256": sha256_file(p),
    }

fail_reasons = []

r1 = read_json(R1)
a_r2 = read_json(A_R2)
stage13_1b = read_json(STAGE13_1B)
stage12_22 = read_json(STAGE12_22)

if r1 is None:
    fail_reasons.append("missing Stage 13.2B-R1 summary")
elif r1.get("pass") is not True:
    fail_reasons.append("Stage 13.2B-R1 did not pass")

if a_r2 is None:
    fail_reasons.append("missing Stage 13.2A-R2 summary")
elif a_r2.get("pass") is not True:
    fail_reasons.append("Stage 13.2A-R2 did not pass")

if stage13_1b is None:
    fail_reasons.append("missing Stage 13.1B summary")
elif stage13_1b.get("pass") is not True:
    fail_reasons.append("Stage 13.1B did not pass")

if stage12_22 is None:
    fail_reasons.append("missing Stage 12.22 summary")
elif stage12_22.get("pass") is not True:
    fail_reasons.append("Stage 12.22 did not pass")

mixed = {} if r1 is None else r1.get("parsed_mixed_summary", {})
wbc = {} if r1 is None else r1.get("parsed_wbc_summary", {})
evidence = {} if r1 is None else r1.get("evidence_files", {})

required_checks = {
    "simulation_only_project": None if r1 is None else r1.get("simulation_only_project") is True,
    "hardware_scope_out_of_scope": None if r1 is None else r1.get("hardware_deployment_scope") == "out_of_scope_by_user_constraint",
    "hardware_deployment_completed_false": None if r1 is None else r1.get("hardware_deployment_completed") is False,
    "torque_enable_ready_false": None if r1 is None else r1.get("torque_enable_ready") is False,
    "torque_publisher_enabled_false": None if r1 is None else r1.get("torque_publisher_enabled") is False,
    "control_law_changed_false": None if r1 is None else r1.get("control_law_changed") is False,
    "previous_13_2b_failure_missing_contact": None if r1 is None else r1.get("previous_stage13_2b_failure_classified_as_missing_contact_schedule") is True,
    "derived_contact_rows_2400": None if r1 is None else r1.get("derived_contact_rows") == 2400,
    "derived_contact_line_count_2401": None if r1 is None else r1.get("derived_contact_line_count") == 2401,
    "wbc_returncode_0": None if r1 is None else r1.get("wbc_returncode") == 0,
    "wbc_timeout_false": None if r1 is None else r1.get("wbc_timeout") is False,
    "mixed_returncode_0": None if r1 is None else r1.get("mixed_returncode") == 0,
    "mixed_timeout_false": None if r1 is None else r1.get("mixed_timeout") is False,
    "runner_unchanged": None if r1 is None else r1.get("runner_changed") is False,
    "wbc_runner_unchanged": None if r1 is None else r1.get("wbc_runner_changed") is False,
    "derived_swing_unchanged": None if r1 is None else r1.get("derived_swing_changed") is False,
    "source_contact_unchanged": None if r1 is None else r1.get("source_contact_changed") is False,
    "mixed_total_steps_2400": mixed.get("total_steps") == 2400,
    "mixed_transition_count_11": mixed.get("transition_count") == 11,
    "mixed_trot_FR_RL_1200": mixed.get("trot_FR_RL_steps") == 1200,
    "mixed_trot_FL_RR_1200": mixed.get("trot_FL_RR_steps") == 1200,
    "mixed_qp_fail_0": mixed.get("qp_fail_steps") == 0,
    "mixed_saturation_0": mixed.get("saturation_steps") == 0,
    "mixed_pass_true": mixed.get("pass") is True,
    "mixed_pass_margin_true": mixed.get("pass_margin") is True,
    "wbc_total_steps_2400": wbc.get("total_steps") == 2400,
    "wbc_qp_fail_0": wbc.get("qp_fail_steps") == 0,
    "wbc_saturation_0": wbc.get("saturation_steps") == 0,
    "wbc_pass_true": wbc.get("pass") is True,
    "wbc_pass_margin_true": wbc.get("pass_margin") is True,
}

threshold_checks = {
    "mixed_min_z_ge_0p22": mixed.get("min_z", -999) >= 0.22,
    "mixed_max_abs_roll_le_0p08": mixed.get("max_abs_roll", 999) <= 0.08,
    "mixed_max_abs_pitch_le_0p08": mixed.get("max_abs_pitch", 999) <= 0.08,
    "mixed_max_joint_error_le_0p12": mixed.get("max_joint_error", 999) <= 0.12,
    "mixed_max_tau_total_abs_le_23p7": mixed.get("max_tau_total_abs", 999) <= 23.7,
}

for k, ok in {**required_checks, **threshold_checks}.items():
    if ok is not True:
        fail_reasons.append(f"final freeze check failed: {k}")

evidence_status = {k: file_status(v) for k, v in evidence.items() if isinstance(v, str)}
missing_evidence = [k for k, st in evidence_status.items() if not st["exists"]]
if missing_evidence:
    fail_reasons.append(f"missing evidence files: {missing_evidence}")

summary = {
    "stage": "13.2C",
    "name": "final_2400step_simulation_only_robustness_evidence_freeze",
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "pass": len(fail_reasons) == 0,
    "fail_reasons": fail_reasons,
    "simulation_only_project": True,
    "hardware_deployment_scope": "out_of_scope_by_user_constraint",
    "hardware_deployment_completed": False,
    "torque_enable_ready": False,
    "torque_publisher_enabled": False,
    "control_law_changed": False,
    "baseline_type": "mixed_online_control_baseline",
    "stage13_1b_1200step_pass": None if stage13_1b is None else stage13_1b.get("pass"),
    "stage13_2a_r2_derived_runner_pass": None if a_r2 is None else a_r2.get("pass"),
    "stage13_2b_r1_2400step_pass": None if r1 is None else r1.get("pass"),
    "mixed_2400_summary": mixed,
    "wbc_2400_summary": wbc,
    "required_checks": required_checks,
    "threshold_checks": threshold_checks,
    "evidence_status": evidence_status,
    "final_statement": "2400-step simulation-only robustness regression passed for the mixed online control baseline; no hardware deployment or actuator enablement is claimed.",
    "next_stage": "Stage 13.3 documentation consolidation and report-ready results packaging",
}

SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

doc_lines = [
    "# Stage 13.2C Final 2400-Step Robustness Evidence Freeze",
    "",
    f"- pass: `{summary['pass']}`",
    f"- fail_reasons: `{summary['fail_reasons']}`",
    f"- simulation_only_project: `{summary['simulation_only_project']}`",
    f"- hardware_deployment_scope: `{summary['hardware_deployment_scope']}`",
    f"- hardware_deployment_completed: `{summary['hardware_deployment_completed']}`",
    f"- torque_enable_ready: `{summary['torque_enable_ready']}`",
    f"- torque_publisher_enabled: `{summary['torque_publisher_enabled']}`",
    f"- control_law_changed: `{summary['control_law_changed']}`",
    f"- baseline_type: `{summary['baseline_type']}`",
    "",
    "## Mixed 2400-step results",
    "",
    f"- total_steps: `{mixed.get('total_steps')}`",
    f"- transition_count: `{mixed.get('transition_count')}`",
    f"- trot_FR_RL_steps: `{mixed.get('trot_FR_RL_steps')}`",
    f"- trot_FL_RR_steps: `{mixed.get('trot_FL_RR_steps')}`",
    f"- min_z: `{mixed.get('min_z')}`",
    f"- final_z: `{mixed.get('final_z')}`",
    f"- max_abs_roll: `{mixed.get('max_abs_roll')}`",
    f"- max_abs_pitch: `{mixed.get('max_abs_pitch')}`",
    f"- max_joint_error: `{mixed.get('max_joint_error')}`",
    f"- max_tau_total_abs: `{mixed.get('max_tau_total_abs')}`",
    f"- qp_fail_steps: `{mixed.get('qp_fail_steps')}`",
    f"- saturation_steps: `{mixed.get('saturation_steps')}`",
    f"- pass: `{mixed.get('pass')}`",
    f"- pass_margin: `{mixed.get('pass_margin')}`",
    "",
    "## WBC 2400-step results",
    "",
    f"- total_steps: `{wbc.get('total_steps')}`",
    f"- transition_count: `{wbc.get('transition_count')}`",
    f"- min_z: `{wbc.get('min_z')}`",
    f"- final_z: `{wbc.get('final_z')}`",
    f"- max_abs_roll: `{wbc.get('max_abs_roll')}`",
    f"- max_abs_pitch: `{wbc.get('max_abs_pitch')}`",
    f"- max_tau_total_abs: `{wbc.get('max_tau_total_abs')}`",
    f"- qp_fail_steps: `{wbc.get('qp_fail_steps')}`",
    f"- saturation_steps: `{wbc.get('saturation_steps')}`",
    f"- pass: `{wbc.get('pass')}`",
    f"- pass_margin: `{wbc.get('pass_margin')}`",
    "",
    "## Evidence files",
]

for k, st in evidence_status.items():
    doc_lines.append(f"- {k}: exists=`{st['exists']}`, sha256=`{st['sha256']}`, path=`{st['path']}`")

doc_lines += [
    "",
    "## Final statement",
    "",
    summary["final_statement"],
    "",
    f"Next stage: `{summary['next_stage']}`",
]

DOC.write_text("\n".join(doc_lines), encoding="utf-8")

results_lines = [
    "# Simulation-Only Results Summary",
    "",
    "## Scope",
    "",
    "- Project scope: simulation-only.",
    "- Hardware deployment: out of scope.",
    "- Real actuator enablement: out of scope.",
    "- Real robot torque execution: out of scope.",
    "",
    "## Frozen milestones",
    "",
    "- Stage 12.22: simulation-only scope freeze passed.",
    "- Stage 13.1B: 1200-step mixed baseline rerun passed.",
    "- Stage 13.2B-R1: 2400-step WBC and mixed baseline robustness regression passed.",
    "- Stage 13.2C: final 2400-step robustness evidence freeze.",
    "",
    "## 2400-step mixed baseline metrics",
    "",
    f"- total_steps: `{mixed.get('total_steps')}`",
    f"- transition_count: `{mixed.get('transition_count')}`",
    f"- min_z: `{mixed.get('min_z')}`",
    f"- max_abs_roll: `{mixed.get('max_abs_roll')}`",
    f"- max_abs_pitch: `{mixed.get('max_abs_pitch')}`",
    f"- max_joint_error: `{mixed.get('max_joint_error')}`",
    f"- max_tau_total_abs: `{mixed.get('max_tau_total_abs')}`",
    f"- qp_fail_steps: `{mixed.get('qp_fail_steps')}`",
    f"- saturation_steps: `{mixed.get('saturation_steps')}`",
    f"- pass: `{mixed.get('pass')}`",
    "",
    "## Safety statement",
    "",
    "No hardware deployment, actuator enablement, or real robot torque execution is claimed.",
]
RESULTS_DOC.write_text("\n".join(results_lines), encoding="utf-8")

if summary["pass"]:
    block = f"""

## Stage 13.2C Final 2400-Step Robustness Evidence Freeze

- timestamp: `{summary['timestamp']}`
- pass: `True`
- simulation_only_project: `True`
- baseline_type: `mixed_online_control_baseline`
- total_steps: `{mixed.get('total_steps')}`
- transition_count: `{mixed.get('transition_count')}`
- trot_FR_RL_steps: `{mixed.get('trot_FR_RL_steps')}`
- trot_FL_RR_steps: `{mixed.get('trot_FL_RR_steps')}`
- min_z: `{mixed.get('min_z')}`
- max_abs_roll: `{mixed.get('max_abs_roll')}`
- max_abs_pitch: `{mixed.get('max_abs_pitch')}`
- max_joint_error: `{mixed.get('max_joint_error')}`
- max_tau_total_abs: `{mixed.get('max_tau_total_abs')}`
- qp_fail_steps: `{mixed.get('qp_fail_steps')}`
- saturation_steps: `{mixed.get('saturation_steps')}`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- next_stage: `{summary['next_stage']}`
"""
    old = PROJECT_STATUS.read_text(encoding="utf-8", errors="replace") if PROJECT_STATUS.exists() else ""
    if "## Stage 13.2C Final 2400-Step Robustness Evidence Freeze" not in old:
        PROJECT_STATUS.write_text(old.rstrip() + block + "\n", encoding="utf-8")

print(json.dumps(summary, indent=2, ensure_ascii=False))
