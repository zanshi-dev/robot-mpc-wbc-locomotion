#!/usr/bin/env bash
set -eo pipefail

ROOT="$(pwd)"
OUT_DIR="$ROOT/results/logs_sample"
DOC_DIR="$ROOT/docs"
mkdir -p "$OUT_DIR" "$DOC_DIR"

SUMMARY_JSON="$OUT_DIR/stage12_21_r2_subscriber_warmup_bounded_streaming_rerun_summary.json"
NODE_LOG="$OUT_DIR/stage12_21_r2_node.log"
CAPTURE_JSON="$OUT_DIR/stage12_21_r2_capture.json"
CAPTURE_READY="$OUT_DIR/stage12_21_r2_capture.ready"
CAPTURE_LOG="$OUT_DIR/stage12_21_r2_capture.log"
PARAM_SET_LOG="$OUT_DIR/stage12_21_r2_param_set.log"
PARAM_FINAL_LOG="$OUT_DIR/stage12_21_r2_param_final.log"
AFTER_STOP_JSON="$OUT_DIR/stage12_21_r2_after_stop_capture.json"
AFTER_STOP_READY="$OUT_DIR/stage12_21_r2_after_stop_capture.ready"
AFTER_STOP_LOG="$OUT_DIR/stage12_21_r2_after_stop_capture.log"
DOC_MD="$DOC_DIR/stage12_21_r2_subscriber_warmup_bounded_streaming_rerun.md"

source /opt/ros/jazzy/setup.bash
source "$ROOT/install/setup.bash"

rm -f "$CAPTURE_JSON" "$CAPTURE_READY" "$AFTER_STOP_JSON" "$AFTER_STOP_READY"
: > "$NODE_LOG"
: > "$CAPTURE_LOG"
: > "$PARAM_SET_LOG"
: > "$PARAM_FINAL_LOG"
: > "$AFTER_STOP_LOG"

ros2 run robot_mpc_wbc_cpp_controller go1_disabled_controller_node > "$NODE_LOG" 2>&1 &
NODE_PID=$!

