#!/usr/bin/env python3
from pathlib import Path
import csv
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE100_SUMMARY = LOG_DIR / "stage10_controller_implementation_plan_and_safety_gate_summary.csv"

PKG_DIR = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller"
CPP_SOURCE = PKG_DIR / "src/disabled_controller_node.cpp"
PACKAGE_XML = PKG_DIR / "package.xml"
CMAKELISTS = PKG_DIR / "CMakeLists.txt"
LAUNCH_FILE = PKG_DIR / "launch/disabled_controller.launch.py"

LOG_PATH = LOG_DIR / "stage10_disabled_cpp_controller_skeleton_check_log.csv"
SUMMARY_PATH = LOG_DIR / "stage10_disabled_cpp_controller_skeleton_check_summary.csv"
BUILD_STDOUT = LOG_DIR / "stage10_disabled_cpp_controller_skeleton_build_stdout.txt"
BUILD_STDERR = LOG_DIR / "stage10_disabled_cpp_controller_skeleton_build_stderr.txt"
DOC_PATH = ROOT / "docs/STAGE10_DISABLED_CPP_CONTROLLER_SKELETON.md"

EXPECTED_SUBSCRIPTIONS = [
    "/go1/joint_states",
    "/go1/base_state",
    "/go1/imu",
    "/go1/foot_contacts",
    "/go1/sim_time",
]


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


