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
BACKUP = OUT / "stage13_2b_backup"
OUT.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)
BACKUP.mkdir(parents=True, exist_ok=True)

R2 = OUT / "stage13_2a_r2_create_2400step_derived_runner_summary.json"
RUNNER = ROOT / "scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py"

MIXED_SUMMARY_CSV = OUT / "stage13_2_2400step_mixed_baseline_summary.csv"
MIXED_LOG_CSV = OUT / "stage13_2_2400step_mixed_baseline_log.csv"
WBC_SUMMARY_CSV = OUT / "stage13_2_2400step_online_full_wbc_scheduler_summary.csv"
WBC_LOG_CSV = OUT / "stage13_2_2400step_online_full_wbc_scheduler_log.csv"
SWING_CSV = OUT / "stage13_2_2400step_swing_trajectory_tracking_check.csv"

RUN_STDOUT = OUT / "stage13_2b_run_2400step_stdout.log"
SUMMARY_JSON = OUT / "stage13_2b_run_2400step_simulation_only_robustness_regression_summary.json"
DOC = DOCS / "stage13_2b_run_2400step_simulation_only_robustness_regression.md"

COPIED_MIXED_SUMMARY = OUT / "stage13_2b_2400step_mixed_baseline_summary.csv"
COPIED_MIXED_LOG = OUT / "stage13_2b_2400step_mixed_baseline_log.csv"
COPIED_WBC_SUMMARY = OUT / "stage13_2b_2400step_wbc_summary.csv"
COPIED_WBC_LOG = OUT / "stage13_2b_2400step_wbc_log.csv"

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

    if len(rows[0]) >= 2 and rows[0][0].strip().lower() in ("metric", "key", "name"):
        for row in rows[1:]:
            if len(row) >= 2:
                data[row[0].strip()] = parse_value(row[1])
        return data

    if len(rows) >= 2 and len(rows[0]) == len(rows[1]):
        for k, v in zip(rows[0], rows[1]):
            data[k.strip()] = parse_value(v)
        return data

    for row in rows:
        if len(row) >= 2:
            data[row[0].strip()] = parse_value(row[1])
    return data

fail_reasons = []

r2 = read_json(R2)
if r2 is None:
    fail_reasons.append("missing Stage 13.2A-R2 summary")
elif r2.get("pass") is not True:
    fail_reasons.append("Stage 13.2A-R2 did not pass")

if not RUNNER.exists():
    fail_reasons.append("missing 2400-step derived recommended runner")

if not SWING_CSV.exists():
    fail_reasons.append("missing 2400-step derived swing target CSV")
else:
    swing_line_count = len(SWING_CSV.read_text(encoding="utf-8", errors="replace").splitlines())
    if swing_line_count != 2401:
        fail_reasons.append(f"2400-step swing CSV line count mismatch: {swing_line_count}, expected 2401 including header")

pre_hashes = {
    "runner": sha256_file(RUNNER),
    "swing_csv": sha256_file(SWING_CSV),
    "mixed_summary": sha256_file(MIXED_SUMMARY_CSV),
    "mixed_log": sha256_file(MIXED_LOG_CSV),
    "wbc_summary": sha256_file(WBC_SUMMARY_CSV),
    "wbc_log": sha256_file(WBC_LOG_CSV),
}

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
for p in [MIXED_SUMMARY_CSV, MIXED_LOG_CSV, WBC_SUMMARY_CSV, WBC_LOG_CSV]:
    if p.exists():
        shutil.copy2(p, BACKUP / f"{timestamp}_{p.name}")

rerun_returncode = None
rerun_timeout = False

