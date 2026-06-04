#!/usr/bin/env python3
from pathlib import Path
import ast
import csv
import json
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

ROS2_WS = ROOT / "ros2_ws"
ROS2_SRC = ROS2_WS / "src"
BRIDGE_PACKAGE_NAME = "robot_mpc_wbc_bridge"

STAGE90_SUMMARY = ROOT / "results/logs_sample/stage09_ros2_cpp_interface_contract_inventory_summary.csv"

LOG_DIR = ROOT / "results/logs_sample"
SCHEMA_DIR = LOG_DIR / "stage09_topic_schemas"
LOG_PATH = LOG_DIR / "stage09_ros2_topic_schema_snapshot_log.csv"
TOPIC_SCHEMA_MAP = LOG_DIR / "stage09_ros2_topic_schema_snapshot_map.csv"
SUMMARY_PATH = LOG_DIR / "stage09_ros2_topic_schema_snapshot_summary.csv"
DOC_PATH = ROOT / "docs/STAGE09_ROS2_TOPIC_SCHEMA_SNAPSHOT.md"

EXPECTED_TOPICS = [
    {"direction": "publish", "topic": "/go1/joint_states", "baseline_signal": "joint_state_feedback"},
    {"direction": "publish", "topic": "/go1/base_state", "baseline_signal": "floating_base_state"},
    {"direction": "publish", "topic": "/go1/imu", "baseline_signal": "imu_feedback"},
    {"direction": "publish", "topic": "/go1/foot_contacts", "baseline_signal": "contact_state_feedback"},
    {"direction": "publish", "topic": "/go1/sim_time", "baseline_signal": "simulation_time"},
    {"direction": "subscribe", "topic": "/go1/joint_torque_cmd", "baseline_signal": "joint_torque_command"},
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


def find_bridge_package():
    if not ROS2_SRC.exists():
        return None

    for package_xml in sorted(ROS2_SRC.rglob("package.xml")):
        text = package_xml.read_text(errors="replace")
        m = re.search(r"<name>\s*([^<]+)\s*</name>", text)
        if m and m.group(1).strip() == BRIDGE_PACKAGE_NAME:
            return package_xml.parent

    return None


def parse_python_imports(text):
    class_to_ros_type = {}

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return class_to_ros_type

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.endswith(".msg"):
                pkg = module[:-4]
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    local_name = alias.asname or alias.name
                    class_to_ros_type[local_name] = f"{pkg}/msg/{alias.name}"

    return class_to_ros_type


def normalize_ros_type(type_expr, class_to_ros_type):
    raw = str(type_expr).strip()

    raw = raw.replace(" ", "")
    raw = raw.replace("::", "/")

    if raw in class_to_ros_type:
        return class_to_ros_type[raw]

    # Python namespace form: sensor_msgs.msg.JointState
    m = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\.msg\.([A-Za-z_][A-Za-z0-9_]*)$", raw)
    if m:
        return f"{m.group(1)}/msg/{m.group(2)}"

    # C++ form after :: replacement: sensor_msgs/msg/JointState
    if re.match(r"^[A-Za-z0-9_]+/msg/[A-Za-z0-9_]+$", raw):
        return raw

    # C++ shared pointer or nested template residue.
    m = re.search(r"([A-Za-z0-9_]+)/msg/([A-Za-z0-9_]+)", raw)
    if m:
        return f"{m.group(1)}/msg/{m.group(2)}"

    return raw


def collect_source_files(package_dir: Path):
    files = []
    for ext in ("*.py", "*.cpp", "*.hpp", "*.h"):
        files.extend(sorted(package_dir.rglob(ext)))
    return files


def find_topic_declarations(package_dir: Path):
    declarations = []

    for path in collect_source_files(package_dir):
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(errors="replace")

        class_to_ros_type = parse_python_imports(text)

        # Python rclpy:
        # self.create_publisher(JointState, "/go1/joint_states", 10)
        py_pub = re.compile(
            r"create_publisher\s*\(\s*([A-Za-z_][A-Za-z0-9_\.]*)\s*,\s*['\"]([^'\"]+)['\"]",
            re.MULTILINE,
        )
        py_sub = re.compile(
            r"create_subscription\s*\(\s*([A-Za-z_][A-Za-z0-9_\.]*)\s*,\s*['\"]([^'\"]+)['\"]",
            re.MULTILINE,
        )

        for m in py_pub.finditer(text):
            declarations.append({
                "file": rel,
                "direction": "publish",
                "topic": m.group(2),
                "type_expr": m.group(1),
                "ros_type": normalize_ros_type(m.group(1), class_to_ros_type),
            })

        for m in py_sub.finditer(text):
            declarations.append({
                "file": rel,
                "direction": "subscribe",
                "topic": m.group(2),
                "type_expr": m.group(1),
                "ros_type": normalize_ros_type(m.group(1), class_to_ros_type),
            })

        # C++ rclcpp:
        # create_publisher<sensor_msgs::msg::JointState>("/go1/joint_states", 10)
        cpp_pub = re.compile(
            r"create_publisher\s*<\s*([^>]+)\s*>\s*\(\s*['\"]([^'\"]+)['\"]",
            re.MULTILINE,
        )
        cpp_sub = re.compile(
            r"create_subscription\s*<\s*([^>]+)\s*>\s*\(\s*['\"]([^'\"]+)['\"]",
            re.MULTILINE,
        )

        for m in cpp_pub.finditer(text):
            declarations.append({
                "file": rel,
                "direction": "publish",
                "topic": m.group(2),
                "type_expr": m.group(1),
                "ros_type": normalize_ros_type(m.group(1), class_to_ros_type),
            })

        for m in cpp_sub.finditer(text):
            declarations.append({
                "file": rel,
                "direction": "subscribe",
                "topic": m.group(2),
                "type_expr": m.group(1),
                "ros_type": normalize_ros_type(m.group(1), class_to_ros_type),
            })

    return declarations


def schema_filename(ros_type):
    safe = ros_type.replace("/", "__").replace(":", "_").replace(" ", "_")
    return SCHEMA_DIR / f"{safe}.txt"


def run_ros2_interface_show(ros_type):
    ros2 = shutil.which("ros2")
    if ros2 is None:
        return False, "ros2 command not found"

    try:
        proc = subprocess.run(
            [ros2, "interface", "show", ros_type],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=10,
        )
    except Exception as e:
        return False, str(e)

    if proc.returncode != 0:
        return False, proc.stderr.strip() or proc.stdout.strip()

    return True, proc.stdout


def count_schema_fields(schema_text):
    count = 0
    for line in schema_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith("="):
            continue
        count += 1
    return count


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    stage90 = load_summary(STAGE90_SUMMARY)
    stage90_pass = as_bool(stage90.get("pass", "False"))

    add_check(rows, "stage90_summary_exists", STAGE90_SUMMARY.exists(), True, STAGE90_SUMMARY.exists(), str(STAGE90_SUMMARY))
    add_check(rows, "stage90_pass", stage90_pass, True, stage90_pass)

    bridge_dir = find_bridge_package()
    add_check(rows, "bridge_package_found", bridge_dir is not None, True, bridge_dir is not None, str(bridge_dir) if bridge_dir else "")

    declarations = []
    if bridge_dir is not None:
        declarations = find_topic_declarations(bridge_dir)

    topic_rows = []
    found_count = 0
    type_inferred_count = 0
    schema_available_count = 0

    for expected in EXPECTED_TOPICS:
        topic = expected["topic"]
        direction = expected["direction"]

        matches = [
            d for d in declarations
            if d["topic"] == topic and d["direction"] == direction
        ]

        found = len(matches) > 0
        if found:
            found_count += 1

        ros_type = matches[0]["ros_type"] if found else ""
        type_inferred = bool(ros_type and "/" in ros_type)
        if type_inferred:
            type_inferred_count += 1

        schema_ok = False
        schema_path = ""
        schema_field_count = 0
        schema_error = ""

        if type_inferred:
            schema_ok, schema_text_or_error = run_ros2_interface_show(ros_type)
            if schema_ok:
                schema_path_obj = schema_filename(ros_type)
                schema_path_obj.write_text(schema_text_or_error)
                schema_path = schema_path_obj.relative_to(ROOT).as_posix()
                schema_field_count = count_schema_fields(schema_text_or_error)
                schema_available_count += 1
            else:
                schema_error = schema_text_or_error

        add_check(rows, f"topic_found_{topic}", found, True, found, json.dumps(matches[:3], ensure_ascii=False))
        add_check(rows, f"type_inferred_{topic}", type_inferred, True, type_inferred, ros_type)
        add_check(rows, f"schema_available_{topic}", schema_ok, True, schema_ok, schema_error)

        topic_rows.append({
            "direction": direction,
            "topic": topic,
            "baseline_signal": expected["baseline_signal"],
            "found_in_source": found,
            "ros_type": ros_type,
            "type_expr": matches[0]["type_expr"] if found else "",
            "source_file": matches[0]["file"] if found else "",
            "schema_available": schema_ok,
            "schema_field_count": schema_field_count,
            "schema_file": schema_path,
            "schema_error": schema_error,
        })

    all_topics_found = found_count == len(EXPECTED_TOPICS)
    all_types_inferred = type_inferred_count == len(EXPECTED_TOPICS)
    all_schemas_available = schema_available_count == len(EXPECTED_TOPICS)

    add_check(rows, "all_expected_topics_found", found_count, len(EXPECTED_TOPICS), all_topics_found)
    add_check(rows, "all_topic_types_inferred", type_inferred_count, len(EXPECTED_TOPICS), all_types_inferred)
    add_check(rows, "all_topic_schemas_available", schema_available_count, len(EXPECTED_TOPICS), all_schemas_available)

    all_pass = all(row["pass"] for row in rows)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(rows)

    with TOPIC_SCHEMA_MAP.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "direction",
                "topic",
                "baseline_signal",
                "found_in_source",
                "ros_type",
                "type_expr",
                "source_file",
                "schema_available",
                "schema_field_count",
                "schema_file",
                "schema_error",
            ],
        )
        writer.writeheader()
        writer.writerows(topic_rows)

    doc_topic_lines = []
    for item in topic_rows:
        doc_topic_lines.append(
            f"| {item['direction']} | `{item['topic']}` | `{item['ros_type']}` | {item['schema_available']} | {item['schema_field_count']} | `{item['baseline_signal']}` |"
        )

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 9.1"])
        writer.writerow(["test_name", "ros2_topic_schema_snapshot"])
        writer.writerow(["stage90_pass", stage90_pass])
        writer.writerow(["bridge_package_found", bridge_dir is not None])
        writer.writerow(["expected_topic_count", len(EXPECTED_TOPICS)])
        writer.writerow(["topic_found_count", found_count])
        writer.writerow(["topic_type_inferred_count", type_inferred_count])
        writer.writerow(["topic_schema_available_count", schema_available_count])
        writer.writerow(["all_expected_topics_found", all_topics_found])
        writer.writerow(["all_topic_types_inferred", all_types_inferred])
        writer.writerow(["all_topic_schemas_available", all_schemas_available])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["stage9_scope", "topic_schema_snapshot_only"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["pure_wbc_locomotion_completed", False])
        writer.writerow(["ros2_cpp_realtime_controller_completed", False])
        writer.writerow(["ekf_completed", False])
        writer.writerow(["full_3d_centroidal_mpc_completed", False])
        writer.writerow(["num_checks", len(rows)])
        writer.writerow(["num_failed_checks", sum(1 for row in rows if not row["pass"])])
        writer.writerow(["pass", all_pass])
        writer.writerow(["log_csv", str(LOG_PATH.relative_to(ROOT))])
        writer.writerow(["schema_map_csv", str(TOPIC_SCHEMA_MAP.relative_to(ROOT))])
        writer.writerow(["schema_dir", str(SCHEMA_DIR.relative_to(ROOT))])
        writer.writerow(["summary_csv", str(SUMMARY_PATH.relative_to(ROOT))])

    DOC_PATH.write_text(f"""# Stage 9.1 ROS2 Topic Schema Snapshot

## 目标

记录 ROS2 bridge topic 的消息类型和字段 schema。

本阶段只做 topic schema snapshot，不写 controller，不改变控制律。

## 前置条件

- Stage 9.0 pass: `{stage90_pass}`
- bridge package found: `{bridge_dir is not None}`

## Topic schema map

| direction | topic | ROS type | schema available | field count | baseline signal |
|---|---|---|---:|---:|---|
{chr(10).join(doc_topic_lines)}

## 结果

- pass: `{all_pass}`
- expected_topic_count: `{len(EXPECTED_TOPICS)}`
- topic_found_count: `{found_count}`
- topic_type_inferred_count: `{type_inferred_count}`
- topic_schema_available_count: `{schema_available_count}`
- all_expected_topics_found: `{all_topics_found}`
- all_topic_types_inferred: `{all_types_inferred}`
- all_topic_schemas_available: `{all_schemas_available}`

## 输出

- Log: `results/logs_sample/stage09_ros2_topic_schema_snapshot_log.csv`
- Schema map: `results/logs_sample/stage09_ros2_topic_schema_snapshot_map.csv`
- Schema dir: `results/logs_sample/stage09_topic_schemas/`
- Summary: `results/logs_sample/stage09_ros2_topic_schema_snapshot_summary.csv`

## 边界

本阶段不改变控制律，不完成 ROS2/C++ real-time controller，不完成 EKF，不完成 pure full WBC locomotion。

当前 baseline 仍是 mixed online control baseline。
""")

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 9.1 ROS2 Topic Schema Snapshot

