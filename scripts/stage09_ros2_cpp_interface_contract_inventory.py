#!/usr/bin/env python3
from pathlib import Path
import csv
import json
import shutil
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

ROS2_WS = ROOT / "ros2_ws"
ROS2_SRC = ROS2_WS / "src"
BRIDGE_PACKAGE_NAME = "robot_mpc_wbc_bridge"

STAGE8_ENTRYPOINT = ROOT / "scripts/stage08_adapter_backed_stage07_recommended_test.py"
STAGE8_ADAPTER = ROOT / "scripts/common/go1_runtime_interface.py"
STAGE8_FREEZE_SUMMARY = ROOT / "results/logs_sample/stage08_freeze_integrity_check_summary.csv"
STAGE8_FREEZE_HASHES = ROOT / "results/logs_sample/stage08_freeze_integrity_hashes.csv"
STAGE8_FREEZE_MANIFEST = ROOT / "docs/STAGE08_BASELINE_FREEZE_MANIFEST.md"

LOG_DIR = ROOT / "results/logs_sample"
INVENTORY_LOG = LOG_DIR / "stage09_ros2_cpp_interface_contract_inventory_log.csv"
SUMMARY_PATH = LOG_DIR / "stage09_ros2_cpp_interface_contract_inventory_summary.csv"
TOPIC_MAP_PATH = LOG_DIR / "stage09_ros2_cpp_interface_topic_contract_map.csv"
DOC_PATH = ROOT / "docs/STAGE09_ROS2_CPP_INTERFACE_CONTRACT_INVENTORY.md"

EXPECTED_PUBLISH_TOPICS = [
    "/go1/joint_states",
    "/go1/base_state",
    "/go1/imu",
    "/go1/foot_contacts",
    "/go1/sim_time",
]

EXPECTED_SUBSCRIBE_TOPICS = [
    "/go1/joint_torque_cmd",
]

