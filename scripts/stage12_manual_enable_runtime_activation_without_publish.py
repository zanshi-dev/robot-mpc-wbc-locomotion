#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import os
import re
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE126_SUMMARY = LOG_DIR / "stage12_manual_enable_activation_design_summary.csv"
STAGE126_GATE = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage126.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
SAFETY_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

SUMMARY_PATH = LOG_DIR / "stage12_manual_enable_runtime_activation_without_publish_summary.csv"
LOG_PATH = LOG_DIR / "stage12_manual_enable_runtime_activation_without_publish_log.csv"
OBS_PATH = LOG_DIR / "stage12_manual_enable_runtime_activation_topic_observations.csv"
PARAM_OBS_PATH = LOG_DIR / "stage12_manual_enable_runtime_activation_param_observations.csv"
ECHO_STDOUT = LOG_DIR / "stage12_manual_enable_runtime_activation_topic_echo_stdout.txt"
ECHO_STDERR = LOG_DIR / "stage12_manual_enable_runtime_activation_topic_echo_stderr.txt"
SAFETY_GATE_PATH = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage127.csv"
DOC_PATH = ROOT / "docs/STAGE12_MANUAL_ENABLE_RUNTIME_ACTIVATION_WITHOUT_PUBLISH.md"

BUILD_STDOUT = LOG_DIR / "stage12_manual_enable_runtime_activation_build_stdout.txt"
BUILD_STDERR = LOG_DIR / "stage12_manual_enable_runtime_activation_build_stderr.txt"
BRIDGE_STDOUT = LOG_DIR / "stage12_manual_enable_runtime_activation_bridge_stdout.txt"
BRIDGE_STDERR = LOG_DIR / "stage12_manual_enable_runtime_activation_bridge_stderr.txt"
CONTROLLER_STDOUT = LOG_DIR / "stage12_manual_enable_runtime_activation_controller_stdout.txt"
CONTROLLER_STDERR = LOG_DIR / "stage12_manual_enable_runtime_activation_controller_stderr.txt"

BRIDGE_PACKAGE = "robot_mpc_wbc_bridge"
BRIDGE_EXECUTABLE = "mujoco_bridge_node"
CONTROLLER_PACKAGE = "robot_mpc_wbc_cpp_controller"
CONTROLLER_EXECUTABLE = "go1_disabled_controller_node"

NODE_NAME = "/go1_disabled_controller_node"
TORQUE_TOPIC = "/go1/joint_torque_cmd"
PARAM_ENABLE = "enable_torque_publisher"
PARAM_CONFIRM = "confirm_torque_publisher_enable"


