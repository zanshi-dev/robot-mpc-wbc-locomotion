#!/usr/bin/env /usr/bin/python3
from pathlib import Path
import csv
import hashlib
import json
from datetime import datetime

ROOT = Path.cwd()
OUT = ROOT / "results/logs_sample"
DOCS = ROOT / "docs"
PROJECT_STATUS = ROOT / "PROJECT_STATUS.md"

OUT.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)

STAGE12_22 = OUT / "stage12_22_simulation_only_scope_freeze_summary.json"
STAGE13_1B = OUT / "stage13_1b_rerun_1200step_simulation_only_mixed_baseline_summary.json"
STAGE13_2C = OUT / "stage13_2c_final_2400step_robustness_evidence_freeze_summary.json"

SUMMARY = OUT / "stage13_3_report_ready_results_packaging_summary.json"
METRICS_CSV = OUT / "stage13_3_report_ready_metrics_table.csv"
DOC = DOCS / "stage13_3_report_ready_results_packaging.md"
REPORT_MD = DOCS / "REPORT_READY_RESULTS.md"
CLAIMS_MD = DOCS / "REPORT_READY_CLAIMS_AND_LIMITATIONS.md"

def read_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))

def sha256_file(path):
    p = Path(path)
    if not p.exists() or not p.is_file():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()

def status(path):
    p = Path(path)
    return {
        "path": str(p),
        "exists": p.exists(),
        "size": p.stat().st_size if p.exists() else None,
        "sha256": sha256_file(p),
    }

fail_reasons = []

s12 = read_json(STAGE12_22)
s131 = read_json(STAGE13_1B)
s132 = read_json(STAGE13_2C)

if s12 is None or s12.get("pass") is not True:
    fail_reasons.append("Stage 12.22 scope freeze missing or failed")
if s131 is None or s131.get("pass") is not True:
    fail_reasons.append("Stage 13.1B 1200-step rerun missing or failed")
if s132 is None or s132.get("pass") is not True:
    fail_reasons.append("Stage 13.2C final 2400-step freeze missing or failed")

m1200 = {} if s131 is None else s131.get("parsed_summary", {})
m2400 = {} if s132 is None else s132.get("mixed_2400_summary", {})
w2400 = {} if s132 is None else s132.get("wbc_2400_summary", {})

scope_checks = {
    "simulation_only_project": (s12 or {}).get("simulation_only_project") is True,
    "hardware_deployment_completed_false": (s132 or {}).get("hardware_deployment_completed") is False,
    "torque_enable_ready_false": (s132 or {}).get("torque_enable_ready") is False,
    "torque_publisher_enabled_false": (s132 or {}).get("torque_publisher_enabled") is False,
    "control_law_changed_false": (s132 or {}).get("control_law_changed") is False,
    "baseline_type_mixed": (s132 or {}).get("baseline_type") == "mixed_online_control_baseline",
}

for k, ok in scope_checks.items():
    if ok is not True:
        fail_reasons.append(f"scope check failed: {k}")

metric_checks = {
    "m1200_pass": m1200.get("pass") is True,
    "m1200_total_steps_1200": m1200.get("total_steps") == 1200,
    "m1200_qp_fail_0": m1200.get("qp_fail_steps") == 0,
    "m1200_saturation_0": m1200.get("saturation_steps") == 0,
    "m2400_pass": m2400.get("pass") is True,
    "m2400_total_steps_2400": m2400.get("total_steps") == 2400,
    "m2400_qp_fail_0": m2400.get("qp_fail_steps") == 0,
    "m2400_saturation_0": m2400.get("saturation_steps") == 0,
    "m2400_min_z_ge_0p22": m2400.get("min_z", -999) >= 0.22,
    "m2400_roll_le_0p08": m2400.get("max_abs_roll", 999) <= 0.08,
    "m2400_pitch_le_0p08": m2400.get("max_abs_pitch", 999) <= 0.08,
    "m2400_joint_error_le_0p12": m2400.get("max_joint_error", 999) <= 0.12,
    "m2400_tau_le_23p7": m2400.get("max_tau_total_abs", 999) <= 23.7,
}

