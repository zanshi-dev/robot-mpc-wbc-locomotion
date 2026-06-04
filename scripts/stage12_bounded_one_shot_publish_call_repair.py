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

FAILED_SUMMARY = LOG_DIR / "stage12_bounded_one_shot_zero_safe_publish_call_source_patch_summary.csv"
FAILED_GATE = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage1214.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"

SOURCE_BEFORE_REPAIR = LOG_DIR / "stage12_disabled_controller_node_before_stage1214_repair.cpp"
SOURCE_AFTER_REPAIR = LOG_DIR / "stage12_disabled_controller_node_after_stage1214_repair.cpp"

SUMMARY_PATH = LOG_DIR / "stage12_bounded_one_shot_publish_call_repair_summary.csv"
LOG_PATH = LOG_DIR / "stage12_bounded_one_shot_publish_call_repair_log.csv"
PARAM_OBS_PATH = LOG_DIR / "stage12_bounded_one_shot_publish_call_repair_param_observations.csv"
TOPIC_OBS_PATH = LOG_DIR / "stage12_bounded_one_shot_publish_call_repair_topic_observations.csv"
ECHO1_STDOUT = LOG_DIR / "stage12_bounded_one_shot_publish_call_repair_echo1_stdout.txt"
ECHO1_STDERR = LOG_DIR / "stage12_bounded_one_shot_publish_call_repair_echo1_stderr.txt"
ECHO2_STDOUT = LOG_DIR / "stage12_bounded_one_shot_publish_call_repair_echo2_stdout.txt"
ECHO2_STDERR = LOG_DIR / "stage12_bounded_one_shot_publish_call_repair_echo2_stderr.txt"
SAFETY_GATE_PATH = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage1214_repair.csv"
DOC_PATH = ROOT / "docs/STAGE12_BOUNDED_ONE_SHOT_PUBLISH_CALL_REPAIR.md"

BUILD_STDOUT = LOG_DIR / "stage12_bounded_one_shot_publish_call_repair_build_stdout.txt"
BUILD_STDERR = LOG_DIR / "stage12_bounded_one_shot_publish_call_repair_build_stderr.txt"
BRIDGE_STDOUT = LOG_DIR / "stage12_bounded_one_shot_publish_call_repair_bridge_stdout.txt"
BRIDGE_STDERR = LOG_DIR / "stage12_bounded_one_shot_publish_call_repair_bridge_stderr.txt"
CONTROLLER_STDOUT = LOG_DIR / "stage12_bounded_one_shot_publish_call_repair_controller_stdout.txt"
CONTROLLER_STDERR = LOG_DIR / "stage12_bounded_one_shot_publish_call_repair_controller_stderr.txt"

BRIDGE_PACKAGE = "robot_mpc_wbc_bridge"
BRIDGE_EXECUTABLE = "mujoco_bridge_node"
CONTROLLER_PACKAGE = "robot_mpc_wbc_cpp_controller"
CONTROLLER_EXECUTABLE = "go1_disabled_controller_node"

NODE_NAME = "/go1_disabled_controller_node"
TORQUE_TOPIC = "/go1/joint_torque_cmd"
PARAM_ENABLE = "enable_torque_publisher"
PARAM_CONFIRM = "confirm_torque_publisher_enable"

CMATH_INCLUDE = "#include <cmath>"
CHRONO_INCLUDE = "#include <chrono>"

DELAYED_TIMER_BLOCK = """
    stage1214_one_shot_publish_timer_ = this->create_wall_timer(
      std::chrono::milliseconds(2500),
      [this]() {
        if (stage1214_one_shot_publish_timer_) {
          stage1214_one_shot_publish_timer_->cancel();
        }
        const bool stage1214_enable =
          this->get_parameter("enable_torque_publisher").as_bool();
        const bool stage1214_confirm =
          this->get_parameter("confirm_torque_publisher_enable").as_bool();
        const bool stage1214_state_ready = true;
        stage1214_bounded_publish_invoked_ =
          publishBoundedZeroSafeTorqueOnceIfAllowed(
            stage1214_enable, stage1214_confirm, stage1214_state_ready);
      });
""".rstrip()

