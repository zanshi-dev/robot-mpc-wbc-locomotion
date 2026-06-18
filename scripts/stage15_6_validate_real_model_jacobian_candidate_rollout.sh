#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"
LOG_DIR="$REPO_ROOT/results/logs_sample"
LOG_FILE="$LOG_DIR/stage15_6_real_model_jacobian_candidate_rollout.log"
SUMMARY_JSON="$LOG_DIR/stage15_6_real_model_jacobian_candidate_rollout_summary.json"
ROLLOUT_CSV="$LOG_DIR/stage15_6_real_model_jacobian_candidate_rollout.csv"
VALIDATION_JSON="$LOG_DIR/stage15_6_real_model_jacobian_candidate_rollout_validation_summary.json"
VALIDATION_CSV="$LOG_DIR/stage15_6_real_model_jacobian_candidate_rollout_validation.csv"
STAGE15_5_REPORT="$LOG_DIR/stage15_5_model_readiness_audit.json"

mkdir -p "$LOG_DIR"
exec > >(tee "$LOG_FILE") 2>&1

echo "[Stage 15.6] Real-model Pinocchio Jacobian candidate rollout validation"
echo "repo_root: $REPO_ROOT"
echo "python: $PYTHON_BIN"
echo "timestamp_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

if [[ ! -f "$STAGE15_5_REPORT" ]]; then
  echo "error: missing Stage 15.5 report: $STAGE15_5_REPORT" >&2
  echo "run: bash scripts/stage15_5_validate_model_readiness_audit.sh" >&2
  exit 1
fi

echo "[1/2] Run real-model Jacobian candidate rollout"
"$PYTHON_BIN" "$REPO_ROOT/scripts/stage15_6_real_model_jacobian_candidate_rollout.py" \
  --repo-root "$REPO_ROOT" \
  --stage15-5-report "$STAGE15_5_REPORT" \
  --output-csv "$ROLLOUT_CSV" \
  --output-json "$SUMMARY_JSON" \
  --total-steps 2400
echo

echo "[2/2] Validate rollout outputs"
"$PYTHON_BIN" "$REPO_ROOT/scripts/stage15_6_validate_real_model_jacobian_candidate_rollout.py" \
  --summary-json "$SUMMARY_JSON" \
  --output-json "$VALIDATION_JSON" \
  --output-csv "$VALIDATION_CSV"
