#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ROS_SETUP="/opt/ros/jazzy/setup.bash"
LOG_DIR="$REPO_ROOT/results/logs_sample"
LOG_FILE="$LOG_DIR/stage15_1_ros2_cpp_controller_test.log"

mkdir -p "$LOG_DIR"

if [[ ! -f "$ROS_SETUP" ]]; then
  echo "error: ROS2 Jazzy setup file not found: $ROS_SETUP" | tee "$LOG_FILE"
  exit 1
fi

# ROS setup files may reference unset environment variables internally.
# Disable nounset only while sourcing ROS, then restore it.
set +u
# shellcheck disable=SC1090
source "$ROS_SETUP"
set -u

cd "$REPO_ROOT/ros2_ws"

{
  echo "[Stage 15.1] ROS2/C++ control algorithm package validation"
  echo "repo_root: $REPO_ROOT"
  echo "ros_setup: $ROS_SETUP"
  echo "timestamp_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo

  echo "[1/3] colcon build"
  colcon build \
    --packages-select robot_mpc_wbc_cpp_controller \
    --cmake-args -DCMAKE_BUILD_TYPE=RelWithDebInfo

  echo
  echo "[2/3] colcon test"
  colcon test \
    --packages-select robot_mpc_wbc_cpp_controller \
    --event-handlers console_direct+

  echo
  echo "[3/3] colcon test-result"
  colcon test-result --verbose

  echo
  echo "stage15_1_result: pass"
} 2>&1 | tee "$LOG_FILE"