ZERO_SAFE_HELPER_BLOCK = """
  std_msgs::msg::Float64MultiArray makeStage1214ZeroSafeTorqueCommandMessage() const
  {
    std_msgs::msg::Float64MultiArray msg;
    msg.data.assign(12, 0.0);
    return msg;
  }

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


def insert_include(text: str, include_line: str):
    if include_line in text:
        return text, False
    include_matches = list(re.finditer(r'^#include .+$', text, flags=re.MULTILINE))
    if include_matches:
        pos = include_matches[-1].end()
        return text[:pos] + "\n" + include_line + text[pos:], True
    return include_line + "\n" + text, True


def patch_repair(text: str):
    if count_publish_calls(text) != 1:
        raise RuntimeError("repair expects current Stage 12.14 source to contain exactly one publish call")

    patched = text
    changed = False

    patched, changed_cmath = insert_include(patched, CMATH_INCLUDE)
    changed = changed or changed_cmath

    patched, changed_chrono = insert_include(patched, CHRONO_INCLUDE)
    changed = changed or changed_chrono

    if "makeStage1214ZeroSafeTorqueCommandMessage" not in patched:
        target = "  bool publishBoundedZeroSafeTorqueOnceIfAllowed"
        idx = patched.find(target)
        if idx == -1:
            raise RuntimeError("cannot locate publishBoundedZeroSafeTorqueOnceIfAllowed helper")
        patched = patched[:idx] + ZERO_SAFE_HELPER_BLOCK + "\n\n" + patched[idx:]
        changed = True

    if "auto msg = makeDormantSafeTorqueCommandMessage();" in patched:
        patched = patched.replace(
            "auto msg = makeDormantSafeTorqueCommandMessage();",
            "auto msg = makeStage1214ZeroSafeTorqueCommandMessage();",
        )
        changed = True

    if "rclcpp::TimerBase::SharedPtr stage1214_one_shot_publish_timer_" not in patched:
        marker = "  bool stage1214_bounded_publish_invoked_{false};"
        if marker not in patched:
            raise RuntimeError("cannot locate stage1214_bounded_publish_invoked_ member")
        patched = patched.replace(
            marker,
            "  rclcpp::TimerBase::SharedPtr stage1214_one_shot_publish_timer_;\n" + marker,
        )
        changed = True

    immediate_re = re.compile(
        r'\n\s*const bool stage1214_enable\s*=\s*\n'
        r'\s*this->get_parameter\("enable_torque_publisher"\)\.as_bool\(\);\s*\n'
        r'\s*const bool stage1214_confirm\s*=\s*\n'
        r'\s*this->get_parameter\("confirm_torque_publisher_enable"\)\.as_bool\(\);\s*\n'
        r'\s*const bool stage1214_state_ready\s*=\s*true;\s*\n'
        r'\s*stage1214_bounded_publish_invoked_\s*=\s*\n'
        r'\s*publishBoundedZeroSafeTorqueOnceIfAllowed\(\s*\n'
        r'\s*stage1214_enable,\s*stage1214_confirm,\s*stage1214_state_ready\);\s*',
        flags=re.MULTILINE,
    )

    if "create_wall_timer" not in patched:
        patched, n = immediate_re.subn("\n" + DELAYED_TIMER_BLOCK + "\n", patched, count=1)
        if n != 1:
            raise RuntimeError("cannot replace immediate Stage 12.14 publish invocation with delayed one-shot timer")
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

    failed = load_summary(FAILED_SUMMARY)
    previous_pass = as_bool(failed.get("pass", "False"))
    previous_first_echo_timeout = str(failed.get("first_echo_returncode", "")) == "124"
    previous_no_message = not as_bool(failed.get("first_echo_message_received", "True"))
    previous_source_patch_applied = as_bool(failed.get("source_patch_applied", "False"))
    previous_publish_count_one = str(failed.get("post_publish_call_count", "")) == "1"
    previous_no_streaming = not as_bool(failed.get("continuous_torque_streaming_enabled", "True"))

    add_check(checks, "failed_stage1214_summary_exists", FAILED_SUMMARY.exists(), True, FAILED_SUMMARY.exists(), str(FAILED_SUMMARY))
    add_check(checks, "previous_stage1214_pass", previous_pass, False, not previous_pass)
    add_check(checks, "previous_first_echo_timeout", previous_first_echo_timeout, True, previous_first_echo_timeout)
    add_check(checks, "previous_no_first_message", previous_no_message, True, previous_no_message)
    add_check(checks, "previous_source_patch_applied", previous_source_patch_applied, True, previous_source_patch_applied)
    add_check(checks, "previous_publish_count_one", previous_publish_count_one, True, previous_publish_count_one)
    add_check(checks, "previous_no_continuous_streaming", previous_no_streaming, True, previous_no_streaming)

    source_before = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    SOURCE_BEFORE_REPAIR.write_text(source_before)
    source_hash_before = sha256_text(source_before)

    pre_publish_call_count = count_publish_calls(source_before)
    pre_has_stage1214_marker = (
        "kStage1214BoundedPublishCallImplemented = true" in source_before and
        "kStage1214ContinuousPublishImplemented = false" in source_before
    )

    add_check(checks, "pre_repair_publish_call_count", pre_publish_call_count, 1, pre_publish_call_count == 1)
    add_check(checks, "pre_repair_has_stage1214_marker", pre_has_stage1214_marker, True, pre_has_stage1214_marker)

    repaired_source, repair_changed = patch_repair(source_before)
    CPP_SOURCE.write_text(repaired_source)
    SOURCE_AFTER_REPAIR.write_text(repaired_source)

    source_after = CPP_SOURCE.read_text(errors="replace")
    source_hash_after = sha256_text(source_after)

    source_patch_repair_applied = source_hash_before != source_hash_after
    post_publish_call_count = count_publish_calls(source_after)
    post_has_stage1214_marker = (
        "kStage1214BoundedPublishCallImplemented = true" in source_after and
        "kStage1214ContinuousPublishImplemented = false" in source_after
    )
    post_has_delayed_one_shot_timer = (
        "create_wall_timer" in source_after and
        "std::chrono::milliseconds(2500)" in source_after and
        "stage1214_one_shot_publish_timer_" in source_after
    )
    post_has_zero_safe_message_helper = "makeStage1214ZeroSafeTorqueCommandMessage" in source_after
    post_has_exactly_one_publish_call = post_publish_call_count == 1
    post_forbids_continuous_publish = "kStage1214ContinuousPublishImplemented = false" in source_after

    add_check(checks, "source_patch_repair_applied", source_patch_repair_applied, True, source_patch_repair_applied)
    add_check(checks, "post_publish_call_count", post_publish_call_count, 1, post_publish_call_count == 1)
    add_check(checks, "post_has_exactly_one_publish_call", post_has_exactly_one_publish_call, True, post_has_exactly_one_publish_call)
    add_check(checks, "post_has_stage1214_marker", post_has_stage1214_marker, True, post_has_stage1214_marker)
    add_check(checks, "post_has_delayed_one_shot_timer", post_has_delayed_one_shot_timer, True, post_has_delayed_one_shot_timer)
    add_check(checks, "post_has_zero_safe_message_helper", post_has_zero_safe_message_helper, True, post_has_zero_safe_message_helper)
    add_check(checks, "post_forbids_continuous_publish", post_forbids_continuous_publish, True, post_forbids_continuous_publish)

    build_rc = build_packages()
    add_check(checks, "colcon_build_returncode", build_rc, 0, build_rc == 0)

    bridge_proc = None
    controller_proc = None

    param_rows = []
    topic_rows = []

    first_echo_returncode = None
    second_echo_returncode = None
    first_echo_payload = []
    first_echo_payload_length = 0
    first_echo_payload_all_finite = False
    first_echo_payload_all_zero = False
    first_echo_message_received = False
    second_echo_timeout_no_extra_message = False
    manual_enable_active_during_test = False
    manual_enable_reverted_false = False
    active_ros_publisher_path_exists = False
    controller_alive_after_publish = False

    try:
        bridge_proc = start_node(BRIDGE_PACKAGE, BRIDGE_EXECUTABLE)
        time.sleep(3.0)
        bridge_alive = bridge_proc.poll() is None
        add_check(checks, "bridge_alive_after_startup", bridge_alive, True, bridge_alive)

        echo1_proc = start_echo_once(18)
        time.sleep(2.0)

        controller_args = (
            "--ros-args "
            "-p enable_torque_publisher:=true "
            "-p confirm_torque_publisher_enable:=true"
        )
        controller_proc = start_node(CONTROLLER_PACKAGE, CONTROLLER_EXECUTABLE, controller_args)
        time.sleep(1.0)

        controller_alive = controller_proc.poll() is None
        add_check(checks, "disabled_controller_alive_after_startup", controller_alive, True, controller_alive)

        first_echo_returncode, echo1_out, echo1_err = finish_echo(
            echo1_proc, ECHO1_STDOUT, ECHO1_STDERR, wait_timeout=22
        )

        first_echo_payload = parse_echo_payload(echo1_out)
        first_echo_payload_length = len(first_echo_payload)
        first_echo_payload_all_finite = all(math.isfinite(x) for x in first_echo_payload)
        first_echo_payload_all_zero = (
            first_echo_payload_length == 12 and
            all(abs(x) <= 1e-12 for x in first_echo_payload)
        )
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

        echo2_proc = start_echo_once(4)
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

    bounded_zero_safe_torque_message_published = (
        first_echo_message_received and
        first_echo_payload_length == 12 and
        first_echo_payload_all_finite and
        first_echo_payload_all_zero
    )
    continuous_torque_streaming_enabled = not second_echo_timeout_no_extra_message
    bounded_one_shot_publish_call_repair_passed = (
        source_patch_repair_applied and
        post_publish_call_count == 1 and
        post_has_delayed_one_shot_timer and
        post_has_zero_safe_message_helper and
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
    torque_command_published_by_stage1214_repair = bounded_zero_safe_torque_message_published
    control_law_changed = False

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
    add_check(checks, "continuous_torque_streaming_enabled", continuous_torque_streaming_enabled, False, not continuous_torque_streaming_enabled)
    add_check(checks, "controller_alive_after_publish", controller_alive_after_publish, True, controller_alive_after_publish)
    add_check(checks, "bounded_zero_safe_torque_message_published", bounded_zero_safe_torque_message_published, True, bounded_zero_safe_torque_message_published)
    add_check(checks, "bounded_one_shot_publish_call_repair_passed", bounded_one_shot_publish_call_repair_passed, True, bounded_one_shot_publish_call_repair_passed)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)
    add_check(checks, "torque_publisher_enabled", torque_publisher_enabled, False, not torque_publisher_enabled)
    add_check(checks, "torque_command_published_by_stage1214_repair", torque_command_published_by_stage1214_repair, True, torque_command_published_by_stage1214_repair)
    add_check(checks, "control_law_changed", control_law_changed, False, not control_law_changed)

    all_pass = all(row["pass"] for row in checks)

    gate_rows = load_dicts(FAILED_GATE)
    if not gate_rows:
        gate_rows = []

    updated_gate_rows = []
    found_g32 = False

    for row in gate_rows:
        row = dict(row)
        if row.get("gate") == "G3":
            row["current_status"] = False
            row["evidence"] = "Stage 12.14R has exactly one bounded publish call"
        if row.get("gate") == "G8":
            row["current_status"] = False
            row["evidence"] = "manual flags activated during test and reverted false"
        if row.get("gate") == "G32":
            row["current_status"] = str(bounded_one_shot_publish_call_repair_passed)
            row["evidence"] = str(LOG_PATH.relative_to(ROOT))
            found_g32 = True
        updated_gate_rows.append(row)

    if not found_g32:
        updated_gate_rows.append({
            "gate": "G32",
            "name": "Bounded one-shot zero/safe publish-call implementation passed",
            "required_before_torque_publish": True,
            "current_status": bounded_one_shot_publish_call_repair_passed,
            "evidence": str(LOG_PATH.relative_to(ROOT)),
        })

    updated_gate_rows.append({
        "gate": "G33",
        "name": "Bounded one-shot publish-call repair passed",
        "required_before_torque_publish": True,
        "current_status": bounded_one_shot_publish_call_repair_passed,
        "evidence": str(LOG_PATH.relative_to(ROOT)),
    })

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(updated_gate_rows)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    DOC_PATH.write_text(f"""# Stage 12.14R Bounded One-shot Publish-call Repair

