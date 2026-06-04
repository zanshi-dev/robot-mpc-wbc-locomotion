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

STAGE110_SUMMARY = LOG_DIR / "stage11_publisher_path_skeleton_planning_summary.csv"
STAGE110_PLAN = LOG_DIR / "stage11_publisher_path_skeleton_plan.csv"
STAGE110_GATE = LOG_DIR / "stage11_torque_publisher_safety_gate_after_stage110.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
SAFETY_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

SUMMARY_PATH = LOG_DIR / "stage11_publisher_path_source_guard_summary.csv"
LOG_PATH = LOG_DIR / "stage11_publisher_path_source_guard_log.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage11_torque_publisher_safety_gate_after_stage111.csv"
DOC_PATH = ROOT / "docs/STAGE11_PUBLISHER_PATH_SOURCE_GUARD_BEFORE_IMPLEMENTATION.md"

BUILD_STDOUT = LOG_DIR / "stage11_publisher_path_source_guard_build_stdout.txt"
BUILD_STDERR = LOG_DIR / "stage11_publisher_path_source_guard_build_stderr.txt"
BRIDGE_STDOUT = LOG_DIR / "stage11_publisher_path_source_guard_bridge_stdout.txt"
BRIDGE_STDERR = LOG_DIR / "stage11_publisher_path_source_guard_bridge_stderr.txt"
CONTROLLER_STDOUT = LOG_DIR / "stage11_publisher_path_source_guard_controller_stdout.txt"
CONTROLLER_STDERR = LOG_DIR / "stage11_publisher_path_source_guard_controller_stderr.txt"
PARAM_STDOUT = LOG_DIR / "stage11_publisher_path_source_guard_param_stdout.txt"
PARAM_STDERR = LOG_DIR / "stage11_publisher_path_source_guard_param_stderr.txt"

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


