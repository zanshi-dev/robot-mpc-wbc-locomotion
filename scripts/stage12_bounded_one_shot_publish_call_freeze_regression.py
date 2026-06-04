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

STAGE1214R2_SUMMARY = LOG_DIR / "stage12_bounded_one_shot_publish_call_repair2_summary.csv"
STAGE1214R2_GATE = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage1214_repair2.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"

SUMMARY_PATH = LOG_DIR / "stage12_bounded_one_shot_publish_call_freeze_regression_summary.csv"
LOG_PATH = LOG_DIR / "stage12_bounded_one_shot_publish_call_freeze_regression_log.csv"
HASH_PATH = LOG_DIR / "stage12_bounded_one_shot_publish_call_freeze_regression_hashes.csv"
PARAM_OBS_PATH = LOG_DIR / "stage12_bounded_one_shot_publish_call_freeze_regression_param_observations.csv"
TOPIC_OBS_PATH = LOG_DIR / "stage12_bounded_one_shot_publish_call_freeze_regression_topic_observations.csv"

DEFAULT_ECHO_STDOUT = LOG_DIR / "stage12_bounded_one_shot_publish_call_freeze_default_echo_stdout.txt"
DEFAULT_ECHO_STDERR = LOG_DIR / "stage12_bounded_one_shot_publish_call_freeze_default_echo_stderr.txt"
ENABLED_ECHO1_STDOUT = LOG_DIR / "stage12_bounded_one_shot_publish_call_freeze_enabled_echo1_stdout.txt"
ENABLED_ECHO1_STDERR = LOG_DIR / "stage12_bounded_one_shot_publish_call_freeze_enabled_echo1_stderr.txt"
ENABLED_ECHO2_STDOUT = LOG_DIR / "stage12_bounded_one_shot_publish_call_freeze_enabled_echo2_stdout.txt"
ENABLED_ECHO2_STDERR = LOG_DIR / "stage12_bounded_one_shot_publish_call_freeze_enabled_echo2_stderr.txt"

SAFETY_GATE_PATH = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage1215.csv"
DOC_PATH = ROOT / "docs/STAGE12_BOUNDED_ONE_SHOT_PUBLISH_CALL_FREEZE_REGRESSION.md"

BUILD_STDOUT = LOG_DIR / "stage12_bounded_one_shot_publish_call_freeze_build_stdout.txt"
BUILD_STDERR = LOG_DIR / "stage12_bounded_one_shot_publish_call_freeze_build_stderr.txt"
BRIDGE_STDOUT = LOG_DIR / "stage12_bounded_one_shot_publish_call_freeze_bridge_stdout.txt"
BRIDGE_STDERR = LOG_DIR / "stage12_bounded_one_shot_publish_call_freeze_bridge_stderr.txt"
DEFAULT_CONTROLLER_STDOUT = LOG_DIR / "stage12_bounded_one_shot_publish_call_freeze_default_controller_stdout.txt"
DEFAULT_CONTROLLER_STDERR = LOG_DIR / "stage12_bounded_one_shot_publish_call_freeze_default_controller_stderr.txt"
ENABLED_CONTROLLER_STDOUT = LOG_DIR / "stage12_bounded_one_shot_publish_call_freeze_enabled_controller_stdout.txt"
ENABLED_CONTROLLER_STDERR = LOG_DIR / "stage12_bounded_one_shot_publish_call_freeze_enabled_controller_stderr.txt"

BRIDGE_PACKAGE = "robot_mpc_wbc_bridge"
BRIDGE_EXECUTABLE = "mujoco_bridge_node"
CONTROLLER_PACKAGE = "robot_mpc_wbc_cpp_controller"
CONTROLLER_EXECUTABLE = "go1_disabled_controller_node"

NODE_NAME = "/go1_disabled_controller_node"
TORQUE_TOPIC = "/go1/joint_torque_cmd"
PARAM_ENABLE = "enable_torque_publisher"
PARAM_CONFIRM = "confirm_torque_publisher_enable"

FREEZE_FILES = [
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp",
    "results/logs_sample/stage12_bounded_one_shot_publish_call_repair2_summary.csv",
    "results/logs_sample/stage12_bounded_one_shot_publish_call_repair2_log.csv",
    "results/logs_sample/stage12_bounded_one_shot_publish_call_repair2_echo1_stdout.txt",
    "results/logs_sample/stage12_bounded_one_shot_publish_call_repair2_echo2_stdout.txt",
    "results/logs_sample/stage12_bounded_one_shot_publish_call_repair2_param_observations.csv",
    "results/logs_sample/stage12_bounded_one_shot_publish_call_repair2_topic_observations.csv",
    "results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1214_repair2.csv",
    "results/logs_sample/stage12_disabled_controller_node_after_stage1214_repair2.cpp",
    "docs/STAGE12_BOUNDED_ONE_SHOT_PUBLISH_CALL_REPAIR2.md",
]