PYTHON_BASELINE_SIGNALS = [
    "qpos",
    "qvel",
    "base_state",
    "imu",
    "foot_contacts",
    "joint_torque_cmd",
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


def list_ros2_packages():
    packages = []

    if not ROS2_SRC.exists():
        return packages

    for package_xml in sorted(ROS2_SRC.rglob("package.xml")):
        pkg_dir = package_xml.parent
        rel = pkg_dir.relative_to(ROOT).as_posix()
        name = pkg_dir.name

        text = package_xml.read_text(errors="replace")
        m = re.search(r"<name>\s*([^<]+)\s*</name>", text)
        if m:
            name = m.group(1).strip()

        packages.append({
            "name": name,
            "path": rel,
            "package_xml": package_xml.relative_to(ROOT).as_posix(),
            "setup_py": (pkg_dir / "setup.py").exists(),
            "cmakelists": (pkg_dir / "CMakeLists.txt").exists(),
            "launch_files": len(list(pkg_dir.rglob("*.launch.py"))),
            "python_files": len(list(pkg_dir.rglob("*.py"))),
            "cpp_files": len(list(pkg_dir.rglob("*.cpp"))),
            "hpp_files": len(list(pkg_dir.rglob("*.hpp"))) + len(list(pkg_dir.rglob("*.h"))),
        })

    return packages


def find_bridge_package(packages):
    for pkg in packages:
        if pkg["name"] == BRIDGE_PACKAGE_NAME:
            return ROOT / pkg["path"]
    return None


def collect_source_text(paths):
    chunks = []
    for base in paths:
        if not base.exists():
            continue

        for ext in ("*.py", "*.cpp", "*.hpp", "*.h", "*.xml", "*.txt", "*.launch.py", "CMakeLists.txt", "setup.py"):
            for path in base.rglob(ext):
                if path.is_file():
                    try:
                        rel = path.relative_to(ROOT).as_posix()
                        text = path.read_text(errors="replace")
                        chunks.append((rel, text))
                    except Exception:
                        pass
    return chunks


def topic_occurrences(source_chunks, topic):
    hits = []
    for rel, text in source_chunks:
        for line_no, line in enumerate(text.splitlines(), start=1):
            if topic in line:
                hits.append({
                    "file": rel,
                    "line": line_no,
                    "text": line.strip()[:240],
                })
    return hits


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    ros2_cmd = shutil.which("ros2")
    colcon_cmd = shutil.which("colcon")

    add_check(rows, "ros2_ws_exists", ROS2_WS.exists(), True, ROS2_WS.exists(), str(ROS2_WS))
    add_check(rows, "ros2_src_exists", ROS2_SRC.exists(), True, ROS2_SRC.exists(), str(ROS2_SRC))
    add_check(rows, "ros2_command_available", ros2_cmd is not None, True, ros2_cmd is not None, str(ros2_cmd))
    add_check(rows, "colcon_command_available", colcon_cmd is not None, True, colcon_cmd is not None, str(colcon_cmd))

    add_check(rows, "stage8_entrypoint_exists", STAGE8_ENTRYPOINT.exists(), True, STAGE8_ENTRYPOINT.exists(), str(STAGE8_ENTRYPOINT))
    add_check(rows, "stage8_adapter_exists", STAGE8_ADAPTER.exists(), True, STAGE8_ADAPTER.exists(), str(STAGE8_ADAPTER))
    add_check(rows, "stage8_freeze_summary_exists", STAGE8_FREEZE_SUMMARY.exists(), True, STAGE8_FREEZE_SUMMARY.exists(), str(STAGE8_FREEZE_SUMMARY))
    add_check(rows, "stage8_freeze_hashes_exists", STAGE8_FREEZE_HASHES.exists(), True, STAGE8_FREEZE_HASHES.exists(), str(STAGE8_FREEZE_HASHES))
    add_check(rows, "stage8_freeze_manifest_exists", STAGE8_FREEZE_MANIFEST.exists(), True, STAGE8_FREEZE_MANIFEST.exists(), str(STAGE8_FREEZE_MANIFEST))

    stage8_metrics = load_summary(STAGE8_FREEZE_SUMMARY)
    stage8_pass = as_bool(stage8_metrics.get("pass", "False"))
    stage8_control_changed = as_bool(stage8_metrics.get("control_law_changed", "True"))

    add_check(rows, "stage8_freeze_pass", stage8_pass, True, stage8_pass)
    add_check(rows, "stage8_control_law_changed", stage8_control_changed, False, not stage8_control_changed)

    packages = list_ros2_packages()
    bridge_pkg = find_bridge_package(packages)

    add_check(rows, "ros2_package_count", len(packages), ">=1", len(packages) >= 1)
    add_check(rows, "bridge_package_found", bridge_pkg is not None, True, bridge_pkg is not None, str(bridge_pkg) if bridge_pkg else "")

    source_roots = []
    if bridge_pkg is not None:
        source_roots.append(bridge_pkg)

    source_chunks = collect_source_text(source_roots)

    publish_found_count = 0
    subscribe_found_count = 0

    topic_map_rows = []

    for topic in EXPECTED_PUBLISH_TOPICS:
        hits = topic_occurrences(source_chunks, topic)
        found = len(hits) > 0
        if found:
            publish_found_count += 1

        add_check(rows, f"expected_publish_topic_found_{topic}", found, True, found, json.dumps(hits[:5], ensure_ascii=False))

        topic_map_rows.append({
            "direction": "publish",
            "topic": topic,
            "expected": True,
            "found_in_source": found,
            "hit_count": len(hits),
            "example_hit": json.dumps(hits[:1], ensure_ascii=False),
            "python_baseline_signal": topic.strip("/").split("/")[-1],
            "stage9_action": "mirror interface only; do not change control law",
        })

    for topic in EXPECTED_SUBSCRIBE_TOPICS:
        hits = topic_occurrences(source_chunks, topic)
        found = len(hits) > 0
        if found:
            subscribe_found_count += 1

        add_check(rows, f"expected_subscribe_topic_found_{topic}", found, True, found, json.dumps(hits[:5], ensure_ascii=False))

        topic_map_rows.append({
            "direction": "subscribe",
            "topic": topic,
            "expected": True,
            "found_in_source": found,
            "hit_count": len(hits),
            "example_hit": json.dumps(hits[:1], ensure_ascii=False),
            "python_baseline_signal": "joint_torque_cmd",
            "stage9_action": "mirror interface only; do not change control law",
        })

    all_expected_topics_found = (
        publish_found_count == len(EXPECTED_PUBLISH_TOPICS)
        and subscribe_found_count == len(EXPECTED_SUBSCRIBE_TOPICS)
    )

    add_check(
        rows,
        "all_expected_topics_found",
        {
            "publish_found_count": publish_found_count,
            "subscribe_found_count": subscribe_found_count,
        },
        {
            "publish_expected": len(EXPECTED_PUBLISH_TOPICS),
            "subscribe_expected": len(EXPECTED_SUBSCRIBE_TOPICS),
        },
        all_expected_topics_found,
    )

    all_pass = all(row["pass"] for row in rows)

    with INVENTORY_LOG.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(rows)

    with TOPIC_MAP_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "direction",
                "topic",
                "expected",
                "found_in_source",
                "hit_count",
                "example_hit",
                "python_baseline_signal",
                "stage9_action",
            ],
        )
        writer.writeheader()
        writer.writerows(topic_map_rows)

    package_rows_text = []
    for pkg in packages:
        package_rows_text.append(
            f"| {pkg['name']} | {pkg['path']} | {pkg['setup_py']} | {pkg['cmakelists']} | {pkg['launch_files']} | {pkg['python_files']} | {pkg['cpp_files']} |"
        )

    if not package_rows_text:
        package_rows_text = ["| none | none | False | False | 0 | 0 | 0 |"]

    topic_doc_lines = []
    for item in topic_map_rows:
        topic_doc_lines.append(
            f"| {item['direction']} | `{item['topic']}` | {item['found_in_source']} | {item['hit_count']} | {item['python_baseline_signal']} |"
        )

    summary_rows = [
        ("stage", "Stage 9.0"),
        ("test_name", "ros2_cpp_interface_contract_inventory"),
        ("ros2_ws_exists", ROS2_WS.exists()),
        ("ros2_src_exists", ROS2_SRC.exists()),
        ("ros2_command_available", ros2_cmd is not None),
        ("colcon_command_available", colcon_cmd is not None),
        ("ros2_package_count", len(packages)),
        ("bridge_package_name", BRIDGE_PACKAGE_NAME),
        ("bridge_package_found", bridge_pkg is not None),
        ("stage8_freeze_pass", stage8_pass),
        ("stage8_control_law_changed", stage8_control_changed),
        ("publish_topic_expected_count", len(EXPECTED_PUBLISH_TOPICS)),
        ("publish_topic_found_count", publish_found_count),
        ("subscribe_topic_expected_count", len(EXPECTED_SUBSCRIBE_TOPICS)),
        ("subscribe_topic_found_count", subscribe_found_count),
        ("all_expected_topics_found", all_expected_topics_found),
        ("control_law_changed", False),
        ("stage9_scope", "interface_inventory_only"),
        ("baseline_type", "mixed_online_control_baseline"),
        ("pure_wbc_locomotion_completed", False),
        ("ros2_cpp_realtime_controller_completed", False),
        ("ekf_completed", False),
        ("full_3d_centroidal_mpc_completed", False),
        ("num_checks", len(rows)),
        ("num_failed_checks", sum(1 for row in rows if not row["pass"])),
        ("pass", all_pass),
        ("log_csv", str(INVENTORY_LOG.relative_to(ROOT))),
        ("topic_map_csv", str(TOPIC_MAP_PATH.relative_to(ROOT))),
        ("summary_csv", str(SUMMARY_PATH.relative_to(ROOT))),
    ]

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerows(summary_rows)

    DOC_PATH.write_text(f"""# Stage 9.0 ROS2/C++ Interface Contract Inventory

## 目标

Stage 9 从 ROS2/C++ interface mirror 开始，不直接写实时控制器，不改变控制律。

本阶段只盘点当前 ROS2 workspace、bridge package、topic contract，以及 Stage 8 frozen Python baseline 与 ROS2 topic 的对应关系。

## Stage 8 frozen baseline

推荐入口：

    /usr/bin/python3 scripts/stage08_adapter_backed_stage07_recommended_test.py

Runtime adapter:

    scripts/common/go1_runtime_interface.py

Stage 8 freeze pass: `{stage8_pass}`

Control law changed: `{stage8_control_changed}`

## ROS2 workspace

- ros2_ws_exists: `{ROS2_WS.exists()}`
- ros2_src_exists: `{ROS2_SRC.exists()}`
- ros2_command_available: `{ros2_cmd is not None}`
- colcon_command_available: `{colcon_cmd is not None}`

## ROS2 packages

| package | path | setup.py | CMakeLists.txt | launch_files | python_files | cpp_files |
|---|---|---:|---:|---:|---:|---:|
{chr(10).join(package_rows_text)}

## Expected bridge topic contract

| direction | topic | found_in_source | hit_count | Python baseline signal |
|---|---|---:|---:|---|
{chr(10).join(topic_doc_lines)}

## 结果

- pass: `{all_pass}`
- bridge_package_found: `{bridge_pkg is not None}`
- all_expected_topics_found: `{all_expected_topics_found}`
- publish_topic_found_count: `{publish_found_count}`
- subscribe_topic_found_count: `{subscribe_found_count}`

## 输出

- Log: `results/logs_sample/stage09_ros2_cpp_interface_contract_inventory_log.csv`
- Topic map: `results/logs_sample/stage09_ros2_cpp_interface_topic_contract_map.csv`
- Summary: `results/logs_sample/stage09_ros2_cpp_interface_contract_inventory_summary.csv`

## 边界

本阶段不改变控制律，不完成 ROS2/C++ real-time controller，不完成 EKF，不完成 pure full WBC locomotion。

当前 baseline 仍是 mixed online control baseline。
""")

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 9.0 ROS2/C++ Interface Contract Inventory

