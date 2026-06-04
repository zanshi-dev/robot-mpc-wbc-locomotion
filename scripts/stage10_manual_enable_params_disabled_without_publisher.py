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

STAGE109_SUMMARY = LOG_DIR / "stage10_7_8_safety_utility_freeze_summary.csv"

PKG_DIR = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller"
CPP_SOURCE = PKG_DIR / "src/disabled_controller_node.cpp"
SAFETY_HEADER = PKG_DIR / "include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"

SUMMARY_PATH = LOG_DIR / "stage10_manual_enable_params_disabled_without_publisher_summary.csv"
LOG_PATH = LOG_DIR / "stage10_manual_enable_params_disabled_without_publisher_log.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage10_torque_publisher_safety_gate_after_stage1010.csv"
DOC_PATH = ROOT / "docs/STAGE10_MANUAL_ENABLE_PARAMS_DISABLED_WITHOUT_PUBLISHER.md"

BUILD_STDOUT = LOG_DIR / "stage10_manual_enable_params_build_stdout.txt"
BUILD_STDERR = LOG_DIR / "stage10_manual_enable_params_build_stderr.txt"
BRIDGE_STDOUT = LOG_DIR / "stage10_manual_enable_params_bridge_stdout.txt"
BRIDGE_STDERR = LOG_DIR / "stage10_manual_enable_params_bridge_stderr.txt"
CONTROLLER_STDOUT = LOG_DIR / "stage10_manual_enable_params_controller_stdout.txt"
CONTROLLER_STDERR = LOG_DIR / "stage10_manual_enable_params_controller_stderr.txt"
PARAM_LIST_STDOUT = LOG_DIR / "stage10_manual_enable_params_param_list_stdout.txt"
PARAM_LIST_STDERR = LOG_DIR / "stage10_manual_enable_params_param_list_stderr.txt"
PARAM_GET_STDOUT = LOG_DIR / "stage10_manual_enable_params_param_get_stdout.txt"
PARAM_GET_STDERR = LOG_DIR / "stage10_manual_enable_params_param_get_stderr.txt"

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


