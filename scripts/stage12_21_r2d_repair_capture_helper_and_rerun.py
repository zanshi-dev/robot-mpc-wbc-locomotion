#!/usr/bin/env /usr/bin/python3
from pathlib import Path
import json
import subprocess
from datetime import datetime

ROOT = Path.cwd()
OUT = ROOT / "results/logs_sample"
DOCS = ROOT / "docs"
OUT.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)

SUMMARY = OUT / "stage12_21_r2d_repair_capture_helper_and_rerun_summary.json"
DOC = DOCS / "stage12_21_r2d_repair_capture_helper_and_rerun.md"
R2B_SUMMARY = OUT / "stage12_21_r2b_robust_subscriber_warmup_rerun_summary.json"
R2B_RUN_LOG = OUT / "stage12_21_r2d_r2b_rerun.log"

CAPTURE_HELPER = ROOT / "scripts/stage12_21_r2b_capture.py"
MAIN_SCRIPT = ROOT / "scripts/stage12_21_r2b_robust_subscriber_warmup_rerun.py"

fail_reasons = []

if not CAPTURE_HELPER.exists():
    fail_reasons.append("capture helper missing before rerun")
if not MAIN_SCRIPT.exists():
    fail_reasons.append("R2B main script missing before rerun")

rerun_returncode = None
if not fail_reasons:
    p = subprocess.run(
        ["/usr/bin/python3", str(MAIN_SCRIPT)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    rerun_returncode = p.returncode
    R2B_RUN_LOG.write_text(p.stdout, encoding="utf-8", errors="replace")

r2b = None
if R2B_SUMMARY.exists():
    r2b = json.loads(R2B_SUMMARY.read_text(encoding="utf-8", errors="replace"))
else:
    fail_reasons.append("R2B summary missing after rerun")

if r2b:
    required = {
        "r2b_pass": r2b.get("pass") is True,
        "source_changed_false": r2b.get("source_changed") is False,
        "source_hash_matches_stage1220e": r2b.get("source_hash_matches_stage1220e") is True,
        "publish_call_count_is_1": r2b.get("publish_call_count") == 1,
        "node_seen": r2b.get("node_seen") is True,
        "subscriber_ready_before_activation": r2b.get("subscriber_ready_before_activation") is True,
        "capture_ok": r2b.get("capture_ok") is True,
        "param_set_ok": r2b.get("param_set_ok") is True,
        "stream_message_count_in_1_to_30": r2b.get("stream_message_count_in_1_to_30") is True,
        "all_stream_payloads_length_12": r2b.get("all_stream_payloads_length_12") is True,
        "all_stream_payload_values_finite": r2b.get("all_stream_payload_values_finite") is True,
        "all_stream_payload_values_zero_safe": r2b.get("all_stream_payload_values_zero_safe") is True,
        "final_flags_false": r2b.get("final_flags_false") is True,
        "after_stop_no_messages": r2b.get("after_stop_no_messages") is True,
        "target_process_after_count_is_0": r2b.get("target_process_after_count") == 0,
        "continuous_torque_streaming_completed": r2b.get("continuous_torque_streaming_completed") is True,
        "torque_enable_ready_false": r2b.get("torque_enable_ready") is False,
        "torque_publisher_enabled_false": r2b.get("torque_publisher_enabled") is False,
        "hardware_deployment_completed_false": r2b.get("hardware_deployment_completed") is False,
        "control_law_changed_false": r2b.get("control_law_changed") is False,
    }

    for k, ok in required.items():
        if not ok:
            fail_reasons.append(f"R2B validation failed: {k}")

summary = {
    "stage": "12.21-R2D",
    "name": "repair_missing_capture_helper_and_rerun_r2b",
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "pass": len(fail_reasons) == 0,
    "fail_reasons": fail_reasons,
    "source_changed": False,
    "capture_helper_exists": CAPTURE_HELPER.exists(),
    "main_script_exists": MAIN_SCRIPT.exists(),
    "r2b_rerun_returncode": rerun_returncode,
    "r2b_summary": r2b,
    "torque_enable_ready": False,
    "torque_publisher_enabled": False,
    "hardware_deployment_completed": False,
    "control_law_changed": False,
    "logs": {
        "r2b_rerun_log": str(R2B_RUN_LOG),
        "r2b_summary": str(R2B_SUMMARY),
        "r2b_capture_json": str(OUT / "stage12_21_r2b_capture.json"),
        "r2b_after_stop_capture_json": str(OUT / "stage12_21_r2b_after_stop_capture.json"),
    },
}

SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

md = [
    "# Stage 12.21-R2D Repair Capture Helper and Rerun R2B",
    "",
    f"- pass: `{summary['pass']}`",
    f"- fail_reasons: `{summary['fail_reasons']}`",
    f"- source_changed: `{summary['source_changed']}`",
    f"- capture_helper_exists: `{summary['capture_helper_exists']}`",
    f"- main_script_exists: `{summary['main_script_exists']}`",
    f"- r2b_rerun_returncode: `{summary['r2b_rerun_returncode']}`",
    f"- r2b_pass: `{None if r2b is None else r2b.get('pass')}`",
    f"- stream_message_count: `{None if r2b is None else r2b.get('stream_message_count')}`",
    f"- all_stream_payloads_length_12: `{None if r2b is None else r2b.get('all_stream_payloads_length_12')}`",
    f"- all_stream_payload_values_finite: `{None if r2b is None else r2b.get('all_stream_payload_values_finite')}`",
    f"- all_stream_payload_values_zero_safe: `{None if r2b is None else r2b.get('all_stream_payload_values_zero_safe')}`",
    f"- after_stop_no_messages: `{None if r2b is None else r2b.get('after_stop_no_messages')}`",
    "",
    "Safety boundary: capture helper repair only; no C++ source change; bounded zero/safe regression only; no hardware deployment.",
]

DOC.write_text("\n".join(md), encoding="utf-8")
print(json.dumps(summary, indent=2, ensure_ascii=False))
