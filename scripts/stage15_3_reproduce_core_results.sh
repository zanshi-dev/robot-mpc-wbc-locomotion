#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

LOG_DIR="results/logs_sample"
LOG_FILE="${LOG_DIR}/stage15_3_reproduce_core_results.log"
SUMMARY_FILE="${LOG_DIR}/stage15_3_reproduce_core_results_summary.txt"

mkdir -p "$LOG_DIR"
: > "$LOG_FILE"
: > "$SUMMARY_FILE"

log() {
  echo "$*" | tee -a "$LOG_FILE"
}

summary() {
  echo "$*" | tee -a "$SUMMARY_FILE" | tee -a "$LOG_FILE" >/dev/null
}

section() {
  echo "" | tee -a "$LOG_FILE"
  echo "========== $* ==========" | tee -a "$LOG_FILE"
}

run_cmd() {
  local name="$1"
  shift

  section "$name"
  log "command: $*"

  if "$@" >> "$LOG_FILE" 2>&1; then
    log "[PASS] $name"
    summary "[PASS] $name"
  else
    log "[FAIL] $name"
    summary "[FAIL] $name"
    exit 1
  fi
}

run_bash() {
  local name="$1"
  local cmd="$2"

  section "$name"
  log "command: ${cmd}"

  if bash -lc "$cmd" >> "$LOG_FILE" 2>&1; then
    log "[PASS] $name"
    summary "[PASS] $name"
  else
    log "[FAIL] $name"
    summary "[FAIL] $name"
    exit 1
  fi
}

section "Stage 15.3 Reproduce Core Results"
log "repo_root: $REPO_ROOT"
log "log_file: $LOG_FILE"
log "summary_file: $SUMMARY_FILE"
log "timestamp: $(date -Iseconds)"
log "git_head: $(git rev-parse --short HEAD)"
log "git_branch: $(git rev-parse --abbrev-ref HEAD)"
log "python: $(/usr/bin/python3 --version 2>&1)"

summary "stage15_3_reproduce_core_results"
summary "repo_root: $REPO_ROOT"
summary "git_head: $(git rev-parse --short HEAD)"
summary "git_branch: $(git rev-parse --abbrev-ref HEAD)"

section "Git working tree"
git status --short | tee -a "$LOG_FILE"

# This script itself and its log may be uncommitted during first run.
# Therefore dirty tree is recorded but not treated as failure.

if [[ -x "scripts/stage15_2_repo_hygiene_audit.sh" ]]; then
  run_cmd "Stage 15.2 repo hygiene audit" bash scripts/stage15_2_repo_hygiene_audit.sh
else
  section "Stage 15.2 repo hygiene audit"
  log "[WARN] scripts/stage15_2_repo_hygiene_audit.sh not found or not executable; skipping"
  summary "[WARN] Stage 15.2 repo hygiene audit skipped"
fi

if [[ -f "scripts/stage14_4_base_velocity_tracking_mpc_demo.py" ]]; then
  run_cmd "Stage 14.4 base velocity tracking MPC demo" /usr/bin/python3 scripts/stage14_4_base_velocity_tracking_mpc_demo.py
else
  section "Stage 14.4 base velocity tracking MPC demo"
  log "[FAIL] missing scripts/stage14_4_base_velocity_tracking_mpc_demo.py"
  summary "[FAIL] missing Stage 14.4 MPC demo"
  exit 1
fi

if [[ -f "scripts/stage14_4b_validate_base_velocity_mpc_rollout.py" ]]; then
  run_cmd "Stage 14.4b validate base velocity MPC rollout" /usr/bin/python3 scripts/stage14_4b_validate_base_velocity_mpc_rollout.py
else
  section "Stage 14.4b validate base velocity MPC rollout"
  log "[FAIL] missing scripts/stage14_4b_validate_base_velocity_mpc_rollout.py"
  summary "[FAIL] missing Stage 14.4b validation"
  exit 1
fi

if [[ -x "scripts/stage15_1_validate_ros2_cpp_controller.sh" ]]; then
  run_cmd "Stage 15.1 ROS2 C++ controller validation" bash scripts/stage15_1_validate_ros2_cpp_controller.sh
elif [[ -f "ros2_ws/src/robot_mpc_wbc_cpp_controller/CMakeLists.txt" ]]; then
  if command -v colcon >/dev/null 2>&1 && [[ -f "/opt/ros/jazzy/setup.bash" ]]; then
    run_bash "ROS2 C++ controller colcon build/test" \
      "source /opt/ros/jazzy/setup.bash && cd ros2_ws && colcon build --packages-select robot_mpc_wbc_cpp_controller && colcon test --packages-select robot_mpc_wbc_cpp_controller && colcon test-result --verbose"
  else
    section "ROS2 C++ controller validation"
    log "[WARN] colcon or /opt/ros/jazzy/setup.bash not available; using direct C++ fallback if possible"
    summary "[WARN] colcon unavailable; trying direct C++ fallback"

    CPP_ROOT="ros2_ws/src/robot_mpc_wbc_cpp_controller"
    if [[ -f "${CPP_ROOT}/test/test_control_algorithms.cpp" ]]; then
      run_bash "Direct C++ control algorithm test fallback" \
        "g++ -std=c++17 -Wall -Wextra -Werror -I ${CPP_ROOT}/include ${CPP_ROOT}/src/control/gait_scheduler.cpp ${CPP_ROOT}/src/control/swing_trajectory.cpp ${CPP_ROOT}/src/control/torque_safety_filter.cpp ${CPP_ROOT}/test/test_control_algorithms.cpp -o /tmp/test_control_algorithms_stage15_3 && /tmp/test_control_algorithms_stage15_3"
    else
      log "[FAIL] no C++ validation path available"
      summary "[FAIL] no C++ validation path available"
      exit 1
    fi
  fi
else
  section "ROS2 C++ controller validation"
  log "[FAIL] C++ controller CMakeLists missing"
  summary "[FAIL] C++ controller CMakeLists missing"
  exit 1
fi

section "Generated result artifacts"
find results/logs_sample -maxdepth 1 -type f \
  \( -name "*stage14_4*" -o -name "*stage15_1*" -o -name "*stage15_2*" -o -name "*stage15_3*" \) \
  -print | sort | tee -a "$LOG_FILE"

section "Final summary"
cat "$SUMMARY_FILE" | tee -a "$LOG_FILE"

if grep -q "^\[FAIL\]" "$SUMMARY_FILE"; then
  log "stage15_3_result: fail"
  exit 1
fi

log "stage15_3_result: pass"
summary "stage15_3_result: pass"
