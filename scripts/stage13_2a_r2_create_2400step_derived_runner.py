#!/usr/bin/env /usr/bin/python3
from pathlib import Path
import csv
import hashlib
import json
import re
import subprocess
from datetime import datetime

ROOT = Path.cwd()
OUT = ROOT / "results/logs_sample"
DOCS = ROOT / "docs"
PROJECT_STATUS = ROOT / "PROJECT_STATUS.md"

OUT.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)

R1 = OUT / "stage13_2a_r1_runner_structure_inspection_summary.json"

SRC_WBC = ROOT / "scripts/stage07_online_full_wbc_scheduler_recommended_run.py"
SRC_RECOMMENDED = ROOT / "scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py"
SRC_SWING = OUT / "stage07_online_swing_trajectory_tracking_check.csv"

DERIVED_WBC = ROOT / "scripts/stage13_2_2400step_online_full_wbc_scheduler_runner.py"
DERIVED_RECOMMENDED = ROOT / "scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py"
DERIVED_SWING = OUT / "stage13_2_2400step_swing_trajectory_tracking_check.csv"

SUMMARY = OUT / "stage13_2a_r2_create_2400step_derived_runner_summary.json"
DOC = DOCS / "stage13_2a_r2_create_2400step_derived_runner.md"

def sha256_file(path: Path):
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))

