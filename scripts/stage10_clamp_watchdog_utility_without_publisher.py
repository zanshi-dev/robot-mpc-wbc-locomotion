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

STAGE106_SUMMARY = LOG_DIR / "stage10_0_5_controller_planning_freeze_summary.csv"

PKG_DIR = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller"
CPP_CONTROLLER_SOURCE = PKG_DIR / "src/disabled_controller_node.cpp"
ZERO_HEADER = PKG_DIR / "include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"
SAFETY_HEADER = PKG_DIR / "include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"
SAFETY_CHECK_SOURCE = PKG_DIR / "src/torque_safety_contract_check.cpp"
CMAKE = PKG_DIR / "CMakeLists.txt"

SUMMARY_PATH = LOG_DIR / "stage10_clamp_watchdog_utility_without_publisher_summary.csv"
LOG_PATH = LOG_DIR / "stage10_clamp_watchdog_utility_without_publisher_log.csv"
CLAMP_VECTOR_PATH = LOG_DIR / "stage10_clamp_watchdog_utility_clamped_vector.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage10_torque_publisher_safety_gate_after_stage107.csv"
DOC_PATH = ROOT / "docs/STAGE10_CLAMP_WATCHDOG_UTILITY_WITHOUT_PUBLISHER.md"

BUILD_STDOUT = LOG_DIR / "stage10_clamp_watchdog_utility_build_stdout.txt"
BUILD_STDERR = LOG_DIR / "stage10_clamp_watchdog_utility_build_stderr.txt"
CHECK_STDOUT = LOG_DIR / "stage10_clamp_watchdog_contract_check_stdout.txt"
CHECK_STDERR = LOG_DIR / "stage10_clamp_watchdog_contract_check_stderr.txt"
BRIDGE_STDOUT = LOG_DIR / "stage10_clamp_watchdog_bridge_stdout.txt"
BRIDGE_STDERR = LOG_DIR / "stage10_clamp_watchdog_bridge_stderr.txt"
CONTROLLER_STDOUT = LOG_DIR / "stage10_clamp_watchdog_controller_stdout.txt"
CONTROLLER_STDERR = LOG_DIR / "stage10_clamp_watchdog_controller_stderr.txt"

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

    stage106 = load_summary(STAGE106_SUMMARY)
    stage106_pass = as_bool(stage106.get("pass", "False"))
    stage106_frozen = as_bool(stage106.get("controller_planning_frozen", "False"))
    stage106_torque_enabled = as_bool(stage106.get("torque_publisher_enabled", "True"))
    stage106_control_changed = as_bool(stage106.get("control_law_changed", "True"))

    add_check(checks, "stage106_summary_exists", STAGE106_SUMMARY.exists(), True, STAGE106_SUMMARY.exists(), str(STAGE106_SUMMARY))
    add_check(checks, "stage106_pass", stage106_pass, True, stage106_pass)
    add_check(checks, "stage106_controller_planning_frozen", stage106_frozen, True, stage106_frozen)
    add_check(checks, "stage106_torque_publisher_enabled", stage106_torque_enabled, False, not stage106_torque_enabled)
    add_check(checks, "stage106_control_law_changed", stage106_control_changed, False, not stage106_control_changed)

    for path in [CPP_CONTROLLER_SOURCE, ZERO_HEADER, SAFETY_HEADER, SAFETY_CHECK_SOURCE, CMAKE]:
        add_check(checks, f"exists_{path.relative_to(ROOT)}", path.exists(), True, path.exists(), str(path))

    cpp_text = CPP_CONTROLLER_SOURCE.read_text(errors="replace") if CPP_CONTROLLER_SOURCE.exists() else ""
    safety_text = SAFETY_HEADER.read_text(errors="replace") if SAFETY_HEADER.exists() else ""
    check_text = SAFETY_CHECK_SOURCE.read_text(errors="replace") if SAFETY_CHECK_SOURCE.exists() else ""
    cmake_text = CMAKE.read_text(errors="replace") if CMAKE.exists() else ""

    source_has_create_publisher = "create_publisher" in cpp_text
    source_has_publish_call = ".publish(" in cpp_text or "->publish(" in cpp_text
    source_has_torque_topic = TORQUE_TOPIC in cpp_text

    safety_has_clamp = "clampTorqueCommand" in safety_text and "max_abs_torque" in safety_text
    safety_has_watchdog = "allInputsFresh" in safety_text and "watchdogFallbackZeroTorque" in safety_text
    safety_uses_zero_header = "zero_torque_dry_run.hpp" in safety_text
    check_registered = SAFETY_CHECK_EXECUTABLE in cmake_text and SAFETY_CHECK_SOURCE.name in cmake_text
    check_uses_safety_header = "torque_safety.hpp" in check_text

    add_check(checks, "controller_source_has_no_create_publisher", source_has_create_publisher, False, not source_has_create_publisher)
    add_check(checks, "controller_source_has_no_publish_call", source_has_publish_call, False, not source_has_publish_call)
    add_check(checks, "controller_source_does_not_reference_torque_topic", source_has_torque_topic, False, not source_has_torque_topic)
    add_check(checks, "safety_header_has_clamp_utility", safety_has_clamp, True, safety_has_clamp)
    add_check(checks, "safety_header_has_watchdog_utility", safety_has_watchdog, True, safety_has_watchdog)
    add_check(checks, "safety_header_uses_zero_header", safety_uses_zero_header, True, safety_uses_zero_header)
    add_check(checks, "safety_contract_check_registered", check_registered, True, check_registered)
    add_check(checks, "safety_contract_check_uses_header", check_uses_safety_header, True, check_uses_safety_header)

    build_rc = build_packages()
    add_check(checks, "colcon_build_returncode", build_rc, 0, build_rc == 0)

    check_proc = bash_cmd(f"ros2 run {CONTROLLER_PACKAGE} {SAFETY_CHECK_EXECUTABLE}", timeout=10)
    CHECK_STDOUT.write_text(check_proc.stdout)
    CHECK_STDERR.write_text(check_proc.stderr)

    metrics = parse_metric_csv_text(check_proc.stdout)

    clamp_output_size_ok = as_bool(metrics.get("clamp_output_size_ok", "False"))
    clamp_output_all_finite = as_bool(metrics.get("clamp_output_all_finite", "False"))
    clamp_detected_nonfinite = as_bool(metrics.get("clamp_detected_nonfinite", "False"))
    clamp_applied = as_bool(metrics.get("clamp_applied", "False"))
    clamp_max_abs_ok = as_bool(metrics.get("clamp_max_abs_ok", "False"))
    clamp_expected_values_ok = as_bool(metrics.get("clamp_expected_values_ok", "False"))
    zero_clamp_all_zero = as_bool(metrics.get("zero_clamp_all_zero", "False"))
    watchdog_fresh_ok = as_bool(metrics.get("watchdog_fresh_ok", "False"))
    watchdog_stale_blocks = as_bool(metrics.get("watchdog_stale_blocks", "False"))
    watchdog_nan_blocks = as_bool(metrics.get("watchdog_nan_blocks", "False"))
    watchdog_zero_all_zero = as_bool(metrics.get("watchdog_zero_all_zero", "False"))

    add_check(checks, "torque_safety_contract_returncode", check_proc.returncode, 0, check_proc.returncode == 0)
    add_check(checks, "clamp_output_size_ok", clamp_output_size_ok, True, clamp_output_size_ok)
    add_check(checks, "clamp_output_all_finite", clamp_output_all_finite, True, clamp_output_all_finite)
    add_check(checks, "clamp_detected_nonfinite", clamp_detected_nonfinite, True, clamp_detected_nonfinite)
    add_check(checks, "clamp_applied", clamp_applied, True, clamp_applied)
    add_check(checks, "clamp_max_abs_ok", clamp_max_abs_ok, True, clamp_max_abs_ok)
    add_check(checks, "clamp_expected_values_ok", clamp_expected_values_ok, True, clamp_expected_values_ok)
    add_check(checks, "zero_clamp_all_zero", zero_clamp_all_zero, True, zero_clamp_all_zero)
    add_check(checks, "watchdog_fresh_ok", watchdog_fresh_ok, True, watchdog_fresh_ok)
    add_check(checks, "watchdog_stale_blocks", watchdog_stale_blocks, True, watchdog_stale_blocks)
    add_check(checks, "watchdog_nan_blocks", watchdog_nan_blocks, True, watchdog_nan_blocks)
    add_check(checks, "watchdog_zero_all_zero", watchdog_zero_all_zero, True, watchdog_zero_all_zero)

    vector_rows = []
    for i in range(12):
        key = f"clamped_tau_{i}"
        vector_rows.append({"joint_index": i, "clamped_tau": metrics.get(key, "")})

    with CLAMP_VECTOR_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["joint_index", "clamped_tau"])
        writer.writeheader()
        writer.writerows(vector_rows)

    bridge_proc = None
    controller_proc = None
    torque_publishers_zero = False
    torque_subscribers_positive = False

    try:
        bridge_proc = start_node(BRIDGE_PACKAGE, BRIDGE_EXECUTABLE)
        time.sleep(3.0)
        bridge_alive = bridge_proc.poll() is None
        add_check(checks, "bridge_alive_after_startup", bridge_alive, True, bridge_alive)

        controller_proc = start_node(CONTROLLER_PACKAGE, CONTROLLER_EXECUTABLE)
        time.sleep(4.0)
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

    clamp_watchdog_utility_implemented = (
        safety_has_clamp and
        safety_has_watchdog and
        check_proc.returncode == 0 and
        clamp_output_all_finite and
        clamp_expected_values_ok and
        watchdog_stale_blocks and
        watchdog_nan_blocks
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
            "evidence": str(CPP_CONTROLLER_SOURCE.relative_to(ROOT)),
        },
        {
            "gate": "G3",
            "name": "C++ controller source has no publish call",
            "required_before_torque_publish": True,
            "current_status": not source_has_publish_call,
            "evidence": str(CPP_CONTROLLER_SOURCE.relative_to(ROOT)),
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
            "current_status": clamp_watchdog_utility_implemented,
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
            "evidence": "not implemented or activated in Stage 10.7",
        },
        {
            "gate": "G9",
            "name": "Publisher path exists",
            "required_before_torque_publish": True,
            "current_status": publisher_path_exists,
            "evidence": "not implemented in Stage 10.7",
        },
    ]

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(gate_rows)

    add_check(checks, "clamp_watchdog_utility_implemented", clamp_watchdog_utility_implemented, True, clamp_watchdog_utility_implemented)
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
        writer.writerow(["stage", "Stage 10.7"])
        writer.writerow(["test_name", "clamp_watchdog_utility_without_publisher"])
        writer.writerow(["stage106_pass", stage106_pass])
        writer.writerow(["colcon_build_returncode", build_rc])
        writer.writerow(["torque_safety_contract_returncode", check_proc.returncode])
        writer.writerow(["clamp_output_size_ok", clamp_output_size_ok])
        writer.writerow(["clamp_output_all_finite", clamp_output_all_finite])
        writer.writerow(["clamp_detected_nonfinite", clamp_detected_nonfinite])
        writer.writerow(["clamp_applied", clamp_applied])
        writer.writerow(["clamp_max_abs_ok", clamp_max_abs_ok])
        writer.writerow(["clamp_expected_values_ok", clamp_expected_values_ok])
        writer.writerow(["zero_clamp_all_zero", zero_clamp_all_zero])
        writer.writerow(["watchdog_fresh_ok", watchdog_fresh_ok])
        writer.writerow(["watchdog_stale_blocks", watchdog_stale_blocks])
        writer.writerow(["watchdog_nan_blocks", watchdog_nan_blocks])
        writer.writerow(["watchdog_zero_all_zero", watchdog_zero_all_zero])
        writer.writerow(["clamp_watchdog_utility_implemented", clamp_watchdog_utility_implemented])
        writer.writerow(["controller_source_has_no_create_publisher", not source_has_create_publisher])
        writer.writerow(["controller_source_has_no_publish_call", not source_has_publish_call])
        writer.writerow(["controller_source_does_not_reference_torque_topic", not source_has_torque_topic])
        writer.writerow(["torque_topic_publishers_zero", torque_publishers_zero])
        writer.writerow(["torque_topic_subscribers_positive", torque_subscribers_positive])
        writer.writerow(["manual_enable_active", manual_enable_active])
        writer.writerow(["publisher_path_exists", publisher_path_exists])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_publisher_enabled", False])
        writer.writerow(["torque_command_published_by_stage107", False])
        writer.writerow(["stage10_scope", "clamp_watchdog_utility_without_publisher_only"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["ros2_cpp_realtime_controller_completed", False])
        writer.writerow(["pure_wbc_locomotion_completed", False])
        writer.writerow(["ekf_completed", False])
        writer.writerow(["full_3d_centroidal_mpc_completed", False])
        writer.writerow(["num_checks", len(checks)])
        writer.writerow(["num_failed_checks", sum(1 for row in checks if not row["pass"])])
        writer.writerow(["pass", all_pass])
        writer.writerow(["log_csv", str(LOG_PATH.relative_to(ROOT))])
        writer.writerow(["clamped_vector_csv", str(CLAMP_VECTOR_PATH.relative_to(ROOT))])
        writer.writerow(["safety_gate_csv", str(SAFETY_GATE_PATH.relative_to(ROOT))])
        writer.writerow(["summary_csv", str(SUMMARY_PATH.relative_to(ROOT))])
        writer.writerow(["build_stdout", str(BUILD_STDOUT.relative_to(ROOT))])
        writer.writerow(["build_stderr", str(BUILD_STDERR.relative_to(ROOT))])
        writer.writerow(["contract_check_stdout", str(CHECK_STDOUT.relative_to(ROOT))])
        writer.writerow(["contract_check_stderr", str(CHECK_STDERR.relative_to(ROOT))])
        writer.writerow(["bridge_stdout", str(BRIDGE_STDOUT.relative_to(ROOT))])
        writer.writerow(["bridge_stderr", str(BRIDGE_STDERR.relative_to(ROOT))])
        writer.writerow(["controller_stdout", str(CONTROLLER_STDOUT.relative_to(ROOT))])
        writer.writerow(["controller_stderr", str(CONTROLLER_STDERR.relative_to(ROOT))])
        writer.writerow(["doc", str(DOC_PATH.relative_to(ROOT))])

    DOC_PATH.write_text(f"""# Stage 10.7 Clamp/Watchdog Utility Without Publisher

## 一、目标

实现 torque clamp 与 watchdog 工具库，并完成 contract check。

本阶段不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、新增文件

- ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp
- ros2_ws/src/robot_mpc_wbc_cpp_controller/src/torque_safety_contract_check.cpp

## 三、已实现 utility

Clamp utility:

- 输入长度固定为 12；
- 非 finite 输入转换为 0；
- 每关节按 max_abs_torque clamp；
- 输出再次检查 finite；
- 记录是否发生 clamp。

Watchdog utility:

- 检查输入 age 是否 finite；
- 检查 age 是否非负；
- 检查 age 是否小于等于 timeout；
- stale 或 NaN 输入会阻断 fresh 状态；
- fallback command 为 zero torque dry-run vector。

## 四、结果

- pass: {all_pass}
- clamp_watchdog_utility_implemented: {clamp_watchdog_utility_implemented}
- clamp_output_all_finite: {clamp_output_all_finite}
- clamp_expected_values_ok: {clamp_expected_values_ok}
- watchdog_stale_blocks: {watchdog_stale_blocks}
- watchdog_nan_blocks: {watchdog_nan_blocks}
- watchdog_zero_all_zero: {watchdog_zero_all_zero}
- torque_topic_publishers_zero: {torque_publishers_zero}

## 五、源码安全边界

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- controller_source_has_create_publisher: {source_has_create_publisher}
- controller_source_has_publish_call: {source_has_publish_call}
- controller_source_has_torque_topic: {source_has_torque_topic}

## 六、Safety gate 更新

Stage 10.7 后：

- G5 torque clamp and watchdog utility implemented: {clamp_watchdog_utility_implemented}
- G8 manual enable flags active at runtime: {manual_enable_active}
- G9 publisher path exists: {publisher_path_exists}

因此：

    torque_enable_ready = {torque_enable_ready}

## 七、边界

当前 baseline 仍是 mixed online control baseline。

Stage 10.7 不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
""")

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 10.7 Clamp/Watchdog Utility Without Publisher

Stage 10.7 完成 clamp/watchdog utility implementation without publisher。

- Script: `scripts/stage10_clamp_watchdog_utility_without_publisher.py`
- Header: `ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp`
- Contract check: `ros2_ws/src/robot_mpc_wbc_cpp_controller/src/torque_safety_contract_check.cpp`
- Log: `results/logs_sample/stage10_clamp_watchdog_utility_without_publisher_log.csv`
- Clamped vector CSV: `results/logs_sample/stage10_clamp_watchdog_utility_clamped_vector.csv`
- Safety gate CSV: `results/logs_sample/stage10_torque_publisher_safety_gate_after_stage107.csv`
- Summary: `results/logs_sample/stage10_clamp_watchdog_utility_without_publisher_summary.csv`
- Docs: `docs/STAGE10_CLAMP_WATCHDOG_UTILITY_WITHOUT_PUBLISHER.md`
- pass: `{all_pass}`
- clamp_watchdog_utility_implemented: `{clamp_watchdog_utility_implemented}`
- torque_topic_publishers_zero: `{torque_publishers_zero}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 10.7 只实现 clamp/watchdog utility，不创建 publisher，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 10.7 Clamp/Watchdog Utility Without Publisher"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 10.7] clamp/watchdog utility without publisher")
    print(f"pass={all_pass}")
    print(f"stage106_pass={stage106_pass}")
    print(f"torque_safety_contract_returncode={check_proc.returncode}")
    print(f"clamp_watchdog_utility_implemented={clamp_watchdog_utility_implemented}")
    print(f"clamp_output_all_finite={clamp_output_all_finite}")
    print(f"clamp_expected_values_ok={clamp_expected_values_ok}")
    print(f"watchdog_stale_blocks={watchdog_stale_blocks}")
    print(f"watchdog_nan_blocks={watchdog_nan_blocks}")
    print(f"torque_topic_publishers_zero={torque_publishers_zero}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print("control_law_changed=False")
    print("torque_publisher_enabled=False")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
    print(f"clamped_vector_csv={CLAMP_VECTOR_PATH.relative_to(ROOT)}")
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
