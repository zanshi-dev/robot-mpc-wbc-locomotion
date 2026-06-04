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

STAGE102_SUMMARY = LOG_DIR / "stage10_cpp_state_cache_runtime_validation_summary.csv"

PKG_DIR = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller"
CPP_SOURCE = PKG_DIR / "src/disabled_controller_node.cpp"
HEADER = PKG_DIR / "include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"
CHECK_SOURCE = PKG_DIR / "src/zero_torque_dry_run_contract_check.cpp"
CMAKE = PKG_DIR / "CMakeLists.txt"

SUMMARY_PATH = LOG_DIR / "stage10_zero_torque_dry_run_internal_validation_summary.csv"
LOG_PATH = LOG_DIR / "stage10_zero_torque_dry_run_internal_validation_log.csv"
VECTOR_PATH = LOG_DIR / "stage10_zero_torque_dry_run_vector.csv"
DOC_PATH = ROOT / "docs/STAGE10_ZERO_TORQUE_DRY_RUN_INTERNAL_VALIDATION.md"

BUILD_STDOUT = LOG_DIR / "stage10_zero_torque_dry_run_build_stdout.txt"
BUILD_STDERR = LOG_DIR / "stage10_zero_torque_dry_run_build_stderr.txt"
CHECK_STDOUT = LOG_DIR / "stage10_zero_torque_dry_run_contract_check_stdout.txt"
CHECK_STDERR = LOG_DIR / "stage10_zero_torque_dry_run_contract_check_stderr.txt"
BRIDGE_STDOUT = LOG_DIR / "stage10_zero_torque_dry_run_bridge_stdout.txt"
BRIDGE_STDERR = LOG_DIR / "stage10_zero_torque_dry_run_bridge_stderr.txt"
CONTROLLER_STDOUT = LOG_DIR / "stage10_zero_torque_dry_run_controller_stdout.txt"
CONTROLLER_STDERR = LOG_DIR / "stage10_zero_torque_dry_run_controller_stderr.txt"

BRIDGE_PACKAGE = "robot_mpc_wbc_bridge"
BRIDGE_EXECUTABLE = "mujoco_bridge_node"
CONTROLLER_PACKAGE = "robot_mpc_wbc_cpp_controller"
CONTROLLER_EXECUTABLE = "go1_disabled_controller_node"
CHECK_EXECUTABLE = "zero_torque_dry_run_contract_check"

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


