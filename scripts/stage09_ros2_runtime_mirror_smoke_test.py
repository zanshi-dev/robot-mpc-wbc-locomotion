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

STAGE93_SUMMARY = LOG_DIR / "stage09_ros2_cpp_interface_mirror_skeleton_check_summary.csv"

SUMMARY_PATH = LOG_DIR / "stage09_ros2_runtime_mirror_smoke_test_summary.csv"
LOG_PATH = LOG_DIR / "stage09_ros2_runtime_mirror_smoke_test_log.csv"
TOPIC_OBS_PATH = LOG_DIR / "stage09_ros2_runtime_mirror_topic_observations.csv"
DOC_PATH = ROOT / "docs/STAGE09_ROS2_RUNTIME_MIRROR_SMOKE_TEST.md"

BUILD_STDOUT = LOG_DIR / "stage09_ros2_runtime_mirror_build_stdout.txt"
BUILD_STDERR = LOG_DIR / "stage09_ros2_runtime_mirror_build_stderr.txt"
BRIDGE_STDOUT = LOG_DIR / "stage09_ros2_runtime_mirror_bridge_stdout.txt"
BRIDGE_STDERR = LOG_DIR / "stage09_ros2_runtime_mirror_bridge_stderr.txt"
MIRROR_STDOUT = LOG_DIR / "stage09_ros2_runtime_mirror_node_stdout.txt"
MIRROR_STDERR = LOG_DIR / "stage09_ros2_runtime_mirror_node_stderr.txt"
TOPIC_LIST_PATH = LOG_DIR / "stage09_ros2_runtime_mirror_topic_list.txt"

BRIDGE_PACKAGE = "robot_mpc_wbc_bridge"
CPP_PACKAGE = "robot_mpc_wbc_cpp_interface"
CPP_EXECUTABLE = "go1_interface_mirror_node"

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


def discover_executable(package_name, preferred_keywords):
    proc = bash_cmd(f"ros2 pkg executables {package_name}", timeout=20)
    lines = proc.stdout.splitlines()

    candidates = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) == 2 and parts[0] == package_name:
            candidates.append(parts[1])

    for exe in candidates:
        lowered = exe.lower()
        if all(k.lower() in lowered for k in preferred_keywords):
            return exe, candidates, proc.returncode, proc.stderr

    for exe in candidates:
        lowered = exe.lower()
        if any(k.lower() in lowered for k in preferred_keywords):
            return exe, candidates, proc.returncode, proc.stderr

    return "", candidates, proc.returncode, proc.stderr


