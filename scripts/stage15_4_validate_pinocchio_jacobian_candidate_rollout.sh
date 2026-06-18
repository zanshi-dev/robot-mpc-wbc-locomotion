#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$REPO_ROOT/results/logs_sample"
LOG_FILE="$LOG_DIR/stage15_4_pinocchio_jacobian_candidate_rollout.log"

mkdir -p "$LOG_DIR"
cd "$REPO_ROOT"

{
  echo "[Stage 15.4] Pinocchio Jacobian candidate rollout validation"
  echo "repo_root: $REPO_ROOT"
  echo "python: /usr/bin/python3"
  echo "timestamp_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo

  echo "[1/2] Generate Pinocchio Jacobian candidate rollout"
  /usr/bin/python3 scripts/stage15_4_pinocchio_jacobian_candidate_rollout.py

  echo
  echo "[2/2] Validate rollout"
  /usr/bin/python3 scripts/stage15_4_validate_pinocchio_jacobian_candidate_rollout.py

  echo
  echo "stage15_4_result: pass"
} 2>&1 | tee "$LOG_FILE"
