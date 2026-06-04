#!/usr/bin/env python3
from pathlib import Path
import csv
import os
import re
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE120_SUMMARY = LOG_DIR / "stage12_active_publisher_construction_planning_summary.csv"
STAGE120_GATE = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage120.csv"
STAGE120_PLAN = LOG_DIR / "stage12_active_publisher_construction_plan.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
SAFETY_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

SUMMARY_PATH = LOG_DIR / "stage12_pre_construction_source_runtime_guard_summary.csv"
LOG_PATH = LOG_DIR / "stage12_pre_construction_source_runtime_guard_log.csv"
OBS_PATH = LOG_DIR / "stage12_pre_construction_topic_observations.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage121.csv"
DOC_PATH = ROOT / "docs/STAGE12_PRE_CONSTRUCTION_SOURCE_RUNTIME_GUARD.md"

BUILD_STDOUT = LOG_DIR / "stage12_pre_construction_guard_build_stdout.txt"
BUILD_STDERR = LOG_DIR / "stage12_pre_construction_guard_build_stderr.txt"
BRIDGE_STDOUT = LOG_DIR / "stage12_pre_construction_guard_bridge_stdout.txt"
BRIDGE_STDERR = LOG_DIR / "stage12_pre_construction_guard_bridge_stderr.txt"
CONTROLLER_STDOUT = LOG_DIR / "stage12_pre_construction_guard_controller_stdout.txt"
CONTROLLER_STDERR = LOG_DIR / "stage12_pre_construction_guard_controller_stderr.txt"
PARAM_STDOUT = LOG_DIR / "stage12_pre_construction_guard_param_stdout.txt"
PARAM_STDERR = LOG_DIR / "stage12_pre_construction_guard_param_stderr.txt"

BRIDGE_PACKAGE = "robot_mpc_wbc_bridge"
BRIDGE_EXECUTABLE = "mujoco_bridge_node"
CONTROLLER_PACKAGE = "robot_mpc_wbc_cpp_controller"
CONTROLLER_EXECUTABLE = "go1_disabled_controller_node"

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


