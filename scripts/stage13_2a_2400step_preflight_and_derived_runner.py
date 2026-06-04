#!/usr/bin/env /usr/bin/python3
from pathlib import Path
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

STAGE13_1B = OUT / "stage13_1b_rerun_1200step_simulation_only_mixed_baseline_summary.json"
SRC_SCRIPT = ROOT / "scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py"
DERIVED_SCRIPT = ROOT / "scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py"

SUMMARY = OUT / "stage13_2a_2400step_preflight_and_derived_runner_summary.json"
DOC = DOCS / "stage13_2a_2400step_preflight_and_derived_runner.md"

def sha256_file(path: Path):
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()

def sha256_text(text: str):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def read_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))

fail_reasons = []

stage13_1b = read_json(STAGE13_1B)
if stage13_1b is None:
    fail_reasons.append("missing Stage 13.1B summary")
else:
    required = {
        "stage13_1b_pass": stage13_1b.get("pass") is True,
        "rerun_returncode_0": stage13_1b.get("rerun_returncode") == 0,
        "rerun_timeout_false": stage13_1b.get("rerun_timeout") is False,
        "source_changed_false": stage13_1b.get("source_changed") is False,
        "simulation_only_project": stage13_1b.get("simulation_only_project") is True,
        "hardware_deployment_completed_false": stage13_1b.get("hardware_deployment_completed") is False,
        "torque_enable_ready_false": stage13_1b.get("torque_enable_ready") is False,
        "torque_publisher_enabled_false": stage13_1b.get("torque_publisher_enabled") is False,
        "control_law_changed_false": stage13_1b.get("control_law_changed") is False,
    }
    for k, ok in required.items():
        if not ok:
            fail_reasons.append(f"Stage 13.1B prerequisite failed: {k}")

if not SRC_SCRIPT.exists():
    fail_reasons.append("missing source Stage 7 recommended runner script")

src_hash_before = sha256_file(SRC_SCRIPT)
derived_hash = None
patch_replacements = {}
candidate_matches = {}

if SRC_SCRIPT.exists():
    src = SRC_SCRIPT.read_text(encoding="utf-8", errors="replace")

    patterns = {
        "total_steps_assignment": r"(\btotal_steps\s*=\s*)1200\b",
        "num_steps_assignment": r"(\bnum_steps\s*=\s*)1200\b",
        "n_steps_assignment": r"(\bn_steps\s*=\s*)1200\b",
        "steps_assignment": r"(\bsteps\s*=\s*)1200\b",
        "N_STEPS_assignment": r"(\bN_STEPS\s*=\s*)1200\b",
    }

    for name, pat in patterns.items():
        candidate_matches[name] = len(re.findall(pat, src))

    derived = src
    for name, pat in patterns.items():
        derived, n = re.subn(pat, r"\g<1>2400", derived)
        patch_replacements[name] = n

    total_replacements = sum(patch_replacements.values())

    if total_replacements <= 0:
        fail_reasons.append("could not locate direct 1200-step assignment to patch")

    if "2400" not in derived:
        fail_reasons.append("derived runner does not contain 2400 after patch")

    if total_replacements > 0 and not fail_reasons:
        header = (
            "# Stage 13.2 derived 2400-step simulation-only runner\n"
            "# Derived from scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py\n"
            "# Original source is not modified. Control law is not changed; only rollout horizon is extended.\n\n"
        )
        DERIVED_SCRIPT.write_text(header + derived, encoding="utf-8")
        DERIVED_SCRIPT.chmod(0o755)
        derived_hash = sha256_file(DERIVED_SCRIPT)