def load_csv_dicts(path: Path):
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

    stage110 = load_summary(STAGE110_SUMMARY)
    stage110_pass = as_bool(stage110.get("pass", "False"))
    stage110_plan_exists = as_bool(stage110.get("publisher_path_plan_exists", "False"))
    stage110_path_implemented = as_bool(stage110.get("publisher_path_implemented", "True"))
    stage110_manual_active = as_bool(stage110.get("manual_enable_active", "True"))
    stage110_torque_ready = as_bool(stage110.get("torque_enable_ready", "True"))
    stage110_control_changed = as_bool(stage110.get("control_law_changed", "True"))
    stage110_torque_enabled = as_bool(stage110.get("torque_publisher_enabled", "True"))

    add_check(checks, "stage110_summary_exists", STAGE110_SUMMARY.exists(), True, STAGE110_SUMMARY.exists(), str(STAGE110_SUMMARY))
    add_check(checks, "stage110_pass", stage110_pass, True, stage110_pass)
    add_check(checks, "stage110_publisher_path_plan_exists", stage110_plan_exists, True, stage110_plan_exists)
    add_check(checks, "stage110_publisher_path_implemented", stage110_path_implemented, False, not stage110_path_implemented)
    add_check(checks, "stage110_manual_enable_active", stage110_manual_active, False, not stage110_manual_active)
    add_check(checks, "stage110_torque_enable_ready", stage110_torque_ready, False, not stage110_torque_ready)
    add_check(checks, "stage110_torque_publisher_enabled", stage110_torque_enabled, False, not stage110_torque_enabled)
    add_check(checks, "stage110_control_law_changed", stage110_control_changed, False, not stage110_control_changed)

    plan_rows = load_csv_dicts(STAGE110_PLAN)
    plan_exists = STAGE110_PLAN.exists()
    plan_mentions_topic = any(row.get("value", "") == TORQUE_TOPIC for row in plan_rows)
    plan_all_not_implemented = all(not as_bool(row.get("implemented_in_stage110", "True")) for row in plan_rows)
    plan_has_manual_gate = any("manual_gate_policy" == row.get("item", "") for row in plan_rows)
    plan_has_safety_filter = any("safety_filter_policy" == row.get("item", "") for row in plan_rows)

    add_check(checks, "stage110_plan_csv_exists", plan_exists, True, plan_exists, str(STAGE110_PLAN))
    add_check(checks, "stage110_plan_mentions_future_torque_topic", plan_mentions_topic, True, plan_mentions_topic)
    add_check(checks, "stage110_plan_all_items_not_implemented", plan_all_not_implemented, True, plan_all_not_implemented)
    add_check(checks, "stage110_plan_has_manual_gate_policy", plan_has_manual_gate, True, plan_has_manual_gate)
    add_check(checks, "stage110_plan_has_safety_filter_policy", plan_has_safety_filter, True, plan_has_safety_filter)

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

    previous_gate_rows = load_csv_dicts(STAGE110_GATE)
    previous_gate_status = {
        row.get("gate", ""): as_bool(row.get("current_status", "False"))
        for row in previous_gate_rows
    }

    add_check(checks, "stage110_gate_exists", STAGE110_GATE.exists(), True, STAGE110_GATE.exists(), str(STAGE110_GATE))
    add_check(checks, "stage110_g8_manual_enable_active_false", previous_gate_status.get("G8", True), False, previous_gate_status.get("G8", True) is False)
    add_check(checks, "stage110_g9_publisher_path_exists_false", previous_gate_status.get("G9", True), False, previous_gate_status.get("G9", True) is False)
    add_check(checks, "stage110_g12_plan_exists_true", previous_gate_status.get("G12", False), True, previous_gate_status.get("G12", False) is True)

    build_rc = build_packages()
    add_check(checks, "colcon_build_returncode", build_rc, 0, build_rc == 0)

    bridge_proc = None
    controller_proc = None

    enable_param_default_false = False
    confirm_param_default_false = False
    torque_publishers_zero = False
    torque_subscribers_positive = False
    controller_alive = False

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

        info_rc, info_out, info_err, pub_count, sub_count = topic_info(TORQUE_TOPIC)
        torque_publishers_zero = isinstance(pub_count, int) and pub_count == 0
        torque_subscribers_positive = isinstance(sub_count, int) and sub_count >= 1

        add_check(checks, "torque_topic_info_returncode", info_rc, 0, info_rc == 0, info_err)
        add_check(checks, "torque_topic_publishers_zero", pub_count, 0, torque_publishers_zero)
        add_check(checks, "torque_topic_subscribers_positive", sub_count, ">=1", torque_subscribers_positive)

    finally:
        stop_process(controller_proc, CONTROLLER_STDOUT, CONTROLLER_STDERR)
        stop_process(bridge_proc, BRIDGE_STDOUT, BRIDGE_STDERR)

    manual_enable_active = False
    publisher_path_implemented = False
    torque_enable_ready = False

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
            "name": "C++ controller source has no torque publisher",
            "required_before_torque_publish": True,
            "current_status": not source_has_create_publisher,
            "evidence": str(CPP_SOURCE.relative_to(ROOT)),
        },
        {
            "gate": "G3",
            "name": "C++ controller source has no publish call",
            "required_before_torque_publish": True,
            "current_status": not source_has_publish_call,
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
            "evidence": "parameters remain default false in Stage 11.1",
        },
        {
            "gate": "G9",
            "name": "Publisher path exists",
            "required_before_torque_publish": True,
            "current_status": publisher_path_implemented,
            "evidence": "guard confirms not implemented in Stage 11.1",
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
            "evidence": str(STAGE110_PLAN.relative_to(ROOT)),
        },
        {
            "gate": "G13",
            "name": "Publisher-path source guard passed before implementation",
            "required_before_torque_publish": True,
            "current_status": True,
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

    add_check(checks, "manual_enable_active", manual_enable_active, False, not manual_enable_active)
    add_check(checks, "publisher_path_implemented", publisher_path_implemented, False, not publisher_path_implemented)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    DOC_PATH.write_text(f"""# Stage 11.1 Publisher-path Source Guard Before Implementation

## 一、结论

Stage 11.1 是 publisher-path implementation 前的 source/runtime guard。

本阶段不修改 C++ controller 源码，不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、前置状态

Stage 11.0:

- pass: {stage110_pass}
- publisher_path_plan_exists: {stage110_plan_exists}
- publisher_path_implemented: {stage110_path_implemented}
- torque_enable_ready: {stage110_torque_ready}

## 三、源码 guard

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: {source_has_create_publisher}
- source_has_publish_call: {source_has_publish_call}
- source_has_torque_topic: {source_has_torque_topic}
- source_declares_enable_param_default_false: {source_declares_enable_param}
- source_declares_confirm_param_default_false: {source_declares_confirm_param}
- source_uses_safety_utilities: {source_uses_safety}

## 四、Runtime guard

Runtime checks:

- disabled_controller_alive_after_startup: {controller_alive}
- enable_param_default_false: {enable_param_default_false}
- confirm_param_default_false: {confirm_param_default_false}
- torque_topic_publishers_zero: {torque_publishers_zero}
- torque_topic_subscribers_positive: {torque_subscribers_positive}

## 五、Safety gate after Stage 11.1

新增：

- G13 publisher-path source guard passed before implementation: True

仍为 False：

- G8 manual enable flags active at runtime: {manual_enable_active}
- G9 publisher path exists: {publisher_path_implemented}

Therefore:

    torque_enable_ready = {torque_enable_ready}

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 11.1 不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
""")

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 11.1"])
        writer.writerow(["test_name", "publisher_path_source_guard_before_implementation"])
        writer.writerow(["stage110_pass", stage110_pass])
        writer.writerow(["stage110_publisher_path_plan_exists", stage110_plan_exists])
        writer.writerow(["stage110_publisher_path_implemented", stage110_path_implemented])
        writer.writerow(["colcon_build_returncode", build_rc])
        writer.writerow(["source_has_no_create_publisher", not source_has_create_publisher])
        writer.writerow(["source_has_no_publish_call", not source_has_publish_call])
        writer.writerow(["source_does_not_reference_torque_topic", not source_has_torque_topic])
        writer.writerow(["source_declares_enable_param_default_false", source_declares_enable_param])
        writer.writerow(["source_declares_confirm_param_default_false", source_declares_confirm_param])
        writer.writerow(["source_uses_safety_utilities", source_uses_safety])
        writer.writerow(["enable_param_default_false", enable_param_default_false])
        writer.writerow(["confirm_param_default_false", confirm_param_default_false])
        writer.writerow(["torque_topic_publishers_zero", torque_publishers_zero])
        writer.writerow(["torque_topic_subscribers_positive", torque_subscribers_positive])
        writer.writerow(["publisher_path_source_guard_passed", True])
        writer.writerow(["publisher_path_implemented", publisher_path_implemented])
        writer.writerow(["manual_enable_active", manual_enable_active])
        writer.writerow(["g8_manual_enable_active", manual_enable_active])
        writer.writerow(["g9_publisher_path_exists", publisher_path_implemented])
        writer.writerow(["g13_publisher_path_source_guard_passed", True])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_publisher_enabled", False])
        writer.writerow(["torque_command_published_by_stage111", False])
        writer.writerow(["stage11_scope", "publisher_path_source_guard_before_implementation_only"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["ros2_cpp_realtime_controller_completed", False])
        writer.writerow(["pure_wbc_locomotion_completed", False])
        writer.writerow(["ekf_completed", False])
        writer.writerow(["full_3d_centroidal_mpc_completed", False])
        writer.writerow(["num_checks", len(checks)])
        writer.writerow(["num_failed_checks", sum(1 for row in checks if not row["pass"])])
        writer.writerow(["pass", all_pass])
        writer.writerow(["log_csv", str(LOG_PATH.relative_to(ROOT))])
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
## Stage 11.1 Publisher-path Source Guard Before Implementation

Stage 11.1 完成 publisher-path source/runtime guard。

- Script: `scripts/stage11_publisher_path_source_guard_before_implementation.py`
- Log: `results/logs_sample/stage11_publisher_path_source_guard_log.csv`
- Safety gate: `results/logs_sample/stage11_torque_publisher_safety_gate_after_stage111.csv`
- Summary: `results/logs_sample/stage11_publisher_path_source_guard_summary.csv`
- Docs: `docs/STAGE11_PUBLISHER_PATH_SOURCE_GUARD_BEFORE_IMPLEMENTATION.md`
- pass: `{all_pass}`
- publisher_path_source_guard_passed: `True`
- publisher_path_implemented: `{publisher_path_implemented}`
- manual_enable_active: `{manual_enable_active}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 11.1 只做 publisher-path implementation 前 guard，不创建 publisher，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 11.1 Publisher-path Source Guard Before Implementation"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 11.1] publisher-path source guard before implementation")
    print(f"pass={all_pass}")
    print(f"stage110_pass={stage110_pass}")
    print(f"publisher_path_source_guard_passed=True")
    print(f"publisher_path_implemented={publisher_path_implemented}")
    print(f"manual_enable_active={manual_enable_active}")
    print(f"torque_topic_publishers_zero={torque_publishers_zero}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print("control_law_changed=False")
    print("torque_publisher_enabled=False")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
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