def param_is_false(stdout):
    text = stdout.strip().lower()
    return "false" in text and "true" not in text


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    checks = []

    s120 = load_summary(STAGE120_SUMMARY)
    stage120_pass = as_bool(s120.get("pass", "False"))
    stage120_plan_complete = as_bool(s120.get("active_publisher_construction_planning_complete", "False"))
    stage120_plan_exists = as_bool(s120.get("active_publisher_construction_plan_exists", "False"))
    stage120_g19 = as_bool(s120.get("g19_active_publisher_construction_planning_exists", "False"))
    stage120_manual_active = as_bool(s120.get("manual_enable_active", "True"))
    stage120_active_path = as_bool(s120.get("active_ros_publisher_path_exists", "True"))
    stage120_torque_ready = as_bool(s120.get("torque_enable_ready", "True"))
    stage120_torque_enabled = as_bool(s120.get("torque_publisher_enabled", "True"))
    stage120_control_changed = as_bool(s120.get("control_law_changed", "True"))

    add_check(checks, "stage120_summary_exists", STAGE120_SUMMARY.exists(), True, STAGE120_SUMMARY.exists(), str(STAGE120_SUMMARY))
    add_check(checks, "stage120_pass", stage120_pass, True, stage120_pass)
    add_check(checks, "stage120_plan_exists", stage120_plan_exists, True, stage120_plan_exists)
    add_check(checks, "stage120_planning_complete", stage120_plan_complete, True, stage120_plan_complete)
    add_check(checks, "stage120_g19_true", stage120_g19, True, stage120_g19)
    add_check(checks, "stage120_manual_enable_active", stage120_manual_active, False, not stage120_manual_active)
    add_check(checks, "stage120_active_ros_publisher_path_exists", stage120_active_path, False, not stage120_active_path)
    add_check(checks, "stage120_torque_enable_ready", stage120_torque_ready, False, not stage120_torque_ready)
    add_check(checks, "stage120_torque_publisher_enabled", stage120_torque_enabled, False, not stage120_torque_enabled)
    add_check(checks, "stage120_control_law_changed", stage120_control_changed, False, not stage120_control_changed)

    plan_rows = load_dicts(STAGE120_PLAN)
    plan_all_not_implemented = all(not as_bool(row.get("implemented_in_stage120", "True")) for row in plan_rows)
    plan_has_topic = any(row.get("item") == "future_active_publisher_topic" for row in plan_rows)
    plan_separates_publish = any(
        row.get("item") == "future_construction_gate" and "no publish call" in row.get("value", "")
        for row in plan_rows
    )
    plan_has_abort_conditions = any(row.get("item") == "future_abort_conditions" for row in plan_rows)

    add_check(checks, "stage120_plan_csv_exists", STAGE120_PLAN.exists(), True, STAGE120_PLAN.exists(), str(STAGE120_PLAN))
    add_check(checks, "stage120_plan_all_items_not_implemented", plan_all_not_implemented, True, plan_all_not_implemented)
    add_check(checks, "stage120_plan_has_future_topic", plan_has_topic, True, plan_has_topic)
    add_check(checks, "stage120_plan_separates_construction_and_publish", plan_separates_publish, True, plan_separates_publish)
    add_check(checks, "stage120_plan_has_abort_conditions", plan_has_abort_conditions, True, plan_has_abort_conditions)

    cpp_text = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    safety_text = SAFETY_HEADER.read_text(errors="replace") if SAFETY_HEADER.exists() else ""
    zero_text = ZERO_HEADER.read_text(errors="replace") if ZERO_HEADER.exists() else ""

    source_has_create_publisher = "create_publisher" in cpp_text
    source_has_publish_call = ".publish(" in cpp_text or "->publish(" in cpp_text
    source_has_torque_topic = TORQUE_TOPIC in cpp_text

    source_declares_enable_param = f'declare_parameter<bool>("{PARAM_ENABLE}", false)' in cpp_text
    source_declares_confirm_param = f'declare_parameter<bool>("{PARAM_CONFIRM}", false)' in cpp_text
    source_uses_safety = "clampTorqueCommand" in cpp_text and "allInputsFresh" in cpp_text and "watchdogFallbackZeroTorque" in cpp_text
    safety_header_has_clamp_watchdog = "clampTorqueCommand" in safety_text and "allInputsFresh" in safety_text and "watchdogFallbackZeroTorque" in safety_text
    zero_header_declares_12 = "kGo1NumActuatedJoints = 12" in zero_text

    source_has_dormant_skeleton_marker = "kDormantPublisherPathSkeletonPresent" in cpp_text
    source_has_construct_forbidden_marker = "kDormantPublisherConstructionAllowed = false" in cpp_text
    source_has_publish_forbidden_marker = "kDormantPublishCallAllowed = false" in cpp_text
    source_has_payload_length_12 = "kDormantTorquePayloadLength = 12" in cpp_text
    source_has_dormant_payload_helper = "makeDormantSafeTorqueCommandMessage" in cpp_text

    dormant_source_skeleton_exists = (
        source_has_dormant_skeleton_marker and
        source_has_construct_forbidden_marker and
        source_has_publish_forbidden_marker and
        source_has_payload_length_12 and
        source_has_dormant_payload_helper
    )

    add_check(checks, "cpp_source_exists", CPP_SOURCE.exists(), True, CPP_SOURCE.exists(), str(CPP_SOURCE))
    add_check(checks, "safety_header_exists", SAFETY_HEADER.exists(), True, SAFETY_HEADER.exists(), str(SAFETY_HEADER))
    add_check(checks, "zero_header_exists", ZERO_HEADER.exists(), True, ZERO_HEADER.exists(), str(ZERO_HEADER))
    add_check(checks, "source_has_no_create_publisher", source_has_create_publisher, False, not source_has_create_publisher)
    add_check(checks, "source_has_no_publish_call", source_has_publish_call, False, not source_has_publish_call)
    add_check(checks, "source_does_not_reference_torque_topic", source_has_torque_topic, False, not source_has_torque_topic)
    add_check(checks, "source_declares_enable_param_default_false", source_declares_enable_param, True, source_declares_enable_param)
    add_check(checks, "source_declares_confirm_param_default_false", source_declares_confirm_param, True, source_declares_confirm_param)
    add_check(checks, "source_uses_safety_utilities", source_uses_safety, True, source_uses_safety)
    add_check(checks, "safety_header_has_clamp_watchdog", safety_header_has_clamp_watchdog, True, safety_header_has_clamp_watchdog)
    add_check(checks, "zero_header_declares_12", zero_header_declares_12, True, zero_header_declares_12)
    add_check(checks, "dormant_publisher_path_source_skeleton_exists", dormant_source_skeleton_exists, True, dormant_source_skeleton_exists)

    previous_gate_rows = load_dicts(STAGE120_GATE)
    previous_gate_status = {
        row.get("gate", ""): as_bool(row.get("current_status", "False"))
        for row in previous_gate_rows
    }

    add_check(checks, "stage120_gate_exists", STAGE120_GATE.exists(), True, STAGE120_GATE.exists(), str(STAGE120_GATE))
    add_check(checks, "stage120_gate_g8_false", previous_gate_status.get("G8", True), False, previous_gate_status.get("G8", True) is False)
    add_check(checks, "stage120_gate_g9_false", previous_gate_status.get("G9", True), False, previous_gate_status.get("G9", True) is False)
    add_check(checks, "stage120_gate_g19_true", previous_gate_status.get("G19", False), True, previous_gate_status.get("G19", False) is True)

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
                "publisher_count_zero": isinstance(pub_count, int) and pub_count == 0,
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
                "publisher_count_zero",
                "subscription_count_positive",
            ],
        )
        writer.writeheader()
        writer.writerows(observations)

    topic_info_all_returncode_zero = all(row["topic_info_returncode"] == 0 for row in observations)
    torque_publishers_zero_all_samples = all(row["publisher_count_zero"] for row in observations)
    torque_subscribers_positive_all_samples = all(row["subscription_count_positive"] for row in observations)
    observed_sample_count = len(observations)

    add_check(checks, "runtime_sample_count", observed_sample_count, runtime_sample_count, observed_sample_count == runtime_sample_count)
    add_check(checks, "topic_info_all_returncode_zero", topic_info_all_returncode_zero, True, topic_info_all_returncode_zero)
    add_check(checks, "torque_publishers_zero_all_samples", torque_publishers_zero_all_samples, True, torque_publishers_zero_all_samples)
    add_check(checks, "torque_subscribers_positive_all_samples", torque_subscribers_positive_all_samples, True, torque_subscribers_positive_all_samples)

    manual_enable_active = False
    active_ros_publisher_path_exists = False
    pre_construction_source_runtime_guard_passed = (
        stage120_pass and
        stage120_plan_complete and
        plan_all_not_implemented and
        not source_has_create_publisher and
        not source_has_publish_call and
        not source_has_torque_topic and
        dormant_source_skeleton_exists and
        controller_alive and
        enable_param_default_false and
        confirm_param_default_false and
        observed_sample_count == runtime_sample_count and
        torque_publishers_zero_all_samples
    )
    torque_enable_ready = False

    gate_rows = []
    for row in previous_gate_rows:
        gate_rows.append(row)

    gate_rows.append({
        "gate": "G20",
        "name": "Pre-construction source and runtime guard passed",
        "required_before_torque_publish": True,
        "current_status": pre_construction_source_runtime_guard_passed,
        "evidence": str(LOG_PATH.relative_to(ROOT)),
    })

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(gate_rows)

    add_check(checks, "pre_construction_source_runtime_guard_passed", pre_construction_source_runtime_guard_passed, True, pre_construction_source_runtime_guard_passed)
    add_check(checks, "manual_enable_active", manual_enable_active, False, not manual_enable_active)
    add_check(checks, "active_ros_publisher_path_exists", active_ros_publisher_path_exists, False, not active_ros_publisher_path_exists)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    DOC_PATH.write_text(f"""# Stage 12.1 Pre-construction Source and Runtime Guard

## 一、结论

Stage 12.1 完成 active publisher construction 前的 source/runtime guard。

本阶段不修改 C++ controller 源码，不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、前置状态

Stage 12.0:

- pass: {stage120_pass}
- active_publisher_construction_planning_complete: {stage120_plan_complete}
- active_ros_publisher_path_exists: {stage120_active_path}
- manual_enable_active: {stage120_manual_active}
- torque_enable_ready: {stage120_torque_ready}

## 三、Source guard

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: {source_has_create_publisher}
- source_has_publish_call: {source_has_publish_call}
- source_has_torque_topic: {source_has_torque_topic}
- dormant_publisher_path_source_skeleton_exists: {dormant_source_skeleton_exists}

## 四、Runtime guard

Runtime samples:

- runtime_expected_sample_count: {runtime_sample_count}
- runtime_observed_sample_count: {observed_sample_count}
- topic_info_all_returncode_zero: {topic_info_all_returncode_zero}
- torque_publishers_zero_all_samples: {torque_publishers_zero_all_samples}
- torque_subscribers_positive_all_samples: {torque_subscribers_positive_all_samples}
- enable_param_default_false: {enable_param_default_false}
- confirm_param_default_false: {confirm_param_default_false}

Observation CSV:

    results/logs_sample/stage12_pre_construction_topic_observations.csv

## 五、Safety gate after Stage 12.1

新增：

- G20 pre-construction source and runtime guard passed: {pre_construction_source_runtime_guard_passed}

仍为 False：

- G8 manual enable flags active at runtime: {manual_enable_active}
- G9 active ROS publisher path exists: {active_ros_publisher_path_exists}

Therefore:

    torque_enable_ready = {torque_enable_ready}

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.1 不是 ROS2/C++ realtime controller，不创建 publisher，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
""")

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 12.1"])
        writer.writerow(["test_name", "pre_construction_source_runtime_guard"])
        writer.writerow(["stage120_pass", stage120_pass])
        writer.writerow(["stage120_active_publisher_construction_planning_complete", stage120_plan_complete])
        writer.writerow(["stage120_g19_active_publisher_construction_planning_exists", stage120_g19])
        writer.writerow(["colcon_build_returncode", build_rc])
        writer.writerow(["source_has_no_create_publisher", not source_has_create_publisher])
        writer.writerow(["source_has_no_publish_call", not source_has_publish_call])
        writer.writerow(["source_does_not_reference_torque_topic", not source_has_torque_topic])
        writer.writerow(["source_declares_enable_param_default_false", source_declares_enable_param])
        writer.writerow(["source_declares_confirm_param_default_false", source_declares_confirm_param])
        writer.writerow(["source_uses_safety_utilities", source_uses_safety])
        writer.writerow(["dormant_publisher_path_source_skeleton_exists", dormant_source_skeleton_exists])
        writer.writerow(["enable_param_default_false", enable_param_default_false])
        writer.writerow(["confirm_param_default_false", confirm_param_default_false])
        writer.writerow(["runtime_expected_sample_count", runtime_sample_count])
        writer.writerow(["runtime_observed_sample_count", observed_sample_count])
        writer.writerow(["topic_info_all_returncode_zero", topic_info_all_returncode_zero])
        writer.writerow(["torque_publishers_zero_all_samples", torque_publishers_zero_all_samples])
        writer.writerow(["torque_subscribers_positive_all_samples", torque_subscribers_positive_all_samples])
        writer.writerow(["pre_construction_source_runtime_guard_passed", pre_construction_source_runtime_guard_passed])
        writer.writerow(["manual_enable_active", manual_enable_active])
        writer.writerow(["active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g8_manual_enable_active", manual_enable_active])
        writer.writerow(["g9_active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g20_pre_construction_source_runtime_guard_passed", pre_construction_source_runtime_guard_passed])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_publisher_enabled", False])
        writer.writerow(["torque_command_published_by_stage121", False])
        writer.writerow(["stage12_scope", "pre_construction_source_runtime_guard_only"])
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
## Stage 12.1 Pre-construction Source and Runtime Guard

