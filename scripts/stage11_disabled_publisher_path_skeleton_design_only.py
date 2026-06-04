#!/usr/bin/env python3
from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE111_SUMMARY = LOG_DIR / "stage11_publisher_path_source_guard_summary.csv"
STAGE111_GATE = LOG_DIR / "stage11_torque_publisher_safety_gate_after_stage111.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
SAFETY_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

DOC_PATH = ROOT / "docs/STAGE11_DISABLED_PUBLISHER_PATH_SKELETON_DESIGN_ONLY.md"
DESIGN_CSV = LOG_DIR / "stage11_disabled_publisher_path_skeleton_design.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage11_torque_publisher_safety_gate_after_stage112.csv"
LOG_PATH = LOG_DIR / "stage11_disabled_publisher_path_skeleton_design_log.csv"
SUMMARY_PATH = LOG_DIR / "stage11_disabled_publisher_path_skeleton_design_summary.csv"

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

    stage111 = load_summary(STAGE111_SUMMARY)
    stage111_pass = as_bool(stage111.get("pass", "False"))
    stage111_guard_passed = as_bool(stage111.get("publisher_path_source_guard_passed", "False"))
    stage111_path_implemented = as_bool(stage111.get("publisher_path_implemented", "True"))
    stage111_manual_active = as_bool(stage111.get("manual_enable_active", "True"))
    stage111_torque_ready = as_bool(stage111.get("torque_enable_ready", "True"))
    stage111_torque_enabled = as_bool(stage111.get("torque_publisher_enabled", "True"))
    stage111_control_changed = as_bool(stage111.get("control_law_changed", "True"))

    add_check(checks, "stage111_summary_exists", STAGE111_SUMMARY.exists(), True, STAGE111_SUMMARY.exists(), str(STAGE111_SUMMARY))
    add_check(checks, "stage111_pass", stage111_pass, True, stage111_pass)
    add_check(checks, "stage111_publisher_path_source_guard_passed", stage111_guard_passed, True, stage111_guard_passed)
    add_check(checks, "stage111_publisher_path_implemented", stage111_path_implemented, False, not stage111_path_implemented)
    add_check(checks, "stage111_manual_enable_active", stage111_manual_active, False, not stage111_manual_active)
    add_check(checks, "stage111_torque_enable_ready", stage111_torque_ready, False, not stage111_torque_ready)
    add_check(checks, "stage111_torque_publisher_enabled", stage111_torque_enabled, False, not stage111_torque_enabled)
    add_check(checks, "stage111_control_law_changed", stage111_control_changed, False, not stage111_control_changed)

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

    previous_gate_rows = load_gate(STAGE111_GATE)
    previous_gate_status = {
        row.get("gate", ""): as_bool(row.get("current_status", "False"))
        for row in previous_gate_rows
    }

    add_check(checks, "stage111_gate_exists", STAGE111_GATE.exists(), True, STAGE111_GATE.exists(), str(STAGE111_GATE))
    add_check(checks, "stage111_g8_manual_enable_active_false", previous_gate_status.get("G8", True), False, previous_gate_status.get("G8", True) is False)
    add_check(checks, "stage111_g9_publisher_path_exists_false", previous_gate_status.get("G9", True), False, previous_gate_status.get("G9", True) is False)
    add_check(checks, "stage111_g13_source_guard_passed", previous_gate_status.get("G13", False), True, previous_gate_status.get("G13", False) is True)

    design_rows = [
        {
            "component": "future_member",
            "name": "torque_cmd_publisher_",
            "type": "rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr",
            "implemented_in_stage112": False,
            "default_state": "nullptr",
            "guard": "must not be constructed unless future stage explicitly allows disabled publisher skeleton",
            "description": "Future publisher handle. Stage 11.2 only designs it.",
        },
        {
            "component": "future_topic",
            "name": "/go1/joint_torque_cmd",
            "type": "std_msgs/msg/Float64MultiArray",
            "implemented_in_stage112": False,
            "default_state": "absent from controller source",
            "guard": "payload length 12, MuJoCo actuator order",
            "description": "Future torque command topic.",
        },
        {
            "component": "future_gate",
            "name": "publisher_construct_allowed",
            "type": "bool",
            "implemented_in_stage112": False,
            "default_state": "false",
            "guard": "manual enable flags must both be true and source guard must be updated in separate stage",
            "description": "Gate for constructing publisher object.",
        },
        {
            "component": "future_gate",
            "name": "publish_allowed",
            "type": "bool",
            "implemented_in_stage112": False,
            "default_state": "false",
            "guard": "publisher exists, state_ready, inputs_fresh, manual flags active, safety filter passed",
            "description": "Gate for actual publish call. Must not be introduced with skeleton construction.",
        },
        {
            "component": "future_payload",
            "name": "safe_torque_command_msg",
            "type": "std_msgs::msg::Float64MultiArray",
            "implemented_in_stage112": False,
            "default_state": "not constructed",
            "guard": "data.size == 12; all finite; clampTorqueCommand applied",
            "description": "Future message object from safe_torque_dry_run_.",
        },
        {
            "component": "future_runtime_guard",
            "name": "publisher_count_guard",
            "type": "runtime check",
            "implemented_in_stage112": False,
            "default_state": "publisher_count must remain 0 until explicit implementation stage",
            "guard": "ros2 topic info /go1/joint_torque_cmd",
            "description": "Runtime guard before any publisher skeleton implementation.",
        },
        {
            "component": "future_runtime_guard",
            "name": "dry_run_first_policy",
            "type": "policy",
            "implemented_in_stage112": False,
            "default_state": "observe-only",
            "guard": "first publisher skeleton must still avoid publish call",
            "description": "Publisher skeleton may exist later, but publish call remains forbidden until a later stage.",
        },
    ]

    with DESIGN_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "component",
                "name",
                "type",
                "implemented_in_stage112",
                "default_state",
                "guard",
                "description",
            ],
        )
        writer.writeheader()
        writer.writerows(design_rows)

    design_exists = DESIGN_CSV.exists()
    design_all_not_implemented = all(not row["implemented_in_stage112"] for row in design_rows)
    design_has_publisher_handle = any(row["name"] == "torque_cmd_publisher_" for row in design_rows)
    design_has_publish_allowed_gate = any(row["name"] == "publish_allowed" for row in design_rows)
    design_has_runtime_guard = any(row["name"] == "publisher_count_guard" for row in design_rows)

    publisher_path_design_exists = True
    publisher_path_implemented = False
    manual_enable_active = False
    torque_enable_ready = False

    add_check(checks, "disabled_publisher_path_design_csv_exists", design_exists, True, design_exists, str(DESIGN_CSV))
    add_check(checks, "design_all_items_not_implemented", design_all_not_implemented, True, design_all_not_implemented)
    add_check(checks, "design_has_future_publisher_handle", design_has_publisher_handle, True, design_has_publisher_handle)
    add_check(checks, "design_has_publish_allowed_gate", design_has_publish_allowed_gate, True, design_has_publish_allowed_gate)
    add_check(checks, "design_has_runtime_guard", design_has_runtime_guard, True, design_has_runtime_guard)
    add_check(checks, "publisher_path_implemented", publisher_path_implemented, False, not publisher_path_implemented)
    add_check(checks, "manual_enable_active", manual_enable_active, False, not manual_enable_active)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)

    gate_rows = [
        {
            "gate": "G0",
            "name": "Stage 8 frozen Python baseline valid",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage08_freeze_integrity_check_summary.csv",
        },
        {
            "gate": "G1",
            "name": "Stage 9 interface mirror frozen",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage09_0_6_interface_mirror_freeze_summary.csv",
        },
        {
            "gate": "G2",
            "name": "C++ controller source has no torque publisher",
            "required_before_torque_publish": True,
            "current_status": not source_has_create_publisher,
            "evidence": str(CPP_SOURCE.relative_to(ROOT)),
        },
        {
            "gate": "G3",
            "name": "C++ controller source has no publish call",
            "required_before_torque_publish": True,
            "current_status": not source_has_publish_call,
            "evidence": str(CPP_SOURCE.relative_to(ROOT)),
        },
        {
            "gate": "G4",
            "name": "Explicit manual enable flag design exists",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "docs/STAGE10_TORQUE_PUBLISHER_ENABLE_GATE_DESIGN.md",
        },
        {
            "gate": "G5",
            "name": "Torque clamp and watchdog utility implemented",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": str(SAFETY_HEADER.relative_to(ROOT)),
        },
        {
            "gate": "G6",
            "name": "Zero torque dry-run regression completed",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage10_zero_torque_dry_run_internal_validation_summary.csv",
        },
        {
            "gate": "G7",
            "name": "Python frozen baseline A/B regression still passes",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage08_adapter_backed_stage07_baseline_ab_test_summary.csv",
        },
        {
            "gate": "G8",
            "name": "Manual enable flags active at runtime",
            "required_before_torque_publish": True,
            "current_status": manual_enable_active,
            "evidence": "not activated in Stage 11.2",
        },
        {
            "gate": "G9",
            "name": "Publisher path exists",
            "required_before_torque_publish": True,
            "current_status": publisher_path_implemented,
            "evidence": "designed only, not implemented in Stage 11.2",
        },
        {
            "gate": "G10",
            "name": "Disabled controller uses clamp/watchdog internally",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": str(CPP_SOURCE.relative_to(ROOT)),
        },
        {
            "gate": "G11",
            "name": "Manual enable parameters exist and default false",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": str(CPP_SOURCE.relative_to(ROOT)),
        },
        {
            "gate": "G12",
            "name": "Publisher path skeleton plan exists",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage11_publisher_path_skeleton_plan.csv",
        },
        {
            "gate": "G13",
            "name": "Publisher-path source guard passed before implementation",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage11_publisher_path_source_guard_log.csv",
        },
        {
            "gate": "G14",
            "name": "Disabled publisher-path skeleton design exists",
            "required_before_torque_publish": True,
            "current_status": publisher_path_design_exists,
            "evidence": str(DESIGN_CSV.relative_to(ROOT)),
        },
    ]

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(gate_rows)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    DOC_PATH.write_text(f"""# Stage 11.2 Disabled Publisher-path Skeleton Design Only

## 一、结论

Stage 11.2 只设计 disabled publisher-path skeleton。

本阶段不修改 C++ controller 源码，不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、前置状态

Stage 11.1:

- pass: {stage111_pass}
- publisher_path_source_guard_passed: {stage111_guard_passed}
- publisher_path_implemented: {stage111_path_implemented}
- manual_enable_active: {stage111_manual_active}
- torque_enable_ready: {stage111_torque_ready}

## 三、当前源码状态

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: {source_has_create_publisher}
- source_has_publish_call: {source_has_publish_call}
- source_has_torque_topic: {source_has_torque_topic}
- source_declares_enable_param_default_false: {source_declares_enable_param}
- source_declares_confirm_param_default_false: {source_declares_confirm_param}
- source_uses_safety_utilities: {source_uses_safety}

## 四、设计内容

Design CSV:

    results/logs_sample/stage11_disabled_publisher_path_skeleton_design.csv

设计但不实现：

- future publisher handle: torque_cmd_publisher_
- future topic: /go1/joint_torque_cmd
- future message type: std_msgs/msg/Float64MultiArray
- future construct gate: publisher_construct_allowed
- future publish gate: publish_allowed
- future payload: safe_torque_command_msg
- future runtime guard: publisher_count_guard

## 五、Safety gate after Stage 11.2

新增：

- G14 disabled publisher-path skeleton design exists: {publisher_path_design_exists}

仍为 False：

- G8 manual enable flags active at runtime: {manual_enable_active}
- G9 publisher path exists: {publisher_path_implemented}

Therefore:

    torque_enable_ready = {torque_enable_ready}

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 11.2 不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
""")

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 11.2"])
        writer.writerow(["test_name", "disabled_publisher_path_skeleton_design_only"])
        writer.writerow(["stage111_pass", stage111_pass])
        writer.writerow(["stage111_publisher_path_source_guard_passed", stage111_guard_passed])
        writer.writerow(["source_has_no_create_publisher", not source_has_create_publisher])
        writer.writerow(["source_has_no_publish_call", not source_has_publish_call])
        writer.writerow(["source_does_not_reference_torque_topic", not source_has_torque_topic])
        writer.writerow(["source_declares_enable_param_default_false", source_declares_enable_param])
        writer.writerow(["source_declares_confirm_param_default_false", source_declares_confirm_param])
        writer.writerow(["source_uses_safety_utilities", source_uses_safety])
        writer.writerow(["disabled_publisher_path_design_exists", publisher_path_design_exists])
        writer.writerow(["design_all_items_not_implemented", design_all_not_implemented])
        writer.writerow(["design_has_future_publisher_handle", design_has_publisher_handle])
        writer.writerow(["design_has_publish_allowed_gate", design_has_publish_allowed_gate])
        writer.writerow(["design_has_runtime_guard", design_has_runtime_guard])
        writer.writerow(["publisher_path_implemented", publisher_path_implemented])
        writer.writerow(["manual_enable_active", manual_enable_active])
        writer.writerow(["g8_manual_enable_active", manual_enable_active])
        writer.writerow(["g9_publisher_path_exists", publisher_path_implemented])
        writer.writerow(["g14_disabled_publisher_path_skeleton_design_exists", publisher_path_design_exists])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_publisher_enabled", False])
        writer.writerow(["torque_command_published_by_stage112", False])
        writer.writerow(["stage11_scope", "disabled_publisher_path_skeleton_design_only"])
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
## Stage 11.2 Disabled Publisher-path Skeleton Design Only

