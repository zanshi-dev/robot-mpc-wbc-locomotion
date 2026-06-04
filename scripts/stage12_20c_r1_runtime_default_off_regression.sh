#!/usr/bin/env bash
set -eo pipefail

ROOT="$(pwd)"
OUT_DIR="$ROOT/results/logs_sample"
DOC_DIR="$ROOT/docs"
mkdir -p "$OUT_DIR" "$DOC_DIR"

SUMMARY_JSON="$OUT_DIR/stage12_20c_r1_runtime_default_off_regression_summary.json"
NODE_LOG="$OUT_DIR/stage12_20c_r1_node_default_off.log"
NODE_LIST_LOG="$OUT_DIR/stage12_20c_r1_node_list.log"
TOPIC_LIST_LOG="$OUT_DIR/stage12_20c_r1_topic_list.log"
PARAM_LOG="$OUT_DIR/stage12_20c_r1_params_default_off.log"
ECHO_LOG="$OUT_DIR/stage12_20c_r1_default_off_echo.log"
DOC_MD="$DOC_DIR/stage12_20c_r1_runtime_default_off_regression.md"

source /opt/ros/jazzy/setup.bash
source "$ROOT/install/setup.bash"

: > "$NODE_LOG"
: > "$NODE_LIST_LOG"
: > "$TOPIC_LIST_LOG"
: > "$PARAM_LOG"
: > "$ECHO_LOG"

ros2 run robot_mpc_wbc_cpp_controller go1_disabled_controller_node > "$NODE_LOG" 2>&1 &
NODE_PID=$!

cleanup() {
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

ros2 topic list -t > "$TOPIC_LIST_LOG" 2>&1 || true

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
  echo
  echo "continuous_torque_streaming_max_ticks:"
  ros2 param get /go1_disabled_controller_node continuous_torque_streaming_max_ticks || true
  echo
  echo "continuous_torque_streaming_max_duration_sec:"
  ros2 param get /go1_disabled_controller_node continuous_torque_streaming_max_duration_sec || true
} > "$PARAM_LOG" 2>&1

set +e
timeout 5s ros2 topic echo --once /go1/joint_torque_cmd std_msgs/msg/Float64MultiArray > "$ECHO_LOG" 2>&1
ECHO_RC=$?
set -e

cleanup
trap - EXIT

PARAMS_FALSE=false
if grep -A1 "enable_torque_publisher:" "$PARAM_LOG" | grep -Eiq "false|False" \
  && grep -A1 "confirm_torque_publisher_enable:" "$PARAM_LOG" | grep -Eiq "false|False" \
  && grep -A1 "enable_continuous_torque_streaming:" "$PARAM_LOG" | grep -Eiq "false|False" \
  && grep -A1 "confirm_continuous_torque_streaming:" "$PARAM_LOG" | grep -Eiq "false|False"; then
  PARAMS_FALSE=true
fi

ECHO_HAS_DATA=false
if grep -Eq "data:|layout:" "$ECHO_LOG"; then
  ECHO_HAS_DATA=true
fi

ECHO_TIMEOUT=false
if [ "$ECHO_RC" -eq 124 ]; then
  ECHO_TIMEOUT=true
fi

PASS=false
FAIL_REASONS_JSON="[]"

/usr/bin/python3 - "$NODE_SEEN" "$PARAMS_FALSE" "$ECHO_RC" "$ECHO_TIMEOUT" "$ECHO_HAS_DATA" "$SUMMARY_JSON" "$DOC_MD" "$NODE_LOG" "$NODE_LIST_LOG" "$TOPIC_LIST_LOG" "$PARAM_LOG" "$ECHO_LOG" <<'PY'
import json
import sys
from pathlib import Path

node_seen = sys.argv[1] == "true"
params_false = sys.argv[2] == "true"
echo_rc = int(sys.argv[3])
echo_timeout = sys.argv[4] == "true"
echo_has_data = sys.argv[5] == "true"

summary_path = Path(sys.argv[6])
doc_path = Path(sys.argv[7])
node_log = sys.argv[8]
node_list_log = sys.argv[9]
topic_list_log = sys.argv[10]
param_log = sys.argv[11]
echo_log = sys.argv[12]

fail_reasons = []
if not node_seen:
    fail_reasons.append("node /go1_disabled_controller_node not seen")
if not params_false:
    fail_reasons.append("default manual flags are not all false or params not readable")
if not echo_timeout:
    fail_reasons.append("default-off echo did not timeout")
if echo_has_data:
    fail_reasons.append("default-off echo captured message data")

summary = {
    "stage": "12.20C-R1",
    "name": "runtime_default_off_echo_regression_repaired_script",
    "pass": len(fail_reasons) == 0,
    "fail_reasons": fail_reasons,
    "node_seen": node_seen,
    "params_default_false": params_false,
    "echo_returncode": echo_rc,
    "echo_timeout": echo_timeout,
    "echo_has_data": echo_has_data,
    "torque_command_published_under_default_false": echo_has_data,
    "torque_enable_ready": False,
    "torque_publisher_enabled": False,
    "hardware_deployment_completed": False,
    "control_law_changed": False,
    "logs": {
        "node_log": node_log,
        "node_list_log": node_list_log,
        "topic_list_log": topic_list_log,
        "param_log": param_log,
        "echo_log": echo_log,
    },
}

summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

doc = [
    "# Stage 12.20C-R1 Runtime Default-Off Echo Regression",
    "",
    f"- pass: `{summary['pass']}`",
    f"- fail_reasons: `{summary['fail_reasons']}`",
    f"- node_seen: `{summary['node_seen']}`",
    f"- params_default_false: `{summary['params_default_false']}`",
    f"- echo_returncode: `{summary['echo_returncode']}`",
    f"- echo_timeout: `{summary['echo_timeout']}`",
    f"- echo_has_data: `{summary['echo_has_data']}`",
    f"- torque_command_published_under_default_false: `{summary['torque_command_published_under_default_false']}`",
    "",
    "Safety boundary: default flags false; no torque message expected; no hardware deployment; no control-law change.",
]
doc_path.write_text("\n".join(doc), encoding="utf-8")

print(json.dumps(summary, indent=2, ensure_ascii=False))
PY