def start_ros2_node(package_name, executable_name):
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
    out_path = LOG_DIR / f"stage09_ros2_runtime_mirror_echo_{safe}.txt"
    proc = bash_cmd(f"timeout 6s ros2 topic echo --once {topic}", timeout=10)
    out_path.write_text(proc.stdout + "\nSTDERR:\n" + proc.stderr)
    return proc.returncode, len(proc.stdout.strip()) > 0, out_path.relative_to(ROOT).as_posix()


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    checks = []

    stage93 = load_summary(STAGE93_SUMMARY)
    stage93_pass = as_bool(stage93.get("pass", "False"))

    add_check(checks, "stage93_summary_exists", STAGE93_SUMMARY.exists(), True, STAGE93_SUMMARY.exists(), str(STAGE93_SUMMARY))
    add_check(checks, "stage93_pass", stage93_pass, True, stage93_pass)

    build_rc = build_packages()
    add_check(checks, "colcon_build_returncode", build_rc, 0, build_rc == 0)

    bridge_exe, bridge_candidates, bridge_disc_rc, bridge_disc_err = discover_executable(BRIDGE_PACKAGE, ["bridge"])
    add_check(
        checks,
        "bridge_executable_discovered",
        {"selected": bridge_exe, "candidates": bridge_candidates},
        "non-empty",
        bool(bridge_exe),
        bridge_disc_err,
    )

    cpp_exe, cpp_candidates, cpp_disc_rc, cpp_disc_err = discover_executable(CPP_PACKAGE, ["mirror"])
    if not cpp_exe:
        cpp_exe = CPP_EXECUTABLE if CPP_EXECUTABLE in cpp_candidates else ""

    add_check(
        checks,
        "mirror_executable_discovered",
        {"selected": cpp_exe, "candidates": cpp_candidates},
        CPP_EXECUTABLE,
        cpp_exe == CPP_EXECUTABLE,
        cpp_disc_err,
    )

    bridge_proc = None
    mirror_proc = None

    topic_observations = []

    try:
        if bridge_exe:
            bridge_proc = start_ros2_node(BRIDGE_PACKAGE, bridge_exe)
            time.sleep(3.0)

        bridge_alive = bridge_proc is not None and bridge_proc.poll() is None
        add_check(checks, "bridge_process_alive_after_startup", bridge_alive, True, bridge_alive)

        if cpp_exe:
            mirror_proc = start_ros2_node(CPP_PACKAGE, cpp_exe)
            time.sleep(3.0)

        mirror_alive = mirror_proc is not None and mirror_proc.poll() is None
        add_check(checks, "mirror_process_alive_after_startup", mirror_alive, True, mirror_alive)

        topic_list_proc = bash_cmd("ros2 topic list", timeout=10)
        TOPIC_LIST_PATH.write_text(topic_list_proc.stdout + "\nSTDERR:\n" + topic_list_proc.stderr)
        topic_list = set(x.strip() for x in topic_list_proc.stdout.splitlines() if x.strip())

        add_check(checks, "ros2_topic_list_returncode", topic_list_proc.returncode, 0, topic_list_proc.returncode == 0)

        topics_present = 0
        type_match_count = 0
        published_echo_success_count = 0

        for topic, expected_type in EXPECTED_TOPIC_TYPES.items():
            present = topic in topic_list
            if present:
                topics_present += 1

            type_rc, observed_type, type_err = topic_type(topic)
            type_match = observed_type == expected_type
            if type_match:
                type_match_count += 1

            info_rc, info_out, info_err, pub_count, sub_count = topic_info(topic)

            echo_rc = ""
            echo_nonempty = ""
            echo_file = ""

            if topic in PUBLISHED_TOPICS:
                echo_rc, echo_nonempty, echo_file = echo_once(topic)
                if echo_nonempty:
                    published_echo_success_count += 1

            topic_observations.append({
                "topic": topic,
                "expected_type": expected_type,
                "present_in_topic_list": present,
                "type_returncode": type_rc,
                "observed_type": observed_type,
                "type_match": type_match,
                "publisher_count": pub_count if pub_count is not None else "",
                "subscription_count": sub_count if sub_count is not None else "",
                "echo_once_returncode": echo_rc,
                "echo_once_nonempty": echo_nonempty,
                "echo_file": echo_file,
            })

            add_check(checks, f"topic_present_{topic}", present, True, present)
            add_check(checks, f"topic_type_match_{topic}", observed_type, expected_type, type_match, type_err)

        torque_obs = [x for x in topic_observations if x["topic"] == TORQUE_TOPIC][0]
        torque_publishers = int(torque_obs["publisher_count"]) if str(torque_obs["publisher_count"]).isdigit() else -1
        torque_subscriptions = int(torque_obs["subscription_count"]) if str(torque_obs["subscription_count"]).isdigit() else -1

        add_check(checks, "all_expected_topics_present", topics_present, len(EXPECTED_TOPIC_TYPES), topics_present == len(EXPECTED_TOPIC_TYPES))
        add_check(checks, "all_expected_topic_types_match", type_match_count, len(EXPECTED_TOPIC_TYPES), type_match_count == len(EXPECTED_TOPIC_TYPES))
        add_check(checks, "published_topics_echo_nonempty", published_echo_success_count, len(PUBLISHED_TOPICS), published_echo_success_count == len(PUBLISHED_TOPICS))
        add_check(checks, "torque_cmd_publisher_count_zero", torque_publishers, 0, torque_publishers == 0)
        add_check(checks, "torque_cmd_subscription_count_positive", torque_subscriptions, ">=1", torque_subscriptions >= 1)

    finally:
        stop_process(mirror_proc, MIRROR_STDOUT, MIRROR_STDERR)
        stop_process(bridge_proc, BRIDGE_STDOUT, BRIDGE_STDERR)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    with TOPIC_OBS_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "topic",
                "expected_type",
                "present_in_topic_list",
                "type_returncode",
                "observed_type",
                "type_match",
                "publisher_count",
                "subscription_count",
                "echo_once_returncode",
                "echo_once_nonempty",
                "echo_file",
            ],
        )
        writer.writeheader()
        writer.writerows(topic_observations)

    topic_present_count = sum(1 for x in topic_observations if x["present_in_topic_list"])
    type_match_count = sum(1 for x in topic_observations if x["type_match"])
    published_echo_success_count = sum(1 for x in topic_observations if x["topic"] in PUBLISHED_TOPICS and x["echo_once_nonempty"] is True)

    torque_obs = [x for x in topic_observations if x["topic"] == TORQUE_TOPIC]
    torque_publishers = torque_obs[0]["publisher_count"] if torque_obs else ""
    torque_subscriptions = torque_obs[0]["subscription_count"] if torque_obs else ""

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 9.4"])
        writer.writerow(["test_name", "ros2_runtime_mirror_smoke_test"])
        writer.writerow(["stage93_pass", stage93_pass])
        writer.writerow(["bridge_executable", bridge_exe])
        writer.writerow(["mirror_executable", cpp_exe])
        writer.writerow(["colcon_build_returncode", build_rc])
        writer.writerow(["expected_topic_count", len(EXPECTED_TOPIC_TYPES)])
        writer.writerow(["topic_present_count", topic_present_count])
        writer.writerow(["topic_type_match_count", type_match_count])
        writer.writerow(["published_topic_echo_success_count", published_echo_success_count])
        writer.writerow(["torque_cmd_publisher_count", torque_publishers])
        writer.writerow(["torque_cmd_subscription_count", torque_subscriptions])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_command_published_by_stage94", False])
        writer.writerow(["stage9_scope", "runtime_mirror_smoke_test_only"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["pure_wbc_locomotion_completed", False])
        writer.writerow(["ros2_cpp_realtime_controller_completed", False])
        writer.writerow(["ekf_completed", False])
        writer.writerow(["full_3d_centroidal_mpc_completed", False])
        writer.writerow(["num_checks", len(checks)])
        writer.writerow(["num_failed_checks", sum(1 for row in checks if not row["pass"])])
        writer.writerow(["pass", all_pass])
        writer.writerow(["log_csv", str(LOG_PATH.relative_to(ROOT))])
        writer.writerow(["topic_observations_csv", str(TOPIC_OBS_PATH.relative_to(ROOT))])
        writer.writerow(["summary_csv", str(SUMMARY_PATH.relative_to(ROOT))])
        writer.writerow(["bridge_stdout", str(BRIDGE_STDOUT.relative_to(ROOT))])
        writer.writerow(["bridge_stderr", str(BRIDGE_STDERR.relative_to(ROOT))])
        writer.writerow(["mirror_stdout", str(MIRROR_STDOUT.relative_to(ROOT))])
        writer.writerow(["mirror_stderr", str(MIRROR_STDERR.relative_to(ROOT))])

    DOC_PATH.write_text(f"""# Stage 9.4 ROS2 Runtime Mirror Smoke Test

## 目标

启动 Python MuJoCo bridge 与 C++ interface mirror node，验证 C++ mirror 能看到 Stage 9.2 已冻结的 ROS2 topic contract。

## 本阶段不做的事

- 不发布 /go1/joint_torque_cmd
- 不运行 C++ controller
- 不实现 WBC / MPC / EKF
- 不改变 Stage 8 frozen Python baseline
- 不声明 pure full WBC locomotion

## 运行对象

Bridge package:

    {BRIDGE_PACKAGE}

Bridge executable:

    {bridge_exe}

Mirror package:

    {CPP_PACKAGE}

Mirror executable:

    {cpp_exe}

## 结果

- pass: {all_pass}
- stage93_pass: {stage93_pass}
- colcon_build_returncode: {build_rc}
- topic_present_count: {topic_present_count}
- topic_type_match_count: {type_match_count}
- published_topic_echo_success_count: {published_echo_success_count}
- torque_cmd_publisher_count: {torque_publishers}
- torque_cmd_subscription_count: {torque_subscriptions}

## 输出

- Log: results/logs_sample/stage09_ros2_runtime_mirror_smoke_test_log.csv
- Topic observations: results/logs_sample/stage09_ros2_runtime_mirror_topic_observations.csv
- Summary: results/logs_sample/stage09_ros2_runtime_mirror_smoke_test_summary.csv
- Bridge stdout/stderr: results/logs_sample/stage09_ros2_runtime_mirror_bridge_stdout.txt / stderr.txt
- Mirror stdout/stderr: results/logs_sample/stage09_ros2_runtime_mirror_node_stdout.txt / stderr.txt

## 边界

当前 baseline 仍是 mixed online control baseline。Stage 9.4 只是 runtime mirror smoke test，不是 ROS2/C++ realtime controller。
""")

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 9.4 ROS2 Runtime Mirror Smoke Test

Stage 9.4 完成 ROS2 runtime mirror smoke test。

- Script: `scripts/stage09_ros2_runtime_mirror_smoke_test.py`
- Log: `results/logs_sample/stage09_ros2_runtime_mirror_smoke_test_log.csv`
- Topic observations: `results/logs_sample/stage09_ros2_runtime_mirror_topic_observations.csv`
- Summary: `results/logs_sample/stage09_ros2_runtime_mirror_smoke_test_summary.csv`
- Docs: `docs/STAGE09_ROS2_RUNTIME_MIRROR_SMOKE_TEST.md`
- pass: `{all_pass}`
- topic_present_count: `{topic_present_count}`
- topic_type_match_count: `{type_match_count}`
- published_topic_echo_success_count: `{published_echo_success_count}`
- torque_cmd_publisher_count: `{torque_publishers}`
- control_law_changed: `False`
- torque_command_published_by_stage94: `False`
- stage9_scope: `runtime_mirror_smoke_test_only`

Stage 9.4 只验证 runtime interface mirror，不发布 torque，不写实时 C++ controller，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 9.4 ROS2 Runtime Mirror Smoke Test"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 9.4] ROS2 runtime mirror smoke test")
    print(f"pass={all_pass}")
    print(f"stage93_pass={stage93_pass}")
    print(f"bridge_executable={bridge_exe}")
    print(f"mirror_executable={cpp_exe}")
    print(f"colcon_build_returncode={build_rc}")
    print(f"topic_present_count={topic_present_count}")
    print(f"topic_type_match_count={type_match_count}")
    print(f"published_topic_echo_success_count={published_echo_success_count}")
    print(f"torque_cmd_publisher_count={torque_publishers}")
    print(f"torque_cmd_subscription_count={torque_subscriptions}")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
    print(f"topic_observations_csv={TOPIC_OBS_PATH.relative_to(ROOT)}")
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