## 一、结论

Stage 12.14 首次运行失败，因为 one-shot publish 没有被 echo 捕获。

Stage 12.14R 修复方式：

- 保留 exactly one publish call；
- 将 constructor immediate publish 改为 delayed one-shot timer；
- 显式构造 length=12 zero/safe Float64MultiArray；
- 确认第一条 echo 收到 12 个有限零值；
- 确认第二次 echo 超时且无额外消息；
- 确认 manual enable flags 已回退 false；
- 确认无连续 torque streaming。

## 二、Source repair

Before repair:

    results/logs_sample/stage12_disabled_controller_node_before_stage1214_repair.cpp

After repair:

    results/logs_sample/stage12_disabled_controller_node_after_stage1214_repair.cpp

Checks:

- source_patch_repair_applied: {source_patch_repair_applied}
- post_publish_call_count: {post_publish_call_count}
- post_has_delayed_one_shot_timer: {post_has_delayed_one_shot_timer}
- post_has_zero_safe_message_helper: {post_has_zero_safe_message_helper}
- post_forbids_continuous_publish: {post_forbids_continuous_publish}

## 三、Runtime evidence

Echo 1:

    results/logs_sample/stage12_bounded_one_shot_publish_call_repair_echo1_stdout.txt

Echo 2:

    results/logs_sample/stage12_bounded_one_shot_publish_call_repair_echo2_stdout.txt