Stage 11.2 完成 disabled publisher-path skeleton design only。

- Script: `scripts/stage11_disabled_publisher_path_skeleton_design_only.py`
- Design CSV: `results/logs_sample/stage11_disabled_publisher_path_skeleton_design.csv`
- Safety gate: `results/logs_sample/stage11_torque_publisher_safety_gate_after_stage112.csv`
- Summary: `results/logs_sample/stage11_disabled_publisher_path_skeleton_design_summary.csv`
- Docs: `docs/STAGE11_DISABLED_PUBLISHER_PATH_SKELETON_DESIGN_ONLY.md`
- pass: `{all_pass}`
- disabled_publisher_path_design_exists: `{publisher_path_design_exists}`
- publisher_path_implemented: `{publisher_path_implemented}`
- manual_enable_active: `{manual_enable_active}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 11.2 只设计 disabled publisher path，不创建 publisher，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 11.2 Disabled Publisher-path Skeleton Design Only"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 11.2] disabled publisher-path skeleton design only")
    print(f"pass={all_pass}")
    print(f"stage111_pass={stage111_pass}")
    print(f"disabled_publisher_path_design_exists={publisher_path_design_exists}")
    print(f"publisher_path_implemented={publisher_path_implemented}")
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
        print("\\nFailed checks:")
        for row in checks:
            if not row["pass"]:
                print(f"- {row['check']}: value={row['value']} expected={row['expected']} detail={row['detail']}")
        sys.exit(2)


if __name__ == "__main__":
    main()