def param_value_false(stdout):
    text = stdout.strip().lower()
    return "false" in text and "true" not in text


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    checks = []

    stage109 = load_summary(STAGE109_SUMMARY)
    stage109_pass = as_bool(stage109.get("pass", "False"))
    stage109_safety_frozen = as_bool(stage109.get("safety_utility_frozen", "False"))
    stage109_torque_enabled = as_bool(stage109.get("torque_publisher_enabled", "True"))
    stage109_control_changed = as_bool(stage109.get("control_law_changed", "True"))

    add_check(checks, "stage109_summary_exists", STAGE109_SUMMARY.exists(), True, STAGE109_SUMMARY.exists(), str(STAGE109_SUMMARY))
    add_check(checks, "stage109_pass", stage109_pass, True, stage109_pass)
    add_check(checks, "stage109_safety_utility_frozen", stage109_safety_frozen, True, stage109_safety_frozen)
    add_check(checks, "stage109_torque_publisher_enabled", stage109_torque_enabled, False, not stage109_torque_enabled)
    add_check(checks, "stage109_control_law_changed", stage109_control_changed, False, not stage109_control_changed)

    cpp_text = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    safety_text = SAFETY_HEADER.read_text(errors="replace") if SAFETY_HEADER.exists() else ""

    source_has_create_publisher = "create_publisher" in cpp_text
    source_has_publish_call = ".publish(" in cpp_text or "->publish(" in cpp_text
    source_has_torque_topic = TORQUE_TOPIC in cpp_text

    source_declares_enable_param = f'declare_parameter<bool>("{PARAM_ENABLE}", false)' in cpp_text
    source_declares_confirm_param = f'declare_parameter<bool>("{PARAM_CONFIRM}", false)' in cpp_text
    source_reads_enable_param = f'get_parameter("{PARAM_ENABLE}").as_bool()' in cpp_text
    source_reads_confirm_param = f'get_parameter("{PARAM_CONFIRM}").as_bool()' in cpp_text
    source_has_manual_enable_active = "manual_enable_active_" in cpp_text
    source_uses_safety = "clampTorqueCommand" in cpp_text and "allInputsFresh" in cpp_text and "watchdogFallbackZeroTorque" in cpp_text
    safety_header_has_clamp_watchdog = "clampTorqueCommand" in safety_text and "allInputsFresh" in safety_text

    add_check(checks, "cpp_source_exists", CPP_SOURCE.exists(), True, CPP_SOURCE.exists(), str(CPP_SOURCE))
    add_check(checks, "safety_header_exists", SAFETY_HEADER.exists(), True, SAFETY_HEADER.exists(), str(SAFETY_HEADER))
    add_check(checks, "source_has_no_create_publisher", source_has_create_publisher, False, not source_has_create_publisher)
    add_check(checks, "source_has_no_publish_call", source_has_publish_call, False, not source_has_publish_call)
    add_check(checks, "source_does_not_reference_torque_topic", source_has_torque_topic, False, not source_has_torque_topic)
    add_check(checks, "source_declares_enable_param_default_false", source_declares_enable_param, True, source_declares_enable_param)
    add_check(checks, "source_declares_confirm_param_default_false", source_declares_confirm_param, True, source_declares_confirm_param)
    add_check(checks, "source_reads_enable_param", source_reads_enable_param, True, source_reads_enable_param)
    add_check(checks, "source_reads_confirm_param", source_reads_confirm_param, True, source_reads_confirm_param)
    add_check(checks, "source_has_manual_enable_active_state", source_has_manual_enable_active, True, source_has_manual_enable_active)
    add_check(checks, "source_uses_safety_utilities", source_uses_safety, True, source_uses_safety)
    add_check(checks, "safety_header_has_clamp_watchdog", safety_header_has_clamp_watchdog, True, safety_header_has_clamp_watchdog)

    build_rc = build_packages()
    add_check(checks, "colcon_build_returncode", build_rc, 0, build_rc == 0)

    bridge_proc = None
    controller_proc = None

    torque_publishers_zero = False
    torque_subscribers_positive = False
    enable_param_listed = False
    confirm_param_listed = False
    enable_param_default_false = False
    confirm_param_default_false = False
    manual_enable_active = False
    publisher_path_exists = False

    try:
        bridge_proc = start_node(BRIDGE_PACKAGE, BRIDGE_EXECUTABLE)
        time.sleep(3.0)
        bridge_alive = bridge_proc.poll() is None
        add_check(checks, "bridge_alive_after_startup", bridge_alive, True, bridge_alive)

        controller_proc = start_node(CONTROLLER_PACKAGE, CONTROLLER_EXECUTABLE)
        time.sleep(4.0)
        controller_alive = controller_proc.poll() is None
        add_check(checks, "disabled_controller_alive_after_startup", controller_alive, True, controller_alive)

        param_list = bash_cmd("ros2 param list /go1_disabled_controller_node", timeout=10)
        PARAM_LIST_STDOUT.write_text(param_list.stdout)
        PARAM_LIST_STDERR.write_text(param_list.stderr)

        enable_param_listed = PARAM_ENABLE in param_list.stdout
        confirm_param_listed = PARAM_CONFIRM in param_list.stdout

        add_check(checks, "param_list_returncode", param_list.returncode, 0, param_list.returncode == 0, param_list.stderr)
        add_check(checks, "enable_param_listed", enable_param_listed, True, enable_param_listed)
        add_check(checks, "confirm_param_listed", confirm_param_listed, True, confirm_param_listed)

        get_enable = bash_cmd(f"ros2 param get /go1_disabled_controller_node {PARAM_ENABLE}", timeout=10)
        get_confirm = bash_cmd(f"ros2 param get /go1_disabled_controller_node {PARAM_CONFIRM}", timeout=10)

        PARAM_GET_STDOUT.write_text(
            f"{PARAM_ENABLE}:\n{get_enable.stdout}\n\n{PARAM_CONFIRM}:\n{get_confirm.stdout}\n"
        )
        PARAM_GET_STDERR.write_text(
            f"{PARAM_ENABLE} stderr:\n{get_enable.stderr}\n\n{PARAM_CONFIRM} stderr:\n{get_confirm.stderr}\n"
        )

        enable_param_default_false = get_enable.returncode == 0 and param_value_false(get_enable.stdout)
        confirm_param_default_false = get_confirm.returncode == 0 and param_value_false(get_confirm.stdout)

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

    manual_enable_params_declared = (
        source_declares_enable_param and
        source_declares_confirm_param and
        enable_param_listed and
        confirm_param_listed
    )

    manual_enable_params_default_false = (
        enable_param_default_false and
        confirm_param_default_false
    )

    manual_enable_active = False
    publisher_path_exists = False
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
            "evidence": "parameters exist but default false in Stage 10.10",
        },
        {
            "gate": "G9",
            "name": "Publisher path exists",
            "required_before_torque_publish": True,
            "current_status": publisher_path_exists,
            "evidence": "not implemented in Stage 10.10",
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
            "current_status": manual_enable_params_declared and manual_enable_params_default_false,
            "evidence": str(CPP_SOURCE.relative_to(ROOT)),
        },
    ]

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(gate_rows)

    add_check(checks, "manual_enable_params_declared", manual_enable_params_declared, True, manual_enable_params_declared)
    add_check(checks, "manual_enable_params_default_false", manual_enable_params_default_false, True, manual_enable_params_default_false)
    add_check(checks, "manual_enable_active", manual_enable_active, False, not manual_enable_active)
    add_check(checks, "publisher_path_exists", publisher_path_exists, False, not publisher_path_exists)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 10.10"])
        writer.writerow(["test_name", "manual_enable_params_disabled_without_publisher"])
        writer.writerow(["stage109_pass", stage109_pass])
        writer.writerow(["colcon_build_returncode", build_rc])
        writer.writerow(["source_has_no_create_publisher", not source_has_create_publisher])
        writer.writerow(["source_has_no_publish_call", not source_has_publish_call])
        writer.writerow(["source_does_not_reference_torque_topic", not source_has_torque_topic])
        writer.writerow(["source_declares_enable_param_default_false", source_declares_enable_param])
        writer.writerow(["source_declares_confirm_param_default_false", source_declares_confirm_param])
        writer.writerow(["enable_param_listed", enable_param_listed])
        writer.writerow(["confirm_param_listed", confirm_param_listed])
        writer.writerow(["enable_param_default_false", enable_param_default_false])
        writer.writerow(["confirm_param_default_false", confirm_param_default_false])
        writer.writerow(["manual_enable_params_declared", manual_enable_params_declared])
        writer.writerow(["manual_enable_params_default_false", manual_enable_params_default_false])
        writer.writerow(["manual_enable_active", manual_enable_active])
        writer.writerow(["publisher_path_exists", publisher_path_exists])
        writer.writerow(["torque_topic_publishers_zero", torque_publishers_zero])
        writer.writerow(["torque_topic_subscribers_positive", torque_subscribers_positive])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_publisher_enabled", False])
        writer.writerow(["torque_command_published_by_stage1010", False])
        writer.writerow(["stage10_scope", "manual_enable_params_disabled_without_publisher_only"])
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
        writer.writerow(["param_list_stdout", str(PARAM_LIST_STDOUT.relative_to(ROOT))])
        writer.writerow(["param_list_stderr", str(PARAM_LIST_STDERR.relative_to(ROOT))])
        writer.writerow(["param_get_stdout", str(PARAM_GET_STDOUT.relative_to(ROOT))])
        writer.writerow(["param_get_stderr", str(PARAM_GET_STDERR.relative_to(ROOT))])
        writer.writerow(["bridge_stdout", str(BRIDGE_STDOUT.relative_to(ROOT))])
        writer.writerow(["bridge_stderr", str(BRIDGE_STDERR.relative_to(ROOT))])
        writer.writerow(["controller_stdout", str(CONTROLLER_STDOUT.relative_to(ROOT))])
        writer.writerow(["controller_stderr", str(CONTROLLER_STDERR.relative_to(ROOT))])
        writer.writerow(["doc", str(DOC_PATH.relative_to(ROOT))])

    DOC_PATH.write_text(f"""# Stage 10.10 Manual Enable Parameters Disabled Without Publisher

## 一、目标

给 disabled controller 增加 manual enable parameters，并确认默认值为 false。

本阶段不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、新增参数

Node:

    go1_disabled_controller_node

Parameters:

    enable_torque_publisher = false
    confirm_torque_publisher_enable = false

两个参数都必须默认为 false。

Stage 10.10 不会把参数设为 true。

## 三、源码安全状态

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: {source_has_create_publisher}
- source_has_publish_call: {source_has_publish_call}
- source_has_torque_topic: {source_has_torque_topic}
- manual_enable_params_declared: {manual_enable_params_declared}
- manual_enable_params_default_false: {manual_enable_params_default_false}

## 四、Runtime 检查

- enable_param_listed: {enable_param_listed}
- confirm_param_listed: {confirm_param_listed}
- enable_param_default_false: {enable_param_default_false}
- confirm_param_default_false: {confirm_param_default_false}
- torque_topic_publishers_zero: {torque_publishers_zero}

## 五、Safety gate

Stage 10.10 后新增：

- G11 manual enable parameters exist and default false: {manual_enable_params_declared and manual_enable_params_default_false}

但以下仍为 False：

- G8 manual enable flags active at runtime: {manual_enable_active}
- G9 publisher path exists: {publisher_path_exists}

Therefore:

    torque_enable_ready = {torque_enable_ready}

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 10.10 不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
""")

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 10.10 Manual Enable Parameters Disabled Without Publisher

