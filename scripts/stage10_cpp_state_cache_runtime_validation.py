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

STAGE101_SUMMARY = LOG_DIR / "stage10_disabled_cpp_controller_skeleton_check_summary.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"

SUMMARY_PATH = LOG_DIR / "stage10_cpp_state_cache_runtime_validation_summary.csv"
LOG_PATH = LOG_DIR / "stage10_cpp_state_cache_runtime_validation_log.csv"
TOPIC_OBS_PATH = LOG_DIR / "stage10_cpp_state_cache_runtime_validation_topic_observations.csv"
DOC_PATH = ROOT / "docs/STAGE10_CPP_STATE_CACHE_RUNTIME_VALIDATION.md"

BUILD_STDOUT = LOG_DIR / "stage10_cpp_state_cache_runtime_validation_build_stdout.txt"
BUILD_STDERR = LOG_DIR / "stage10_cpp_state_cache_runtime_validation_build_stderr.txt"
BRIDGE_STDOUT = LOG_DIR / "stage10_cpp_state_cache_runtime_validation_bridge_stdout.txt"
BRIDGE_STDERR = LOG_DIR / "stage10_cpp_state_cache_runtime_validation_bridge_stderr.txt"
CONTROLLER_STDOUT = LOG_DIR / "stage10_cpp_state_cache_runtime_validation_controller_stdout.txt"
CONTROLLER_STDERR = LOG_DIR / "stage10_cpp_state_cache_runtime_validation_controller_stderr.txt"

BRIDGE_PACKAGE = "robot_mpc_wbc_bridge"
BRIDGE_EXECUTABLE = "mujoco_bridge_node"
CONTROLLER_PACKAGE = "robot_mpc_wbc_cpp_controller"
CONTROLLER_EXECUTABLE = "go1_disabled_controller_node"

STATE_TOPICS = {
    "/go1/joint_states": "sensor_msgs/msg/JointState",
    "/go1/base_state": "std_msgs/msg/Float64MultiArray",
    "/go1/imu": "sensor_msgs/msg/Imu",
    "/go1/foot_contacts": "std_msgs/msg/Int32MultiArray",
    "/go1/sim_time": "std_msgs/msg/Float64",
}

TORQUE_TOPIC = "/go1/joint_torque_cmd"
TORQUE_TOPIC_TYPE = "std_msgs/msg/Float64MultiArray"


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


