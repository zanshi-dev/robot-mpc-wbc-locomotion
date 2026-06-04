#!/usr/bin/env python3
from pathlib import Path
import csv
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

PKG_DIR = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_interface"
CPP_SOURCE = PKG_DIR / "src/interface_mirror_node.cpp"
PACKAGE_XML = PKG_DIR / "package.xml"
CMAKELISTS = PKG_DIR / "CMakeLists.txt"
LAUNCH_FILE = PKG_DIR / "launch/interface_mirror.launch.py"

STAGE92_SUMMARY = ROOT / "results/logs_sample/stage09_python_baseline_ros2_field_mapping_summary.csv"

LOG_DIR = ROOT / "results/logs_sample"
LOG_PATH = LOG_DIR / "stage09_ros2_cpp_interface_mirror_skeleton_check_log.csv"
SUMMARY_PATH = LOG_DIR / "stage09_ros2_cpp_interface_mirror_skeleton_check_summary.csv"
BUILD_STDOUT = LOG_DIR / "stage09_ros2_cpp_interface_mirror_skeleton_build_stdout.txt"
BUILD_STDERR = LOG_DIR / "stage09_ros2_cpp_interface_mirror_skeleton_build_stderr.txt"
DOC_PATH = ROOT / "docs/STAGE09_ROS2_CPP_INTERFACE_MIRROR_SKELETON.md"

