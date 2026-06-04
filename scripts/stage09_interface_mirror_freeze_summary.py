#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

DOC_PATH = ROOT / "docs/STAGE09_0_6_INTERFACE_MIRROR_FREEZE_SUMMARY.md"
SUMMARY_PATH = LOG_DIR / "stage09_0_6_interface_mirror_freeze_summary.csv"
HASH_PATH = LOG_DIR / "stage09_0_6_interface_mirror_freeze_hashes.csv"
LOG_PATH = LOG_DIR / "stage09_0_6_interface_mirror_freeze_log.csv"

STAGE_SUMMARIES = {
    "Stage 9.0": LOG_DIR / "stage09_ros2_cpp_interface_contract_inventory_summary.csv",
    "Stage 9.1": LOG_DIR / "stage09_ros2_topic_schema_snapshot_summary.csv",
    "Stage 9.2": LOG_DIR / "stage09_python_baseline_ros2_field_mapping_summary.csv",
    "Stage 9.3": LOG_DIR / "stage09_ros2_cpp_interface_mirror_skeleton_check_summary.csv",
    "Stage 9.4": LOG_DIR / "stage09_ros2_runtime_mirror_smoke_test_summary.csv",
    "Stage 9.5": LOG_DIR / "stage09_cpp_mirror_contract_report_summary.csv",
    "Stage 9.6": LOG_DIR / "stage09_cpp_mirror_runtime_contract_guard_summary.csv",
}