cleanup() {
  set +e
  ros2 param set /go1_disabled_controller_node confirm_continuous_torque_streaming false >> "$PARAM_SET_LOG" 2>&1 || true
  ros2 param set /go1_disabled_controller_node enable_continuous_torque_streaming false >> "$PARAM_SET_LOG" 2>&1 || true
  ros2 param set /go1_disabled_controller_node confirm_torque_publisher_enable false >> "$PARAM_SET_LOG" 2>&1 || true
  ros2 param set /go1_disabled_controller_node enable_torque_publisher false >> "$PARAM_SET_LOG" 2>&1 || true

  if [ -n "${CAPTURE_PID:-}" ] && kill -0 "$CAPTURE_PID" >/dev/null 2>&1; then
    kill "$CAPTURE_PID" >/dev/null 2>&1 || true
  fi
  if [ -n "${AFTER_STOP_PID:-}" ] && kill -0 "$AFTER_STOP_PID" >/dev/null 2>&1; then
    kill "$AFTER_STOP_PID" >/dev/null 2>&1 || true
  fi
  if kill -0 "$NODE_PID" >/dev/null 2>&1; then
    kill "$NODE_PID" >/dev/null 2>&1 || true
    sleep 1
  fi
  if kill -0 "$NODE_PID" >/dev/null 2>&1; then
    kill -9 "$NODE_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

sleep 3

NODE_SEEN=false
if ros2 node list | grep -qx "/go1_disabled_controller_node"; then
  NODE_SEEN=true
fi

/usr/bin/python3 scripts/stage12_21_r2_subscriber_capture.py "$CAPTURE_JSON" "$CAPTURE_READY" 12 > "$CAPTURE_LOG" 2>&1 &
CAPTURE_PID=$!

for i in $(seq 1 50); do
  [ -f "$CAPTURE_READY" ] && break
  sleep 0.1
done

CAPTURE_READY_SEEN=false
if [ -f "$CAPTURE_READY" ]; then
  CAPTURE_READY_SEEN=true
fi

# Extra DDS discovery warmup after subscriber is already spinning.
sleep 3

{
  echo "set continuous_torque_streaming_max_ticks=10"
  ros2 param set /go1_disabled_controller_node continuous_torque_streaming_max_ticks 10
  echo "set continuous_torque_streaming_max_duration_sec=1.5"
  ros2 param set /go1_disabled_controller_node continuous_torque_streaming_max_duration_sec 1.5

  echo "set enable_torque_publisher=true"
  ros2 param set /go1_disabled_controller_node enable_torque_publisher true
  echo "set confirm_torque_publisher_enable=true"
  ros2 param set /go1_disabled_controller_node confirm_torque_publisher_enable true
  echo "set enable_continuous_torque_streaming=true"
  ros2 param set /go1_disabled_controller_node enable_continuous_torque_streaming true
  echo "set confirm_continuous_torque_streaming=true"
  ros2 param set /go1_disabled_controller_node confirm_continuous_torque_streaming true
} >> "$PARAM_SET_LOG" 2>&1

wait "$CAPTURE_PID"

{
  echo "fail-closed revert confirm_continuous_torque_streaming=false"
  ros2 param set /go1_disabled_controller_node confirm_continuous_torque_streaming false
  echo "fail-closed revert enable_continuous_torque_streaming=false"
  ros2 param set /go1_disabled_controller_node enable_continuous_torque_streaming false
  echo "fail-closed revert confirm_torque_publisher_enable=false"
  ros2 param set /go1_disabled_controller_node confirm_torque_publisher_enable false
  echo "fail-closed revert enable_torque_publisher=false"
  ros2 param set /go1_disabled_controller_node enable_torque_publisher false
} >> "$PARAM_SET_LOG" 2>&1

{
  echo "enable_torque_publisher:"
  ros2 param get /go1_disabled_controller_node enable_torque_publisher || true
  echo
  echo "confirm_torque_publisher_enable:"
  ros2 param get /go1_disabled_controller_node confirm_torque_publisher_enable || true
  echo
  echo "enable_continuous_torque_streaming:"
  ros2 param get /go1_disabled_controller_node enable_continuous_torque_streaming || true
  echo
  echo "confirm_continuous_torque_streaming:"
  ros2 param get /go1_disabled_controller_node confirm_continuous_torque_streaming || true
} > "$PARAM_FINAL_LOG" 2>&1

/usr/bin/python3 scripts/stage12_21_r2_subscriber_capture.py "$AFTER_STOP_JSON" "$AFTER_STOP_READY" 4 > "$AFTER_STOP_LOG" 2>&1 &
AFTER_STOP_PID=$!
wait "$AFTER_STOP_PID"

cleanup
trap - EXIT

/usr/bin/python3 - "$NODE_SEEN" "$CAPTURE_READY_SEEN" "$SUMMARY_JSON" "$DOC_MD" "$CAPTURE_JSON" "$AFTER_STOP_JSON" "$PARAM_SET_LOG" "$PARAM_FINAL_LOG" "$NODE_LOG" "$CAPTURE_LOG" "$AFTER_STOP_LOG" <<'PY'
import json
import math
import re
import sys
from pathlib import Path

node_seen = sys.argv[1] == "true"
capture_ready_seen = sys.argv[2] == "true"
summary_path = Path(sys.argv[3])
doc_path = Path(sys.argv[4])
capture_json = Path(sys.argv[5])
after_stop_json = Path(sys.argv[6])
param_set_log = Path(sys.argv[7])
param_final_log = Path(sys.argv[8])
node_log = Path(sys.argv[9])
capture_log = Path(sys.argv[10])
after_stop_log = Path(sys.argv[11])

capture = json.loads(capture_json.read_text(encoding="utf-8")) if capture_json.exists() else {"messages": []}
after_stop = json.loads(after_stop_json.read_text(encoding="utf-8")) if after_stop_json.exists() else {"messages": []}

messages = capture.get("messages", [])
after_messages = after_stop.get("messages", [])

count = len(messages)
lengths = [m.get("length") for m in messages]
all_len12 = count > 0 and all(m.get("length") == 12 for m in messages)
all_finite = count > 0 and all(m.get("all_finite") is True for m in messages)
all_zero_safe = count > 0 and all(float(m.get("max_abs", 999.0)) <= 1e-12 for m in messages)
count_in_range = 1 <= count <= 30

param_set_text = param_set_log.read_text(encoding="utf-8", errors="replace") if param_set_log.exists() else ""
param_final_text = param_final_log.read_text(encoding="utf-8", errors="replace") if param_final_log.exists() else ""

param_set_ok = all(s in param_set_text for s in [
    "set enable_torque_publisher=true",
    "set confirm_torque_publisher_enable=true",
    "set enable_continuous_torque_streaming=true",
    "set confirm_continuous_torque_streaming=true",
]) and len(re.findall(r"Set parameter successful", param_set_text, re.IGNORECASE)) >= 10

final_flags_false = all(re.search(p, param_final_text) for p in [
    r"enable_torque_publisher:\s*\nBoolean value is: False",
    r"confirm_torque_publisher_enable:\s*\nBoolean value is: False",
    r"enable_continuous_torque_streaming:\s*\nBoolean value is: False",
    r"confirm_continuous_torque_streaming:\s*\nBoolean value is: False",
])

after_stop_no_messages = len(after_messages) == 0

fail_reasons = []
if not node_seen:
    fail_reasons.append("node /go1_disabled_controller_node not seen")
if not capture_ready_seen:
    fail_reasons.append("subscriber capture readiness file not observed before activation")
if not param_set_ok:
    fail_reasons.append("four-flag activation/revert parameter success evidence incomplete")
if not count_in_range:
    fail_reasons.append(f"stream message count not in 1..30: {count}")
if not all_len12:
    fail_reasons.append(f"not all stream payloads have length 12: lengths={lengths}")
if not all_finite:
    fail_reasons.append("not all stream payload values are finite")
if not all_zero_safe:
    fail_reasons.append("not all stream payload values are zero-safe")
if not final_flags_false:
    fail_reasons.append("final flags are not all false")
if not after_stop_no_messages:
    fail_reasons.append(f"after-stop subscriber captured messages: {len(after_messages)}")

summary = {
    "stage": "12.21-R2",
    "name": "subscriber_warmup_bounded_streaming_rerun",
    "pass": len(fail_reasons) == 0,
    "fail_reasons": fail_reasons,
    "source_changed": False,
    "node_seen": node_seen,
    "subscriber_ready_before_activation": capture_ready_seen,
    "param_set_ok": param_set_ok,
    "stream_message_count": count,
    "stream_message_count_in_1_to_30": count_in_range,
    "stream_payload_lengths": lengths,
    "all_stream_payloads_length_12": all_len12,
    "all_stream_payload_values_finite": all_finite,
    "all_stream_payload_values_zero_safe": all_zero_safe,
    "final_flags_false": final_flags_false,
    "after_stop_message_count": len(after_messages),
    "after_stop_no_messages": after_stop_no_messages,
    "continuous_torque_streaming_completed": len(fail_reasons) == 0,
    "torque_enable_ready": False,
    "torque_publisher_enabled": False,
    "hardware_deployment_completed": False,
    "control_law_changed": False,
    "logs": {
        "capture_json": str(capture_json),
        "after_stop_json": str(after_stop_json),
        "param_set_log": str(param_set_log),
        "param_final_log": str(param_final_log),
        "node_log": str(node_log),
        "capture_log": str(capture_log),
        "after_stop_log": str(after_stop_log),
    },
}

summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

doc = [
    "# Stage 12.21-R2 Subscriber-Warmup Bounded Streaming Rerun",
    "",
    f"- pass: `{summary['pass']}`",
    f"- fail_reasons: `{summary['fail_reasons']}`",
    f"- source_changed: `{summary['source_changed']}`",
    f"- node_seen: `{summary['node_seen']}`",
    f"- subscriber_ready_before_activation: `{summary['subscriber_ready_before_activation']}`",
    f"- param_set_ok: `{summary['param_set_ok']}`",
    f"- stream_message_count: `{summary['stream_message_count']}`",
    f"- stream_message_count_in_1_to_30: `{summary['stream_message_count_in_1_to_30']}`",
    f"- all_stream_payloads_length_12: `{summary['all_stream_payloads_length_12']}`",
    f"- all_stream_payload_values_finite: `{summary['all_stream_payload_values_finite']}`",
    f"- all_stream_payload_values_zero_safe: `{summary['all_stream_payload_values_zero_safe']}`",
    f"- final_flags_false: `{summary['final_flags_false']}`",
    f"- after_stop_no_messages: `{summary['after_stop_no_messages']}`",
    f"- continuous_torque_streaming_completed: `{summary['continuous_torque_streaming_completed']}`",
    "",
    "Safety boundary: subscriber-warmup regression only; no source change; no hardware deployment; no control-law change.",
]
doc_path.write_text("\n".join(doc), encoding="utf-8")

print(json.dumps(summary, indent=2, ensure_ascii=False))
PY
