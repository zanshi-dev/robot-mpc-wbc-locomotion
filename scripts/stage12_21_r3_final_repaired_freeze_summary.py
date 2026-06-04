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

R2D = OUT / "stage12_21_r2d_repair_capture_helper_and_rerun_summary.json"
SUMMARY = OUT / "stage12_21_r3_final_repaired_freeze_summary.json"
DOC = DOCS / "stage12_21_r3_final_repaired_freeze_summary.md"

EXPECTED_HASH = "b2d7371786b58300ca68be5542372d5cf8aa2814678b9f451e09bdb8061aa138"

def sha256_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def read_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))

fail_reasons = []
r2d = read_json(R2D)

if r2d is None:
    fail_reasons.append("missing Stage 12.21-R2D summary")
else:
    if r2d.get("pass") is not True:
        fail_reasons.append("Stage 12.21-R2D did not pass")

r2b = None if r2d is None else r2d.get("r2b_summary")

if r2b is None:
    fail_reasons.append("missing embedded R2B summary in R2D")
else:
    required = {
        "r2b_pass": r2b.get("pass") is True,
        "source_changed_false": r2b.get("source_changed") is False,
        "source_hash_matches_stage1220e": r2b.get("source_hash_matches_stage1220e") is True,
        "publish_call_count_is_1": r2b.get("publish_call_count") == 1,
        "subscriber_ready_before_activation": r2b.get("subscriber_ready_before_activation") is True,
        "capture_ok": r2b.get("capture_ok") is True,
        "stream_message_count_in_1_to_30": r2b.get("stream_message_count_in_1_to_30") is True,
        "all_stream_payloads_length_12": r2b.get("all_stream_payloads_length_12") is True,
        "all_stream_payload_values_finite": r2b.get("all_stream_payload_values_finite") is True,
        "all_stream_payload_values_zero_safe": r2b.get("all_stream_payload_values_zero_safe") is True,
        "after_stop_no_messages": r2b.get("after_stop_no_messages") is True,
        "final_flags_false": r2b.get("final_flags_false") is True,
        "target_process_after_count_is_0": r2b.get("target_process_after_count") == 0,
    }
    for k, ok in required.items():
        if not ok:
            fail_reasons.append(f"R2B repaired regression check failed: {k}")

source_hash = None
publish_call_count = None
if not SRC.exists():
    fail_reasons.append("missing disabled_controller_node.cpp")
else:
    src = SRC.read_text(encoding="utf-8", errors="replace")
    source_hash = sha256_text(src)
    publish_call_count = len(re.findall(r"(?:->|\.)publish\s*\(", src))
    if source_hash != EXPECTED_HASH:
        fail_reasons.append("source hash does not match Stage 12.20E frozen hash")
    if publish_call_count != 1:
        fail_reasons.append("publish_call_count is not 1")

summary = {
    "stage": "12.21-R3",
    "name": "final_repaired_freeze_summary_after_r2d",
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "pass": len(fail_reasons) == 0,
    "fail_reasons": fail_reasons,
    "stage1221_repaired_pass": len(fail_reasons) == 0,
    "stage1220_completed_remains_true": len(fail_reasons) == 0,
    "continuous_torque_streaming_completed": len(fail_reasons) == 0,
    "simulation_only_project": True,
    "hardware_deployment_scope": "out_of_scope_by_user_constraint",
    "hardware_deployment_completed": False,
    "torque_enable_ready": False,
    "torque_publisher_enabled": False,
    "control_law_changed": False,
    "baseline_type": "mixed_online_control_baseline",
    "source_hash": source_hash,
    "publish_call_count": publish_call_count,
    "r2d_pass": None if r2d is None else r2d.get("pass"),
    "r2b_stream_message_count": None if r2b is None else r2b.get("stream_message_count"),
    "r2b_after_stop_message_count": None if r2b is None else r2b.get("after_stop_message_count"),
    "next_stage": "Stage 12.22 simulation-only project scope freeze and documentation update",
}

SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

md = [
    "# Stage 12.21-R3 Final Repaired Freeze Summary",
    "",
    f"- pass: `{summary['pass']}`",
    f"- fail_reasons: `{summary['fail_reasons']}`",
    f"- stage1221_repaired_pass: `{summary['stage1221_repaired_pass']}`",
    f"- stage1220_completed_remains_true: `{summary['stage1220_completed_remains_true']}`",
    f"- continuous_torque_streaming_completed: `{summary['continuous_torque_streaming_completed']}`",
    f"- simulation_only_project: `{summary['simulation_only_project']}`",
    f"- hardware_deployment_scope: `{summary['hardware_deployment_scope']}`",
    f"- hardware_deployment_completed: `{summary['hardware_deployment_completed']}`",
    f"- torque_enable_ready: `{summary['torque_enable_ready']}`",
    f"- torque_publisher_enabled: `{summary['torque_publisher_enabled']}`",
    f"- control_law_changed: `{summary['control_law_changed']}`",
    f"- source_hash: `{summary['source_hash']}`",
    f"- publish_call_count: `{summary['publish_call_count']}`",
    f"- r2b_stream_message_count: `{summary['r2b_stream_message_count']}`",
    f"- r2b_after_stop_message_count: `{summary['r2b_after_stop_message_count']}`",
    "",
    "Project constraint: no hardware is available. Hardware deployment, actuator enablement, and real robot torque execution are out of scope. The project continues as simulation-only with MuJoCo, ROS2 topic dry-run, and reproducible safety-gated regression evidence.",
    "",
    f"Next stage: `{summary['next_stage']}`",
]
DOC.write_text("\n".join(md), encoding="utf-8")

if summary["pass"]:
    block = f"""

## Stage 12.21-R3 Final Repaired Freeze Summary

- timestamp: `{summary['timestamp']}`
- pass: `True`
- stage1221_repaired_pass: `True`
- stage1220_completed_remains_true: `True`
- continuous_torque_streaming_completed: `True`
- simulation_only_project: `True`
- hardware_deployment_scope: `out_of_scope_by_user_constraint`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- source_hash: `{summary['source_hash']}`
- publish_call_count: `{summary['publish_call_count']}`
- bounded streaming repaired regression: `pass`
- next_stage: `{summary['next_stage']}`
"""
    old = PROJECT_STATUS.read_text(encoding="utf-8", errors="replace") if PROJECT_STATUS.exists() else ""
    if "## Stage 12.21-R3 Final Repaired Freeze Summary" not in old:
        PROJECT_STATUS.write_text(old.rstrip() + block + "\n", encoding="utf-8")

print(json.dumps(summary, indent=2, ensure_ascii=False))
