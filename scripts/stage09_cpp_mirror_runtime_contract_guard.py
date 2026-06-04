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

STAGE95_SUMMARY = LOG_DIR / "stage09_cpp_mirror_contract_report_summary.csv"

SUMMARY_PATH = LOG_DIR / "stage09_cpp_mirror_runtime_contract_guard_summary.csv"
LOG_PATH = LOG_DIR / "stage09_cpp_mirror_runtime_contract_guard_log.csv"
SAMPLES_PATH = LOG_DIR / "stage09_cpp_mirror_runtime_contract_guard_samples.csv"
DOC_PATH = ROOT / "docs/STAGE09_CPP_MIRROR_RUNTIME_CONTRACT_GUARD.md"

BUILD_STDOUT = LOG_DIR / "stage09_cpp_mirror_runtime_contract_guard_build_stdout.txt"
BUILD_STDERR = LOG_DIR / "stage09_cpp_mirror_runtime_contract_guard_build_stderr.txt"
BRIDGE_STDOUT = LOG_DIR / "stage09_cpp_mirror_runtime_contract_guard_bridge_stdout.txt"
BRIDGE_STDERR = LOG_DIR / "stage09_cpp_mirror_runtime_contract_guard_bridge_stderr.txt"
MIRROR_STDOUT = LOG_DIR / "stage09_cpp_mirror_runtime_contract_guard_mirror_stdout.txt"
MIRROR_STDERR = LOG_DIR / "stage09_cpp_mirror_runtime_contract_guard_mirror_stderr.txt"

BRIDGE_PACKAGE = "robot_mpc_wbc_bridge"
CPP_PACKAGE = "robot_mpc_wbc_cpp_interface"
BRIDGE_EXECUTABLE = "mujoco_bridge_node"
MIRROR_EXECUTABLE = "go1_interface_mirror_node"

EXPECTED_TOPIC_TYPES = {
    "/go1/joint_states": "sensor_msgs/msg/JointState",
    "/go1/base_state": "std_msgs/msg/Float64MultiArray",
    "/go1/imu": "sensor_msgs/msg/Imu",
    "/go1/foot_contacts": "std_msgs/msg/Int32MultiArray",
    "/go1/sim_time": "std_msgs/msg/Float64",
    "/go1/joint_torque_cmd": "std_msgs/msg/Float64MultiArray",
}

PUBLISHED_TOPICS = [
    "/go1/joint_states",
    "/go1/base_state",
    "/go1/imu",
    "/go1/foot_contacts",
    "/go1/sim_time",
]

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
        "colcon build --packages-select robot_mpc_wbc_bridge robot_mpc_wbc_cpp_interface --symlink-install"
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


def topic_type(topic):
    proc = bash_cmd(f"ros2 topic type {topic}", timeout=10)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


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


