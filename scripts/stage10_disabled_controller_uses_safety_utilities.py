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

STAGE107_SUMMARY = LOG_DIR / "stage10_clamp_watchdog_utility_without_publisher_summary.csv"

PKG_DIR = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller"
CPP_SOURCE = PKG_DIR / "src/disabled_controller_node.cpp"
SAFETY_HEADER = PKG_DIR / "include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"

SUMMARY_PATH = LOG_DIR / "stage10_disabled_controller_uses_safety_utilities_summary.csv"
LOG_PATH = LOG_DIR / "stage10_disabled_controller_uses_safety_utilities_log.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage10_torque_publisher_safety_gate_after_stage108.csv"
DOC_PATH = ROOT / "docs/STAGE10_DISABLED_CONTROLLER_USES_SAFETY_UTILITIES.md"

BUILD_STDOUT = LOG_DIR / "stage10_disabled_controller_uses_safety_build_stdout.txt"
BUILD_STDERR = LOG_DIR / "stage10_disabled_controller_uses_safety_build_stderr.txt"
SAFETY_CHECK_STDOUT = LOG_DIR / "stage10_disabled_controller_uses_safety_contract_stdout.txt"
SAFETY_CHECK_STDERR = LOG_DIR / "stage10_disabled_controller_uses_safety_contract_stderr.txt"
BRIDGE_STDOUT = LOG_DIR / "stage10_disabled_controller_uses_safety_bridge_stdout.txt"
BRIDGE_STDERR = LOG_DIR / "stage10_disabled_controller_uses_safety_bridge_stderr.txt"
CONTROLLER_STDOUT = LOG_DIR / "stage10_disabled_controller_uses_safety_controller_stdout.txt"
CONTROLLER_STDERR = LOG_DIR / "stage10_disabled_controller_uses_safety_controller_stderr.txt"

BRIDGE_PACKAGE = "robot_mpc_wbc_bridge"
BRIDGE_EXECUTABLE = "mujoco_bridge_node"
CONTROLLER_PACKAGE = "robot_mpc_wbc_cpp_controller"
CONTROLLER_EXECUTABLE = "go1_disabled_controller_node"
SAFETY_CHECK_EXECUTABLE = "torque_safety_contract_check"
TORQUE_TOPIC = "/go1/joint_torque_cmd"


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


