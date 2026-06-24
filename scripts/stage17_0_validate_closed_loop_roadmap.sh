#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${REPO_ROOT}/results/logs_sample"
LOG_FILE="${LOG_DIR}/stage17_0_closed_loop_roadmap_validation.log"
SUMMARY_FILE="${LOG_DIR}/stage17_0_closed_loop_roadmap_validation_summary.json"

mkdir -p "${LOG_DIR}"

{
  echo "[Stage 17.0] Closed-loop roadmap validation"
  echo "repo_root: ${REPO_ROOT}"
  echo "timestamp_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo

  DOC="${REPO_ROOT}/docs/STAGE17_CLOSED_LOOP_ROADMAP.md"
  pass=true

  check_file() {
    local path="$1"
    local name="$2"
    if [[ -f "${path}" ]]; then
      echo "PASS: ${name} -- ${path}"
    else
      echo "FAIL: ${name} -- missing ${path}"
      pass=false
    fi
  }

  check_contains() {
    local path="$1"
    local pattern="$2"
    local name="$3"
    if grep -Fq "${pattern}" "${path}"; then
      echo "PASS: ${name} -- pattern '${pattern}'"
    else
      echo "FAIL: ${name} -- pattern '${pattern}' not found"
      pass=false
    fi
  }

  check_file "${DOC}" "stage17_roadmap_exists"

  if [[ -f "${DOC}" ]]; then
    check_contains "${DOC}" "torque-level closed-loop rollout" "closed_loop_goal"
    check_contains "${DOC}" "MPC contact force reference" "mpc_force_reference"
    check_contains "${DOC}" "WBC / J^T f torque candidate" "wbc_jtf_candidate"
    check_contains "${DOC}" "torque safety filter" "torque_safety_filter"
    check_contains "${DOC}" "不声明" "boundary_statement"
    check_contains "${DOC}" "rollout metrics" "metrics_plan"
    check_contains "${DOC}" "Stage 17.1" "stage17_1_plan"
    check_contains "${DOC}" "Stage 17.4" "stage17_4_plan"
  fi

  echo

  if [[ "${pass}" == "true" ]]; then
    echo "stage17_0_result: pass"
    cat > "${SUMMARY_FILE}" <<JSON
{
  "stage": "17.0",
  "result": "pass",
  "roadmap": "docs/STAGE17_CLOSED_LOOP_ROADMAP.md",
  "log": "results/logs_sample/stage17_0_closed_loop_roadmap_validation.log"
}
JSON
  else
    echo "stage17_0_result: fail"
    cat > "${SUMMARY_FILE}" <<JSON
{
  "stage": "17.0",
  "result": "fail",
  "roadmap": "docs/STAGE17_CLOSED_LOOP_ROADMAP.md",
  "log": "results/logs_sample/stage17_0_closed_loop_roadmap_validation.log"
}
JSON
    exit 1
  fi
} | tee "${LOG_FILE}"
