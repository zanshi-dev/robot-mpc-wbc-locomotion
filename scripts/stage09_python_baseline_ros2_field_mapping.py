#!/usr/bin/env python3
from pathlib import Path
import csv
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

STAGE91_SUMMARY = ROOT / "results/logs_sample/stage09_ros2_topic_schema_snapshot_summary.csv"
STAGE91_SCHEMA_MAP = ROOT / "results/logs_sample/stage09_ros2_topic_schema_snapshot_map.csv"
STAGE8_ADAPTER = ROOT / "scripts/common/go1_runtime_interface.py"
STAGE8_ENTRYPOINT = ROOT / "scripts/stage08_adapter_backed_stage07_recommended_test.py"

BRIDGE_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_bridge/robot_mpc_wbc_bridge/mujoco_bridge_node.py"

LOG_DIR = ROOT / "results/logs_sample"
FIELD_MAP_PATH = LOG_DIR / "stage09_python_baseline_ros2_field_mapping.csv"
LOG_PATH = LOG_DIR / "stage09_python_baseline_ros2_field_mapping_log.csv"
SUMMARY_PATH = LOG_DIR / "stage09_python_baseline_ros2_field_mapping_summary.csv"
DOC_PATH = ROOT / "docs/STAGE09_PYTHON_BASELINE_ROS2_FIELD_MAPPING.md"

