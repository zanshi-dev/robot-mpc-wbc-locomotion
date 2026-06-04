#!/usr/bin/env /usr/bin/python3
from pathlib import Path
import hashlib
import json
from datetime import datetime

ROOT = Path.cwd()
OUT = ROOT / "results/logs_sample"
DOCS = ROOT / "docs"
PROJECT_STATUS = ROOT / "PROJECT_STATUS.md"

SUMMARY = OUT / "stage13_4b_report_ready_package_manifest_freeze_summary.json"
MANIFEST_JSON = OUT / "stage13_4b_report_ready_package_manifest.json"
MANIFEST_MD = DOCS / "REPORT_READY_PACKAGE_MANIFEST.md"
DOC = DOCS / "stage13_4b_report_ready_package_manifest_freeze.md"

STAGE13_4A = OUT / "stage13_4a_report_ready_plots_and_tables_summary.json"
STAGE13_3 = OUT / "stage13_3_report_ready_results_packaging_summary.json"
STAGE13_2C = OUT / "stage13_2c_final_2400step_robustness_evidence_freeze_summary.json"

REQUIRED_FILES = {
    "stage13_4a_summary": STAGE13_4A,
    "stage13_3_summary": STAGE13_3,
    "stage13_2c_summary": STAGE13_2C,
    "report_ready_results": DOCS / "REPORT_READY_RESULTS.md",
    "claims_and_limitations": DOCS / "REPORT_READY_CLAIMS_AND_LIMITATIONS.md",
    "figures_index": DOCS / "REPORT_READY_FIGURES.md",
    "metrics_table_md": DOCS / "REPORT_READY_METRICS_TABLE.md",
    "simulation_only_scope": DOCS / "SIMULATION_ONLY_SCOPE.md",
    "simulation_only_results_summary": DOCS / "SIMULATION_ONLY_RESULTS_SUMMARY.md",
    "metrics_table_csv": OUT / "stage13_3_report_ready_metrics_table.csv",
}

def sha256_file(path):
    p = Path(path)
    if not p.exists() or not p.is_file():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read_json(path):
    if not Path(path).exists():
        return None
    return json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))

def file_status(path):
    p = Path(path)
    return {
        "path": str(p),
        "exists": p.exists(),
        "size": p.stat().st_size if p.exists() else None,
        "sha256": sha256_file(p),
    }

fail_reasons = []

s134a = read_json(STAGE13_4A)
s133 = read_json(STAGE13_3)
s132c = read_json(STAGE13_2C)

if s134a is None or s134a.get("pass") is not True:
    fail_reasons.append("Stage 13.4A missing or failed")
if s133 is None or s133.get("pass") is not True:
    fail_reasons.append("Stage 13.3 missing or failed")
if s132c is None or s132c.get("pass") is not True:
    fail_reasons.append("Stage 13.2C missing or failed")

scope_checks = {
    "simulation_only_project": (s134a or {}).get("simulation_only_project") is True,
    "hardware_deployment_completed_false": (s134a or {}).get("hardware_deployment_completed") is False,
    "torque_enable_ready_false": (s134a or {}).get("torque_enable_ready") is False,
    "torque_publisher_enabled_false": (s134a or {}).get("torque_publisher_enabled") is False,
    "control_law_changed_false": (s134a or {}).get("control_law_changed") is False,
    "baseline_type_mixed": (s134a or {}).get("baseline_type") == "mixed_online_control_baseline",
}

for k, ok in scope_checks.items():
    if ok is not True:
        fail_reasons.append(f"scope check failed: {k}")

figure_paths = []
if s134a:
    figure_paths = list((s134a.get("figures") or {}).values())

for i, p in enumerate(figure_paths):
    REQUIRED_FILES[f"figure_{i+1}_{Path(p).stem}"] = Path(p)

manifest = {k: file_status(v) for k, v in REQUIRED_FILES.items()}

missing = [k for k, st in manifest.items() if not st["exists"]]
empty = [k for k, st in manifest.items() if st["exists"] and (st["size"] is None or st["size"] <= 0)]

if missing:
    fail_reasons.append(f"missing package files: {missing}")
if empty:
    fail_reasons.append(f"empty package files: {empty}")

summary = {
    "stage": "13.4B",
    "name": "report_ready_package_manifest_freeze",
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
    "manifest_json": str(MANIFEST_JSON),
    "manifest_md": str(MANIFEST_MD),
    "package_file_count": len(manifest),
    "manifest": manifest,
    "final_statement": "Report-ready simulation-only package frozen. No hardware deployment, actuator enablement, or real robot torque execution is claimed.",
    "next_stage": "Stage 14 simulation-only improvement planning, or stop at report-ready package",
}

MANIFEST_JSON.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

md_lines = [
    "# Report-Ready Package Manifest",
    "",
    f"- frozen_at: `{summary['timestamp']}`",
    f"- simulation_only_project: `{summary['simulation_only_project']}`",
    f"- hardware_deployment_completed: `{summary['hardware_deployment_completed']}`",
    f"- torque_enable_ready: `{summary['torque_enable_ready']}`",
    f"- torque_publisher_enabled: `{summary['torque_publisher_enabled']}`",
    f"- control_law_changed: `{summary['control_law_changed']}`",
    f"- baseline_type: `{summary['baseline_type']}`",
    "",
    "## Files",
    "",
]

for name, st in manifest.items():
    md_lines.append(f"- {name}: exists=`{st['exists']}`, size=`{st['size']}`, sha256=`{st['sha256']}`, path=`{st['path']}`")

md_lines += [
    "",
    "## Final statement",
    "",
    summary["final_statement"],
]

MANIFEST_MD.write_text("\n".join(md_lines), encoding="utf-8")

doc_lines = [
    "# Stage 13.4B Report-Ready Package Manifest Freeze",
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
    f"- package_file_count: `{summary['package_file_count']}`",
    f"- manifest_json: `{summary['manifest_json']}`",
    f"- manifest_md: `{summary['manifest_md']}`",
    "",
    f"Next stage: `{summary['next_stage']}`",
]

DOC.write_text("\n".join(doc_lines), encoding="utf-8")

if summary["pass"]:
    block = f"""

## Stage 13.4B Report-Ready Package Manifest Freeze

- timestamp: `{summary['timestamp']}`
- pass: `True`
- simulation_only_project: `True`
- baseline_type: `mixed_online_control_baseline`
- package_file_count: `{summary['package_file_count']}`
- manifest_json: `{MANIFEST_JSON}`
- manifest_md: `{MANIFEST_MD}`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- next_stage: `{summary['next_stage']}`
"""
    old = PROJECT_STATUS.read_text(encoding="utf-8", errors="replace") if PROJECT_STATUS.exists() else ""
    if "## Stage 13.4B Report-Ready Package Manifest Freeze" not in old:
        PROJECT_STATUS.write_text(old.rstrip() + block + "\n", encoding="utf-8")

print(json.dumps(summary, indent=2, ensure_ascii=False))
