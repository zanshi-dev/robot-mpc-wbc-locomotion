#!/usr/bin/env bash
set -eo pipefail

ROOT="$(pwd)"
OUT_DIR="$ROOT/results/logs_sample"
DOC_DIR="$ROOT/docs"
mkdir -p "$OUT_DIR" "$DOC_DIR"

SUMMARY_JSON="$OUT_DIR/stage12_21_r2a_cleanup_and_failed_capture_inspection_summary.json"
DOC_MD="$DOC_DIR/stage12_21_r2a_cleanup_and_failed_capture_inspection.md"

PROC_BEFORE="$OUT_DIR/stage12_21_r2a_processes_before_cleanup.log"
PROC_AFTER="$OUT_DIR/stage12_21_r2a_processes_after_cleanup.log"
NODE_BEFORE="$OUT_DIR/stage12_21_r2a_nodes_before_cleanup.log"
NODE_AFTER="$OUT_DIR/stage12_21_r2a_nodes_after_cleanup.log"
DAEMON_LOG="$OUT_DIR/stage12_21_r2a_ros2_daemon_reset.log"
KILL_LOG="$OUT_DIR/stage12_21_r2a_kill.log"
R2_FILE_STATUS="$OUT_DIR/stage12_21_r2a_r2_file_status.log"

source /opt/ros/jazzy/setup.bash
source "$ROOT/install/setup.bash"

list_target_processes() {
  ps -u "$USER" -o pid=,ppid=,stat=,comm=,args= \
    | grep -E "go1_disabled_controller_node|stage12_21_r2_subscriber_capture.py|stage12_21_r2_joint_torque_capture|ros2 topic echo.*/go1/joint_torque_cmd" \
    | grep -v grep || true
}

list_target_processes > "$PROC_BEFORE"

set +e
ros2 node list > "$NODE_BEFORE" 2>&1
NODE_BEFORE_RC=$?
set -e

{
  echo "pkill go1_disabled_controller_node"
  pkill -f "go1_disabled_controller_node" || true

  echo "pkill stage12_21_r2_subscriber_capture.py"
  pkill -f "stage12_21_r2_subscriber_capture.py" || true

  echo "pkill stage12_21_r2_joint_torque_capture"
  pkill -f "stage12_21_r2_joint_torque_capture" || true

  echo "pkill ros2 topic echo /go1/joint_torque_cmd"
  pkill -f "ros2 topic echo.*/go1/joint_torque_cmd" || true
} > "$KILL_LOG" 2>&1

sleep 2

{
  echo "ros2 daemon stop"
  ros2 daemon stop || true
  sleep 1
  echo "ros2 daemon start"
  ros2 daemon start || true
  sleep 2
} > "$DAEMON_LOG" 2>&1

list_target_processes > "$PROC_AFTER"

set +e
ros2 node list > "$NODE_AFTER" 2>&1
NODE_AFTER_RC=$?
set -e

{
  for f in \
    results/logs_sample/stage12_21_r2_subscriber_warmup_bounded_streaming_rerun_summary.json \
    docs/stage12_21_r2_subscriber_warmup_bounded_streaming_rerun.md \
    results/logs_sample/stage12_21_r2_capture.json \
    results/logs_sample/stage12_21_r2_after_stop_capture.json \
    results/logs_sample/stage12_21_r2_capture.log \
    results/logs_sample/stage12_21_r2_after_stop_capture.log \
    results/logs_sample/stage12_21_r2_param_set.log \
    results/logs_sample/stage12_21_r2_param_final.log \
    results/logs_sample/stage12_21_r2_node.log
  do
    if [ -f "$f" ]; then
      printf "exists size=%s %s\n" "$(wc -c < "$f")" "$f"
    else
      printf "missing %s\n" "$f"
    fi
  done
} > "$R2_FILE_STATUS"

/usr/bin/python3 - "$SUMMARY_JSON" "$DOC_MD" "$PROC_BEFORE" "$PROC_AFTER" "$NODE_BEFORE" "$NODE_AFTER" "$DAEMON_LOG" "$KILL_LOG" "$R2_FILE_STATUS" "$NODE_BEFORE_RC" "$NODE_AFTER_RC" <<'PY'
import json
import re
import sys
from pathlib import Path
from datetime import datetime

