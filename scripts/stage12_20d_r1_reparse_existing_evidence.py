#!/usr/bin/env /usr/bin/python3
from pathlib import Path
import ast
import json
import math
import re
from datetime import datetime

ROOT = Path.cwd()
OUT_DIR = ROOT / "results/logs_sample"
DOC_DIR = ROOT / "docs"
DOC_DIR.mkdir(parents=True, exist_ok=True)

PRE_SUMMARY = OUT_DIR / "stage12_20d_runtime_bounded_streaming_regression_summary.json"
STREAM_ECHO_LOG = OUT_DIR / "stage12_20d_stream_echo.log"
AFTER_STOP_ECHO_LOG = OUT_DIR / "stage12_20d_after_stop_echo.log"
PARAM_SET_LOG = OUT_DIR / "stage12_20d_param_set.log"
PARAM_FINAL_LOG = OUT_DIR / "stage12_20d_param_final.log"
NODE_LOG = OUT_DIR / "stage12_20d_node.log"
NODE_LIST_LOG = OUT_DIR / "stage12_20d_node_list.log"

SUMMARY_JSON = OUT_DIR / "stage12_20d_r1_reparse_existing_evidence_summary.json"
DOC_MD = DOC_DIR / "stage12_20d_r1_reparse_existing_evidence.md"

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""

def parse_float64multiarray_messages(text: str):
    messages = []
    current = None

    for raw in text.splitlines():
        line = raw.strip()

        if line.startswith("data:"):
            rest = line[len("data:"):].strip()
            if rest.startswith("["):
                try:
                    arr = ast.literal_eval(rest)
                    messages.append([float(x) for x in arr])
                    current = None
                except Exception:
                    current = []
            else:
                current = []
            continue

        if current is not None:
            if line == "---":
                messages.append(current)
                current = None
                continue
            if line.startswith("- "):
                token = line[2:].strip()
                try:
                    current.append(float(token))
                except ValueError:
                    current.append(float("nan"))

    if current:
        messages.append(current)

    return messages

def has_successful_command(text: str, label: str) -> bool:
    # Accept ROS outputs such as "Set parameter successful" regardless of case.
    pattern = re.compile(
        re.escape(label) + r".{0,300}?set parameter successful",
        re.IGNORECASE | re.DOTALL,
    )
    return pattern.search(text) is not None

fail_reasons = []

if not PRE_SUMMARY.exists():
    fail_reasons.append("missing original Stage 12.20D summary")

pre = {}
if PRE_SUMMARY.exists():
    pre = json.loads(PRE_SUMMARY.read_text(encoding="utf-8"))

stream_text = read_text(STREAM_ECHO_LOG)
after_text = read_text(AFTER_STOP_ECHO_LOG)
param_set_text = read_text(PARAM_SET_LOG)
param_final_text = read_text(PARAM_FINAL_LOG)
node_list_text = read_text(NODE_LIST_LOG)

messages = parse_float64multiarray_messages(stream_text)
after_stop_messages = parse_float64multiarray_messages(after_text)

message_count = len(messages)
lengths = [len(m) for m in messages]

node_seen = (
    pre.get("node_seen") is True
    or "/go1_disabled_controller_node" in node_list_text
)

all_length_12 = bool(messages) and all(len(m) == 12 for m in messages)
all_finite = bool(messages) and all(math.isfinite(x) for m in messages for x in m)
all_zero_safe = bool(messages) and all(abs(x) <= 1e-12 for m in messages for x in m)
stream_count_in_range = 1 <= message_count <= 30

required_param_commands = [
    "set continuous_torque_streaming_max_ticks=10",
    "set continuous_torque_streaming_max_duration_sec=1.5",
    "set enable_torque_publisher=true",
    "set confirm_torque_publisher_enable=true",
    "set enable_continuous_torque_streaming=true",
    "set confirm_continuous_torque_streaming=true",
    "fail-closed revert confirm_continuous_torque_streaming=false",
    "fail-closed revert enable_continuous_torque_streaming=false",
    "fail-closed revert confirm_torque_publisher_enable=false",
    "fail-closed revert enable_torque_publisher=false",
]

param_command_results = {
    cmd: has_successful_command(param_set_text, cmd)
    for cmd in required_param_commands
}

param_set_ok = all(param_command_results.values())

final_flags_false = (
    re.search(r"enable_torque_publisher:\s*\nBoolean value is: False", param_final_text) is not None
    and re.search(r"confirm_torque_publisher_enable:\s*\nBoolean value is: False", param_final_text) is not None
    and re.search(r"enable_continuous_torque_streaming:\s*\nBoolean value is: False", param_final_text) is not None
    and re.search(r"confirm_continuous_torque_streaming:\s*\nBoolean value is: False", param_final_text) is not None
)

