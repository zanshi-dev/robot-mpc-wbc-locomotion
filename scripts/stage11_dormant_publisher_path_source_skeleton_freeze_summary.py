#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE_SUMMARIES = {
    "Stage 11.3": LOG_DIR / "stage11_0_2_publisher_path_planning_freeze_summary.csv",
    "Stage 11.4": LOG_DIR / "stage11_disabled_publisher_path_skeleton_preflight_summary.csv",
    "Stage 11.5": LOG_DIR / "stage11_dormant_publisher_path_source_skeleton_summary.csv",
}

FINAL_GATE = LOG_DIR / "stage11_torque_publisher_safety_gate_after_stage115.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
SAFETY_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

DOC_PATH = ROOT / "docs/STAGE11_DORMANT_PUBLISHER_PATH_SOURCE_SKELETON_FREEZE_SUMMARY.md"
SUMMARY_PATH = LOG_DIR / "stage11_dormant_publisher_path_source_skeleton_freeze_summary.csv"
LOG_PATH = LOG_DIR / "stage11_dormant_publisher_path_source_skeleton_freeze_log.csv"
HASH_PATH = LOG_DIR / "stage11_dormant_publisher_path_source_skeleton_freeze_hashes.csv"

FREEZE_FILES = [
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp",

    "docs/STAGE11_0_2_PUBLISHER_PATH_PLANNING_FREEZE_SUMMARY.md",
    "docs/STAGE11_DISABLED_PUBLISHER_PATH_SKELETON_PREFLIGHT.md",
    "docs/STAGE11_DORMANT_PUBLISHER_PATH_SOURCE_SKELETON.md",

    "results/logs_sample/stage11_0_2_publisher_path_planning_freeze_summary.csv",
    "results/logs_sample/stage11_disabled_publisher_path_skeleton_preflight_summary.csv",
    "results/logs_sample/stage11_dormant_publisher_path_source_skeleton_summary.csv",

    "results/logs_sample/stage11_torque_publisher_safety_gate_after_stage112.csv",
    "results/logs_sample/stage11_torque_publisher_safety_gate_after_stage114.csv",
    "results/logs_sample/stage11_torque_publisher_safety_gate_after_stage115.csv",

    "results/logs_sample/stage11_disabled_publisher_path_skeleton_design.csv",
    "results/logs_sample/stage11_disabled_publisher_path_skeleton_preflight.csv",
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
            for k, v in zip(header, row):
                metrics[k.strip()] = v.strip()
            return metrics

    return metrics


def load_gate(path: Path):
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


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

    s113 = summaries["Stage 11.3"]
    s114 = summaries["Stage 11.4"]
    s115 = summaries["Stage 11.5"]

    add_check(checks, "stage113_publisher_path_planning_frozen", as_bool(s113.get("publisher_path_planning_frozen", "False")), True, as_bool(s113.get("publisher_path_planning_frozen", "False")))
    add_check(checks, "stage114_preflight_passed", as_bool(s114.get("disabled_publisher_path_skeleton_preflight_passed", "False")), True, as_bool(s114.get("disabled_publisher_path_skeleton_preflight_passed", "False")))
    add_check(checks, "stage115_dormant_skeleton_exists", as_bool(s115.get("dormant_publisher_path_source_skeleton_exists", "False")), True, as_bool(s115.get("dormant_publisher_path_source_skeleton_exists", "False")))
    add_check(checks, "stage115_torque_topic_publishers_zero", as_bool(s115.get("torque_topic_publishers_zero", "False")), True, as_bool(s115.get("torque_topic_publishers_zero", "False")))
    add_check(checks, "stage115_publisher_path_implemented", as_bool(s115.get("publisher_path_implemented", "True")), False, not as_bool(s115.get("publisher_path_implemented", "True")))
    add_check(checks, "stage115_manual_enable_active", as_bool(s115.get("manual_enable_active", "True")), False, not as_bool(s115.get("manual_enable_active", "True")))

    control_law_changed_any = any(as_bool(m.get("control_law_changed", "False")) for m in summaries.values())
    torque_publisher_enabled_any = any(as_bool(m.get("torque_publisher_enabled", "False")) for m in summaries.values())

    torque_command_published_any = False
    for metrics in summaries.values():
        for key, value in metrics.items():
            if key.startswith("torque_command_published_by_stage") and as_bool(value):
                torque_command_published_any = True

    add_check(checks, "control_law_changed_any", control_law_changed_any, False, not control_law_changed_any)
    add_check(checks, "torque_publisher_enabled_any", torque_publisher_enabled_any, False, not torque_publisher_enabled_any)
    add_check(checks, "torque_command_published_any", torque_command_published_any, False, not torque_command_published_any)

    cpp_text = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    safety_text = SAFETY_HEADER.read_text(errors="replace") if SAFETY_HEADER.exists() else ""
    zero_text = ZERO_HEADER.read_text(errors="replace") if ZERO_HEADER.exists() else ""

    source_has_create_publisher = "create_publisher" in cpp_text
    source_has_publish_call = ".publish(" in cpp_text or "->publish(" in cpp_text
    source_has_torque_topic = TORQUE_TOPIC in cpp_text

    source_declares_enable_param = 'declare_parameter<bool>("enable_torque_publisher", false)' in cpp_text
    source_declares_confirm_param = 'declare_parameter<bool>("confirm_torque_publisher_enable", false)' in cpp_text
    source_uses_safety = "clampTorqueCommand" in cpp_text and "allInputsFresh" in cpp_text and "watchdogFallbackZeroTorque" in cpp_text

    safety_header_has_clamp_watchdog = "clampTorqueCommand" in safety_text and "allInputsFresh" in safety_text and "watchdogFallbackZeroTorque" in safety_text
    zero_header_declares_12 = "kGo1NumActuatedJoints = 12" in zero_text

    source_has_dormant_skeleton_marker = "kDormantPublisherPathSkeletonPresent" in cpp_text
    source_has_construct_forbidden_marker = "kDormantPublisherConstructionAllowed = false" in cpp_text
    source_has_publish_forbidden_marker = "kDormantPublishCallAllowed = false" in cpp_text
    source_has_payload_length_12 = "kDormantTorquePayloadLength = 12" in cpp_text
    source_has_dormant_payload_helper = "makeDormantSafeTorqueCommandMessage" in cpp_text

    dormant_source_skeleton_exists = (
        source_has_dormant_skeleton_marker and
        source_has_construct_forbidden_marker and
        source_has_publish_forbidden_marker and
        source_has_payload_length_12 and
        source_has_dormant_payload_helper
    )

    add_check(checks, "cpp_source_exists", CPP_SOURCE.exists(), True, CPP_SOURCE.exists(), str(CPP_SOURCE))
    add_check(checks, "safety_header_exists", SAFETY_HEADER.exists(), True, SAFETY_HEADER.exists(), str(SAFETY_HEADER))
    add_check(checks, "zero_header_exists", ZERO_HEADER.exists(), True, ZERO_HEADER.exists(), str(ZERO_HEADER))
    add_check(checks, "source_has_no_create_publisher", source_has_create_publisher, False, not source_has_create_publisher)
    add_check(checks, "source_has_no_publish_call", source_has_publish_call, False, not source_has_publish_call)
    add_check(checks, "source_does_not_reference_torque_topic", source_has_torque_topic, False, not source_has_torque_topic)
    add_check(checks, "source_declares_enable_param_default_false", source_declares_enable_param, True, source_declares_enable_param)
    add_check(checks, "source_declares_confirm_param_default_false", source_declares_confirm_param, True, source_declares_confirm_param)
    add_check(checks, "source_uses_safety_utilities", source_uses_safety, True, source_uses_safety)
    add_check(checks, "safety_header_has_clamp_watchdog", safety_header_has_clamp_watchdog, True, safety_header_has_clamp_watchdog)
    add_check(checks, "zero_header_declares_12", zero_header_declares_12, True, zero_header_declares_12)
    add_check(checks, "source_has_dormant_skeleton_marker", source_has_dormant_skeleton_marker, True, source_has_dormant_skeleton_marker)
    add_check(checks, "source_has_construct_forbidden_marker", source_has_construct_forbidden_marker, True, source_has_construct_forbidden_marker)
    add_check(checks, "source_has_publish_forbidden_marker", source_has_publish_forbidden_marker, True, source_has_publish_forbidden_marker)
    add_check(checks, "source_has_payload_length_12", source_has_payload_length_12, True, source_has_payload_length_12)
    add_check(checks, "source_has_dormant_payload_helper", source_has_dormant_payload_helper, True, source_has_dormant_payload_helper)
    add_check(checks, "dormant_publisher_path_source_skeleton_exists", dormant_source_skeleton_exists, True, dormant_source_skeleton_exists)

    gate_rows = load_gate(FINAL_GATE)
    gate_status = {row.get("gate", ""): as_bool(row.get("current_status", "False")) for row in gate_rows}

    expected_gate_status = {
        "G0": True,
        "G1": True,
        "G2": True,
        "G3": True,
        "G4": True,
        "G5": True,
        "G6": True,
        "G7": True,
        "G8": False,
        "G9": False,
        "G10": True,
        "G11": True,
        "G12": True,
        "G13": True,
        "G14": True,
        "G15": True,
        "G16": True,
    }

    add_check(checks, "stage115_safety_gate_exists", FINAL_GATE.exists(), True, FINAL_GATE.exists(), str(FINAL_GATE))
    for gate, expected in expected_gate_status.items():
        value = gate_status.get(gate, None)
        add_check(checks, f"{gate}_status_after_stage115", value, expected, value == expected)

    torque_enable_ready = all(gate_status.get(gate, False) for gate in expected_gate_status)
    add_check(checks, "torque_enable_ready_after_stage115", torque_enable_ready, False, not torque_enable_ready)

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

    add_check(checks, "missing_freeze_file_count", len(missing_files), 0, len(missing_files) == 0)

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
            f"| {stage} | {metrics.get('test_name', '')} | {metrics.get('stage11_scope', '')} | {metrics.get('pass', '')} | {metrics.get('torque_publisher_enabled', '')} | {metrics.get('control_law_changed', '')} |"
        )

    DOC_PATH.write_text(f"""# Stage 11.6 Dormant Publisher-path Source Skeleton Freeze Summary

## 一、冻结结论

Stage 11.5 dormant publisher-path source skeleton 已冻结。

该 baseline 包含：

- Stage 11.3 publisher-path planning freeze；
- Stage 11.4 disabled publisher-path skeleton preflight；
- Stage 11.5 dormant publisher-path source skeleton；
- disabled controller 中的 dormant skeleton marker；
- construct forbidden marker；
- publish forbidden marker；
- 12-length dormant payload helper。

该 baseline 不创建 ROS torque publisher，不调用 publish，不引用 /go1/joint_torque_cmd，不发布 torque，不改变控制律。

## 二、Stage 11.3–11.5 汇总

| 阶段 | 测试名 | scope | pass | torque_publisher_enabled | control_law_changed |
|---|---|---|---:|---:|---:|
{chr(10).join(stage_rows)}

## 三、源码安全状态

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: {source_has_create_publisher}
- source_has_publish_call: {source_has_publish_call}
- source_has_torque_topic: {source_has_torque_topic}
- source_has_dormant_skeleton_marker: {source_has_dormant_skeleton_marker}
- source_has_construct_forbidden_marker: {source_has_construct_forbidden_marker}
- source_has_publish_forbidden_marker: {source_has_publish_forbidden_marker}
- source_has_payload_length_12: {source_has_payload_length_12}
- source_has_dormant_payload_helper: {source_has_dormant_payload_helper}

## 四、Safety gate after Stage 11.5

- G8 manual enable flags active at runtime: {gate_status.get("G8")}
- G9 active ROS publisher path exists: {gate_status.get("G9")}
- G15 disabled publisher-path skeleton preflight passed: {gate_status.get("G15")}
- G16 dormant publisher-path source skeleton exists: {gate_status.get("G16")}

Therefore:

    torque_enable_ready = {torque_enable_ready}

G8 与 G9 仍为 False，因此不能发布 torque。

## 五、冻结 hash

Hash CSV:

    results/logs_sample/stage11_dormant_publisher_path_source_skeleton_freeze_hashes.csv

## 六、明确边界

当前 baseline 仍是 mixed online control baseline。

Stage 11.6 没有完成：

- ROS torque publisher construction；
- /go1/joint_torque_cmd publisher；
- publish call；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。

## 七、结论

Stage 11.5 可作为 dormant publisher-path source skeleton frozen baseline。

后续如果继续，下一阶段只能做 runtime guard hardening；不得直接引入 create_publisher 或 publish call。
""")

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 11.6"])
        writer.writerow(["test_name", "dormant_publisher_path_source_skeleton_freeze_summary"])
        writer.writerow(["stage113_pass", s113.get("pass", "False")])
        writer.writerow(["stage114_pass", s114.get("pass", "False")])
        writer.writerow(["stage115_pass", s115.get("pass", "False")])
        writer.writerow(["freeze_file_count", len(FREEZE_FILES)])
        writer.writerow(["missing_file_count", len(missing_files)])
        writer.writerow(["publisher_path_planning_frozen", as_bool(s113.get("publisher_path_planning_frozen", "False"))])
        writer.writerow(["disabled_publisher_path_skeleton_preflight_passed", as_bool(s114.get("disabled_publisher_path_skeleton_preflight_passed", "False"))])
        writer.writerow(["dormant_publisher_path_source_skeleton_exists", dormant_source_skeleton_exists])
        writer.writerow(["source_has_no_create_publisher", not source_has_create_publisher])
        writer.writerow(["source_has_no_publish_call", not source_has_publish_call])
        writer.writerow(["source_does_not_reference_torque_topic", not source_has_torque_topic])
        writer.writerow(["source_has_dormant_skeleton_marker", source_has_dormant_skeleton_marker])
        writer.writerow(["source_has_construct_forbidden_marker", source_has_construct_forbidden_marker])
        writer.writerow(["source_has_publish_forbidden_marker", source_has_publish_forbidden_marker])
        writer.writerow(["source_has_payload_length_12", source_has_payload_length_12])
        writer.writerow(["source_has_dormant_payload_helper", source_has_dormant_payload_helper])
        writer.writerow(["stage115_torque_topic_publishers_zero", as_bool(s115.get("torque_topic_publishers_zero", "False"))])
        writer.writerow(["publisher_path_implemented", False])
        writer.writerow(["manual_enable_active", False])
        writer.writerow(["g8_manual_enable_active", gate_status.get("G8", False)])
        writer.writerow(["g9_active_ros_publisher_path_exists", gate_status.get("G9", False)])
        writer.writerow(["g16_dormant_publisher_path_source_skeleton_exists", gate_status.get("G16", False)])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_publisher_enabled", False])
        writer.writerow(["torque_command_published_by_stage116", False])
        writer.writerow(["stage11_scope", "dormant_publisher_path_source_skeleton_freeze_summary_only"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["dormant_publisher_path_source_skeleton_frozen", True])
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
## Stage 11.6 Dormant Publisher-path Source Skeleton Freeze Summary

Stage 11.6 冻结 Stage 11.5 dormant publisher-path source skeleton。

- Script: `scripts/stage11_dormant_publisher_path_source_skeleton_freeze_summary.py`
- Log: `results/logs_sample/stage11_dormant_publisher_path_source_skeleton_freeze_log.csv`
- Hashes: `results/logs_sample/stage11_dormant_publisher_path_source_skeleton_freeze_hashes.csv`
- Summary: `results/logs_sample/stage11_dormant_publisher_path_source_skeleton_freeze_summary.csv`
- Docs: `docs/STAGE11_DORMANT_PUBLISHER_PATH_SOURCE_SKELETON_FREEZE_SUMMARY.md`
- pass: `{all_pass}`
- dormant_publisher_path_source_skeleton_frozen: `True`
- dormant_publisher_path_source_skeleton_exists: `{dormant_source_skeleton_exists}`
- g8_manual_enable_active: `{gate_status.get("G8", False)}`
- g9_active_ros_publisher_path_exists: `{gate_status.get("G9", False)}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 11.6 只冻结 dormant source skeleton，不创建 ROS publisher，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 11.6 Dormant Publisher-path Source Skeleton Freeze Summary"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 11.6] dormant publisher-path source skeleton freeze summary")
    print(f"pass={all_pass}")
    print(f"missing_file_count={len(missing_files)}")
    print("dormant_publisher_path_source_skeleton_frozen=True")
    print(f"dormant_publisher_path_source_skeleton_exists={dormant_source_skeleton_exists}")
    print(f"g8_manual_enable_active={gate_status.get('G8', False)}")
    print(f"g9_active_ros_publisher_path_exists={gate_status.get('G9', False)}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print("control_law_changed=False")
    print("torque_publisher_enabled=False")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
    print(f"hash_csv={HASH_PATH.relative_to(ROOT)}")
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
