#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE125_SUMMARY = LOG_DIR / "stage12_publisher_construction_no_publish_freeze_summary.csv"
STAGE125_GATE = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage125.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"

DESIGN_CSV = LOG_DIR / "stage12_manual_enable_activation_design.csv"
LOG_PATH = LOG_DIR / "stage12_manual_enable_activation_design_log.csv"
SUMMARY_PATH = LOG_DIR / "stage12_manual_enable_activation_design_summary.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage126.csv"
DOC_PATH = ROOT / "docs/STAGE12_MANUAL_ENABLE_ACTIVATION_DESIGN_ONLY.md"

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

    s125 = load_summary(STAGE125_SUMMARY)

    stage125_pass = as_bool(s125.get("pass", "False"))
    no_publish_integrity_passed = as_bool(s125.get("publisher_construction_no_publish_integrity_passed", "False"))
    stage125_source_has_create_publisher = as_bool(s125.get("current_source_has_create_publisher", "False"))
    stage125_source_has_publish_call = as_bool(s125.get("current_source_has_publish_call", "True"))
    stage125_active_path = as_bool(s125.get("active_ros_publisher_path_exists", "False"))
    stage125_manual_active = as_bool(s125.get("manual_enable_active", "True"))
    stage125_torque_ready = as_bool(s125.get("torque_enable_ready", "True"))
    stage125_torque_enabled = as_bool(s125.get("torque_publisher_enabled", "True"))
    stage125_control_changed = as_bool(s125.get("control_law_changed", "True"))

    add_check(checks, "stage125_summary_exists", STAGE125_SUMMARY.exists(), True, STAGE125_SUMMARY.exists(), str(STAGE125_SUMMARY))
    add_check(checks, "stage125_pass", stage125_pass, True, stage125_pass)
    add_check(checks, "stage125_no_publish_integrity_passed", no_publish_integrity_passed, True, no_publish_integrity_passed)
    add_check(checks, "stage125_current_source_has_create_publisher", stage125_source_has_create_publisher, True, stage125_source_has_create_publisher)
    add_check(checks, "stage125_current_source_has_publish_call", stage125_source_has_publish_call, False, not stage125_source_has_publish_call)
    add_check(checks, "stage125_active_ros_publisher_path_exists", stage125_active_path, True, stage125_active_path)
    add_check(checks, "stage125_manual_enable_active", stage125_manual_active, False, not stage125_manual_active)
    add_check(checks, "stage125_torque_enable_ready", stage125_torque_ready, False, not stage125_torque_ready)
    add_check(checks, "stage125_torque_publisher_enabled", stage125_torque_enabled, False, not stage125_torque_enabled)
    add_check(checks, "stage125_control_law_changed", stage125_control_changed, False, not stage125_control_changed)

    source_before = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    source_hash_before = sha256_text(source_before)

    source_has_create_publisher = "create_publisher<std_msgs::msg::Float64MultiArray>" in source_before
    source_has_publish_call = ".publish(" in source_before or "->publish(" in source_before
    source_references_torque_topic = TORQUE_TOPIC in source_before
    source_has_active_publisher_member = "active_torque_cmd_publisher_" in source_before
    source_has_stage124_marker = (
        "kStage124PublisherConstructionImplemented" in source_before and
        "kStage124PublishCallImplemented = false" in source_before
    )
    source_declares_enable_param = 'declare_parameter<bool>("enable_torque_publisher", false)' in source_before
    source_declares_confirm_param = 'declare_parameter<bool>("confirm_torque_publisher_enable", false)' in source_before

    add_check(checks, "cpp_source_exists", CPP_SOURCE.exists(), True, CPP_SOURCE.exists(), str(CPP_SOURCE))
    add_check(checks, "source_has_create_publisher", source_has_create_publisher, True, source_has_create_publisher)
    add_check(checks, "source_has_no_publish_call", source_has_publish_call, False, not source_has_publish_call)
    add_check(checks, "source_references_torque_topic", source_references_torque_topic, True, source_references_torque_topic)
    add_check(checks, "source_has_active_publisher_member", source_has_active_publisher_member, True, source_has_active_publisher_member)
    add_check(checks, "source_has_stage124_marker", source_has_stage124_marker, True, source_has_stage124_marker)
    add_check(checks, "source_declares_enable_param_default_false", source_declares_enable_param, True, source_declares_enable_param)
    add_check(checks, "source_declares_confirm_param_default_false", source_declares_confirm_param, True, source_declares_confirm_param)

    gate_rows = load_dicts(STAGE125_GATE)
    gate_status = {
        row.get("gate", ""): as_bool(row.get("current_status", "False"))
        for row in gate_rows
    }

    expected_gate_status = {
        "G2": False,
        "G3": True,
        "G8": False,
        "G9": True,
        "G22": True,
        "G23": True,
    }

    add_check(checks, "stage125_gate_exists", STAGE125_GATE.exists(), True, STAGE125_GATE.exists(), str(STAGE125_GATE))
    for gate, expected in expected_gate_status.items():
        value = gate_status.get(gate, None)
        add_check(checks, f"{gate}_status_after_stage125", value, expected, value == expected)

    design_rows = [
        {
            "item": "stage12_scope",
            "value": "manual_enable_activation_design_only",
            "applied_in_stage126": False,
            "allowed_in_future_activation_stage": True,
            "guard": "Stage 12.6 must not set runtime params true",
            "description": "Only records the future activation protocol.",
        },
        {
            "item": "future_enable_param",
            "value": "enable_torque_publisher := true",
            "applied_in_stage126": False,
            "allowed_in_future_activation_stage": True,
            "guard": "Can only be set in a later explicit runtime activation stage",
            "description": "First manual confirmation flag.",
        },
        {
            "item": "future_confirm_param",
            "value": "confirm_torque_publisher_enable := true",
            "applied_in_stage126": False,
            "allowed_in_future_activation_stage": True,
            "guard": "Can only be set in a later explicit runtime activation stage",
            "description": "Second manual confirmation flag.",
        },
        {
            "item": "future_activation_commands",
            "value": "ros2 param set /go1_disabled_controller_node enable_torque_publisher true; ros2 param set /go1_disabled_controller_node confirm_torque_publisher_enable true",
            "applied_in_stage126": False,
            "allowed_in_future_activation_stage": True,
            "guard": "Commands are documentation only in Stage 12.6",
            "description": "Future runtime-only activation commands.",
        },
        {
            "item": "future_no_source_change_rule",
            "value": "manual activation stage must not edit C++ source",
            "applied_in_stage126": False,
            "allowed_in_future_activation_stage": True,
            "guard": "source hash before/after must match",
            "description": "Manual activation is runtime-only.",
        },
        {
            "item": "future_no_publish_rule",
            "value": "manual activation stage must still forbid .publish( and ->publish(",
            "applied_in_stage126": False,
            "allowed_in_future_activation_stage": True,
            "guard": "source must still contain no publish call",
            "description": "Manual enable does not imply torque command publishing.",
        },
        {
            "item": "future_runtime_observation",
            "value": "publisher count positive; params true; no torque command publishing",
            "applied_in_stage126": False,
            "allowed_in_future_activation_stage": True,
            "guard": "runtime observations required after activation",
            "description": "Future activation stage must observe params and topic state.",
        },
        {
            "item": "future_revert_procedure",
            "value": "set confirm_torque_publisher_enable false; set enable_torque_publisher false",
            "applied_in_stage126": False,
            "allowed_in_future_activation_stage": True,
            "guard": "must be available before activation test",
            "description": "Fail-closed revert sequence.",
        },
        {
            "item": "future_abort_conditions",
            "value": "publish call appears; source hash changes; param set fails; unexpected topic count; controller exits",
            "applied_in_stage126": False,
            "allowed_in_future_activation_stage": True,
            "guard": "future activation script must fail closed",
            "description": "Abort policy for later activation stage.",
        },
    ]

    with DESIGN_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "item",
                "value",
                "applied_in_stage126",
                "allowed_in_future_activation_stage",
                "guard",
                "description",
            ],
        )
        writer.writeheader()
        writer.writerows(design_rows)

    manual_enable_activation_design_exists = DESIGN_CSV.exists()
    design_all_items_not_applied = all(not row["applied_in_stage126"] for row in design_rows)
    design_has_two_flag_activation = (
        any(row["item"] == "future_enable_param" for row in design_rows) and
        any(row["item"] == "future_confirm_param" for row in design_rows)
    )
    design_has_runtime_commands = any(row["item"] == "future_activation_commands" for row in design_rows)
    design_forbids_source_change = any(row["item"] == "future_no_source_change_rule" for row in design_rows)
    design_forbids_publish_call = any(row["item"] == "future_no_publish_rule" for row in design_rows)
    design_has_revert_procedure = any(row["item"] == "future_revert_procedure" for row in design_rows)
    design_has_abort_conditions = any(row["item"] == "future_abort_conditions" for row in design_rows)

    source_after = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    source_hash_after = sha256_text(source_after)
    source_unchanged_by_stage126 = source_hash_before == source_hash_after

    add_check(checks, "manual_enable_activation_design_exists", manual_enable_activation_design_exists, True, manual_enable_activation_design_exists, str(DESIGN_CSV))
    add_check(checks, "design_all_items_not_applied", design_all_items_not_applied, True, design_all_items_not_applied)
    add_check(checks, "design_has_two_flag_activation", design_has_two_flag_activation, True, design_has_two_flag_activation)
    add_check(checks, "design_has_runtime_commands", design_has_runtime_commands, True, design_has_runtime_commands)
    add_check(checks, "design_forbids_source_change", design_forbids_source_change, True, design_forbids_source_change)
    add_check(checks, "design_forbids_publish_call", design_forbids_publish_call, True, design_forbids_publish_call)
    add_check(checks, "design_has_revert_procedure", design_has_revert_procedure, True, design_has_revert_procedure)
    add_check(checks, "design_has_abort_conditions", design_has_abort_conditions, True, design_has_abort_conditions)
    add_check(checks, "source_unchanged_by_stage126", source_unchanged_by_stage126, True, source_unchanged_by_stage126)

    manual_enable_active = False
    active_ros_publisher_path_exists = True
    torque_enable_ready = False
    torque_publisher_enabled = False
    control_law_changed = False
    manual_enable_activation_design_complete = True

    gate_out_rows = []
    for row in gate_rows:
        gate_out_rows.append(row)

    gate_out_rows.append({
        "gate": "G24",
        "name": "Manual enable activation design exists",
        "required_before_torque_publish": True,
        "current_status": manual_enable_activation_design_complete,
        "evidence": str(DESIGN_CSV.relative_to(ROOT)),
    })

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(gate_out_rows)

    add_check(checks, "manual_enable_activation_design_complete", manual_enable_activation_design_complete, True, manual_enable_activation_design_complete)
    add_check(checks, "manual_enable_active", manual_enable_active, False, not manual_enable_active)
    add_check(checks, "active_ros_publisher_path_exists", active_ros_publisher_path_exists, True, active_ros_publisher_path_exists)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)
    add_check(checks, "torque_publisher_enabled", torque_publisher_enabled, False, not torque_publisher_enabled)
    add_check(checks, "control_law_changed", control_law_changed, False, not control_law_changed)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    DOC_PATH.write_text(f"""# Stage 12.6 Manual Enable Activation Design Only

## 一、结论

Stage 12.6 只设计 future manual enable activation protocol。

本阶段不设置 runtime params 为 true，不修改 C++ source，不添加 publish call，不发布 torque，不改变控制律。

## 二、前置状态

Stage 12.5:

- pass: {stage125_pass}
- publisher_construction_no_publish_integrity_passed: {no_publish_integrity_passed}
- current_source_has_create_publisher: {stage125_source_has_create_publisher}
- current_source_has_publish_call: {stage125_source_has_publish_call}
- active_ros_publisher_path_exists: {stage125_active_path}
- manual_enable_active: {stage125_manual_active}
- torque_enable_ready: {stage125_torque_ready}

## 三、当前 source guard

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: {source_has_create_publisher}
- source_has_publish_call: {source_has_publish_call}
- source_references_torque_topic: {source_references_torque_topic}
- source_has_active_publisher_member: {source_has_active_publisher_member}
- source_unchanged_by_stage126: {source_unchanged_by_stage126}

## 四、Manual enable activation design

Design CSV:

    results/logs_sample/stage12_manual_enable_activation_design.csv

Future activation protocol:

- set enable_torque_publisher true；
- set confirm_torque_publisher_enable true；
- no C++ source change；
- no publish call；
- runtime observations required；
- fail-closed revert procedure required；
- abort on source hash change, publish call, param failure, unexpected topic count, or controller exit。

## 五、Safety gate after Stage 12.6

新增：

- G24 manual enable activation design exists: {manual_enable_activation_design_complete}

仍为 False：

- G8 manual enable flags active at runtime: {manual_enable_active}

保持 True：

- G9 active ROS publisher path exists: {active_ros_publisher_path_exists}

Therefore:

    torque_enable_ready = {torque_enable_ready}

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.6 没有完成：

- manual enable activation；
- publish call；
- torque command publishing；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。
""")

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 12.6"])
        writer.writerow(["test_name", "manual_enable_activation_design_only"])
        writer.writerow(["stage125_pass", stage125_pass])
        writer.writerow(["stage125_publisher_construction_no_publish_integrity_passed", no_publish_integrity_passed])
        writer.writerow(["source_has_create_publisher", source_has_create_publisher])
        writer.writerow(["source_has_publish_call", source_has_publish_call])
        writer.writerow(["source_references_torque_topic", source_references_torque_topic])
        writer.writerow(["source_has_active_publisher_member", source_has_active_publisher_member])
        writer.writerow(["source_has_stage124_marker", source_has_stage124_marker])
        writer.writerow(["source_declares_enable_param_default_false", source_declares_enable_param])
        writer.writerow(["source_declares_confirm_param_default_false", source_declares_confirm_param])
        writer.writerow(["source_unchanged_by_stage126", source_unchanged_by_stage126])
        writer.writerow(["manual_enable_activation_design_exists", manual_enable_activation_design_exists])
        writer.writerow(["design_all_items_not_applied", design_all_items_not_applied])
        writer.writerow(["design_has_two_flag_activation", design_has_two_flag_activation])
        writer.writerow(["design_has_runtime_commands", design_has_runtime_commands])
        writer.writerow(["design_forbids_source_change", design_forbids_source_change])
        writer.writerow(["design_forbids_publish_call", design_forbids_publish_call])
        writer.writerow(["design_has_revert_procedure", design_has_revert_procedure])
        writer.writerow(["design_has_abort_conditions", design_has_abort_conditions])
        writer.writerow(["manual_enable_activation_design_complete", manual_enable_activation_design_complete])
        writer.writerow(["manual_enable_active", manual_enable_active])
        writer.writerow(["active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g2_no_publisher_construction", gate_status.get("G2", False)])
        writer.writerow(["g3_no_publish_call", gate_status.get("G3", False)])
        writer.writerow(["g8_manual_enable_active", manual_enable_active])
        writer.writerow(["g9_active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g23_publisher_construction_no_publish_freeze_passed", gate_status.get("G23", False)])
        writer.writerow(["g24_manual_enable_activation_design_exists", manual_enable_activation_design_complete])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", control_law_changed])
        writer.writerow(["torque_publisher_enabled", torque_publisher_enabled])
        writer.writerow(["torque_command_published_by_stage126", False])
        writer.writerow(["stage12_scope", "manual_enable_activation_design_only"])
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
## Stage 12.6 Manual Enable Activation Design Only