after_stop_echo_returncode = pre.get("after_stop_echo_returncode")
after_stop_timeout = after_stop_echo_returncode == 124
after_stop_has_data = len(after_stop_messages) > 0 or bool(re.search(r"(^|\n)\s*data\s*:", after_text))

if not node_seen:
    fail_reasons.append("node /go1_disabled_controller_node not seen")
if not param_set_ok:
    missing = [cmd for cmd, ok in param_command_results.items() if not ok]
    fail_reasons.append(f"parameter command success evidence missing: {missing}")
if not stream_count_in_range:
    fail_reasons.append(f"stream message count not in 1..30: {message_count}")
if not all_length_12:
    fail_reasons.append(f"not all stream payloads have length 12: lengths={lengths}")
if not all_finite:
    fail_reasons.append("not all stream payload values are finite")
if not all_zero_safe:
    fail_reasons.append("not all stream payload values are zero-safe")
if not final_flags_false:
    fail_reasons.append("final manual flags are not all false")
if not after_stop_timeout:
    fail_reasons.append(f"after-stop echo did not timeout: rc={after_stop_echo_returncode}")
if after_stop_has_data:
    fail_reasons.append("after-stop echo captured message data")

summary = {
    "stage": "12.20D-R1",
    "name": "reparse_existing_stage1220d_evidence_with_case_insensitive_param_success",
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "pass": len(fail_reasons) == 0,
    "fail_reasons": fail_reasons,
    "original_stage1220d_pass": pre.get("pass"),
    "original_stage1220d_fail_reasons": pre.get("fail_reasons"),
    "node_seen": node_seen,
    "param_set_ok": param_set_ok,
    "param_command_results": param_command_results,
    "stream_message_count": message_count,
    "stream_message_count_in_1_to_30": stream_count_in_range,
    "stream_payload_lengths": lengths,
    "all_stream_payloads_length_12": all_length_12,
    "all_stream_payload_values_finite": all_finite,
    "all_stream_payload_values_zero_safe": all_zero_safe,
    "final_flags_false": final_flags_false,
    "after_stop_echo_returncode": after_stop_echo_returncode,
    "after_stop_echo_timeout": after_stop_timeout,
    "after_stop_echo_has_data": after_stop_has_data,
    "continuous_torque_streaming_completed": len(fail_reasons) == 0,
    "torque_enable_ready": False,
    "torque_publisher_enabled": False,
    "hardware_deployment_completed": False,
    "control_law_changed": False,
    "logs": {
        "original_summary": str(PRE_SUMMARY),
        "stream_echo_log": str(STREAM_ECHO_LOG),
        "after_stop_echo_log": str(AFTER_STOP_ECHO_LOG),
        "param_set_log": str(PARAM_SET_LOG),
        "param_final_log": str(PARAM_FINAL_LOG),
        "node_log": str(NODE_LOG),
        "node_list_log": str(NODE_LIST_LOG),
    },
}

SUMMARY_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

doc = [
    "# Stage 12.20D-R1 Reparse Existing Evidence",
    "",
    f"- pass: `{summary['pass']}`",
    f"- fail_reasons: `{summary['fail_reasons']}`",
    f"- original_stage1220d_pass: `{summary['original_stage1220d_pass']}`",
    f"- original_stage1220d_fail_reasons: `{summary['original_stage1220d_fail_reasons']}`",
    f"- node_seen: `{summary['node_seen']}`",
    f"- param_set_ok: `{summary['param_set_ok']}`",
    f"- stream_message_count: `{summary['stream_message_count']}`",
    f"- stream_message_count_in_1_to_30: `{summary['stream_message_count_in_1_to_30']}`",
    f"- all_stream_payloads_length_12: `{summary['all_stream_payloads_length_12']}`",
    f"- all_stream_payload_values_finite: `{summary['all_stream_payload_values_finite']}`",
    f"- all_stream_payload_values_zero_safe: `{summary['all_stream_payload_values_zero_safe']}`",
    f"- final_flags_false: `{summary['final_flags_false']}`",
    f"- after_stop_echo_timeout: `{summary['after_stop_echo_timeout']}`",
    f"- after_stop_echo_has_data: `{summary['after_stop_echo_has_data']}`",
    f"- continuous_torque_streaming_completed: `{summary['continuous_torque_streaming_completed']}`",
    "",
    "Safety boundary: bounded zero/safe dry-run only; no hardware deployment; no control-law change.",
]

DOC_MD.write_text("\n".join(doc), encoding="utf-8")
print(json.dumps(summary, indent=2, ensure_ascii=False))
