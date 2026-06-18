#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"
LOG_DIR="$REPO_ROOT/results/logs_sample"
LOG_FILE="$LOG_DIR/stage16_4_readme_rewrite.log"
VALIDATION_JSON="$LOG_DIR/stage16_4_readme_rewrite_validation_summary.json"
VALIDATION_CSV="$LOG_DIR/stage16_4_readme_rewrite_validation.csv"

mkdir -p "$LOG_DIR"
exec > >(tee "$LOG_FILE") 2>&1

echo "[Stage 16.4] README rewrite validation"
echo "repo_root: $REPO_ROOT"
echo "python: $PYTHON_BIN"
echo "timestamp_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

"$PYTHON_BIN" "$REPO_ROOT/scripts/stage16_4_validate_readme_rewrite.py" \
  --repo-root "$REPO_ROOT" \
  --output-json "$VALIDATION_JSON" \
  --output-csv "$VALIDATION_CSV"
