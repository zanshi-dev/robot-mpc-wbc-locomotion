#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"
LOG_DIR="$REPO_ROOT/results/logs_sample"
LOG_FILE="$LOG_DIR/stage15_9_mujoco_jtf_candidate_injection.log"
SUMMARY_JSON="$LOG_DIR/stage15_9_mujoco_jtf_candidate_injection_summary.json"
INJECTION_CSV="$LOG_DIR/stage15_9_mujoco_jtf_candidate_injection.csv"
VALIDATION_JSON="$LOG_DIR/stage15_9_mujoco_jtf_candidate_injection_validation_summary.json"
VALIDATION_CSV="$LOG_DIR/stage15_9_mujoco_jtf_candidate_injection_validation.csv"
STAGE15_5_REPORT="$LOG_DIR/stage15_5_model_readiness_audit.json"
STAGE15_6_SUMMARY="$LOG_DIR/stage15_6_real_model_jacobian_candidate_rollout_summary.json"
STAGE15_7_SUMMARY="$LOG_DIR/stage15_7_mujoco_candidate_compatibility_audit_summary.json"

mkdir -p "$LOG_DIR"
exec > >(tee "$LOG_FILE") 2>&1

echo "[Stage 15.9] MuJoCo J^T f candidate injection validation"
echo "repo_root: $REPO_ROOT"
echo "python: $PYTHON_BIN"
echo "timestamp_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

for required in "$STAGE15_5_REPORT" "$STAGE15_6_SUMMARY" "$STAGE15_7_SUMMARY"; do
  if [[ ! -f "$required" ]]; then
    echo "error: missing required prerequisite file: $required" >&2
    exit 1
  fi
done

echo "[1/2] Run bounded MuJoCo J^T f candidate injection"
"$PYTHON_BIN" "$REPO_ROOT/scripts/stage15_9_mujoco_jtf_candidate_injection.py" \
  --repo-root "$REPO_ROOT" \
  --stage15-5-report "$STAGE15_5_REPORT" \
  --stage15-6-summary "$STAGE15_6_SUMMARY" \
  --stage15-7-summary "$STAGE15_7_SUMMARY" \
  --output-csv "$INJECTION_CSV" \
  --output-json "$SUMMARY_JSON"
echo

echo "[2/2] Validate injection outputs"
"$PYTHON_BIN" "$REPO_ROOT/scripts/stage15_9_validate_mujoco_jtf_candidate_injection.py" \
  --summary-json "$SUMMARY_JSON" \
  --output-json "$VALIDATION_JSON" \
  --output-csv "$VALIDATION_CSV"