FREEZE_FILES = [
    "ros2_ws/src/robot_mpc_wbc_cpp_interface/package.xml",
    "ros2_ws/src/robot_mpc_wbc_cpp_interface/CMakeLists.txt",
    "ros2_ws/src/robot_mpc_wbc_cpp_interface/src/interface_mirror_node.cpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_interface/launch/interface_mirror.launch.py",
    "docs/STAGE09_ROS2_CPP_INTERFACE_CONTRACT_INVENTORY.md",
    "docs/STAGE09_ROS2_TOPIC_SCHEMA_SNAPSHOT.md",
    "docs/STAGE09_PYTHON_BASELINE_ROS2_FIELD_MAPPING.md",
    "docs/STAGE09_ROS2_CPP_INTERFACE_MIRROR_SKELETON.md",
    "docs/STAGE09_ROS2_RUNTIME_MIRROR_SMOKE_TEST.md",
    "docs/STAGE09_CPP_MIRROR_CONTRACT_REPORT.md",
    "docs/STAGE09_CPP_MIRROR_RUNTIME_CONTRACT_GUARD.md",
    "results/logs_sample/stage09_ros2_cpp_interface_topic_contract_map.csv",
    "results/logs_sample/stage09_ros2_topic_schema_snapshot_map.csv",
    "results/logs_sample/stage09_python_baseline_ros2_field_mapping.csv",
    "results/logs_sample/stage09_ros2_runtime_mirror_topic_observations.csv",
    "results/logs_sample/stage09_cpp_mirror_runtime_contract_guard_samples.csv",
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


def sha256_file(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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

    control_law_changed_any = any(
        as_bool(metrics.get("control_law_changed", "False"))
        for metrics in summaries.values()
    )
    torque_published_any = any(
        as_bool(metrics.get("torque_command_published_by_stage94", "False")) or
        as_bool(metrics.get("torque_command_published_by_stage95", "False")) or
        as_bool(metrics.get("torque_command_published_by_stage96", "False"))
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
    ekf_completed_any = any(
        as_bool(metrics.get("ekf_completed", "False"))
        for metrics in summaries.values()
    )

    add_check(checks, "control_law_changed_any", control_law_changed_any, False, not control_law_changed_any)
    add_check(checks, "torque_published_any", torque_published_any, False, not torque_published_any)
    add_check(checks, "ros2_cpp_realtime_controller_completed_any", ros2_cpp_realtime_completed_any, False, not ros2_cpp_realtime_completed_any)
    add_check(checks, "pure_wbc_locomotion_completed_any", pure_wbc_completed_any, False, not pure_wbc_completed_any)
    add_check(checks, "ekf_completed_any", ekf_completed_any, False, not ekf_completed_any)

    s94 = summaries.get("Stage 9.4", {})
    s96 = summaries.get("Stage 9.6", {})

    add_check(checks, "stage94_torque_cmd_publisher_count_zero", s94.get("torque_cmd_publisher_count", ""), "0", s94.get("torque_cmd_publisher_count", "") == "0")
    add_check(checks, "stage96_torque_cmd_publishers_all_zero", as_bool(s96.get("torque_cmd_publishers_all_zero", "False")), True, as_bool(s96.get("torque_cmd_publishers_all_zero", "False")))
    add_check(checks, "stage96_source_has_no_create_publisher", as_bool(s96.get("source_has_no_create_publisher", "False")), True, as_bool(s96.get("source_has_no_create_publisher", "False")))
    add_check(checks, "stage96_source_has_no_publish_call", as_bool(s96.get("source_has_no_publish_call", "False")), True, as_bool(s96.get("source_has_no_publish_call", "False")))

    hash_rows = []
    missing_files = []

    for rel in FREEZE_FILES:
        path = ROOT / rel
        if path.exists():
            hash_rows.append({
                "file": rel,
                "exists": True,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            })
        else:
            missing_files.append(rel)
            hash_rows.append({
                "file": rel,
                "exists": False,
                "sha256": "",
                "size_bytes": "",
            })

    add_check(checks, "freeze_files_missing_count", len(missing_files), 0, len(missing_files) == 0)

    with HASH_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "exists", "sha256", "size_bytes"])
        writer.writeheader()
        writer.writerows(hash_rows)

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

    DOC_PATH.write_text(f"""# Stage 9.0–9.6 ROS2/C++ Interface Mirror Freeze Summary

## 一、冻结结论

Stage 9.0–9.6 已形成 ROS2/C++ interface mirror baseline。

该 baseline 只完成接口镜像、schema 记录、字段映射、C++ mirror skeleton、runtime smoke test 与 runtime contract guard。

它不是 ROS2/C++ real-time controller。

它不发布 torque command。

它没有改变 Stage 8 frozen Python baseline 的控制律。

## 二、当前 C++ mirror package

Package:

    ros2_ws/src/robot_mpc_wbc_cpp_interface

Node:

    go1_interface_mirror_node

Launch:

    ros2_ws/src/robot_mpc_wbc_cpp_interface/launch/interface_mirror.launch.py

## 三、Stage 9.0–9.6 汇总

| 阶段 | 测试名 | scope | pass | control_law_changed |
|---|---|---|---:|---:|
{chr(10).join(stage_rows)}

## 四、关键 runtime guard 结果

Stage 9.6 结果：

- sample_row_count: {s96.get("sample_row_count", "")}
- all_sample_topic_types_match: {s96.get("all_sample_topic_types_match", "")}
- torque_cmd_publishers_all_zero: {s96.get("torque_cmd_publishers_all_zero", "")}
- torque_cmd_subscribers_positive: {s96.get("torque_cmd_subscribers_positive", "")}
- source_has_no_create_publisher: {s96.get("source_has_no_create_publisher", "")}
- source_has_no_publish_call: {s96.get("source_has_no_publish_call", "")}

## 五、接口合同

已冻结 topic：

- /go1/joint_states
- /go1/base_state
- /go1/imu
- /go1/foot_contacts
- /go1/sim_time
- /go1/joint_torque_cmd

关键约束：

- /go1/joint_torque_cmd publisher count 必须为 0；
- C++ mirror 只能订阅，不允许发布 torque；
- C++ mirror 不允许调用 publish；
- joint order 继续遵守 MuJoCo actuator order: FR, FL, RR, RL；每条腿 hip, thigh, calf；
- quaternion 顺序继续遵守 Stage 8 runtime adapter contract。

## 六、边界

Stage 9.0–9.6 没有完成：

- ROS2/C++ real-time controller
- pure full WBC locomotion
- EKF
- full 3D centroidal MPC
- base velocity tracking
- hardware deployment

当前 baseline 仍是 mixed online control baseline。

## 七、冻结文件 hash

Hash log:

    results/logs_sample/stage09_0_6_interface_mirror_freeze_hashes.csv

## 八、结论

Stage 9.0–9.6 可作为 ROS2/C++ interface mirror frozen baseline。

后续如果进入控制器实现，必须先以该 baseline 做回归，且第一步应继续保持 torque publisher disabled。
""")

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 9.7"])
        writer.writerow(["test_name", "stage09_0_6_interface_mirror_freeze_summary"])
        writer.writerow(["stage90_pass", summaries["Stage 9.0"].get("pass", "False")])
        writer.writerow(["stage91_pass", summaries["Stage 9.1"].get("pass", "False")])
        writer.writerow(["stage92_pass", summaries["Stage 9.2"].get("pass", "False")])
        writer.writerow(["stage93_pass", summaries["Stage 9.3"].get("pass", "False")])
        writer.writerow(["stage94_pass", summaries["Stage 9.4"].get("pass", "False")])
        writer.writerow(["stage95_pass", summaries["Stage 9.5"].get("pass", "False")])
        writer.writerow(["stage96_pass", summaries["Stage 9.6"].get("pass", "False")])
        writer.writerow(["freeze_file_count", len(FREEZE_FILES)])
        writer.writerow(["missing_file_count", len(missing_files)])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_command_published_by_stage97", False])
        writer.writerow(["stage9_scope", "interface_mirror_freeze_summary_only"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["ros2_cpp_interface_mirror_frozen", True])
        writer.writerow(["ros2_cpp_realtime_controller_completed", False])
        writer.writerow(["pure_wbc_locomotion_completed", False])
        writer.writerow(["ekf_completed", False])
        writer.writerow(["full_3d_centroidal_mpc_completed", False])
        writer.writerow(["num_checks", len(checks)])
        writer.writerow(["num_failed_checks", sum(1 for row in checks if not row["pass"])])
        writer.writerow(["pass", all_pass])
        writer.writerow(["log_csv", str(LOG_PATH.relative_to(ROOT))])
        writer.writerow(["hash_csv", str(HASH_PATH.relative_to(ROOT))])
        writer.writerow(["summary_csv", str(SUMMARY_PATH.relative_to(ROOT))])
        writer.writerow(["doc", str(DOC_PATH.relative_to(ROOT))])

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 9.7 Stage 9.0–9.6 Interface Mirror Freeze Summary

Stage 9.7 生成了 Stage 9.0–9.6 ROS2/C++ interface mirror freeze summary。

- Script: `scripts/stage09_interface_mirror_freeze_summary.py`
- Log: `results/logs_sample/stage09_0_6_interface_mirror_freeze_log.csv`
- Hashes: `results/logs_sample/stage09_0_6_interface_mirror_freeze_hashes.csv`
- Summary: `results/logs_sample/stage09_0_6_interface_mirror_freeze_summary.csv`
- Docs: `docs/STAGE09_0_6_INTERFACE_MIRROR_FREEZE_SUMMARY.md`
- pass: `{all_pass}`
- ros2_cpp_interface_mirror_frozen: `True`
- control_law_changed: `False`
- torque_command_published_by_stage97: `False`
- stage9_scope: `interface_mirror_freeze_summary_only`

Stage 9.0–9.6 形成 ROS2/C++ interface mirror frozen baseline。它不是实时控制器，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 9.7 Stage 9.0–9.6 Interface Mirror Freeze Summary"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 9.7] Stage 9.0-9.6 interface mirror freeze summary")
    print(f"pass={all_pass}")
    print(f"missing_file_count={len(missing_files)}")
    print("ros2_cpp_interface_mirror_frozen=True")
    print("control_law_changed=False")
    print("torque_command_published_by_stage97=False")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
    print(f"hash_csv={HASH_PATH.relative_to(ROOT)}")
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