Stage 12.6 完成 manual enable activation design only。

- Script: `scripts/stage12_manual_enable_activation_design_only.py`
- Design: `results/logs_sample/stage12_manual_enable_activation_design.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage126.csv`
- Summary: `results/logs_sample/stage12_manual_enable_activation_design_summary.csv`
- Docs: `docs/STAGE12_MANUAL_ENABLE_ACTIVATION_DESIGN_ONLY.md`
- pass: `{all_pass}`
- manual_enable_activation_design_complete: `{manual_enable_activation_design_complete}`
- source_unchanged_by_stage126: `{source_unchanged_by_stage126}`
- active_ros_publisher_path_exists: `{active_ros_publisher_path_exists}`
- manual_enable_active: `{manual_enable_active}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `{torque_publisher_enabled}`
- control_law_changed: `{control_law_changed}`

Stage 12.6 只设计 manual enable activation，不设置参数，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 12.6 Manual Enable Activation Design Only"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 12.6] manual enable activation design only")
    print(f"pass={all_pass}")
    print(f"stage125_pass={stage125_pass}")
    print(f"manual_enable_activation_design_complete={manual_enable_activation_design_complete}")
    print(f"source_unchanged_by_stage126={source_unchanged_by_stage126}")
    print(f"active_ros_publisher_path_exists={active_ros_publisher_path_exists}")
    print(f"manual_enable_active={manual_enable_active}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print(f"control_law_changed={control_law_changed}")
    print(f"torque_publisher_enabled={torque_publisher_enabled}")
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