Stage 9.0 完成 ROS2/C++ interface contract inventory。

- Script: `scripts/stage09_ros2_cpp_interface_contract_inventory.py`
- Log: `results/logs_sample/stage09_ros2_cpp_interface_contract_inventory_log.csv`
- Topic map: `results/logs_sample/stage09_ros2_cpp_interface_topic_contract_map.csv`
- Summary: `results/logs_sample/stage09_ros2_cpp_interface_contract_inventory_summary.csv`
- Docs: `docs/STAGE09_ROS2_CPP_INTERFACE_CONTRACT_INVENTORY.md`
- pass: `{all_pass}`
- bridge_package_found: `{bridge_pkg is not None}`
- all_expected_topics_found: `{all_expected_topics_found}`
- control_law_changed: `False`
- stage9_scope: `interface_inventory_only`

Stage 9.0 只做接口盘点，不写实时 C++ controller，不改变控制律。当前 baseline 仍是 mixed online control baseline。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 9.0 ROS2/C++ Interface Contract Inventory"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 9.0] ROS2/C++ interface contract inventory")
    print(f"pass={all_pass}")
    print(f"ros2_ws_exists={ROS2_WS.exists()}")
    print(f"ros2_src_exists={ROS2_SRC.exists()}")
    print(f"ros2_command_available={ros2_cmd is not None}")
    print(f"colcon_command_available={colcon_cmd is not None}")
    print(f"ros2_package_count={len(packages)}")
    print(f"bridge_package_found={bridge_pkg is not None}")
    print(f"all_expected_topics_found={all_expected_topics_found}")
    print(f"log_csv={INVENTORY_LOG.relative_to(ROOT)}")
    print(f"topic_map_csv={TOPIC_MAP_PATH.relative_to(ROOT)}")
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