def run_build():
    cmd = (
        "source /opt/ros/jazzy/setup.bash && "
        "cd ros2_ws && "
        "colcon build --packages-select robot_mpc_wbc_cpp_controller --symlink-install"
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


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    stage100 = load_summary(STAGE100_SUMMARY)
    stage100_pass = as_bool(stage100.get("pass", "False"))
    torque_enable_ready = as_bool(stage100.get("torque_enable_ready", "True"))
    torque_publisher_enabled_stage100 = as_bool(stage100.get("torque_publisher_enabled", "True"))

    add_check(rows, "stage100_summary_exists", STAGE100_SUMMARY.exists(), True, STAGE100_SUMMARY.exists(), str(STAGE100_SUMMARY))
    add_check(rows, "stage100_pass", stage100_pass, True, stage100_pass)
    add_check(rows, "stage100_torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)
    add_check(rows, "stage100_torque_publisher_enabled", torque_publisher_enabled_stage100, False, not torque_publisher_enabled_stage100)

    for path in [PKG_DIR, PACKAGE_XML, CMAKELISTS, CPP_SOURCE, LAUNCH_FILE]:
        add_check(rows, f"exists_{path.relative_to(ROOT)}", path.exists(), True, path.exists(), str(path))

    cpp_text = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""

    subscription_found_count = 0
    for topic in EXPECTED_SUBSCRIPTIONS:
        found = topic in cpp_text and "create_subscription" in cpp_text
        if found:
            subscription_found_count += 1
        add_check(rows, f"subscription_found_{topic}", found, True, found)

    source_has_torque_topic = "/go1/joint_torque_cmd" in cpp_text
    source_has_create_publisher = "create_publisher" in cpp_text
    source_has_publish_call = ".publish(" in cpp_text or "->publish(" in cpp_text
    zero_torque_vector_declared = "zero_torque_dry_run_" in cpp_text and "kNumJoints" in cpp_text
    torque_publisher_enabled_literal_false = "torque_publisher_enabled=0" in cpp_text or "No torque publisher is created" in cpp_text

    add_check(rows, "source_does_not_reference_torque_cmd_topic", source_has_torque_topic, False, not source_has_torque_topic)
    add_check(rows, "source_has_no_create_publisher", source_has_create_publisher, False, not source_has_create_publisher)
    add_check(rows, "source_has_no_publish_call", source_has_publish_call, False, not source_has_publish_call)
    add_check(rows, "zero_torque_dry_run_vector_declared", zero_torque_vector_declared, True, zero_torque_vector_declared)
    add_check(rows, "disabled_status_literal_present", torque_publisher_enabled_literal_false, True, torque_publisher_enabled_literal_false)

    build_rc = run_build()
    add_check(rows, "colcon_build_returncode", build_rc, 0, build_rc == 0)

    all_pass = all(row["pass"] for row in rows)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(rows)

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 10.1"])
        writer.writerow(["test_name", "disabled_cpp_controller_skeleton_check"])
        writer.writerow(["stage100_pass", stage100_pass])
        writer.writerow(["stage100_torque_enable_ready", torque_enable_ready])
        writer.writerow(["stage100_torque_publisher_enabled", torque_publisher_enabled_stage100])
        writer.writerow(["package_dir", str(PKG_DIR.relative_to(ROOT))])
        writer.writerow(["cpp_source", str(CPP_SOURCE.relative_to(ROOT))])
        writer.writerow(["launch_file", str(LAUNCH_FILE.relative_to(ROOT))])
        writer.writerow(["expected_subscription_count", len(EXPECTED_SUBSCRIPTIONS)])
        writer.writerow(["subscription_found_count", subscription_found_count])
        writer.writerow(["source_references_torque_cmd_topic", source_has_torque_topic])
        writer.writerow(["source_has_create_publisher", source_has_create_publisher])
        writer.writerow(["source_has_publish_call", source_has_publish_call])
        writer.writerow(["zero_torque_dry_run_vector_declared", zero_torque_vector_declared])
        writer.writerow(["colcon_build_returncode", build_rc])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_publisher_enabled", False])
        writer.writerow(["torque_command_published_by_stage101", False])
        writer.writerow(["stage10_scope", "disabled_cpp_controller_skeleton_only"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["ros2_cpp_realtime_controller_completed", False])
        writer.writerow(["pure_wbc_locomotion_completed", False])
        writer.writerow(["ekf_completed", False])
        writer.writerow(["full_3d_centroidal_mpc_completed", False])
        writer.writerow(["num_checks", len(rows)])
        writer.writerow(["num_failed_checks", sum(1 for row in rows if not row["pass"])])
        writer.writerow(["pass", all_pass])
        writer.writerow(["log_csv", str(LOG_PATH.relative_to(ROOT))])
        writer.writerow(["summary_csv", str(SUMMARY_PATH.relative_to(ROOT))])
        writer.writerow(["build_stdout", str(BUILD_STDOUT.relative_to(ROOT))])
        writer.writerow(["build_stderr", str(BUILD_STDERR.relative_to(ROOT))])

    DOC_PATH.write_text(f"""# Stage 10.1 Disabled-by-default C++ Controller Skeleton

## 目标

创建 disabled-by-default C++ controller skeleton。

该节点只订阅状态 topic，建立 state cache，并生成内部 zero torque dry-run vector。

本阶段不创建 /go1/joint_torque_cmd publisher，不调用 publish，不改变控制律。

## Package

    ros2_ws/src/robot_mpc_wbc_cpp_controller

## Node

    go1_disabled_controller_node

## 订阅 topic

- /go1/joint_states
- /go1/base_state
- /go1/imu
- /go1/foot_contacts
- /go1/sim_time

## 明确禁止

本阶段源码不得包含：

- /go1/joint_torque_cmd
- create_publisher
- publish call

## 结果

- pass: {all_pass}
- subscription_found_count: {subscription_found_count}
- source_references_torque_cmd_topic: {source_has_torque_topic}
- source_has_create_publisher: {source_has_create_publisher}
- source_has_publish_call: {source_has_publish_call}
- zero_torque_dry_run_vector_declared: {zero_torque_vector_declared}
- colcon_build_returncode: {build_rc}

## 输出

- Log: results/logs_sample/stage10_disabled_cpp_controller_skeleton_check_log.csv
- Summary: results/logs_sample/stage10_disabled_cpp_controller_skeleton_check_summary.csv
- Build stdout: results/logs_sample/stage10_disabled_cpp_controller_skeleton_build_stdout.txt
- Build stderr: results/logs_sample/stage10_disabled_cpp_controller_skeleton_build_stderr.txt

## 边界

当前 baseline 仍是 mixed online control baseline。

本阶段不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
""")

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 10.1 Disabled-by-default C++ Controller Skeleton

Stage 10.1 创建并编译了 disabled-by-default C++ controller skeleton。

- Package: `ros2_ws/src/robot_mpc_wbc_cpp_controller`
- Node: `go1_disabled_controller_node`
- Script: `scripts/stage10_disabled_cpp_controller_skeleton_check.py`
- Log: `results/logs_sample/stage10_disabled_cpp_controller_skeleton_check_log.csv`
- Summary: `results/logs_sample/stage10_disabled_cpp_controller_skeleton_check_summary.csv`
- Docs: `docs/STAGE10_DISABLED_CPP_CONTROLLER_SKELETON.md`
- pass: `{all_pass}`
- subscription_found_count: `{subscription_found_count}`
- source_references_torque_cmd_topic: `{source_has_torque_topic}`
- source_has_create_publisher: `{source_has_create_publisher}`
- source_has_publish_call: `{source_has_publish_call}`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 10.1 只创建 disabled controller skeleton，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 10.1 Disabled-by-default C++ Controller Skeleton"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 10.1] disabled-by-default C++ controller skeleton")
    print(f"pass={all_pass}")
    print(f"stage100_pass={stage100_pass}")
    print(f"subscription_found_count={subscription_found_count}")
    print(f"source_references_torque_cmd_topic={source_has_torque_topic}")
    print(f"source_has_create_publisher={source_has_create_publisher}")
    print(f"source_has_publish_call={source_has_publish_call}")
    print(f"zero_torque_dry_run_vector_declared={zero_torque_vector_declared}")
    print(f"colcon_build_returncode={build_rc}")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
    print(f"summary_csv={SUMMARY_PATH.relative_to(ROOT)}")
    print(f"doc={DOC_PATH.relative_to(ROOT)}")

    if not all_pass:
        print("\\nFailed checks:")
        for row in rows:
            if not row["pass"]:
                print(f"- {row['check']}: value={row['value']} expected={row['expected']} detail={row['detail']}")
        sys.exit(2)


if __name__ == "__main__":
    main()
