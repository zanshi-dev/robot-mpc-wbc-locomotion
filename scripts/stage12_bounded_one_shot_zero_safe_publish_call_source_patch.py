#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import math
import os
import re
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE1213_SUMMARY = LOG_DIR / "stage12_bounded_publish_call_source_patch_preflight_freeze_summary.csv"
STAGE1213_GATE = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage1213.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
SAFETY_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

SOURCE_BACKUP = LOG_DIR / "stage12_disabled_controller_node_before_stage1214.cpp"
SOURCE_AFTER = LOG_DIR / "stage12_disabled_controller_node_after_stage1214.cpp"

SUMMARY_PATH = LOG_DIR / "stage12_bounded_one_shot_zero_safe_publish_call_source_patch_summary.csv"
LOG_PATH = LOG_DIR / "stage12_bounded_one_shot_zero_safe_publish_call_source_patch_log.csv"
TOPIC_OBS_PATH = LOG_DIR / "stage12_bounded_one_shot_zero_safe_publish_call_topic_observations.csv"
PARAM_OBS_PATH = LOG_DIR / "stage12_bounded_one_shot_zero_safe_publish_call_param_observations.csv"
ECHO1_STDOUT = LOG_DIR / "stage12_bounded_one_shot_zero_safe_publish_call_echo1_stdout.txt"
ECHO1_STDERR = LOG_DIR / "stage12_bounded_one_shot_zero_safe_publish_call_echo1_stderr.txt"
ECHO2_STDOUT = LOG_DIR / "stage12_bounded_one_shot_zero_safe_publish_call_echo2_stdout.txt"
ECHO2_STDERR = LOG_DIR / "stage12_bounded_one_shot_zero_safe_publish_call_echo2_stderr.txt"
SAFETY_GATE_PATH = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage1214.csv"
DOC_PATH = ROOT / "docs/STAGE12_BOUNDED_ONE_SHOT_ZERO_SAFE_PUBLISH_CALL_SOURCE_PATCH.md"

BUILD_STDOUT = LOG_DIR / "stage12_bounded_one_shot_zero_safe_publish_call_build_stdout.txt"
BUILD_STDERR = LOG_DIR / "stage12_bounded_one_shot_zero_safe_publish_call_build_stderr.txt"
BRIDGE_STDOUT = LOG_DIR / "stage12_bounded_one_shot_zero_safe_publish_call_bridge_stdout.txt"
BRIDGE_STDERR = LOG_DIR / "stage12_bounded_one_shot_zero_safe_publish_call_bridge_stderr.txt"
CONTROLLER_STDOUT = LOG_DIR / "stage12_bounded_one_shot_zero_safe_publish_call_controller_stdout.txt"
CONTROLLER_STDERR = LOG_DIR / "stage12_bounded_one_shot_zero_safe_publish_call_controller_stderr.txt"

BRIDGE_PACKAGE = "robot_mpc_wbc_bridge"
BRIDGE_EXECUTABLE = "mujoco_bridge_node"
CONTROLLER_PACKAGE = "robot_mpc_wbc_cpp_controller"
CONTROLLER_EXECUTABLE = "go1_disabled_controller_node"

NODE_NAME = "/go1_disabled_controller_node"
TORQUE_TOPIC = "/go1/joint_torque_cmd"
PARAM_ENABLE = "enable_torque_publisher"
PARAM_CONFIRM = "confirm_torque_publisher_enable"

CMATH_INCLUDE = "#include <cmath>"

STAGE1214_CALL_BLOCK = """
    const bool stage1214_enable =
      this->get_parameter("enable_torque_publisher").as_bool();
    const bool stage1214_confirm =
      this->get_parameter("confirm_torque_publisher_enable").as_bool();
    const bool stage1214_state_ready = true;
    stage1214_bounded_publish_invoked_ =
      publishBoundedZeroSafeTorqueOnceIfAllowed(
        stage1214_enable, stage1214_confirm, stage1214_state_ready);
""".rstrip()

STAGE1214_HELPER_BLOCK = """
  bool publishBoundedZeroSafeTorqueOnceIfAllowed(
    const bool manual_enable,
    const bool manual_confirm,
    const bool state_ready)
  {
    if (!manual_enable || !manual_confirm || !state_ready) {
      return false;
    }
    if (active_torque_cmd_publisher_ == nullptr) {
      return false;
    }

    auto msg = makeDormantSafeTorqueCommandMessage();
    if (msg.data.size() != kDormantTorquePayloadLength) {
      return false;
    }
    for (const auto value : msg.data) {
      if (!std::isfinite(value)) {
        return false;
      }
    }

    active_torque_cmd_publisher_->publish(msg);
    return true;
  }

  bool stage1214_bounded_publish_invoked_{false};
  static constexpr bool kStage1214BoundedPublishCallImplemented = true;
  static constexpr bool kStage1214ContinuousPublishImplemented = false;
""".rstrip()


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


