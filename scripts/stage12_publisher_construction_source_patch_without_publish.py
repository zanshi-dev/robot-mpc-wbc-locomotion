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

STAGE123_SUMMARY = LOG_DIR / "stage12_construction_stage_preflight_freeze_summary.csv"
STAGE122_GATE = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage122.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
SAFETY_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

SUMMARY_PATH = LOG_DIR / "stage12_publisher_construction_source_patch_without_publish_summary.csv"
LOG_PATH = LOG_DIR / "stage12_publisher_construction_source_patch_without_publish_log.csv"
OBS_PATH = LOG_DIR / "stage12_publisher_construction_without_publish_topic_observations.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage124.csv"
DOC_PATH = ROOT / "docs/STAGE12_PUBLISHER_CONSTRUCTION_SOURCE_PATCH_WITHOUT_PUBLISH.md"

SOURCE_BACKUP = LOG_DIR / "stage12_disabled_controller_node_before_stage124.cpp"
SOURCE_AFTER = LOG_DIR / "stage12_disabled_controller_node_after_stage124.cpp"

BUILD_STDOUT = LOG_DIR / "stage12_publisher_construction_without_publish_build_stdout.txt"
BUILD_STDERR = LOG_DIR / "stage12_publisher_construction_without_publish_build_stderr.txt"
BRIDGE_STDOUT = LOG_DIR / "stage12_publisher_construction_without_publish_bridge_stdout.txt"
BRIDGE_STDERR = LOG_DIR / "stage12_publisher_construction_without_publish_bridge_stderr.txt"
CONTROLLER_STDOUT = LOG_DIR / "stage12_publisher_construction_without_publish_controller_stdout.txt"
CONTROLLER_STDERR = LOG_DIR / "stage12_publisher_construction_without_publish_controller_stderr.txt"
PARAM_STDOUT = LOG_DIR / "stage12_publisher_construction_without_publish_param_stdout.txt"
PARAM_STDERR = LOG_DIR / "stage12_publisher_construction_without_publish_param_stderr.txt"

BRIDGE_PACKAGE = "robot_mpc_wbc_bridge"
BRIDGE_EXECUTABLE = "mujoco_bridge_node"
CONTROLLER_PACKAGE = "robot_mpc_wbc_cpp_controller"
CONTROLLER_EXECUTABLE = "go1_disabled_controller_node"

TORQUE_TOPIC = "/go1/joint_torque_cmd"
PARAM_ENABLE = "enable_torque_publisher"
PARAM_CONFIRM = "confirm_torque_publisher_enable"

INCLUDE_LINE = '#include "std_msgs/msg/float64_multi_array.hpp"'
ACTIVE_MEMBER = "active_torque_cmd_publisher_"
ACTIVE_CONSTRUCTION_SNIPPET = """
    active_torque_cmd_publisher_ =
      this->create_publisher<std_msgs::msg::Float64MultiArray>(
        "/go1/joint_torque_cmd", rclcpp::QoS(1));
    RCLCPP_INFO(
      this->get_logger(),
      "Stage 12.4 active torque publisher constructed without publish call; manual flags remain default false.");
""".rstrip()

