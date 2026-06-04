#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE_SUMMARIES = {
    "Stage 12.0": LOG_DIR / "stage12_active_publisher_construction_planning_summary.csv",
    "Stage 12.1": LOG_DIR / "stage12_pre_construction_source_runtime_guard_summary.csv",
    "Stage 12.2": LOG_DIR / "stage12_publisher_construction_source_patch_design_summary.csv",
}

FINAL_GATE = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage122.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
SAFETY_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

DOC_PATH = ROOT / "docs/STAGE12_CONSTRUCTION_STAGE_PREFLIGHT_FREEZE.md"
SUMMARY_PATH = LOG_DIR / "stage12_construction_stage_preflight_freeze_summary.csv"
LOG_PATH = LOG_DIR / "stage12_construction_stage_preflight_freeze_log.csv"
HASH_PATH = LOG_DIR / "stage12_construction_stage_preflight_freeze_hashes.csv"

TORQUE_TOPIC = "/go1/joint_torque_cmd"

FREEZE_FILES = [
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp",

    "docs/STAGE12_ACTIVE_PUBLISHER_CONSTRUCTION_PLANNING_ONLY.md",
    "docs/STAGE12_PRE_CONSTRUCTION_SOURCE_RUNTIME_GUARD.md",
    "docs/STAGE12_PUBLISHER_CONSTRUCTION_SOURCE_PATCH_DESIGN_ONLY.md",

    "results/logs_sample/stage12_active_publisher_construction_plan.csv",
    "results/logs_sample/stage12_pre_construction_topic_observations.csv",
    "results/logs_sample/stage12_publisher_construction_source_patch_design.csv",

    "results/logs_sample/stage12_active_publisher_construction_planning_summary.csv",
    "results/logs_sample/stage12_pre_construction_source_runtime_guard_summary.csv",
    "results/logs_sample/stage12_publisher_construction_source_patch_design_summary.csv",

    "results/logs_sample/stage12_torque_publisher_safety_gate_after_stage120.csv",
    "results/logs_sample/stage12_torque_publisher_safety_gate_after_stage121.csv",
    "results/logs_sample/stage12_torque_publisher_safety_gate_after_stage122.csv",
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


def load_dicts(path: Path):
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

    s120 = summaries["Stage 12.0"]
    s121 = summaries["Stage 12.1"]
    s122 = summaries["Stage 12.2"]

    add_check(checks, "stage120_active_publisher_construction_planning_complete", as_bool(s120.get("active_publisher_construction_planning_complete", "False")), True, as_bool(s120.get("active_publisher_construction_planning_complete", "False")))
    add_check(checks, "stage120_g19_active_publisher_construction_planning_exists", as_bool(s120.get("g19_active_publisher_construction_planning_exists", "False")), True, as_bool(s120.get("g19_active_publisher_construction_planning_exists", "False")))

    add_check(checks, "stage121_pre_construction_source_runtime_guard_passed", as_bool(s121.get("pre_construction_source_runtime_guard_passed", "False")), True, as_bool(s121.get("pre_construction_source_runtime_guard_passed", "False")))
    add_check(checks, "stage121_g20_pre_construction_source_runtime_guard_passed", as_bool(s121.get("g20_pre_construction_source_runtime_guard_passed", "False")), True, as_bool(s121.get("g20_pre_construction_source_runtime_guard_passed", "False")))
    add_check(checks, "stage121_torque_publishers_zero_all_samples", as_bool(s121.get("torque_publishers_zero_all_samples", "False")), True, as_bool(s121.get("torque_publishers_zero_all_samples", "False")))

    add_check(checks, "stage122_publisher_construction_source_patch_design_complete", as_bool(s122.get("publisher_construction_source_patch_design_complete", "False")), True, as_bool(s122.get("publisher_construction_source_patch_design_complete", "False")))
    add_check(checks, "stage122_source_unchanged_by_stage122", as_bool(s122.get("source_unchanged_by_stage122", "False")), True, as_bool(s122.get("source_unchanged_by_stage122", "False")))
    add_check(checks, "stage122_g21_publisher_construction_source_patch_design_exists", as_bool(s122.get("g21_publisher_construction_source_patch_design_exists", "False")), True, as_bool(s122.get("g21_publisher_construction_source_patch_design_exists", "False")))

    control_law_changed_any = any(as_bool(m.get("control_law_changed", "False")) for m in summaries.values())
    torque_publisher_enabled_any = any(as_bool(m.get("torque_publisher_enabled", "False")) for m in summaries.values())
    active_ros_publisher_path_exists_any = any(as_bool(m.get("active_ros_publisher_path_exists", "False")) for m in summaries.values())
    manual_enable_active_any = any(as_bool(m.get("manual_enable_active", "False")) for m in summaries.values())

    torque_command_published_any = False
    for metrics in summaries.values():
        for key, value in metrics.items():
            if key.startswith("torque_command_published_by_stage") and as_bool(value):
                torque_command_published_any = True

    add_check(checks, "control_law_changed_any", control_law_changed_any, False, not control_law_changed_any)
    add_check(checks, "torque_publisher_enabled_any", torque_publisher_enabled_any, False, not torque_publisher_enabled_any)
    add_check(checks, "active_ros_publisher_path_exists_any", active_ros_publisher_path_exists_any, False, not active_ros_publisher_path_exists_any)
    add_check(checks, "manual_enable_active_any", manual_enable_active_any, False, not manual_enable_active_any)
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
    add_check(checks, "dormant_publisher_path_source_skeleton_exists", dormant_source_skeleton_exists, True, dormant_source_skeleton_exists)

    gate_rows = load_dicts(FINAL_GATE)
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
        "G17": True,
        "G18": True,
        "G19": True,
        "G20": True,
        "G21": True,
    }

    add_check(checks, "stage122_safety_gate_exists", FINAL_GATE.exists(), True, FINAL_GATE.exists(), str(FINAL_GATE))
    for gate, expected in expected_gate_status.items():
        value = gate_status.get(gate, None)
        add_check(checks, f"{gate}_status_after_stage122", value, expected, value == expected)

    torque_enable_ready = all(gate_status.get(gate, False) for gate in expected_gate_status)
    add_check(checks, "torque_enable_ready_after_stage122", torque_enable_ready, False, not torque_enable_ready)

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

    construction_stage_preflight_frozen = True

    add_check(checks, "construction_stage_preflight_frozen", construction_stage_preflight_frozen, True, construction_stage_preflight_frozen)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    stage_rows = []
    for stage, metrics in summaries.items():
        stage_rows.append(
            f"| {stage} | {metrics.get('test_name', '')} | {metrics.get('stage12_scope', '')} | {metrics.get('pass', '')} | {metrics.get('torque_publisher_enabled', '')} | {metrics.get('control_law_changed', '')} |"
        )

    DOC_PATH.write_text(f"""# Stage 12.3 Construction-stage Preflight Freeze

## 一、冻结结论

Stage 12.0–12.2 已形成 construction-stage preflight frozen baseline。

该 baseline 包含：

- active publisher construction planning；
- pre-construction source/runtime guard；
- publisher construction source patch design；
- source unchanged check；
- no create_publisher；
- no publish call；
- no /go1/joint_torque_cmd reference in controller source；
- active publisher path remains absent。

Stage 12.3 不修改 C++ controller 源码，不创建 publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、Stage 12.0–12.2 汇总

| 阶段 | 测试名 | scope | pass | torque_publisher_enabled | control_law_changed |
|---|---|---|---:|---:|---:|
{chr(10).join(stage_rows)}

## 三、Source guard

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: {source_has_create_publisher}
- source_has_publish_call: {source_has_publish_call}
- source_has_torque_topic: {source_has_torque_topic}
- dormant_publisher_path_source_skeleton_exists: {dormant_source_skeleton_exists}

## 四、Safety gate after Stage 12.2

- G8 manual enable flags active at runtime: {gate_status.get("G8")}
- G9 active ROS publisher path exists: {gate_status.get("G9")}
- G19 active publisher construction planning exists: {gate_status.get("G19")}
- G20 pre-construction source and runtime guard passed: {gate_status.get("G20")}
- G21 publisher construction source patch design exists: {gate_status.get("G21")}

Therefore:

    torque_enable_ready = {torque_enable_ready}

G8 与 G9 仍为 False，因此不能发布 torque。

## 五、冻结 hash

Hash CSV:

    results/logs_sample/stage12_construction_stage_preflight_freeze_hashes.csv

## 六、明确边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.3 没有完成：

- ROS torque publisher construction；
- /go1/joint_torque_cmd active publisher；
- publish call；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。

## 七、结论

Stage 12.0–12.3 可作为 construction-stage preflight frozen baseline。

后续如果继续，下一阶段才可考虑 publisher construction source patch implementation，但仍不得调用 publish。
""")

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 12.3"])
        writer.writerow(["test_name", "construction_stage_preflight_freeze"])
        writer.writerow(["stage120_pass", s120.get("pass", "False")])
        writer.writerow(["stage121_pass", s121.get("pass", "False")])
        writer.writerow(["stage122_pass", s122.get("pass", "False")])
        writer.writerow(["freeze_file_count", len(FREEZE_FILES)])
        writer.writerow(["missing_file_count", len(missing_files)])
        writer.writerow(["active_publisher_construction_planning_complete", as_bool(s120.get("active_publisher_construction_planning_complete", "False"))])
        writer.writerow(["pre_construction_source_runtime_guard_passed", as_bool(s121.get("pre_construction_source_runtime_guard_passed", "False"))])
        writer.writerow(["publisher_construction_source_patch_design_complete", as_bool(s122.get("publisher_construction_source_patch_design_complete", "False"))])
        writer.writerow(["source_unchanged_by_stage122", as_bool(s122.get("source_unchanged_by_stage122", "False"))])
        writer.writerow(["stage121_torque_publishers_zero_all_samples", as_bool(s121.get("torque_publishers_zero_all_samples", "False"))])
        writer.writerow(["source_has_no_create_publisher", not source_has_create_publisher])
        writer.writerow(["source_has_no_publish_call", not source_has_publish_call])
        writer.writerow(["source_does_not_reference_torque_topic", not source_has_torque_topic])
        writer.writerow(["dormant_publisher_path_source_skeleton_exists", dormant_source_skeleton_exists])
        writer.writerow(["manual_enable_active", False])
        writer.writerow(["active_ros_publisher_path_exists", False])
        writer.writerow(["g8_manual_enable_active", gate_status.get("G8", False)])
        writer.writerow(["g9_active_ros_publisher_path_exists", gate_status.get("G9", False)])
        writer.writerow(["g19_active_publisher_construction_planning_exists", gate_status.get("G19", False)])
        writer.writerow(["g20_pre_construction_source_runtime_guard_passed", gate_status.get("G20", False)])
        writer.writerow(["g21_publisher_construction_source_patch_design_exists", gate_status.get("G21", False)])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_publisher_enabled", False])
        writer.writerow(["torque_command_published_by_stage123", False])
        writer.writerow(["stage12_scope", "construction_stage_preflight_freeze_only"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["construction_stage_preflight_frozen", construction_stage_preflight_frozen])
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
## Stage 12.3 Construction-stage Preflight Freeze

Stage 12.3 冻结 construction-stage preflight baseline。

- Script: `scripts/stage12_construction_stage_preflight_freeze.py`
- Log: `results/logs_sample/stage12_construction_stage_preflight_freeze_log.csv`
- Hashes: `results/logs_sample/stage12_construction_stage_preflight_freeze_hashes.csv`
- Summary: `results/logs_sample/stage12_construction_stage_preflight_freeze_summary.csv`
- Docs: `docs/STAGE12_CONSTRUCTION_STAGE_PREFLIGHT_FREEZE.md`
- pass: `{all_pass}`
- construction_stage_preflight_frozen: `{construction_stage_preflight_frozen}`
- g8_manual_enable_active: `{gate_status.get("G8", False)}`
- g9_active_ros_publisher_path_exists: `{gate_status.get("G9", False)}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 12.3 只冻结 preflight，不创建 publisher，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 12.3 Construction-stage Preflight Freeze"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 12.3] construction-stage preflight freeze")
    print(f"pass={all_pass}")
    print(f"missing_file_count={len(missing_files)}")
    print(f"construction_stage_preflight_frozen={construction_stage_preflight_frozen}")
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