EXPECTED_MAPPING_ROWS = [
    {
        "direction": "publish",
        "topic": "/go1/joint_states",
        "ros_type": "sensor_msgs/msg/JointState",
        "ros_field": "name",
        "python_baseline_source": "MuJoCo actuator / joint labels",
        "expected_shape_or_length": "12",
        "order_contract": "MJ_LEG_ORDER: FR, FL, RR, RL; JOINT_ORDER: hip, thigh, calf",
        "adapter_contract": "scripts/common/go1_runtime_interface.py: MJ_JOINT_LABELS",
        "stage9_use": "C++ mirror must preserve joint label order",
    },
    {
        "direction": "publish",
        "topic": "/go1/joint_states",
        "ros_type": "sensor_msgs/msg/JointState",
        "ros_field": "position",
        "python_baseline_source": "MuJoCo qpos actuated slice",
        "expected_shape_or_length": "12",
        "order_contract": "qpos actuated starts after free joint; adapter handles reorder contract",
        "adapter_contract": "mujoco_qpos_to_pinocchio / pinocchio_qpos_to_mujoco",
        "stage9_use": "C++ mirror must not hard-code a conflicting joint order",
    },
    {
        "direction": "publish",
        "topic": "/go1/joint_states",
        "ros_type": "sensor_msgs/msg/JointState",
        "ros_field": "velocity",
        "python_baseline_source": "MuJoCo qvel actuated slice",
        "expected_shape_or_length": "12",
        "order_contract": "qvel actuated starts after 6 floating-base velocities; adapter handles reorder contract",
        "adapter_contract": "mujoco_qvel_to_pinocchio / pinocchio_qvel_to_mujoco",
        "stage9_use": "C++ mirror must preserve actuator-order joint velocity layout",
    },
    {
        "direction": "publish",
        "topic": "/go1/joint_states",
        "ros_type": "sensor_msgs/msg/JointState",
        "ros_field": "effort",
        "python_baseline_source": "MuJoCo actuator torque / ctrl feedback if populated by bridge",
        "expected_shape_or_length": "12",
        "order_contract": "torque order follows MuJoCo actuator order",
        "adapter_contract": "mujoco_tau_to_pinocchio / pinocchio_tau_to_mujoco",
        "stage9_use": "C++ mirror must keep command and feedback torque order identical",
    },
    {
        "direction": "publish",
        "topic": "/go1/base_state",
        "ros_type": "std_msgs/msg/Float64MultiArray",
        "ros_field": "data",
        "python_baseline_source": "MuJoCo floating-base qpos/qvel",
        "expected_shape_or_length": "implementation-defined Float64MultiArray; must be documented before C++ mirror",
        "order_contract": "MuJoCo free joint quaternion is x,y,z,qw,qx,qy,qz; Pinocchio is x,y,z,qx,qy,qz,qw",
        "adapter_contract": "mujoco_qpos_to_pinocchio / pinocchio_qpos_to_mujoco",
        "stage9_use": "C++ mirror must explicitly document base_state data layout before subscribing",
    },
    {
        "direction": "publish",
        "topic": "/go1/imu",
        "ros_type": "sensor_msgs/msg/Imu",
        "ros_field": "orientation",
        "python_baseline_source": "MuJoCo base orientation or simulated IMU orientation",
        "expected_shape_or_length": "geometry_msgs/Quaternion",
        "order_contract": "ROS Quaternion fields are x,y,z,w; MuJoCo qpos stores qw,qx,qy,qz after xyz",
        "adapter_contract": "adapter documents MuJoCo / Pinocchio quaternion convention",
        "stage9_use": "C++ mirror must not copy MuJoCo qpos[3:7] directly into ROS orientation",
    },
    {
        "direction": "publish",
        "topic": "/go1/imu",
        "ros_type": "sensor_msgs/msg/Imu",
        "ros_field": "angular_velocity",
        "python_baseline_source": "MuJoCo base angular velocity or sensor data",
        "expected_shape_or_length": "Vector3",
        "order_contract": "must document frame convention before controller use",
        "adapter_contract": "not a reorder helper yet; interface contract only",
        "stage9_use": "C++ mirror records field but does not consume it for control yet",
    },
    {
        "direction": "publish",
        "topic": "/go1/imu",
        "ros_type": "sensor_msgs/msg/Imu",
        "ros_field": "linear_acceleration",
        "python_baseline_source": "MuJoCo IMU acceleration or sensor data",
        "expected_shape_or_length": "Vector3",
        "order_contract": "must document frame convention before EKF use",
        "adapter_contract": "not a reorder helper yet; interface contract only",
        "stage9_use": "C++ mirror records field but does not implement EKF",
    },
    {
        "direction": "publish",
        "topic": "/go1/foot_contacts",
        "ros_type": "std_msgs/msg/Int32MultiArray",
        "ros_field": "data",
        "python_baseline_source": "MuJoCo contact flags",
        "expected_shape_or_length": "4",
        "order_contract": "FR, FL, RR, RL",
        "adapter_contract": "MJ_LEG_ORDER",
        "stage9_use": "C++ mirror must preserve leg contact order",
    },
    {
        "direction": "publish",
        "topic": "/go1/sim_time",
        "ros_type": "std_msgs/msg/Float64",
        "ros_field": "data",
        "python_baseline_source": "MuJoCo simulation time",
        "expected_shape_or_length": "1",
        "order_contract": "scalar seconds",
        "adapter_contract": "not applicable",
        "stage9_use": "C++ mirror uses it only as timestamp/reference unless clock integration is added",
    },
    {
        "direction": "subscribe",
        "topic": "/go1/joint_torque_cmd",
        "ros_type": "std_msgs/msg/Float64MultiArray",
        "ros_field": "data",
        "python_baseline_source": "controller torque command",
        "expected_shape_or_length": "12",
        "order_contract": "MuJoCo actuator order: FR, FL, RR, RL; hip, thigh, calf",
        "adapter_contract": "pinocchio_tau_to_mujoco / mujoco_tau_to_pinocchio",
        "stage9_use": "C++ mirror must publish or consume torque in MuJoCo actuator order",
    },
]


def load_metric_summary(path: Path):
    metrics = {}
    if not path.exists():
        return metrics

    with path.open(newline="") as f:
        rows = list(csv.reader(f))

    if not rows:
        return metrics

    header = [cell.strip() for cell in rows[0]]

    if len(header) >= 2 and header[0] == "metric" and header[1] == "value":
        for row in rows[1:]:
            if len(row) >= 2:
                metrics[row[0].strip()] = row[1].strip()
        return metrics

    for row in rows[1:]:
        if any(cell.strip() for cell in row):
            for key, value in zip(header, row):
                metrics[key.strip()] = value.strip()
            return metrics

    return metrics


def as_bool(x):
    return str(x).strip().lower() in {"true", "1", "yes"}


def load_schema_map(path: Path):
    if not path.exists():
        return []

    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def add_check(rows, check, value, expected, passed, detail=""):
    rows.append({
        "check": check,
        "value": str(value),
        "expected": str(expected),
        "pass": bool(passed),
        "detail": detail,
    })


