#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"
LOG_DIR="$REPO_ROOT/results/logs_sample"
LOG_FILE="$LOG_DIR/stage15_10_mujoco_torque_smoke_policy_comparison.log"
SUMMARY_JSON="$LOG_DIR/stage15_10_mujoco_torque_smoke_policy_comparison_summary.json"
COMPARISON_CSV="$LOG_DIR/stage15_10_mujoco_torque_smoke_policy_comparison.csv"
VALIDATION_JSON="$LOG_DIR/stage15_10_mujoco_torque_smoke_policy_comparison_validation_summary.json"
VALIDATION_CSV="$LOG_DIR/stage15_10_mujoco_torque_smoke_policy_comparison_validation.csv"
STAGE15_5_REPORT="$LOG_DIR/stage15_5_model_readiness_audit.json"
STAGE15_7_SUMMARY="$LOG_DIR/stage15_7_mujoco_candidate_compatibility_audit_summary.json"
STAGE15_9_SUMMARY="$LOG_DIR/stage15_9_mujoco_jtf_candidate_injection_summary.json"

mkdir -p "$LOG_DIR"
exec > >(tee "$LOG_FILE") 2>&1

echo "[Stage 15.10] MuJoCo torque-smoke policy comparison validation"
echo "repo_root: $REPO_ROOT"
echo "python: $PYTHON_BIN"
echo "timestamp_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

for required in "$STAGE15_5_REPORT" "$STAGE15_7_SUMMARY" "$STAGE15_9_SUMMARY"; do
  if [[ ! -f "$required" ]]; then
    echo "error: missing required prerequisite file: $required" >&2
    exit 1
  fi
done

echo "[1/2] Run MuJoCo torque-smoke policy comparison"
"$PYTHON_BIN" "$REPO_ROOT/scripts/stage15_10_compare_mujoco_torque_smoke_policies.py" \
  --repo-root "$REPO_ROOT" \
  --stage15-5-report "$STAGE15_5_REPORT" \
  --stage15-7-summary "$STAGE15_7_SUMMARY" \
  --stage15-9-summary "$STAGE15_9_SUMMARY" \
  --output-csv "$COMPARISON_CSV" \
  --output-json "$SUMMARY_JSON"
echo

echo "[2/2] Validate comparison outputs"
"$PYTHON_BIN" "$REPO_ROOT/scripts/stage15_10_validate_mujoco_torque_smoke_policy_comparison.py" \
  --summary-json "$SUMMARY_JSON" \
  --output-json "$VALIDATION_JSON" \
  --output-csv "$VALIDATION_CSV"