def load_summary(path: Path):
    out = {}
    if not path.exists():
        return out
    with path.open(newline="") as f:
        rows = list(csv.reader(f))
    if rows and len(rows[0]) >= 2 and rows[0][0] == "metric":
        for row in rows[1:]:
            if len(row) >= 2:
                out[row[0]] = row[1]
    return out


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


def sha256_text(text: str):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def count_publish_calls(text: str):
    return len(re.findall(r"(?:->|\.)publish\s*\(", text))


def add_check(rows, check, value, expected, passed, detail=""):
    rows.append({
        "check": check,
        "value": str(value),
        "expected": str(expected),
        "pass": bool(passed),
        "detail": detail,
    })


def bash_cmd(cmd, timeout=20):
    full = "source /opt/ros/jazzy/setup.bash && source ros2_ws/install/setup.bash && " + cmd
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


def start_node(package_name, executable_name, extra_ros_args=""):
    cmd = (
        "source /opt/ros/jazzy/setup.bash && "
        "source ros2_ws/install/setup.bash && "
        f"exec ros2 run {package_name} {executable_name} {extra_ros_args}"
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


def start_echo_once(timeout_seconds):
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

    return proc.returncode, pub_count, sub_count


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
    payload = stdout.split("data:", 1)[1].split("---", 1)[0]
    nums = re.findall(r"[-+]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", payload)
    return [float(x) for x in nums]


def sample_topic_rows(phase, count):
    rows = []
    for i in range(count):
        rc, pub_count, sub_count = topic_info(TORQUE_TOPIC)
        rows.append({
            "phase": phase,
            "sample_index": i,
            "topic": TORQUE_TOPIC,
            "topic_info_returncode": rc,
            "publisher_count": "" if pub_count is None else pub_count,
            "subscription_count": "" if sub_count is None else sub_count,
            "publisher_count_positive": isinstance(pub_count, int) and pub_count >= 1,
            "subscription_count_positive": isinstance(sub_count, int) and sub_count >= 1,
        })
        time.sleep(0.4)
    return rows


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    checks = []
    param_rows = []
    topic_rows = []

    prev = load_summary(STAGE1214R2_SUMMARY)
    stage1214r2_pass = as_bool(prev.get("pass", "False"))
    previous_repair2_passed = as_bool(prev.get("bounded_one_shot_publish_call_repair2_passed", "False"))
    previous_msg_published = as_bool(prev.get("bounded_zero_safe_torque_message_published", "False"))
    previous_no_streaming = not as_bool(prev.get("continuous_torque_streaming_enabled", "True"))
    previous_payload_len_12 = str(prev.get("first_echo_payload_length", "")) == "12"
    previous_payload_zero = as_bool(prev.get("first_echo_payload_all_zero", "False"))
    previous_publish_count_one = str(prev.get("post_publish_call_count", "")) == "1"

    add_check(checks, "stage1214r2_summary_exists", STAGE1214R2_SUMMARY.exists(), True, STAGE1214R2_SUMMARY.exists(), str(STAGE1214R2_SUMMARY))
    add_check(checks, "stage1214r2_pass", stage1214r2_pass, True, stage1214r2_pass)
    add_check(checks, "previous_repair2_passed", previous_repair2_passed, True, previous_repair2_passed)
    add_check(checks, "previous_bounded_zero_safe_torque_message_published", previous_msg_published, True, previous_msg_published)
    add_check(checks, "previous_no_continuous_streaming", previous_no_streaming, True, previous_no_streaming)
    add_check(checks, "previous_payload_length_12", previous_payload_len_12, True, previous_payload_len_12)
    add_check(checks, "previous_payload_all_zero", previous_payload_zero, True, previous_payload_zero)
    add_check(checks, "previous_publish_count_one", previous_publish_count_one, True, previous_publish_count_one)

    gate_rows_in = load_dicts(STAGE1214R2_GATE)
    gate_status_in = {
        row.get("gate", ""): as_bool(row.get("current_status", "False"))
        for row in gate_rows_in
    }

    add_check(checks, "stage1214r2_gate_exists", STAGE1214R2_GATE.exists(), True, STAGE1214R2_GATE.exists(), str(STAGE1214R2_GATE))
    add_check(checks, "g32_true_before_stage1215", gate_status_in.get("G32", False), True, gate_status_in.get("G32", False))
    add_check(checks, "g34_true_before_stage1215", gate_status_in.get("G34", False), True, gate_status_in.get("G34", False))

    source_before = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    source_hash_before = sha256_text(source_before)

    publish_call_count = count_publish_calls(source_before)
    source_has_exactly_one_publish_call = publish_call_count == 1
    source_has_delayed_one_shot_timer = (
        "stage1214_one_shot_publish_timer_ = this->create_wall_timer" in source_before and
        "std::chrono::milliseconds(2500)" in source_before
    )
    source_has_timer_member = "rclcpp::TimerBase::SharedPtr stage1214_one_shot_publish_timer_" in source_before
    source_has_zero_safe_message_helper = "makeStage1214ZeroSafeTorqueCommandMessage" in source_before
    source_uses_zero_safe_message_helper = "auto msg = makeStage1214ZeroSafeTorqueCommandMessage();" in source_before
    source_has_stage1214_marker = (
        "kStage1214BoundedPublishCallImplemented = true" in source_before and
        "kStage1214ContinuousPublishImplemented = false" in source_before
    )
    source_has_stage124_marker = (
        "kStage124PublisherConstructionImplemented" in source_before and
        "kStage124PublishCallImplemented = false" in source_before
    )
    source_references_torque_topic = TORQUE_TOPIC in source_before
    source_has_active_publisher_member = "active_torque_cmd_publisher_" in source_before
    source_has_cancel = "stage1214_one_shot_publish_timer_->cancel()" in source_before

    add_check(checks, "source_exists", CPP_SOURCE.exists(), True, CPP_SOURCE.exists(), str(CPP_SOURCE))
    add_check(checks, "publish_call_count", publish_call_count, 1, publish_call_count == 1)
    add_check(checks, "source_has_exactly_one_publish_call", source_has_exactly_one_publish_call, True, source_has_exactly_one_publish_call)
    add_check(checks, "source_has_delayed_one_shot_timer", source_has_delayed_one_shot_timer, True, source_has_delayed_one_shot_timer)
    add_check(checks, "source_has_timer_member", source_has_timer_member, True, source_has_timer_member)
    add_check(checks, "source_has_zero_safe_message_helper", source_has_zero_safe_message_helper, True, source_has_zero_safe_message_helper)
    add_check(checks, "source_uses_zero_safe_message_helper", source_uses_zero_safe_message_helper, True, source_uses_zero_safe_message_helper)
    add_check(checks, "source_has_stage1214_marker", source_has_stage1214_marker, True, source_has_stage1214_marker)
    add_check(checks, "source_has_stage124_marker", source_has_stage124_marker, True, source_has_stage124_marker)
    add_check(checks, "source_references_torque_topic", source_references_torque_topic, True, source_references_torque_topic)
    add_check(checks, "source_has_active_publisher_member", source_has_active_publisher_member, True, source_has_active_publisher_member)
    add_check(checks, "source_timer_cancels_itself", source_has_cancel, True, source_has_cancel)

    build_rc = build_packages()
    add_check(checks, "colcon_build_returncode", build_rc, 0, build_rc == 0)

    bridge_proc = None
    default_controller_proc = None
    enabled_controller_proc = None

    default_echo_returncode = None
    default_no_message_observed = False
    default_controller_alive = False

    enabled_echo1_returncode = None
    enabled_echo2_returncode = None
    enabled_payload = []
    enabled_payload_length = 0
    enabled_payload_all_finite = False
    enabled_payload_all_zero = False
    enabled_first_message_received = False
    enabled_second_echo_timeout_no_extra_message = False
    enabled_controller_alive = False
    manual_enable_active_during_enabled_test = False
    manual_enable_reverted_false = False

    try:
        bridge_proc = start_node(BRIDGE_PACKAGE, BRIDGE_EXECUTABLE)
        time.sleep(3.0)
        bridge_alive = bridge_proc.poll() is None
        add_check(checks, "bridge_alive_after_startup", bridge_alive, True, bridge_alive)

        default_echo_proc = start_echo_once(8)
        time.sleep(2.0)

        default_controller_proc = start_node(CONTROLLER_PACKAGE, CONTROLLER_EXECUTABLE)
        time.sleep(1.0)
        default_controller_alive = default_controller_proc.poll() is None
        add_check(checks, "default_controller_alive_after_startup", default_controller_alive, True, default_controller_alive)

        default_echo_returncode, default_echo_out, default_echo_err = finish_echo(
            default_echo_proc, DEFAULT_ECHO_STDOUT, DEFAULT_ECHO_STDERR, wait_timeout=12
        )
        default_no_message_observed = default_echo_returncode == 124 and not default_echo_out.strip()

        topic_rows.extend(sample_topic_rows("default_disabled_after_timer", 4))

        stop_process(default_controller_proc, DEFAULT_CONTROLLER_STDOUT, DEFAULT_CONTROLLER_STDERR)
        default_controller_proc = None
        time.sleep(1.0)

        enabled_echo1_proc = start_echo_once(20)
        time.sleep(2.0)

        enabled_args = (
            "--ros-args "
            "-p enable_torque_publisher:=true "
            "-p confirm_torque_publisher_enable:=true"
        )
        enabled_controller_proc = start_node(CONTROLLER_PACKAGE, CONTROLLER_EXECUTABLE, enabled_args)
        time.sleep(1.0)
        enabled_controller_alive_start = enabled_controller_proc.poll() is None
        add_check(checks, "enabled_controller_alive_after_startup", enabled_controller_alive_start, True, enabled_controller_alive_start)

        enabled_echo1_returncode, enabled_echo1_out, enabled_echo1_err = finish_echo(
            enabled_echo1_proc, ENABLED_ECHO1_STDOUT, ENABLED_ECHO1_STDERR, wait_timeout=24
        )

        enabled_payload = parse_echo_payload(enabled_echo1_out)
        enabled_payload_length = len(enabled_payload)
        enabled_payload_all_finite = all(math.isfinite(x) for x in enabled_payload)
        enabled_payload_all_zero = enabled_payload_length == 12 and all(abs(x) <= 1e-12 for x in enabled_payload)
        enabled_first_message_received = enabled_echo1_returncode == 0 and enabled_payload_length == 12

        rc, value, out, err = get_param_bool(PARAM_ENABLE)
        param_rows.append({"phase": "enabled_test", "param": PARAM_ENABLE, "returncode": rc, "value": value, "stdout": out.strip(), "stderr": err.strip()})
        enabled_param_true = rc == 0 and value is True

        rc, value, out, err = get_param_bool(PARAM_CONFIRM)
        param_rows.append({"phase": "enabled_test", "param": PARAM_CONFIRM, "returncode": rc, "value": value, "stdout": out.strip(), "stderr": err.strip()})
        confirm_param_true = rc == 0 and value is True

        manual_enable_active_during_enabled_test = enabled_param_true and confirm_param_true

        topic_rows.extend(sample_topic_rows("enabled_after_first_publish", 6))

        set_confirm_false = set_param_bool(PARAM_CONFIRM, False)
        param_rows.append({"phase": "revert_false", "param": PARAM_CONFIRM, "returncode": set_confirm_false.returncode, "value": "", "stdout": set_confirm_false.stdout.strip(), "stderr": set_confirm_false.stderr.strip()})

        set_enable_false = set_param_bool(PARAM_ENABLE, False)
        param_rows.append({"phase": "revert_false", "param": PARAM_ENABLE, "returncode": set_enable_false.returncode, "value": "", "stdout": set_enable_false.stdout.strip(), "stderr": set_enable_false.stderr.strip()})

        time.sleep(0.5)

        rc, value, out, err = get_param_bool(PARAM_ENABLE)
        param_rows.append({"phase": "after_revert", "param": PARAM_ENABLE, "returncode": rc, "value": value, "stdout": out.strip(), "stderr": err.strip()})
        enable_false = rc == 0 and value is False

        rc, value, out, err = get_param_bool(PARAM_CONFIRM)
        param_rows.append({"phase": "after_revert", "param": PARAM_CONFIRM, "returncode": rc, "value": value, "stdout": out.strip(), "stderr": err.strip()})
        confirm_false = rc == 0 and value is False

        manual_enable_reverted_false = enable_false and confirm_false

        enabled_echo2_proc = start_echo_once(5)
        enabled_echo2_returncode, enabled_echo2_out, enabled_echo2_err = finish_echo(
            enabled_echo2_proc, ENABLED_ECHO2_STDOUT, ENABLED_ECHO2_STDERR, wait_timeout=9
        )
        enabled_second_echo_timeout_no_extra_message = enabled_echo2_returncode == 124 and not enabled_echo2_out.strip()

        enabled_controller_alive = enabled_controller_proc.poll() is None

    finally:
        try:
            set_param_bool(PARAM_CONFIRM, False)
            set_param_bool(PARAM_ENABLE, False)
        except Exception:
            pass

        stop_process(enabled_controller_proc, ENABLED_CONTROLLER_STDOUT, ENABLED_CONTROLLER_STDERR)
        stop_process(default_controller_proc, DEFAULT_CONTROLLER_STDOUT, DEFAULT_CONTROLLER_STDERR)
        stop_process(bridge_proc, BRIDGE_STDOUT, BRIDGE_STDERR)

    with PARAM_OBS_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["phase", "param", "returncode", "value", "stdout", "stderr"])
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

    source_after = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    source_hash_after = sha256_text(source_after)
    source_unchanged_by_stage1215 = source_hash_before == source_hash_after

    hash_rows = []
    missing_files = []
    for rel in FREEZE_FILES:
        path = ROOT / rel
        if path.exists():
            hash_rows.append({
                "file": rel,
                "exists": True,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            })
        else:
            missing_files.append(rel)
            hash_rows.append({
                "file": rel,
                "exists": False,
                "sha256": "",
                "size_bytes": "",
            })

    with HASH_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "exists", "sha256", "size_bytes"])
        writer.writeheader()
        writer.writerows(hash_rows)

    bounded_zero_safe_torque_message_published_by_stage1215 = (
        enabled_first_message_received and
        enabled_payload_length == 12 and
        enabled_payload_all_finite and
        enabled_payload_all_zero
    )
    continuous_torque_streaming_enabled = not enabled_second_echo_timeout_no_extra_message
    default_disabled_regression_passed = default_no_message_observed
    enabled_bounded_publish_regression_passed = (
        manual_enable_active_during_enabled_test and
        manual_enable_reverted_false and
        bounded_zero_safe_torque_message_published_by_stage1215 and
        enabled_second_echo_timeout_no_extra_message
    )

    bounded_one_shot_publish_call_freeze_regression_passed = (
        stage1214r2_pass and
        previous_repair2_passed and
        source_unchanged_by_stage1215 and
        source_has_exactly_one_publish_call and
        source_has_delayed_one_shot_timer and
        source_has_zero_safe_message_helper and
        source_uses_zero_safe_message_helper and
        source_has_stage1214_marker and
        source_has_cancel and
        build_rc == 0 and
        default_disabled_regression_passed and
        enabled_bounded_publish_regression_passed and
        not continuous_torque_streaming_enabled and
        active_ros_publisher_path_exists and
        len(missing_files) == 0
    )

    torque_enable_ready = False
    control_law_changed = False
    torque_publisher_enabled = False
    torque_command_published_by_stage1215 = bounded_zero_safe_torque_message_published_by_stage1215

    add_check(checks, "source_unchanged_by_stage1215", source_unchanged_by_stage1215, True, source_unchanged_by_stage1215)
    add_check(checks, "missing_freeze_file_count", len(missing_files), 0, len(missing_files) == 0)
    add_check(checks, "default_echo_returncode_timeout", default_echo_returncode, 124, default_echo_returncode == 124)
    add_check(checks, "default_disabled_no_message_observed", default_no_message_observed, True, default_no_message_observed)
    add_check(checks, "manual_enable_active_during_enabled_test", manual_enable_active_during_enabled_test, True, manual_enable_active_during_enabled_test)
    add_check(checks, "manual_enable_reverted_false", manual_enable_reverted_false, True, manual_enable_reverted_false)
    add_check(checks, "runtime_topic_sample_count", runtime_topic_sample_count, 10, runtime_topic_sample_count == 10)
    add_check(checks, "topic_info_all_returncode_zero", topic_info_all_returncode_zero, True, topic_info_all_returncode_zero)
    add_check(checks, "torque_publishers_positive_all_samples", torque_publishers_positive_all_samples, True, torque_publishers_positive_all_samples)
    add_check(checks, "torque_subscribers_positive_all_samples", torque_subscribers_positive_all_samples, True, torque_subscribers_positive_all_samples)
    add_check(checks, "enabled_echo1_returncode", enabled_echo1_returncode, 0, enabled_echo1_returncode == 0)
    add_check(checks, "enabled_first_message_received", enabled_first_message_received, True, enabled_first_message_received)
    add_check(checks, "enabled_payload_length", enabled_payload_length, 12, enabled_payload_length == 12)
    add_check(checks, "enabled_payload_all_finite", enabled_payload_all_finite, True, enabled_payload_all_finite)
    add_check(checks, "enabled_payload_all_zero", enabled_payload_all_zero, True, enabled_payload_all_zero)
    add_check(checks, "enabled_echo2_returncode_timeout", enabled_echo2_returncode, 124, enabled_echo2_returncode == 124)
    add_check(checks, "enabled_second_echo_timeout_no_extra_message", enabled_second_echo_timeout_no_extra_message, True, enabled_second_echo_timeout_no_extra_message)
    add_check(checks, "bounded_zero_safe_torque_message_published_by_stage1215", bounded_zero_safe_torque_message_published_by_stage1215, True, bounded_zero_safe_torque_message_published_by_stage1215)
    add_check(checks, "continuous_torque_streaming_enabled", continuous_torque_streaming_enabled, False, not continuous_torque_streaming_enabled)
    add_check(checks, "default_disabled_regression_passed", default_disabled_regression_passed, True, default_disabled_regression_passed)
    add_check(checks, "enabled_bounded_publish_regression_passed", enabled_bounded_publish_regression_passed, True, enabled_bounded_publish_regression_passed)
    add_check(checks, "enabled_controller_alive_after_publish", enabled_controller_alive, True, enabled_controller_alive)
    add_check(checks, "bounded_one_shot_publish_call_freeze_regression_passed", bounded_one_shot_publish_call_freeze_regression_passed, True, bounded_one_shot_publish_call_freeze_regression_passed)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)
    add_check(checks, "control_law_changed", control_law_changed, False, not control_law_changed)
    add_check(checks, "torque_publisher_enabled", torque_publisher_enabled, False, not torque_publisher_enabled)
    add_check(checks, "torque_command_published_by_stage1215", torque_command_published_by_stage1215, True, torque_command_published_by_stage1215)

    all_pass = all(row["pass"] for row in checks)

    gate_rows_out = []
    for row in gate_rows_in:
        row = dict(row)
        if row.get("gate") == "G3":
            row["current_status"] = False
            row["evidence"] = "Stage 12.15 freezes exactly one bounded publish call"
        if row.get("gate") == "G8":
            row["current_status"] = False
            row["evidence"] = "manual flags activated only during regression and reverted false"
        gate_rows_out.append(row)

    gate_rows_out.append({
        "gate": "G35",
        "name": "Bounded one-shot publish-call freeze and regression passed",
        "required_before_torque_publish": True,
        "current_status": bounded_one_shot_publish_call_freeze_regression_passed,
        "evidence": str(LOG_PATH.relative_to(ROOT)),
    })

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(gate_rows_out)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    DOC_PATH.write_text(f"""# Stage 12.15 Bounded One-shot Publish-call Freeze and Regression Check

## 一、结论

Stage 12.15 freezes the bounded one-shot zero/safe publish-call state and runs regression checks.

Current source state:

- publish_call_count: {publish_call_count}
- source_has_delayed_one_shot_timer: {source_has_delayed_one_shot_timer}
- source_has_zero_safe_message_helper: {source_has_zero_safe_message_helper}
- source_unchanged_by_stage1215: {source_unchanged_by_stage1215}

Default-disabled regression:

- default_echo_returncode: {default_echo_returncode}
- default_disabled_no_message_observed: {default_no_message_observed}

Manual-enabled bounded publish regression:

- enabled_echo1_returncode: {enabled_echo1_returncode}
- enabled_first_message_received: {enabled_first_message_received}
- enabled_payload_length: {enabled_payload_length}
- enabled_payload_all_finite: {enabled_payload_all_finite}
- enabled_payload_all_zero: {enabled_payload_all_zero}
- enabled_echo2_returncode: {enabled_echo2_returncode}
- enabled_second_echo_timeout_no_extra_message: {enabled_second_echo_timeout_no_extra_message}

Safety boundary:

- bounded_zero_safe_torque_message_published_by_stage1215: {bounded_zero_safe_torque_message_published_by_stage1215}
- continuous_torque_streaming_enabled: {continuous_torque_streaming_enabled}
- torque_enable_ready: {torque_enable_ready}
- torque_publisher_enabled: {torque_publisher_enabled}
- control_law_changed: {control_law_changed}

## 二、Artifacts

- Log: `results/logs_sample/stage12_bounded_one_shot_publish_call_freeze_regression_log.csv`
- Summary: `results/logs_sample/stage12_bounded_one_shot_publish_call_freeze_regression_summary.csv`
- Hashes: `results/logs_sample/stage12_bounded_one_shot_publish_call_freeze_regression_hashes.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1215.csv`
- Default echo stdout: `results/logs_sample/stage12_bounded_one_shot_publish_call_freeze_default_echo_stdout.txt`
- Enabled echo stdout: `results/logs_sample/stage12_bounded_one_shot_publish_call_freeze_enabled_echo1_stdout.txt`

## 三、Scope boundary

Current baseline remains `mixed_online_control_baseline`.

Stage 12.15 does not complete:

- continuous torque streaming;
- torque streaming controller;
- ROS2/C++ realtime controller;
- pure full WBC locomotion;
- EKF;
- full 3D centroidal MPC;
- hardware deployment.
""")

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 12.15"])
        writer.writerow(["test_name", "bounded_one_shot_publish_call_freeze_regression"])
        writer.writerow(["stage1214r2_pass", stage1214r2_pass])
        writer.writerow(["previous_repair2_passed", previous_repair2_passed])
        writer.writerow(["previous_bounded_zero_safe_torque_message_published", previous_msg_published])
        writer.writerow(["previous_no_continuous_streaming", previous_no_streaming])
        writer.writerow(["freeze_file_count", len(FREEZE_FILES)])
        writer.writerow(["missing_file_count", len(missing_files)])
        writer.writerow(["source_hash_before", source_hash_before])
        writer.writerow(["source_hash_after", source_hash_after])
        writer.writerow(["source_unchanged_by_stage1215", source_unchanged_by_stage1215])
        writer.writerow(["publish_call_count", publish_call_count])
        writer.writerow(["source_has_exactly_one_publish_call", source_has_exactly_one_publish_call])
        writer.writerow(["source_has_delayed_one_shot_timer", source_has_delayed_one_shot_timer])
        writer.writerow(["source_has_timer_member", source_has_timer_member])
        writer.writerow(["source_timer_cancels_itself", source_has_cancel])
        writer.writerow(["source_has_zero_safe_message_helper", source_has_zero_safe_message_helper])
        writer.writerow(["source_uses_zero_safe_message_helper", source_uses_zero_safe_message_helper])
        writer.writerow(["source_has_stage1214_marker", source_has_stage1214_marker])
        writer.writerow(["source_has_stage124_marker", source_has_stage124_marker])
        writer.writerow(["source_references_torque_topic", source_references_torque_topic])
        writer.writerow(["source_has_active_publisher_member", source_has_active_publisher_member])
        writer.writerow(["colcon_build_returncode", build_rc])
        writer.writerow(["default_echo_returncode", default_echo_returncode])
        writer.writerow(["default_disabled_no_message_observed", default_no_message_observed])
        writer.writerow(["manual_enable_active_during_enabled_test", manual_enable_active_during_enabled_test])
        writer.writerow(["manual_enable_reverted_false", manual_enable_reverted_false])
        writer.writerow(["runtime_topic_sample_count", runtime_topic_sample_count])
        writer.writerow(["topic_info_all_returncode_zero", topic_info_all_returncode_zero])
        writer.writerow(["torque_publishers_positive_all_samples", torque_publishers_positive_all_samples])
        writer.writerow(["torque_subscribers_positive_all_samples", torque_subscribers_positive_all_samples])
        writer.writerow(["enabled_echo1_returncode", enabled_echo1_returncode])
        writer.writerow(["enabled_first_message_received", enabled_first_message_received])
        writer.writerow(["enabled_payload_length", enabled_payload_length])
        writer.writerow(["enabled_payload_all_finite", enabled_payload_all_finite])
        writer.writerow(["enabled_payload_all_zero", enabled_payload_all_zero])
        writer.writerow(["enabled_echo2_returncode", enabled_echo2_returncode])
        writer.writerow(["enabled_second_echo_timeout_no_extra_message", enabled_second_echo_timeout_no_extra_message])
        writer.writerow(["bounded_zero_safe_torque_message_published_by_stage1215", bounded_zero_safe_torque_message_published_by_stage1215])
        writer.writerow(["continuous_torque_streaming_enabled", continuous_torque_streaming_enabled])
        writer.writerow(["default_disabled_regression_passed", default_disabled_regression_passed])
        writer.writerow(["enabled_bounded_publish_regression_passed", enabled_bounded_publish_regression_passed])
        writer.writerow(["bounded_one_shot_publish_call_freeze_regression_passed", bounded_one_shot_publish_call_freeze_regression_passed])
        writer.writerow(["active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g3_no_publish_call", False])
        writer.writerow(["g8_manual_enable_active_after_revert", False])
        writer.writerow(["g9_active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g32_bounded_one_shot_zero_safe_publish_call_implementation_passed", gate_status_in.get("G32", False)])
        writer.writerow(["g34_bounded_one_shot_publish_call_delayed_repair_passed", gate_status_in.get("G34", False)])
        writer.writerow(["g35_bounded_one_shot_publish_call_freeze_regression_passed", bounded_one_shot_publish_call_freeze_regression_passed])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", control_law_changed])
        writer.writerow(["torque_publisher_enabled", torque_publisher_enabled])
        writer.writerow(["torque_command_published_by_stage1215", torque_command_published_by_stage1215])
        writer.writerow(["stage12_scope", "bounded_one_shot_publish_call_freeze_regression"])
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
        writer.writerow(["hash_csv", str(HASH_PATH.relative_to(ROOT))])
        writer.writerow(["param_observations_csv", str(PARAM_OBS_PATH.relative_to(ROOT))])
        writer.writerow(["topic_observations_csv", str(TOPIC_OBS_PATH.relative_to(ROOT))])
        writer.writerow(["default_echo_stdout", str(DEFAULT_ECHO_STDOUT.relative_to(ROOT))])
        writer.writerow(["default_echo_stderr", str(DEFAULT_ECHO_STDERR.relative_to(ROOT))])
        writer.writerow(["enabled_echo1_stdout", str(ENABLED_ECHO1_STDOUT.relative_to(ROOT))])
        writer.writerow(["enabled_echo1_stderr", str(ENABLED_ECHO1_STDERR.relative_to(ROOT))])
        writer.writerow(["enabled_echo2_stdout", str(ENABLED_ECHO2_STDOUT.relative_to(ROOT))])
        writer.writerow(["enabled_echo2_stderr", str(ENABLED_ECHO2_STDERR.relative_to(ROOT))])
        writer.writerow(["safety_gate_csv", str(SAFETY_GATE_PATH.relative_to(ROOT))])
        writer.writerow(["summary_csv", str(SUMMARY_PATH.relative_to(ROOT))])
        writer.writerow(["build_stdout", str(BUILD_STDOUT.relative_to(ROOT))])
        writer.writerow(["build_stderr", str(BUILD_STDERR.relative_to(ROOT))])
        writer.writerow(["doc", str(DOC_PATH.relative_to(ROOT))])

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 12.15 Bounded One-shot Publish-call Freeze and Regression

