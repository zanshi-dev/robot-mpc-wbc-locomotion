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

SUMMARY_1221 = OUT_DIR / "stage12_21_freeze_and_regression_check_summary.json"
D_R1_SUMMARY = OUT_DIR / "stage12_20d_r1_reparse_existing_evidence_summary.json"
STREAM_ECHO = OUT_DIR / "stage12_20d_stream_echo.log"
AFTER_STOP_ECHO = OUT_DIR / "stage12_20d_after_stop_echo.log"
PARAM_SET = OUT_DIR / "stage12_20d_param_set.log"
PARAM_FINAL = OUT_DIR / "stage12_20d_param_final.log"
NODE_LOG = OUT_DIR / "stage12_20d_node.log"
NODE_LIST = OUT_DIR / "stage12_20d_node_list.log"
ORIG_D_SUMMARY = OUT_DIR / "stage12_20d_runtime_bounded_streaming_regression_summary.json"

OUT_JSON = OUT_DIR / "stage12_21_r1_inspect_bounded_streaming_failure_summary.json"
OUT_MD = DOC_DIR / "stage12_21_r1_inspect_bounded_streaming_failure.md"

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""

def read_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))

def parse_msgs(text: str):
    msgs = []
    current = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("data:"):
            rest = line[len("data:"):].strip()
            if rest.startswith("["):
                try:
                    msgs.append([float(x) for x in ast.literal_eval(rest)])
                    current = None
                except Exception:
                    current = []
            else:
                current = []
            continue
        if current is not None:
            if line == "---":
                msgs.append(current)
                current = None
                continue
            if line.startswith("- "):
                try:
                    current.append(float(line[2:].strip()))
                except Exception:
                    current.append(float("nan"))
    if current:
        msgs.append(current)
    return msgs

summary1221 = read_json(SUMMARY_1221)
orig_d = read_json(ORIG_D_SUMMARY)
d_r1 = read_json(D_R1_SUMMARY)

stream_text = read(STREAM_ECHO)
after_text = read(AFTER_STOP_ECHO)
param_set_text = read(PARAM_SET)
param_final_text = read(PARAM_FINAL)
node_text = read(NODE_LOG)
node_list_text = read(NODE_LIST)

msgs = parse_msgs(stream_text)
after_msgs = parse_msgs(after_text)

lengths = [len(m) for m in msgs]
msg_count = len(msgs)

param_success_count = len(re.findall(r"Set parameter successful", param_set_text, re.IGNORECASE))
four_flag_success = all(s in param_set_text for s in [
    "set enable_torque_publisher=true",
    "set confirm_torque_publisher_enable=true",
    "set enable_continuous_torque_streaming=true",
    "set confirm_continuous_torque_streaming=true",
]) and param_success_count >= 10

final_flags_false = all(re.search(p, param_final_text) for p in [
    r"enable_torque_publisher:\s*\nBoolean value is: False",
    r"confirm_torque_publisher_enable:\s*\nBoolean value is: False",
    r"enable_continuous_torque_streaming:\s*\nBoolean value is: False",
    r"confirm_continuous_torque_streaming:\s*\nBoolean value is: False",
])

node_seen = "/go1_disabled_controller_node" in node_list_text or (d_r1 or {}).get("node_seen") is True

manual_enable_active_seen = "manual_enable_active=1" in node_text
base_flags_active_seen = "enable_torque_publisher=1 confirm_torque_publisher_enable=1" in node_text

stream_echo_has_data_marker = bool(re.search(r"(^|\n)\s*data\s*:", stream_text))
stream_echo_timeout_text = "timeout" in stream_text.lower()
stream_echo_line_count = len(stream_text.splitlines())

all_len12 = msg_count > 0 and all(len(m) == 12 for m in msgs)
all_finite = msg_count > 0 and all(math.isfinite(x) for m in msgs for x in m)
all_zero = msg_count > 0 and all(abs(x) <= 1e-12 for m in msgs for x in m)

diagnosis = []
if msg_count == 0 and four_flag_success and node_seen:
    diagnosis.append("no stream payload captured despite successful four-flag activation; likely DDS/echo timing race or timer already missed by echo")
if msg_count == 0 and not four_flag_success:
    diagnosis.append("parameter activation evidence incomplete")
if msg_count > 0 and not all_len12:
    diagnosis.append("payload captured but length check failed")
if msg_count > 0 and all_len12 and all_finite and all_zero:
    diagnosis.append("runtime payload evidence looks valid; prior failure likely parser/summary mismatch")

pass_inspection = summary1221 is not None and summary1221.get("pass") is False and node_seen and four_flag_success and final_flags_false

result = {
    "stage": "12.21-R1",
    "name": "inspect_bounded_streaming_rerun_failure",
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "pass": pass_inspection,
    "inspection_only": True,
    "original_stage1221_pass": None if summary1221 is None else summary1221.get("pass"),
    "node_seen": node_seen,
    "four_flag_param_set_success": four_flag_success,
    "param_success_count": param_success_count,
    "final_flags_false": final_flags_false,
    "manual_enable_active_seen_in_node_log": manual_enable_active_seen,
    "base_flags_active_seen_in_node_log": base_flags_active_seen,
    "stream_echo_line_count": stream_echo_line_count,
    "stream_echo_has_data_marker": stream_echo_has_data_marker,
    "stream_message_count": msg_count,
    "stream_payload_lengths": lengths,
    "all_stream_payloads_length_12": all_len12,
    "all_stream_payload_values_finite": all_finite,
    "all_stream_payload_values_zero_safe": all_zero,
    "after_stop_message_count": len(after_msgs),
    "diagnosis": diagnosis,
    "recommended_repair": "Stage 12.21-R2 rerun bounded streaming with subscriber warmup/readiness and longer capture window; no source change",
    "logs": {
        "stage1221_summary": str(SUMMARY_1221),
        "stage20d_r1_summary": str(D_R1_SUMMARY),
        "stream_echo": str(STREAM_ECHO),
        "after_stop_echo": str(AFTER_STOP_ECHO),
        "param_set": str(PARAM_SET),
        "param_final": str(PARAM_FINAL),
        "node_log": str(NODE_LOG),
        "node_list": str(NODE_LIST),
    }
}

OUT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

md = [
    "# Stage 12.21-R1 Bounded Streaming Failure Inspection",
    "",
    f"- pass: `{result['pass']}`",
    f"- inspection_only: `{result['inspection_only']}`",
    f"- original_stage1221_pass: `{result['original_stage1221_pass']}`",
    f"- node_seen: `{result['node_seen']}`",
    f"- four_flag_param_set_success: `{result['four_flag_param_set_success']}`",
    f"- final_flags_false: `{result['final_flags_false']}`",
    f"- manual_enable_active_seen_in_node_log: `{result['manual_enable_active_seen_in_node_log']}`",
    f"- stream_echo_has_data_marker: `{result['stream_echo_has_data_marker']}`",
    f"- stream_message_count: `{result['stream_message_count']}`",
    f"- stream_payload_lengths: `{result['stream_payload_lengths']}`",
    f"- diagnosis: `{result['diagnosis']}`",
    "",
    f"Recommended repair: `{result['recommended_repair']}`",
    "",
    "Safety boundary: inspection only; no source change; no hardware deployment.",
]
OUT_MD.write_text("\n".join(md), encoding="utf-8")

print(json.dumps(result, indent=2, ensure_ascii=False))