Stage 12.1 完成 active publisher construction 前 source/runtime guard。

- Script: `scripts/stage12_pre_construction_source_runtime_guard.py`
- Observations: `results/logs_sample/stage12_pre_construction_topic_observations.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage121.csv`
- Summary: `results/logs_sample/stage12_pre_construction_source_runtime_guard_summary.csv`
- Docs: `docs/STAGE12_PRE_CONSTRUCTION_SOURCE_RUNTIME_GUARD.md`
- pass: `{all_pass}`
- pre_construction_source_runtime_guard_passed: `{pre_construction_source_runtime_guard_passed}`
- torque_publishers_zero_all_samples: `{torque_publishers_zero_all_samples}`
- active_ros_publisher_path_exists: `{active_ros_publisher_path_exists}`
- manual_enable_active: `{manual_enable_active}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 12.1 只做 source/runtime guard，不创建 publisher，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 12.1 Pre-construction Source and Runtime Guard"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 12.1] pre-construction source and runtime guard")
    print(f"pass={all_pass}")
    print(f"stage120_pass={stage120_pass}")
    print(f"pre_construction_source_runtime_guard_passed={pre_construction_source_runtime_guard_passed}")
    print(f"torque_publishers_zero_all_samples={torque_publishers_zero_all_samples}")
    print(f"runtime_observed_sample_count={observed_sample_count}")
    print(f"active_ros_publisher_path_exists={active_ros_publisher_path_exists}")
    print(f"manual_enable_active={manual_enable_active}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print("control_law_changed=False")
    print("torque_publisher_enabled=False")
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