for k, ok in metric_checks.items():
    if ok is not True:
        fail_reasons.append(f"metric check failed: {k}")

rows = [
    {
        "experiment": "mixed_1200_step",
        "total_steps": m1200.get("total_steps"),
        "transition_count": m1200.get("transition_count"),
        "min_z": m1200.get("min_z"),
        "final_z": m1200.get("final_z"),
        "max_abs_roll": m1200.get("max_abs_roll"),
        "max_abs_pitch": m1200.get("max_abs_pitch"),
        "max_joint_error": m1200.get("max_joint_error"),
        "max_tau_total_abs": m1200.get("max_tau_total_abs"),
        "qp_fail_steps": m1200.get("qp_fail_steps"),
        "saturation_steps": m1200.get("saturation_steps"),
        "pass": m1200.get("pass"),
    },
    {
        "experiment": "mixed_2400_step",
        "total_steps": m2400.get("total_steps"),
        "transition_count": m2400.get("transition_count"),
        "min_z": m2400.get("min_z"),
        "final_z": m2400.get("final_z"),
        "max_abs_roll": m2400.get("max_abs_roll"),
        "max_abs_pitch": m2400.get("max_abs_pitch"),
        "max_joint_error": m2400.get("max_joint_error"),
        "max_tau_total_abs": m2400.get("max_tau_total_abs"),
        "qp_fail_steps": m2400.get("qp_fail_steps"),
        "saturation_steps": m2400.get("saturation_steps"),
        "pass": m2400.get("pass"),
    },
    {
        "experiment": "wbc_2400_step",
        "total_steps": w2400.get("total_steps"),
        "transition_count": w2400.get("transition_count"),
        "min_z": w2400.get("min_z"),
        "final_z": w2400.get("final_z"),
        "max_abs_roll": w2400.get("max_abs_roll"),
        "max_abs_pitch": w2400.get("max_abs_pitch"),
        "max_joint_error": "",
        "max_tau_total_abs": w2400.get("max_tau_total_abs"),
        "qp_fail_steps": w2400.get("qp_fail_steps"),
        "saturation_steps": w2400.get("saturation_steps"),
        "pass": w2400.get("pass"),
    },
]

with METRICS_CSV.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

evidence_files = {
    "stage12_22_summary": STAGE12_22,
    "stage13_1b_summary": STAGE13_1B,
    "stage13_2c_summary": STAGE13_2C,
    "stage13_3_metrics_csv": METRICS_CSV,
    "simulation_only_scope_doc": DOCS / "SIMULATION_ONLY_SCOPE.md",
    "simulation_only_results_summary": DOCS / "SIMULATION_ONLY_RESULTS_SUMMARY.md",
}

evidence_status = {k: status(v) for k, v in evidence_files.items()}
for k, st in evidence_status.items():
    if not st["exists"]:
        fail_reasons.append(f"missing evidence file: {k}")

summary = {
    "stage": "13.3",
    "name": "documentation_consolidation_and_report_ready_results_packaging",
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
    "scope_checks": scope_checks,
    "metric_checks": metric_checks,
    "metrics_table": str(METRICS_CSV),
    "report_ready_docs": {
        "stage13_3_doc": str(DOC),
        "report_ready_results": str(REPORT_MD),
        "claims_and_limitations": str(CLAIMS_MD),
    },
    "evidence_status": evidence_status,
    "allowed_claims": [
        "The project is simulation-only.",
        "The frozen baseline is mixed_online_control_baseline, not a hardware realtime controller.",
        "The 1200-step mixed baseline rerun passed.",
        "The 2400-step simulation-only mixed baseline robustness regression passed.",
        "ROS2/C++ torque streaming evidence is bounded zero/safe dry-run only."
    ],
    "disallowed_claims": [
        "Hardware deployment completed.",
        "Actuator enablement completed.",
        "Real robot torque execution completed.",
        "torque_enable_ready=True.",
        "A realtime hardware controller was completed."
    ],
    "next_stage": "Stage 13.4 optional plots/tables for report, or Stage 14 simulation-only improvement planning",
}

SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

doc_lines = [
    "# Stage 13.3 Report-Ready Results Packaging",
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
    "## Packaged metrics",
    "",
    f"- metrics_table: `{METRICS_CSV}`",
    "",
    "## Evidence status",
]

for k, st in evidence_status.items():
    doc_lines.append(f"- {k}: exists=`{st['exists']}`, sha256=`{st['sha256']}`, path=`{st['path']}`")

doc_lines += [
    "",
    "## Allowed claims",
]
doc_lines += [f"- {x}" for x in summary["allowed_claims"]]
doc_lines += ["", "## Disallowed claims"]
doc_lines += [f"- {x}" for x in summary["disallowed_claims"]]
doc_lines += ["", f"Next stage: `{summary['next_stage']}`"]
DOC.write_text("\n".join(doc_lines), encoding="utf-8")

report_lines = [
    "# Report-Ready Results",
    "",
    "## Scope",
    "",
    "This project is explicitly simulation-only. Hardware deployment, actuator enablement, and real robot torque execution are out of scope.",
    "",
    "## Baseline",
    "",
    "The evaluated baseline is `mixed_online_control_baseline`: stance PD + scaled WBC contribution plus swing PD tracking. It should not be described as a completed full realtime hardware WBC controller.",
    "",
    "## Main results",
    "",
    "| Experiment | Steps | Transitions | min_z | max_abs_roll | max_abs_pitch | max_joint_error | max_tau_total_abs | QP fails | Saturations | Pass |",
    "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
]

for row in rows:
    report_lines.append(
        f"| {row['experiment']} | {row['total_steps']} | {row['transition_count']} | "
        f"{row['min_z']} | {row['max_abs_roll']} | {row['max_abs_pitch']} | "
        f"{row['max_joint_error']} | {row['max_tau_total_abs']} | "
        f"{row['qp_fail_steps']} | {row['saturation_steps']} | {row['pass']} |"
    )

report_lines += [
    "",
    "## Safety statement",
    "",
    "No hardware deployment, actuator enablement, or real robot torque execution is claimed.",
]
REPORT_MD.write_text("\n".join(report_lines), encoding="utf-8")

claims_lines = [
    "# Report-Ready Claims and Limitations",
    "",
    "## Claims allowed by current evidence",
]
claims_lines += [f"- {x}" for x in summary["allowed_claims"]]
claims_lines += ["", "## Claims not supported by current evidence"]
claims_lines += [f"- {x}" for x in summary["disallowed_claims"]]
claims_lines += [
    "",
    "## Recommended wording",
    "",
    "Use: `simulation-only mixed online control baseline with safety-gated ROS2/C++ dry-run evidence`.",
    "",
    "Avoid: `hardware-ready torque controller`, `actuator-enabled controller`, or `real robot deployment`.",
]
CLAIMS_MD.write_text("\n".join(claims_lines), encoding="utf-8")

if summary["pass"]:
    block = f"""

## Stage 13.3 Report-Ready Results Packaging

- timestamp: `{summary['timestamp']}`
- pass: `True`
- simulation_only_project: `True`
- baseline_type: `mixed_online_control_baseline`
- metrics_table: `{METRICS_CSV}`
- report_ready_results: `{REPORT_MD}`
- claims_and_limitations: `{CLAIMS_MD}`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- next_stage: `{summary['next_stage']}`
"""
    old = PROJECT_STATUS.read_text(encoding="utf-8", errors="replace") if PROJECT_STATUS.exists() else ""
    if "## Stage 13.3 Report-Ready Results Packaging" not in old:
        PROJECT_STATUS.write_text(old.rstrip() + block + "\n", encoding="utf-8")

print(json.dumps(summary, indent=2, ensure_ascii=False))