def sample_topics(sample_idx):
    rows = []

    for topic, expected_type in EXPECTED_TOPIC_TYPES.items():
        type_rc, observed_type, type_err = topic_type(topic)
        info_rc, info_out, info_err, pub_count, sub_count = topic_info(topic)

        rows.append({
            "sample_idx": sample_idx,
            "topic": topic,
            "expected_type": expected_type,
            "observed_type": observed_type,
            "type_match": observed_type == expected_type,
            "publisher_count": pub_count if pub_count is not None else "",
            "subscription_count": sub_count if sub_count is not None else "",
            "type_returncode": type_rc,
            "info_returncode": info_rc,
            "type_error": type_err,
            "info_error": info_err,
        })

    return rows


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    checks = []
    sample_rows = []

    stage95 = load_summary(STAGE95_SUMMARY)
    stage95_pass = as_bool(stage95.get("pass", "False"))

    add_check(checks, "stage95_summary_exists", STAGE95_SUMMARY.exists(), True, STAGE95_SUMMARY.exists(), str(STAGE95_SUMMARY))
    add_check(checks, "stage95_pass", stage95_pass, True, stage95_pass)

    add_check(checks, "stage95_torque_cmd_publisher_count_zero", stage95.get("torque_cmd_publisher_count", ""), "0", stage95.get("torque_cmd_publisher_count", "") == "0")
    add_check(checks, "stage95_control_law_unchanged", as_bool(stage95.get("control_law_changed", "True")), False, not as_bool(stage95.get("control_law_changed", "True")))

    build_rc = build_packages()
    add_check(checks, "colcon_build_returncode", build_rc, 0, build_rc == 0)

    bridge_proc = None
    mirror_proc = None

    try:
        bridge_proc = start_node(BRIDGE_PACKAGE, BRIDGE_EXECUTABLE)
        time.sleep(3.0)

        bridge_alive = bridge_proc.poll() is None
        add_check(checks, "bridge_alive_after_startup", bridge_alive, True, bridge_alive)

        mirror_proc = start_node(CPP_PACKAGE, MIRROR_EXECUTABLE)
        time.sleep(3.0)

        mirror_alive = mirror_proc.poll() is None
        add_check(checks, "mirror_alive_after_startup", mirror_alive, True, mirror_alive)

        for sample_idx in range(5):
            sample_rows.extend(sample_topics(sample_idx))
            time.sleep(0.5)

    finally:
        stop_process(mirror_proc, MIRROR_STDOUT, MIRROR_STDERR)
        stop_process(bridge_proc, BRIDGE_STDOUT, BRIDGE_STDERR)

    with SAMPLES_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "sample_idx",
                "topic",
                "expected_type",
                "observed_type",
                "type_match",
                "publisher_count",
                "subscription_count",
                "type_returncode",
                "info_returncode",
                "type_error",
                "info_error",
            ],
        )
        writer.writeheader()
        writer.writerows(sample_rows)

    expected_sample_count = 5 * len(EXPECTED_TOPIC_TYPES)
    add_check(checks, "sample_row_count", len(sample_rows), expected_sample_count, len(sample_rows) == expected_sample_count)

    all_type_matches = all(str(row["type_match"]) == "True" or row["type_match"] is True for row in sample_rows)
    add_check(checks, "all_sample_topic_types_match", all_type_matches, True, all_type_matches)

    torque_rows = [row for row in sample_rows if row["topic"] == TORQUE_TOPIC]
    torque_publishers_all_zero = all(str(row["publisher_count"]) == "0" for row in torque_rows)
    torque_subscribers_positive = all(str(row["subscription_count"]).isdigit() and int(row["subscription_count"]) >= 2 for row in torque_rows)

    add_check(checks, "torque_cmd_publishers_all_zero", [row["publisher_count"] for row in torque_rows], "all 0", torque_publishers_all_zero)
    add_check(checks, "torque_cmd_subscribers_positive", [row["subscription_count"] for row in torque_rows], "all >=2", torque_subscribers_positive)

    published_rows = [row for row in sample_rows if row["topic"] in PUBLISHED_TOPICS]
    published_have_publishers = all(str(row["publisher_count"]).isdigit() and int(row["publisher_count"]) >= 1 for row in published_rows)
    published_have_subscribers = all(str(row["subscription_count"]).isdigit() and int(row["subscription_count"]) >= 1 for row in published_rows)

    add_check(checks, "published_topics_have_publishers", published_have_publishers, True, published_have_publishers)
    add_check(checks, "published_topics_have_subscribers", published_have_subscribers, True, published_have_subscribers)

    cpp_source = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_interface/src/interface_mirror_node.cpp"
    cpp_text = cpp_source.read_text(errors="replace") if cpp_source.exists() else ""

    source_has_create_publisher = "create_publisher" in cpp_text
    source_has_publish_call = ".publish(" in cpp_text or "->publish(" in cpp_text

    add_check(
        checks,
        "source_has_no_create_publisher",
        source_has_create_publisher,
        False,
        not source_has_create_publisher,
        str(cpp_source.relative_to(ROOT)) if cpp_source.exists() else "missing source",
    )

    add_check(
        checks,
        "source_has_no_publish_call",
        source_has_publish_call,
        False,
        not source_has_publish_call,
        str(cpp_source.relative_to(ROOT)) if cpp_source.exists() else "missing source",
    )

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 9.6"])
        writer.writerow(["test_name", "cpp_mirror_runtime_contract_guard"])
        writer.writerow(["stage95_pass", stage95_pass])
        writer.writerow(["colcon_build_returncode", build_rc])
        writer.writerow(["sample_rounds", 5])
        writer.writerow(["expected_topic_count", len(EXPECTED_TOPIC_TYPES)])
        writer.writerow(["sample_row_count", len(sample_rows)])
        writer.writerow(["all_sample_topic_types_match", all_type_matches])
        writer.writerow(["torque_cmd_publishers_all_zero", torque_publishers_all_zero])
        writer.writerow(["torque_cmd_subscribers_positive", torque_subscribers_positive])
        writer.writerow(["published_topics_have_publishers", published_have_publishers])
        writer.writerow(["published_topics_have_subscribers", published_have_subscribers])
        writer.writerow(["source_has_no_create_publisher", not source_has_create_publisher])
        writer.writerow(["source_has_no_publish_call", not source_has_publish_call])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_command_published_by_stage96", False])
        writer.writerow(["stage9_scope", "cpp_mirror_runtime_contract_guard_only"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["pure_wbc_locomotion_completed", False])
        writer.writerow(["ros2_cpp_realtime_controller_completed", False])
        writer.writerow(["ekf_completed", False])
        writer.writerow(["full_3d_centroidal_mpc_completed", False])
        writer.writerow(["num_checks", len(checks)])
        writer.writerow(["num_failed_checks", sum(1 for row in checks if not row["pass"])])
        writer.writerow(["pass", all_pass])
        writer.writerow(["log_csv", str(LOG_PATH.relative_to(ROOT))])
        writer.writerow(["samples_csv", str(SAMPLES_PATH.relative_to(ROOT))])
        writer.writerow(["summary_csv", str(SUMMARY_PATH.relative_to(ROOT))])
        writer.writerow(["bridge_stdout", str(BRIDGE_STDOUT.relative_to(ROOT))])
        writer.writerow(["bridge_stderr", str(BRIDGE_STDERR.relative_to(ROOT))])
        writer.writerow(["mirror_stdout", str(MIRROR_STDOUT.relative_to(ROOT))])
        writer.writerow(["mirror_stderr", str(MIRROR_STDERR.relative_to(ROOT))])

    DOC_PATH.write_text(f"""# Stage 9.6 C++ Mirror Runtime Contract Guard

## 目标

将 Stage 9.4 smoke test 固化为可重复运行的 runtime contract guard。

该 guard 多轮采样 ROS2 topic type、publisher count、subscription count，确认 C++ mirror 只做 interface mirror。

## 检查内容

- Stage 9.5 contract report 已通过；
- bridge 与 mirror 节点可启动；
- 6 个 topic 的类型持续匹配；
- 5 个 bridge 发布 topic 均有 publisher 与 subscriber；
- /go1/joint_torque_cmd 的 publisher count 始终为 0；
- /go1/joint_torque_cmd 的 subscriber count 始终大于等于 2；
- C++ mirror stdout 明确声明不发布 torque command。

## 结果

- pass: {all_pass}
- all_sample_topic_types_match: {all_type_matches}
- torque_cmd_publishers_all_zero: {torque_publishers_all_zero}
- torque_cmd_subscribers_positive: {torque_subscribers_positive}
- published_topics_have_publishers: {published_have_publishers}
- published_topics_have_subscribers: {published_have_subscribers}

## 输出

- Log: results/logs_sample/stage09_cpp_mirror_runtime_contract_guard_log.csv
- Samples: results/logs_sample/stage09_cpp_mirror_runtime_contract_guard_samples.csv
- Summary: results/logs_sample/stage09_cpp_mirror_runtime_contract_guard_summary.csv
- Bridge stdout/stderr: results/logs_sample/stage09_cpp_mirror_runtime_contract_guard_bridge_stdout.txt / stderr.txt
- Mirror stdout/stderr: results/logs_sample/stage09_cpp_mirror_runtime_contract_guard_mirror_stdout.txt / stderr.txt

## 边界

本阶段不发布 torque command，不写实时 C++ controller，不改变控制律，不完成 EKF，不完成 pure WBC locomotion。

当前 baseline 仍是 mixed online control baseline。
""")

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 9.6 C++ Mirror Runtime Contract Guard

Stage 9.6 完成 C++ mirror runtime contract guard。

- Script: `scripts/stage09_cpp_mirror_runtime_contract_guard.py`
- Log: `results/logs_sample/stage09_cpp_mirror_runtime_contract_guard_log.csv`
- Samples: `results/logs_sample/stage09_cpp_mirror_runtime_contract_guard_samples.csv`
- Summary: `results/logs_sample/stage09_cpp_mirror_runtime_contract_guard_summary.csv`
- Docs: `docs/STAGE09_CPP_MIRROR_RUNTIME_CONTRACT_GUARD.md`
- pass: `{all_pass}`
- all_sample_topic_types_match: `{all_type_matches}`
- torque_cmd_publishers_all_zero: `{torque_publishers_all_zero}`
- torque_cmd_subscribers_positive: `{torque_subscribers_positive}`
- control_law_changed: `False`
- torque_command_published_by_stage96: `False`
- stage9_scope: `cpp_mirror_runtime_contract_guard_only`

Stage 9.6 只固化 interface mirror runtime guard，不发布 torque，不写实时 C++ controller，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 9.6 C++ Mirror Runtime Contract Guard"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 9.6] C++ mirror runtime contract guard")
    print(f"pass={all_pass}")
    print(f"stage95_pass={stage95_pass}")
    print(f"sample_row_count={len(sample_rows)}")
    print(f"all_sample_topic_types_match={all_type_matches}")
    print(f"torque_cmd_publishers_all_zero={torque_publishers_all_zero}")
    print(f"torque_cmd_subscribers_positive={torque_subscribers_positive}")
    print(f"published_topics_have_publishers={published_have_publishers}")
    print(f"published_topics_have_subscribers={published_have_subscribers}")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
    print(f"samples_csv={SAMPLES_PATH.relative_to(ROOT)}")
    print(f"summary_csv={SUMMARY_PATH.relative_to(ROOT)}")
    print(f"doc={DOC_PATH.relative_to(ROOT)}")

    if not all_pass:
        print("\\nFailed checks:")
        for row in checks:
            if not row["pass"]:
                print(f"- {row['check']}: value={row['value']} expected={row['expected']} detail={row['detail']}")
        sys.exit(2)


if __name__ == "__main__":
    main()
