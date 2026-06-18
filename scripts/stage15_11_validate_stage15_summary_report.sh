#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"
LOG_DIR="$REPO_ROOT/results/logs_sample"
LOG_FILE="$LOG_DIR/stage15_11_stage15_summary_report.log"
REPORT_JSON="$LOG_DIR/stage15_11_stage15_summary_report.json"
REPORT_CSV="$LOG_DIR/stage15_11_stage15_summary_report.csv"
REPORT_MD="$REPO_ROOT/docs/STAGE15_UPGRADE_SUMMARY.md"
VALIDATION_JSON="$LOG_DIR/stage15_11_stage15_summary_report_validation_summary.json"
VALIDATION_CSV="$LOG_DIR/stage15_11_stage15_summary_report_validation.csv"

mkdir -p "$LOG_DIR"
exec > >(tee "$LOG_FILE") 2>&1

echo "[Stage 15.11] Stage 15 summary report validation"
echo "repo_root: $REPO_ROOT"
echo "python: $PYTHON_BIN"
echo "timestamp_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

echo "[1/2] Generate Stage 15 summary report"
"$PYTHON_BIN" "$REPO_ROOT/scripts/stage15_11_stage15_summary_report.py" \
  --repo-root "$REPO_ROOT" \
  --output-json "$REPORT_JSON" \
  --output-csv "$REPORT_CSV" \
  --output-md "$REPORT_MD"
echo

echo "[2/2] Validate Stage 15 summary report"
"$PYTHON_BIN" "$REPO_ROOT/scripts/stage15_11_validate_stage15_summary_report.py" \
  --report-json "$REPORT_JSON" \
  --report-md "$REPORT_MD" \
  --output-json "$VALIDATION_JSON" \
  --output-csv "$VALIDATION_CSV"
