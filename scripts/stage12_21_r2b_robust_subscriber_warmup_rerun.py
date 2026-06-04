#!/usr/bin/env /usr/bin/python3
from pathlib import Path
import hashlib
import json
import re
import subprocess
import time
from datetime import datetime

ROOT = Path.cwd()
OUT = ROOT / "results/logs_sample"
DOCS = ROOT / "docs"
OUT.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)

SUMMARY = OUT / "stage12_21_r2b_robust_subscriber_warmup_rerun_summary.json"
DOC = DOCS / "stage12_21_r2b_robust_subscriber_warmup_rerun.md"

SRC = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
EXPECTED_HASH = "b2d7371786b58300ca68be5542372d5cf8aa2814678b9f451e09bdb8061aa138"

NODE_LOG = OUT / "stage12_21_r2b_node.log"
CAPTURE_JSON = OUT / "stage12_21_r2b_capture.json"
CAPTURE_READY = OUT / "stage12_21_r2b_capture.ready"
CAPTURE_LOG = OUT / "stage12_21_r2b_capture.log"
AFTER_JSON = OUT / "stage12_21_r2b_after_stop_capture.json"
AFTER_READY = OUT / "stage12_21_r2b_after_stop_capture.ready"
AFTER_LOG = OUT / "stage12_21_r2b_after_stop_capture.log"
PARAM_SET_LOG = OUT / "stage12_21_r2b_param_set.log"
PARAM_FINAL_LOG = OUT / "stage12_21_r2b_param_final.log"
PROC_AFTER = OUT / "stage12_21_r2b_processes_after.log"

def bash(cmd, timeout=20):
    full = f"source /opt/ros/jazzy/setup.bash && source '{ROOT}/install/setup.bash' && {cmd}"
    return subprocess.run(
        ["bash", "-lc", full],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )

def cleanup():
    for pat in [
        "go1_disabled_controller_node",
        "stage12_21_r2b_capture.py",
        "stage12_21_r2b_joint_torque_capture",
        "ros2 topic echo.*/go1/joint_torque_cmd",
    ]:
        subprocess.run(["bash", "-lc", f"pkill -f '{pat}' || true"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def wait_file(path, timeout_sec):
    t0 = time.time()
    while time.time() - t0 < timeout_sec:
        if path.exists():
            return True
        time.sleep(0.1)
    return False

def sha256_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def append(path, text):
    with open(path, "a", encoding="utf-8") as f:
        f.write(text)
        if not text.endswith("\n"):
            f.write("\n")

def set_param(name, value):
    p = bash(f"ros2 param set /go1_disabled_controller_node {name} {value}", timeout=10)
    append(PARAM_SET_LOG, f"set {name}={value}")
    append(PARAM_SET_LOG, p.stdout)
    return p

def read_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))

result = {
    "stage": "12.21-R2B",
    "name": "robust_subscriber_warmup_bounded_streaming_rerun",
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "pass": False,
    "fail_reasons": [],
    "source_changed": False,
    "torque_enable_ready": False,
    "torque_publisher_enabled": False,
    "hardware_deployment_completed": False,
    "control_law_changed": False,
}

node_proc = None
cap_proc = None
after_proc = None

