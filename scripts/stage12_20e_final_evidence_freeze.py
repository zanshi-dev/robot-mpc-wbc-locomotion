#!/usr/bin/env /usr/bin/python3
from pathlib import Path
import hashlib
import json
import re
from datetime import datetime

ROOT = Path.cwd()
SRC = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
OUT_DIR = ROOT / "results/logs_sample"
DOC_DIR = ROOT / "docs"
PROJECT_STATUS = ROOT / "PROJECT_STATUS.md"

OUT_DIR.mkdir(parents=True, exist_ok=True)
DOC_DIR.mkdir(parents=True, exist_ok=True)

B_R3_SUMMARY = OUT_DIR / "stage12_20b_r3_repair_summary.json"
B_R3_BUILD_RC = OUT_DIR / "stage12_20b_r3_colcon_build_returncode.txt"
C_R1_SUMMARY = OUT_DIR / "stage12_20c_r1_runtime_default_off_regression_summary.json"
D_R1_SUMMARY = OUT_DIR / "stage12_20d_r1_reparse_existing_evidence_summary.json"

SUMMARY_JSON = OUT_DIR / "stage12_20e_final_evidence_freeze_summary.json"
DOC_MD = DOC_DIR / "stage12_20e_final_evidence_freeze.md"

def read_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def count_publish_calls(text: str) -> int:
    return len(re.findall(r"(?:->|\.)publish\s*\(", text))

def as_bool(x):
    return bool(x) is True

fail_reasons = []

b_r3 = read_json(B_R3_SUMMARY)
c_r1 = read_json(C_R1_SUMMARY)
d_r1 = read_json(D_R1_SUMMARY)

if b_r3 is None:
    fail_reasons.append("missing Stage 12.20B-R3 summary")
if c_r1 is None:
    fail_reasons.append("missing Stage 12.20C-R1 summary")
if d_r1 is None:
    fail_reasons.append("missing Stage 12.20D-R1 summary")

build_returncode = None
if B_R3_BUILD_RC.exists():
    build_returncode = B_R3_BUILD_RC.read_text(encoding="utf-8", errors="replace").strip()
else:
    fail_reasons.append("missing Stage 12.20B-R3 build returncode")

source_hash = None
source_exists = SRC.exists()
source_text = ""

if not source_exists:
    fail_reasons.append("missing disabled_controller_node.cpp")
else:
    source_text = SRC.read_text(encoding="utf-8", errors="replace")
    source_hash = sha256_text(source_text)

expected_source_hash = None
if b_r3:
    expected_source_hash = b_r3.get("post_hash")

source_checks = {
    "source_exists": source_exists,
    "source_hash": source_hash,
    "expected_source_hash_from_stage1220b_r3": expected_source_hash,
    "source_hash_matches_stage1220b_r3": source_hash == expected_source_hash if source_hash and expected_source_hash else False,
    "publish_call_count": count_publish_calls(source_text) if source_text else None,
    "publish_call_count_is_1": count_publish_calls(source_text) == 1 if source_text else False,
    "has_enable_continuous_torque_streaming": "enable_continuous_torque_streaming" in source_text,
    "has_confirm_continuous_torque_streaming": "confirm_continuous_torque_streaming" in source_text,
    "has_continuous_timer": "continuous_torque_streaming_timer_" in source_text,
    "has_four_flag_gate": "four_flag_gate" in source_text,
    "has_10hz_timer": "std::chrono::milliseconds(100)" in source_text,
    "has_max_ticks_30_bound": "max_ticks > 30" in source_text,
    "has_max_duration_3s_bound": "max_duration_sec > 3.0" in source_text,
    "has_repaired_helper_call_with_args": "publishBoundedZeroSafeTorqueOnceIfAllowed(enable_torque_publisher, confirm_torque_publisher_enable, true)" in source_text,
}

if source_exists:
    if not source_checks["source_hash_matches_stage1220b_r3"]:
        fail_reasons.append("current source hash does not match Stage 12.20B-R3 post_hash")
    if not source_checks["publish_call_count_is_1"]:
        fail_reasons.append("current source publish_call_count is not 1")
    for key in [
        "has_enable_continuous_torque_streaming",
        "has_confirm_continuous_torque_streaming",
        "has_continuous_timer",
        "has_four_flag_gate",
        "has_10hz_timer",
        "has_max_ticks_30_bound",
        "has_max_duration_3s_bound",
        "has_repaired_helper_call_with_args",
    ]:
        if not source_checks[key]:
            fail_reasons.append(f"source static check failed: {key}")

