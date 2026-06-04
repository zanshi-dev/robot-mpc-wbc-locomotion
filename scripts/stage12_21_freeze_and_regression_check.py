#!/usr/bin/env /usr/bin/python3
from pathlib import Path
import hashlib
import json
import re
import subprocess
from datetime import datetime

ROOT = Path.cwd()
SRC = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
OUT_DIR = ROOT / "results/logs_sample"
DOC_DIR = ROOT / "docs"
PROJECT_STATUS = ROOT / "PROJECT_STATUS.md"

OUT_DIR.mkdir(parents=True, exist_ok=True)
DOC_DIR.mkdir(parents=True, exist_ok=True)

STAGE1220E = OUT_DIR / "stage12_20e_final_evidence_freeze_summary.json"
SUMMARY_JSON = OUT_DIR / "stage12_21_freeze_and_regression_check_summary.json"
DOC_MD = DOC_DIR / "stage12_21_freeze_and_regression_check.md"

EXPECTED_STAGE1220E_SOURCE_HASH = "b2d7371786b58300ca68be5542372d5cf8aa2814678b9f451e09bdb8061aa138"

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def count_publish_calls(text: str) -> int:
    return len(re.findall(r"(?:->|\.)publish\s*\(", text))

def read_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

def run_cmd(name: str, cmd: str):
    log_path = OUT_DIR / f"stage12_21_{name}.log"
    p = subprocess.run(
        cmd,
        cwd=ROOT,
        shell=True,
        executable="/bin/bash",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    log_path.write_text(p.stdout, encoding="utf-8")
    return {
        "name": name,
        "cmd": cmd,
        "returncode": p.returncode,
        "log": str(log_path),
    }

fail_reasons = []
commands = []

stage1220e = read_json(STAGE1220E)
if not stage1220e:
    fail_reasons.append("missing Stage 12.20E summary")
elif stage1220e.get("pass") is not True:
    fail_reasons.append("Stage 12.20E did not pass")

source_text = ""
source_hash = None
source_checks = {
    "source_exists": SRC.exists(),
}
if not SRC.exists():
    fail_reasons.append("missing disabled_controller_node.cpp")
else:
    source_text = SRC.read_text(encoding="utf-8", errors="replace")
    source_hash = sha256_text(source_text)
    source_checks.update({
        "source_hash": source_hash,
        "source_hash_matches_stage1220e": source_hash == EXPECTED_STAGE1220E_SOURCE_HASH,
        "publish_call_count": count_publish_calls(source_text),
        "publish_call_count_is_1": count_publish_calls(source_text) == 1,
        "has_enable_continuous_torque_streaming": "enable_continuous_torque_streaming" in source_text,
        "has_confirm_continuous_torque_streaming": "confirm_continuous_torque_streaming" in source_text,
        "has_continuous_timer": "continuous_torque_streaming_timer_" in source_text,
        "has_four_flag_gate": "four_flag_gate" in source_text,
        "has_10hz_timer": "std::chrono::milliseconds(100)" in source_text,
        "has_max_ticks_30_bound": "max_ticks > 30" in source_text,
        "has_max_duration_3s_bound": "max_duration_sec > 3.0" in source_text,
        "has_repaired_helper_call_with_args": "publishBoundedZeroSafeTorqueOnceIfAllowed(enable_torque_publisher, confirm_torque_publisher_enable, true)" in source_text,
    })

    for key in [
        "source_hash_matches_stage1220e",
        "publish_call_count_is_1",
        "has_enable_continuous_torque_streaming",
        "has_confirm_continuous_torque_streaming",
        "has_continuous_timer",
        "has_four_flag_gate",
        "has_10hz_timer",
        "has_max_ticks_30_bound",
        "has_max_duration_3s_bound",
        "has_repaired_helper_call_with_args",
    ]:
        if source_checks.get(key) is not True:
            fail_reasons.append(f"source freeze check failed: {key}")

commands.append(run_cmd(
    "colcon_build",
    "source /opt/ros/jazzy/setup.bash && colcon build --packages-select robot_mpc_wbc_cpp_controller"
))

commands.append(run_cmd(
    "runtime_default_off",
    "bash scripts/stage12_20c_r1_runtime_default_off_regression.sh"
))

commands.append(run_cmd(
    "runtime_bounded_streaming_original",
    "bash scripts/stage12_20d_runtime_bounded_streaming_regression.sh"
))

commands.append(run_cmd(
    "runtime_bounded_streaming_reparse",
    "/usr/bin/python3 scripts/stage12_20d_r1_reparse_existing_evidence.py"
))

c_r1 = read_json(OUT_DIR / "stage12_20c_r1_runtime_default_off_regression_summary.json")
d_r1 = read_json(OUT_DIR / "stage12_20d_r1_reparse_existing_evidence_summary.json")

build_ok = commands[0]["returncode"] == 0
if not build_ok:
    fail_reasons.append("colcon build failed")

c_checks = {}
if not c_r1:
    fail_reasons.append("missing rerun Stage 12.20C-R1 summary")
else:
    c_checks = {
        "pass": c_r1.get("pass") is True,
        "node_seen": c_r1.get("node_seen") is True,
        "params_default_false": c_r1.get("params_default_false") is True,
        "echo_timeout": c_r1.get("echo_timeout") is True,
        "echo_has_data_false": c_r1.get("echo_has_data") is False,
        "torque_command_published_under_default_false_false": c_r1.get("torque_command_published_under_default_false") is False,
        "torque_enable_ready_false": c_r1.get("torque_enable_ready") is False,
        "torque_publisher_enabled_false": c_r1.get("torque_publisher_enabled") is False,
        "hardware_deployment_completed_false": c_r1.get("hardware_deployment_completed") is False,
        "control_law_changed_false": c_r1.get("control_law_changed") is False,
    }
    for key, ok in c_checks.items():
        if not ok:
            fail_reasons.append(f"default-off regression failed: {key}")

d_checks = {}
if not d_r1:
    fail_reasons.append("missing rerun Stage 12.20D-R1 summary")
else:
    d_checks = {
        "pass": d_r1.get("pass") is True,
        "node_seen": d_r1.get("node_seen") is True,
        "param_set_ok": d_r1.get("param_set_ok") is True,
        "stream_message_count_in_1_to_30": d_r1.get("stream_message_count_in_1_to_30") is True,
        "all_stream_payloads_length_12": d_r1.get("all_stream_payloads_length_12") is True,
        "all_stream_payload_values_finite": d_r1.get("all_stream_payload_values_finite") is True,
        "all_stream_payload_values_zero_safe": d_r1.get("all_stream_payload_values_zero_safe") is True,
        "final_flags_false": d_r1.get("final_flags_false") is True,
        "after_stop_echo_timeout": d_r1.get("after_stop_echo_timeout") is True,
        "after_stop_echo_has_data_false": d_r1.get("after_stop_echo_has_data") is False,
        "continuous_torque_streaming_completed": d_r1.get("continuous_torque_streaming_completed") is True,
        "torque_enable_ready_false": d_r1.get("torque_enable_ready") is False,
        "torque_publisher_enabled_false": d_r1.get("torque_publisher_enabled") is False,
        "hardware_deployment_completed_false": d_r1.get("hardware_deployment_completed") is False,
        "control_law_changed_false": d_r1.get("control_law_changed") is False,
    }
    for key, ok in d_checks.items():
        if not ok:
            fail_reasons.append(f"bounded streaming regression failed: {key}")

summary = {
    "stage": "12.21",
    "name": "freeze_and_regression_check_after_stage1220",
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "pass": len(fail_reasons) == 0,
    "fail_reasons": fail_reasons,
    "stage1220_completed_remains_true": len(fail_reasons) == 0,
    "continuous_torque_streaming_completed": len(fail_reasons) == 0,
    "torque_enable_ready": False,
    "torque_publisher_enabled": False,
    "hardware_deployment_completed": False,
    "control_law_changed": False,
    "baseline_type": "mixed_online_control_baseline",
    "source_checks": source_checks,
    "build_ok": build_ok,
    "default_off_regression_checks": c_checks,
    "bounded_streaming_regression_checks": d_checks,
    "commands": commands,
    "next_stage": "Stage 12.22 planning only for post-streaming safety freeze; no hardware deployment",
}

SUMMARY_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

md = [
    "# Stage 12.21 Freeze and Regression Check",
    "",
    f"- pass: `{summary['pass']}`",
    f"- fail_reasons: `{summary['fail_reasons']}`",
    f"- stage1220_completed_remains_true: `{summary['stage1220_completed_remains_true']}`",
    f"- continuous_torque_streaming_completed: `{summary['continuous_torque_streaming_completed']}`",
    f"- torque_enable_ready: `{summary['torque_enable_ready']}`",
    f"- torque_publisher_enabled: `{summary['torque_publisher_enabled']}`",
    f"- hardware_deployment_completed: `{summary['hardware_deployment_completed']}`",
    f"- control_law_changed: `{summary['control_law_changed']}`",
    "",
    "## Source freeze",
    "",
    f"- source_hash: `{source_checks.get('source_hash')}`",
    f"- source_hash_matches_stage1220e: `{source_checks.get('source_hash_matches_stage1220e')}`",
    f"- publish_call_count: `{source_checks.get('publish_call_count')}`",
    f"- has_four_flag_gate: `{source_checks.get('has_four_flag_gate')}`",
    f"- has_continuous_timer: `{source_checks.get('has_continuous_timer')}`",
    f"- has_10hz_timer: `{source_checks.get('has_10hz_timer')}`",
    "",
    "## Regression",
    "",
    f"- build_ok: `{build_ok}`",
    f"- default_off_pass: `{c_checks.get('pass')}`",
    f"- default_off_echo_timeout: `{c_checks.get('echo_timeout')}`",
    f"- default_off_echo_has_data_false: `{c_checks.get('echo_has_data_false')}`",
    f"- bounded_streaming_pass: `{d_checks.get('pass')}`",
    f"- stream_message_count_in_1_to_30: `{d_checks.get('stream_message_count_in_1_to_30')}`",
    f"- all_stream_payloads_length_12: `{d_checks.get('all_stream_payloads_length_12')}`",
    f"- all_stream_payload_values_finite: `{d_checks.get('all_stream_payload_values_finite')}`",
    f"- all_stream_payload_values_zero_safe: `{d_checks.get('all_stream_payload_values_zero_safe')}`",
    f"- final_flags_false: `{d_checks.get('final_flags_false')}`",
    f"- after_stop_echo_timeout: `{d_checks.get('after_stop_echo_timeout')}`",
    f"- after_stop_echo_has_data_false: `{d_checks.get('after_stop_echo_has_data_false')}`",
    "",
    "Safety boundary: Stage 12.21 is a freeze/regression check only. No hardware deployment, no torque enable readiness, no realtime-controller completion claim, no control-law change.",
    "",
    f"Next stage: `{summary['next_stage']}`",
]
DOC_MD.write_text("\n".join(md), encoding="utf-8")

if summary["pass"]:
    status_block = f"""

## Stage 12.21 Freeze and Regression Check

- timestamp: `{summary['timestamp']}`
- pass: `True`
- stage1220_completed_remains_true: `True`
- continuous_torque_streaming_completed: `True`
- source_hash: `{source_checks.get('source_hash')}`
- publish_call_count: `{source_checks.get('publish_call_count')}`
- build_ok: `True`
- default-off regression: `pass`
- bounded streaming regression: `pass`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- hardware_deployment_completed: `False`
- control_law_changed: `False`
- next_stage: `{summary['next_stage']}`
"""
    old = PROJECT_STATUS.read_text(encoding="utf-8", errors="replace") if PROJECT_STATUS.exists() else ""
    if "## Stage 12.21 Freeze and Regression Check" not in old:
        PROJECT_STATUS.write_text(old.rstrip() + status_block + "\n", encoding="utf-8")

print(json.dumps(summary, indent=2, ensure_ascii=False))