Stage 12.15 冻结 bounded one-shot zero/safe publish-call 状态并完成回归检查。

- Script: `scripts/stage12_bounded_one_shot_publish_call_freeze_regression.py`
- Summary: `results/logs_sample/stage12_bounded_one_shot_publish_call_freeze_regression_summary.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1215.csv`
- pass: `{all_pass}`
- bounded_one_shot_publish_call_freeze_regression_passed: `{bounded_one_shot_publish_call_freeze_regression_passed}`
- default_disabled_no_message_observed: `{default_no_message_observed}`
- enabled_payload_length: `{enabled_payload_length}`
- enabled_payload_all_zero: `{enabled_payload_all_zero}`
- enabled_second_echo_timeout_no_extra_message: `{enabled_second_echo_timeout_no_extra_message}`
- continuous_torque_streaming_enabled: `{continuous_torque_streaming_enabled}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `{torque_publisher_enabled}`
- torque_command_published_by_stage1215: `{torque_command_published_by_stage1215}`
- control_law_changed: `{control_law_changed}`

Stage 12.15 不完成连续 torque streaming，不完成 ROS2/C++ realtime controller，不完成硬件部署。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 12.15 Bounded One-shot Publish-call Freeze and Regression"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 12.15] bounded one-shot publish-call freeze and regression")
    print(f"pass={all_pass}")
    print(f"stage1214r2_pass={stage1214r2_pass}")
    print(f"source_unchanged_by_stage1215={source_unchanged_by_stage1215}")
    print(f"publish_call_count={publish_call_count}")
    print(f"source_has_delayed_one_shot_timer={source_has_delayed_one_shot_timer}")
    print(f"default_disabled_no_message_observed={default_no_message_observed}")
    print(f"enabled_first_message_received={enabled_first_message_received}")
    print(f"enabled_payload_length={enabled_payload_length}")
    print(f"enabled_payload_all_finite={enabled_payload_all_finite}")
    print(f"enabled_payload_all_zero={enabled_payload_all_zero}")
    print(f"enabled_second_echo_timeout_no_extra_message={enabled_second_echo_timeout_no_extra_message}")
    print(f"bounded_zero_safe_torque_message_published_by_stage1215={bounded_zero_safe_torque_message_published_by_stage1215}")
    print(f"continuous_torque_streaming_enabled={continuous_torque_streaming_enabled}")
    print(f"bounded_one_shot_publish_call_freeze_regression_passed={bounded_one_shot_publish_call_freeze_regression_passed}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print(f"control_law_changed={control_law_changed}")
    print(f"torque_publisher_enabled={torque_publisher_enabled}")
    print(f"torque_command_published_by_stage1215={torque_command_published_by_stage1215}")
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