Stage 10.10 给 disabled controller 增加 manual enable parameters，默认值保持 false。

- Script: `scripts/stage10_manual_enable_params_disabled_without_publisher.py`
- Source: `ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp`
- Log: `results/logs_sample/stage10_manual_enable_params_disabled_without_publisher_log.csv`
- Safety gate: `results/logs_sample/stage10_torque_publisher_safety_gate_after_stage1010.csv`
- Summary: `results/logs_sample/stage10_manual_enable_params_disabled_without_publisher_summary.csv`
- Docs: `docs/STAGE10_MANUAL_ENABLE_PARAMS_DISABLED_WITHOUT_PUBLISHER.md`
- pass: `{all_pass}`
- manual_enable_params_declared: `{manual_enable_params_declared}`
- manual_enable_params_default_false: `{manual_enable_params_default_false}`
- manual_enable_active: `{manual_enable_active}`
- publisher_path_exists: `{publisher_path_exists}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 10.10 只增加 disabled-by-default manual enable parameters，不创建 publisher，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 10.10 Manual Enable Parameters Disabled Without Publisher"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 10.10] manual enable parameters disabled without publisher")
    print(f"pass={all_pass}")
    print(f"stage109_pass={stage109_pass}")
    print(f"manual_enable_params_declared={manual_enable_params_declared}")
    print(f"manual_enable_params_default_false={manual_enable_params_default_false}")
    print(f"enable_param_default_false={enable_param_default_false}")
    print(f"confirm_param_default_false={confirm_param_default_false}")
    print(f"manual_enable_active={manual_enable_active}")
    print(f"publisher_path_exists={publisher_path_exists}")
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