def echo_once(topic):
    safe = topic.strip("/").replace("/", "_")
    out_path = LOG_DIR / f"stage10_cpp_state_cache_echo_{safe}.txt"
    proc = bash_cmd(f"timeout 6s ros2 topic echo --once {topic}", timeout=10)
    out_path.write_text(proc.stdout + "\\nSTDERR:\\n" + proc.stderr)
    return proc.returncode, len(proc.stdout.strip()) > 0, out_path.relative_to(ROOT).as_posix()


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    checks = []
    topic_rows = []

    stage101 = load_summary(STAGE101_SUMMARY)
    stage101_pass = as_bool(stage101.get("pass", "False"))
    stage101_torque_enabled = as_bool(stage101.get("torque_publisher_enabled", "True"))
    stage101_control_changed = as_bool(stage101.get("control_law_changed", "True"))

    add_check(checks, "stage101_summary_exists", STAGE101_SUMMARY.exists(), True, STAGE101_SUMMARY.exists(), str(STAGE101_SUMMARY))
    add_check(checks, "stage101_pass", stage101_pass, True, stage101_pass)
    add_check(checks, "stage101_torque_publisher_enabled", stage101_torque_enabled, False, not stage101_torque_enabled)
    add_check(checks, "stage101_control_law_changed", stage101_control_changed, False, not stage101_control_changed)

    cpp_text = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""

    source_has_create_publisher = "create_publisher" in cpp_text
    source_has_publish_call = ".publish(" in cpp_text or "->publish(" in cpp_text
    source_has_torque_topic = TORQUE_TOPIC in cpp_text

    state_cache_markers = [
        "joint_position_ = msg->position",
        "joint_velocity_ = msg->velocity",
        "base_state_ = msg->data",
        "foot_contacts_[i] = msg->data[i]",
        "sim_time_ = msg->data",
        "zero_torque_dry_run_",
    ]

    missing_state_cache_markers = [marker for marker in state_cache_markers if marker not in cpp_text]

    add_check(checks, "cpp_source_exists", CPP_SOURCE.exists(), True, CPP_SOURCE.exists(), str(CPP_SOURCE))
    add_check(checks, "source_has_no_create_publisher", source_has_create_publisher, False, not source_has_create_publisher)
    add_check(checks, "source_has_no_publish_call", source_has_publish_call, False, not source_has_publish_call)
    add_check(checks, "source_does_not_reference_torque_topic", source_has_torque_topic, False, not source_has_torque_topic)
    add_check(checks, "state_cache_markers_present", missing_state_cache_markers, "[]", len(missing_state_cache_markers) == 0)

    build_rc = build_packages()
    add_check(checks, "colcon_build_returncode", build_rc, 0, build_rc == 0)

    bridge_proc = None
    controller_proc = None

    try:
        bridge_proc = start_node(BRIDGE_PACKAGE, BRIDGE_EXECUTABLE)
        time.sleep(3.0)
        bridge_alive = bridge_proc.poll() is None
        add_check(checks, "bridge_alive_after_startup", bridge_alive, True, bridge_alive)

        controller_proc = start_node(CONTROLLER_PACKAGE, CONTROLLER_EXECUTABLE)
        time.sleep(4.0)
        controller_alive = controller_proc.poll() is None
        add_check(checks, "disabled_controller_alive_after_startup", controller_alive, True, controller_alive)

        state_topic_present_count = 0
        state_topic_type_match_count = 0
        state_topic_pubsub_ok_count = 0
        state_topic_echo_ok_count = 0

        for topic, expected_type in STATE_TOPICS.items():
            type_rc, observed_type, type_err = topic_type(topic)
            info_rc, info_out, info_err, pub_count, sub_count = topic_info(topic)
            echo_rc, echo_nonempty, echo_file = echo_once(topic)

            present = type_rc == 0 and bool(observed_type)
            type_match = observed_type == expected_type
            pubsub_ok = (
                isinstance(pub_count, int) and pub_count >= 1 and
                isinstance(sub_count, int) and sub_count >= 1
            )

            if present:
                state_topic_present_count += 1
            if type_match:
                state_topic_type_match_count += 1
            if pubsub_ok:
                state_topic_pubsub_ok_count += 1
            if echo_nonempty:
                state_topic_echo_ok_count += 1

            topic_rows.append({
                "topic": topic,
                "expected_type": expected_type,
                "observed_type": observed_type,
                "present": present,
                "type_match": type_match,
                "publisher_count": pub_count if pub_count is not None else "",
                "subscription_count": sub_count if sub_count is not None else "",
                "pubsub_ok": pubsub_ok,
                "echo_once_returncode": echo_rc,
                "echo_once_nonempty": echo_nonempty,
                "echo_file": echo_file,
            })

        type_rc, observed_type, type_err = topic_type(TORQUE_TOPIC)
        info_rc, info_out, info_err, pub_count, sub_count = topic_info(TORQUE_TOPIC)

        torque_type_match = observed_type == TORQUE_TOPIC_TYPE
        torque_publishers_zero = isinstance(pub_count, int) and pub_count == 0
        torque_subscribers_positive = isinstance(sub_count, int) and sub_count >= 1

        topic_rows.append({
            "topic": TORQUE_TOPIC,
            "expected_type": TORQUE_TOPIC_TYPE,
            "observed_type": observed_type,
            "present": bool(observed_type),
            "type_match": torque_type_match,
            "publisher_count": pub_count if pub_count is not None else "",
            "subscription_count": sub_count if sub_count is not None else "",
            "pubsub_ok": torque_publishers_zero and torque_subscribers_positive,
            "echo_once_returncode": "",
            "echo_once_nonempty": "",
            "echo_file": "",
        })

        add_check(checks, "state_topic_present_count", state_topic_present_count, len(STATE_TOPICS), state_topic_present_count == len(STATE_TOPICS))
        add_check(checks, "state_topic_type_match_count", state_topic_type_match_count, len(STATE_TOPICS), state_topic_type_match_count == len(STATE_TOPICS))
        add_check(checks, "state_topic_pubsub_ok_count", state_topic_pubsub_ok_count, len(STATE_TOPICS), state_topic_pubsub_ok_count == len(STATE_TOPICS))
        add_check(checks, "state_topic_echo_ok_count", state_topic_echo_ok_count, len(STATE_TOPICS), state_topic_echo_ok_count == len(STATE_TOPICS))
        add_check(checks, "torque_topic_type_match", observed_type, TORQUE_TOPIC_TYPE, torque_type_match, type_err)
        add_check(checks, "torque_topic_publishers_zero", pub_count, 0, torque_publishers_zero)
        add_check(checks, "torque_topic_subscribers_positive", sub_count, ">=1", torque_subscribers_positive)

    finally:
        stop_process(controller_proc, CONTROLLER_STDOUT, CONTROLLER_STDERR)
        stop_process(bridge_proc, BRIDGE_STDOUT, BRIDGE_STDERR)

    with TOPIC_OBS_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "topic",
                "expected_type",
                "observed_type",
                "present",
                "type_match",
                "publisher_count",
                "subscription_count",
                "pubsub_ok",
                "echo_once_returncode",
                "echo_once_nonempty",
                "echo_file",
            ],
        )
        writer.writeheader()
        writer.writerows(topic_rows)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 10.2"])
        writer.writerow(["test_name", "cpp_state_cache_runtime_validation"])
        writer.writerow(["stage101_pass", stage101_pass])
        writer.writerow(["colcon_build_returncode", build_rc])
        writer.writerow(["source_has_no_create_publisher", not source_has_create_publisher])
        writer.writerow(["source_has_no_publish_call", not source_has_publish_call])
        writer.writerow(["source_does_not_reference_torque_topic", not source_has_torque_topic])
        writer.writerow(["state_cache_markers_present", len(missing_state_cache_markers) == 0])
        writer.writerow(["state_topic_expected_count", len(STATE_TOPICS)])
        writer.writerow(["state_topic_present_count", state_topic_present_count])
        writer.writerow(["state_topic_type_match_count", state_topic_type_match_count])
        writer.writerow(["state_topic_pubsub_ok_count", state_topic_pubsub_ok_count])
        writer.writerow(["state_topic_echo_ok_count", state_topic_echo_ok_count])
        writer.writerow(["torque_topic_type_match", torque_type_match])
        writer.writerow(["torque_topic_publishers_zero", torque_publishers_zero])
        writer.writerow(["torque_topic_subscribers_positive", torque_subscribers_positive])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_publisher_enabled", False])
        writer.writerow(["torque_command_published_by_stage102", False])
        writer.writerow(["stage10_scope", "cpp_state_cache_runtime_validation_only"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["ros2_cpp_realtime_controller_completed", False])
        writer.writerow(["pure_wbc_locomotion_completed", False])
        writer.writerow(["ekf_completed", False])
        writer.writerow(["full_3d_centroidal_mpc_completed", False])
        writer.writerow(["num_checks", len(checks)])
        writer.writerow(["num_failed_checks", sum(1 for row in checks if not row["pass"])])
        writer.writerow(["pass", all_pass])
        writer.writerow(["log_csv", str(LOG_PATH.relative_to(ROOT))])
        writer.writerow(["topic_observations_csv", str(TOPIC_OBS_PATH.relative_to(ROOT))])
        writer.writerow(["summary_csv", str(SUMMARY_PATH.relative_to(ROOT))])
        writer.writerow(["build_stdout", str(BUILD_STDOUT.relative_to(ROOT))])
        writer.writerow(["build_stderr", str(BUILD_STDERR.relative_to(ROOT))])
        writer.writerow(["bridge_stdout", str(BRIDGE_STDOUT.relative_to(ROOT))])
        writer.writerow(["bridge_stderr", str(BRIDGE_STDERR.relative_to(ROOT))])
        writer.writerow(["controller_stdout", str(CONTROLLER_STDOUT.relative_to(ROOT))])
        writer.writerow(["controller_stderr", str(CONTROLLER_STDERR.relative_to(ROOT))])

    DOC_PATH.write_text(f"""# Stage 10.2 C++ State Cache Runtime Validation

## 目标

验证 disabled-by-default C++ controller skeleton 的 state cache 输入链路。

本阶段只验证状态订阅与缓存逻辑，不创建 torque publisher，不调用 publish，不改变控制律。

## 验证内容

- Stage 10.1 已通过；
- C++ source 无 create_publisher；
- C++ source 无 publish call；
- C++ source 不引用 /go1/joint_torque_cmd；
- C++ source 包含 state cache 写入逻辑；
- bridge 与 disabled controller 可同时启动；
- 5 个状态 topic 存在、类型匹配、有 publisher/subscriber，并可 echo 到非空样本；
- /go1/joint_torque_cmd publisher count 为 0。

## 结果

- pass: {all_pass}
- state_topic_present_count: {state_topic_present_count}
- state_topic_type_match_count: {state_topic_type_match_count}
- state_topic_pubsub_ok_count: {state_topic_pubsub_ok_count}
- state_topic_echo_ok_count: {state_topic_echo_ok_count}
- torque_topic_publishers_zero: {torque_publishers_zero}

## 输出

- Log: results/logs_sample/stage10_cpp_state_cache_runtime_validation_log.csv
- Topic observations: results/logs_sample/stage10_cpp_state_cache_runtime_validation_topic_observations.csv
- Summary: results/logs_sample/stage10_cpp_state_cache_runtime_validation_summary.csv
- Build stdout/stderr: results/logs_sample/stage10_cpp_state_cache_runtime_validation_build_stdout.txt / stderr.txt
- Controller stdout/stderr: results/logs_sample/stage10_cpp_state_cache_runtime_validation_controller_stdout.txt / stderr.txt

## 边界

当前 baseline 仍是 mixed online control baseline。

本阶段不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
""")

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 10.2 C++ State Cache Runtime Validation

Stage 10.2 完成 disabled-by-default C++ controller skeleton 的 state cache runtime validation。

- Script: `scripts/stage10_cpp_state_cache_runtime_validation.py`
- Log: `results/logs_sample/stage10_cpp_state_cache_runtime_validation_log.csv`
- Topic observations: `results/logs_sample/stage10_cpp_state_cache_runtime_validation_topic_observations.csv`
- Summary: `results/logs_sample/stage10_cpp_state_cache_runtime_validation_summary.csv`
- Docs: `docs/STAGE10_CPP_STATE_CACHE_RUNTIME_VALIDATION.md`
- pass: `{all_pass}`
- state_topic_present_count: `{state_topic_present_count}`
- state_topic_type_match_count: `{state_topic_type_match_count}`
- state_topic_pubsub_ok_count: `{state_topic_pubsub_ok_count}`
- state_topic_echo_ok_count: `{state_topic_echo_ok_count}`
- torque_topic_publishers_zero: `{torque_publishers_zero}`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 10.2 只验证 state cache 输入链路，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 10.2 C++ State Cache Runtime Validation"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\\n\\n" + block + "\\n")

    print("[Stage 10.2] C++ state cache runtime validation")
    print(f"pass={all_pass}")
    print(f"stage101_pass={stage101_pass}")
    print(f"state_topic_present_count={state_topic_present_count}")
    print(f"state_topic_type_match_count={state_topic_type_match_count}")
    print(f"state_topic_pubsub_ok_count={state_topic_pubsub_ok_count}")
    print(f"state_topic_echo_ok_count={state_topic_echo_ok_count}")
    print(f"torque_topic_publishers_zero={torque_publishers_zero}")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
    print(f"topic_observations_csv={TOPIC_OBS_PATH.relative_to(ROOT)}")
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
