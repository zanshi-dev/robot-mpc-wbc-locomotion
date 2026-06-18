#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

LOG_DIR="results/logs_sample"
LOG_FILE="${LOG_DIR}/stage15_2_repo_hygiene_audit.log"

mkdir -p "$LOG_DIR"
: > "$LOG_FILE"

log() {
  echo "$*" | tee -a "$LOG_FILE"
}

section() {
  echo "" | tee -a "$LOG_FILE"
  echo "========== $* ==========" | tee -a "$LOG_FILE"
}

fail_count=0
warn_count=0

pass() {
  log "[PASS] $*"
}

warn() {
  log "[WARN] $*"
  warn_count=$((warn_count + 1))
}

fail() {
  log "[FAIL] $*"
  fail_count=$((fail_count + 1))
}

section "Stage 15.2 Repo Hygiene Audit"
log "repo_root: $REPO_ROOT"
log "log_file: $LOG_FILE"

section "Git status"

current_branch="$(git rev-parse --abbrev-ref HEAD)"
log "current_branch: ${current_branch}"

if [[ "$current_branch" == "main" ]]; then
  pass "current branch is main"
else
  warn "current branch is not main"
fi

remote_url="$(git remote get-url origin 2>/dev/null || true)"
log "origin_url: ${remote_url}"

if [[ "$remote_url" == "git@github.com:zanshi-dev/robot-mpc-wbc-locomotion.git" ]]; then
  pass "origin remote matches expected GitHub SSH URL"
else
  warn "origin remote differs from expected URL"
fi

git_status_short="$(git status --short)"
if [[ -z "$git_status_short" ]]; then
  pass "working tree is clean"
else
  warn "working tree has uncommitted changes"
  log "$git_status_short"
fi

local_head="$(git rev-parse --short HEAD)"
log "local_head: ${local_head}"

if git rev-parse --verify origin/main >/dev/null 2>&1; then
  origin_head="$(git rev-parse --short origin/main)"
  log "origin_main: ${origin_head}"

  if [[ "$local_head" == "$origin_head" ]]; then
    pass "local HEAD matches origin/main"
  else
    warn "local HEAD differs from origin/main"
  fi
else
  warn "origin/main is not available locally; run git fetch origin if needed"
fi

section "Root file hygiene"

root_temp_files="$(
  find . -maxdepth 1 -type f \( \
    -name "*.save" -o \
    -name "*.bak" -o \
    -name "*.bak_*" -o \
    -name "*~" -o \
    -name "*.tmp" -o \
    -name "*.old" \
  \) -print | sort
)"

if [[ -z "$root_temp_files" ]]; then
  pass "no root-level backup/temp files found"
else
  fail "root-level backup/temp files found"
  log "$root_temp_files"
fi

section "Required top-level structure"

required_paths=(
  "README.md"
  "PROJECT_STATUS.md"
  "docs"
  "scripts"
  "results/logs_sample"
  "ros2_ws"
  "ros2_ws/src"
  "ros2_ws/src/robot_mpc_wbc_cpp_controller"
  "ros2_ws/src/robot_mpc_wbc_bridge"
)

for p in "${required_paths[@]}"; do
  if [[ -e "$p" ]]; then
    pass "exists: $p"
  else
    fail "missing: $p"
  fi
done

section "Key documentation files"

doc_candidates=(
  "docs/ONE_PAGE_TECHNICAL_REPORT.md"
  "docs/REPORT_READY_RESULTS.md"
  "docs/CONTROL_ARCHITECTURE_OVERVIEW.md"
  "docs/WBC_QP_EXPLAINED.md"
  "docs/CPP_CONTROL_ALGORITHMS.md"
  "docs/FINAL_PACKAGE_WITH_DEMO_VIDEO_MANIFEST.md"
)

for p in "${doc_candidates[@]}"; do
  if [[ -f "$p" ]]; then
    pass "doc exists: $p"
  else
    warn "doc not found: $p"
  fi
done

section "Core scripts"

script_candidates=(
  "scripts/stage14_4_base_velocity_tracking_mpc_demo.py"
  "scripts/stage14_4b_validate_base_velocity_mpc_rollout.py"
)

for p in "${script_candidates[@]}"; do
  if [[ -f "$p" ]]; then
    pass "script exists: $p"
  else
    warn "script not found: $p"
  fi
done

section "ROS2 package files"