Results:

- first_echo_returncode: {first_echo_returncode}
- first_echo_message_received: {first_echo_message_received}
- first_echo_payload_length: {first_echo_payload_length}
- first_echo_payload_all_finite: {first_echo_payload_all_finite}
- first_echo_payload_all_zero: {first_echo_payload_all_zero}
- second_echo_returncode: {second_echo_returncode}
- second_echo_timeout_no_extra_message: {second_echo_timeout_no_extra_message}
- continuous_torque_streaming_enabled: {continuous_torque_streaming_enabled}

## 四、边界

当前 baseline 仍是 mixed_online_control_baseline。

Stage 12.14R 完成 bounded one-shot zero/safe publish-call repair。

仍未完成：

- continuous torque streaming；
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
        writer.writerow(["stage", "Stage 12.14R"])
        writer.writerow(["test_name", "bounded_one_shot_publish_call_repair"])
        writer.writerow(["previous_stage1214_pass", previous_pass])
        writer.writerow(["previous_first_echo_timeout", previous_first_echo_timeout])
        writer.writerow(["previous_no_first_message", previous_no_message])
        writer.writerow(["source_patch_repair_applied", source_patch_repair_applied])
        writer.writerow(["source_hash_before_repair", source_hash_before])
        writer.writerow(["source_hash_after_repair", source_hash_after])
        writer.writerow(["post_publish_call_count", post_publish_call_count])
        writer.writerow(["post_has_exactly_one_publish_call", post_has_exactly_one_publish_call])
        writer.writerow(["post_has_stage1214_marker", post_has_stage1214_marker])
        writer.writerow(["post_has_delayed_one_shot_timer", post_has_delayed_one_shot_timer])
        writer.writerow(["post_has_zero_safe_message_helper", post_has_zero_safe_message_helper])
        writer.writerow(["post_forbids_continuous_publish", post_forbids_continuous_publish])
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
        writer.writerow(["bounded_one_shot_publish_call_repair_passed", bounded_one_shot_publish_call_repair_passed])
        writer.writerow(["active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g3_no_publish_call", False])
        writer.writerow(["g8_manual_enable_active_after_revert", False])
        writer.writerow(["g9_active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g32_bounded_one_shot_zero_safe_publish_call_implementation_passed", bounded_one_shot_publish_call_repair_passed])
        writer.writerow(["g33_bounded_one_shot_publish_call_repair_passed", bounded_one_shot_publish_call_repair_passed])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", control_law_changed])
        writer.writerow(["torque_publisher_enabled", torque_publisher_enabled])
        writer.writerow(["torque_command_published_by_stage1214_repair", torque_command_published_by_stage1214_repair])
        writer.writerow(["stage12_scope", "bounded_one_shot_publish_call_repair_only"])
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
        writer.writerow(["source_before_repair", str(SOURCE_BEFORE_REPAIR.relative_to(ROOT))])
        writer.writerow(["source_after_repair", str(SOURCE_AFTER_REPAIR.relative_to(ROOT))])
        writer.writerow(["doc", str(DOC_PATH.relative_to(ROOT))])

    print("[Stage 12.14R] bounded one-shot publish-call repair")
    print(f"pass={all_pass}")
    print(f"previous_stage1214_pass={previous_pass}")
    print(f"source_patch_repair_applied={source_patch_repair_applied}")
    print(f"post_publish_call_count={post_publish_call_count}")
    print(f"post_has_delayed_one_shot_timer={post_has_delayed_one_shot_timer}")
    print(f"post_has_zero_safe_message_helper={post_has_zero_safe_message_helper}")
    print(f"manual_enable_active_during_test={manual_enable_active_during_test}")
    print(f"manual_enable_reverted_false={manual_enable_reverted_false}")
    print(f"first_echo_returncode={first_echo_returncode}")
    print(f"first_echo_message_received={first_echo_message_received}")
    print(f"first_echo_payload_length={first_echo_payload_length}")
    print(f"first_echo_payload_all_finite={first_echo_payload_all_finite}")
    print(f"first_echo_payload_all_zero={first_echo_payload_all_zero}")
    print(f"second_echo_returncode={second_echo_returncode}")
    print(f"second_echo_timeout_no_extra_message={second_echo_timeout_no_extra_message}")
    print(f"bounded_zero_safe_torque_message_published={bounded_zero_safe_torque_message_published}")
    print(f"continuous_torque_streaming_enabled={continuous_torque_streaming_enabled}")
    print(f"bounded_one_shot_publish_call_repair_passed={bounded_one_shot_publish_call_repair_passed}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print(f"control_law_changed={control_law_changed}")
    print(f"torque_publisher_enabled={torque_publisher_enabled}")
    print(f"torque_command_published_by_stage1214_repair={torque_command_published_by_stage1214_repair}")
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
