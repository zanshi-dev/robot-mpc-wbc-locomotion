#!/usr/bin/env /usr/bin/python3
from pathlib import Path
import csv
import hashlib
import json
import math
import shutil
import subprocess
from datetime import datetime

ROOT = Path.cwd()
OUT = ROOT / "results/logs_sample"
DOCS = ROOT / "docs"
BACKUP = OUT / "stage13_2b_r1_backup"
PROJECT_STATUS = ROOT / "PROJECT_STATUS.md"

OUT.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)
BACKUP.mkdir(parents=True, exist_ok=True)

R2 = OUT / "stage13_2a_r2_create_2400step_derived_runner_summary.json"
PREV_13_2B = OUT / "stage13_2b_run_2400step_simulation_only_robustness_regression_summary.json"

SRC_CONTACT = OUT / "stage07_contact_schedule_wbc_qp.csv"
DERIVED_CONTACT = OUT / "stage13_2_2400step_contact_schedule_wbc_qp.csv"
DERIVED_SWING = OUT / "stage13_2_2400step_swing_trajectory_tracking_check.csv"

WBC_RUNNER = ROOT / "scripts/stage13_2_2400step_online_full_wbc_scheduler_runner.py"
MIXED_RUNNER = ROOT / "scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py"

WBC_STDOUT = OUT / "stage13_2b_r1_wbc_rerun_stdout.log"
MIXED_STDOUT = OUT / "stage13_2b_r1_mixed_rerun_stdout.log"

WBC_SUMMARY_CSV = OUT / "stage13_2_2400step_online_full_wbc_scheduler_summary.csv"
WBC_LOG_CSV = OUT / "stage13_2_2400step_online_full_wbc_scheduler_log.csv"
MIXED_SUMMARY_CSV = OUT / "stage13_2_2400step_mixed_baseline_summary.csv"
MIXED_LOG_CSV = OUT / "stage13_2_2400step_mixed_baseline_log.csv"

SUMMARY_JSON = OUT / "stage13_2b_r1_derive_contact_schedule_and_rerun_2400step_summary.json"
DOC = DOCS / "stage13_2b_r1_derive_contact_schedule_and_rerun_2400step.md"

COPIED_CONTACT = OUT / "stage13_2b_r1_2400step_contact_schedule_wbc_qp.csv"
COPIED_WBC_SUMMARY = OUT / "stage13_2b_r1_2400step_wbc_summary.csv"
COPIED_WBC_LOG = OUT / "stage13_2b_r1_2400step_wbc_log.csv"
COPIED_MIXED_SUMMARY = OUT / "stage13_2b_r1_2400step_mixed_summary.csv"
COPIED_MIXED_LOG = OUT / "stage13_2b_r1_2400step_mixed_log.csv"

EXPECTED = {
    "total_steps": 2400,
    "transition_count": 11,
    "trot_FR_RL_steps": 1200,
    "trot_FL_RR_steps": 1200,
    "pass": True,
    "pass_margin": True,
    "qp_fail_steps": 0,
    "saturation_steps": 0,
}

THRESHOLDS = {
    "min_z": (">=", 0.22),
    "max_abs_roll": ("<=", 0.08),
    "max_abs_pitch": ("<=", 0.08),
    "max_joint_error": ("<=", 0.12),
    "max_tau_total_abs": ("<=", 23.7),
}

def sha256_file(path):
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))

def parse_value(x):
    s = str(x).strip()
    if s.lower() in ("true", "false"):
        return s.lower() == "true"
    try:
        v = float(s)
        if math.isfinite(v) and abs(v - round(v)) < 1e-12:
            return int(round(v))
        return v
    except Exception:
        return s

def parse_summary_csv(path):
    rows = list(csv.reader(path.open("r", encoding="utf-8", errors="replace")))
    data = {}
    if not rows:
        return data

    if len(rows) >= 2 and len(rows[0]) == len(rows[1]):
        for k, v in zip(rows[0], rows[1]):
            data[k.strip()] = parse_value(v)
        return data

    for row in rows:
        if len(row) >= 2:
            data[row[0].strip()] = parse_value(row[1])
    return data

def csv_data_row_count(path):
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        return max(0, sum(1 for _ in f) - 1)

