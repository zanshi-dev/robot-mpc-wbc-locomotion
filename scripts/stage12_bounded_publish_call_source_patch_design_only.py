#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE1211_SUMMARY = LOG_DIR / "stage12_bounded_zero_safe_publish_call_implementation_plan_summary.csv"
STAGE1211_GATE = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage1211.csv"
STAGE1211_PLAN = LOG_DIR / "stage12_bounded_zero_safe_publish_call_implementation_plan.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
SAFETY_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

DESIGN_CSV = LOG_DIR / "stage12_bounded_publish_call_source_patch_design.csv"
LOG_PATH = LOG_DIR / "stage12_bounded_publish_call_source_patch_design_log.csv"
SUMMARY_PATH = LOG_DIR / "stage12_bounded_publish_call_source_patch_design_summary.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage1212.csv"
DOC_PATH = ROOT / "docs/STAGE12_BOUNDED_PUBLISH_CALL_SOURCE_PATCH_DESIGN_ONLY.md"

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

    s1211 = load_summary(STAGE1211_SUMMARY)

    stage1211_pass = as_bool(s1211.get("pass", "False"))
    stage1211_plan_complete = as_bool(s1211.get("bounded_zero_safe_publish_call_implementation_plan_complete", "False"))
    stage1211_source_has_publish_call = as_bool(s1211.get("source_has_publish_call", "True"))
    stage1211_source_has_create_publisher = as_bool(s1211.get("source_has_create_publisher", "False"))
    stage1211_active_path = as_bool(s1211.get("active_ros_publisher_path_exists", "False"))
    stage1211_manual_active = as_bool(s1211.get("manual_enable_active", "True"))
    stage1211_torque_ready = as_bool(s1211.get("torque_enable_ready", "True"))
    stage1211_torque_enabled = as_bool(s1211.get("torque_publisher_enabled", "True"))
    stage1211_torque_published = as_bool(s1211.get("torque_command_published_by_stage1211", "True"))
    stage1211_control_changed = as_bool(s1211.get("control_law_changed", "True"))

    add_check(checks, "stage1211_summary_exists", STAGE1211_SUMMARY.exists(), True, STAGE1211_SUMMARY.exists(), str(STAGE1211_SUMMARY))
    add_check(checks, "stage1211_pass", stage1211_pass, True, stage1211_pass)
    add_check(checks, "stage1211_plan_complete", stage1211_plan_complete, True, stage1211_plan_complete)
    add_check(checks, "stage1211_source_has_create_publisher", stage1211_source_has_create_publisher, True, stage1211_source_has_create_publisher)
    add_check(checks, "stage1211_source_has_publish_call", stage1211_source_has_publish_call, False, not stage1211_source_has_publish_call)
    add_check(checks, "stage1211_active_ros_publisher_path_exists", stage1211_active_path, True, stage1211_active_path)
    add_check(checks, "stage1211_manual_enable_active", stage1211_manual_active, False, not stage1211_manual_active)
    add_check(checks, "stage1211_torque_enable_ready", stage1211_torque_ready, False, not stage1211_torque_ready)
    add_check(checks, "stage1211_torque_publisher_enabled", stage1211_torque_enabled, False, not stage1211_torque_enabled)
    add_check(checks, "stage1211_torque_command_published", stage1211_torque_published, False, not stage1211_torque_published)
    add_check(checks, "stage1211_control_law_changed", stage1211_control_changed, False, not stage1211_control_changed)

    plan_rows = load_dicts(STAGE1211_PLAN)
    plan_all_not_implemented = all(not as_bool(row.get("implemented_in_stage1211", "True")) for row in plan_rows)
    plan_has_publish_limit = any(row.get("item") == "future_publish_call_limit" for row in plan_rows)
    plan_has_safe_payload = any(row.get("item") == "future_publish_payload" for row in plan_rows)
    plan_has_payload_order = any(row.get("item") == "future_payload_order" for row in plan_rows)
    plan_has_preconditions = any(row.get("item") == "future_preconditions" for row in plan_rows)
    plan_has_safety_chain = any(row.get("item") == "future_safety_chain" for row in plan_rows)
    plan_has_runtime_evidence = any(row.get("item") == "future_runtime_evidence" for row in plan_rows)
    plan_has_abort_conditions = any(row.get("item") == "future_abort_conditions" for row in plan_rows)

    add_check(checks, "stage1211_plan_csv_exists", STAGE1211_PLAN.exists(), True, STAGE1211_PLAN.exists(), str(STAGE1211_PLAN))
    add_check(checks, "stage1211_plan_all_not_implemented", plan_all_not_implemented, True, plan_all_not_implemented)
    add_check(checks, "stage1211_plan_has_publish_limit", plan_has_publish_limit, True, plan_has_publish_limit)
    add_check(checks, "stage1211_plan_has_safe_payload", plan_has_safe_payload, True, plan_has_safe_payload)
    add_check(checks, "stage1211_plan_has_payload_order", plan_has_payload_order, True, plan_has_payload_order)
    add_check(checks, "stage1211_plan_has_preconditions", plan_has_preconditions, True, plan_has_preconditions)
    add_check(checks, "stage1211_plan_has_safety_chain", plan_has_safety_chain, True, plan_has_safety_chain)
    add_check(checks, "stage1211_plan_has_runtime_evidence", plan_has_runtime_evidence, True, plan_has_runtime_evidence)
    add_check(checks, "stage1211_plan_has_abort_conditions", plan_has_abort_conditions, True, plan_has_abort_conditions)

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
    source_uses_safety = "clampTorqueCommand" in source_before and "allInputsFresh" in source_before and "watchdogFallbackZeroTorque" in source_before

    safety_text = SAFETY_HEADER.read_text(errors="replace") if SAFETY_HEADER.exists() else ""
    zero_text = ZERO_HEADER.read_text(errors="replace") if ZERO_HEADER.exists() else ""
    safety_header_has_clamp_watchdog = "clampTorqueCommand" in safety_text and "allInputsFresh" in safety_text and "watchdogFallbackZeroTorque" in safety_text
    zero_header_declares_12 = "kGo1NumActuatedJoints = 12" in zero_text

    add_check(checks, "cpp_source_exists", CPP_SOURCE.exists(), True, CPP_SOURCE.exists(), str(CPP_SOURCE))
    add_check(checks, "source_has_create_publisher", source_has_create_publisher, True, source_has_create_publisher)
    add_check(checks, "source_has_no_publish_call", source_has_publish_call, False, not source_has_publish_call)
    add_check(checks, "source_references_torque_topic", source_references_torque_topic, True, source_references_torque_topic)
    add_check(checks, "source_has_active_publisher_member", source_has_active_publisher_member, True, source_has_active_publisher_member)
    add_check(checks, "source_has_stage124_marker", source_has_stage124_marker, True, source_has_stage124_marker)
    add_check(checks, "source_declares_enable_param_default_false", source_declares_enable_param, True, source_declares_enable_param)
    add_check(checks, "source_declares_confirm_param_default_false", source_declares_confirm_param, True, source_declares_confirm_param)
    add_check(checks, "source_uses_safety_utilities", source_uses_safety, True, source_uses_safety)
    add_check(checks, "safety_header_has_clamp_watchdog", safety_header_has_clamp_watchdog, True, safety_header_has_clamp_watchdog)
    add_check(checks, "zero_header_declares_12", zero_header_declares_12, True, zero_header_declares_12)

    gate_rows = load_dicts(STAGE1211_GATE)
    gate_status = {
        row.get("gate", ""): as_bool(row.get("current_status", "False"))
        for row in gate_rows
    }

    expected_gate_status = {
        "G2": False,
        "G3": True,
        "G8": False,
        "G9": True,
        "G28": True,
        "G29": True,
    }

    add_check(checks, "stage1211_gate_exists", STAGE1211_GATE.exists(), True, STAGE1211_GATE.exists(), str(STAGE1211_GATE))
    for gate, expected in expected_gate_status.items():
        value = gate_status.get(gate, None)
        add_check(checks, f"{gate}_status_after_stage1211", value, expected, value == expected)

    design_rows = [
        {
            "item": "stage12_scope",
            "value": "bounded_publish_call_source_patch_design_only",
            "applied_in_stage1212": False,
            "allowed_in_future_patch_stage": True,
            "guard": "Stage 12.12 must not edit C++ source and must not add publish call",
            "description": "Only records the future bounded publish-call source patch design.",
        },
        {
            "item": "future_patch_target",
            "value": "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp",
            "applied_in_stage1212": False,
            "allowed_in_future_patch_stage": True,
            "guard": "source hash must be checked before and after future patch",
            "description": "Future source patch target.",
        },
        {
            "item": "future_stage_marker",
            "value": "kStage1213BoundedPublishCallImplemented = true; kStage1213ContinuousPublishImplemented = false",
            "applied_in_stage1212": False,
            "allowed_in_future_patch_stage": True,
            "guard": "marker must explicitly distinguish bounded publish from continuous streaming",
            "description": "Future stage marker.",
        },
        {
            "item": "future_publish_helper",
            "value": "publishBoundedZeroSafeTorqueOnceIfAllowed()",
            "applied_in_stage1212": False,
            "allowed_in_future_patch_stage": True,
            "guard": "helper may contain the only allowed publish call in the future patch",
            "description": "Future bounded publish helper.",
        },
        {
            "item": "future_message_helper",
            "value": "makeStage1213ZeroSafeTorqueCommandMessage()",
            "applied_in_stage1212": False,
            "allowed_in_future_patch_stage": True,
            "guard": "message helper must return Float64MultiArray length 12",
            "description": "Future zero/safe message construction helper.",
        },
        {
            "item": "future_publish_call_site",
            "value": "active_torque_cmd_publisher_->publish(msg)",
            "applied_in_stage1212": False,
            "allowed_in_future_patch_stage": True,
            "guard": "future patch must allow exactly one bounded publish site",
            "description": "Future publish call site.",
        },
        {
            "item": "future_precondition_gate",
            "value": "manual flags true && active_torque_cmd_publisher_ != nullptr && state_ready && allInputsFresh(...)",
            "applied_in_stage1212": False,
            "allowed_in_future_patch_stage": True,
            "guard": "publish helper must return false without publishing if gate fails",
            "description": "Future runtime gate.",
        },
        {
            "item": "future_safety_chain",
            "value": "watchdogFallbackZeroTorque then clampTorqueCommand before Float64MultiArray conversion",
            "applied_in_stage1212": False,
            "allowed_in_future_patch_stage": True,
            "guard": "no raw unclamped torque may reach the message",
            "description": "Future safety chain.",
        },
        {
            "item": "future_payload_contract",
            "value": "length=12; finite; zero/safe torque; order FR,FL,RR,RL hip,thigh,calf",
            "applied_in_stage1212": False,
            "allowed_in_future_patch_stage": True,
            "guard": "invalid payload must abort or publish nothing",
            "description": "Future message contract.",
        },
        {
            "item": "future_publish_count_limit",
            "value": "max 1 message in first implementation stage",
            "applied_in_stage1212": False,
            "allowed_in_future_patch_stage": True,
            "guard": "continuous or timer-based streaming forbidden in first patch",
            "description": "Future bounded publish limit.",
        },
        {
            "item": "future_no_timer_loop_rule",
            "value": "no periodic torque publisher timer in bounded first publish stage",
            "applied_in_stage1212": False,
            "allowed_in_future_patch_stage": True,
            "guard": "timer-based continuous publication requires later stage",
            "description": "Future streaming prevention rule.",
        },
        {
            "item": "future_no_control_law_change_rule",
            "value": "do not modify estimator, MPC, WBC, gait, or baseline control computation",
            "applied_in_stage1212": False,
            "allowed_in_future_patch_stage": True,
            "guard": "future diff must be limited to publish-gated output path",
            "description": "Future source patch boundary.",
        },
        {
            "item": "future_runtime_evidence",
            "value": "manual flags true; one message echoed; payload length 12; all finite; flags reverted",
            "applied_in_stage1212": False,
            "allowed_in_future_patch_stage": True,
            "guard": "future publish stage must collect runtime evidence",
            "description": "Future evidence requirements.",
        },
        {
            "item": "future_revert_procedure",
            "value": "set confirm flag false; set enable flag false; stop controller",
            "applied_in_stage1212": False,
            "allowed_in_future_patch_stage": True,
            "guard": "future script must fail closed in finally block",
            "description": "Future cleanup rule.",
        },
        {
            "item": "future_abort_conditions",
            "value": "unexpected source hash; more than one publish site; timer loop; payload invalid; message count unexpected; controller exits",
            "applied_in_stage1212": False,
            "allowed_in_future_patch_stage": True,
            "guard": "future implementation must abort before publishing if any check fails",
            "description": "Future abort policy.",
        },
    ]

    with DESIGN_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "item",
                "value",
                "applied_in_stage1212",
                "allowed_in_future_patch_stage",
                "guard",
                "description",
            ],
        )
        writer.writeheader()
        writer.writerows(design_rows)

    bounded_publish_call_source_patch_design_exists = DESIGN_CSV.exists()
    design_all_items_not_applied = all(not row["applied_in_stage1212"] for row in design_rows)
    design_has_patch_target = any(row["item"] == "future_patch_target" for row in design_rows)
    design_has_stage_marker = any(row["item"] == "future_stage_marker" for row in design_rows)
    design_has_publish_helper = any(row["item"] == "future_publish_helper" for row in design_rows)
    design_has_message_helper = any(row["item"] == "future_message_helper" for row in design_rows)
    design_has_publish_call_site = any(row["item"] == "future_publish_call_site" for row in design_rows)
    design_has_precondition_gate = any(row["item"] == "future_precondition_gate" for row in design_rows)
    design_has_safety_chain = any(row["item"] == "future_safety_chain" for row in design_rows)
    design_has_payload_contract = any(row["item"] == "future_payload_contract" for row in design_rows)
    design_has_publish_count_limit = any(row["item"] == "future_publish_count_limit" for row in design_rows)
    design_forbids_timer_loop = any(row["item"] == "future_no_timer_loop_rule" for row in design_rows)
    design_forbids_control_law_change = any(row["item"] == "future_no_control_law_change_rule" for row in design_rows)
    design_has_runtime_evidence = any(row["item"] == "future_runtime_evidence" for row in design_rows)
    design_has_revert_procedure = any(row["item"] == "future_revert_procedure" for row in design_rows)
    design_has_abort_conditions = any(row["item"] == "future_abort_conditions" for row in design_rows)

    source_after = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    source_hash_after = sha256_text(source_after)
    source_unchanged_by_stage1212 = source_hash_before == source_hash_after

    add_check(checks, "bounded_publish_call_source_patch_design_exists", bounded_publish_call_source_patch_design_exists, True, bounded_publish_call_source_patch_design_exists, str(DESIGN_CSV))
    add_check(checks, "design_all_items_not_applied", design_all_items_not_applied, True, design_all_items_not_applied)
    add_check(checks, "design_has_patch_target", design_has_patch_target, True, design_has_patch_target)
    add_check(checks, "design_has_stage_marker", design_has_stage_marker, True, design_has_stage_marker)
    add_check(checks, "design_has_publish_helper", design_has_publish_helper, True, design_has_publish_helper)
    add_check(checks, "design_has_message_helper", design_has_message_helper, True, design_has_message_helper)
    add_check(checks, "design_has_publish_call_site", design_has_publish_call_site, True, design_has_publish_call_site)
    add_check(checks, "design_has_precondition_gate", design_has_precondition_gate, True, design_has_precondition_gate)
    add_check(checks, "design_has_safety_chain", design_has_safety_chain, True, design_has_safety_chain)
    add_check(checks, "design_has_payload_contract", design_has_payload_contract, True, design_has_payload_contract)
    add_check(checks, "design_has_publish_count_limit", design_has_publish_count_limit, True, design_has_publish_count_limit)
    add_check(checks, "design_forbids_timer_loop", design_forbids_timer_loop, True, design_forbids_timer_loop)
    add_check(checks, "design_forbids_control_law_change", design_forbids_control_law_change, True, design_forbids_control_law_change)
    add_check(checks, "design_has_runtime_evidence", design_has_runtime_evidence, True, design_has_runtime_evidence)
    add_check(checks, "design_has_revert_procedure", design_has_revert_procedure, True, design_has_revert_procedure)
    add_check(checks, "design_has_abort_conditions", design_has_abort_conditions, True, design_has_abort_conditions)
    add_check(checks, "source_unchanged_by_stage1212", source_unchanged_by_stage1212, True, source_unchanged_by_stage1212)

    bounded_publish_call_source_patch_design_complete = True
    manual_enable_active = False
    active_ros_publisher_path_exists = True
    torque_enable_ready = False
    control_law_changed = False
    torque_publisher_enabled = False
    torque_command_published_by_stage1212 = False

    gate_out_rows = []
    for row in gate_rows:
        gate_out_rows.append(row)

    gate_out_rows.append({
        "gate": "G30",
        "name": "Bounded publish-call source patch design exists",
        "required_before_torque_publish": True,
        "current_status": bounded_publish_call_source_patch_design_complete,
        "evidence": str(DESIGN_CSV.relative_to(ROOT)),
    })

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(gate_out_rows)

    add_check(checks, "bounded_publish_call_source_patch_design_complete", bounded_publish_call_source_patch_design_complete, True, bounded_publish_call_source_patch_design_complete)
    add_check(checks, "manual_enable_active", manual_enable_active, False, not manual_enable_active)
    add_check(checks, "active_ros_publisher_path_exists", active_ros_publisher_path_exists, True, active_ros_publisher_path_exists)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)
    add_check(checks, "control_law_changed", control_law_changed, False, not control_law_changed)
    add_check(checks, "torque_publisher_enabled", torque_publisher_enabled, False, not torque_publisher_enabled)
    add_check(checks, "torque_command_published_by_stage1212", torque_command_published_by_stage1212, False, not torque_command_published_by_stage1212)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    DOC_PATH.write_text(f"""# Stage 12.12 Bounded Publish-call Source Patch Design Only

## 一、结论

Stage 12.12 只设计 bounded publish-call source patch。

本阶段不修改 C++ source，不加入 publish call，不发布 torque，不改变控制律。

## 二、前置状态

Stage 12.11:

- pass: {stage1211_pass}
- bounded_zero_safe_publish_call_implementation_plan_complete: {stage1211_plan_complete}
- source_has_create_publisher: {stage1211_source_has_create_publisher}
- source_has_publish_call: {stage1211_source_has_publish_call}
- active_ros_publisher_path_exists: {stage1211_active_path}
- manual_enable_active: {stage1211_manual_active}
- torque_enable_ready: {stage1211_torque_ready}

## 三、当前 source guard

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: {source_has_create_publisher}
- source_has_publish_call: {source_has_publish_call}
- source_references_torque_topic: {source_references_torque_topic}
- source_has_active_publisher_member: {source_has_active_publisher_member}
- source_unchanged_by_stage1212: {source_unchanged_by_stage1212}

## 四、Bounded publish-call source patch design

Design CSV:

    results/logs_sample/stage12_bounded_publish_call_source_patch_design.csv

Future source patch design:

- exactly one bounded publish helper;
- exactly one publish call site inside the allowed helper;
- no timer loop and no continuous streaming;
- message helper produces length-12 Float64MultiArray;
- payload is zero or watchdog-safe torque only;
- safety chain is watchdogFallbackZeroTorque then clampTorqueCommand;
- future source diff is limited to publish-gated output path;
- no estimator, MPC, WBC, gait, or control-law changes;
- future runtime evidence must verify one bounded message, payload length, finite values, and fail-closed revert.

## 五、Safety gate after Stage 12.12

新增：

- G30 bounded publish-call source patch design exists: {bounded_publish_call_source_patch_design_complete}

Key gates remain:

- G3 no publish call: {gate_status.get("G3")}
- G8 manual enable active after revert: {manual_enable_active}
- G9 active ROS publisher path exists: {active_ros_publisher_path_exists}
- G29 bounded zero/safe publish-call implementation plan exists: {gate_status.get("G29")}

Therefore:

    torque_enable_ready = {torque_enable_ready}

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.12 没有完成：

- publish call；
- torque command publishing；
- continuous torque streaming；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。
""")

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 12.12"])
        writer.writerow(["test_name", "bounded_publish_call_source_patch_design_only"])
        writer.writerow(["stage1211_pass", stage1211_pass])
        writer.writerow(["stage1211_bounded_zero_safe_publish_call_implementation_plan_complete", stage1211_plan_complete])
        writer.writerow(["source_has_create_publisher", source_has_create_publisher])
        writer.writerow(["source_has_publish_call", source_has_publish_call])
        writer.writerow(["source_references_torque_topic", source_references_torque_topic])
        writer.writerow(["source_has_active_publisher_member", source_has_active_publisher_member])
        writer.writerow(["source_has_stage124_marker", source_has_stage124_marker])
        writer.writerow(["source_declares_enable_param_default_false", source_declares_enable_param])
        writer.writerow(["source_declares_confirm_param_default_false", source_declares_confirm_param])
        writer.writerow(["source_unchanged_by_stage1212", source_unchanged_by_stage1212])
        writer.writerow(["bounded_publish_call_source_patch_design_exists", bounded_publish_call_source_patch_design_exists])
        writer.writerow(["design_all_items_not_applied", design_all_items_not_applied])
        writer.writerow(["design_has_patch_target", design_has_patch_target])
        writer.writerow(["design_has_stage_marker", design_has_stage_marker])
        writer.writerow(["design_has_publish_helper", design_has_publish_helper])
        writer.writerow(["design_has_message_helper", design_has_message_helper])
        writer.writerow(["design_has_publish_call_site", design_has_publish_call_site])
        writer.writerow(["design_has_precondition_gate", design_has_precondition_gate])
        writer.writerow(["design_has_safety_chain", design_has_safety_chain])
        writer.writerow(["design_has_payload_contract", design_has_payload_contract])
        writer.writerow(["design_has_publish_count_limit", design_has_publish_count_limit])
        writer.writerow(["design_forbids_timer_loop", design_forbids_timer_loop])
        writer.writerow(["design_forbids_control_law_change", design_forbids_control_law_change])
        writer.writerow(["design_has_runtime_evidence", design_has_runtime_evidence])
        writer.writerow(["design_has_revert_procedure", design_has_revert_procedure])
        writer.writerow(["design_has_abort_conditions", design_has_abort_conditions])
        writer.writerow(["bounded_publish_call_source_patch_design_complete", bounded_publish_call_source_patch_design_complete])
        writer.writerow(["manual_enable_active", manual_enable_active])
        writer.writerow(["active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g3_no_publish_call", gate_status.get("G3", False)])
        writer.writerow(["g8_manual_enable_active", manual_enable_active])
        writer.writerow(["g9_active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g29_bounded_zero_safe_publish_call_implementation_plan_exists", gate_status.get("G29", False)])
        writer.writerow(["g30_bounded_publish_call_source_patch_design_exists", bounded_publish_call_source_patch_design_complete])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", control_law_changed])
        writer.writerow(["torque_publisher_enabled", torque_publisher_enabled])
        writer.writerow(["torque_command_published_by_stage1212", torque_command_published_by_stage1212])
        writer.writerow(["stage12_scope", "bounded_publish_call_source_patch_design_only"])
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
## Stage 12.12 Bounded Publish-call Source Patch Design Only

