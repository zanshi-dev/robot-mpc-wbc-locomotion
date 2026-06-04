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
BACKUP = OUT / "stage13_1b_backup"
OUT.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)
BACKUP.mkdir(parents=True, exist_ok=True)

STAGE13_1A = OUT / "stage13_1a_existing_stage7_baseline_summary_verification_summary.json"
RUN_SCRIPT = ROOT / "scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py"

STAGE7_SUMMARY = OUT / "stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test_summary.csv"
STAGE7_LOG = OUT / "stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test_log.csv"
STAGE7_SWING = OUT / "stage07_online_swing_trajectory_tracking_check.csv"

RUN_STDOUT = OUT / "stage13_1b_rerun_1200step_stdout.log"
SUMMARY_JSON = OUT / "stage13_1b_rerun_1200step_simulation_only_mixed_baseline_summary.json"
DOC = DOCS / "stage13_1b_rerun_1200step_simulation_only_mixed_baseline.md"

COPIED_SUMMARY = OUT / "stage13_1b_stage07_rerun_summary.csv"
COPIED_LOG = OUT / "stage13_1b_stage07_rerun_log.csv"
COPIED_SWING = OUT / "stage13_1b_stage07_rerun_swing_tracking.csv"

EXPECTED = {
    "total_steps": 1200,
    "transition_count": 5,
    "trot_FR_RL_steps": 600,
    "trot_FL_RR_steps": 600,
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

stage13_1a = read_json(STAGE13_1A)
if stage13_1a is None:
    fail_reasons.append("missing Stage 13.1A summary")
elif stage13_1a.get("pass") is not True:
    fail_reasons.append("Stage 13.1A did not pass")

if not RUN_SCRIPT.exists():
    fail_reasons.append("missing Stage 7 recommended rerun script")

pre_hashes = {
    "stage7_summary": sha256_file(STAGE7_SUMMARY),
    "stage7_log": sha256_file(STAGE7_LOG),
    "stage7_swing": sha256_file(STAGE7_SWING),
    "run_script": sha256_file(RUN_SCRIPT),
}

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
for p in [STAGE7_SUMMARY, STAGE7_LOG, STAGE7_SWING]:
    if p.exists():
        shutil.copy2(p, BACKUP / f"{timestamp}_{p.name}")

rerun_returncode = None
rerun_timeout = False

if not fail_reasons:
    try:
        proc = subprocess.run(
            ["/usr/bin/python3", str(RUN_SCRIPT)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=900,
        )
        rerun_returncode = proc.returncode
        RUN_STDOUT.write_text(proc.stdout, encoding="utf-8", errors="replace")
        if proc.returncode != 0:
            fail_reasons.append(f"Stage 7 rerun script returned nonzero: {proc.returncode}")
    except subprocess.TimeoutExpired as e:
        rerun_timeout = True
        RUN_STDOUT.write_text((e.stdout or "") + "\nTIMEOUT\n", encoding="utf-8", errors="replace")
        fail_reasons.append("Stage 7 rerun timed out")

post_hashes = {
    "stage7_summary": sha256_file(STAGE7_SUMMARY),
    "stage7_log": sha256_file(STAGE7_LOG),
    "stage7_swing": sha256_file(STAGE7_SWING),
    "run_script": sha256_file(RUN_SCRIPT),
}

for src, dst in [
    (STAGE7_SUMMARY, COPIED_SUMMARY),
    (STAGE7_LOG, COPIED_LOG),
    (STAGE7_SWING, COPIED_SWING),
]:
    if src.exists():
        shutil.copy2(src, dst)

if not STAGE7_SUMMARY.exists():
    fail_reasons.append("rerun did not produce Stage 7 summary CSV")
if not STAGE7_LOG.exists():
    fail_reasons.append("rerun did not produce Stage 7 log CSV")

summary_data = {}
checks = {}

if STAGE7_SUMMARY.exists():
    summary_data = parse_summary_csv(STAGE7_SUMMARY)

    for key, expected in EXPECTED.items():
        actual = summary_data.get(key)
        ok = actual == expected
        checks[f"{key}_eq_{expected}"] = {
            "actual": actual,
            "expected": expected,
            "pass": ok,
        }
        if not ok:
            fail_reasons.append(f"{key} mismatch: actual={actual}, expected={expected}")

    for key, (op, threshold) in THRESHOLDS.items():
        actual = summary_data.get(key)
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

source_changed = pre_hashes["run_script"] != post_hashes["run_script"]

if source_changed:
    fail_reasons.append("Stage 7 rerun script hash changed during rerun")

result = {
    "stage": "13.1B",
    "name": "rerun_1200step_simulation_only_mixed_baseline_regression",
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
    "source_changed": source_changed,
    "pre_hashes": pre_hashes,
    "post_hashes": post_hashes,
    "parsed_summary": summary_data,
    "checks": checks,
    "evidence_files": {
        "stdout": str(RUN_STDOUT),
        "copied_summary": str(COPIED_SUMMARY),
        "copied_log": str(COPIED_LOG),
        "copied_swing_tracking": str(COPIED_SWING),
        "backup_dir": str(BACKUP),
    },
    "recommended_next_stage": "Stage 13.2 2400-step simulation-only robustness regression" if len(fail_reasons) == 0 else "Stage 13.1B-R inspect rerun failure",
}

SUMMARY_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

md = [
    "# Stage 13.1B Rerun 1200-Step Simulation-Only Mixed Baseline Regression",
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
    f"- source_changed: `{result['source_changed']}`",
    "",
    "## Key checks",
]

for name, c in checks.items():
    md.append(f"- {name}: pass=`{c['pass']}`, actual=`{c.get('actual')}`")

md += [
    "",
    "## Evidence files",
    "",
    f"- stdout: `{RUN_STDOUT}`",
    f"- copied_summary: `{COPIED_SUMMARY}`",
    f"- copied_log: `{COPIED_LOG}`",
    f"- copied_swing_tracking: `{COPIED_SWING}`",
    f"- backup_dir: `{BACKUP}`",
    "",
    f"Recommended next stage: `{result['recommended_next_stage']}`",
]

DOC.write_text("\n".join(md), encoding="utf-8")

print(json.dumps(result, indent=2, ensure_ascii=False))