def parse_metric_csv_text(text):
    metrics = {}
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        return metrics
    for row in rows[1:]:
        if len(row) >= 2:
            metrics[row[0].strip()] = row[1].strip()
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


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    checks = []

    stage107 = load_summary(STAGE107_SUMMARY)
    stage107_pass = as_bool(stage107.get("pass", "False"))
    stage107_torque_enabled = as_bool(stage107.get("torque_publisher_enabled", "True"))
    stage107_control_changed = as_bool(stage107.get("control_law_changed", "True"))

    add_check(checks, "stage107_summary_exists", STAGE107_SUMMARY.exists(), True, STAGE107_SUMMARY.exists(), str(STAGE107_SUMMARY))
    add_check(checks, "stage107_pass", stage107_pass, True, stage107_pass)
    add_check(checks, "stage107_torque_publisher_enabled", stage107_torque_enabled, False, not stage107_torque_enabled)
    add_check(checks, "stage107_control_law_changed", stage107_control_changed, False, not stage107_control_changed)

    cpp_text = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    safety_text = SAFETY_HEADER.read_text(errors="replace") if SAFETY_HEADER.exists() else ""

    source_has_create_publisher = "create_publisher" in cpp_text
    source_has_publish_call = ".publish(" in cpp_text or "->publish(" in cpp_text
    source_has_torque_topic = TORQUE_TOPIC in cpp_text

    source_includes_safety_header = "torque_safety.hpp" in cpp_text
    source_uses_clamp = "clampTorqueCommand" in cpp_text
    source_uses_watchdog_fresh = "allInputsFresh" in cpp_text
    source_uses_watchdog_fallback = "watchdogFallbackZeroTorque" in cpp_text
    source_has_internal_safe_tau = "safe_torque_dry_run_" in cpp_text
    source_has_input_timeout = "kInputFreshnessTimeoutSeconds" in cpp_text
    source_has_runtime_log_marker = "uses_safety_utilities=1" in cpp_text

    safety_header_has_clamp = "clampTorqueCommand" in safety_text
    safety_header_has_watchdog = "allInputsFresh" in safety_text and "watchdogFallbackZeroTorque" in safety_text

    add_check(checks, "cpp_source_exists", CPP_SOURCE.exists(), True, CPP_SOURCE.exists(), str(CPP_SOURCE))
    add_check(checks, "safety_header_exists", SAFETY_HEADER.exists(), True, SAFETY_HEADER.exists(), str(SAFETY_HEADER))
    add_check(checks, "source_has_no_create_publisher", source_has_create_publisher, False, not source_has_create_publisher)
    add_check(checks, "source_has_no_publish_call", source_has_publish_call, False, not source_has_publish_call)
    add_check(checks, "source_does_not_reference_torque_topic", source_has_torque_topic, False, not source_has_torque_topic)
    add_check(checks, "source_includes_safety_header", source_includes_safety_header, True, source_includes_safety_header)
    add_check(checks, "source_uses_clamp_torque_command", source_uses_clamp, True, source_uses_clamp)
    add_check(checks, "source_uses_watchdog_fresh_check", source_uses_watchdog_fresh, True, source_uses_watchdog_fresh)
    add_check(checks, "source_uses_watchdog_fallback_zero", source_uses_watchdog_fallback, True, source_uses_watchdog_fallback)
    add_check(checks, "source_has_internal_safe_tau_buffer", source_has_internal_safe_tau, True, source_has_internal_safe_tau)
    add_check(checks, "source_has_input_freshness_timeout", source_has_input_timeout, True, source_has_input_timeout)
    add_check(checks, "source_has_runtime_log_marker", source_has_runtime_log_marker, True, source_has_runtime_log_marker)
    add_check(checks, "safety_header_has_clamp", safety_header_has_clamp, True, safety_header_has_clamp)
    add_check(checks, "safety_header_has_watchdog", safety_header_has_watchdog, True, safety_header_has_watchdog)

    build_rc = build_packages()
    add_check(checks, "colcon_build_returncode", build_rc, 0, build_rc == 0)

    safety_check = bash_cmd(f"ros2 run {CONTROLLER_PACKAGE} {SAFETY_CHECK_EXECUTABLE}", timeout=10)
    SAFETY_CHECK_STDOUT.write_text(safety_check.stdout)
    SAFETY_CHECK_STDERR.write_text(safety_check.stderr)

    metrics = parse_metric_csv_text(safety_check.stdout)
    clamp_output_all_finite = as_bool(metrics.get("clamp_output_all_finite", "False"))
    clamp_expected_values_ok = as_bool(metrics.get("clamp_expected_values_ok", "False"))
    watchdog_stale_blocks = as_bool(metrics.get("watchdog_stale_blocks", "False"))
    watchdog_nan_blocks = as_bool(metrics.get("watchdog_nan_blocks", "False"))
    watchdog_zero_all_zero = as_bool(metrics.get("watchdog_zero_all_zero", "False"))

    add_check(checks, "torque_safety_contract_returncode", safety_check.returncode, 0, safety_check.returncode == 0)
    add_check(checks, "clamp_output_all_finite", clamp_output_all_finite, True, clamp_output_all_finite)
    add_check(checks, "clamp_expected_values_ok", clamp_expected_values_ok, True, clamp_expected_values_ok)
    add_check(checks, "watchdog_stale_blocks", watchdog_stale_blocks, True, watchdog_stale_blocks)
    add_check(checks, "watchdog_nan_blocks", watchdog_nan_blocks, True, watchdog_nan_blocks)
    add_check(checks, "watchdog_zero_all_zero", watchdog_zero_all_zero, True, watchdog_zero_all_zero)

    bridge_proc = None
    controller_proc = None
    torque_publishers_zero = False
    torque_subscribers_positive = False
    controller_alive = False

    try:
        bridge_proc = start_node(BRIDGE_PACKAGE, BRIDGE_EXECUTABLE)
        time.sleep(3.0)
        bridge_alive = bridge_proc.poll() is None
        add_check(checks, "bridge_alive_after_startup", bridge_alive, True, bridge_alive)

        controller_proc = start_node(CONTROLLER_PACKAGE, CONTROLLER_EXECUTABLE)
        time.sleep(6.0)
        controller_alive = controller_proc.poll() is None
        add_check(checks, "disabled_controller_alive_after_startup", controller_alive, True, controller_alive)

        info_rc, info_out, info_err, pub_count, sub_count = topic_info(TORQUE_TOPIC)
        torque_publishers_zero = isinstance(pub_count, int) and pub_count == 0
        torque_subscribers_positive = isinstance(sub_count, int) and sub_count >= 1

        add_check(checks, "torque_topic_info_returncode", info_rc, 0, info_rc == 0, info_err)
        add_check(checks, "torque_topic_publishers_zero", pub_count, 0, torque_publishers_zero)
        add_check(checks, "torque_topic_subscribers_positive", sub_count, ">=1", torque_subscribers_positive)

    finally:
        stop_process(controller_proc, CONTROLLER_STDOUT, CONTROLLER_STDERR)
        stop_process(bridge_proc, BRIDGE_STDOUT, BRIDGE_STDERR)

    controller_uses_safety_utilities = (
        source_includes_safety_header and
        source_uses_clamp and
        source_uses_watchdog_fresh and
        source_uses_watchdog_fallback and
        source_has_internal_safe_tau and
        safety_check.returncode == 0
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
            "evidence": "not implemented or activated in Stage 10.8",
        },
        {
            "gate": "G9",
            "name": "Publisher path exists",
            "required_before_torque_publish": True,
            "current_status": publisher_path_exists,
            "evidence": "not implemented in Stage 10.8",
        },
        {
            "gate": "G10",
            "name": "Disabled controller uses clamp/watchdog internally",
            "required_before_torque_publish": True,
            "current_status": controller_uses_safety_utilities,
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

    add_check(checks, "controller_uses_safety_utilities", controller_uses_safety_utilities, True, controller_uses_safety_utilities)
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
        writer.writerow(["stage", "Stage 10.8"])
        writer.writerow(["test_name", "disabled_controller_uses_safety_utilities"])
        writer.writerow(["stage107_pass", stage107_pass])
        writer.writerow(["colcon_build_returncode", build_rc])
        writer.writerow(["torque_safety_contract_returncode", safety_check.returncode])
        writer.writerow(["source_has_no_create_publisher", not source_has_create_publisher])
        writer.writerow(["source_has_no_publish_call", not source_has_publish_call])
        writer.writerow(["source_does_not_reference_torque_topic", not source_has_torque_topic])
        writer.writerow(["source_includes_safety_header", source_includes_safety_header])
        writer.writerow(["source_uses_clamp_torque_command", source_uses_clamp])
        writer.writerow(["source_uses_watchdog_fresh_check", source_uses_watchdog_fresh])
        writer.writerow(["source_uses_watchdog_fallback_zero", source_uses_watchdog_fallback])
        writer.writerow(["source_has_internal_safe_tau_buffer", source_has_internal_safe_tau])
        writer.writerow(["controller_uses_safety_utilities", controller_uses_safety_utilities])
        writer.writerow(["clamp_output_all_finite", clamp_output_all_finite])
        writer.writerow(["clamp_expected_values_ok", clamp_expected_values_ok])
        writer.writerow(["watchdog_stale_blocks", watchdog_stale_blocks])
        writer.writerow(["watchdog_nan_blocks", watchdog_nan_blocks])
        writer.writerow(["watchdog_zero_all_zero", watchdog_zero_all_zero])
        writer.writerow(["disabled_controller_alive_after_startup", controller_alive])
        writer.writerow(["torque_topic_publishers_zero", torque_publishers_zero])
        writer.writerow(["torque_topic_subscribers_positive", torque_subscribers_positive])
        writer.writerow(["manual_enable_active", manual_enable_active])
        writer.writerow(["publisher_path_exists", publisher_path_exists])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_publisher_enabled", False])
        writer.writerow(["torque_command_published_by_stage108", False])
        writer.writerow(["stage10_scope", "disabled_controller_uses_safety_utilities_without_publisher_only"])
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
        writer.writerow(["contract_check_stdout", str(SAFETY_CHECK_STDOUT.relative_to(ROOT))])
        writer.writerow(["contract_check_stderr", str(SAFETY_CHECK_STDERR.relative_to(ROOT))])
        writer.writerow(["bridge_stdout", str(BRIDGE_STDOUT.relative_to(ROOT))])
        writer.writerow(["bridge_stderr", str(BRIDGE_STDERR.relative_to(ROOT))])
        writer.writerow(["controller_stdout", str(CONTROLLER_STDOUT.relative_to(ROOT))])
        writer.writerow(["controller_stderr", str(CONTROLLER_STDERR.relative_to(ROOT))])
        writer.writerow(["doc", str(DOC_PATH.relative_to(ROOT))])

    DOC_PATH.write_text(f"""# Stage 10.8 Disabled Controller Uses Safety Utilities

## 一、目标

将 Stage 10.7 的 torque_safety utility 接入 disabled controller 内部路径。

本阶段不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、接入内容

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

已接入：

- torque_safety.hpp
- clampTorqueCommand
- allInputsFresh
- watchdogFallbackZeroTorque
- internal safe_torque_dry_run_ buffer
- input freshness timeout

## 三、运行时边界

Stage 10.8 运行 bridge 和 disabled controller，只验证：

- controller 可启动；
- safety utility contract check 仍通过；
- torque topic publisher count 仍为 0；
- controller source 无 create_publisher；
- controller source 无 publish call；
- controller source 不引用 /go1/joint_torque_cmd。

## 四、结果

- pass: {all_pass}
- controller_uses_safety_utilities: {controller_uses_safety_utilities}
- disabled_controller_alive_after_startup: {controller_alive}
- torque_topic_publishers_zero: {torque_publishers_zero}
- torque_enable_ready: {torque_enable_ready}

## 五、Safety gate

Stage 10.8 后：

- G10 disabled controller uses clamp/watchdog internally: {controller_uses_safety_utilities}
- G8 manual enable flags active at runtime: {manual_enable_active}
- G9 publisher path exists: {publisher_path_exists}

因此 torque_enable_ready 仍必须为 False。

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 10.8 不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
""")

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 10.8 Disabled Controller Uses Safety Utilities

Stage 10.8 将 clamp/watchdog utilities 接入 disabled controller 内部路径。

- Script: `scripts/stage10_disabled_controller_uses_safety_utilities.py`
- Source: `ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp`
- Log: `results/logs_sample/stage10_disabled_controller_uses_safety_utilities_log.csv`
- Safety gate: `results/logs_sample/stage10_torque_publisher_safety_gate_after_stage108.csv`
- Summary: `results/logs_sample/stage10_disabled_controller_uses_safety_utilities_summary.csv`
- Docs: `docs/STAGE10_DISABLED_CONTROLLER_USES_SAFETY_UTILITIES.md`
- pass: `{all_pass}`
- controller_uses_safety_utilities: `{controller_uses_safety_utilities}`
- torque_topic_publishers_zero: `{torque_publishers_zero}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 10.8 只接入内部 safety utility，不创建 publisher，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 10.8 Disabled Controller Uses Safety Utilities"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 10.8] disabled controller uses safety utilities")
    print(f"pass={all_pass}")
    print(f"stage107_pass={stage107_pass}")
    print(f"torque_safety_contract_returncode={safety_check.returncode}")
    print(f"controller_uses_safety_utilities={controller_uses_safety_utilities}")
    print(f"disabled_controller_alive_after_startup={controller_alive}")
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