def py_compile(path: Path):
    p = subprocess.run(
        ["/usr/bin/python3", "-m", "py_compile", str(path)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return {"returncode": p.returncode, "output": p.stdout}

fail_reasons = []

r1 = read_json(R1)
if r1 is None:
    fail_reasons.append("missing Stage 13.2A-R1 summary")
elif r1.get("pass") is not True:
    fail_reasons.append("Stage 13.2A-R1 did not pass")

for name, path in [
    ("source WBC runner", SRC_WBC),
    ("source recommended runner", SRC_RECOMMENDED),
    ("source swing target CSV", SRC_SWING),
]:
    if not path.exists():
        fail_reasons.append(f"missing {name}: {path}")

pre_hashes = {
    "src_wbc": sha256_file(SRC_WBC),
    "src_recommended": sha256_file(SRC_RECOMMENDED),
    "src_swing": sha256_file(SRC_SWING),
}

patch_info = {}

# 1. Derive WBC runner: TOTAL_STEPS 1200 -> 2400 and stage13_2 output paths.
if SRC_WBC.exists():
    text = SRC_WBC.read_text(encoding="utf-8", errors="replace")
    derived = text

    derived, n_total = re.subn(
        r"(^\s*TOTAL_STEPS\s*=\s*)1200\b",
        r"\g<1>2400",
        derived,
        count=1,
        flags=re.MULTILINE,
    )

    replacements = {
        'CONTACT_WBC_CSV = "results/logs_sample/stage07_contact_schedule_wbc_qp.csv"':
            'CONTACT_WBC_CSV = "results/logs_sample/stage13_2_2400step_contact_schedule_wbc_qp.csv"',
        'LOG_CSV = "results/logs_sample/stage07_online_full_wbc_scheduler_recommended_run_log.csv"':
            'LOG_CSV = "results/logs_sample/stage13_2_2400step_online_full_wbc_scheduler_log.csv"',
        'SUMMARY_CSV = "results/logs_sample/stage07_online_full_wbc_scheduler_recommended_run_summary.csv"':
            'SUMMARY_CSV = "results/logs_sample/stage13_2_2400step_online_full_wbc_scheduler_summary.csv"',
    }

    path_replacements = {}
    for old, new in replacements.items():
        count = derived.count(old)
        derived = derived.replace(old, new)
        path_replacements[old] = count

    patch_info["wbc_total_steps_replacements"] = n_total
    patch_info["wbc_path_replacements"] = path_replacements

    if n_total != 1:
        fail_reasons.append(f"WBC TOTAL_STEPS replacement count is {n_total}, expected 1")

    header = (
        "# Stage 13.2 derived 2400-step WBC runner.\n"
        "# Original Stage 7 WBC runner is not modified.\n"
        "# Control law is unchanged; rollout horizon and evidence output paths are derived for simulation-only robustness regression.\n\n"
    )
    DERIVED_WBC.write_text(header + derived, encoding="utf-8")
    DERIVED_WBC.chmod(0o755)

# 2. Derive 2400 swing target CSV by tiling the validated 1200-row target once.
swing_row_count = None
derived_swing_row_count = None
if SRC_SWING.exists():
    with SRC_SWING.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    swing_row_count = len(rows)
    if swing_row_count != 1200:
        fail_reasons.append(f"source swing target row count is {swing_row_count}, expected 1200")

    tiled = []
    if fieldnames:
        for repeat_i in range(2):
            for row in rows:
                new_row = dict(row)
                new_row["step"] = str(int(row["step"]) + repeat_i * swing_row_count)
                tiled.append(new_row)

        with DERIVED_SWING.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(tiled)

        derived_swing_row_count = len(tiled)
    else:
        fail_reasons.append("source swing target CSV has no header")

# 3. Derive recommended mixed baseline runner: point to derived WBC runner, derived swing target CSV, and stage13_2 outputs.
if SRC_RECOMMENDED.exists():
    text = SRC_RECOMMENDED.read_text(encoding="utf-8", errors="replace")
    derived = text

    replacements = {
        'WBC_SCRIPT = "scripts/stage07_online_full_wbc_scheduler_recommended_run.py"':
            'WBC_SCRIPT = "scripts/stage13_2_2400step_online_full_wbc_scheduler_runner.py"',
        'SWING_TARGET_CSV = "results/logs_sample/stage07_online_swing_trajectory_tracking_check.csv"':
            'SWING_TARGET_CSV = "results/logs_sample/stage13_2_2400step_swing_trajectory_tracking_check.csv"',
        'LOG_CSV = "results/logs_sample/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test_log.csv"':
            'LOG_CSV = "results/logs_sample/stage13_2_2400step_mixed_baseline_log.csv"',
        'SUMMARY_CSV = "results/logs_sample/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test_summary.csv"':
            'SUMMARY_CSV = "results/logs_sample/stage13_2_2400step_mixed_baseline_summary.csv"',
        'print("Stage 7 online stance PD WBC plus swing PD recommended test")':
            'print("Stage 13.2 2400-step simulation-only mixed baseline regression")',
    }

    wrapper_path_replacements = {}
    for old, new in replacements.items():
        count = derived.count(old)
        derived = derived.replace(old, new)
        wrapper_path_replacements[old] = count

    patch_info["recommended_path_replacements"] = wrapper_path_replacements

    if wrapper_path_replacements.get('WBC_SCRIPT = "scripts/stage07_online_full_wbc_scheduler_recommended_run.py"', 0) != 1:
        fail_reasons.append("recommended wrapper WBC_SCRIPT replacement count is not 1")
    if wrapper_path_replacements.get('SWING_TARGET_CSV = "results/logs_sample/stage07_online_swing_trajectory_tracking_check.csv"', 0) != 1:
        fail_reasons.append("recommended wrapper SWING_TARGET_CSV replacement count is not 1")
    if wrapper_path_replacements.get('LOG_CSV = "results/logs_sample/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test_log.csv"', 0) != 1:
        fail_reasons.append("recommended wrapper LOG_CSV replacement count is not 1")
    if wrapper_path_replacements.get('SUMMARY_CSV = "results/logs_sample/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test_summary.csv"', 0) != 1:
        fail_reasons.append("recommended wrapper SUMMARY_CSV replacement count is not 1")

    header = (
        "# Stage 13.2 derived 2400-step simulation-only mixed baseline runner.\n"
        "# Original Stage 7 recommended runner is not modified.\n"
        "# Control law is unchanged; WBC horizon and target CSV are derived for 2400-step robustness regression.\n\n"
    )
    DERIVED_RECOMMENDED.write_text(header + derived, encoding="utf-8")
    DERIVED_RECOMMENDED.chmod(0o755)

post_hashes = {
    "src_wbc": sha256_file(SRC_WBC),
    "src_recommended": sha256_file(SRC_RECOMMENDED),
    "src_swing": sha256_file(SRC_SWING),
    "derived_wbc": sha256_file(DERIVED_WBC),
    "derived_recommended": sha256_file(DERIVED_RECOMMENDED),
    "derived_swing": sha256_file(DERIVED_SWING),
}

if pre_hashes["src_wbc"] != post_hashes["src_wbc"]:
    fail_reasons.append("source WBC runner changed")
if pre_hashes["src_recommended"] != post_hashes["src_recommended"]:
    fail_reasons.append("source recommended runner changed")
if pre_hashes["src_swing"] != post_hashes["src_swing"]:
    fail_reasons.append("source swing target CSV changed")

compile_wbc = py_compile(DERIVED_WBC) if DERIVED_WBC.exists() else None
compile_recommended = py_compile(DERIVED_RECOMMENDED) if DERIVED_RECOMMENDED.exists() else None

if compile_wbc is None or compile_wbc["returncode"] != 0:
    fail_reasons.append("derived WBC runner py_compile failed")
if compile_recommended is None or compile_recommended["returncode"] != 0:
    fail_reasons.append("derived recommended runner py_compile failed")

# Static confirmation.
derived_wbc_text = DERIVED_WBC.read_text(encoding="utf-8", errors="replace") if DERIVED_WBC.exists() else ""
derived_rec_text = DERIVED_RECOMMENDED.read_text(encoding="utf-8", errors="replace") if DERIVED_RECOMMENDED.exists() else ""

static_checks = {
    "derived_wbc_has_TOTAL_STEPS_2400": bool(re.search(r"^\s*TOTAL_STEPS\s*=\s*2400\b", derived_wbc_text, re.MULTILINE)),
    "derived_wbc_no_TOTAL_STEPS_1200": not bool(re.search(r"^\s*TOTAL_STEPS\s*=\s*1200\b", derived_wbc_text, re.MULTILINE)),
    "derived_recommended_points_to_derived_wbc": "scripts/stage13_2_2400step_online_full_wbc_scheduler_runner.py" in derived_rec_text,
    "derived_recommended_points_to_derived_swing_csv": "results/logs_sample/stage13_2_2400step_swing_trajectory_tracking_check.csv" in derived_rec_text,
    "derived_swing_row_count_2400": derived_swing_row_count == 2400,
}

for k, ok in static_checks.items():
    if not ok:
        fail_reasons.append(f"static check failed: {k}")

summary = {
    "stage": "13.2A-R2",
    "name": "create_2400step_derived_wbc_runner_recommended_runner_and_swing_target",
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
    "source_changed": False,
    "original_sources_unchanged": (
        pre_hashes["src_wbc"] == post_hashes["src_wbc"]
        and pre_hashes["src_recommended"] == post_hashes["src_recommended"]
        and pre_hashes["src_swing"] == post_hashes["src_swing"]
    ),
    "pre_hashes": pre_hashes,
    "post_hashes": post_hashes,
    "patch_info": patch_info,
    "swing_row_count": swing_row_count,
    "derived_swing_row_count": derived_swing_row_count,
    "static_checks": static_checks,
    "compile_wbc": compile_wbc,
    "compile_recommended": compile_recommended,
    "derived_files": {
        "derived_wbc_runner": str(DERIVED_WBC),
        "derived_recommended_runner": str(DERIVED_RECOMMENDED),
        "derived_swing_target_csv": str(DERIVED_SWING),
    },
    "recommended_next_stage": "Stage 13.2B run 2400-step simulation-only robustness regression" if len(fail_reasons) == 0 else "Stage 13.2A-R2-R inspect derived runner creation failure",
}

SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

md = [
    "# Stage 13.2A-R2 Create 2400-Step Derived Runner",
    "",
    f"- pass: `{summary['pass']}`",
    f"- fail_reasons: `{summary['fail_reasons']}`",
    f"- simulation_only_project: `{summary['simulation_only_project']}`",
    f"- hardware_deployment_scope: `{summary['hardware_deployment_scope']}`",
    f"- hardware_deployment_completed: `{summary['hardware_deployment_completed']}`",
    f"- torque_enable_ready: `{summary['torque_enable_ready']}`",
    f"- torque_publisher_enabled: `{summary['torque_publisher_enabled']}`",
    f"- control_law_changed: `{summary['control_law_changed']}`",
    f"- original_sources_unchanged: `{summary['original_sources_unchanged']}`",
    f"- swing_row_count: `{summary['swing_row_count']}`",
    f"- derived_swing_row_count: `{summary['derived_swing_row_count']}`",
    "",
    "## Static checks",
]

for k, v in static_checks.items():
    md.append(f"- {k}: `{v}`")

md += [
    "",
    "## Compile checks",
    f"- derived WBC returncode: `{None if compile_wbc is None else compile_wbc.get('returncode')}`",
    f"- derived recommended returncode: `{None if compile_recommended is None else compile_recommended.get('returncode')}`",
    "",
    "## Derived files",
    f"- derived_wbc_runner: `{DERIVED_WBC}`",
    f"- derived_recommended_runner: `{DERIVED_RECOMMENDED}`",
    f"- derived_swing_target_csv: `{DERIVED_SWING}`",
    "",
    f"Recommended next stage: `{summary['recommended_next_stage']}`",
]

DOC.write_text("\n".join(md), encoding="utf-8")

if summary["pass"]:
    block = f"""

## Stage 13.2A-R2 2400-Step Derived Runner Creation

- timestamp: `{summary['timestamp']}`
- pass: `True`
- original_sources_unchanged: `True`
- derived_wbc_runner: `{DERIVED_WBC}`
- derived_recommended_runner: `{DERIVED_RECOMMENDED}`
- derived_swing_target_csv: `{DERIVED_SWING}`
- derived_swing_row_count: `{derived_swing_row_count}`
- control_law_changed: `False`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- next_stage: `{summary['recommended_next_stage']}`
"""
    old = PROJECT_STATUS.read_text(encoding="utf-8", errors="replace") if PROJECT_STATUS.exists() else ""
    if "## Stage 13.2A-R2 2400-Step Derived Runner Creation" not in old:
        PROJECT_STATUS.write_text(old.rstrip() + block + "\n", encoding="utf-8")

print(json.dumps(summary, indent=2, ensure_ascii=False))
