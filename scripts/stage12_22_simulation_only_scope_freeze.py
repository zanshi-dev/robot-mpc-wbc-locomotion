#!/usr/bin/env /usr/bin/python3
from pathlib import Path
import hashlib
import json
import re
from datetime import datetime

ROOT = Path.cwd()
OUT = ROOT / "results/logs_sample"
DOCS = ROOT / "docs"
PROJECT_STATUS = ROOT / "PROJECT_STATUS.md"
SRC = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"

OUT.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)

R3 = OUT / "stage12_21_r3_final_repaired_freeze_summary.json"
SUMMARY = OUT / "stage12_22_simulation_only_scope_freeze_summary.json"
DOC = DOCS / "stage12_22_simulation_only_scope_freeze.md"
SCOPE_DOC = DOCS / "SIMULATION_ONLY_SCOPE.md"

EXPECTED_HASH = "b2d7371786b58300ca68be5542372d5cf8aa2814678b9f451e09bdb8061aa138"

def read_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))

def sha256_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

fail_reasons = []

r3 = read_json(R3)
if r3 is None:
    fail_reasons.append("missing Stage 12.21-R3 summary")
else:
    checks = {
        "r3_pass": r3.get("pass") is True,
        "stage1221_repaired_pass": r3.get("stage1221_repaired_pass") is True,
        "stage1220_completed_remains_true": r3.get("stage1220_completed_remains_true") is True,
        "continuous_torque_streaming_completed": r3.get("continuous_torque_streaming_completed") is True,
        "simulation_only_project": r3.get("simulation_only_project") is True,
        "hardware_deployment_scope_out_of_scope": r3.get("hardware_deployment_scope") == "out_of_scope_by_user_constraint",
        "hardware_deployment_completed_false": r3.get("hardware_deployment_completed") is False,
        "torque_enable_ready_false": r3.get("torque_enable_ready") is False,
        "torque_publisher_enabled_false": r3.get("torque_publisher_enabled") is False,
        "control_law_changed_false": r3.get("control_law_changed") is False,
    }
    for k, ok in checks.items():
        if not ok:
            fail_reasons.append(f"Stage 12.21-R3 check failed: {k}")

source_hash = None
publish_call_count = None
if not SRC.exists():
    fail_reasons.append("missing disabled_controller_node.cpp")
else:
    src = SRC.read_text(encoding="utf-8", errors="replace")
    source_hash = sha256_text(src)
    publish_call_count = len(re.findall(r"(?:->|\.)publish\s*\(", src))
    if source_hash != EXPECTED_HASH:
        fail_reasons.append("source hash does not match Stage 12.20E/12.21-R3 frozen hash")
    if publish_call_count != 1:
        fail_reasons.append("publish_call_count is not 1")

summary = {
    "stage": "12.22",
    "name": "simulation_only_project_scope_freeze_and_documentation_update",
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "pass": len(fail_reasons) == 0,
    "fail_reasons": fail_reasons,
    "simulation_only_project": True,
    "hardware_available": False,
    "hardware_deployment_scope": "out_of_scope_by_user_constraint",
    "hardware_deployment_completed": False,
    "real_robot_torque_execution_scope": "out_of_scope",
    "actuator_hardware_enablement_scope": "out_of_scope",
    "torque_enable_ready": False,
    "torque_publisher_enabled": False,
    "control_law_changed": False,
    "baseline_type": "mixed_online_control_baseline",
    "allowed_future_work": [
        "MuJoCo closed-loop locomotion regression",
        "ROS2 topic dry-run validation",
        "simulation-only safety-gated controller evidence",
        "documentation/report/paper-ready experiment packaging",
        "Python-to-C++ interface consistency checks without hardware deployment"
    ],
    "disallowed_future_work": [
        "hardware deployment",
        "actuator hardware enablement",
        "real robot torque execution",
        "claiming torque_enable_ready=True",
        "claiming realtime hardware controller completion"
    ],
    "source_hash": source_hash,
    "publish_call_count": publish_call_count,
    "previous_stage": "Stage 12.21-R3",
    "next_stage": "Stage 13 simulation-only MuJoCo locomotion regression and documentation consolidation",
}

SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

scope_lines = [
    "# Simulation-Only Project Scope",
    "",
    "This project is now explicitly scoped as simulation-only.",
    "",
    "## In scope",
    "",
    "- Unitree Go1 MuJoCo simulation.",
    "- ROS2 topic dry-run validation.",
    "- C++ controller safety-gated bounded zero/safe torque streaming dry-run.",
    "- Reproducible logs, summaries, docs, and regression evidence.",
    "- Python prototype and ROS2/C++ interface consistency checks.",
    "- Report/paper/defense-ready experiment packaging.",
    "",
    "## Out of scope",
    "",
    "- Hardware deployment.",
    "- Real actuator enablement.",
    "- Real robot torque execution.",
    "- Claiming `torque_enable_ready=True`.",
    "- Claiming hardware realtime controller completion.",
    "",
    "## Current frozen evidence",
    "",
    f"- Stage 12.21-R3 pass: `{None if r3 is None else r3.get('pass')}`",
    f"- continuous_torque_streaming_completed: `{None if r3 is None else r3.get('continuous_torque_streaming_completed')}`",
    f"- source_hash: `{source_hash}`",
    f"- publish_call_count: `{publish_call_count}`",
    "- hardware_deployment_completed: `False`",
    "- torque_enable_ready: `False`",
    "- torque_publisher_enabled: `False`",
    "- control_law_changed: `False`",
]
SCOPE_DOC.write_text("\n".join(scope_lines), encoding="utf-8")

doc_lines = [
    "# Stage 12.22 Simulation-Only Scope Freeze",
    "",
    f"- pass: `{summary['pass']}`",
    f"- fail_reasons: `{summary['fail_reasons']}`",
    f"- simulation_only_project: `{summary['simulation_only_project']}`",
    f"- hardware_available: `{summary['hardware_available']}`",
    f"- hardware_deployment_scope: `{summary['hardware_deployment_scope']}`",
    f"- hardware_deployment_completed: `{summary['hardware_deployment_completed']}`",
    f"- real_robot_torque_execution_scope: `{summary['real_robot_torque_execution_scope']}`",
    f"- actuator_hardware_enablement_scope: `{summary['actuator_hardware_enablement_scope']}`",
    f"- torque_enable_ready: `{summary['torque_enable_ready']}`",
    f"- torque_publisher_enabled: `{summary['torque_publisher_enabled']}`",
    f"- control_law_changed: `{summary['control_law_changed']}`",
    f"- baseline_type: `{summary['baseline_type']}`",
    f"- source_hash: `{summary['source_hash']}`",
    f"- publish_call_count: `{summary['publish_call_count']}`",
    "",
    "## Allowed future work",
    "",
]
doc_lines += [f"- {x}" for x in summary["allowed_future_work"]]
doc_lines += ["", "## Disallowed future work", ""]
doc_lines += [f"- {x}" for x in summary["disallowed_future_work"]]
doc_lines += ["", f"Next stage: `{summary['next_stage']}`"]
DOC.write_text("\n".join(doc_lines), encoding="utf-8")

if summary["pass"]:
    block = f"""

## Stage 12.22 Simulation-Only Scope Freeze

- timestamp: `{summary['timestamp']}`
- pass: `True`
- simulation_only_project: `True`
- hardware_available: `False`
- hardware_deployment_scope: `out_of_scope_by_user_constraint`
- hardware_deployment_completed: `False`
- real_robot_torque_execution_scope: `out_of_scope`
- actuator_hardware_enablement_scope: `out_of_scope`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- source_hash: `{summary['source_hash']}`
- publish_call_count: `{summary['publish_call_count']}`
- next_stage: `{summary['next_stage']}`
"""
    old = PROJECT_STATUS.read_text(encoding="utf-8", errors="replace") if PROJECT_STATUS.exists() else ""
    if "## Stage 12.22 Simulation-Only Scope Freeze" not in old:
        PROJECT_STATUS.write_text(old.rstrip() + block + "\n", encoding="utf-8")

print(json.dumps(summary, indent=2, ensure_ascii=False))