EXPECTED_SUBSCRIPTIONS = [
    "/go1/joint_states",
    "/go1/base_state",
    "/go1/imu",
    "/go1/foot_contacts",
    "/go1/sim_time",
    "/go1/joint_torque_cmd",
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
            for key, value in zip(header, row):
                metrics[key.strip()] = value.strip()
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


def run_colcon_build():
    cmd = (
        "if [ -f /opt/ros/jazzy/setup.bash ]; then source /opt/ros/jazzy/setup.bash; fi; "
        "cd ros2_ws && "
        "colcon build --packages-select robot_mpc_wbc_cpp_interface --symlink-install"
    )

    proc = subprocess.run(
        ["/bin/bash", "-lc", cmd],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )

    BUILD_STDOUT.write_text(proc.stdout)
    BUILD_STDERR.write_text(proc.stderr)

    return proc.returncode


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    stage92 = load_summary(STAGE92_SUMMARY)
    stage92_pass = as_bool(stage92.get("pass", "False"))

    add_check(rows, "stage92_summary_exists", STAGE92_SUMMARY.exists(), True, STAGE92_SUMMARY.exists(), str(STAGE92_SUMMARY))
    add_check(rows, "stage92_pass", stage92_pass, True, stage92_pass)

    for path in [PKG_DIR, PACKAGE_XML, CMAKELISTS, CPP_SOURCE, LAUNCH_FILE]:
        add_check(rows, f"exists_{path.relative_to(ROOT)}", path.exists(), True, path.exists(), str(path))

    cpp_text = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""

    subscription_found_count = 0
    for topic in EXPECTED_SUBSCRIPTIONS:
        found = topic in cpp_text and "create_subscription" in cpp_text
        if found:
            subscription_found_count += 1
        add_check(rows, f"subscription_topic_found_{topic}", found, True, found, "")

    torque_publish_patterns = [
        r"create_publisher\s*<[^>]+>\s*\(\s*\"/go1/joint_torque_cmd\"",
        r"create_publisher\s*<[^>]+>\s*\(\s*'/go1/joint_torque_cmd'",
        r"publish\s*\(",
    ]

    torque_publisher_found = False
    publish_call_found = False

    if CPP_SOURCE.exists():
        torque_publisher_found = bool(re.search(torque_publish_patterns[0], cpp_text)) or bool(re.search(torque_publish_patterns[1], cpp_text))
        publish_call_found = bool(re.search(torque_publish_patterns[2], cpp_text))

    add_check(rows, "no_torque_command_publisher", torque_publisher_found, False, not torque_publisher_found)
    add_check(rows, "no_publish_call_in_skeleton", publish_call_found, False, not publish_call_found)

    build_rc = run_colcon_build()
    add_check(rows, "colcon_build_returncode", build_rc, 0, build_rc == 0)

    all_pass = all(row["pass"] for row in rows)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(rows)

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 9.3"])
        writer.writerow(["test_name", "ros2_cpp_interface_mirror_skeleton_check"])
        writer.writerow(["stage92_pass", stage92_pass])
        writer.writerow(["package_dir", str(PKG_DIR.relative_to(ROOT))])
        writer.writerow(["cpp_source", str(CPP_SOURCE.relative_to(ROOT))])
        writer.writerow(["launch_file", str(LAUNCH_FILE.relative_to(ROOT))])
        writer.writerow(["expected_subscription_count", len(EXPECTED_SUBSCRIPTIONS)])
        writer.writerow(["subscription_found_count", subscription_found_count])
        writer.writerow(["torque_command_publisher_found", torque_publisher_found])
        writer.writerow(["publish_call_found", publish_call_found])
        writer.writerow(["colcon_build_returncode", build_rc])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["stage9_scope", "cpp_interface_mirror_skeleton_only"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["pure_wbc_locomotion_completed", False])
        writer.writerow(["ros2_cpp_realtime_controller_completed", False])
        writer.writerow(["ekf_completed", False])
        writer.writerow(["full_3d_centroidal_mpc_completed", False])
        writer.writerow(["num_checks", len(rows)])
        writer.writerow(["num_failed_checks", sum(1 for row in rows if not row["pass"])])
        writer.writerow(["pass", all_pass])
        writer.writerow(["log_csv", str(LOG_PATH.relative_to(ROOT))])
        writer.writerow(["summary_csv", str(SUMMARY_PATH.relative_to(ROOT))])
        writer.writerow(["build_stdout", str(BUILD_STDOUT.relative_to(ROOT))])
        writer.writerow(["build_stderr", str(BUILD_STDERR.relative_to(ROOT))])

    DOC_PATH.write_text(f"""# Stage 9.3 ROS2/C++ Interface Mirror Skeleton

## 目标

创建一个 C++ ROS2 interface mirror skeleton，用于镜像 Stage 9.2 已记录的 ROS2 topic schema。

本阶段只创建空壳接口节点，不写控制器，不发布 torque command，不改变控制律。

## Package

    ros2_ws/src/robot_mpc_wbc_cpp_interface

## Node

    go1_interface_mirror_node

## 订阅 topic

- /go1/joint_states
- /go1/base_state
- /go1/imu
- /go1/foot_contacts
- /go1/sim_time
- /go1/joint_torque_cmd

## 安全边界

该节点不创建 /go1/joint_torque_cmd publisher。

该节点不调用 publish。

该节点不实现 WBC、MPC、EKF 或 torque controller。

## 编译结果

- colcon_build_returncode: {build_rc}
- pass: {all_pass}

## 输出

- Log: results/logs_sample/stage09_ros2_cpp_interface_mirror_skeleton_check_log.csv
- Summary: results/logs_sample/stage09_ros2_cpp_interface_mirror_skeleton_check_summary.csv
- Build stdout: results/logs_sample/stage09_ros2_cpp_interface_mirror_skeleton_build_stdout.txt
- Build stderr: results/logs_sample/stage09_ros2_cpp_interface_mirror_skeleton_build_stderr.txt

## 运行方式

先 source ROS2 与 workspace：

    source /opt/ros/jazzy/setup.bash
    source ros2_ws/install/setup.bash

运行节点：

    ros2 run robot_mpc_wbc_cpp_interface go1_interface_mirror_node

或使用 launch：

    ros2 launch robot_mpc_wbc_cpp_interface interface_mirror.launch.py

## 边界

当前 baseline 仍是 mixed online control baseline。

本阶段不完成 ROS2/C++ real-time controller，不完成 pure WBC locomotion，不完成 EKF，不完成 full 3D centroidal MPC。
""")

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 9.3 ROS2/C++ Interface Mirror Skeleton

Stage 9.3 创建并编译了 C++ ROS2 interface mirror skeleton。

- Package: `ros2_ws/src/robot_mpc_wbc_cpp_interface`
- Node: `go1_interface_mirror_node`
- Script: `scripts/stage09_ros2_cpp_interface_mirror_skeleton_check.py`
- Log: `results/logs_sample/stage09_ros2_cpp_interface_mirror_skeleton_check_log.csv`
- Summary: `results/logs_sample/stage09_ros2_cpp_interface_mirror_skeleton_check_summary.csv`
- Docs: `docs/STAGE09_ROS2_CPP_INTERFACE_MIRROR_SKELETON.md`
- pass: `{all_pass}`
- subscription_found_count: `{subscription_found_count}`
- torque_command_publisher_found: `{torque_publisher_found}`
- publish_call_found: `{publish_call_found}`
- colcon_build_returncode: `{build_rc}`
- control_law_changed: `False`
- stage9_scope: `cpp_interface_mirror_skeleton_only`

Stage 9.3 只创建 C++ interface mirror skeleton，不发布 torque command，不写实时 controller，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 9.3 ROS2/C++ Interface Mirror Skeleton"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 9.3] ROS2/C++ interface mirror skeleton")
    print(f"pass={all_pass}")
    print(f"stage92_pass={stage92_pass}")
    print(f"subscription_found_count={subscription_found_count}")
    print(f"torque_command_publisher_found={torque_publisher_found}")
    print(f"publish_call_found={publish_call_found}")
    print(f"colcon_build_returncode={build_rc}")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
    print(f"summary_csv={SUMMARY_PATH.relative_to(ROOT)}")
    print(f"doc={DOC_PATH.relative_to(ROOT)}")

    if not all_pass:
        print("\nFailed checks:")
        for row in rows:
            if not row["pass"]:
                print(f"- {row['check']}: value={row['value']} expected={row['expected']} detail={row['detail']}")
        sys.exit(2)


if __name__ == "__main__":
    main()
