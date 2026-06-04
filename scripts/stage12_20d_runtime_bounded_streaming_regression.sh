#!/usr/bin/env bash
set -eo pipefail

ROOT="$(pwd)"
OUT_DIR="$ROOT/results/logs_sample"
DOC_DIR="$ROOT/docs"
mkdir -p "$OUT_DIR" "$DOC_DIR"

PRE_SUMMARY="$OUT_DIR/stage12_20c_r1_runtime_default_off_regression_summary.json"
SUMMARY_JSON="$OUT_DIR/stage12_20d_runtime_bounded_streaming_regression_summary.json"
NODE_LOG="$OUT_DIR/stage12_20d_node.log"
NODE_LIST_LOG="$OUT_DIR/stage12_20d_node_list.log"
PARAM_SET_LOG="$OUT_DIR/stage12_20d_param_set.log"
PARAM_FINAL_LOG="$OUT_DIR/stage12_20d_param_final.log"
STREAM_ECHO_LOG="$OUT_DIR/stage12_20d_stream_echo.log"
AFTER_STOP_ECHO_LOG="$OUT_DIR/stage12_20d_after_stop_echo.log"
DOC_MD="$DOC_DIR/stage12_20d_runtime_bounded_streaming_regression.md"

if [ ! -f "$PRE_SUMMARY" ]; then
  /usr/bin/python3 - <<PY
import json
from pathlib import Path
summary = {
  "stage": "12.20D",
  "pass": False,
  "fail_reasons": ["missing Stage 12.20C-R1 summary; do not run streaming regression before default-off pass"],
}
Path("$SUMMARY_JSON").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(summary, indent=2, ensure_ascii=False))
PY
  exit 1
fi

/usr/bin/python3 - "$PRE_SUMMARY" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
s = json.loads(p.read_text(encoding="utf-8"))
if not s.get("pass", False):
    raise SystemExit("Stage 12.20C-R1 did not pass")
PY

source /opt/ros/jazzy/setup.bash
source "$ROOT/install/setup.bash"

: > "$NODE_LOG"
: > "$NODE_LIST_LOG"
: > "$PARAM_SET_LOG"
: > "$PARAM_FINAL_LOG"
: > "$STREAM_ECHO_LOG"
: > "$AFTER_STOP_ECHO_LOG"

ros2 run robot_mpc_wbc_cpp_controller go1_disabled_controller_node > "$NODE_LOG" 2>&1 &
NODE_PID=$!