b_r3_checks = {}
if b_r3:
    b_r3_checks = {
        "pass": b_r3.get("pass") is True,
        "patch_applied": b_r3.get("patch_applied") is True,
        "post_publish_call_count_is_1": b_r3.get("post_publish_call_count") == 1,
        "post_zero_arg_helper_call_count_is_0": b_r3.get("post_zero_arg_helper_call_count") == 0,
        "post_repaired_helper_call_count_ge_1": b_r3.get("post_repaired_helper_call_count", 0) >= 1,
        "post_has_four_flag_gate": b_r3.get("post_has_four_flag_gate") is True,
        "post_has_continuous_timer": b_r3.get("post_has_continuous_timer") is True,
        "post_rate_limited_to_10hz": b_r3.get("post_rate_limited_to_10hz") is True,
        "build_returncode_is_0": build_returncode == "0",
    }
    for key, value in b_r3_checks.items():
        if not value:
            fail_reasons.append(f"Stage 12.20B-R3 check failed: {key}")

c_r1_checks = {}
if c_r1:
    c_r1_checks = {
        "pass": c_r1.get("pass") is True,
        "node_seen": c_r1.get("node_seen") is True,
        "params_default_false": c_r1.get("params_default_false") is True,
        "echo_returncode_124": c_r1.get("echo_returncode") == 124,
        "echo_timeout": c_r1.get("echo_timeout") is True,
        "echo_has_data_false": c_r1.get("echo_has_data") is False,
        "torque_command_published_under_default_false_false": c_r1.get("torque_command_published_under_default_false") is False,
        "torque_enable_ready_false": c_r1.get("torque_enable_ready") is False,
        "torque_publisher_enabled_false": c_r1.get("torque_publisher_enabled") is False,
        "hardware_deployment_completed_false": c_r1.get("hardware_deployment_completed") is False,
        "control_law_changed_false": c_r1.get("control_law_changed") is False,
    }
    for key, value in c_r1_checks.items():
        if not value:
            fail_reasons.append(f"Stage 12.20C-R1 check failed: {key}")

d_r1_checks = {}
if d_r1:
    d_r1_checks = {
        "pass": d_r1.get("pass") is True,
        "node_seen": d_r1.get("node_seen") is True,
        "param_set_ok": d_r1.get("param_set_ok") is True,
        "stream_message_count_in_1_to_30": d_r1.get("stream_message_count_in_1_to_30") is True,
        "all_stream_payloads_length_12": d_r1.get("all_stream_payloads_length_12") is True,
        "all_stream_payload_values_finite": d_r1.get("all_stream_payload_values_finite") is True,
        "all_stream_payload_values_zero_safe": d_r1.get("all_stream_payload_values_zero_safe") is True,
        "final_flags_false": d_r1.get("final_flags_false") is True,
        "after_stop_echo_timeout": d_r1.get("after_stop_echo_timeout") is True,
        "after_stop_echo_has_data_false": d_r1.get("after_stop_echo_has_data") is False,
        "continuous_torque_streaming_completed": d_r1.get("continuous_torque_streaming_completed") is True,
        "torque_enable_ready_false": d_r1.get("torque_enable_ready") is False,
        "torque_publisher_enabled_false": d_r1.get("torque_publisher_enabled") is False,
        "hardware_deployment_completed_false": d_r1.get("hardware_deployment_completed") is False,
        "control_law_changed_false": d_r1.get("control_law_changed") is False,
    }
    for key, value in d_r1_checks.items():
        if not value:
            fail_reasons.append(f"Stage 12.20D-R1 check failed: {key}")

summary = {
    "stage": "12.20E",
    "name": "final_evidence_freeze_for_bounded_continuous_zero_safe_streaming",
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "pass": len(fail_reasons) == 0,
    "fail_reasons": fail_reasons,
    "stage1220_completed": len(fail_reasons) == 0,
    "continuous_torque_streaming_completed": len(fail_reasons) == 0,
    "torque_enable_ready": False,
    "torque_publisher_enabled": False,
    "hardware_deployment_completed": False,
    "control_law_changed": False,
    "baseline_type": "mixed_online_control_baseline",
    "source_checks": source_checks,
    "stage1220b_r3_checks": b_r3_checks,
    "stage1220c_r1_checks": c_r1_checks,
    "stage1220d_r1_checks": d_r1_checks,
    "evidence_files": {
        "stage1220b_r3_summary": str(B_R3_SUMMARY),
        "stage1220b_r3_build_returncode": str(B_R3_BUILD_RC),
        "stage1220c_r1_summary": str(C_R1_SUMMARY),
        "stage1220d_r1_summary": str(D_R1_SUMMARY),
        "source": str(SRC),
    },
    "next_stage": "Stage 12.21 freeze and regression check; no hardware deployment",
}