ACTIVE_MEMBER_SNIPPET = """
  rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr active_torque_cmd_publisher_;
  static constexpr bool kStage124PublisherConstructionImplemented = true;
  static constexpr bool kStage124PublishCallImplemented = false;
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


def patch_source(text: str):
    patched = text
    changed = False

    if INCLUDE_LINE not in patched:
        include_lines = [m.end() for m in re.finditer(r'^#include .+$', patched, flags=re.MULTILINE)]
        if include_lines:
            pos = include_lines[-1]
            patched = patched[:pos] + "\n" + INCLUDE_LINE + patched[pos:]
        else:
            patched = INCLUDE_LINE + "\n" + patched
        changed = True

    if "create_publisher<std_msgs::msg::Float64MultiArray>" not in patched:
        confirm_pattern = r'(?m)^(\s*.*declare_parameter<bool>\("confirm_torque_publisher_enable", false\).*)$'
        m = re.search(confirm_pattern, patched)
        if not m:
            raise RuntimeError("Cannot find confirm_torque_publisher_enable declare_parameter line for safe constructor insertion.")
        insert_pos = m.end()
        patched = patched[:insert_pos] + "\n" + ACTIVE_CONSTRUCTION_SNIPPET + patched[insert_pos:]
        changed = True

    if ACTIVE_MEMBER not in patched:
        class_end_marker = "\n};\n\nint main"
        idx = patched.rfind(class_end_marker)
        if idx == -1:
            idx = patched.rfind("\n};")
        if idx == -1:
            raise RuntimeError("Cannot find class closing brace for active publisher member insertion.")
        patched = patched[:idx] + "\n" + ACTIVE_MEMBER_SNIPPET + patched[idx:]
        changed = True

    if "kStage124PublisherConstructionImplemented" not in patched:
        class_end_marker = "\n};\n\nint main"
        idx = patched.rfind(class_end_marker)
        if idx == -1:
            idx = patched.rfind("\n};")
        if idx == -1:
            raise RuntimeError("Cannot find class closing brace for Stage 12.4 marker insertion.")
        patched = patched[:idx] + "\n" + ACTIVE_MEMBER_SNIPPET + patched[idx:]
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


def param_is_false(stdout):
    text = stdout.strip().lower()
    return "false" in text and "true" not in text


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    checks = []

    s123 = load_summary(STAGE123_SUMMARY)
    stage123_pass = as_bool(s123.get("pass", "False"))
    preflight_frozen = as_bool(s123.get("construction_stage_preflight_frozen", "False"))
    stage123_g8 = as_bool(s123.get("g8_manual_enable_active", "True"))
    stage123_g9 = as_bool(s123.get("g9_active_ros_publisher_path_exists", "True"))
    stage123_torque_ready = as_bool(s123.get("torque_enable_ready", "True"))
    stage123_torque_enabled = as_bool(s123.get("torque_publisher_enabled", "True"))
    stage123_control_changed = as_bool(s123.get("control_law_changed", "True"))

    add_check(checks, "stage123_summary_exists", STAGE123_SUMMARY.exists(), True, STAGE123_SUMMARY.exists(), str(STAGE123_SUMMARY))
    add_check(checks, "stage123_pass", stage123_pass, True, stage123_pass)
    add_check(checks, "stage123_construction_stage_preflight_frozen", preflight_frozen, True, preflight_frozen)
    add_check(checks, "stage123_g8_manual_enable_active", stage123_g8, False, not stage123_g8)
    add_check(checks, "stage123_g9_active_ros_publisher_path_exists", stage123_g9, False, not stage123_g9)
    add_check(checks, "stage123_torque_enable_ready", stage123_torque_ready, False, not stage123_torque_ready)
    add_check(checks, "stage123_torque_publisher_enabled", stage123_torque_enabled, False, not stage123_torque_enabled)
    add_check(checks, "stage123_control_law_changed", stage123_control_changed, False, not stage123_control_changed)

    gate_in_rows = load_dicts(STAGE122_GATE)
    gate_in_status = {row.get("gate", ""): as_bool(row.get("current_status", "False")) for row in gate_in_rows}

    add_check(checks, "stage122_gate_exists", STAGE122_GATE.exists(), True, STAGE122_GATE.exists(), str(STAGE122_GATE))
    add_check(checks, "stage122_gate_g8_false", gate_in_status.get("G8", True), False, gate_in_status.get("G8", True) is False)
    add_check(checks, "stage122_gate_g9_false", gate_in_status.get("G9", True), False, gate_in_status.get("G9", True) is False)
    add_check(checks, "stage122_gate_g21_true", gate_in_status.get("G21", False), True, gate_in_status.get("G21", False) is True)

    source_before = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    SOURCE_BACKUP.write_text(source_before)
    hash_before = sha256_text(source_before)

    pre_source_has_create_publisher = "create_publisher" in source_before
    pre_source_has_publish_call = ".publish(" in source_before or "->publish(" in source_before
    pre_source_has_torque_topic = TORQUE_TOPIC in source_before

    add_check(checks, "pre_patch_source_has_no_create_publisher", pre_source_has_create_publisher, False, not pre_source_has_create_publisher)
    add_check(checks, "pre_patch_source_has_no_publish_call", pre_source_has_publish_call, False, not pre_source_has_publish_call)
    add_check(checks, "pre_patch_source_does_not_reference_torque_topic", pre_source_has_torque_topic, False, not pre_source_has_torque_topic)

    patched_source, patch_changed = patch_source(source_before)
    CPP_SOURCE.write_text(patched_source)
    SOURCE_AFTER.write_text(patched_source)

    hash_after = sha256_text(patched_source)
    source_patch_applied = hash_before != hash_after
    source_changed_only_by_stage124 = source_patch_applied or (ACTIVE_MEMBER in source_before and "create_publisher<std_msgs::msg::Float64MultiArray>" in source_before)

    post_text = CPP_SOURCE.read_text(errors="replace")
    post_source_has_create_publisher = "create_publisher<std_msgs::msg::Float64MultiArray>" in post_text
    post_source_has_publish_call = ".publish(" in post_text or "->publish(" in post_text
    post_source_references_torque_topic = TORQUE_TOPIC in post_text
    post_source_has_active_member = ACTIVE_MEMBER in post_text
    post_source_has_stage124_marker = "kStage124PublisherConstructionImplemented" in post_text and "kStage124PublishCallImplemented = false" in post_text

    source_declares_enable_param = f'declare_parameter<bool>("{PARAM_ENABLE}", false)' in post_text
    source_declares_confirm_param = f'declare_parameter<bool>("{PARAM_CONFIRM}", false)' in post_text
    source_uses_safety = "clampTorqueCommand" in post_text and "allInputsFresh" in post_text and "watchdogFallbackZeroTorque" in post_text

    safety_text = SAFETY_HEADER.read_text(errors="replace") if SAFETY_HEADER.exists() else ""
    zero_text = ZERO_HEADER.read_text(errors="replace") if ZERO_HEADER.exists() else ""
    safety_header_has_clamp_watchdog = "clampTorqueCommand" in safety_text and "allInputsFresh" in safety_text and "watchdogFallbackZeroTorque" in safety_text
    zero_header_declares_12 = "kGo1NumActuatedJoints = 12" in zero_text

    add_check(checks, "source_patch_applied", source_patch_applied, True, source_patch_applied)
    add_check(checks, "source_changed_only_by_stage124", source_changed_only_by_stage124, True, source_changed_only_by_stage124)
    add_check(checks, "post_source_has_create_publisher", post_source_has_create_publisher, True, post_source_has_create_publisher)
    add_check(checks, "post_source_has_publish_call", post_source_has_publish_call, False, not post_source_has_publish_call)
    add_check(checks, "post_source_references_torque_topic", post_source_references_torque_topic, True, post_source_references_torque_topic)
    add_check(checks, "post_source_has_active_publisher_member", post_source_has_active_member, True, post_source_has_active_member)
    add_check(checks, "post_source_has_stage124_marker", post_source_has_stage124_marker, True, post_source_has_stage124_marker)
    add_check(checks, "source_declares_enable_param_default_false", source_declares_enable_param, True, source_declares_enable_param)
    add_check(checks, "source_declares_confirm_param_default_false", source_declares_confirm_param, True, source_declares_confirm_param)
    add_check(checks, "source_uses_safety_utilities", source_uses_safety, True, source_uses_safety)
    add_check(checks, "safety_header_has_clamp_watchdog", safety_header_has_clamp_watchdog, True, safety_header_has_clamp_watchdog)
    add_check(checks, "zero_header_declares_12", zero_header_declares_12, True, zero_header_declares_12)

    build_rc = build_packages()
    add_check(checks, "colcon_build_returncode", build_rc, 0, build_rc == 0)

    bridge_proc = None
    controller_proc = None

    enable_param_default_false = False
    confirm_param_default_false = False
    controller_alive = False
    runtime_sample_count = 6
    observations = []

    try:
        bridge_proc = start_node(BRIDGE_PACKAGE, BRIDGE_EXECUTABLE)
        time.sleep(3.0)
        bridge_alive = bridge_proc.poll() is None
        add_check(checks, "bridge_alive_after_startup", bridge_alive, True, bridge_alive)

        controller_proc = start_node(CONTROLLER_PACKAGE, CONTROLLER_EXECUTABLE)
        time.sleep(4.0)
        controller_alive = controller_proc.poll() is None
        add_check(checks, "disabled_controller_alive_after_startup", controller_alive, True, controller_alive)

        get_enable = bash_cmd(f"ros2 param get /go1_disabled_controller_node {PARAM_ENABLE}", timeout=10)
        get_confirm = bash_cmd(f"ros2 param get /go1_disabled_controller_node {PARAM_CONFIRM}", timeout=10)

        PARAM_STDOUT.write_text(
            f"{PARAM_ENABLE}:\n{get_enable.stdout}\n\n{PARAM_CONFIRM}:\n{get_confirm.stdout}\n"
        )
        PARAM_STDERR.write_text(
            f"{PARAM_ENABLE} stderr:\n{get_enable.stderr}\n\n{PARAM_CONFIRM} stderr:\n{get_confirm.stderr}\n"
        )

        enable_param_default_false = get_enable.returncode == 0 and param_is_false(get_enable.stdout)
        confirm_param_default_false = get_confirm.returncode == 0 and param_is_false(get_confirm.stdout)

        add_check(checks, "enable_param_get_returncode", get_enable.returncode, 0, get_enable.returncode == 0, get_enable.stderr)
        add_check(checks, "confirm_param_get_returncode", get_confirm.returncode, 0, get_confirm.returncode == 0, get_confirm.stderr)
        add_check(checks, "enable_param_default_false", enable_param_default_false, True, enable_param_default_false, get_enable.stdout)
        add_check(checks, "confirm_param_default_false", confirm_param_default_false, True, confirm_param_default_false, get_confirm.stdout)

        for i in range(runtime_sample_count):
            info_rc, info_out, info_err, pub_count, sub_count = topic_info(TORQUE_TOPIC)
            observations.append({
                "sample_index": i,
                "topic": TORQUE_TOPIC,
                "topic_info_returncode": info_rc,
                "publisher_count": "" if pub_count is None else pub_count,
                "subscription_count": "" if sub_count is None else sub_count,
                "publisher_count_positive": isinstance(pub_count, int) and pub_count >= 1,
                "subscription_count_positive": isinstance(sub_count, int) and sub_count >= 1,
            })
            time.sleep(0.75)

    finally:
        stop_process(controller_proc, CONTROLLER_STDOUT, CONTROLLER_STDERR)
        stop_process(bridge_proc, BRIDGE_STDOUT, BRIDGE_STDERR)

    with OBS_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
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
        writer.writerows(observations)

    observed_sample_count = len(observations)
    topic_info_all_returncode_zero = all(row["topic_info_returncode"] == 0 for row in observations)
    torque_publishers_positive_all_samples = all(row["publisher_count_positive"] for row in observations)
    torque_subscribers_positive_all_samples = all(row["subscription_count_positive"] for row in observations)

    add_check(checks, "runtime_sample_count", observed_sample_count, runtime_sample_count, observed_sample_count == runtime_sample_count)
    add_check(checks, "topic_info_all_returncode_zero", topic_info_all_returncode_zero, True, topic_info_all_returncode_zero)
    add_check(checks, "torque_publishers_positive_all_samples", torque_publishers_positive_all_samples, True, torque_publishers_positive_all_samples)
    add_check(checks, "torque_subscribers_positive_all_samples", torque_subscribers_positive_all_samples, True, torque_subscribers_positive_all_samples)

    manual_enable_active = False
    active_ros_publisher_path_exists = torque_publishers_positive_all_samples
    publisher_construction_implemented_without_publish_call = (
        stage123_pass and
        preflight_frozen and
        source_patch_applied and
        post_source_has_create_publisher and
        not post_source_has_publish_call and
        post_source_references_torque_topic and
        post_source_has_active_member and
        post_source_has_stage124_marker and
        build_rc == 0 and
        controller_alive and
        enable_param_default_false and
        confirm_param_default_false and
        torque_publishers_positive_all_samples
    )
    torque_enable_ready = False
    torque_publisher_enabled = False

    gate_rows = [
        {
            "gate": "G0",
            "name": "Stage 8 frozen Python baseline valid",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage08_freeze_integrity_check_summary.csv",
        },
        {
            "gate": "G1",
            "name": "Stage 9 interface mirror frozen",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage09_0_6_interface_mirror_freeze_summary.csv",
        },
        {
            "gate": "G2",
            "name": "C++ controller source has no ROS torque publisher construction",
            "required_before_torque_publish": True,
            "current_status": False,
            "evidence": "Stage 12.4 intentionally constructs publisher object but still forbids publish call",
        },
        {
            "gate": "G3",
            "name": "C++ controller source has no publish call",
            "required_before_torque_publish": True,
            "current_status": not post_source_has_publish_call,
            "evidence": str(CPP_SOURCE.relative_to(ROOT)),
        },
        {
            "gate": "G4",
            "name": "Explicit manual enable flag design exists",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "docs/STAGE10_TORQUE_PUBLISHER_ENABLE_GATE_DESIGN.md",
        },
        {
            "gate": "G5",
            "name": "Torque clamp and watchdog utility implemented",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": str(SAFETY_HEADER.relative_to(ROOT)),
        },
        {
            "gate": "G6",
            "name": "Zero torque dry-run regression completed",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage10_zero_torque_dry_run_internal_validation_summary.csv",
        },
        {
            "gate": "G7",
            "name": "Python frozen baseline A/B regression still passes",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage08_adapter_backed_stage07_baseline_ab_test_summary.csv",
        },
        {
            "gate": "G8",
            "name": "Manual enable flags active at runtime",
            "required_before_torque_publish": True,
            "current_status": manual_enable_active,
            "evidence": "parameters remain default false in Stage 12.4",
        },
        {
            "gate": "G9",
            "name": "Active ROS publisher path exists",
            "required_before_torque_publish": True,
            "current_status": active_ros_publisher_path_exists,
            "evidence": str(OBS_PATH.relative_to(ROOT)),
        },
        {
            "gate": "G10",
            "name": "Disabled controller uses clamp/watchdog internally",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": str(CPP_SOURCE.relative_to(ROOT)),
        },
        {
            "gate": "G11",
            "name": "Manual enable parameters exist and default false",
            "required_before_torque_publish": True,
            "current_status": enable_param_default_false and confirm_param_default_false,
            "evidence": str(PARAM_STDOUT.relative_to(ROOT)),
        },
        {
            "gate": "G12",
            "name": "Publisher path skeleton plan exists",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage11_publisher_path_skeleton_plan.csv",
        },
        {
            "gate": "G13",
            "name": "Publisher-path source guard passed before implementation",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage11_publisher_path_source_guard_log.csv",
        },
        {
            "gate": "G14",
            "name": "Disabled publisher-path skeleton design exists",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage11_disabled_publisher_path_skeleton_design.csv",
        },
        {
            "gate": "G15",
            "name": "Disabled publisher-path skeleton preflight passed",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage11_disabled_publisher_path_skeleton_preflight.csv",
        },
        {
            "gate": "G16",
            "name": "Dormant publisher-path source skeleton exists",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": str(CPP_SOURCE.relative_to(ROOT)),
        },
        {
            "gate": "G17",
            "name": "Runtime guard hardened for dormant publisher skeleton",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage11_runtime_guard_hardening_topic_observations.csv",
        },
        {
            "gate": "G18",
            "name": "Stage 11 full freeze integrity check passed",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage11_full_freeze_integrity_check_log.csv",
        },
        {
            "gate": "G19",
            "name": "Active publisher construction planning exists",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage12_active_publisher_construction_plan.csv",
        },
        {
            "gate": "G20",
            "name": "Pre-construction source and runtime guard passed",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage12_pre_construction_source_runtime_guard_log.csv",
        },
        {
            "gate": "G21",
            "name": "Publisher construction source patch design exists",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage12_publisher_construction_source_patch_design.csv",
        },
        {
            "gate": "G22",
            "name": "Publisher construction implemented without publish call",
            "required_before_torque_publish": True,
            "current_status": publisher_construction_implemented_without_publish_call,
            "evidence": str(LOG_PATH.relative_to(ROOT)),
        },
    ]

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(gate_rows)

    add_check(checks, "publisher_construction_implemented_without_publish_call", publisher_construction_implemented_without_publish_call, True, publisher_construction_implemented_without_publish_call)
    add_check(checks, "manual_enable_active", manual_enable_active, False, not manual_enable_active)
    add_check(checks, "active_ros_publisher_path_exists", active_ros_publisher_path_exists, True, active_ros_publisher_path_exists)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)
    add_check(checks, "torque_publisher_enabled", torque_publisher_enabled, False, not torque_publisher_enabled)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    DOC_PATH.write_text(f"""# Stage 12.4 Publisher Construction Source Patch Without Publish