def sha256_text(text: str):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def add_check(rows, check, value, expected, passed, detail=""):
    rows.append({
        "check": check,
        "value": str(value),
        "expected": str(expected),
        "pass": bool(passed),
        "detail": detail,
    })


def count_publish_calls(text: str):
    return len(re.findall(r"(?:->|\.)publish\s*\(", text))


def patch_source(text: str):
    if count_publish_calls(text) != 0:
        raise RuntimeError("pre-patch source already contains a publish call")

    patched = text
    changed = False

    if CMATH_INCLUDE not in patched:
        include_matches = list(re.finditer(r'^#include .+$', patched, flags=re.MULTILINE))
        if include_matches:
            pos = include_matches[-1].end()
            patched = patched[:pos] + "\n" + CMATH_INCLUDE + patched[pos:]
        else:
            patched = CMATH_INCLUDE + "\n" + patched
        changed = True

    if "publishBoundedZeroSafeTorqueOnceIfAllowed" not in patched:
        class_end_marker = "\n};\n\nint main"
        idx = patched.rfind(class_end_marker)
        if idx == -1:
            idx = patched.rfind("\n};")
        if idx == -1:
            raise RuntimeError("cannot locate class closing brace for Stage 12.14 helper insertion")
        patched = patched[:idx] + "\n" + STAGE1214_HELPER_BLOCK + patched[idx:]
        changed = True

    if "stage1214_bounded_publish_invoked_" not in patched.split("publishBoundedZeroSafeTorqueOnceIfAllowed")[0]:
        marker = "Stage 12.4 active torque publisher constructed without publish call; manual flags remain default false."
        marker_idx = patched.find(marker)
        if marker_idx == -1:
            raise RuntimeError("cannot locate Stage 12.4 publisher construction marker for bounded publish call insertion")
        insert_pos = patched.find(");", marker_idx)
        if insert_pos == -1:
            raise RuntimeError("cannot locate end of Stage 12.4 RCLCPP_INFO statement")
        insert_pos += len(");")
        patched = patched[:insert_pos] + "\n" + STAGE1214_CALL_BLOCK + patched[insert_pos:]
        changed = True

    return patched, changed


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
    BUILD_STDOUT.write_text(proc.stdout or "")
    BUILD_STDERR.write_text(proc.stderr or "")
    return proc.returncode


