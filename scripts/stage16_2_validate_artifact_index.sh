#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"
LOG_DIR="$REPO_ROOT/results/logs_sample"
LOG_FILE="$LOG_DIR/stage16_2_artifact_index.log"
SUMMARY_JSON="$LOG_DIR/stage16_2_artifact_index_summary.json"
VALIDATION_JSON="$LOG_DIR/stage16_2_artifact_index_validation_summary.json"
VALIDATION_CSV="$LOG_DIR/stage16_2_artifact_index_validation.csv"

mkdir -p "$LOG_DIR"
exec > >(tee "$LOG_FILE") 2>&1

echo "[Stage 16.2] Artifact index validation"
echo "repo_root: $REPO_ROOT"
echo "python: $PYTHON_BIN"
echo "timestamp_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

echo "[1/2] Generate artifact index"
"$PYTHON_BIN" "$REPO_ROOT/scripts/stage16_2_generate_artifact_index.py" \
  --repo-root "$REPO_ROOT"
echo

echo "[2/2] Validate artifact index"
"$PYTHON_BIN" "$REPO_ROOT/scripts/stage16_2_validate_artifact_index.py" \
  --repo-root "$REPO_ROOT" \
  --summary-json "$SUMMARY_JSON" \
  --output-json "$VALIDATION_JSON" \
  --output-csv "$VALIDATION_CSV"