summary_path = Path(sys.argv[1])
doc_path = Path(sys.argv[2])
proc_before = Path(sys.argv[3])
proc_after = Path(sys.argv[4])
node_before = Path(sys.argv[5])
node_after = Path(sys.argv[6])
daemon_log = Path(sys.argv[7])
kill_log = Path(sys.argv[8])
r2_file_status = Path(sys.argv[9])
node_before_rc = int(sys.argv[10])
node_after_rc = int(sys.argv[11])

def read(p):
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""

proc_before_text = read(proc_before)
proc_after_text = read(proc_after)
node_before_text = read(node_before)
node_after_text = read(node_after)
r2_files_text = read(r2_file_status)

target_proc_after_count = len([x for x in proc_after_text.splitlines() if x.strip()])
go1_node_after_count = len(re.findall(r"^/go1_disabled_controller_node$", node_after_text, re.MULTILINE))
capture_node_after_count = len(re.findall(r"stage12_21_r2_joint_torque_capture", node_after_text))
duplicate_warning_before = "share an exact name" in node_before_text
duplicate_warning_after = "share an exact name" in node_after_text

r2_summary_exists = "exists" in r2_files_text and "stage12_21_r2_subscriber_warmup_bounded_streaming_rerun_summary.json" in r2_files_text
r2_capture_exists = "exists" in r2_files_text and "stage12_21_r2_capture.json" in r2_files_text
r2_after_stop_exists = "exists" in r2_files_text and "stage12_21_r2_after_stop_capture.json" in r2_files_text

fail_reasons = []
if target_proc_after_count != 0:
    fail_reasons.append(f"target processes still alive after cleanup: {target_proc_after_count}")
if go1_node_after_count != 0:
    fail_reasons.append(f"/go1_disabled_controller_node still visible after cleanup: {go1_node_after_count}")
if capture_node_after_count != 0:
    fail_reasons.append(f"capture node still visible after cleanup: {capture_node_after_count}")
if duplicate_warning_after:
    fail_reasons.append("duplicate-node warning still present after daemon reset")

summary = {
    "stage": "12.21-R2A",
    "name": "cleanup_and_failed_capture_inspection_before_rerun",
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "pass": len(fail_reasons) == 0,
    "fail_reasons": fail_reasons,
    "source_changed": False,
    "inspection_only": True,
    "node_before_returncode": node_before_rc,
    "node_after_returncode": node_after_rc,
    "duplicate_warning_before": duplicate_warning_before,
    "duplicate_warning_after": duplicate_warning_after,
    "target_process_after_count": target_proc_after_count,
    "go1_node_after_count": go1_node_after_count,
    "capture_node_after_count": capture_node_after_count,
    "r2_summary_exists": r2_summary_exists,
    "r2_capture_exists": r2_capture_exists,
    "r2_after_stop_capture_exists": r2_after_stop_exists,
    "recommended_next_stage": "Stage 12.21-R2B robust subscriber-warmup rerun with pre-cleanup and always-write summary; no source change",
    "logs": {
        "processes_before": str(proc_before),
        "processes_after": str(proc_after),
        "nodes_before": str(node_before),
        "nodes_after": str(node_after),
        "daemon_log": str(daemon_log),
        "kill_log": str(kill_log),
        "r2_file_status": str(r2_file_status),
    },
}

summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

doc = [
    "# Stage 12.21-R2A Cleanup and Failed Capture Inspection",
    "",
    f"- pass: `{summary['pass']}`",
    f"- fail_reasons: `{summary['fail_reasons']}`",
    f"- source_changed: `{summary['source_changed']}`",
    f"- inspection_only: `{summary['inspection_only']}`",
    f"- duplicate_warning_before: `{summary['duplicate_warning_before']}`",
    f"- duplicate_warning_after: `{summary['duplicate_warning_after']}`",
    f"- target_process_after_count: `{summary['target_process_after_count']}`",
    f"- go1_node_after_count: `{summary['go1_node_after_count']}`",
    f"- capture_node_after_count: `{summary['capture_node_after_count']}`",
    f"- r2_summary_exists: `{summary['r2_summary_exists']}`",
    f"- r2_capture_exists: `{summary['r2_capture_exists']}`",
    f"- r2_after_stop_capture_exists: `{summary['r2_after_stop_capture_exists']}`",
    "",
    f"Recommended next stage: `{summary['recommended_next_stage']}`",
    "",
    "Safety boundary: cleanup/inspection only; no source change; no hardware deployment.",
]
doc_path.write_text("\n".join(doc), encoding="utf-8")

print(json.dumps(summary, indent=2, ensure_ascii=False))
PY