if not fail_reasons:
    try:
        proc = subprocess.run(
            ["/usr/bin/python3", str(RUNNER)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=1800,
        )
        rerun_returncode = proc.returncode
        RUN_STDOUT.write_text(proc.stdout, encoding="utf-8", errors="replace")
        if proc.returncode != 0:
            fail_reasons.append(f"2400-step runner returned nonzero: {proc.returncode}")
    except subprocess.TimeoutExpired as e:
        rerun_timeout = True
        out = e.stdout if isinstance(e.stdout, str) else ""
        RUN_STDOUT.write_text(out + "\nTIMEOUT\n", encoding="utf-8", errors="replace")
        fail_reasons.append("2400-step runner timed out")

post_hashes = {
    "runner": sha256_file(RUNNER),
    "swing_csv": sha256_file(SWING_CSV),
    "mixed_summary": sha256_file(MIXED_SUMMARY_CSV),
    "mixed_log": sha256_file(MIXED_LOG_CSV),
    "wbc_summary": sha256_file(WBC_SUMMARY_CSV),
    "wbc_log": sha256_file(WBC_LOG_CSV),
}

if pre_hashes["runner"] != post_hashes["runner"]:
    fail_reasons.append("derived runner changed during 2400-step run")
if pre_hashes["swing_csv"] != post_hashes["swing_csv"]:
    fail_reasons.append("derived swing CSV changed during 2400-step run")

for src, dst in [
    (MIXED_SUMMARY_CSV, COPIED_MIXED_SUMMARY),
    (MIXED_LOG_CSV, COPIED_MIXED_LOG),
    (WBC_SUMMARY_CSV, COPIED_WBC_SUMMARY),
    (WBC_LOG_CSV, COPIED_WBC_LOG),
]:
    if src.exists():
        shutil.copy2(src, dst)

if not MIXED_SUMMARY_CSV.exists():
    fail_reasons.append("2400-step run did not produce mixed baseline summary CSV")
if not MIXED_LOG_CSV.exists():
    fail_reasons.append("2400-step run did not produce mixed baseline log CSV")
if not WBC_SUMMARY_CSV.exists():
    fail_reasons.append("2400-step run did not produce WBC summary CSV")
if not WBC_LOG_CSV.exists():
    fail_reasons.append("2400-step run did not produce WBC log CSV")

mixed_summary = {}
wbc_summary = {}
checks = {}

if MIXED_SUMMARY_CSV.exists():
    mixed_summary = parse_summary_csv(MIXED_SUMMARY_CSV)

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

if WBC_SUMMARY_CSV.exists():
    wbc_summary = parse_summary_csv(WBC_SUMMARY_CSV)

result = {
    "stage": "13.2B",
    "name": "run_2400step_simulation_only_robustness_regression",
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
    "rerun_returncode": rerun_returncode,
    "rerun_timeout": rerun_timeout,
    "runner_changed": pre_hashes["runner"] != post_hashes["runner"],
    "swing_csv_changed": pre_hashes["swing_csv"] != post_hashes["swing_csv"],
    "pre_hashes": pre_hashes,
    "post_hashes": post_hashes,
    "parsed_mixed_summary": mixed_summary,
    "parsed_wbc_summary": wbc_summary,
    "checks": checks,
    "evidence_files": {
        "stdout": str(RUN_STDOUT),
        "mixed_summary": str(COPIED_MIXED_SUMMARY),
        "mixed_log": str(COPIED_MIXED_LOG),
        "wbc_summary": str(COPIED_WBC_SUMMARY),
        "wbc_log": str(COPIED_WBC_LOG),
        "backup_dir": str(BACKUP),
    },
    "recommended_next_stage": "Stage 13.2C final 2400-step robustness evidence freeze" if len(fail_reasons) == 0 else "Stage 13.2B-R inspect 2400-step robustness regression failure",
}

SUMMARY_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

md = [
    "# Stage 13.2B 2400-Step Simulation-Only Robustness Regression",
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
    f"- rerun_returncode: `{result['rerun_returncode']}`",
    f"- rerun_timeout: `{result['rerun_timeout']}`",
    f"- runner_changed: `{result['runner_changed']}`",
    f"- swing_csv_changed: `{result['swing_csv_changed']}`",
    "",
    "## Key checks",
]

for name, c in checks.items():
    md.append(f"- {name}: pass=`{c['pass']}`, actual=`{c.get('actual')}`")

md += [
    "",
    "## Evidence files",
    f"- stdout: `{RUN_STDOUT}`",
    f"- mixed_summary: `{COPIED_MIXED_SUMMARY}`",
    f"- mixed_log: `{COPIED_MIXED_LOG}`",
    f"- wbc_summary: `{COPIED_WBC_SUMMARY}`",
    f"- wbc_log: `{COPIED_WBC_LOG}`",
    "",
    f"Recommended next stage: `{result['recommended_next_stage']}`",
]

DOC.write_text("\n".join(md), encoding="utf-8")

print(json.dumps(result, indent=2, ensure_ascii=False))