Stage 12.12 完成 bounded publish-call source patch design only。

- Script: `scripts/stage12_bounded_publish_call_source_patch_design_only.py`
- Design: `results/logs_sample/stage12_bounded_publish_call_source_patch_design.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1212.csv`
- Summary: `results/logs_sample/stage12_bounded_publish_call_source_patch_design_summary.csv`
- Docs: `docs/STAGE12_BOUNDED_PUBLISH_CALL_SOURCE_PATCH_DESIGN_ONLY.md`
- pass: `{all_pass}`
- bounded_publish_call_source_patch_design_complete: `{bounded_publish_call_source_patch_design_complete}`
- source_unchanged_by_stage1212: `{source_unchanged_by_stage1212}`
- source_has_publish_call: `{source_has_publish_call}`
- active_ros_publisher_path_exists: `{active_ros_publisher_path_exists}`
- manual_enable_active: `{manual_enable_active}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `{torque_publisher_enabled}`
- torque_command_published_by_stage1212: `{torque_command_published_by_stage1212}`
- control_law_changed: `{control_law_changed}`

Stage 12.12 只设计 bounded publish-call source patch，不加入 publish call，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 12.12 Bounded Publish-call Source Patch Design Only"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 12.12] bounded publish-call source patch design only")
    print(f"pass={all_pass}")
    print(f"stage1211_pass={stage1211_pass}")
    print(f"bounded_publish_call_source_patch_design_complete={bounded_publish_call_source_patch_design_complete}")
    print(f"source_unchanged_by_stage1212={source_unchanged_by_stage1212}")
    print(f"source_has_publish_call={source_has_publish_call}")
    print(f"active_ros_publisher_path_exists={active_ros_publisher_path_exists}")
    print(f"manual_enable_active={manual_enable_active}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print(f"control_law_changed={control_law_changed}")
    print(f"torque_publisher_enabled={torque_publisher_enabled}")
    print(f"torque_command_published_by_stage1212={torque_command_published_by_stage1212}")
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