def parse_metric_csv_text(text):
    metrics = {}
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        return metrics
    for row in rows[1:]:
        if len(row) >= 2:
            metrics[row[0].strip()] = row[1].strip()
    return metrics


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

    stage102 = load_summary(STAGE102_SUMMARY)
    stage102_pass = as_bool(stage102.get("pass", "False"))
    stage102_torque_enabled = as_bool(stage102.get("torque_publisher_enabled", "True"))
    stage102_control_changed = as_bool(stage102.get("control_law_changed", "True"))

    add_check(checks, "stage102_summary_exists", STAGE102_SUMMARY.exists(), True, STAGE102_SUMMARY.exists(), str(STAGE102_SUMMARY))
    add_check(checks, "stage102_pass", stage102_pass, True, stage102_pass)
    add_check(checks, "stage102_torque_publisher_enabled", stage102_torque_enabled, False, not stage102_torque_enabled)
    add_check(checks, "stage102_control_law_changed", stage102_control_changed, False, not stage102_control_changed)

    for path in [CPP_SOURCE, HEADER, CHECK_SOURCE, CMAKE]:
        add_check(checks, f"exists_{path.relative_to(ROOT)}", path.exists(), True, path.exists(), str(path))

    cpp_text = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    header_text = HEADER.read_text(errors="replace") if HEADER.exists() else ""
    check_text = CHECK_SOURCE.read_text(errors="replace") if CHECK_SOURCE.exists() else ""
    cmake_text = CMAKE.read_text(errors="replace") if CMAKE.exists() else ""

    source_has_create_publisher = "create_publisher" in cpp_text
    source_has_publish_call = ".publish(" in cpp_text or "->publish(" in cpp_text
    source_has_torque_topic = TORQUE_TOPIC in cpp_text
    source_uses_zero_factory = "makeZeroTorqueDryRun()" in cpp_text
    header_declares_12 = "kGo1NumActuatedJoints = 12" in header_text
    header_has_zero_factory = "makeZeroTorqueDryRun" in header_text and "tau.fill(0.0)" in header_text
    check_executable_registered = CHECK_EXECUTABLE in cmake_text and CHECK_SOURCE.name in cmake_text

    add_check(checks, "source_has_no_create_publisher", source_has_create_publisher, False, not source_has_create_publisher)
    add_check(checks, "source_has_no_publish_call", source_has_publish_call, False, not source_has_publish_call)
    add_check(checks, "source_does_not_reference_torque_topic", source_has_torque_topic, False, not source_has_torque_topic)
    add_check(checks, "source_uses_zero_torque_factory", source_uses_zero_factory, True, source_uses_zero_factory)
    add_check(checks, "header_declares_12_actuated_joints", header_declares_12, True, header_declares_12)
    add_check(checks, "header_has_zero_torque_factory", header_has_zero_factory, True, header_has_zero_factory)
    add_check(checks, "contract_check_source_uses_header", "zero_torque_dry_run.hpp" in check_text, True, "zero_torque_dry_run.hpp" in check_text)
    add_check(checks, "contract_check_executable_registered", check_executable_registered, True, check_executable_registered)

    build_rc = build_packages()
    add_check(checks, "colcon_build_returncode", build_rc, 0, build_rc == 0)

    check_proc = bash_cmd(f"ros2 run {CONTROLLER_PACKAGE} {CHECK_EXECUTABLE}", timeout=10)
    CHECK_STDOUT.write_text(check_proc.stdout)
    CHECK_STDERR.write_text(check_proc.stderr)
    contract_metrics = parse_metric_csv_text(check_proc.stdout)

    zero_size = contract_metrics.get("zero_torque_size", "")
    zero_size_ok = as_bool(contract_metrics.get("zero_torque_size_ok", "False"))
    zero_all_finite = as_bool(contract_metrics.get("zero_torque_all_finite", "False"))
    zero_all_zero = as_bool(contract_metrics.get("zero_torque_all_zero", "False"))
    zero_max_abs = contract_metrics.get("zero_torque_max_abs", "")
    zero_l1 = contract_metrics.get("zero_torque_l1", "")

    add_check(checks, "zero_torque_contract_returncode", check_proc.returncode, 0, check_proc.returncode == 0)
    add_check(checks, "zero_torque_size", zero_size, "12", zero_size == "12")
    add_check(checks, "zero_torque_size_ok", zero_size_ok, True, zero_size_ok)
    add_check(checks, "zero_torque_all_finite", zero_all_finite, True, zero_all_finite)
    add_check(checks, "zero_torque_all_zero", zero_all_zero, True, zero_all_zero)
    add_check(checks, "zero_torque_max_abs", zero_max_abs, "0", str(zero_max_abs) in {"0", "0.0", "0.000000"})
    add_check(checks, "zero_torque_l1", zero_l1, "0", str(zero_l1) in {"0", "0.0", "0.000000"})

    vector_rows = []
    for i in range(12):
        key = f"tau_{i}"
        value = contract_metrics.get(key, "")
        vector_rows.append({"joint_index": i, "tau": value, "is_zero": value in {"0", "0.0", "0.000000"}})

    with VECTOR_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["joint_index", "tau", "is_zero"])
        writer.writeheader()
        writer.writerows(vector_rows)

    all_vector_entries_zero = all(row["is_zero"] for row in vector_rows)
    add_check(checks, "all_vector_entries_zero", all_vector_entries_zero, True, all_vector_entries_zero)

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

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 10.3"])
        writer.writerow(["test_name", "zero_torque_dry_run_internal_validation"])
        writer.writerow(["stage102_pass", stage102_pass])
        writer.writerow(["colcon_build_returncode", build_rc])
        writer.writerow(["zero_torque_contract_returncode", check_proc.returncode])
        writer.writerow(["zero_torque_size", zero_size])
        writer.writerow(["zero_torque_size_ok", zero_size_ok])
        writer.writerow(["zero_torque_all_finite", zero_all_finite])
        writer.writerow(["zero_torque_all_zero", zero_all_zero])
        writer.writerow(["zero_torque_max_abs", zero_max_abs])
        writer.writerow(["zero_torque_l1", zero_l1])
        writer.writerow(["all_vector_entries_zero", all_vector_entries_zero])
        writer.writerow(["source_has_no_create_publisher", not source_has_create_publisher])
        writer.writerow(["source_has_no_publish_call", not source_has_publish_call])
        writer.writerow(["source_does_not_reference_torque_topic", not source_has_torque_topic])
        writer.writerow(["source_uses_zero_torque_factory", source_uses_zero_factory])
        writer.writerow(["header_declares_12_actuated_joints", header_declares_12])
        writer.writerow(["torque_topic_publishers_zero", torque_publishers_zero])
        writer.writerow(["torque_topic_subscribers_positive", torque_subscribers_positive])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_publisher_enabled", False])
        writer.writerow(["torque_command_published_by_stage103", False])
        writer.writerow(["stage10_scope", "zero_torque_dry_run_internal_validation_only"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["ros2_cpp_realtime_controller_completed", False])
        writer.writerow(["pure_wbc_locomotion_completed", False])
        writer.writerow(["ekf_completed", False])
        writer.writerow(["full_3d_centroidal_mpc_completed", False])
        writer.writerow(["num_checks", len(checks)])
        writer.writerow(["num_failed_checks", sum(1 for row in checks if not row["pass"])])
        writer.writerow(["pass", all_pass])
        writer.writerow(["log_csv", str(LOG_PATH.relative_to(ROOT))])
        writer.writerow(["vector_csv", str(VECTOR_PATH.relative_to(ROOT))])
        writer.writerow(["summary_csv", str(SUMMARY_PATH.relative_to(ROOT))])
        writer.writerow(["build_stdout", str(BUILD_STDOUT.relative_to(ROOT))])
        writer.writerow(["build_stderr", str(BUILD_STDERR.relative_to(ROOT))])
        writer.writerow(["contract_check_stdout", str(CHECK_STDOUT.relative_to(ROOT))])
        writer.writerow(["contract_check_stderr", str(CHECK_STDERR.relative_to(ROOT))])
        writer.writerow(["bridge_stdout", str(BRIDGE_STDOUT.relative_to(ROOT))])
        writer.writerow(["bridge_stderr", str(BRIDGE_STDERR.relative_to(ROOT))])
        writer.writerow(["controller_stdout", str(CONTROLLER_STDOUT.relative_to(ROOT))])
        writer.writerow(["controller_stderr", str(CONTROLLER_STDERR.relative_to(ROOT))])

    DOC_PATH.write_text(f"""# Stage 10.3 Zero Torque Dry-run Internal Command Validation

## 目标

验证 disabled-by-default C++ controller skeleton 的内部 zero torque dry-run command 对象。

本阶段不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 新增 C++ 文件

- ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp
- ros2_ws/src/robot_mpc_wbc_cpp_controller/src/zero_torque_dry_run_contract_check.cpp

## 验证内容

- zero torque vector 长度为 12；
- 所有元素 finite；
- 所有元素等于 0；
- max abs 为 0；
- L1 norm 为 0；
- disabled controller 源码使用 zero torque factory；
- disabled controller 源码无 create_publisher；
- disabled controller 源码无 publish call；
- disabled controller 源码不引用 /go1/joint_torque_cmd；
- runtime 下 /go1/joint_torque_cmd publisher count 为 0。

## 结果

- pass: {all_pass}
- zero_torque_size: {zero_size}
- zero_torque_all_finite: {zero_all_finite}
- zero_torque_all_zero: {zero_all_zero}
- zero_torque_max_abs: {zero_max_abs}
- zero_torque_l1: {zero_l1}
- torque_topic_publishers_zero: {torque_publishers_zero}

## 输出

- Log: results/logs_sample/stage10_zero_torque_dry_run_internal_validation_log.csv
- Vector CSV: results/logs_sample/stage10_zero_torque_dry_run_vector.csv
- Summary: results/logs_sample/stage10_zero_torque_dry_run_internal_validation_summary.csv
- Docs: docs/STAGE10_ZERO_TORQUE_DRY_RUN_INTERNAL_VALIDATION.md

## 边界

当前 baseline 仍是 mixed online control baseline。

本阶段不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
""")

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 10.3 Zero Torque Dry-run Internal Command Validation

Stage 10.3 完成 zero torque dry-run internal command validation。

- Script: `scripts/stage10_zero_torque_dry_run_internal_validation.py`
- Header: `ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp`
- Contract check: `ros2_ws/src/robot_mpc_wbc_cpp_controller/src/zero_torque_dry_run_contract_check.cpp`
- Log: `results/logs_sample/stage10_zero_torque_dry_run_internal_validation_log.csv`
- Vector CSV: `results/logs_sample/stage10_zero_torque_dry_run_vector.csv`
- Summary: `results/logs_sample/stage10_zero_torque_dry_run_internal_validation_summary.csv`
- Docs: `docs/STAGE10_ZERO_TORQUE_DRY_RUN_INTERNAL_VALIDATION.md`
- pass: `{all_pass}`
- zero_torque_size: `{zero_size}`
- zero_torque_all_zero: `{zero_all_zero}`
- zero_torque_max_abs: `{zero_max_abs}`
- torque_topic_publishers_zero: `{torque_publishers_zero}`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 10.3 只验证内部 zero torque dry-run command，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 10.3 Zero Torque Dry-run Internal Command Validation"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 10.3] zero torque dry-run internal validation")
    print(f"pass={all_pass}")
    print(f"stage102_pass={stage102_pass}")
    print(f"zero_torque_contract_returncode={check_proc.returncode}")
    print(f"zero_torque_size={zero_size}")
    print(f"zero_torque_all_finite={zero_all_finite}")
    print(f"zero_torque_all_zero={zero_all_zero}")
    print(f"zero_torque_max_abs={zero_max_abs}")
    print(f"zero_torque_l1={zero_l1}")
    print(f"torque_topic_publishers_zero={torque_publishers_zero}")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
    print(f"vector_csv={VECTOR_PATH.relative_to(ROOT)}")
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
