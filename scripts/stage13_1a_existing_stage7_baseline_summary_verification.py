#!/usr/bin/env /usr/bin/python3
from pathlib import Path
import csv
import json
import math
from datetime import datetime

ROOT = Path.cwd()
OUT = ROOT / "results/logs_sample"
DOCS = ROOT / "docs"
OUT.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)

STAGE13_0 = OUT / "stage13_0_simulation_only_locomotion_preflight_inventory_summary.json"
SUMMARY_CSV = OUT / "stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test_summary.csv"
LOG_CSV = OUT / "stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test_log.csv"

SUMMARY_JSON = OUT / "stage13_1a_existing_stage7_baseline_summary_verification_summary.json"
DOC = DOCS / "stage13_1a_existing_stage7_baseline_summary_verification.md"

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
    "min_z_min": 0.22,
    "max_abs_roll_max": 0.08,
    "max_abs_pitch_max": 0.08,
    "max_joint_error_max": 0.12,
    "max_tau_total_abs_max": 23.7,
}

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

    # Case 1: two-column key,value CSV
    if len(rows[0]) >= 2 and rows[0][0].strip().lower() in ("metric", "key", "name"):
        for row in rows[1:]:
            if len(row) >= 2:
                data[row[0].strip()] = parse_value(row[1])
        return data

    # Case 2: single-row header + single-row values
    if len(rows) >= 2 and len(rows[0]) == len(rows[1]):
        for k, v in zip(rows[0], rows[1]):
            data[k.strip()] = parse_value(v)
        return data

    # Case 3: raw key,value lines without header
    for row in rows:
        if len(row) >= 2:
            data[row[0].strip()] = parse_value(row[1])

    return data

fail_reasons = []
stage13_0 = read_json(STAGE13_0)

if stage13_0 is None:
    fail_reasons.append("missing Stage 13.0 summary")
elif stage13_0.get("pass") is not True:
    fail_reasons.append("Stage 13.0 did not pass")
elif stage13_0.get("simulation_only_project") is not True:
    fail_reasons.append("Stage 13.0 did not freeze simulation_only_project=True")

if not SUMMARY_CSV.exists():
    fail_reasons.append("missing Stage 7 recommended summary CSV")
if not LOG_CSV.exists():
    fail_reasons.append("missing Stage 7 recommended log CSV")

summary_data = {}
if SUMMARY_CSV.exists():
    summary_data = parse_summary_csv(SUMMARY_CSV)

checks = {}

def check_eq(key, expected):
    actual = summary_data.get(key)
    ok = actual == expected
    checks[f"{key}_eq_{expected}"] = {"actual": actual, "expected": expected, "pass": ok}
    if not ok:
        fail_reasons.append(f"{key} mismatch: actual={actual}, expected={expected}")

def check_threshold(key, op, threshold):
    actual = summary_data.get(key)
    ok = False
    if isinstance(actual, (int, float)):
        if op == ">=":
            ok = actual >= threshold
        elif op == "<=":
            ok = actual <= threshold
    checks[f"{key}_{op}_{threshold}"] = {"actual": actual, "threshold": threshold, "pass": ok}
    if not ok:
        fail_reasons.append(f"{key} threshold failed: actual={actual}, required {op} {threshold}")

for k, v in EXPECTED.items():
    check_eq(k, v)

check_threshold("min_z", ">=", THRESHOLDS["min_z_min"])
check_threshold("max_abs_roll", "<=", THRESHOLDS["max_abs_roll_max"])
check_threshold("max_abs_pitch", "<=", THRESHOLDS["max_abs_pitch_max"])
check_threshold("max_joint_error", "<=", THRESHOLDS["max_joint_error_max"])
check_threshold("max_tau_total_abs", "<=", THRESHOLDS["max_tau_total_abs_max"])

result = {
    "stage": "13.1A",
    "name": "existing_stage7_mixed_baseline_summary_verification",
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
    "summary_csv": str(SUMMARY_CSV),
    "log_csv": str(LOG_CSV),
    "parsed_summary": summary_data,
    "checks": checks,
    "recommended_next_stage": "Stage 13.1B rerun 1200-step simulation-only mixed baseline regression" if len(fail_reasons) == 0 else "Stage 13.1A-R repair/inspect Stage 7 summary parsing or missing files",
}

SUMMARY_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

md = [
    "# Stage 13.1A Existing Stage 7 Mixed Baseline Summary Verification",
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
    "",
    "## Key checks",
]

for name, c in checks.items():
    md.append(f"- {name}: pass=`{c['pass']}`, actual=`{c.get('actual')}`")

md += ["", f"Recommended next stage: `{result['recommended_next_stage']}`"]
DOC.write_text("\n".join(md), encoding="utf-8")

print(json.dumps(result, indent=2, ensure_ascii=False))