def load_summary(path: Path):
    metrics = {}
    if not path.exists():
        return metrics
    with path.open(newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return metrics
    header = [x.strip() for x in rows[0]]
    if len(header) >= 2 and header[0] == "metric" and header[1] == "value":
        for row in rows[1:]:
            if len(row) >= 2:
                metrics[row[0].strip()] = row[1].strip()
        return metrics
    for row in rows[1:]:
        if any(x.strip() for x in row):
            for k, v in zip(header, row):
                metrics[k.strip()] = v.strip()
            return metrics
    return metrics


def load_dicts(path: Path):
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def as_bool(x):
    return str(x).strip().lower() in {"true", "1", "yes"}


def sha256_file(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def add_check(rows, check, value, expected, passed, detail=""):
    rows.append({
        "check": check,
        "value": str(value),
        "expected": str(expected),
        "pass": bool(passed),
        "detail": detail,
    })


def bash_cmd(cmd, timeout=20):
    full = (
        "source /opt/ros/jazzy/setup.bash && "
        "source ros2_ws/install/setup.bash && "
        f"{cmd}"
    )
    return subprocess.run(
        ["/bin/bash", "-lc", full],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def build_packages():
    cmd = (
        "source /opt/ros/jazzy/setup.bash && "
        "cd ros2_ws && "
        "colcon build --packages-select robot_mpc_wbc_bridge robot_mpc_wbc_cpp_controller --symlink-install"
    )
    proc = subprocess.run(
        ["/bin/bash", "-lc", cmd],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        timeout=120,
    )
    BUILD_STDOUT.write_text(proc.stdout)
    BUILD_STDERR.write_text(proc.stderr)
    return proc.returncode


def start_node(package_name, executable_name):
    cmd = (
        "source /opt/ros/jazzy/setup.bash && "
        "source ros2_ws/install/setup.bash && "
        f"exec ros2 run {package_name} {executable_name}"
    )
    return subprocess.Popen(
        ["/bin/bash", "-lc", cmd],
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )


def stop_process(proc, stdout_path, stderr_path):
    if proc is None:
        return
    try:
        if proc.poll() is None:
            os.killpg(os.getpgid(proc.pid), signal.SIGINT)
            time.sleep(1.0)
        if proc.poll() is None:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            time.sleep(1.0)
        out, err = proc.communicate(timeout=5)
    except Exception:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            pass
        try:
            out, err = proc.communicate(timeout=5)
        except Exception:
            out, err = "", ""
    stdout_path.write_text(out or "")
    stderr_path.write_text(err or "")


def topic_info(topic):
    proc = bash_cmd(f"ros2 topic info {topic}", timeout=10)
    stdout = proc.stdout
    pub_count = None
    sub_count = None

    m = re.search(r"Publisher count:\s*(\d+)", stdout)
    if m:
        pub_count = int(m.group(1))

    m = re.search(r"Subscription count:\s*(\d+)", stdout)
    if m:
        sub_count = int(m.group(1))

    return proc.returncode, stdout, proc.stderr, pub_count, sub_count


def get_param_bool(param_name):
    proc = bash_cmd(f"ros2 param get {NODE_NAME} {param_name}", timeout=10)
    text = (proc.stdout or "").strip().lower()
    if "true" in text:
        value = True
    elif "false" in text:
        value = False
    else:
        value = None
    return proc.returncode, value, proc.stdout, proc.stderr


def set_param_bool(param_name, value):
    literal = "true" if value else "false"
    return bash_cmd(f"ros2 param set {NODE_NAME} {param_name} {literal}", timeout=10)


def echo_once_no_message_expected():
    cmd = (
        "source /opt/ros/jazzy/setup.bash && "
        "source ros2_ws/install/setup.bash && "
        f"timeout 3s ros2 topic echo --once {TORQUE_TOPIC}"
    )
    proc = subprocess.run(
        ["/bin/bash", "-lc", cmd],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        timeout=8,
    )
    ECHO_STDOUT.write_text(proc.stdout or "")
    ECHO_STDERR.write_text(proc.stderr or "")
    no_message_observed = proc.returncode == 124 and not (proc.stdout or "").strip()
    return proc.returncode, no_message_observed, proc.stdout, proc.stderr


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    checks = []

    s126 = load_summary(STAGE126_SUMMARY)
    stage126_pass = as_bool(s126.get("pass", "False"))
    design_complete = as_bool(s126.get("manual_enable_activation_design_complete", "False"))
    stage126_source_unchanged = as_bool(s126.get("source_unchanged_by_stage126", "False"))
    stage126_source_has_publish_call = as_bool(s126.get("source_has_publish_call", "True"))
    stage126_active_path = as_bool(s126.get("active_ros_publisher_path_exists", "False"))
    stage126_manual_active = as_bool(s126.get("manual_enable_active", "True"))
    stage126_torque_ready = as_bool(s126.get("torque_enable_ready", "True"))
    stage126_torque_enabled = as_bool(s126.get("torque_publisher_enabled", "True"))
    stage126_control_changed = as_bool(s126.get("control_law_changed", "True"))

    add_check(checks, "stage126_summary_exists", STAGE126_SUMMARY.exists(), True, STAGE126_SUMMARY.exists(), str(STAGE126_SUMMARY))
    add_check(checks, "stage126_pass", stage126_pass, True, stage126_pass)
    add_check(checks, "stage126_manual_enable_activation_design_complete", design_complete, True, design_complete)
    add_check(checks, "stage126_source_unchanged_by_stage126", stage126_source_unchanged, True, stage126_source_unchanged)
    add_check(checks, "stage126_source_has_publish_call", stage126_source_has_publish_call, False, not stage126_source_has_publish_call)
    add_check(checks, "stage126_active_ros_publisher_path_exists", stage126_active_path, True, stage126_active_path)
    add_check(checks, "stage126_manual_enable_active", stage126_manual_active, False, not stage126_manual_active)
    add_check(checks, "stage126_torque_enable_ready", stage126_torque_ready, False, not stage126_torque_ready)
    add_check(checks, "stage126_torque_publisher_enabled", stage126_torque_enabled, False, not stage126_torque_enabled)
    add_check(checks, "stage126_control_law_changed", stage126_control_changed, False, not stage126_control_changed)

    gate_rows_in = load_dicts(STAGE126_GATE)
    gate_status_in = {
        row.get("gate", ""): as_bool(row.get("current_status", "False"))
        for row in gate_rows_in
    }

    add_check(checks, "stage126_gate_exists", STAGE126_GATE.exists(), True, STAGE126_GATE.exists(), str(STAGE126_GATE))
    add_check(checks, "stage126_gate_g3_true", gate_status_in.get("G3", False), True, gate_status_in.get("G3", False) is True)
    add_check(checks, "stage126_gate_g8_false", gate_status_in.get("G8", True), False, gate_status_in.get("G8", True) is False)
    add_check(checks, "stage126_gate_g9_true", gate_status_in.get("G9", False), True, gate_status_in.get("G9", False) is True)
    add_check(checks, "stage126_gate_g24_true", gate_status_in.get("G24", False), True, gate_status_in.get("G24", False) is True)

    source_hash_before = sha256_file(CPP_SOURCE) if CPP_SOURCE.exists() else ""
    cpp_text = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""

    source_has_create_publisher = "create_publisher<std_msgs::msg::Float64MultiArray>" in cpp_text
    source_has_publish_call = ".publish(" in cpp_text or "->publish(" in cpp_text
    source_references_torque_topic = TORQUE_TOPIC in cpp_text
    source_has_active_member = "active_torque_cmd_publisher_" in cpp_text
    source_has_stage124_marker = (
        "kStage124PublisherConstructionImplemented" in cpp_text and
        "kStage124PublishCallImplemented = false" in cpp_text
    )
    source_declares_enable_param = 'declare_parameter<bool>("enable_torque_publisher", false)' in cpp_text
    source_declares_confirm_param = 'declare_parameter<bool>("confirm_torque_publisher_enable", false)' in cpp_text
    source_uses_safety = "clampTorqueCommand" in cpp_text and "allInputsFresh" in cpp_text and "watchdogFallbackZeroTorque" in cpp_text

    safety_text = SAFETY_HEADER.read_text(errors="replace") if SAFETY_HEADER.exists() else ""
    zero_text = ZERO_HEADER.read_text(errors="replace") if ZERO_HEADER.exists() else ""
    safety_header_has_clamp_watchdog = "clampTorqueCommand" in safety_text and "allInputsFresh" in safety_text and "watchdogFallbackZeroTorque" in safety_text
    zero_header_declares_12 = "kGo1NumActuatedJoints = 12" in zero_text

    add_check(checks, "cpp_source_exists", CPP_SOURCE.exists(), True, CPP_SOURCE.exists(), str(CPP_SOURCE))
    add_check(checks, "source_has_create_publisher", source_has_create_publisher, True, source_has_create_publisher)
    add_check(checks, "source_has_no_publish_call", source_has_publish_call, False, not source_has_publish_call)
    add_check(checks, "source_references_torque_topic", source_references_torque_topic, True, source_references_torque_topic)
    add_check(checks, "source_has_active_publisher_member", source_has_active_member, True, source_has_active_member)
    add_check(checks, "source_has_stage124_marker", source_has_stage124_marker, True, source_has_stage124_marker)
    add_check(checks, "source_declares_enable_param_default_false", source_declares_enable_param, True, source_declares_enable_param)
    add_check(checks, "source_declares_confirm_param_default_false", source_declares_confirm_param, True, source_declares_confirm_param)
    add_check(checks, "source_uses_safety_utilities", source_uses_safety, True, source_uses_safety)
    add_check(checks, "safety_header_has_clamp_watchdog", safety_header_has_clamp_watchdog, True, safety_header_has_clamp_watchdog)
    add_check(checks, "zero_header_declares_12", zero_header_declares_12, True, zero_header_declares_12)

    build_rc = build_packages()
    add_check(checks, "colcon_build_returncode", build_rc, 0, build_rc == 0)

    bridge_proc = None
    controller_proc = None

    param_rows = []
    topic_rows = []

    initial_enable_false = False
    initial_confirm_false = False
    activated_enable_true = False
    activated_confirm_true = False
    reverted_enable_false = False
    reverted_confirm_false = False
    no_message_observed_during_activation = False
    echo_returncode = None
    controller_alive_after_activation = False

    try:
        bridge_proc = start_node(BRIDGE_PACKAGE, BRIDGE_EXECUTABLE)
        time.sleep(3.0)
        bridge_alive = bridge_proc.poll() is None
        add_check(checks, "bridge_alive_after_startup", bridge_alive, True, bridge_alive)

        controller_proc = start_node(CONTROLLER_PACKAGE, CONTROLLER_EXECUTABLE)
        time.sleep(4.0)
        controller_alive = controller_proc.poll() is None
        add_check(checks, "disabled_controller_alive_after_startup", controller_alive, True, controller_alive)

        rc, value, out, err = get_param_bool(PARAM_ENABLE)
        param_rows.append({"phase": "initial", "param": PARAM_ENABLE, "returncode": rc, "value": value, "stdout": out.strip(), "stderr": err.strip()})
        initial_enable_false = rc == 0 and value is False

        rc, value, out, err = get_param_bool(PARAM_CONFIRM)
        param_rows.append({"phase": "initial", "param": PARAM_CONFIRM, "returncode": rc, "value": value, "stdout": out.strip(), "stderr": err.strip()})
        initial_confirm_false = rc == 0 and value is False

        for i in range(2):
            info_rc, info_out, info_err, pub_count, sub_count = topic_info(TORQUE_TOPIC)
            topic_rows.append({
                "phase": "initial",
                "sample_index": i,
                "topic": TORQUE_TOPIC,
                "topic_info_returncode": info_rc,
                "publisher_count": "" if pub_count is None else pub_count,
                "subscription_count": "" if sub_count is None else sub_count,
                "publisher_count_positive": isinstance(pub_count, int) and pub_count >= 1,
                "subscription_count_positive": isinstance(sub_count, int) and sub_count >= 1,
            })
            time.sleep(0.5)

        set_enable = set_param_bool(PARAM_ENABLE, True)
        param_rows.append({"phase": "set_true", "param": PARAM_ENABLE, "returncode": set_enable.returncode, "value": "", "stdout": set_enable.stdout.strip(), "stderr": set_enable.stderr.strip()})

        set_confirm = set_param_bool(PARAM_CONFIRM, True)
        param_rows.append({"phase": "set_true", "param": PARAM_CONFIRM, "returncode": set_confirm.returncode, "value": "", "stdout": set_confirm.stdout.strip(), "stderr": set_confirm.stderr.strip()})

        time.sleep(1.0)

        rc, value, out, err = get_param_bool(PARAM_ENABLE)
        param_rows.append({"phase": "activated", "param": PARAM_ENABLE, "returncode": rc, "value": value, "stdout": out.strip(), "stderr": err.strip()})
        activated_enable_true = rc == 0 and value is True

        rc, value, out, err = get_param_bool(PARAM_CONFIRM)
        param_rows.append({"phase": "activated", "param": PARAM_CONFIRM, "returncode": rc, "value": value, "stdout": out.strip(), "stderr": err.strip()})
        activated_confirm_true = rc == 0 and value is True

        for i in range(4):
            info_rc, info_out, info_err, pub_count, sub_count = topic_info(TORQUE_TOPIC)
            topic_rows.append({
                "phase": "activated",
                "sample_index": i,
                "topic": TORQUE_TOPIC,
                "topic_info_returncode": info_rc,
                "publisher_count": "" if pub_count is None else pub_count,
                "subscription_count": "" if sub_count is None else sub_count,
                "publisher_count_positive": isinstance(pub_count, int) and pub_count >= 1,
                "subscription_count_positive": isinstance(sub_count, int) and sub_count >= 1,
            })
            time.sleep(0.5)

        echo_returncode, no_message_observed_during_activation, echo_out, echo_err = echo_once_no_message_expected()

        revert_confirm = set_param_bool(PARAM_CONFIRM, False)
        param_rows.append({"phase": "revert_false", "param": PARAM_CONFIRM, "returncode": revert_confirm.returncode, "value": "", "stdout": revert_confirm.stdout.strip(), "stderr": revert_confirm.stderr.strip()})

        revert_enable = set_param_bool(PARAM_ENABLE, False)
        param_rows.append({"phase": "revert_false", "param": PARAM_ENABLE, "returncode": revert_enable.returncode, "value": "", "stdout": revert_enable.stdout.strip(), "stderr": revert_enable.stderr.strip()})

        time.sleep(0.5)

        rc, value, out, err = get_param_bool(PARAM_ENABLE)
        param_rows.append({"phase": "reverted", "param": PARAM_ENABLE, "returncode": rc, "value": value, "stdout": out.strip(), "stderr": err.strip()})
        reverted_enable_false = rc == 0 and value is False

        rc, value, out, err = get_param_bool(PARAM_CONFIRM)
        param_rows.append({"phase": "reverted", "param": PARAM_CONFIRM, "returncode": rc, "value": value, "stdout": out.strip(), "stderr": err.strip()})
        reverted_confirm_false = rc == 0 and value is False

        controller_alive_after_activation = controller_proc.poll() is None

    finally:
        try:
            set_param_bool(PARAM_CONFIRM, False)
            set_param_bool(PARAM_ENABLE, False)
        except Exception:
            pass

        stop_process(controller_proc, CONTROLLER_STDOUT, CONTROLLER_STDERR)
        stop_process(bridge_proc, BRIDGE_STDOUT, BRIDGE_STDERR)

    with PARAM_OBS_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["phase", "param", "returncode", "value", "stdout", "stderr"],
        )
        writer.writeheader()
        writer.writerows(param_rows)

    with OBS_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "phase",
                "sample_index",
                "topic",
                "topic_info_returncode",
                "publisher_count",
                "subscription_count",
                "publisher_count_positive",
                "subscription_count_positive",
            ],
        )
        writer.writeheader()
        writer.writerows(topic_rows)

    topic_info_all_returncode_zero = all(row["topic_info_returncode"] == 0 for row in topic_rows)
    torque_publishers_positive_all_samples = all(row["publisher_count_positive"] for row in topic_rows)
    torque_subscribers_positive_all_samples = all(row["subscription_count_positive"] for row in topic_rows)
    runtime_topic_sample_count = len(topic_rows)

    add_check(checks, "initial_enable_param_false", initial_enable_false, True, initial_enable_false)
    add_check(checks, "initial_confirm_param_false", initial_confirm_false, True, initial_confirm_false)
    add_check(checks, "activated_enable_param_true", activated_enable_true, True, activated_enable_true)
    add_check(checks, "activated_confirm_param_true", activated_confirm_true, True, activated_confirm_true)
    add_check(checks, "reverted_enable_param_false", reverted_enable_false, True, reverted_enable_false)
    add_check(checks, "reverted_confirm_param_false", reverted_confirm_false, True, reverted_confirm_false)
    add_check(checks, "runtime_topic_sample_count", runtime_topic_sample_count, 6, runtime_topic_sample_count == 6)
    add_check(checks, "topic_info_all_returncode_zero", topic_info_all_returncode_zero, True, topic_info_all_returncode_zero)
    add_check(checks, "torque_publishers_positive_all_samples", torque_publishers_positive_all_samples, True, torque_publishers_positive_all_samples)
    add_check(checks, "torque_subscribers_positive_all_samples", torque_subscribers_positive_all_samples, True, torque_subscribers_positive_all_samples)
    add_check(checks, "topic_echo_returncode_timeout", echo_returncode, 124, echo_returncode == 124)
    add_check(checks, "no_message_observed_during_activation", no_message_observed_during_activation, True, no_message_observed_during_activation)
    add_check(checks, "controller_alive_after_activation", controller_alive_after_activation, True, controller_alive_after_activation)

    source_hash_after = sha256_file(CPP_SOURCE) if CPP_SOURCE.exists() else ""
    source_unchanged_by_stage127 = source_hash_before == source_hash_after

    add_check(checks, "source_unchanged_by_stage127", source_unchanged_by_stage127, True, source_unchanged_by_stage127)

    manual_enable_active_during_test = activated_enable_true and activated_confirm_true
    manual_enable_reverted_false = reverted_enable_false and reverted_confirm_false
    active_ros_publisher_path_exists = torque_publishers_positive_all_samples
    torque_command_published_by_stage127 = not no_message_observed_during_activation
    torque_enable_ready = False
    torque_publisher_enabled = False
    control_law_changed = False

    manual_enable_runtime_activation_without_publish_passed = (
        stage126_pass and
        design_complete and
        source_has_create_publisher and
        not source_has_publish_call and
        active_ros_publisher_path_exists and
        initial_enable_false and
        initial_confirm_false and
        manual_enable_active_during_test and
        manual_enable_reverted_false and
        no_message_observed_during_activation and
        source_unchanged_by_stage127 and
        controller_alive_after_activation
    )

    gate_rows_out = []
    for row in gate_rows_in:
        gate_rows_out.append(row)

    gate_rows_out.append({
        "gate": "G25",
        "name": "Manual enable runtime activation without publish passed",
        "required_before_torque_publish": True,
        "current_status": manual_enable_runtime_activation_without_publish_passed,
        "evidence": str(LOG_PATH.relative_to(ROOT)),
    })

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(gate_rows_out)

    add_check(checks, "manual_enable_active_during_test", manual_enable_active_during_test, True, manual_enable_active_during_test)
    add_check(checks, "manual_enable_reverted_false", manual_enable_reverted_false, True, manual_enable_reverted_false)
    add_check(checks, "active_ros_publisher_path_exists", active_ros_publisher_path_exists, True, active_ros_publisher_path_exists)
    add_check(checks, "manual_enable_runtime_activation_without_publish_passed", manual_enable_runtime_activation_without_publish_passed, True, manual_enable_runtime_activation_without_publish_passed)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)
    add_check(checks, "torque_publisher_enabled", torque_publisher_enabled, False, not torque_publisher_enabled)
    add_check(checks, "torque_command_published_by_stage127", torque_command_published_by_stage127, False, not torque_command_published_by_stage127)
    add_check(checks, "control_law_changed", control_law_changed, False, not control_law_changed)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    DOC_PATH.write_text(f"""# Stage 12.7 Manual Enable Runtime Activation Without Publish

## 一、结论

Stage 12.7 执行 runtime-only manual enable activation test，但不实现 publish call。

本阶段行为：

- runtime 设置 enable_torque_publisher=true；
- runtime 设置 confirm_torque_publisher_enable=true；
- 确认 active ROS publisher path 仍存在；
- 确认 C++ source 未改变；
- 确认 source 仍无 publish call；
- 用 ros2 topic echo --once 超时验证没有 torque message；
- 测试结束后 fail-closed revert 两个参数为 false。

## 二、Source guard

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: {source_has_create_publisher}
- source_has_publish_call: {source_has_publish_call}
- source_references_torque_topic: {source_references_torque_topic}
- source_unchanged_by_stage127: {source_unchanged_by_stage127}

## 三、Runtime manual activation

Parameter observation CSV:

    results/logs_sample/stage12_manual_enable_runtime_activation_param_observations.csv

Topic observation CSV:

    results/logs_sample/stage12_manual_enable_runtime_activation_topic_observations.csv

Results:

- initial_enable_param_false: {initial_enable_false}
- initial_confirm_param_false: {initial_confirm_false}
- activated_enable_param_true: {activated_enable_true}
- activated_confirm_param_true: {activated_confirm_true}
- reverted_enable_param_false: {reverted_enable_false}
- reverted_confirm_param_false: {reverted_confirm_false}
- torque_publishers_positive_all_samples: {torque_publishers_positive_all_samples}
- no_message_observed_during_activation: {no_message_observed_during_activation}

## 四、Safety gate after Stage 12.7

新增：

- G25 manual enable runtime activation without publish passed: {manual_enable_runtime_activation_without_publish_passed}

Runtime during test:

- manual_enable_active_during_test: {manual_enable_active_during_test}
- active_ros_publisher_path_exists: {active_ros_publisher_path_exists}

After test:

- manual_enable_reverted_false: {manual_enable_reverted_false}
- torque_enable_ready: {torque_enable_ready}
- torque_publisher_enabled: {torque_publisher_enabled}
- torque_command_published_by_stage127: {torque_command_published_by_stage127}

## 五、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.7 没有完成：

- publish call；
- torque command publishing；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。
""")

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 12.7"])
        writer.writerow(["test_name", "manual_enable_runtime_activation_without_publish"])
        writer.writerow(["stage126_pass", stage126_pass])
        writer.writerow(["stage126_manual_enable_activation_design_complete", design_complete])
        writer.writerow(["source_has_create_publisher", source_has_create_publisher])
        writer.writerow(["source_has_publish_call", source_has_publish_call])
        writer.writerow(["source_references_torque_topic", source_references_torque_topic])
        writer.writerow(["source_has_active_publisher_member", source_has_active_member])
        writer.writerow(["source_has_stage124_marker", source_has_stage124_marker])
        writer.writerow(["source_unchanged_by_stage127", source_unchanged_by_stage127])
        writer.writerow(["colcon_build_returncode", build_rc])
        writer.writerow(["initial_enable_param_false", initial_enable_false])
        writer.writerow(["initial_confirm_param_false", initial_confirm_false])
        writer.writerow(["activated_enable_param_true", activated_enable_true])
        writer.writerow(["activated_confirm_param_true", activated_confirm_true])
        writer.writerow(["manual_enable_active_during_test", manual_enable_active_during_test])
        writer.writerow(["reverted_enable_param_false", reverted_enable_false])
        writer.writerow(["reverted_confirm_param_false", reverted_confirm_false])
        writer.writerow(["manual_enable_reverted_false", manual_enable_reverted_false])
        writer.writerow(["runtime_topic_sample_count", runtime_topic_sample_count])
        writer.writerow(["topic_info_all_returncode_zero", topic_info_all_returncode_zero])
        writer.writerow(["torque_publishers_positive_all_samples", torque_publishers_positive_all_samples])
        writer.writerow(["torque_subscribers_positive_all_samples", torque_subscribers_positive_all_samples])
        writer.writerow(["topic_echo_returncode", echo_returncode])
        writer.writerow(["no_message_observed_during_activation", no_message_observed_during_activation])
        writer.writerow(["controller_alive_after_activation", controller_alive_after_activation])
        writer.writerow(["manual_enable_runtime_activation_without_publish_passed", manual_enable_runtime_activation_without_publish_passed])
        writer.writerow(["active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g3_no_publish_call", not source_has_publish_call])
        writer.writerow(["g8_manual_enable_active_during_test", manual_enable_active_during_test])
        writer.writerow(["g9_active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g24_manual_enable_activation_design_exists", gate_status_in.get("G24", False)])
        writer.writerow(["g25_manual_enable_runtime_activation_without_publish_passed", manual_enable_runtime_activation_without_publish_passed])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", control_law_changed])
        writer.writerow(["torque_publisher_enabled", torque_publisher_enabled])
        writer.writerow(["torque_command_published_by_stage127", torque_command_published_by_stage127])
        writer.writerow(["stage12_scope", "manual_enable_runtime_activation_without_publish_call"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["ros2_cpp_realtime_controller_completed", False])
        writer.writerow(["pure_wbc_locomotion_completed", False])
        writer.writerow(["ekf_completed", False])
        writer.writerow(["full_3d_centroidal_mpc_completed", False])
        writer.writerow(["num_checks", len(checks)])
        writer.writerow(["num_failed_checks", sum(1 for row in checks if not row["pass"])])
        writer.writerow(["pass", all_pass])
        writer.writerow(["log_csv", str(LOG_PATH.relative_to(ROOT))])
        writer.writerow(["param_observations_csv", str(PARAM_OBS_PATH.relative_to(ROOT))])
        writer.writerow(["topic_observations_csv", str(OBS_PATH.relative_to(ROOT))])
        writer.writerow(["topic_echo_stdout", str(ECHO_STDOUT.relative_to(ROOT))])
        writer.writerow(["topic_echo_stderr", str(ECHO_STDERR.relative_to(ROOT))])
        writer.writerow(["safety_gate_csv", str(SAFETY_GATE_PATH.relative_to(ROOT))])
        writer.writerow(["summary_csv", str(SUMMARY_PATH.relative_to(ROOT))])
        writer.writerow(["build_stdout", str(BUILD_STDOUT.relative_to(ROOT))])
        writer.writerow(["build_stderr", str(BUILD_STDERR.relative_to(ROOT))])
        writer.writerow(["bridge_stdout", str(BRIDGE_STDOUT.relative_to(ROOT))])
        writer.writerow(["bridge_stderr", str(BRIDGE_STDERR.relative_to(ROOT))])
        writer.writerow(["controller_stdout", str(CONTROLLER_STDOUT.relative_to(ROOT))])
        writer.writerow(["controller_stderr", str(CONTROLLER_STDERR.relative_to(ROOT))])
        writer.writerow(["doc", str(DOC_PATH.relative_to(ROOT))])

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 12.7 Manual Enable Runtime Activation Without Publish

Stage 12.7 完成 runtime manual enable activation without publish call。

- Script: `scripts/stage12_manual_enable_runtime_activation_without_publish.py`
- Param observations: `results/logs_sample/stage12_manual_enable_runtime_activation_param_observations.csv`
- Topic observations: `results/logs_sample/stage12_manual_enable_runtime_activation_topic_observations.csv`
- Summary: `results/logs_sample/stage12_manual_enable_runtime_activation_without_publish_summary.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage127.csv`
- Docs: `docs/STAGE12_MANUAL_ENABLE_RUNTIME_ACTIVATION_WITHOUT_PUBLISH.md`
- pass: `{all_pass}`
- manual_enable_runtime_activation_without_publish_passed: `{manual_enable_runtime_activation_without_publish_passed}`
- manual_enable_active_during_test: `{manual_enable_active_during_test}`
- manual_enable_reverted_false: `{manual_enable_reverted_false}`
- active_ros_publisher_path_exists: `{active_ros_publisher_path_exists}`
- no_message_observed_during_activation: `{no_message_observed_during_activation}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `{torque_publisher_enabled}`
- torque_command_published_by_stage127: `{torque_command_published_by_stage127}`
- control_law_changed: `{control_law_changed}`

Stage 12.7 只激活 runtime manual flags 并回退，不加入 publish call，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 12.7 Manual Enable Runtime Activation Without Publish"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 12.7] manual enable runtime activation without publish")
    print(f"pass={all_pass}")
    print(f"stage126_pass={stage126_pass}")
    print(f"manual_enable_runtime_activation_without_publish_passed={manual_enable_runtime_activation_without_publish_passed}")
    print(f"manual_enable_active_during_test={manual_enable_active_during_test}")
    print(f"manual_enable_reverted_false={manual_enable_reverted_false}")
    print(f"active_ros_publisher_path_exists={active_ros_publisher_path_exists}")
    print(f"source_has_publish_call={source_has_publish_call}")
    print(f"no_message_observed_during_activation={no_message_observed_during_activation}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print(f"control_law_changed={control_law_changed}")
    print(f"torque_publisher_enabled={torque_publisher_enabled}")
    print(f"torque_command_published_by_stage127={torque_command_published_by_stage127}")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
    print(f"param_observations_csv={PARAM_OBS_PATH.relative_to(ROOT)}")
    print(f"topic_observations_csv={OBS_PATH.relative_to(ROOT)}")
    print(f"safety_gate_csv={SAFETY_GATE_PATH.relative_to(ROOT)}")
    print(f"summary_csv={SUMMARY_PATH.relative_to(ROOT)}")
    print(f"doc={DOC_PATH.relative_to(ROOT)}")

    if not all_pass:
        print("\nFailed checks:")
        for row in checks:
            if not row["pass"]:
                print(f"- {row['check']}: value={row['value']} expected={row['expected']} detail={row['detail']}")
        sys.exit(2)


if __name__ == "__main__":
    main()