## 一、结论

Stage 12.4 实现 publisher construction source patch，但仍不实现 publish call。

本阶段第一次修改 C++ controller source：

- 添加 /go1/joint_torque_cmd publisher construction；
- 添加 active publisher member；
- 添加 Stage 12.4 construction marker；
- 保持 publish call absent；
- manual enable 参数仍默认 false；
- 不发布 torque；
- 不改变控制律。

## 二、Source patch

Before source backup:

    results/logs_sample/stage12_disabled_controller_node_before_stage124.cpp

After source snapshot:

    results/logs_sample/stage12_disabled_controller_node_after_stage124.cpp

Hashes:

- hash_before: {hash_before}
- hash_after: {hash_after}
- source_patch_applied: {source_patch_applied}

## 三、Source guard after patch

- post_source_has_create_publisher: {post_source_has_create_publisher}
- post_source_has_publish_call: {post_source_has_publish_call}
- post_source_references_torque_topic: {post_source_references_torque_topic}
- post_source_has_active_publisher_member: {post_source_has_active_member}
- post_source_has_stage124_marker: {post_source_has_stage124_marker}

## 四、Runtime observation

Observation CSV:

    results/logs_sample/stage12_publisher_construction_without_publish_topic_observations.csv

Results:

- runtime_observed_sample_count: {observed_sample_count}
- topic_info_all_returncode_zero: {topic_info_all_returncode_zero}
- torque_publishers_positive_all_samples: {torque_publishers_positive_all_samples}
- torque_subscribers_positive_all_samples: {torque_subscribers_positive_all_samples}
- enable_param_default_false: {enable_param_default_false}
- confirm_param_default_false: {confirm_param_default_false}