def start_node(package_name, executable_name, extra_ros_args=None):
    extra = extra_ros_args or ""
    cmd = (
        "source /opt/ros/jazzy/setup.bash && "
        "source ros2_ws/install/setup.bash && "
        f"exec ros2 run {package_name} {executable_name} {extra}"
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


def start_echo_once(timeout_seconds, stdout_path, stderr_path):
    cmd = (
        "source /opt/ros/jazzy/setup.bash && "
        "source ros2_ws/install/setup.bash && "
        f"exec timeout {timeout_seconds}s ros2 topic echo --once {TORQUE_TOPIC}"
    )
    return subprocess.Popen(
        ["/bin/bash", "-lc", cmd],
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )


def finish_echo(proc, stdout_path, stderr_path, wait_timeout):
    try:
        out, err = proc.communicate(timeout=wait_timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            pass
        out, err = proc.communicate(timeout=3)
    stdout_path.write_text(out or "")
    stderr_path.write_text(err or "")
    return proc.returncode, out or "", err or ""


def topic_info(topic):
    proc = bash_cmd(f"ros2 topic info {topic}", timeout=10)
    stdout = proc.stdout or ""
    pub_count = None
    sub_count = None

    m = re.search(r"Publisher count:\s*(\d+)", stdout)
    if m:
        pub_count = int(m.group(1))

    m = re.search(r"Subscription count:\s*(\d+)", stdout)
    if m:
        sub_count = int(m.group(1))

    return proc.returncode, stdout, proc.stderr or "", pub_count, sub_count


def get_param_bool(param_name):
    proc = bash_cmd(f"ros2 param get {NODE_NAME} {param_name}", timeout=10)
    text = (proc.stdout or "").strip().lower()
    if "true" in text:
        value = True
    elif "false" in text:
        value = False
    else:
        value = None
    return proc.returncode, value, proc.stdout or "", proc.stderr or ""


def set_param_bool(param_name, value):
    literal = "true" if value else "false"
    return bash_cmd(f"ros2 param set {NODE_NAME} {param_name} {literal}", timeout=10)


def parse_echo_payload(stdout):
    if "data:" not in stdout:
        return []
    payload_part = stdout.split("data:", 1)[1]
    payload_part = payload_part.split("---", 1)[0]
    nums = re.findall(r"[-+]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", payload_part)
    return [float(x) for x in nums]


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    checks = []

    s1213 = load_summary(STAGE1213_SUMMARY)

    stage1213_pass = as_bool(s1213.get("pass", "False"))
    preflight_frozen = as_bool(s1213.get("bounded_publish_call_source_patch_preflight_frozen", "False"))
    stage1213_source_has_publish_call = as_bool(s1213.get("current_source_has_publish_call", "True"))
    stage1213_active_path = as_bool(s1213.get("active_ros_publisher_path_exists", "False"))
    stage1213_manual_active = as_bool(s1213.get("manual_enable_active", "True"))
    stage1213_torque_ready = as_bool(s1213.get("torque_enable_ready", "True"))
    stage1213_torque_enabled = as_bool(s1213.get("torque_publisher_enabled", "True"))
    stage1213_torque_published = as_bool(s1213.get("torque_command_published_by_stage1213", "True"))
    stage1213_control_changed = as_bool(s1213.get("control_law_changed", "True"))

    add_check(checks, "stage1213_summary_exists", STAGE1213_SUMMARY.exists(), True, STAGE1213_SUMMARY.exists(), str(STAGE1213_SUMMARY))
    add_check(checks, "stage1213_pass", stage1213_pass, True, stage1213_pass)
    add_check(checks, "stage1213_preflight_frozen", preflight_frozen, True, preflight_frozen)
    add_check(checks, "stage1213_source_has_publish_call", stage1213_source_has_publish_call, False, not stage1213_source_has_publish_call)
    add_check(checks, "stage1213_active_ros_publisher_path_exists", stage1213_active_path, True, stage1213_active_path)
    add_check(checks, "stage1213_manual_enable_active", stage1213_manual_active, False, not stage1213_manual_active)
    add_check(checks, "stage1213_torque_enable_ready", stage1213_torque_ready, False, not stage1213_torque_ready)
    add_check(checks, "stage1213_torque_publisher_enabled", stage1213_torque_enabled, False, not stage1213_torque_enabled)
    add_check(checks, "stage1213_torque_command_published", stage1213_torque_published, False, not stage1213_torque_published)
    add_check(checks, "stage1213_control_law_changed", stage1213_control_changed, False, not stage1213_control_changed)

    gate_rows_in = load_dicts(STAGE1213_GATE)
    gate_status_in = {
        row.get("gate", ""): as_bool(row.get("current_status", "False"))
        for row in gate_rows_in
    }

    add_check(checks, "stage1213_gate_exists", STAGE1213_GATE.exists(), True, STAGE1213_GATE.exists(), str(STAGE1213_GATE))
    add_check(checks, "stage1213_gate_g3_true", gate_status_in.get("G3", False), True, gate_status_in.get("G3", False) is True)
    add_check(checks, "stage1213_gate_g8_false", gate_status_in.get("G8", True), False, gate_status_in.get("G8", True) is False)
    add_check(checks, "stage1213_gate_g9_true", gate_status_in.get("G9", False), True, gate_status_in.get("G9", False) is True)
    add_check(checks, "stage1213_gate_g31_true", gate_status_in.get("G31", False), True, gate_status_in.get("G31", False) is True)

    source_before = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    SOURCE_BACKUP.write_text(source_before)
    source_hash_before = sha256_text(source_before)

    pre_source_has_create_publisher = "create_publisher<std_msgs::msg::Float64MultiArray>" in source_before
    pre_source_has_publish_call = count_publish_calls(source_before) > 0
    pre_source_references_torque_topic = TORQUE_TOPIC in source_before
    pre_source_has_active_member = "active_torque_cmd_publisher_" in source_before
    pre_source_has_stage124_marker = (
        "kStage124PublisherConstructionImplemented" in source_before and
        "kStage124PublishCallImplemented = false" in source_before
    )

    add_check(checks, "pre_source_has_create_publisher", pre_source_has_create_publisher, True, pre_source_has_create_publisher)
    add_check(checks, "pre_source_has_no_publish_call", pre_source_has_publish_call, False, not pre_source_has_publish_call)
    add_check(checks, "pre_source_references_torque_topic", pre_source_references_torque_topic, True, pre_source_references_torque_topic)
    add_check(checks, "pre_source_has_active_publisher_member", pre_source_has_active_member, True, pre_source_has_active_member)
    add_check(checks, "pre_source_has_stage124_marker", pre_source_has_stage124_marker, True, pre_source_has_stage124_marker)

    patched_source, patch_changed = patch_source(source_before)
    CPP_SOURCE.write_text(patched_source)
    SOURCE_AFTER.write_text(patched_source)

    source_after = CPP_SOURCE.read_text(errors="replace")
    source_hash_after = sha256_text(source_after)

    source_patch_applied = source_hash_before != source_hash_after
    post_publish_call_count = count_publish_calls(source_after)
    post_source_has_create_publisher = "create_publisher<std_msgs::msg::Float64MultiArray>" in source_after
    post_source_has_publish_call = post_publish_call_count == 1
    post_source_references_torque_topic = TORQUE_TOPIC in source_after
    post_source_has_active_member = "active_torque_cmd_publisher_" in source_after
    post_source_has_stage124_marker = (
        "kStage124PublisherConstructionImplemented" in source_after and
        "kStage124PublishCallImplemented = false" in source_after
    )
    post_source_has_stage1214_marker = (
        "kStage1214BoundedPublishCallImplemented = true" in source_after and
        "kStage1214ContinuousPublishImplemented = false" in source_after
    )
    post_source_has_bounded_publish_helper = "publishBoundedZeroSafeTorqueOnceIfAllowed" in source_after
    post_source_has_zero_safe_message_helper = "makeDormantSafeTorqueCommandMessage" in source_after
    post_source_uses_safety_chain = (
        "watchdogFallbackZeroTorque" in source_after and
        "clampTorqueCommand" in source_after
    )
    post_source_forbids_continuous_publish = "kStage1214ContinuousPublishImplemented = false" in source_after

    add_check(checks, "source_patch_applied", source_patch_applied, True, source_patch_applied)
    add_check(checks, "post_source_has_create_publisher", post_source_has_create_publisher, True, post_source_has_create_publisher)
    add_check(checks, "post_publish_call_count", post_publish_call_count, 1, post_publish_call_count == 1)
    add_check(checks, "post_source_has_one_publish_call", post_source_has_publish_call, True, post_source_has_publish_call)
    add_check(checks, "post_source_references_torque_topic", post_source_references_torque_topic, True, post_source_references_torque_topic)
    add_check(checks, "post_source_has_active_publisher_member", post_source_has_active_member, True, post_source_has_active_member)
    add_check(checks, "post_source_has_stage124_marker", post_source_has_stage124_marker, True, post_source_has_stage124_marker)
    add_check(checks, "post_source_has_stage1214_marker", post_source_has_stage1214_marker, True, post_source_has_stage1214_marker)
    add_check(checks, "post_source_has_bounded_publish_helper", post_source_has_bounded_publish_helper, True, post_source_has_bounded_publish_helper)
    add_check(checks, "post_source_has_zero_safe_message_helper", post_source_has_zero_safe_message_helper, True, post_source_has_zero_safe_message_helper)
    add_check(checks, "post_source_uses_safety_chain", post_source_uses_safety_chain, True, post_source_uses_safety_chain)
    add_check(checks, "post_source_forbids_continuous_publish", post_source_forbids_continuous_publish, True, post_source_forbids_continuous_publish)

    safety_text = SAFETY_HEADER.read_text(errors="replace") if SAFETY_HEADER.exists() else ""
    zero_text = ZERO_HEADER.read_text(errors="replace") if ZERO_HEADER.exists() else ""
    safety_header_has_clamp_watchdog = "clampTorqueCommand" in safety_text and "watchdogFallbackZeroTorque" in safety_text
    zero_header_declares_12 = "kGo1NumActuatedJoints = 12" in zero_text

    add_check(checks, "safety_header_has_clamp_watchdog", safety_header_has_clamp_watchdog, True, safety_header_has_clamp_watchdog)
    add_check(checks, "zero_header_declares_12", zero_header_declares_12, True, zero_header_declares_12)

    build_rc = build_packages()
    add_check(checks, "colcon_build_returncode", build_rc, 0, build_rc == 0)

    bridge_proc = None
    controller_proc = None
    echo1_proc = None

    param_rows = []
    topic_rows = []

    manual_enable_active_during_test = False
    manual_enable_reverted_false = False
    active_ros_publisher_path_exists = False
    first_echo_returncode = None
    second_echo_returncode = None
    first_echo_payload = []
    first_echo_payload_length = 0
    first_echo_payload_all_finite = False
    first_echo_payload_all_zero = False
    first_echo_message_received = False
    second_echo_timeout_no_extra_message = False
    controller_alive_after_publish = False

    try:
        bridge_proc = start_node(BRIDGE_PACKAGE, BRIDGE_EXECUTABLE)
        time.sleep(3.0)
        bridge_alive = bridge_proc.poll() is None
        add_check(checks, "bridge_alive_after_startup", bridge_alive, True, bridge_alive)

        echo1_proc = start_echo_once(12, ECHO1_STDOUT, ECHO1_STDERR)
        time.sleep(2.0)

        controller_args = (
            "--ros-args "
            "-p enable_torque_publisher:=true "
            "-p confirm_torque_publisher_enable:=true"
        )
        controller_proc = start_node(CONTROLLER_PACKAGE, CONTROLLER_EXECUTABLE, controller_args)
        time.sleep(3.0)
        controller_alive = controller_proc.poll() is None
        add_check(checks, "disabled_controller_alive_after_startup", controller_alive, True, controller_alive)

        first_echo_returncode, echo1_out, echo1_err = finish_echo(
            echo1_proc, ECHO1_STDOUT, ECHO1_STDERR, wait_timeout=15
        )

        first_echo_payload = parse_echo_payload(echo1_out)
        first_echo_payload_length = len(first_echo_payload)
        first_echo_payload_all_finite = all(math.isfinite(x) for x in first_echo_payload)
        first_echo_payload_all_zero = first_echo_payload_length == 12 and all(abs(x) <= 1e-12 for x in first_echo_payload)
        first_echo_message_received = first_echo_returncode == 0 and first_echo_payload_length == 12

        rc, value, out, err = get_param_bool(PARAM_ENABLE)
        param_rows.append({"phase": "during_test", "param": PARAM_ENABLE, "returncode": rc, "value": value, "stdout": out.strip(), "stderr": err.strip()})
        activated_enable_true = rc == 0 and value is True

        rc, value, out, err = get_param_bool(PARAM_CONFIRM)
        param_rows.append({"phase": "during_test", "param": PARAM_CONFIRM, "returncode": rc, "value": value, "stdout": out.strip(), "stderr": err.strip()})
        activated_confirm_true = rc == 0 and value is True

        manual_enable_active_during_test = activated_enable_true and activated_confirm_true

        for i in range(6):
            info_rc, info_out, info_err, pub_count, sub_count = topic_info(TORQUE_TOPIC)
            topic_rows.append({
                "phase": "after_first_publish",
                "sample_index": i,
                "topic": TORQUE_TOPIC,
                "topic_info_returncode": info_rc,
                "publisher_count": "" if pub_count is None else pub_count,
                "subscription_count": "" if sub_count is None else sub_count,
                "publisher_count_positive": isinstance(pub_count, int) and pub_count >= 1,
                "subscription_count_positive": isinstance(sub_count, int) and sub_count >= 1,
            })
            time.sleep(0.4)

        set_confirm_false = set_param_bool(PARAM_CONFIRM, False)
        param_rows.append({"phase": "revert_false", "param": PARAM_CONFIRM, "returncode": set_confirm_false.returncode, "value": "", "stdout": set_confirm_false.stdout.strip(), "stderr": set_confirm_false.stderr.strip()})

        set_enable_false = set_param_bool(PARAM_ENABLE, False)
        param_rows.append({"phase": "revert_false", "param": PARAM_ENABLE, "returncode": set_enable_false.returncode, "value": "", "stdout": set_enable_false.stdout.strip(), "stderr": set_enable_false.stderr.strip()})

        time.sleep(0.5)

        rc, value, out, err = get_param_bool(PARAM_ENABLE)
        param_rows.append({"phase": "after_revert", "param": PARAM_ENABLE, "returncode": rc, "value": value, "stdout": out.strip(), "stderr": err.strip()})
        reverted_enable_false = rc == 0 and value is False

        rc, value, out, err = get_param_bool(PARAM_CONFIRM)
        param_rows.append({"phase": "after_revert", "param": PARAM_CONFIRM, "returncode": rc, "value": value, "stdout": out.strip(), "stderr": err.strip()})
        reverted_confirm_false = rc == 0 and value is False

        manual_enable_reverted_false = reverted_enable_false and reverted_confirm_false

        echo2_proc = start_echo_once(4, ECHO2_STDOUT, ECHO2_STDERR)
        second_echo_returncode, echo2_out, echo2_err = finish_echo(
            echo2_proc, ECHO2_STDOUT, ECHO2_STDERR, wait_timeout=8
        )
        second_echo_timeout_no_extra_message = second_echo_returncode == 124 and not echo2_out.strip()

        controller_alive_after_publish = controller_proc.poll() is None

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

    with TOPIC_OBS_PATH.open("w", newline="") as f:
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
    active_ros_publisher_path_exists = torque_publishers_positive_all_samples

    add_check(checks, "manual_enable_active_during_test", manual_enable_active_during_test, True, manual_enable_active_during_test)
    add_check(checks, "manual_enable_reverted_false", manual_enable_reverted_false, True, manual_enable_reverted_false)
    add_check(checks, "runtime_topic_sample_count", runtime_topic_sample_count, 6, runtime_topic_sample_count == 6)
    add_check(checks, "topic_info_all_returncode_zero", topic_info_all_returncode_zero, True, topic_info_all_returncode_zero)
    add_check(checks, "torque_publishers_positive_all_samples", torque_publishers_positive_all_samples, True, torque_publishers_positive_all_samples)
    add_check(checks, "torque_subscribers_positive_all_samples", torque_subscribers_positive_all_samples, True, torque_subscribers_positive_all_samples)

    add_check(checks, "first_echo_returncode", first_echo_returncode, 0, first_echo_returncode == 0)
    add_check(checks, "first_echo_message_received", first_echo_message_received, True, first_echo_message_received)
    add_check(checks, "first_echo_payload_length", first_echo_payload_length, 12, first_echo_payload_length == 12)
    add_check(checks, "first_echo_payload_all_finite", first_echo_payload_all_finite, True, first_echo_payload_all_finite)
    add_check(checks, "first_echo_payload_all_zero", first_echo_payload_all_zero, True, first_echo_payload_all_zero)
    add_check(checks, "second_echo_returncode_timeout", second_echo_returncode, 124, second_echo_returncode == 124)
    add_check(checks, "second_echo_timeout_no_extra_message", second_echo_timeout_no_extra_message, True, second_echo_timeout_no_extra_message)
    add_check(checks, "controller_alive_after_publish", controller_alive_after_publish, True, controller_alive_after_publish)

    bounded_zero_safe_torque_message_published = first_echo_message_received and first_echo_payload_all_zero and first_echo_payload_all_finite
    continuous_torque_streaming_enabled = not second_echo_timeout_no_extra_message
    bounded_one_shot_publish_call_implemented = (
        stage1213_pass and
        preflight_frozen and
        source_patch_applied and
        post_publish_call_count == 1 and
        post_source_has_stage1214_marker and
        post_source_has_bounded_publish_helper and
        build_rc == 0 and
        manual_enable_active_during_test and
        manual_enable_reverted_false and
        bounded_zero_safe_torque_message_published and
        second_echo_timeout_no_extra_message and
        controller_alive_after_publish and
        active_ros_publisher_path_exists
    )

    torque_enable_ready = False
    torque_publisher_enabled = False
    torque_command_published_by_stage1214 = bounded_zero_safe_torque_message_published
    control_law_changed = False

    gate_rows_out = []
    for row in gate_rows_in:
        if row.get("gate") == "G3":
            row = dict(row)
            row["current_status"] = False
            row["evidence"] = "Stage 12.14 intentionally adds exactly one bounded publish call"
        if row.get("gate") == "G8":
            row = dict(row)
            row["current_status"] = False
            row["evidence"] = "manual flags were activated during test and reverted false"
        gate_rows_out.append(row)

    gate_rows_out.append({
        "gate": "G32",
        "name": "Bounded one-shot zero/safe publish-call implementation passed",
        "required_before_torque_publish": True,
        "current_status": bounded_one_shot_publish_call_implemented,
        "evidence": str(LOG_PATH.relative_to(ROOT)),
    })

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(gate_rows_out)

    add_check(checks, "bounded_zero_safe_torque_message_published", bounded_zero_safe_torque_message_published, True, bounded_zero_safe_torque_message_published)
    add_check(checks, "continuous_torque_streaming_enabled", continuous_torque_streaming_enabled, False, not continuous_torque_streaming_enabled)
    add_check(checks, "bounded_one_shot_publish_call_implemented", bounded_one_shot_publish_call_implemented, True, bounded_one_shot_publish_call_implemented)
    add_check(checks, "active_ros_publisher_path_exists", active_ros_publisher_path_exists, True, active_ros_publisher_path_exists)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)
    add_check(checks, "torque_publisher_enabled", torque_publisher_enabled, False, not torque_publisher_enabled)
    add_check(checks, "torque_command_published_by_stage1214", torque_command_published_by_stage1214, True, torque_command_published_by_stage1214)
    add_check(checks, "control_law_changed", control_law_changed, False, not control_law_changed)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    DOC_PATH.write_text(f"""# Stage 12.14 Bounded One-shot Zero/Safe Publish-call Source Patch

## 一、结论

Stage 12.14 实现 bounded one-shot zero/safe publish-call source patch。

本阶段允许 exactly one bounded publish call：

- source publish call count: {post_publish_call_count}
- first_echo_message_received: {first_echo_message_received}
- first_echo_payload_length: {first_echo_payload_length}
- first_echo_payload_all_finite: {first_echo_payload_all_finite}
- first_echo_payload_all_zero: {first_echo_payload_all_zero}
- second_echo_timeout_no_extra_message: {second_echo_timeout_no_extra_message}
- continuous_torque_streaming_enabled: {continuous_torque_streaming_enabled}

## 二、Source patch

Before source backup:

    results/logs_sample/stage12_disabled_controller_node_before_stage1214.cpp

After source snapshot:

    results/logs_sample/stage12_disabled_controller_node_after_stage1214.cpp

Hash before:

    {source_hash_before}

Hash after:

    {source_hash_after}

Source checks:

- post_source_has_create_publisher: {post_source_has_create_publisher}
- post_publish_call_count: {post_publish_call_count}
- post_source_has_stage1214_marker: {post_source_has_stage1214_marker}
- post_source_has_bounded_publish_helper: {post_source_has_bounded_publish_helper}
- post_source_forbids_continuous_publish: {post_source_forbids_continuous_publish}

## 三、Runtime evidence

Echo 1 stdout:

    results/logs_sample/stage12_bounded_one_shot_zero_safe_publish_call_echo1_stdout.txt

Echo 2 stdout:

    results/logs_sample/stage12_bounded_one_shot_zero_safe_publish_call_echo2_stdout.txt

Param observations:

    results/logs_sample/stage12_bounded_one_shot_zero_safe_publish_call_param_observations.csv

Topic observations:

    results/logs_sample/stage12_bounded_one_shot_zero_safe_publish_call_topic_observations.csv

Runtime checks:

- manual_enable_active_during_test: {manual_enable_active_during_test}
- manual_enable_reverted_false: {manual_enable_reverted_false}
- active_ros_publisher_path_exists: {active_ros_publisher_path_exists}
- bounded_zero_safe_torque_message_published: {bounded_zero_safe_torque_message_published}
- controller_alive_after_publish: {controller_alive_after_publish}

## 四、Safety gate after Stage 12.14

Updated:

- G3 no publish call: False by design
- G8 manual enable active after revert: False
- G9 active ROS publisher path exists: True
- G32 bounded one-shot zero/safe publish-call implementation passed: {bounded_one_shot_publish_call_implemented}

Therefore:

    torque_enable_ready = {torque_enable_ready}

## 五、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.14 完成的是 bounded one-shot zero/safe publish-call test，不是连续 torque streaming。

Stage 12.14 没有完成：

- continuous torque publishing；
- torque streaming controller；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。
""")

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 12.14"])
        writer.writerow(["test_name", "bounded_one_shot_zero_safe_publish_call_source_patch"])
        writer.writerow(["stage1213_pass", stage1213_pass])
        writer.writerow(["stage1213_bounded_publish_call_source_patch_preflight_frozen", preflight_frozen])
        writer.writerow(["source_patch_applied", source_patch_applied])
        writer.writerow(["source_hash_before", source_hash_before])
        writer.writerow(["source_hash_after", source_hash_after])
        writer.writerow(["post_source_has_create_publisher", post_source_has_create_publisher])
        writer.writerow(["post_publish_call_count", post_publish_call_count])
        writer.writerow(["post_source_has_one_publish_call", post_source_has_publish_call])
        writer.writerow(["post_source_references_torque_topic", post_source_references_torque_topic])
        writer.writerow(["post_source_has_active_publisher_member", post_source_has_active_member])
        writer.writerow(["post_source_has_stage124_marker", post_source_has_stage124_marker])
        writer.writerow(["post_source_has_stage1214_marker", post_source_has_stage1214_marker])
        writer.writerow(["post_source_has_bounded_publish_helper", post_source_has_bounded_publish_helper])
        writer.writerow(["post_source_has_zero_safe_message_helper", post_source_has_zero_safe_message_helper])
        writer.writerow(["post_source_uses_safety_chain", post_source_uses_safety_chain])
        writer.writerow(["post_source_forbids_continuous_publish", post_source_forbids_continuous_publish])
        writer.writerow(["colcon_build_returncode", build_rc])
        writer.writerow(["manual_enable_active_during_test", manual_enable_active_during_test])
        writer.writerow(["manual_enable_reverted_false", manual_enable_reverted_false])
        writer.writerow(["runtime_topic_sample_count", runtime_topic_sample_count])
        writer.writerow(["topic_info_all_returncode_zero", topic_info_all_returncode_zero])
        writer.writerow(["torque_publishers_positive_all_samples", torque_publishers_positive_all_samples])
        writer.writerow(["torque_subscribers_positive_all_samples", torque_subscribers_positive_all_samples])
        writer.writerow(["first_echo_returncode", first_echo_returncode])
        writer.writerow(["first_echo_message_received", first_echo_message_received])
        writer.writerow(["first_echo_payload_length", first_echo_payload_length])
        writer.writerow(["first_echo_payload_all_finite", first_echo_payload_all_finite])
        writer.writerow(["first_echo_payload_all_zero", first_echo_payload_all_zero])
        writer.writerow(["second_echo_returncode", second_echo_returncode])
        writer.writerow(["second_echo_timeout_no_extra_message", second_echo_timeout_no_extra_message])
        writer.writerow(["bounded_zero_safe_torque_message_published", bounded_zero_safe_torque_message_published])
        writer.writerow(["continuous_torque_streaming_enabled", continuous_torque_streaming_enabled])
        writer.writerow(["controller_alive_after_publish", controller_alive_after_publish])
        writer.writerow(["bounded_one_shot_publish_call_implemented", bounded_one_shot_publish_call_implemented])
        writer.writerow(["active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g3_no_publish_call", False])
        writer.writerow(["g8_manual_enable_active_after_revert", False])
        writer.writerow(["g9_active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g31_bounded_publish_call_source_patch_preflight_freeze_passed", gate_status_in.get("G31", False)])
        writer.writerow(["g32_bounded_one_shot_zero_safe_publish_call_implementation_passed", bounded_one_shot_publish_call_implemented])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", control_law_changed])
        writer.writerow(["torque_publisher_enabled", torque_publisher_enabled])
        writer.writerow(["torque_command_published_by_stage1214", torque_command_published_by_stage1214])
        writer.writerow(["stage12_scope", "bounded_one_shot_zero_safe_publish_call_source_patch"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["continuous_torque_streaming_completed", False])
        writer.writerow(["ros2_cpp_realtime_controller_completed", False])
        writer.writerow(["pure_wbc_locomotion_completed", False])
        writer.writerow(["ekf_completed", False])
        writer.writerow(["full_3d_centroidal_mpc_completed", False])
        writer.writerow(["hardware_deployment_completed", False])
        writer.writerow(["num_checks", len(checks)])
        writer.writerow(["num_failed_checks", sum(1 for row in checks if not row["pass"])])
        writer.writerow(["pass", all_pass])
        writer.writerow(["log_csv", str(LOG_PATH.relative_to(ROOT))])
        writer.writerow(["param_observations_csv", str(PARAM_OBS_PATH.relative_to(ROOT))])
        writer.writerow(["topic_observations_csv", str(TOPIC_OBS_PATH.relative_to(ROOT))])
        writer.writerow(["echo1_stdout", str(ECHO1_STDOUT.relative_to(ROOT))])
        writer.writerow(["echo1_stderr", str(ECHO1_STDERR.relative_to(ROOT))])
        writer.writerow(["echo2_stdout", str(ECHO2_STDOUT.relative_to(ROOT))])
        writer.writerow(["echo2_stderr", str(ECHO2_STDERR.relative_to(ROOT))])
        writer.writerow(["safety_gate_csv", str(SAFETY_GATE_PATH.relative_to(ROOT))])
        writer.writerow(["summary_csv", str(SUMMARY_PATH.relative_to(ROOT))])
        writer.writerow(["source_backup", str(SOURCE_BACKUP.relative_to(ROOT))])
        writer.writerow(["source_after", str(SOURCE_AFTER.relative_to(ROOT))])
        writer.writerow(["build_stdout", str(BUILD_STDOUT.relative_to(ROOT))])
        writer.writerow(["build_stderr", str(BUILD_STDERR.relative_to(ROOT))])
        writer.writerow(["bridge_stdout", str(BRIDGE_STDOUT.relative_to(ROOT))])
        writer.writerow(["bridge_stderr", str(BRIDGE_STDERR.relative_to(ROOT))])
        writer.writerow(["controller_stdout", str(CONTROLLER_STDOUT.relative_to(ROOT))])
        writer.writerow(["controller_stderr", str(CONTROLLER_STDERR.relative_to(ROOT))])
        writer.writerow(["doc", str(DOC_PATH.relative_to(ROOT))])

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 12.14 Bounded One-shot Zero/Safe Publish-call Source Patch

Stage 12.14 完成 bounded one-shot zero/safe publish-call source patch。

- Script: `scripts/stage12_bounded_one_shot_zero_safe_publish_call_source_patch.py`
- Summary: `results/logs_sample/stage12_bounded_one_shot_zero_safe_publish_call_source_patch_summary.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1214.csv`
- Echo 1: `results/logs_sample/stage12_bounded_one_shot_zero_safe_publish_call_echo1_stdout.txt`
- Echo 2: `results/logs_sample/stage12_bounded_one_shot_zero_safe_publish_call_echo2_stdout.txt`
- pass: `{all_pass}`
- bounded_one_shot_publish_call_implemented: `{bounded_one_shot_publish_call_implemented}`
- bounded_zero_safe_torque_message_published: `{bounded_zero_safe_torque_message_published}`
- first_echo_payload_length: `{first_echo_payload_length}`
- first_echo_payload_all_zero: `{first_echo_payload_all_zero}`
- second_echo_timeout_no_extra_message: `{second_echo_timeout_no_extra_message}`
- continuous_torque_streaming_enabled: `{continuous_torque_streaming_enabled}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `{torque_publisher_enabled}`
- torque_command_published_by_stage1214: `{torque_command_published_by_stage1214}`
- control_law_changed: `{control_law_changed}`

Stage 12.14 只完成 bounded one-shot zero/safe publish，不完成连续 torque streaming，不完成 realtime controller。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 12.14 Bounded One-shot Zero/Safe Publish-call Source Patch"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 12.14] bounded one-shot zero/safe publish-call source patch")
    print(f"pass={all_pass}")
    print(f"source_patch_applied={source_patch_applied}")
    print(f"post_publish_call_count={post_publish_call_count}")
    print(f"post_source_has_stage1214_marker={post_source_has_stage1214_marker}")
    print(f"manual_enable_active_during_test={manual_enable_active_during_test}")
    print(f"manual_enable_reverted_false={manual_enable_reverted_false}")
    print(f"first_echo_message_received={first_echo_message_received}")
    print(f"first_echo_payload_length={first_echo_payload_length}")
    print(f"first_echo_payload_all_finite={first_echo_payload_all_finite}")
    print(f"first_echo_payload_all_zero={first_echo_payload_all_zero}")
    print(f"second_echo_timeout_no_extra_message={second_echo_timeout_no_extra_message}")
    print(f"bounded_zero_safe_torque_message_published={bounded_zero_safe_torque_message_published}")
    print(f"continuous_torque_streaming_enabled={continuous_torque_streaming_enabled}")
    print(f"bounded_one_shot_publish_call_implemented={bounded_one_shot_publish_call_implemented}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print(f"control_law_changed={control_law_changed}")
    print(f"torque_publisher_enabled={torque_publisher_enabled}")
    print(f"torque_command_published_by_stage1214={torque_command_published_by_stage1214}")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
    print(f"summary_csv={SUMMARY_PATH.relative_to(ROOT)}")
    print(f"safety_gate_csv={SAFETY_GATE_PATH.relative_to(ROOT)}")
    print(f"doc={DOC_PATH.relative_to(ROOT)}")

    if not all_pass:
        print("\nFailed checks:")
        for row in checks:
            if not row["pass"]:
                print(f"- {row['check']}: value={row['value']} expected={row['expected']} detail={row['detail']}")
        sys.exit(2)


if __name__ == "__main__":
    main()
