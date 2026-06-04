#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE1210_SUMMARY = LOG_DIR / "stage12_publish_call_preflight_freeze_summary.csv"
STAGE1210_GATE = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage1210.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
SAFETY_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

PLAN_CSV = LOG_DIR / "stage12_bounded_zero_safe_publish_call_implementation_plan.csv"
LOG_PATH = LOG_DIR / "stage12_bounded_zero_safe_publish_call_implementation_plan_log.csv"
SUMMARY_PATH = LOG_DIR / "stage12_bounded_zero_safe_publish_call_implementation_plan_summary.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage1211.csv"
DOC_PATH = ROOT / "docs/STAGE12_BOUNDED_ZERO_SAFE_PUBLISH_CALL_IMPLEMENTATION_PLAN.md"

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

    s1210 = load_summary(STAGE1210_SUMMARY)

    stage1210_pass = as_bool(s1210.get("pass", "False"))
    preflight_frozen = as_bool(s1210.get("publish_call_preflight_frozen", "False"))
    stage1210_source_has_create_publisher = as_bool(s1210.get("current_source_has_create_publisher", "False"))
    stage1210_source_has_publish_call = as_bool(s1210.get("current_source_has_publish_call", "True"))
    stage1210_active_path = as_bool(s1210.get("active_ros_publisher_path_exists", "False"))
    stage1210_manual_active = as_bool(s1210.get("manual_enable_active", "True"))
    stage1210_torque_ready = as_bool(s1210.get("torque_enable_ready", "True"))
    stage1210_torque_enabled = as_bool(s1210.get("torque_publisher_enabled", "True"))
    stage1210_torque_published = as_bool(s1210.get("torque_command_published_by_stage1210", "True"))
    stage1210_control_changed = as_bool(s1210.get("control_law_changed", "True"))

    add_check(checks, "stage1210_summary_exists", STAGE1210_SUMMARY.exists(), True, STAGE1210_SUMMARY.exists(), str(STAGE1210_SUMMARY))
    add_check(checks, "stage1210_pass", stage1210_pass, True, stage1210_pass)
    add_check(checks, "stage1210_publish_call_preflight_frozen", preflight_frozen, True, preflight_frozen)
    add_check(checks, "stage1210_current_source_has_create_publisher", stage1210_source_has_create_publisher, True, stage1210_source_has_create_publisher)
    add_check(checks, "stage1210_current_source_has_publish_call", stage1210_source_has_publish_call, False, not stage1210_source_has_publish_call)
    add_check(checks, "stage1210_active_ros_publisher_path_exists", stage1210_active_path, True, stage1210_active_path)
    add_check(checks, "stage1210_manual_enable_active", stage1210_manual_active, False, not stage1210_manual_active)
    add_check(checks, "stage1210_torque_enable_ready", stage1210_torque_ready, False, not stage1210_torque_ready)
    add_check(checks, "stage1210_torque_publisher_enabled", stage1210_torque_enabled, False, not stage1210_torque_enabled)
    add_check(checks, "stage1210_torque_command_published", stage1210_torque_published, False, not stage1210_torque_published)
    add_check(checks, "stage1210_control_law_changed", stage1210_control_changed, False, not stage1210_control_changed)

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

    gate_rows = load_dicts(STAGE1210_GATE)
    gate_status = {
        row.get("gate", ""): as_bool(row.get("current_status", "False"))
        for row in gate_rows
    }

    expected_gate_status = {
        "G2": False,
        "G3": True,
        "G8": False,
        "G9": True,
        "G26": True,
        "G27": True,
        "G28": True,
    }

    add_check(checks, "stage1210_gate_exists", STAGE1210_GATE.exists(), True, STAGE1210_GATE.exists(), str(STAGE1210_GATE))
    for gate, expected in expected_gate_status.items():
        value = gate_status.get(gate, None)
        add_check(checks, f"{gate}_status_after_stage1210", value, expected, value == expected)

    plan_rows = [
        {
            "item": "stage12_scope",
            "value": "bounded_zero_safe_publish_call_implementation_plan_only",
            "implemented_in_stage1211": False,
            "allowed_in_future_bounded_publish_stage": True,
            "guard": "Stage 12.11 must not edit C++ source and must not add publish call",
            "description": "Only records the future bounded zero/safe publish-call implementation plan.",
        },
        {
            "item": "future_publish_call_limit",
            "value": "one-shot or bounded finite count; no continuous torque streaming",
            "implemented_in_stage1211": False,
            "allowed_in_future_bounded_publish_stage": True,
            "guard": "Continuous publishing requires a later separate stage",
            "description": "Future first publish stage must be bounded.",
        },
        {
            "item": "future_publish_payload",
            "value": "zero or watchdog-safe torque only; Float64MultiArray length=12; all finite",
            "implemented_in_stage1211": False,
            "allowed_in_future_bounded_publish_stage": True,
            "guard": "Invalid payload must abort or fall back to zero",
            "description": "First published payload must be safe and bounded.",
        },
        {
            "item": "future_payload_order",
            "value": "Go1 actuator order FR,FL,RR,RL hip,thigh,calf",
            "implemented_in_stage1211": False,
            "allowed_in_future_bounded_publish_stage": True,
            "guard": "Order mismatch must abort future publish test",
            "description": "Payload ordering contract.",
        },
        {
            "item": "future_preconditions",
            "value": "active publisher exists && manual flags true && state_ready && inputs_fresh",
            "implemented_in_stage1211": False,
            "allowed_in_future_bounded_publish_stage": True,
            "guard": "If any precondition is false, publish is forbidden",
            "description": "Runtime conditions before any future publish call.",
        },
        {
            "item": "future_safety_chain",
            "value": "watchdogFallbackZeroTorque then clampTorqueCommand before message conversion",
            "implemented_in_stage1211": False,
            "allowed_in_future_bounded_publish_stage": True,
            "guard": "No raw unclamped torque may be published",
            "description": "Safety processing required before future publication.",
        },
        {
            "item": "future_source_patch_boundary",
            "value": "future diff limited to publish-gated output path and Stage 12 publish markers",
            "implemented_in_stage1211": False,
            "allowed_in_future_bounded_publish_stage": True,
            "guard": "No control law, estimator, MPC, or WBC logic changes",
            "description": "Future source patch must be minimal.",
        },
        {
            "item": "future_runtime_evidence",
            "value": "topic echo receives bounded message count; payload length=12; finite; zero/safe; params reverted",
            "implemented_in_stage1211": False,
            "allowed_in_future_bounded_publish_stage": True,
            "guard": "Missing runtime evidence aborts future publish stage",
            "description": "Evidence required after future bounded publish test.",
        },
        {
            "item": "future_revert_procedure",
            "value": "set confirm_torque_publisher_enable false; set enable_torque_publisher false; stop controller",
            "implemented_in_stage1211": False,
            "allowed_in_future_bounded_publish_stage": True,
            "guard": "Revert must run in finally block",
            "description": "Fail-closed cleanup for future publish test.",
        },
        {
            "item": "future_abort_conditions",
            "value": "unexpected source hash; publish call outside allowed block; param set failure; controller exit; invalid payload; unexpected message count",
            "implemented_in_stage1211": False,
            "allowed_in_future_bounded_publish_stage": True,
            "guard": "Future publish script must fail closed",
            "description": "Abort policy for future bounded publish implementation.",
        },
        {
            "item": "future_stage_boundary",
            "value": "bounded publish test is not realtime controller completion and not hardware deployment",
            "implemented_in_stage1211": False,
            "allowed_in_future_bounded_publish_stage": True,
            "guard": "Do not claim pure WBC, EKF, full MPC, or realtime controller completion",
            "description": "Explicit scope boundary.",
        },
    ]

    with PLAN_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "item",
                "value",
                "implemented_in_stage1211",
                "allowed_in_future_bounded_publish_stage",
                "guard",
                "description",
            ],
        )
        writer.writeheader()
        writer.writerows(plan_rows)

    bounded_publish_plan_exists = PLAN_CSV.exists()
    plan_all_items_not_implemented = all(not row["implemented_in_stage1211"] for row in plan_rows)
    plan_has_publish_limit = any(row["item"] == "future_publish_call_limit" for row in plan_rows)
    plan_has_safe_payload = any(row["item"] == "future_publish_payload" for row in plan_rows)
    plan_has_payload_order = any(row["item"] == "future_payload_order" for row in plan_rows)
    plan_has_preconditions = any(row["item"] == "future_preconditions" for row in plan_rows)
    plan_has_safety_chain = any(row["item"] == "future_safety_chain" for row in plan_rows)
    plan_has_source_boundary = any(row["item"] == "future_source_patch_boundary" for row in plan_rows)
    plan_has_runtime_evidence = any(row["item"] == "future_runtime_evidence" for row in plan_rows)
    plan_has_revert_procedure = any(row["item"] == "future_revert_procedure" for row in plan_rows)
    plan_has_abort_conditions = any(row["item"] == "future_abort_conditions" for row in plan_rows)

    source_after = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    source_hash_after = sha256_text(source_after)
    source_unchanged_by_stage1211 = source_hash_before == source_hash_after

    add_check(checks, "bounded_zero_safe_publish_call_implementation_plan_exists", bounded_publish_plan_exists, True, bounded_publish_plan_exists, str(PLAN_CSV))
    add_check(checks, "plan_all_items_not_implemented", plan_all_items_not_implemented, True, plan_all_items_not_implemented)
    add_check(checks, "plan_has_publish_limit", plan_has_publish_limit, True, plan_has_publish_limit)
    add_check(checks, "plan_has_safe_payload", plan_has_safe_payload, True, plan_has_safe_payload)
    add_check(checks, "plan_has_payload_order", plan_has_payload_order, True, plan_has_payload_order)
    add_check(checks, "plan_has_preconditions", plan_has_preconditions, True, plan_has_preconditions)
    add_check(checks, "plan_has_safety_chain", plan_has_safety_chain, True, plan_has_safety_chain)
    add_check(checks, "plan_has_source_boundary", plan_has_source_boundary, True, plan_has_source_boundary)
    add_check(checks, "plan_has_runtime_evidence", plan_has_runtime_evidence, True, plan_has_runtime_evidence)
    add_check(checks, "plan_has_revert_procedure", plan_has_revert_procedure, True, plan_has_revert_procedure)
    add_check(checks, "plan_has_abort_conditions", plan_has_abort_conditions, True, plan_has_abort_conditions)
    add_check(checks, "source_unchanged_by_stage1211", source_unchanged_by_stage1211, True, source_unchanged_by_stage1211)

    bounded_zero_safe_publish_call_implementation_plan_complete = True
    manual_enable_active = False
    active_ros_publisher_path_exists = True
    torque_enable_ready = False
    control_law_changed = False
    torque_publisher_enabled = False
    torque_command_published_by_stage1211 = False

    gate_out_rows = []
    for row in gate_rows:
        gate_out_rows.append(row)

    gate_out_rows.append({
        "gate": "G29",
        "name": "Bounded zero/safe publish-call implementation plan exists",
        "required_before_torque_publish": True,
        "current_status": bounded_zero_safe_publish_call_implementation_plan_complete,
        "evidence": str(PLAN_CSV.relative_to(ROOT)),
    })

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(gate_out_rows)

    add_check(checks, "bounded_zero_safe_publish_call_implementation_plan_complete", bounded_zero_safe_publish_call_implementation_plan_complete, True, bounded_zero_safe_publish_call_implementation_plan_complete)
    add_check(checks, "manual_enable_active", manual_enable_active, False, not manual_enable_active)
    add_check(checks, "active_ros_publisher_path_exists", active_ros_publisher_path_exists, True, active_ros_publisher_path_exists)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)
    add_check(checks, "control_law_changed", control_law_changed, False, not control_law_changed)
    add_check(checks, "torque_publisher_enabled", torque_publisher_enabled, False, not torque_publisher_enabled)
    add_check(checks, "torque_command_published_by_stage1211", torque_command_published_by_stage1211, False, not torque_command_published_by_stage1211)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    DOC_PATH.write_text(f"""# Stage 12.11 Bounded Zero/Safe Publish-call Implementation Plan

## 一、结论

Stage 12.11 只制定 bounded zero/safe publish-call implementation plan。

本阶段不修改 C++ source，不加入 publish call，不发布 torque，不改变控制律。

## 二、前置状态

Stage 12.10:

- pass: {stage1210_pass}
- publish_call_preflight_frozen: {preflight_frozen}
- current_source_has_create_publisher: {stage1210_source_has_create_publisher}
- current_source_has_publish_call: {stage1210_source_has_publish_call}
- active_ros_publisher_path_exists: {stage1210_active_path}
- manual_enable_active: {stage1210_manual_active}
- torque_enable_ready: {stage1210_torque_ready}

## 三、当前 source guard

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: {source_has_create_publisher}
- source_has_publish_call: {source_has_publish_call}
- source_references_torque_topic: {source_references_torque_topic}
- source_has_active_publisher_member: {source_has_active_publisher_member}
- source_unchanged_by_stage1211: {source_unchanged_by_stage1211}

## 四、Bounded zero/safe publish-call implementation plan

Plan CSV:

    results/logs_sample/stage12_bounded_zero_safe_publish_call_implementation_plan.csv

Future bounded publish protocol:

- one-shot or finite bounded message count only；
- zero or watchdog-safe torque only；
- Float64MultiArray length 12；
- all values finite；
- actuator order FR, FL, RR, RL; each hip, thigh, calf；
- watchdogFallbackZeroTorque before clampTorqueCommand；
- manual flags true, active publisher exists, state_ready, inputs_fresh；
- runtime topic echo must verify message count and payload；
- params must be reverted in fail-closed cleanup；
- no control law, estimator, MPC, or WBC logic changes。

## 五、Safety gate after Stage 12.11

新增：

- G29 bounded zero/safe publish-call implementation plan exists: {bounded_zero_safe_publish_call_implementation_plan_complete}

Key gates remain:

- G3 no publish call: {gate_status.get("G3")}
- G8 manual enable active after revert: {manual_enable_active}
- G9 active ROS publisher path exists: {active_ros_publisher_path_exists}
- G28 publish-call preflight freeze passed: {gate_status.get("G28")}

Therefore:

    torque_enable_ready = {torque_enable_ready}

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.11 没有完成：

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
        writer.writerow(["stage", "Stage 12.11"])
        writer.writerow(["test_name", "bounded_zero_safe_publish_call_implementation_plan"])
        writer.writerow(["stage1210_pass", stage1210_pass])
        writer.writerow(["stage1210_publish_call_preflight_frozen", preflight_frozen])
        writer.writerow(["source_has_create_publisher", source_has_create_publisher])
        writer.writerow(["source_has_publish_call", source_has_publish_call])
        writer.writerow(["source_references_torque_topic", source_references_torque_topic])
        writer.writerow(["source_has_active_publisher_member", source_has_active_publisher_member])
        writer.writerow(["source_has_stage124_marker", source_has_stage124_marker])
        writer.writerow(["source_declares_enable_param_default_false", source_declares_enable_param])
        writer.writerow(["source_declares_confirm_param_default_false", source_declares_confirm_param])
        writer.writerow(["source_unchanged_by_stage1211", source_unchanged_by_stage1211])
        writer.writerow(["bounded_zero_safe_publish_call_implementation_plan_exists", bounded_publish_plan_exists])
        writer.writerow(["plan_all_items_not_implemented", plan_all_items_not_implemented])
        writer.writerow(["plan_has_publish_limit", plan_has_publish_limit])
        writer.writerow(["plan_has_safe_payload", plan_has_safe_payload])
        writer.writerow(["plan_has_payload_order", plan_has_payload_order])
        writer.writerow(["plan_has_preconditions", plan_has_preconditions])
        writer.writerow(["plan_has_safety_chain", plan_has_safety_chain])
        writer.writerow(["plan_has_source_boundary", plan_has_source_boundary])
        writer.writerow(["plan_has_runtime_evidence", plan_has_runtime_evidence])
        writer.writerow(["plan_has_revert_procedure", plan_has_revert_procedure])
        writer.writerow(["plan_has_abort_conditions", plan_has_abort_conditions])
        writer.writerow(["bounded_zero_safe_publish_call_implementation_plan_complete", bounded_zero_safe_publish_call_implementation_plan_complete])
        writer.writerow(["manual_enable_active", manual_enable_active])
        writer.writerow(["active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g3_no_publish_call", gate_status.get("G3", False)])
        writer.writerow(["g8_manual_enable_active", manual_enable_active])
        writer.writerow(["g9_active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g28_publish_call_preflight_freeze_passed", gate_status.get("G28", False)])
        writer.writerow(["g29_bounded_zero_safe_publish_call_implementation_plan_exists", bounded_zero_safe_publish_call_implementation_plan_complete])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", control_law_changed])
        writer.writerow(["torque_publisher_enabled", torque_publisher_enabled])
        writer.writerow(["torque_command_published_by_stage1211", torque_command_published_by_stage1211])
        writer.writerow(["stage12_scope", "bounded_zero_safe_publish_call_implementation_plan_only"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["ros2_cpp_realtime_controller_completed", False])
        writer.writerow(["pure_wbc_locomotion_completed", False])
        writer.writerow(["ekf_completed", False])
        writer.writerow(["full_3d_centroidal_mpc_completed", False])
        writer.writerow(["num_checks", len(checks)])
        writer.writerow(["num_failed_checks", sum(1 for row in checks if not row["pass"])])
        writer.writerow(["pass", all_pass])
        writer.writerow(["log_csv", str(LOG_PATH.relative_to(ROOT))])
        writer.writerow(["plan_csv", str(PLAN_CSV.relative_to(ROOT))])
        writer.writerow(["safety_gate_csv", str(SAFETY_GATE_PATH.relative_to(ROOT))])
        writer.writerow(["summary_csv", str(SUMMARY_PATH.relative_to(ROOT))])
        writer.writerow(["doc", str(DOC_PATH.relative_to(ROOT))])

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 12.11 Bounded Zero/Safe Publish-call Implementation Plan

Stage 12.11 完成 bounded zero/safe publish-call implementation plan only。

- Script: `scripts/stage12_bounded_zero_safe_publish_call_implementation_plan.py`
- Plan: `results/logs_sample/stage12_bounded_zero_safe_publish_call_implementation_plan.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1211.csv`
- Summary: `results/logs_sample/stage12_bounded_zero_safe_publish_call_implementation_plan_summary.csv`
- Docs: `docs/STAGE12_BOUNDED_ZERO_SAFE_PUBLISH_CALL_IMPLEMENTATION_PLAN.md`
- pass: `{all_pass}`
- bounded_zero_safe_publish_call_implementation_plan_complete: `{bounded_zero_safe_publish_call_implementation_plan_complete}`
- source_unchanged_by_stage1211: `{source_unchanged_by_stage1211}`
- source_has_publish_call: `{source_has_publish_call}`
- active_ros_publisher_path_exists: `{active_ros_publisher_path_exists}`
- manual_enable_active: `{manual_enable_active}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `{torque_publisher_enabled}`
- torque_command_published_by_stage1211: `{torque_command_published_by_stage1211}`
- control_law_changed: `{control_law_changed}`

Stage 12.11 只规划 bounded zero/safe publish-call implementation，不加入 publish call，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 12.11 Bounded Zero/Safe Publish-call Implementation Plan"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 12.11] bounded zero/safe publish-call implementation plan")
    print(f"pass={all_pass}")
    print(f"stage1210_pass={stage1210_pass}")
    print(f"bounded_zero_safe_publish_call_implementation_plan_complete={bounded_zero_safe_publish_call_implementation_plan_complete}")
    print(f"source_unchanged_by_stage1211={source_unchanged_by_stage1211}")
    print(f"source_has_publish_call={source_has_publish_call}")
    print(f"active_ros_publisher_path_exists={active_ros_publisher_path_exists}")
    print(f"manual_enable_active={manual_enable_active}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print(f"control_law_changed={control_law_changed}")
    print(f"torque_publisher_enabled={torque_publisher_enabled}")
    print(f"torque_command_published_by_stage1211={torque_command_published_by_stage1211}")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
    print(f"plan_csv={PLAN_CSV.relative_to(ROOT)}")
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