Stage 9.1 完成 ROS2 topic schema snapshot。

- Script: `scripts/stage09_ros2_topic_schema_snapshot.py`
- Log: `results/logs_sample/stage09_ros2_topic_schema_snapshot_log.csv`
- Schema map: `results/logs_sample/stage09_ros2_topic_schema_snapshot_map.csv`
- Schema dir: `results/logs_sample/stage09_topic_schemas/`
- Summary: `results/logs_sample/stage09_ros2_topic_schema_snapshot_summary.csv`
- Docs: `docs/STAGE09_ROS2_TOPIC_SCHEMA_SNAPSHOT.md`
- pass: `{all_pass}`
- topic_found_count: `{found_count}`
- topic_type_inferred_count: `{type_inferred_count}`
- topic_schema_available_count: `{schema_available_count}`
- control_law_changed: `False`
- stage9_scope: `topic_schema_snapshot_only`

Stage 9.1 只记录消息类型和字段 schema，不写实时 C++ controller，不改变控制律。当前 baseline 仍是 mixed online control baseline。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 9.1 ROS2 Topic Schema Snapshot"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 9.1] ROS2 topic schema snapshot")
    print(f"pass={all_pass}")
    print(f"stage90_pass={stage90_pass}")
    print(f"bridge_package_found={bridge_dir is not None}")
    print(f"topic_found_count={found_count}")
    print(f"topic_type_inferred_count={type_inferred_count}")
    print(f"topic_schema_available_count={schema_available_count}")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
    print(f"schema_map_csv={TOPIC_SCHEMA_MAP.relative_to(ROOT)}")
    print(f"schema_dir={SCHEMA_DIR.relative_to(ROOT)}")
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