cleanup() {
  set +e
  ros2 param set /go1_disabled_controller_node confirm_continuous_torque_streaming false >> "$PARAM_SET_LOG" 2>&1 || true
  ros2 param set /go1_disabled_controller_node enable_continuous_torque_streaming false >> "$PARAM_SET_LOG" 2>&1 || true
  ros2 param set /go1_disabled_controller_node confirm_torque_publisher_enable false >> "$PARAM_SET_LOG" 2>&1 || true
  ros2 param set /go1_disabled_controller_node enable_torque_publisher false >> "$PARAM_SET_LOG" 2>&1 || true
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
if ros2 node list > "$NODE_LIST_LOG" 2>&1; then
  if grep -qx "/go1_disabled_controller_node" "$NODE_LIST_LOG"; then
    NODE_SEEN=true
  fi
fi

timeout 7s ros2 topic echo /go1/joint_torque_cmd std_msgs/msg/Float64MultiArray > "$STREAM_ECHO_LOG" 2>&1 &
STREAM_ECHO_PID=$!
sleep 1

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

sleep 3

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

set +e
wait "$STREAM_ECHO_PID"
STREAM_ECHO_RC=$?
set -e

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

set +e
timeout 3s ros2 topic echo --once /go1/joint_torque_cmd std_msgs/msg/Float64MultiArray > "$AFTER_STOP_ECHO_LOG" 2>&1
AFTER_STOP_ECHO_RC=$?
set -e

cleanup
trap - EXIT

/usr/bin/python3 - "$NODE_SEEN" "$STREAM_ECHO_RC" "$AFTER_STOP_ECHO_RC" "$SUMMARY_JSON" "$DOC_MD" "$STREAM_ECHO_LOG" "$AFTER_STOP_ECHO_LOG" "$PARAM_SET_LOG" "$PARAM_FINAL_LOG" "$NODE_LOG" "$NODE_LIST_LOG" <<'PY'
import ast
import json
import math
import re
import sys
from pathlib import Path

node_seen = sys.argv[1] == "true"
stream_echo_rc = int(sys.argv[2])
after_stop_echo_rc = int(sys.argv[3])
summary_path = Path(sys.argv[4])
doc_path = Path(sys.argv[5])
stream_echo_log = Path(sys.argv[6])
after_stop_echo_log = Path(sys.argv[7])
param_set_log = Path(sys.argv[8])
param_final_log = Path(sys.argv[9])
node_log = Path(sys.argv[10])
node_list_log = Path(sys.argv[11])

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

stream_text = stream_echo_log.read_text(encoding="utf-8", errors="replace") if stream_echo_log.exists() else ""
after_text = after_stop_echo_log.read_text(encoding="utf-8", errors="replace") if after_stop_echo_log.exists() else ""
param_set_text = param_set_log.read_text(encoding="utf-8", errors="replace") if param_set_log.exists() else ""
param_final_text = param_final_log.read_text(encoding="utf-8", errors="replace") if param_final_log.exists() else ""

messages = parse_float64multiarray_messages(stream_text)
after_stop_messages = parse_float64multiarray_messages(after_text)

message_count = len(messages)
lengths = [len(m) for m in messages]
all_length_12 = bool(messages) and all(len(m) == 12 for m in messages)
all_finite = bool(messages) and all(math.isfinite(x) for m in messages for x in m)
all_zero_safe = bool(messages) and all(abs(x) <= 1e-12 for m in messages for x in m)

stream_count_in_range = 1 <= message_count <= 30
after_stop_timeout = after_stop_echo_rc == 124
after_stop_has_data = len(after_stop_messages) > 0 or bool(re.search(r"(^|\n)\s*data\s*:", after_text))

final_flags_false = (
    re.search(r"enable_torque_publisher:\s*\nBoolean value is: False", param_final_text) is not None
    and re.search(r"confirm_torque_publisher_enable:\s*\nBoolean value is: False", param_final_text) is not None
    and re.search(r"enable_continuous_torque_streaming:\s*\nBoolean value is: False", param_final_text) is not None
    and re.search(r"confirm_continuous_torque_streaming:\s*\nBoolean value is: False", param_final_text) is not None
)

param_set_ok = (
    "Successful" in param_set_text
    and "enable_torque_publisher=true" in param_set_text
    and "confirm_torque_publisher_enable=true" in param_set_text
    and "enable_continuous_torque_streaming=true" in param_set_text
    and "confirm_continuous_torque_streaming=true" in param_set_text
)

fail_reasons = []
if not node_seen:
    fail_reasons.append("node /go1_disabled_controller_node not seen")
if not param_set_ok:
    fail_reasons.append("parameter set log does not show successful four-flag activation")
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
    fail_reasons.append(f"after-stop echo did not timeout: rc={after_stop_echo_rc}")
if after_stop_has_data:
    fail_reasons.append("after-stop echo captured message data")

summary = {
    "stage": "12.20D",
    "name": "four_flag_true_bounded_continuous_zero_safe_streaming_runtime_regression",
    "pass": len(fail_reasons) == 0,
    "fail_reasons": fail_reasons,
    "node_seen": node_seen,
    "stream_echo_returncode": stream_echo_rc,
    "stream_message_count": message_count,
    "stream_message_count_in_1_to_30": stream_count_in_range,
    "stream_payload_lengths": lengths,
    "all_stream_payloads_length_12": all_length_12,
    "all_stream_payload_values_finite": all_finite,
    "all_stream_payload_values_zero_safe": all_zero_safe,
    "param_set_ok": param_set_ok,
    "final_flags_false": final_flags_false,
    "after_stop_echo_returncode": after_stop_echo_rc,
    "after_stop_echo_timeout": after_stop_timeout,
    "after_stop_echo_has_data": after_stop_has_data,
    "torque_enable_ready": False,
    "torque_publisher_enabled": False,
    "hardware_deployment_completed": False,
    "control_law_changed": False,
    "logs": {
        "stream_echo_log": str(stream_echo_log),
        "after_stop_echo_log": str(after_stop_echo_log),
        "param_set_log": str(param_set_log),
        "param_final_log": str(param_final_log),
        "node_log": str(node_log),
        "node_list_log": str(node_list_log),
    },
}

summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

doc = [
    "# Stage 12.20D Runtime Bounded Continuous Streaming Regression",
    "",
    f"- pass: `{summary['pass']}`",
    f"- fail_reasons: `{summary['fail_reasons']}`",
    f"- node_seen: `{summary['node_seen']}`",
    f"- stream_message_count: `{summary['stream_message_count']}`",
    f"- stream_message_count_in_1_to_30: `{summary['stream_message_count_in_1_to_30']}`",
    f"- all_stream_payloads_length_12: `{summary['all_stream_payloads_length_12']}`",
    f"- all_stream_payload_values_finite: `{summary['all_stream_payload_values_finite']}`",
    f"- all_stream_payload_values_zero_safe: `{summary['all_stream_payload_values_zero_safe']}`",
    f"- final_flags_false: `{summary['final_flags_false']}`",
    f"- after_stop_echo_timeout: `{summary['after_stop_echo_timeout']}`",
    f"- after_stop_echo_has_data: `{summary['after_stop_echo_has_data']}`",
    "",
    "Safety boundary: bounded zero/safe dry-run only; no hardware deployment; no control-law change.",
]
doc_path.write_text("\n".join(doc), encoding="utf-8")

print(json.dumps(summary, indent=2, ensure_ascii=False))
PY