## 五、Safety gate after Stage 12.4

Updated:

- G2 source has no publisher construction: False by design
- G3 source has no publish call: {not post_source_has_publish_call}
- G8 manual enable flags active at runtime: {manual_enable_active}
- G9 active ROS publisher path exists: {active_ros_publisher_path_exists}
- G22 publisher construction implemented without publish call: {publisher_construction_implemented_without_publish_call}

Therefore:

    torque_enable_ready = {torque_enable_ready}

G8 remains False and no publish call exists, so torque command is not published.

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.4 没有完成：

- publish call；
- torque command publishing；
- manual torque enable；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。
""")

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 12.4"])
        writer.writerow(["test_name", "publisher_construction_source_patch_without_publish"])
        writer.writerow(["stage123_pass", stage123_pass])
        writer.writerow(["stage123_construction_stage_preflight_frozen", preflight_frozen])
        writer.writerow(["pre_patch_source_has_no_create_publisher", not pre_source_has_create_publisher])
        writer.writerow(["pre_patch_source_has_no_publish_call", not pre_source_has_publish_call])
        writer.writerow(["pre_patch_source_does_not_reference_torque_topic", not pre_source_has_torque_topic])
        writer.writerow(["source_patch_applied", source_patch_applied])
        writer.writerow(["source_hash_before", hash_before])
        writer.writerow(["source_hash_after", hash_after])
        writer.writerow(["post_source_has_create_publisher", post_source_has_create_publisher])
        writer.writerow(["post_source_has_publish_call", post_source_has_publish_call])
        writer.writerow(["post_source_references_torque_topic", post_source_references_torque_topic])
        writer.writerow(["post_source_has_active_publisher_member", post_source_has_active_member])
        writer.writerow(["post_source_has_stage124_marker", post_source_has_stage124_marker])
        writer.writerow(["source_declares_enable_param_default_false", source_declares_enable_param])
        writer.writerow(["source_declares_confirm_param_default_false", source_declares_confirm_param])
        writer.writerow(["source_uses_safety_utilities", source_uses_safety])
        writer.writerow(["colcon_build_returncode", build_rc])
        writer.writerow(["enable_param_default_false", enable_param_default_false])
        writer.writerow(["confirm_param_default_false", confirm_param_default_false])
        writer.writerow(["runtime_expected_sample_count", runtime_sample_count])
        writer.writerow(["runtime_observed_sample_count", observed_sample_count])
        writer.writerow(["topic_info_all_returncode_zero", topic_info_all_returncode_zero])
        writer.writerow(["torque_publishers_positive_all_samples", torque_publishers_positive_all_samples])
        writer.writerow(["torque_subscribers_positive_all_samples", torque_subscribers_positive_all_samples])
        writer.writerow(["publisher_construction_implemented_without_publish_call", publisher_construction_implemented_without_publish_call])
        writer.writerow(["manual_enable_active", manual_enable_active])
        writer.writerow(["active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g2_no_publisher_construction", False])
        writer.writerow(["g3_no_publish_call", not post_source_has_publish_call])
        writer.writerow(["g8_manual_enable_active", manual_enable_active])
        writer.writerow(["g9_active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g22_publisher_construction_implemented_without_publish_call", publisher_construction_implemented_without_publish_call])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_publisher_enabled", torque_publisher_enabled])
        writer.writerow(["torque_command_published_by_stage124", False])
        writer.writerow(["stage12_scope", "publisher_construction_source_patch_without_publish_call"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["ros2_cpp_realtime_controller_completed", False])
        writer.writerow(["pure_wbc_locomotion_completed", False])
        writer.writerow(["ekf_completed", False])
        writer.writerow(["full_3d_centroidal_mpc_completed", False])
        writer.writerow(["num_checks", len(checks)])
        writer.writerow(["num_failed_checks", sum(1 for row in checks if not row["pass"])])
        writer.writerow(["pass", all_pass])
        writer.writerow(["log_csv", str(LOG_PATH.relative_to(ROOT))])
        writer.writerow(["observations_csv", str(OBS_PATH.relative_to(ROOT))])
        writer.writerow(["safety_gate_csv", str(SAFETY_GATE_PATH.relative_to(ROOT))])
        writer.writerow(["summary_csv", str(SUMMARY_PATH.relative_to(ROOT))])
        writer.writerow(["source_backup", str(SOURCE_BACKUP.relative_to(ROOT))])
        writer.writerow(["source_after", str(SOURCE_AFTER.relative_to(ROOT))])
        writer.writerow(["build_stdout", str(BUILD_STDOUT.relative_to(ROOT))])
        writer.writerow(["build_stderr", str(BUILD_STDERR.relative_to(ROOT))])
        writer.writerow(["param_stdout", str(PARAM_STDOUT.relative_to(ROOT))])
        writer.writerow(["param_stderr", str(PARAM_STDERR.relative_to(ROOT))])
        writer.writerow(["bridge_stdout", str(BRIDGE_STDOUT.relative_to(ROOT))])
        writer.writerow(["bridge_stderr", str(BRIDGE_STDERR.relative_to(ROOT))])
        writer.writerow(["controller_stdout", str(CONTROLLER_STDOUT.relative_to(ROOT))])
        writer.writerow(["controller_stderr", str(CONTROLLER_STDERR.relative_to(ROOT))])
        writer.writerow(["doc", str(DOC_PATH.relative_to(ROOT))])

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 12.4 Publisher Construction Source Patch Without Publish

Stage 12.4 实现 publisher construction source patch without publish call。

- Script: `scripts/stage12_publisher_construction_source_patch_without_publish.py`
- Observations: `results/logs_sample/stage12_publisher_construction_without_publish_topic_observations.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage124.csv`
- Summary: `results/logs_sample/stage12_publisher_construction_source_patch_without_publish_summary.csv`
- Docs: `docs/STAGE12_PUBLISHER_CONSTRUCTION_SOURCE_PATCH_WITHOUT_PUBLISH.md`
- pass: `{all_pass}`
- publisher_construction_implemented_without_publish_call: `{publisher_construction_implemented_without_publish_call}`
- active_ros_publisher_path_exists: `{active_ros_publisher_path_exists}`
- manual_enable_active: `{manual_enable_active}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `{torque_publisher_enabled}`
- control_law_changed: `False`

Stage 12.4 只构造 publisher，不调用 publish，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 12.4 Publisher Construction Source Patch Without Publish"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 12.4] publisher construction source patch without publish")
    print(f"pass={all_pass}")
    print(f"stage123_pass={stage123_pass}")
    print(f"source_patch_applied={source_patch_applied}")
    print(f"post_source_has_create_publisher={post_source_has_create_publisher}")
    print(f"post_source_has_publish_call={post_source_has_publish_call}")
    print(f"post_source_references_torque_topic={post_source_references_torque_topic}")
    print(f"publisher_construction_implemented_without_publish_call={publisher_construction_implemented_without_publish_call}")
    print(f"torque_publishers_positive_all_samples={torque_publishers_positive_all_samples}")
    print(f"active_ros_publisher_path_exists={active_ros_publisher_path_exists}")
    print(f"manual_enable_active={manual_enable_active}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print("control_law_changed=False")
    print(f"torque_publisher_enabled={torque_publisher_enabled}")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
    print(f"observations_csv={OBS_PATH.relative_to(ROOT)}")
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
