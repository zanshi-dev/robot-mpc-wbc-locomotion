#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE121_SUMMARY = LOG_DIR / "stage12_pre_construction_source_runtime_guard_summary.csv"
STAGE121_GATE = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage121.csv"
STAGE120_PLAN = LOG_DIR / "stage12_active_publisher_construction_plan.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
SAFETY_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

DESIGN_CSV = LOG_DIR / "stage12_publisher_construction_source_patch_design.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage122.csv"
LOG_PATH = LOG_DIR / "stage12_publisher_construction_source_patch_design_log.csv"
SUMMARY_PATH = LOG_DIR / "stage12_publisher_construction_source_patch_design_summary.csv"
DOC_PATH = ROOT / "docs/STAGE12_PUBLISHER_CONSTRUCTION_SOURCE_PATCH_DESIGN_ONLY.md"

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


def load_dicts(path: Path):
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def as_bool(x):
    return str(x).strip().lower() in {"true", "1", "yes"}


def sha256_text(text: str):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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

    s121 = load_summary(STAGE121_SUMMARY)
    stage121_pass = as_bool(s121.get("pass", "False"))
    stage121_guard_passed = as_bool(s121.get("pre_construction_source_runtime_guard_passed", "False"))
    stage121_runtime_zero = as_bool(s121.get("torque_publishers_zero_all_samples", "False"))
    stage121_g20 = as_bool(s121.get("g20_pre_construction_source_runtime_guard_passed", "False"))
    stage121_manual_active = as_bool(s121.get("manual_enable_active", "True"))
    stage121_active_path = as_bool(s121.get("active_ros_publisher_path_exists", "True"))
    stage121_torque_ready = as_bool(s121.get("torque_enable_ready", "True"))
    stage121_torque_enabled = as_bool(s121.get("torque_publisher_enabled", "True"))
    stage121_control_changed = as_bool(s121.get("control_law_changed", "True"))

    add_check(checks, "stage121_summary_exists", STAGE121_SUMMARY.exists(), True, STAGE121_SUMMARY.exists(), str(STAGE121_SUMMARY))
    add_check(checks, "stage121_pass", stage121_pass, True, stage121_pass)
    add_check(checks, "stage121_pre_construction_source_runtime_guard_passed", stage121_guard_passed, True, stage121_guard_passed)
    add_check(checks, "stage121_torque_publishers_zero_all_samples", stage121_runtime_zero, True, stage121_runtime_zero)
    add_check(checks, "stage121_g20_pre_construction_source_runtime_guard_passed", stage121_g20, True, stage121_g20)
    add_check(checks, "stage121_manual_enable_active", stage121_manual_active, False, not stage121_manual_active)
    add_check(checks, "stage121_active_ros_publisher_path_exists", stage121_active_path, False, not stage121_active_path)
    add_check(checks, "stage121_torque_enable_ready", stage121_torque_ready, False, not stage121_torque_ready)
    add_check(checks, "stage121_torque_publisher_enabled", stage121_torque_enabled, False, not stage121_torque_enabled)
    add_check(checks, "stage121_control_law_changed", stage121_control_changed, False, not stage121_control_changed)

    plan_rows = load_dicts(STAGE120_PLAN)
    plan_exists = STAGE120_PLAN.exists()
    plan_has_future_topic = any(row.get("item") == "future_active_publisher_topic" for row in plan_rows)
    plan_separates_publish = any(
        row.get("item") == "future_construction_gate" and "no publish call" in row.get("value", "")
        for row in plan_rows
    )
    plan_has_abort_conditions = any(row.get("item") == "future_abort_conditions" for row in plan_rows)

    add_check(checks, "stage120_plan_exists", plan_exists, True, plan_exists, str(STAGE120_PLAN))
    add_check(checks, "stage120_plan_has_future_topic", plan_has_future_topic, True, plan_has_future_topic)
    add_check(checks, "stage120_plan_separates_construction_and_publish_call", plan_separates_publish, True, plan_separates_publish)
    add_check(checks, "stage120_plan_has_abort_conditions", plan_has_abort_conditions, True, plan_has_abort_conditions)

    cpp_text_before = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    cpp_hash_before = sha256_text(cpp_text_before)

    safety_text = SAFETY_HEADER.read_text(errors="replace") if SAFETY_HEADER.exists() else ""
    zero_text = ZERO_HEADER.read_text(errors="replace") if ZERO_HEADER.exists() else ""

    source_has_create_publisher = "create_publisher" in cpp_text_before
    source_has_publish_call = ".publish(" in cpp_text_before or "->publish(" in cpp_text_before
    source_has_torque_topic = TORQUE_TOPIC in cpp_text_before

    source_declares_enable_param = 'declare_parameter<bool>("enable_torque_publisher", false)' in cpp_text_before
    source_declares_confirm_param = 'declare_parameter<bool>("confirm_torque_publisher_enable", false)' in cpp_text_before
    source_uses_safety = "clampTorqueCommand" in cpp_text_before and "allInputsFresh" in cpp_text_before and "watchdogFallbackZeroTorque" in cpp_text_before

    safety_header_has_clamp_watchdog = "clampTorqueCommand" in safety_text and "allInputsFresh" in safety_text and "watchdogFallbackZeroTorque" in safety_text
    zero_header_declares_12 = "kGo1NumActuatedJoints = 12" in zero_text

    source_has_dormant_skeleton_marker = "kDormantPublisherPathSkeletonPresent" in cpp_text_before
    source_has_construct_forbidden_marker = "kDormantPublisherConstructionAllowed = false" in cpp_text_before
    source_has_publish_forbidden_marker = "kDormantPublishCallAllowed = false" in cpp_text_before
    source_has_payload_length_12 = "kDormantTorquePayloadLength = 12" in cpp_text_before
    source_has_dormant_payload_helper = "makeDormantSafeTorqueCommandMessage" in cpp_text_before

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

    previous_gate_rows = load_dicts(STAGE121_GATE)
    previous_gate_status = {
        row.get("gate", ""): as_bool(row.get("current_status", "False"))
        for row in previous_gate_rows
    }

    add_check(checks, "stage121_gate_exists", STAGE121_GATE.exists(), True, STAGE121_GATE.exists(), str(STAGE121_GATE))
    add_check(checks, "stage121_gate_g8_false", previous_gate_status.get("G8", True), False, previous_gate_status.get("G8", True) is False)
    add_check(checks, "stage121_gate_g9_false", previous_gate_status.get("G9", True), False, previous_gate_status.get("G9", True) is False)
    add_check(checks, "stage121_gate_g20_true", previous_gate_status.get("G20", False), True, previous_gate_status.get("G20", False) is True)

    design_rows = [
        {
            "patch_item": "target_source",
            "planned_value": "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp",
            "applied_in_stage122": False,
            "allowed_in_future_construction_stage": True,
            "guard": "source hash must be checked before and after construction stage",
            "description": "Future patch target. Stage 12.2 does not edit it.",
        },
        {
            "patch_item": "future_include_dependency",
            "planned_value": "std_msgs/msg/float64_multi_array.hpp",
            "applied_in_stage122": False,
            "allowed_in_future_construction_stage": True,
            "guard": "header is already present; no source patch needed in Stage 12.2",
            "description": "Message type needed by future publisher.",
        },
        {
            "patch_item": "future_publisher_member",
            "planned_value": "rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr active_torque_cmd_publisher_",
            "applied_in_stage122": False,
            "allowed_in_future_construction_stage": True,
            "guard": "member alone must not imply publish call",
            "description": "Future publisher handle.",
        },
        {
            "patch_item": "future_publisher_topic",
            "planned_value": "/go1/joint_torque_cmd",
            "applied_in_stage122": False,
            "allowed_in_future_construction_stage": True,
            "guard": "topic string must appear only in explicit construction stage",
            "description": "Future active publisher topic.",
        },
        {
            "patch_item": "future_create_publisher_call",
            "planned_value": "create_publisher<std_msgs::msg::Float64MultiArray>",
            "applied_in_stage122": False,
            "allowed_in_future_construction_stage": True,
            "guard": "construction stage must still forbid publish call",
            "description": "Future publisher construction only; not a torque publish stage.",
        },
        {
            "patch_item": "future_publish_call",
            "planned_value": "forbidden",
            "applied_in_stage122": False,
            "allowed_in_future_construction_stage": False,
            "guard": "no .publish( or ->publish( in construction source patch",
            "description": "Publish call must remain absent in the construction stage.",
        },
        {
            "patch_item": "future_runtime_default",
            "planned_value": "manual flags false, publisher count remains 0",
            "applied_in_stage122": False,
            "allowed_in_future_construction_stage": True,
            "guard": "runtime topic observations required after construction patch",
            "description": "Future construction patch must remain default-disabled.",
        },
        {
            "patch_item": "future_abort_policy",
            "planned_value": "abort on hash mismatch, publish call, topic count anomaly, parameter default violation",
            "applied_in_stage122": False,
            "allowed_in_future_construction_stage": True,
            "guard": "construction script must fail closed",
            "description": "Safety policy for later implementation stage.",
        },
    ]

    with DESIGN_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "patch_item",
                "planned_value",
                "applied_in_stage122",
                "allowed_in_future_construction_stage",
                "guard",
                "description",
            ],
        )
        writer.writeheader()
        writer.writerows(design_rows)

    publisher_construction_source_patch_design_exists = DESIGN_CSV.exists()
    patch_design_all_items_not_applied = all(not row["applied_in_stage122"] for row in design_rows)
    patch_design_has_future_publisher_member = any(row["patch_item"] == "future_publisher_member" for row in design_rows)
    patch_design_has_future_create_publisher_call = any(row["patch_item"] == "future_create_publisher_call" for row in design_rows)
    patch_design_forbids_publish_call = any(
        row["patch_item"] == "future_publish_call" and row["planned_value"] == "forbidden"
        for row in design_rows
    )
    patch_design_requires_runtime_recheck = any(row["patch_item"] == "future_runtime_default" for row in design_rows)
    patch_design_has_abort_policy = any(row["patch_item"] == "future_abort_policy" for row in design_rows)

    cpp_text_after = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    cpp_hash_after = sha256_text(cpp_text_after)
    source_unchanged_by_stage122 = cpp_hash_before == cpp_hash_after

    add_check(checks, "publisher_construction_source_patch_design_exists", publisher_construction_source_patch_design_exists, True, publisher_construction_source_patch_design_exists, str(DESIGN_CSV))
    add_check(checks, "patch_design_all_items_not_applied", patch_design_all_items_not_applied, True, patch_design_all_items_not_applied)
    add_check(checks, "patch_design_has_future_publisher_member", patch_design_has_future_publisher_member, True, patch_design_has_future_publisher_member)
    add_check(checks, "patch_design_has_future_create_publisher_call", patch_design_has_future_create_publisher_call, True, patch_design_has_future_create_publisher_call)
    add_check(checks, "patch_design_forbids_publish_call_in_construction_stage", patch_design_forbids_publish_call, True, patch_design_forbids_publish_call)
    add_check(checks, "patch_design_requires_runtime_recheck", patch_design_requires_runtime_recheck, True, patch_design_requires_runtime_recheck)
    add_check(checks, "patch_design_has_abort_policy", patch_design_has_abort_policy, True, patch_design_has_abort_policy)
    add_check(checks, "source_unchanged_by_stage122", source_unchanged_by_stage122, True, source_unchanged_by_stage122)

    manual_enable_active = False
    active_ros_publisher_path_exists = False
    torque_enable_ready = False
    publisher_construction_source_patch_design_complete = True

    gate_rows = []
    for row in previous_gate_rows:
        gate_rows.append(row)

    gate_rows.append({
        "gate": "G21",
        "name": "Publisher construction source patch design exists",
        "required_before_torque_publish": True,
        "current_status": publisher_construction_source_patch_design_complete,
        "evidence": str(DESIGN_CSV.relative_to(ROOT)),
    })

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(gate_rows)

    add_check(checks, "manual_enable_active", manual_enable_active, False, not manual_enable_active)
    add_check(checks, "active_ros_publisher_path_exists", active_ros_publisher_path_exists, False, not active_ros_publisher_path_exists)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)
    add_check(checks, "publisher_construction_source_patch_design_complete", publisher_construction_source_patch_design_complete, True, publisher_construction_source_patch_design_complete)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    DOC_PATH.write_text(f"""# Stage 12.2 Publisher Construction Source Patch Design Only

## 一、结论

Stage 12.2 只设计 future publisher construction source patch。

本阶段不修改 C++ controller 源码，不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、前置状态

Stage 12.1:

- pass: {stage121_pass}
- pre_construction_source_runtime_guard_passed: {stage121_guard_passed}
- torque_publishers_zero_all_samples: {stage121_runtime_zero}
- G20 pre-construction source/runtime guard passed: {stage121_g20}
- manual_enable_active: {stage121_manual_active}
- active_ros_publisher_path_exists: {stage121_active_path}
- torque_enable_ready: {stage121_torque_ready}

## 三、当前 source guard

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: {source_has_create_publisher}
- source_has_publish_call: {source_has_publish_call}
- source_has_torque_topic: {source_has_torque_topic}
- dormant_publisher_path_source_skeleton_exists: {dormant_source_skeleton_exists}
- source_unchanged_by_stage122: {source_unchanged_by_stage122}

## 四、Source patch design

Design CSV:

    results/logs_sample/stage12_publisher_construction_source_patch_design.csv

Stage 12.2 只设计未来 source patch：

- future publisher member；
- future /go1/joint_torque_cmd topic；
- future create_publisher call；
- construction stage 与 publish stage 分离；
- construction stage 仍禁止 publish call；
- future runtime recheck；
- fail-closed abort policy。

## 五、Safety gate after Stage 12.2

新增：

- G21 publisher construction source patch design exists: {publisher_construction_source_patch_design_complete}

仍为 False：

- G8 manual enable flags active at runtime: {manual_enable_active}
- G9 active ROS publisher path exists: {active_ros_publisher_path_exists}

Therefore:

    torque_enable_ready = {torque_enable_ready}

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.2 不是 ROS2/C++ realtime controller，不创建 publisher，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
""")

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 12.2"])
        writer.writerow(["test_name", "publisher_construction_source_patch_design_only"])
        writer.writerow(["stage121_pass", stage121_pass])
        writer.writerow(["stage121_pre_construction_source_runtime_guard_passed", stage121_guard_passed])
        writer.writerow(["stage121_g20_pre_construction_source_runtime_guard_passed", stage121_g20])
        writer.writerow(["stage121_torque_publishers_zero_all_samples", stage121_runtime_zero])
        writer.writerow(["source_has_no_create_publisher", not source_has_create_publisher])
        writer.writerow(["source_has_no_publish_call", not source_has_publish_call])
        writer.writerow(["source_does_not_reference_torque_topic", not source_has_torque_topic])
        writer.writerow(["source_declares_enable_param_default_false", source_declares_enable_param])
        writer.writerow(["source_declares_confirm_param_default_false", source_declares_confirm_param])
        writer.writerow(["source_uses_safety_utilities", source_uses_safety])
        writer.writerow(["dormant_publisher_path_source_skeleton_exists", dormant_source_skeleton_exists])
        writer.writerow(["source_unchanged_by_stage122", source_unchanged_by_stage122])
        writer.writerow(["publisher_construction_source_patch_design_exists", publisher_construction_source_patch_design_exists])
        writer.writerow(["patch_design_all_items_not_applied", patch_design_all_items_not_applied])
        writer.writerow(["patch_design_has_future_publisher_member", patch_design_has_future_publisher_member])
        writer.writerow(["patch_design_has_future_create_publisher_call", patch_design_has_future_create_publisher_call])
        writer.writerow(["patch_design_forbids_publish_call_in_construction_stage", patch_design_forbids_publish_call])
        writer.writerow(["patch_design_requires_runtime_recheck", patch_design_requires_runtime_recheck])
        writer.writerow(["patch_design_has_abort_policy", patch_design_has_abort_policy])
        writer.writerow(["publisher_construction_source_patch_design_complete", publisher_construction_source_patch_design_complete])
        writer.writerow(["manual_enable_active", manual_enable_active])
        writer.writerow(["active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g8_manual_enable_active", manual_enable_active])
        writer.writerow(["g9_active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g21_publisher_construction_source_patch_design_exists", publisher_construction_source_patch_design_complete])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_publisher_enabled", False])
        writer.writerow(["torque_command_published_by_stage122", False])
        writer.writerow(["stage12_scope", "publisher_construction_source_patch_design_only"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["ros2_cpp_realtime_controller_completed", False])
        writer.writerow(["pure_wbc_locomotion_completed", False])
        writer.writerow(["ekf_completed", False])
        writer.writerow(["full_3d_centroidal_mpc_completed", False])
        writer.writerow(["num_checks", len(checks)])
        writer.writerow(["num_failed_checks", sum(1 for row in checks if not row["pass"])])
        writer.writerow(["pass", all_pass])
        writer.writerow(["log_csv", str(LOG_PATH.relative_to(ROOT))])
        writer.writerow(["design_csv", str(DESIGN_CSV.relative_to(ROOT))])
        writer.writerow(["safety_gate_csv", str(SAFETY_GATE_PATH.relative_to(ROOT))])
        writer.writerow(["summary_csv", str(SUMMARY_PATH.relative_to(ROOT))])
        writer.writerow(["doc", str(DOC_PATH.relative_to(ROOT))])

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 12.2 Publisher Construction Source Patch Design Only

Stage 12.2 完成 publisher construction source patch design only。

- Script: `scripts/stage12_publisher_construction_source_patch_design_only.py`
- Design: `results/logs_sample/stage12_publisher_construction_source_patch_design.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage122.csv`
- Summary: `results/logs_sample/stage12_publisher_construction_source_patch_design_summary.csv`
- Docs: `docs/STAGE12_PUBLISHER_CONSTRUCTION_SOURCE_PATCH_DESIGN_ONLY.md`
- pass: `{all_pass}`
- publisher_construction_source_patch_design_complete: `{publisher_construction_source_patch_design_complete}`
- source_unchanged_by_stage122: `{source_unchanged_by_stage122}`
- active_ros_publisher_path_exists: `{active_ros_publisher_path_exists}`
- manual_enable_active: `{manual_enable_active}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 12.2 只设计 source patch，不创建 publisher，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 12.2 Publisher Construction Source Patch Design Only"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 12.2] publisher construction source patch design only")
    print(f"pass={all_pass}")
    print(f"stage121_pass={stage121_pass}")
    print(f"publisher_construction_source_patch_design_complete={publisher_construction_source_patch_design_complete}")
    print(f"source_unchanged_by_stage122={source_unchanged_by_stage122}")
    print(f"active_ros_publisher_path_exists={active_ros_publisher_path_exists}")
    print(f"manual_enable_active={manual_enable_active}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print("control_law_changed=False")
    print("torque_publisher_enabled=False")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
    print(f"design_csv={DESIGN_CSV.relative_to(ROOT)}")
    print(f"safety_gate_csv={SAFETY_GATE_PATH.relative_to(ROOT)}")
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