try:
    for p in [NODE_LOG, CAPTURE_JSON, CAPTURE_READY, CAPTURE_LOG, AFTER_JSON, AFTER_READY, AFTER_LOG, PARAM_SET_LOG, PARAM_FINAL_LOG, PROC_AFTER]:
        if p.exists():
            p.unlink()

    cleanup()
    time.sleep(2)
    bash("ros2 daemon stop || true; sleep 1; ros2 daemon start || true; sleep 2", timeout=20)

    source_text = SRC.read_text(encoding="utf-8", errors="replace")
    result["source_hash"] = sha256_text(source_text)
    result["source_hash_matches_stage1220e"] = result["source_hash"] == EXPECTED_HASH
    result["publish_call_count"] = len(re.findall(r"(?:->|\.)publish\s*\(", source_text))
    result["source_has_four_flag_gate"] = "four_flag_gate" in source_text
    result["source_has_continuous_timer"] = "continuous_torque_streaming_timer_" in source_text

    node_cmd = f"source /opt/ros/jazzy/setup.bash && source '{ROOT}/install/setup.bash' && ros2 run robot_mpc_wbc_cpp_controller go1_disabled_controller_node"
    node_log_f = open(NODE_LOG, "w", encoding="utf-8")
    node_proc = subprocess.Popen(["bash", "-lc", node_cmd], cwd=ROOT, stdout=node_log_f, stderr=subprocess.STDOUT, text=True)

    time.sleep(3)
    nodes = bash("ros2 node list", timeout=10).stdout
    result["node_seen"] = "/go1_disabled_controller_node" in nodes

    suffix = str(int(time.time()))
    cap_cmd = f"source /opt/ros/jazzy/setup.bash && source '{ROOT}/install/setup.bash' && /usr/bin/python3 scripts/stage12_21_r2b_capture.py '{CAPTURE_JSON}' '{CAPTURE_READY}' 14 '{suffix}'"
    cap_log_f = open(CAPTURE_LOG, "w", encoding="utf-8")
    cap_proc = subprocess.Popen(["bash", "-lc", cap_cmd], cwd=ROOT, stdout=cap_log_f, stderr=subprocess.STDOUT, text=True)

    result["subscriber_ready_before_activation"] = wait_file(CAPTURE_READY, 8)
    time.sleep(5)

    for name, value in [
        ("continuous_torque_streaming_max_ticks", "10"),
        ("continuous_torque_streaming_max_duration_sec", "1.5"),
        ("enable_torque_publisher", "true"),
        ("confirm_torque_publisher_enable", "true"),
        ("enable_continuous_torque_streaming", "true"),
        ("confirm_continuous_torque_streaming", "true"),
    ]:
        set_param(name, value)
        time.sleep(0.2)

    result["capture_returncode"] = cap_proc.wait(timeout=25)

    for name, value in [
        ("confirm_continuous_torque_streaming", "false"),
        ("enable_continuous_torque_streaming", "false"),
        ("confirm_torque_publisher_enable", "false"),
        ("enable_torque_publisher", "false"),
    ]:
        set_param(name, value)
        time.sleep(0.1)

    final_cmd = """
echo "enable_torque_publisher:"
ros2 param get /go1_disabled_controller_node enable_torque_publisher || true
echo
echo "confirm_torque_publisher_enable:"
ros2 param get /go1_disabled_controller_node confirm_torque_publisher_enable || true
echo
echo "enable_continuous_torque_streaming:"
ros2 param get /go1_disabled_controller_node enable_continuous_torque_streaming || true
echo
echo "confirm_continuous_torque_streaming:"
ros2 param get /go1_disabled_controller_node confirm_continuous_torque_streaming || true
"""
    final_params = bash(final_cmd, timeout=10).stdout
    PARAM_FINAL_LOG.write_text(final_params, encoding="utf-8")

    after_suffix = str(int(time.time()))
    after_cmd = f"source /opt/ros/jazzy/setup.bash && source '{ROOT}/install/setup.bash' && /usr/bin/python3 scripts/stage12_21_r2b_capture.py '{AFTER_JSON}' '{AFTER_READY}' 4 '{after_suffix}'"
    after_log_f = open(AFTER_LOG, "w", encoding="utf-8")
    after_proc = subprocess.Popen(["bash", "-lc", after_cmd], cwd=ROOT, stdout=after_log_f, stderr=subprocess.STDOUT, text=True)
    result["after_stop_subscriber_ready"] = wait_file(AFTER_READY, 5)
    result["after_stop_capture_returncode"] = after_proc.wait(timeout=10)

    cap = read_json(CAPTURE_JSON)
    after = read_json(AFTER_JSON)
    msgs = cap.get("messages", [])
    after_msgs = after.get("messages", [])

    result["capture_ok"] = cap.get("ok") is True
    result["stream_message_count"] = len(msgs)
    result["stream_payload_lengths"] = [m.get("length") for m in msgs]
    result["stream_message_count_in_1_to_30"] = 1 <= len(msgs) <= 30
    result["all_stream_payloads_length_12"] = len(msgs) > 0 and all(m.get("length") == 12 for m in msgs)
    result["all_stream_payload_values_finite"] = len(msgs) > 0 and all(m.get("all_finite") is True for m in msgs)
    result["all_stream_payload_values_zero_safe"] = len(msgs) > 0 and all(float(m.get("max_abs", 999.0)) <= 1e-12 for m in msgs)
    result["after_stop_message_count"] = len(after_msgs)
    result["after_stop_no_messages"] = len(after_msgs) == 0

    param_set_text = PARAM_SET_LOG.read_text(encoding="utf-8", errors="replace")
    result["param_success_count"] = len(re.findall(r"Set parameter successful", param_set_text, re.IGNORECASE))
    result["param_set_ok"] = result["param_success_count"] >= 10

    result["final_flags_false"] = all(re.search(p, final_params) for p in [
        r"enable_torque_publisher:\s*\nBoolean value is: False",
        r"confirm_torque_publisher_enable:\s*\nBoolean value is: False",
        r"enable_continuous_torque_streaming:\s*\nBoolean value is: False",
        r"confirm_continuous_torque_streaming:\s*\nBoolean value is: False",
    ])

except Exception as e:
    result["exception"] = repr(e)