SUMMARY_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

md = [
    "# Stage 12.20E Final Evidence Freeze",
    "",
    f"- pass: `{summary['pass']}`",
    f"- fail_reasons: `{summary['fail_reasons']}`",
    f"- stage1220_completed: `{summary['stage1220_completed']}`",
    f"- continuous_torque_streaming_completed: `{summary['continuous_torque_streaming_completed']}`",
    f"- torque_enable_ready: `{summary['torque_enable_ready']}`",
    f"- torque_publisher_enabled: `{summary['torque_publisher_enabled']}`",
    f"- hardware_deployment_completed: `{summary['hardware_deployment_completed']}`",
    f"- control_law_changed: `{summary['control_law_changed']}`",
    f"- baseline_type: `{summary['baseline_type']}`",
    "",
    "## Source freeze",
    "",
    f"- source_hash: `{source_checks.get('source_hash')}`",
    f"- source_hash_matches_stage1220b_r3: `{source_checks.get('source_hash_matches_stage1220b_r3')}`",
    f"- publish_call_count: `{source_checks.get('publish_call_count')}`",
    f"- has_four_flag_gate: `{source_checks.get('has_four_flag_gate')}`",
    f"- has_continuous_timer: `{source_checks.get('has_continuous_timer')}`",
    f"- has_10hz_timer: `{source_checks.get('has_10hz_timer')}`",
    f"- has_max_ticks_30_bound: `{source_checks.get('has_max_ticks_30_bound')}`",
    f"- has_max_duration_3s_bound: `{source_checks.get('has_max_duration_3s_bound')}`",
    "",
    "## Runtime evidence",
    "",
    f"- default_off_pass: `{c_r1_checks.get('pass')}`",
    f"- default_off_echo_timeout: `{c_r1_checks.get('echo_timeout')}`",
    f"- default_off_echo_has_data_false: `{c_r1_checks.get('echo_has_data_false')}`",
    f"- streaming_pass: `{d_r1_checks.get('pass')}`",
    f"- stream_message_count_in_1_to_30: `{d_r1_checks.get('stream_message_count_in_1_to_30')}`",
    f"- all_stream_payloads_length_12: `{d_r1_checks.get('all_stream_payloads_length_12')}`",
    f"- all_stream_payload_values_finite: `{d_r1_checks.get('all_stream_payload_values_finite')}`",
    f"- all_stream_payload_values_zero_safe: `{d_r1_checks.get('all_stream_payload_values_zero_safe')}`",
    f"- final_flags_false: `{d_r1_checks.get('final_flags_false')}`",
    f"- after_stop_echo_timeout: `{d_r1_checks.get('after_stop_echo_timeout')}`",
    f"- after_stop_echo_has_data_false: `{d_r1_checks.get('after_stop_echo_has_data_false')}`",
    "",
    "Safety boundary: Stage 12.20 completes bounded continuous zero/safe streaming dry-run only. It is not hardware deployment, not torque enable readiness, not realtime controller completion, and not a control-law change.",
    "",
    f"Next stage: `{summary['next_stage']}`",
]

DOC_MD.write_text("\n".join(md), encoding="utf-8")

if summary["pass"]:
    status_block = f"""

## Stage 12.20E Final Evidence Freeze

- timestamp: `{summary['timestamp']}`
- pass: `True`
- stage1220_completed: `True`
- continuous_torque_streaming_completed: `True`
- source_hash: `{source_checks.get('source_hash')}`
- publish_call_count: `{source_checks.get('publish_call_count')}`
- default-off regression: `pass`
- bounded streaming regression: `pass`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- hardware_deployment_completed: `False`
- control_law_changed: `False`
- next_stage: `Stage 12.21 freeze and regression check; no hardware deployment`
"""
    old = PROJECT_STATUS.read_text(encoding="utf-8", errors="replace") if PROJECT_STATUS.exists() else ""
    if "## Stage 12.20E Final Evidence Freeze" not in old:
        PROJECT_STATUS.write_text(old.rstrip() + status_block + "\n", encoding="utf-8")

print(json.dumps(summary, indent=2, ensure_ascii=False))