def derive_contact_schedule_2400(src, dst):
    with src.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    if not fieldnames:
        raise RuntimeError("source contact schedule has no header")
    if len(rows) <= 0:
        raise RuntimeError("source contact schedule has no data rows")

    tiled = []
    for step in range(2400):
        base = rows[step % len(rows)]
        row = dict(base)

        if "step" in fieldnames:
            row["step"] = str(step)
        if "global_step" in fieldnames:
            row["global_step"] = str(step)

        tiled.append(row)

    with dst.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tiled)

    return len(rows), len(tiled), fieldnames

fail_reasons = []

r2 = read_json(R2)
prev_13_2b = read_json(PREV_13_2B)

if r2 is None:
    fail_reasons.append("missing Stage 13.2A-R2 summary")
elif r2.get("pass") is not True:
    fail_reasons.append("Stage 13.2A-R2 did not pass")

for name, path in [
    ("source contact schedule", SRC_CONTACT),
    ("derived swing CSV", DERIVED_SWING),
    ("WBC runner", WBC_RUNNER),
    ("mixed runner", MIXED_RUNNER),
]:
    if not path.exists():
        fail_reasons.append(f"missing {name}: {path}")

pre_hashes = {
    "src_contact": sha256_file(SRC_CONTACT),
    "derived_swing": sha256_file(DERIVED_SWING),
    "wbc_runner": sha256_file(WBC_RUNNER),
    "mixed_runner": sha256_file(MIXED_RUNNER),
}

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
for p in [DERIVED_CONTACT, WBC_SUMMARY_CSV, WBC_LOG_CSV, MIXED_SUMMARY_CSV, MIXED_LOG_CSV]:
    if p.exists():
        shutil.copy2(p, BACKUP / f"{timestamp}_{p.name}")

source_contact_rows = None
derived_contact_rows = None
contact_fieldnames = None

if not fail_reasons:
    try:
        source_contact_rows, derived_contact_rows, contact_fieldnames = derive_contact_schedule_2400(SRC_CONTACT, DERIVED_CONTACT)
    except Exception as e:
        fail_reasons.append(f"failed to derive 2400-step contact schedule: {repr(e)}")

if derived_contact_rows != 2400:
    fail_reasons.append(f"derived contact row count mismatch: {derived_contact_rows}, expected 2400")

wbc_returncode = None
wbc_timeout = False
mixed_returncode = None
mixed_timeout = False

