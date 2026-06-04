#!/usr/bin/env python3
from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"
DOC_PATH = ROOT / "docs/STAGE09_CPP_MIRROR_CONTRACT_REPORT.md"
SUMMARY_PATH = LOG_DIR / "stage09_cpp_mirror_contract_report_summary.csv"
LOG_PATH = LOG_DIR / "stage09_cpp_mirror_contract_report_log.csv"

STAGE_SUMMARIES = {
    "Stage 9.0": LOG_DIR / "stage09_ros2_cpp_interface_contract_inventory_summary.csv",
    "Stage 9.1": LOG_DIR / "stage09_ros2_topic_schema_snapshot_summary.csv",
    "Stage 9.2": LOG_DIR / "stage09_python_baseline_ros2_field_mapping_summary.csv",
    "Stage 9.3": LOG_DIR / "stage09_ros2_cpp_interface_mirror_skeleton_check_summary.csv",
    "Stage 9.4": LOG_DIR / "stage09_ros2_runtime_mirror_smoke_test_summary.csv",
}

REQUIRED_FILES = [
    "docs/STAGE09_ROS2_CPP_INTERFACE_CONTRACT_INVENTORY.md",
    "docs/STAGE09_ROS2_TOPIC_SCHEMA_SNAPSHOT.md",
    "docs/STAGE09_PYTHON_BASELINE_ROS2_FIELD_MAPPING.md",
    "docs/STAGE09_ROS2_CPP_INTERFACE_MIRROR_SKELETON.md",
    "docs/STAGE09_ROS2_RUNTIME_MIRROR_SMOKE_TEST.md",
    "ros2_ws/src/robot_mpc_wbc_cpp_interface/package.xml",
    "ros2_ws/src/robot_mpc_wbc_cpp_interface/CMakeLists.txt",
    "ros2_ws/src/robot_mpc_wbc_cpp_interface/src/interface_mirror_node.cpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_interface/launch/interface_mirror.launch.py",
    "results/logs_sample/stage09_ros2_cpp_interface_topic_contract_map.csv",
    "results/logs_sample/stage09_ros2_topic_schema_snapshot_map.csv",
    "results/logs_sample/stage09_python_baseline_ros2_field_mapping.csv",
    "results/logs_sample/stage09_ros2_runtime_mirror_topic_observations.csv",
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


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    checks = []
    summaries = {}

    for stage, path in STAGE_SUMMARIES.items():
        exists = path.exists()
        add_check(checks, f"{stage}_summary_exists", exists, True, exists, str(path))
        metrics = load_summary(path)
        summaries[stage] = metrics
        stage_pass = as_bool(metrics.get("pass", "False"))
        add_check(checks, f"{stage}_pass", stage_pass, True, stage_pass)

    for rel in REQUIRED_FILES:
        path = ROOT / rel
        add_check(checks, f"required_file_exists_{rel}", path.exists(), True, path.exists(), rel)

    s90 = summaries.get("Stage 9.0", {})
    s91 = summaries.get("Stage 9.1", {})
    s92 = summaries.get("Stage 9.2", {})
    s93 = summaries.get("Stage 9.3", {})
    s94 = summaries.get("Stage 9.4", {})

    add_check(checks, "stage90_all_expected_topics_found", as_bool(s90.get("all_expected_topics_found", "False")), True, as_bool(s90.get("all_expected_topics_found", "False")))
    add_check(checks, "stage91_all_topic_schemas_available", as_bool(s91.get("all_topic_schemas_available", "False")), True, as_bool(s91.get("all_topic_schemas_available", "False")))
    add_check(checks, "stage92_all_types_match", as_bool(s92.get("all_types_match_stage91_schema", "False")), True, as_bool(s92.get("all_types_match_stage91_schema", "False")))
    add_check(checks, "stage93_no_torque_publisher", s93.get("torque_command_publisher_found", ""), "False", s93.get("torque_command_publisher_found", "") == "False")
    add_check(checks, "stage93_no_publish_call", s93.get("publish_call_found", ""), "False", s93.get("publish_call_found", "") == "False")
    add_check(checks, "stage94_torque_publisher_zero", s94.get("torque_cmd_publisher_count", ""), "0", s94.get("torque_cmd_publisher_count", "") == "0")

    control_law_changed_any = any(
        as_bool(metrics.get("control_law_changed", "False"))
        for metrics in summaries.values()
    )

    ros2_cpp_realtime_completed_any = any(
        as_bool(metrics.get("ros2_cpp_realtime_controller_completed", "False"))
        for metrics in summaries.values()
    )

    pure_wbc_completed_any = any(
        as_bool(metrics.get("pure_wbc_locomotion_completed", "False"))
        for metrics in summaries.values()
    )

    add_check(checks, "control_law_changed_any", control_law_changed_any, False, not control_law_changed_any)
    add_check(checks, "ros2_cpp_realtime_controller_completed_any", ros2_cpp_realtime_completed_any, False, not ros2_cpp_realtime_completed_any)
    add_check(checks, "pure_wbc_locomotion_completed_any", pure_wbc_completed_any, False, not pure_wbc_completed_any)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    stage_rows = []
    for stage, metrics in summaries.items():
        stage_rows.append(
            f"| {stage} | {metrics.get('test_name', '')} | {metrics.get('stage9_scope', '')} | {metrics.get('pass', '')} | {metrics.get('control_law_changed', '')} |"
        )

    DOC_PATH.write_text(f"""# Stage 9.5 C++ Mirror Contract Report

## 一、结论

Stage 9.0–9.4 已完成 ROS2/C++ interface mirror 的第一轮闭环。

当前成果是 interface mirror，不是实时控制器。

本阶段没有改变控制律，没有发布 torque command，没有完成 pure full WBC locomotion。

## 二、当前 C++ mirror package

Package:

    ros2_ws/src/robot_mpc_wbc_cpp_interface

Node:

    go1_interface_mirror_node

Launch:

    ros2_ws/src/robot_mpc_wbc_cpp_interface/launch/interface_mirror.launch.py

## 三、推荐运行方式

先 source 环境：

    source /opt/ros/jazzy/setup.bash
    source ros2_ws/install/setup.bash

运行 MuJoCo bridge：

    ros2 run robot_mpc_wbc_bridge mujoco_bridge_node

另一个终端运行 C++ mirror：

    ros2 run robot_mpc_wbc_cpp_interface go1_interface_mirror_node

或：

    ros2 launch robot_mpc_wbc_cpp_interface interface_mirror.launch.py

## 四、Stage 9.0–9.4 汇总

| 阶段 | 测试名 | scope | pass | control_law_changed |
|---|---|---|---:|---:|
{chr(10).join(stage_rows)}

## 五、已确认 topic contract

Stage 9.0–9.4 已确认：

- /go1/joint_states
- /go1/base_state
- /go1/imu
- /go1/foot_contacts
- /go1/sim_time
- /go1/joint_torque_cmd

关键 runtime smoke test 结果：

- topic_present_count: {s94.get("topic_present_count", "")}
- topic_type_match_count: {s94.get("topic_type_match_count", "")}
- published_topic_echo_success_count: {s94.get("published_topic_echo_success_count", "")}
- torque_cmd_publisher_count: {s94.get("torque_cmd_publisher_count", "")}
- torque_cmd_subscription_count: {s94.get("torque_cmd_subscription_count", "")}

## 六、关键安全边界

C++ mirror node 当前只订阅 topic。

它不创建 /go1/joint_torque_cmd publisher。

它不调用 publish。

它不运行 MPC、WBC、EKF 或任何 torque controller。

## 七、当前 baseline 边界

当前 baseline 仍是 mixed online control baseline。

它不是 pure full WBC locomotion。

Stage 9.5 不代表以下事项完成：

- ROS2/C++ real-time controller
- EKF
- full 3D centroidal MPC
- base velocity tracking
- hardware deployment

## 八、输出文件

- Log: results/logs_sample/stage09_cpp_mirror_contract_report_log.csv
- Summary: results/logs_sample/stage09_cpp_mirror_contract_report_summary.csv
- Docs: docs/STAGE09_CPP_MIRROR_CONTRACT_REPORT.md

## 九、结论

Stage 9.0–9.5 可作为 ROS2/C++ interface mirror baseline。

下一步若继续推进，应进入 Stage 9.6 C++ mirror runtime contract guard，而不是直接写控制器。
""")

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 9.5"])
        writer.writerow(["test_name", "cpp_mirror_contract_report"])
        writer.writerow(["stage90_pass", summaries["Stage 9.0"].get("pass", "False")])
        writer.writerow(["stage91_pass", summaries["Stage 9.1"].get("pass", "False")])
        writer.writerow(["stage92_pass", summaries["Stage 9.2"].get("pass", "False")])
        writer.writerow(["stage93_pass", summaries["Stage 9.3"].get("pass", "False")])
        writer.writerow(["stage94_pass", summaries["Stage 9.4"].get("pass", "False")])
        writer.writerow(["topic_present_count", s94.get("topic_present_count", "")])
        writer.writerow(["topic_type_match_count", s94.get("topic_type_match_count", "")])
        writer.writerow(["published_topic_echo_success_count", s94.get("published_topic_echo_success_count", "")])
        writer.writerow(["torque_cmd_publisher_count", s94.get("torque_cmd_publisher_count", "")])
        writer.writerow(["torque_cmd_subscription_count", s94.get("torque_cmd_subscription_count", "")])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_command_published_by_stage95", False])
        writer.writerow(["stage9_scope", "cpp_mirror_contract_report_only"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["pure_wbc_locomotion_completed", False])
        writer.writerow(["ros2_cpp_realtime_controller_completed", False])
        writer.writerow(["ekf_completed", False])
        writer.writerow(["full_3d_centroidal_mpc_completed", False])
        writer.writerow(["num_checks", len(checks)])
        writer.writerow(["num_failed_checks", sum(1 for row in checks if not row["pass"])])
        writer.writerow(["pass", all_pass])
        writer.writerow(["log_csv", str(LOG_PATH.relative_to(ROOT))])
        writer.writerow(["summary_csv", str(SUMMARY_PATH.relative_to(ROOT))])
        writer.writerow(["doc", str(DOC_PATH.relative_to(ROOT))])

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 9.5 C++ Mirror Contract Report

Stage 9.5 生成了 C++ mirror contract report，汇总 Stage 9.0–9.4。

- Script: `scripts/stage09_cpp_mirror_contract_report.py`
- Log: `results/logs_sample/stage09_cpp_mirror_contract_report_log.csv`
- Summary: `results/logs_sample/stage09_cpp_mirror_contract_report_summary.csv`
- Docs: `docs/STAGE09_CPP_MIRROR_CONTRACT_REPORT.md`
- pass: `{all_pass}`
- topic_present_count: `{s94.get("topic_present_count", "")}`
- topic_type_match_count: `{s94.get("topic_type_match_count", "")}`
- torque_cmd_publisher_count: `{s94.get("torque_cmd_publisher_count", "")}`
- control_law_changed: `False`
- stage9_scope: `cpp_mirror_contract_report_only`

Stage 9.5 只汇总 interface mirror contract，不发布 torque，不写实时 C++ controller，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 9.5 C++ Mirror Contract Report"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 9.5] C++ mirror contract report")
    print(f"pass={all_pass}")
    print(f"topic_present_count={s94.get('topic_present_count', '')}")
    print(f"topic_type_match_count={s94.get('topic_type_match_count', '')}")
    print(f"torque_cmd_publisher_count={s94.get('torque_cmd_publisher_count', '')}")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
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