py_compile = None
if DERIVED_SCRIPT.exists():
    p = subprocess.run(
        ["/usr/bin/python3", "-m", "py_compile", str(DERIVED_SCRIPT)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    py_compile = {
        "returncode": p.returncode,
        "output": p.stdout,
    }
    if p.returncode != 0:
        fail_reasons.append("derived runner py_compile failed")

src_hash_after = sha256_file(SRC_SCRIPT)
if src_hash_before != src_hash_after:
    fail_reasons.append("original Stage 7 runner hash changed unexpectedly")

summary = {
    "stage": "13.2A",
    "name": "2400step_simulation_only_preflight_and_derived_runner_creation",
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
    "source_stage7_runner": str(SRC_SCRIPT),
    "derived_2400_runner": str(DERIVED_SCRIPT),
    "original_runner_hash_before": src_hash_before,
    "original_runner_hash_after": src_hash_after,
    "original_runner_unchanged": src_hash_before == src_hash_after,
    "derived_runner_hash": derived_hash,
    "candidate_matches": candidate_matches,
    "patch_replacements": patch_replacements,
    "derived_runner_exists": DERIVED_SCRIPT.exists(),
    "py_compile": py_compile,
    "stage13_1b_pass": None if stage13_1b is None else stage13_1b.get("pass"),
    "stage13_1b_total_steps": None if stage13_1b is None else stage13_1b.get("parsed_summary", {}).get("total_steps"),
    "recommended_next_stage": "Stage 13.2B run 2400-step simulation-only robustness regression" if len(fail_reasons) == 0 else "Stage 13.2A-R inspect 2400-step runner derivation failure",
}

SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

md = [
    "# Stage 13.2A 2400-Step Simulation-Only Preflight and Derived Runner Creation",
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
    f"- source_stage7_runner: `{summary['source_stage7_runner']}`",
    f"- derived_2400_runner: `{summary['derived_2400_runner']}`",
    f"- original_runner_unchanged: `{summary['original_runner_unchanged']}`",
    f"- derived_runner_exists: `{summary['derived_runner_exists']}`",
    f"- stage13_1b_pass: `{summary['stage13_1b_pass']}`",
    f"- stage13_1b_total_steps: `{summary['stage13_1b_total_steps']}`",
    "",
    "## Patch replacements",
]

for k, v in patch_replacements.items():
    md.append(f"- {k}: `{v}`")

md += [
    "",
    "## Python compile",
    "",
    f"- returncode: `{None if py_compile is None else py_compile.get('returncode')}`",
    "",
    f"Recommended next stage: `{summary['recommended_next_stage']}`",
]

DOC.write_text("\n".join(md), encoding="utf-8")

if summary["pass"]:
    block = f"""

## Stage 13.1B 1200-Step Simulation-Only Mixed Baseline Rerun

- timestamp: `{stage13_1b.get('timestamp') if stage13_1b else 'unknown'}`
- pass: `True`
- total_steps: `{stage13_1b.get('parsed_summary', {}).get('total_steps') if stage13_1b else 'unknown'}`
- qp_fail_steps: `{stage13_1b.get('parsed_summary', {}).get('qp_fail_steps') if stage13_1b else 'unknown'}`
- saturation_steps: `{stage13_1b.get('parsed_summary', {}).get('saturation_steps') if stage13_1b else 'unknown'}`
- min_z: `{stage13_1b.get('parsed_summary', {}).get('min_z') if stage13_1b else 'unknown'}`
- max_abs_roll: `{stage13_1b.get('parsed_summary', {}).get('max_abs_roll') if stage13_1b else 'unknown'}`
- max_abs_pitch: `{stage13_1b.get('parsed_summary', {}).get('max_abs_pitch') if stage13_1b else 'unknown'}`
- max_joint_error: `{stage13_1b.get('parsed_summary', {}).get('max_joint_error') if stage13_1b else 'unknown'}`
- max_tau_total_abs: `{stage13_1b.get('parsed_summary', {}).get('max_tau_total_abs') if stage13_1b else 'unknown'}`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

## Stage 13.2A 2400-Step Simulation-Only Preflight

- timestamp: `{summary['timestamp']}`
- pass: `True`
- original_runner_unchanged: `True`
- derived_runner_exists: `True`
- derived_2400_runner: `{summary['derived_2400_runner']}`
- control_law_changed: `False`
- next_stage: `{summary['recommended_next_stage']}`
"""
    old = PROJECT_STATUS.read_text(encoding="utf-8", errors="replace") if PROJECT_STATUS.exists() else ""
    if "## Stage 13.2A 2400-Step Simulation-Only Preflight" not in old:
        PROJECT_STATUS.write_text(old.rstrip() + block + "\n", encoding="utf-8")

print(json.dumps(summary, indent=2, ensure_ascii=False))