if not fail_reasons:
    try:
        p = subprocess.run(
            ["/usr/bin/python3", str(WBC_RUNNER)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=1800,
        )
        wbc_returncode = p.returncode
        WBC_STDOUT.write_text(p.stdout, encoding="utf-8", errors="replace")
        if p.returncode != 0:
            fail_reasons.append(f"derived WBC runner returned nonzero: {p.returncode}")
    except subprocess.TimeoutExpired as e:
        wbc_timeout = True
        WBC_STDOUT.write_text((e.stdout or "") + "\nTIMEOUT\n", encoding="utf-8", errors="replace")
        fail_reasons.append("derived WBC runner timed out")

if not fail_reasons:
    try:
        p = subprocess.run(
            ["/usr/bin/python3", str(MIXED_RUNNER)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=1800,
        )
        mixed_returncode = p.returncode
        MIXED_STDOUT.write_text(p.stdout, encoding="utf-8", errors="replace")
        if p.returncode != 0:
            fail_reasons.append(f"derived mixed runner returned nonzero: {p.returncode}")
    except subprocess.TimeoutExpired as e:
        mixed_timeout = True
        MIXED_STDOUT.write_text((e.stdout or "") + "\nTIMEOUT\n", encoding="utf-8", errors="replace")
        fail_reasons.append("derived mixed runner timed out")

post_hashes = {
    "src_contact": sha256_file(SRC_CONTACT),
    "derived_contact": sha256_file(DERIVED_CONTACT),
    "derived_swing": sha256_file(DERIVED_SWING),
    "wbc_runner": sha256_file(WBC_RUNNER),
    "mixed_runner": sha256_file(MIXED_RUNNER),
    "wbc_summary": sha256_file(WBC_SUMMARY_CSV),
    "wbc_log": sha256_file(WBC_LOG_CSV),
    "mixed_summary": sha256_file(MIXED_SUMMARY_CSV),
    "mixed_log": sha256_file(MIXED_LOG_CSV),
}

if pre_hashes["src_contact"] != post_hashes["src_contact"]:
    fail_reasons.append("source contact schedule changed")
if pre_hashes["derived_swing"] != post_hashes["derived_swing"]:
    fail_reasons.append("derived swing CSV changed")
if pre_hashes["wbc_runner"] != post_hashes["wbc_runner"]:
    fail_reasons.append("derived WBC runner changed")
if pre_hashes["mixed_runner"] != post_hashes["mixed_runner"]:
    fail_reasons.append("derived mixed runner changed")

for name, path in [
    ("derived contact schedule", DERIVED_CONTACT),
    ("WBC summary CSV", WBC_SUMMARY_CSV),
    ("WBC log CSV", WBC_LOG_CSV),
    ("mixed summary CSV", MIXED_SUMMARY_CSV),
    ("mixed log CSV", MIXED_LOG_CSV),
]:
    if not path.exists():
        fail_reasons.append(f"missing output file: {name}")

for src, dst in [
    (DERIVED_CONTACT, COPIED_CONTACT),
    (WBC_SUMMARY_CSV, COPIED_WBC_SUMMARY),
    (WBC_LOG_CSV, COPIED_WBC_LOG),
    (MIXED_SUMMARY_CSV, COPIED_MIXED_SUMMARY),
    (MIXED_LOG_CSV, COPIED_MIXED_LOG),
]:
    if src.exists():
        shutil.copy2(src, dst)

mixed_summary = parse_summary_csv(MIXED_SUMMARY_CSV) if MIXED_SUMMARY_CSV.exists() else {}
wbc_summary = parse_summary_csv(WBC_SUMMARY_CSV) if WBC_SUMMARY_CSV.exists() else {}

checks = {}

for key, expected in EXPECTED.items():
    actual = mixed_summary.get(key)
    ok = actual == expected
    checks[f"{key}_eq_{expected}"] = {
        "actual": actual,
        "expected": expected,
        "pass": ok,
    }
    if not ok:
        fail_reasons.append(f"{key} mismatch: actual={actual}, expected={expected}")

for key, (op, threshold) in THRESHOLDS.items():
    actual = mixed_summary.get(key)
    ok = False
    if isinstance(actual, (int, float)):
        if op == ">=":
            ok = actual >= threshold
        elif op == "<=":
            ok = actual <= threshold
    checks[f"{key}_{op}_{threshold}"] = {
        "actual": actual,
        "threshold": threshold,
        "pass": ok,
    }
    if not ok:
        fail_reasons.append(f"{key} threshold failed: actual={actual}, required {op} {threshold}")

result = {
    "stage": "13.2B-R1",
    "name": "derive_2400step_contact_schedule_and_rerun_robustness_regression",
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
    "previous_stage13_2b_pass": None if prev_13_2b is None else prev_13_2b.get("pass"),
    "previous_stage13_2b_failure_classified_as_missing_contact_schedule": True,
    "source_contact_rows": source_contact_rows,
    "derived_contact_rows": derived_contact_rows,
    "derived_contact_line_count": None if not DERIVED_CONTACT.exists() else len(DERIVED_CONTACT.read_text(encoding="utf-8", errors="replace").splitlines()),
    "wbc_returncode": wbc_returncode,
    "wbc_timeout": wbc_timeout,
    "mixed_returncode": mixed_returncode,
    "mixed_timeout": mixed_timeout,
    "runner_changed": pre_hashes["mixed_runner"] != post_hashes["mixed_runner"],
    "wbc_runner_changed": pre_hashes["wbc_runner"] != post_hashes["wbc_runner"],
    "derived_swing_changed": pre_hashes["derived_swing"] != post_hashes["derived_swing"],
    "source_contact_changed": pre_hashes["src_contact"] != post_hashes["src_contact"],
    "pre_hashes": pre_hashes,
    "post_hashes": post_hashes,
    "parsed_mixed_summary": mixed_summary,
    "parsed_wbc_summary": wbc_summary,
    "checks": checks,
    "evidence_files": {
        "wbc_stdout": str(WBC_STDOUT),
        "mixed_stdout": str(MIXED_STDOUT),
        "derived_contact": str(COPIED_CONTACT),
        "wbc_summary": str(COPIED_WBC_SUMMARY),
        "wbc_log": str(COPIED_WBC_LOG),
        "mixed_summary": str(COPIED_MIXED_SUMMARY),
        "mixed_log": str(COPIED_MIXED_LOG),
        "backup_dir": str(BACKUP),
    },
    "recommended_next_stage": "Stage 13.2C final 2400-step robustness evidence freeze" if len(fail_reasons) == 0 else "Stage 13.2B-R2 inspect repaired 2400-step regression failure",
}

SUMMARY_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

md = [
    "# Stage 13.2B-R1 Derive Contact Schedule and Rerun 2400-Step Robustness Regression",
    "",
    f"- pass: `{result['pass']}`",
    f"- fail_reasons: `{result['fail_reasons']}`",
    f"- simulation_only_project: `{result['simulation_only_project']}`",
    f"- hardware_deployment_scope: `{result['hardware_deployment_scope']}`",
    f"- hardware_deployment_completed: `{result['hardware_deployment_completed']}`",
    f"- torque_enable_ready: `{result['torque_enable_ready']}`",
    f"- torque_publisher_enabled: `{result['torque_publisher_enabled']}`",
    f"- control_law_changed: `{result['control_law_changed']}`",
    f"- baseline_type: `{result['baseline_type']}`",
    f"- source_contact_rows: `{result['source_contact_rows']}`",
    f"- derived_contact_rows: `{result['derived_contact_rows']}`",
    f"- derived_contact_line_count: `{result['derived_contact_line_count']}`",
    f"- wbc_returncode: `{result['wbc_returncode']}`",
    f"- wbc_timeout: `{result['wbc_timeout']}`",
    f"- mixed_returncode: `{result['mixed_returncode']}`",
    f"- mixed_timeout: `{result['mixed_timeout']}`",
    f"- runner_changed: `{result['runner_changed']}`",
    f"- wbc_runner_changed: `{result['wbc_runner_changed']}`",
    f"- derived_swing_changed: `{result['derived_swing_changed']}`",
    f"- source_contact_changed: `{result['source_contact_changed']}`",
    "",
    "## Key checks",
]

for name, c in checks.items():
    md.append(f"- {name}: pass=`{c['pass']}`, actual=`{c.get('actual')}`")

md += [
    "",
    "## Evidence files",
    f"- wbc_stdout: `{WBC_STDOUT}`",
    f"- mixed_stdout: `{MIXED_STDOUT}`",
    f"- derived_contact: `{COPIED_CONTACT}`",
    f"- wbc_summary: `{COPIED_WBC_SUMMARY}`",
    f"- wbc_log: `{COPIED_WBC_LOG}`",
    f"- mixed_summary: `{COPIED_MIXED_SUMMARY}`",
    f"- mixed_log: `{COPIED_MIXED_LOG}`",
    "",
    f"Recommended next stage: `{result['recommended_next_stage']}`",
]

DOC.write_text("\n".join(md), encoding="utf-8")

if result["pass"]:
    block = f"""

## Stage 13.2B-R1 2400-Step Simulation-Only Robustness Regression

- timestamp: `{result['timestamp']}`
- pass: `True`
- previous_stage13_2b_failure_classified_as_missing_contact_schedule: `True`
- total_steps: `{mixed_summary.get('total_steps')}`
- transition_count: `{mixed_summary.get('transition_count')}`
- trot_FR_RL_steps: `{mixed_summary.get('trot_FR_RL_steps')}`
- trot_FL_RR_steps: `{mixed_summary.get('trot_FL_RR_steps')}`
- qp_fail_steps: `{mixed_summary.get('qp_fail_steps')}`
- saturation_steps: `{mixed_summary.get('saturation_steps')}`
- min_z: `{mixed_summary.get('min_z')}`
- max_abs_roll: `{mixed_summary.get('max_abs_roll')}`
- max_abs_pitch: `{mixed_summary.get('max_abs_pitch')}`
- max_joint_error: `{mixed_summary.get('max_joint_error')}`
- max_tau_total_abs: `{mixed_summary.get('max_tau_total_abs')}`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- next_stage: `{result['recommended_next_stage']}`
"""
    old = PROJECT_STATUS.read_text(encoding="utf-8", errors="replace") if PROJECT_STATUS.exists() else ""
    if "## Stage 13.2B-R1 2400-Step Simulation-Only Robustness Regression" not in old:
        PROJECT_STATUS.write_text(old.rstrip() + block + "\n", encoding="utf-8")

print(json.dumps(result, indent=2, ensure_ascii=False))