def bridge_source_hits(topic, field):
    if not BRIDGE_SOURCE.exists():
        return []

    lines = BRIDGE_SOURCE.read_text(errors="replace").splitlines()
    hits = []

    compact_field = field.split(".")[0]

    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if topic in stripped or compact_field in stripped:
            hits.append({
                "line": line_no,
                "text": stripped[:220],
            })

    return hits[:10]


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    checks = []

    stage91 = load_metric_summary(STAGE91_SUMMARY)
    stage91_pass = as_bool(stage91.get("pass", "False"))

    add_check(checks, "stage91_summary_exists", STAGE91_SUMMARY.exists(), True, STAGE91_SUMMARY.exists(), str(STAGE91_SUMMARY))
    add_check(checks, "stage91_pass", stage91_pass, True, stage91_pass)

    add_check(checks, "stage91_schema_map_exists", STAGE91_SCHEMA_MAP.exists(), True, STAGE91_SCHEMA_MAP.exists(), str(STAGE91_SCHEMA_MAP))
    add_check(checks, "stage8_adapter_exists", STAGE8_ADAPTER.exists(), True, STAGE8_ADAPTER.exists(), str(STAGE8_ADAPTER))
    add_check(checks, "stage8_entrypoint_exists", STAGE8_ENTRYPOINT.exists(), True, STAGE8_ENTRYPOINT.exists(), str(STAGE8_ENTRYPOINT))
    add_check(checks, "bridge_source_exists", BRIDGE_SOURCE.exists(), True, BRIDGE_SOURCE.exists(), str(BRIDGE_SOURCE))

    schema_rows = load_schema_map(STAGE91_SCHEMA_MAP)

    topic_type_map = {}
    for row in schema_rows:
        topic_type_map[(row.get("direction", ""), row.get("topic", ""))] = row.get("ros_type", "")

    output_rows = []

    for item in EXPECTED_MAPPING_ROWS:
        key = (item["direction"], item["topic"])
        observed_type = topic_type_map.get(key, "")
        observed_matches_expected = observed_type == item["ros_type"]

        source_hits = bridge_source_hits(item["topic"], item["ros_field"])

        add_check(
            checks,
            f"type_match_{item['direction']}_{item['topic']}_{item['ros_field']}",
            observed_type,
            item["ros_type"],
            observed_matches_expected,
            "",
        )

        output = dict(item)
        output["observed_ros_type"] = observed_type
        output["observed_type_matches_expected"] = observed_matches_expected
        output["bridge_source_hit_count_limited"] = len(source_hits)
        output["bridge_source_hits"] = json.dumps(source_hits, ensure_ascii=False)
        output_rows.append(output)

    all_types_match = all(row["observed_type_matches_expected"] for row in output_rows)
    all_pass = all(row["pass"] for row in checks) and all_types_match

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    with FIELD_MAP_PATH.open("w", newline="") as f:
        fieldnames = [
            "direction",
            "topic",
            "ros_type",
            "observed_ros_type",
            "observed_type_matches_expected",
            "ros_field",
            "python_baseline_source",
            "expected_shape_or_length",
            "order_contract",
            "adapter_contract",
            "stage9_use",
            "bridge_source_hit_count_limited",
            "bridge_source_hits",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    doc_rows = []
    for row in output_rows:
        doc_rows.append(
            f"| {row['direction']} | `{row['topic']}` | `{row['ros_type']}` | `{row['ros_field']}` | `{row['expected_shape_or_length']}` | {row['observed_type_matches_expected']} |"
        )

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 9.2"])
        writer.writerow(["test_name", "python_baseline_ros2_field_mapping"])
        writer.writerow(["stage91_pass", stage91_pass])
        writer.writerow(["field_mapping_rows", len(output_rows)])
        writer.writerow(["all_types_match_stage91_schema", all_types_match])
        writer.writerow(["stage8_adapter_exists", STAGE8_ADAPTER.exists()])
        writer.writerow(["stage8_entrypoint_exists", STAGE8_ENTRYPOINT.exists()])
        writer.writerow(["bridge_source_exists", BRIDGE_SOURCE.exists()])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["stage9_scope", "field_mapping_table_only"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["pure_wbc_locomotion_completed", False])
        writer.writerow(["ros2_cpp_realtime_controller_completed", False])
        writer.writerow(["ekf_completed", False])
        writer.writerow(["full_3d_centroidal_mpc_completed", False])
        writer.writerow(["num_checks", len(checks)])
        writer.writerow(["num_failed_checks", sum(1 for row in checks if not row["pass"])])
        writer.writerow(["pass", all_pass])
        writer.writerow(["log_csv", str(LOG_PATH.relative_to(ROOT))])
        writer.writerow(["field_map_csv", str(FIELD_MAP_PATH.relative_to(ROOT))])
        writer.writerow(["summary_csv", str(SUMMARY_PATH.relative_to(ROOT))])

    DOC_PATH.write_text(f"""# Stage 9.2 Python frozen baseline ↔ ROS2 topic field mapping table

## 目标

建立 Stage 8 frozen Python baseline 与 ROS2 bridge topic 字段之间的映射表。

本阶段只生成接口映射表，不写 controller，不改变控制律。

## 前置条件

- Stage 9.1 pass: `{stage91_pass}`
- Stage 8 adapter exists: `{STAGE8_ADAPTER.exists()}`
- Stage 8 entrypoint exists: `{STAGE8_ENTRYPOINT.exists()}`
- bridge source exists: `{BRIDGE_SOURCE.exists()}`

## 字段映射表

| direction | topic | ROS type | field | expected shape / length | type match |
|---|---|---|---|---|---:|
{chr(10).join(doc_rows)}

## 关键合同

### Joint order

MuJoCo actuator / ROS torque command order:

    FR, FL, RR, RL

每条腿顺序：

    hip, thigh, calf

### Floating-base quaternion

MuJoCo free joint qpos:

    x, y, z, qw, qx, qy, qz

Pinocchio free-flyer qpos:

    x, y, z, qx, qy, qz, qw

ROS Quaternion field order:

    x, y, z, w

因此后续 C++ mirror 不能直接把 MuJoCo qpos[3:7] 当成 ROS orientation。

### Torque command

/go1/joint_torque_cmd 使用 Float64MultiArray.data，长度必须为 12，顺序必须是 MuJoCo actuator order。

## 结果

- pass: `{all_pass}`
- field_mapping_rows: `{len(output_rows)}`
- all_types_match_stage91_schema: `{all_types_match}`

## 输出

- Log: `results/logs_sample/stage09_python_baseline_ros2_field_mapping_log.csv`
- Field map: `results/logs_sample/stage09_python_baseline_ros2_field_mapping.csv`
- Summary: `results/logs_sample/stage09_python_baseline_ros2_field_mapping_summary.csv`

## 边界

本阶段不改变控制律，不完成 ROS2/C++ real-time controller，不完成 EKF，不完成 pure full WBC locomotion。

当前 baseline 仍是 mixed online control baseline。
""")

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 9.2 Python frozen baseline ↔ ROS2 topic field mapping table

Stage 9.2 完成 Python frozen baseline 与 ROS2 bridge topic 字段之间的映射表。

- Script: `scripts/stage09_python_baseline_ros2_field_mapping.py`
- Log: `results/logs_sample/stage09_python_baseline_ros2_field_mapping_log.csv`
- Field map: `results/logs_sample/stage09_python_baseline_ros2_field_mapping.csv`
- Summary: `results/logs_sample/stage09_python_baseline_ros2_field_mapping_summary.csv`
- Docs: `docs/STAGE09_PYTHON_BASELINE_ROS2_FIELD_MAPPING.md`
- pass: `{all_pass}`
- field_mapping_rows: `{len(output_rows)}`
- all_types_match_stage91_schema: `{all_types_match}`
- control_law_changed: `False`
- stage9_scope: `field_mapping_table_only`

Stage 9.2 只生成接口映射表，不写实时 C++ controller，不改变控制律。当前 baseline 仍是 mixed online control baseline。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 9.2 Python frozen baseline ↔ ROS2 topic field mapping table"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 9.2] Python frozen baseline <-> ROS2 topic field mapping")
    print(f"pass={all_pass}")
    print(f"stage91_pass={stage91_pass}")
    print(f"field_mapping_rows={len(output_rows)}")
    print(f"all_types_match_stage91_schema={all_types_match}")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
    print(f"field_map_csv={FIELD_MAP_PATH.relative_to(ROOT)}")
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
