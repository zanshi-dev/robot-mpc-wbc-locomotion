#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"
LOG_DIR="$REPO_ROOT/results/logs_sample"
LOG_FILE="$LOG_DIR/stage15_8_mujoco_torque_smoke_test.log"
SUMMARY_JSON="$LOG_DIR/stage15_8_mujoco_torque_smoke_test_summary.json"
SMOKE_CSV="$LOG_DIR/stage15_8_mujoco_torque_smoke_test.csv"
VALIDATION_JSON="$LOG_DIR/stage15_8_mujoco_torque_smoke_test_validation_summary.json"
VALIDATION_CSV="$LOG_DIR/stage15_8_mujoco_torque_smoke_test_validation.csv"
STAGE15_7_SUMMARY="$LOG_DIR/stage15_7_mujoco_candidate_compatibility_audit_summary.json"

mkdir -p "$LOG_DIR"
exec > >(tee "$LOG_FILE") 2>&1

echo "[Stage 15.8] Bounded MuJoCo torque-path smoke test validation"
echo "repo_root: $REPO_ROOT"
echo "python: $PYTHON_BIN"
echo "timestamp_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

if [[ ! -f "$STAGE15_7_SUMMARY" ]]; then
  echo "error: missing Stage 15.7 summary: $STAGE15_7_SUMMARY" >&2
  echo "run: bash scripts/stage15_7_validate_mujoco_candidate_compatibility_audit.sh" >&2
  exit 1
fi

echo "[1/2] Run bounded MuJoCo torque smoke test"
"$PYTHON_BIN" "$REPO_ROOT/scripts/stage15_8_mujoco_torque_smoke_test.py" \
  --repo-root "$REPO_ROOT" \
  --stage15-7-summary "$STAGE15_7_SUMMARY" \
  --output-csv "$SMOKE_CSV" \
  --output-json "$SUMMARY_JSON"
echo

echo "[2/2] Validate smoke test outputs"
"$PYTHON_BIN" "$REPO_ROOT/scripts/stage15_8_validate_mujoco_torque_smoke_test.py" \
  --summary-json "$SUMMARY_JSON" \
  --output-json "$VALIDATION_JSON" \
  --output-csv "$VALIDATION_CSV"
