#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"
LOG_DIR="$REPO_ROOT/results/logs_sample"
LOG_FILE="$LOG_DIR/stage15_5_model_readiness_audit.log"
AUDIT_JSON="$LOG_DIR/stage15_5_model_readiness_audit.json"
AUDIT_CSV="$LOG_DIR/stage15_5_model_readiness_audit_inventory.csv"
VALIDATION_JSON="$LOG_DIR/stage15_5_model_readiness_audit_validation_summary.json"
VALIDATION_CSV="$LOG_DIR/stage15_5_model_readiness_audit_validation.csv"

mkdir -p "$LOG_DIR"
exec > >(tee "$LOG_FILE") 2>&1

echo "[Stage 15.5] Model readiness audit validation"
echo "repo_root: $REPO_ROOT"
echo "python: $PYTHON_BIN"
echo "timestamp_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

echo "[1/2] Run model readiness audit"
"$PYTHON_BIN" "$REPO_ROOT/scripts/stage15_5_model_readiness_audit.py" \
  --repo-root "$REPO_ROOT" \
  --output-json "$AUDIT_JSON" \
  --output-csv "$AUDIT_CSV"
echo

echo "[2/2] Validate audit outputs"
"$PYTHON_BIN" "$REPO_ROOT/scripts/stage15_5_validate_model_readiness_audit.py" \
  --report-json "$AUDIT_JSON" \
  --output-json "$VALIDATION_JSON" \
  --output-csv "$VALIDATION_CSV"