BRIDGE_PKG="ros2_ws/src/robot_mpc_wbc_bridge"
CPP_PKG="ros2_ws/src/robot_mpc_wbc_cpp_controller"

if [[ -f "${BRIDGE_PKG}/package.xml" ]]; then
  pass "bridge package.xml exists"
else
  fail "bridge package.xml missing"
fi

if [[ -f "${BRIDGE_PKG}/CMakeLists.txt" ]]; then
  pass "bridge appears to be an ament_cmake package"
elif [[ -f "${BRIDGE_PKG}/setup.py" || -f "${BRIDGE_PKG}/setup.cfg" || -f "${BRIDGE_PKG}/pyproject.toml" ]]; then
  pass "bridge appears to be an ament_python/Python ROS2 package; CMakeLists.txt not required"
else
  fail "bridge has neither CMakeLists.txt nor Python package metadata"
fi

if [[ -f "${CPP_PKG}/package.xml" ]]; then
  pass "C++ controller package.xml exists"
else
  fail "C++ controller package.xml missing"
fi

if [[ -f "${CPP_PKG}/CMakeLists.txt" ]]; then
  pass "C++ controller CMakeLists.txt exists"
else
  fail "C++ controller CMakeLists.txt missing"
fi

section "C++ controller module structure"

cpp_paths=(
  "ros2_ws/src/robot_mpc_wbc_cpp_controller/include"
  "ros2_ws/src/robot_mpc_wbc_cpp_controller/src"
  "ros2_ws/src/robot_mpc_wbc_cpp_controller/test"
)

for p in "${cpp_paths[@]}"; do
  if [[ -e "$p" ]]; then
    pass "C++ path exists: $p"
  else
    fail "C++ path missing: $p"
  fi
done

cpp_expected_files=(
  "ros2_ws/src/robot_mpc_wbc_cpp_controller/test/test_control_algorithms.cpp"
)

for p in "${cpp_expected_files[@]}"; do
  if [[ -f "$p" ]]; then
    pass "C++ test file exists: $p"
  else
    fail "C++ test file missing: $p"
  fi
done

section "CMake test integration check"

CPP_CMAKE="ros2_ws/src/robot_mpc_wbc_cpp_controller/CMakeLists.txt"

if [[ -f "$CPP_CMAKE" ]]; then
  if grep -Eq "ament_add_gtest|add_test|enable_testing|BUILD_TESTING" "$CPP_CMAKE"; then
    pass "C++ CMakeLists appears to contain test integration"
  else
    fail "C++ CMakeLists does not appear to contain test integration"
  fi
else
  fail "C++ CMakeLists missing; cannot check test integration"
fi

section "ROS topic / executable naming check"

if grep -R "/go1/joint_torque_cmd" -n ros2_ws/src >/dev/null 2>&1; then
  pass "ROS torque topic /go1/joint_torque_cmd found in ros2_ws/src"
else
  warn "ROS torque topic /go1/joint_torque_cmd not found by grep"
fi

if grep -R "go1_disabled_controller_node" -n ros2_ws/src >/dev/null 2>&1; then
  pass "disabled controller executable/name found"
else
  warn "go1_disabled_controller_node not found by grep"
fi

if grep -R "mujoco_bridge_node" -n ros2_ws/src >/dev/null 2>&1; then
  pass "mujoco_bridge_node found"
else
  warn "mujoco_bridge_node not found by grep"
fi

section "Python import smoke check"

PYTHON_BIN="/usr/bin/python3"
log "python_bin: ${PYTHON_BIN}"

if "$PYTHON_BIN" - <<'PY' >> "$LOG_FILE" 2>&1
import importlib

modules = [
    "numpy",
    "scipy",
    "scipy.sparse",
    "osqp",
    "mujoco",
    "pinocchio",
]

missing = []
for m in modules:
    try:
        importlib.import_module(m)
        print(f"[PASS] import {m}")
    except Exception as e:
        print(f"[FAIL] import {m}: {type(e).__name__}: {e}")
        missing.append(m)

if missing:
    raise SystemExit(1)
PY
then
  pass "Python dependency smoke check passed"
else
  fail "Python dependency smoke check failed"
fi

section "Summary"

log "warn_count: ${warn_count}"
log "fail_count: ${fail_count}"

if [[ "$fail_count" -eq 0 ]]; then
  log "stage15_2_result: pass"
  exit 0
else
  log "stage15_2_result: fail"
  exit 1
fi