finally:
    try:
        for name, value in [
            ("confirm_continuous_torque_streaming", "false"),
            ("enable_continuous_torque_streaming", "false"),
            ("confirm_torque_publisher_enable", "false"),
            ("enable_torque_publisher", "false"),
        ]:
            try:
                set_param(name, value)
            except Exception:
                pass
    except Exception:
        pass

    cleanup()

    try:
        if cap_proc and cap_proc.poll() is None:
            cap_proc.terminate()
    except Exception:
        pass
    try:
        if after_proc and after_proc.poll() is None:
            after_proc.terminate()
    except Exception:
        pass
    try:
        if node_proc and node_proc.poll() is None:
            node_proc.terminate()
            time.sleep(1)
            if node_proc.poll() is None:
                node_proc.kill()
    except Exception:
        pass

    time.sleep(1)
    proc = subprocess.run(
        ["bash", "-lc", "ps -u \"$USER\" -o pid=,ppid=,stat=,comm=,args= | grep -E 'go1_disabled_controller_node|stage12_21_r2b_capture|stage12_21_r2b_joint_torque_capture' | grep -v grep || true"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    PROC_AFTER.write_text(proc.stdout, encoding="utf-8")
    result["target_process_after_count"] = len([x for x in proc.stdout.splitlines() if x.strip()])

    checks = {
        "source_hash_matches_stage1220e": result.get("source_hash_matches_stage1220e") is True,
        "publish_call_count_is_1": result.get("publish_call_count") == 1,
        "source_has_four_flag_gate": result.get("source_has_four_flag_gate") is True,
        "source_has_continuous_timer": result.get("source_has_continuous_timer") is True,
        "node_seen": result.get("node_seen") is True,
        "subscriber_ready_before_activation": result.get("subscriber_ready_before_activation") is True,
        "capture_ok": result.get("capture_ok") is True,
        "param_set_ok": result.get("param_set_ok") is True,
        "stream_message_count_in_1_to_30": result.get("stream_message_count_in_1_to_30") is True,
        "all_stream_payloads_length_12": result.get("all_stream_payloads_length_12") is True,
        "all_stream_payload_values_finite": result.get("all_stream_payload_values_finite") is True,
        "all_stream_payload_values_zero_safe": result.get("all_stream_payload_values_zero_safe") is True,
        "final_flags_false": result.get("final_flags_false") is True,
        "after_stop_no_messages": result.get("after_stop_no_messages") is True,
        "target_process_after_count_is_0": result.get("target_process_after_count") == 0,
    }

    result["checks"] = checks
    result["fail_reasons"] = [k for k, v in checks.items() if not v]
    result["pass"] = len(result["fail_reasons"]) == 0
    result["continuous_torque_streaming_completed"] = result["pass"]

    result["logs"] = {
        "node_log": str(NODE_LOG),
        "capture_json": str(CAPTURE_JSON),
        "capture_log": str(CAPTURE_LOG),
        "after_stop_capture_json": str(AFTER_JSON),
        "after_stop_capture_log": str(AFTER_LOG),
        "param_set_log": str(PARAM_SET_LOG),
        "param_final_log": str(PARAM_FINAL_LOG),
        "processes_after": str(PROC_AFTER),
    }

    SUMMARY.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    md = [
        "# Stage 12.21-R2B Robust Subscriber-Warmup Bounded Streaming Rerun",
        "",
        f"- pass: `{result['pass']}`",
        f"- fail_reasons: `{result['fail_reasons']}`",
        f"- source_changed: `{result['source_changed']}`",
        f"- source_hash_matches_stage1220e: `{result.get('source_hash_matches_stage1220e')}`",
        f"- publish_call_count: `{result.get('publish_call_count')}`",
        f"- node_seen: `{result.get('node_seen')}`",
        f"- subscriber_ready_before_activation: `{result.get('subscriber_ready_before_activation')}`",
        f"- capture_ok: `{result.get('capture_ok')}`",
        f"- param_set_ok: `{result.get('param_set_ok')}`",
        f"- stream_message_count: `{result.get('stream_message_count')}`",
        f"- stream_message_count_in_1_to_30: `{result.get('stream_message_count_in_1_to_30')}`",
        f"- all_stream_payloads_length_12: `{result.get('all_stream_payloads_length_12')}`",
        f"- all_stream_payload_values_finite: `{result.get('all_stream_payload_values_finite')}`",
        f"- all_stream_payload_values_zero_safe: `{result.get('all_stream_payload_values_zero_safe')}`",
        f"- final_flags_false: `{result.get('final_flags_false')}`",
        f"- after_stop_no_messages: `{result.get('after_stop_no_messages')}`",
        f"- target_process_after_count: `{result.get('target_process_after_count')}`",
        f"- continuous_torque_streaming_completed: `{result.get('continuous_torque_streaming_completed')}`",
        "",
        "Safety boundary: no source change; bounded zero/safe streaming regression only; no hardware deployment; no control-law change.",
    ]
    DOC.write_text("\n".join(md), encoding="utf-8")

    print(json.dumps(result, indent=2, ensure_ascii=False))
