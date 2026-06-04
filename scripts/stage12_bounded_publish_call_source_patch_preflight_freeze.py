#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE1211_SUMMARY = LOG_DIR / "stage12_bounded_zero_safe_publish_call_implementation_plan_summary.csv"
STAGE1212_SUMMARY = LOG_DIR / "stage12_bounded_publish_call_source_patch_design_summary.csv"
STAGE1212_GATE = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage1212.csv"

STAGE1211_PLAN = LOG_DIR / "stage12_bounded_zero_safe_publish_call_implementation_plan.csv"
STAGE1212_DESIGN = LOG_DIR / "stage12_bounded_publish_call_source_patch_design.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
SAFETY_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

DOC_PATH = ROOT / "docs/STAGE12_BOUNDED_PUBLISH_CALL_SOURCE_PATCH_PREFLIGHT_FREEZE.md"
SUMMARY_PATH = LOG_DIR / "stage12_bounded_publish_call_source_patch_preflight_freeze_summary.csv"
LOG_PATH = LOG_DIR / "stage12_bounded_publish_call_source_patch_preflight_freeze_log.csv"
HASH_PATH = LOG_DIR / "stage12_bounded_publish_call_source_patch_preflight_freeze_hashes.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage1213.csv"

TORQUE_TOPIC = "/go1/joint_torque_cmd"

FREEZE_FILES = [
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp",

    "docs/STAGE12_BOUNDED_ZERO_SAFE_PUBLISH_CALL_IMPLEMENTATION_PLAN.md",
    "docs/STAGE12_BOUNDED_PUBLISH_CALL_SOURCE_PATCH_DESIGN_ONLY.md",

    "results/logs_sample/stage12_bounded_zero_safe_publish_call_implementation_plan.csv",
    "results/logs_sample/stage12_bounded_publish_call_source_patch_design.csv",

    "results/logs_sample/stage12_bounded_zero_safe_publish_call_implementation_plan_summary.csv",
    "results/logs_sample/stage12_bounded_publish_call_source_patch_design_summary.csv",

    "results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1211.csv",
    "results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1212.csv",
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

    s1211 = load_summary(STAGE1211_SUMMARY)
    s1212 = load_summary(STAGE1212_SUMMARY)

    stage1211_pass = as_bool(s1211.get("pass", "False"))
    stage1211_plan_complete = as_bool(s1211.get("bounded_zero_safe_publish_call_implementation_plan_complete", "False"))

    stage1212_pass = as_bool(s1212.get("pass", "False"))
    stage1212_design_complete = as_bool(s1212.get("bounded_publish_call_source_patch_design_complete", "False"))
    stage1212_source_unchanged = as_bool(s1212.get("source_unchanged_by_stage1212", "False"))
    stage1212_source_has_publish_call = as_bool(s1212.get("source_has_publish_call", "True"))
    stage1212_active_path = as_bool(s1212.get("active_ros_publisher_path_exists", "False"))
    stage1212_manual_active = as_bool(s1212.get("manual_enable_active", "True"))
    stage1212_torque_ready = as_bool(s1212.get("torque_enable_ready", "True"))
    stage1212_torque_enabled = as_bool(s1212.get("torque_publisher_enabled", "True"))
    stage1212_torque_published = as_bool(s1212.get("torque_command_published_by_stage1212", "True"))
    stage1212_control_changed = as_bool(s1212.get("control_law_changed", "True"))

    add_check(checks, "stage1211_summary_exists", STAGE1211_SUMMARY.exists(), True, STAGE1211_SUMMARY.exists(), str(STAGE1211_SUMMARY))
    add_check(checks, "stage1211_pass", stage1211_pass, True, stage1211_pass)
    add_check(checks, "stage1211_plan_complete", stage1211_plan_complete, True, stage1211_plan_complete)

    add_check(checks, "stage1212_summary_exists", STAGE1212_SUMMARY.exists(), True, STAGE1212_SUMMARY.exists(), str(STAGE1212_SUMMARY))
    add_check(checks, "stage1212_pass", stage1212_pass, True, stage1212_pass)
    add_check(checks, "stage1212_design_complete", stage1212_design_complete, True, stage1212_design_complete)
    add_check(checks, "stage1212_source_unchanged", stage1212_source_unchanged, True, stage1212_source_unchanged)
    add_check(checks, "stage1212_source_has_publish_call", stage1212_source_has_publish_call, False, not stage1212_source_has_publish_call)
    add_check(checks, "stage1212_active_ros_publisher_path_exists", stage1212_active_path, True, stage1212_active_path)
    add_check(checks, "stage1212_manual_enable_active", stage1212_manual_active, False, not stage1212_manual_active)
    add_check(checks, "stage1212_torque_enable_ready", stage1212_torque_ready, False, not stage1212_torque_ready)
    add_check(checks, "stage1212_torque_publisher_enabled", stage1212_torque_enabled, False, not stage1212_torque_enabled)
    add_check(checks, "stage1212_torque_command_published", stage1212_torque_published, False, not stage1212_torque_published)
    add_check(checks, "stage1212_control_law_changed", stage1212_control_changed, False, not stage1212_control_changed)

    plan_rows = load_dicts(STAGE1211_PLAN)
    design_rows = load_dicts(STAGE1212_DESIGN)

    plan_all_not_implemented = all(not as_bool(row.get("implemented_in_stage1211", "True")) for row in plan_rows)
    plan_has_publish_limit = any(row.get("item") == "future_publish_call_limit" for row in plan_rows)
    plan_has_safe_payload = any(row.get("item") == "future_publish_payload" for row in plan_rows)
    plan_has_safety_chain = any(row.get("item") == "future_safety_chain" for row in plan_rows)
    plan_has_abort_conditions = any(row.get("item") == "future_abort_conditions" for row in plan_rows)

    design_all_not_applied = all(not as_bool(row.get("applied_in_stage1212", "True")) for row in design_rows)
    design_has_publish_helper = any(row.get("item") == "future_publish_helper" for row in design_rows)
    design_has_message_helper = any(row.get("item") == "future_message_helper" for row in design_rows)
    design_has_publish_call_site = any(row.get("item") == "future_publish_call_site" for row in design_rows)
    design_has_precondition_gate = any(row.get("item") == "future_precondition_gate" for row in design_rows)
    design_has_safety_chain = any(row.get("item") == "future_safety_chain" for row in design_rows)
    design_has_payload_contract = any(row.get("item") == "future_payload_contract" for row in design_rows)
    design_has_publish_count_limit = any(row.get("item") == "future_publish_count_limit" for row in design_rows)
    design_forbids_timer_loop = any(row.get("item") == "future_no_timer_loop_rule" for row in design_rows)
    design_forbids_control_law_change = any(row.get("item") == "future_no_control_law_change_rule" for row in design_rows)
    design_has_runtime_evidence = any(row.get("item") == "future_runtime_evidence" for row in design_rows)
    design_has_revert_procedure = any(row.get("item") == "future_revert_procedure" for row in design_rows)
    design_has_abort_conditions = any(row.get("item") == "future_abort_conditions" for row in design_rows)

    add_check(checks, "stage1211_plan_csv_exists", STAGE1211_PLAN.exists(), True, STAGE1211_PLAN.exists(), str(STAGE1211_PLAN))
    add_check(checks, "stage1211_plan_all_not_implemented", plan_all_not_implemented, True, plan_all_not_implemented)
    add_check(checks, "stage1211_plan_has_publish_limit", plan_has_publish_limit, True, plan_has_publish_limit)
    add_check(checks, "stage1211_plan_has_safe_payload", plan_has_safe_payload, True, plan_has_safe_payload)
    add_check(checks, "stage1211_plan_has_safety_chain", plan_has_safety_chain, True, plan_has_safety_chain)
    add_check(checks, "stage1211_plan_has_abort_conditions", plan_has_abort_conditions, True, plan_has_abort_conditions)

    add_check(checks, "stage1212_design_csv_exists", STAGE1212_DESIGN.exists(), True, STAGE1212_DESIGN.exists(), str(STAGE1212_DESIGN))
    add_check(checks, "stage1212_design_all_not_applied", design_all_not_applied, True, design_all_not_applied)
    add_check(checks, "stage1212_design_has_publish_helper", design_has_publish_helper, True, design_has_publish_helper)
    add_check(checks, "stage1212_design_has_message_helper", design_has_message_helper, True, design_has_message_helper)
    add_check(checks, "stage1212_design_has_publish_call_site", design_has_publish_call_site, True, design_has_publish_call_site)
    add_check(checks, "stage1212_design_has_precondition_gate", design_has_precondition_gate, True, design_has_precondition_gate)
    add_check(checks, "stage1212_design_has_safety_chain", design_has_safety_chain, True, design_has_safety_chain)
    add_check(checks, "stage1212_design_has_payload_contract", design_has_payload_contract, True, design_has_payload_contract)
    add_check(checks, "stage1212_design_has_publish_count_limit", design_has_publish_count_limit, True, design_has_publish_count_limit)
    add_check(checks, "stage1212_design_forbids_timer_loop", design_forbids_timer_loop, True, design_forbids_timer_loop)
    add_check(checks, "stage1212_design_forbids_control_law_change", design_forbids_control_law_change, True, design_forbids_control_law_change)
    add_check(checks, "stage1212_design_has_runtime_evidence", design_has_runtime_evidence, True, design_has_runtime_evidence)
    add_check(checks, "stage1212_design_has_revert_procedure", design_has_revert_procedure, True, design_has_revert_procedure)
    add_check(checks, "stage1212_design_has_abort_conditions", design_has_abort_conditions, True, design_has_abort_conditions)

    cpp_text = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    safety_text = SAFETY_HEADER.read_text(errors="replace") if SAFETY_HEADER.exists() else ""
    zero_text = ZERO_HEADER.read_text(errors="replace") if ZERO_HEADER.exists() else ""

    current_source_has_create_publisher = "create_publisher<std_msgs::msg::Float64MultiArray>" in cpp_text
    current_source_has_publish_call = ".publish(" in cpp_text or "->publish(" in cpp_text
    current_source_references_torque_topic = TORQUE_TOPIC in cpp_text
    current_source_has_active_member = "active_torque_cmd_publisher_" in cpp_text
    current_source_has_stage124_marker = (
        "kStage124PublisherConstructionImplemented" in cpp_text and
        "kStage124PublishCallImplemented = false" in cpp_text
    )
    source_declares_enable_param = 'declare_parameter<bool>("enable_torque_publisher", false)' in cpp_text
    source_declares_confirm_param = 'declare_parameter<bool>("confirm_torque_publisher_enable", false)' in cpp_text
    source_uses_safety = "clampTorqueCommand" in cpp_text and "allInputsFresh" in cpp_text and "watchdogFallbackZeroTorque" in cpp_text
    safety_header_has_clamp_watchdog = "clampTorqueCommand" in safety_text and "allInputsFresh" in safety_text and "watchdogFallbackZeroTorque" in safety_text
    zero_header_declares_12 = "kGo1NumActuatedJoints = 12" in zero_text

    add_check(checks, "cpp_source_exists", CPP_SOURCE.exists(), True, CPP_SOURCE.exists(), str(CPP_SOURCE))
    add_check(checks, "current_source_has_create_publisher", current_source_has_create_publisher, True, current_source_has_create_publisher)
    add_check(checks, "current_source_has_no_publish_call", current_source_has_publish_call, False, not current_source_has_publish_call)
    add_check(checks, "current_source_references_torque_topic", current_source_references_torque_topic, True, current_source_references_torque_topic)
    add_check(checks, "current_source_has_active_publisher_member", current_source_has_active_member, True, current_source_has_active_member)
    add_check(checks, "current_source_has_stage124_marker", current_source_has_stage124_marker, True, current_source_has_stage124_marker)
    add_check(checks, "source_declares_enable_param_default_false", source_declares_enable_param, True, source_declares_enable_param)
    add_check(checks, "source_declares_confirm_param_default_false", source_declares_confirm_param, True, source_declares_confirm_param)
    add_check(checks, "source_uses_safety_utilities", source_uses_safety, True, source_uses_safety)
    add_check(checks, "safety_header_has_clamp_watchdog", safety_header_has_clamp_watchdog, True, safety_header_has_clamp_watchdog)
    add_check(checks, "zero_header_declares_12", zero_header_declares_12, True, zero_header_declares_12)

    gate_rows = load_dicts(STAGE1212_GATE)
    gate_status = {row.get("gate", ""): as_bool(row.get("current_status", "False")) for row in gate_rows}

    expected_gate_status = {
        "G2": False,
        "G3": True,
        "G8": False,
        "G9": True,
        "G28": True,
        "G29": True,
        "G30": True,
    }

    add_check(checks, "stage1212_gate_exists", STAGE1212_GATE.exists(), True, STAGE1212_GATE.exists(), str(STAGE1212_GATE))
    for gate, expected in expected_gate_status.items():
        value = gate_status.get(gate, None)
        add_check(checks, f"{gate}_status_after_stage1212", value, expected, value == expected)

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

    manual_enable_active = False
    active_ros_publisher_path_exists = gate_status.get("G9", False)
    bounded_publish_call_source_patch_preflight_frozen = (
        stage1211_pass and
        stage1211_plan_complete and
        stage1212_pass and
        stage1212_design_complete and
        stage1212_source_unchanged and
        current_source_has_create_publisher and
        not current_source_has_publish_call and
        current_source_references_torque_topic and
        current_source_has_active_member and
        current_source_has_stage124_marker and
        design_all_not_applied and
        design_has_publish_helper and
        design_has_message_helper and
        design_has_publish_call_site and
        design_has_precondition_gate and
        design_has_safety_chain and
        design_has_payload_contract and
        design_has_publish_count_limit and
        design_forbids_timer_loop and
        design_forbids_control_law_change and
        design_has_runtime_evidence and
        design_has_revert_procedure and
        design_has_abort_conditions and
        active_ros_publisher_path_exists and
        not manual_enable_active and
        gate_status.get("G30", False) and
        len(missing_files) == 0
    )

    torque_enable_ready = False
    control_law_changed = False
    torque_publisher_enabled = False
    torque_command_published_by_stage1213 = False

    gate_out_rows = []
    for row in gate_rows:
        gate_out_rows.append(row)

    gate_out_rows.append({
        "gate": "G31",
        "name": "Bounded publish-call source patch preflight freeze passed",
        "required_before_torque_publish": True,
        "current_status": bounded_publish_call_source_patch_preflight_frozen,
        "evidence": str(LOG_PATH.relative_to(ROOT)),
    })

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(gate_out_rows)

    add_check(checks, "bounded_publish_call_source_patch_preflight_frozen", bounded_publish_call_source_patch_preflight_frozen, True, bounded_publish_call_source_patch_preflight_frozen)
    add_check(checks, "manual_enable_active", manual_enable_active, False, not manual_enable_active)
    add_check(checks, "active_ros_publisher_path_exists", active_ros_publisher_path_exists, True, active_ros_publisher_path_exists)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)
    add_check(checks, "control_law_changed", control_law_changed, False, not control_law_changed)
    add_check(checks, "torque_publisher_enabled", torque_publisher_enabled, False, not torque_publisher_enabled)
    add_check(checks, "torque_command_published_by_stage1213", torque_command_published_by_stage1213, False, not torque_command_published_by_stage1213)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    DOC_PATH.write_text(f"""# Stage 12.13 Bounded Publish-call Source Patch Preflight Freeze

## 一、冻结结论

Stage 12.13 冻结 bounded publish-call source patch preflight baseline。

本阶段不修改 C++ source，不加入 publish call，不发布 torque，不改变控制律。

## 二、前置状态

- Stage 12.11 pass: {stage1211_pass}
- Stage 12.11 plan complete: {stage1211_plan_complete}
- Stage 12.12 pass: {stage1212_pass}
- Stage 12.12 design complete: {stage1212_design_complete}
- Stage 12.12 source unchanged: {stage1212_source_unchanged}

## 三、Source integrity

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- current_source_has_create_publisher: {current_source_has_create_publisher}
- current_source_has_publish_call: {current_source_has_publish_call}
- current_source_references_torque_topic: {current_source_references_torque_topic}
- current_source_has_active_publisher_member: {current_source_has_active_member}
- current_source_has_stage124_marker: {current_source_has_stage124_marker}

## 四、Design integrity

Design CSV:

    results/logs_sample/stage12_bounded_publish_call_source_patch_design.csv

Checks:

- design_all_not_applied: {design_all_not_applied}
- design_has_publish_helper: {design_has_publish_helper}
- design_has_message_helper: {design_has_message_helper}
- design_has_publish_call_site: {design_has_publish_call_site}
- design_has_precondition_gate: {design_has_precondition_gate}
- design_has_safety_chain: {design_has_safety_chain}
- design_has_payload_contract: {design_has_payload_contract}
- design_has_publish_count_limit: {design_has_publish_count_limit}
- design_forbids_timer_loop: {design_forbids_timer_loop}
- design_forbids_control_law_change: {design_forbids_control_law_change}
- design_has_runtime_evidence: {design_has_runtime_evidence}
- design_has_revert_procedure: {design_has_revert_procedure}
- design_has_abort_conditions: {design_has_abort_conditions}

## 五、Safety gate after Stage 12.13

新增：

- G31 bounded publish-call source patch preflight freeze passed: {bounded_publish_call_source_patch_preflight_frozen}

Key gates:

- G3 no publish call: {gate_status.get("G3")}
- G8 manual enable active: {manual_enable_active}
- G9 active ROS publisher path exists: {active_ros_publisher_path_exists}
- G30 bounded publish-call source patch design exists: {gate_status.get("G30")}

Therefore:

    torque_enable_ready = {torque_enable_ready}

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.13 没有完成：

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
        writer.writerow(["stage", "Stage 12.13"])
        writer.writerow(["test_name", "bounded_publish_call_source_patch_preflight_freeze"])
        writer.writerow(["stage1211_pass", stage1211_pass])
        writer.writerow(["stage1211_bounded_zero_safe_publish_call_implementation_plan_complete", stage1211_plan_complete])
        writer.writerow(["stage1212_pass", stage1212_pass])
        writer.writerow(["stage1212_bounded_publish_call_source_patch_design_complete", stage1212_design_complete])
        writer.writerow(["stage1212_source_unchanged_by_stage1212", stage1212_source_unchanged])
        writer.writerow(["freeze_file_count", len(FREEZE_FILES)])
        writer.writerow(["missing_file_count", len(missing_files)])
        writer.writerow(["current_source_has_create_publisher", current_source_has_create_publisher])
        writer.writerow(["current_source_has_publish_call", current_source_has_publish_call])
        writer.writerow(["current_source_references_torque_topic", current_source_references_torque_topic])
        writer.writerow(["current_source_has_active_publisher_member", current_source_has_active_member])
        writer.writerow(["current_source_has_stage124_marker", current_source_has_stage124_marker])
        writer.writerow(["design_all_items_not_applied", design_all_not_applied])
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
        writer.writerow(["bounded_publish_call_source_patch_preflight_frozen", bounded_publish_call_source_patch_preflight_frozen])
        writer.writerow(["manual_enable_active", manual_enable_active])
        writer.writerow(["active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g3_no_publish_call", gate_status.get("G3", False)])
        writer.writerow(["g8_manual_enable_active", manual_enable_active])
        writer.writerow(["g9_active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g30_bounded_publish_call_source_patch_design_exists", gate_status.get("G30", False)])
        writer.writerow(["g31_bounded_publish_call_source_patch_preflight_freeze_passed", bounded_publish_call_source_patch_preflight_frozen])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", control_law_changed])
        writer.writerow(["torque_publisher_enabled", torque_publisher_enabled])
        writer.writerow(["torque_command_published_by_stage1213", torque_command_published_by_stage1213])
        writer.writerow(["stage12_scope", "bounded_publish_call_source_patch_preflight_freeze_only"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["ros2_cpp_realtime_controller_completed", False])
        writer.writerow(["pure_wbc_locomotion_completed", False])
        writer.writerow(["ekf_completed", False])
        writer.writerow(["full_3d_centroidal_mpc_completed", False])
        writer.writerow(["num_checks", len(checks)])
        writer.writerow(["num_failed_checks", sum(1 for row in checks if not row["pass"])])
        writer.writerow(["pass", all_pass])
        writer.writerow(["log_csv", str(LOG_PATH.relative_to(ROOT))])
        writer.writerow(["hash_csv", str(HASH_PATH.relative_to(ROOT))])
        writer.writerow(["safety_gate_csv", str(SAFETY_GATE_PATH.relative_to(ROOT))])
        writer.writerow(["summary_csv", str(SUMMARY_PATH.relative_to(ROOT))])
        writer.writerow(["doc", str(DOC_PATH.relative_to(ROOT))])

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 12.13 Bounded Publish-call Source Patch Preflight Freeze

Stage 12.13 冻结 bounded publish-call source patch preflight baseline。

- Script: `scripts/stage12_bounded_publish_call_source_patch_preflight_freeze.py`
- Log: `results/logs_sample/stage12_bounded_publish_call_source_patch_preflight_freeze_log.csv`
- Hashes: `results/logs_sample/stage12_bounded_publish_call_source_patch_preflight_freeze_hashes.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1213.csv`
- Summary: `results/logs_sample/stage12_bounded_publish_call_source_patch_preflight_freeze_summary.csv`
- Docs: `docs/STAGE12_BOUNDED_PUBLISH_CALL_SOURCE_PATCH_PREFLIGHT_FREEZE.md`
- pass: `{all_pass}`
- bounded_publish_call_source_patch_preflight_frozen: `{bounded_publish_call_source_patch_preflight_frozen}`
- current_source_has_publish_call: `{current_source_has_publish_call}`
- active_ros_publisher_path_exists: `{active_ros_publisher_path_exists}`
- manual_enable_active: `{manual_enable_active}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `{torque_publisher_enabled}`
- torque_command_published_by_stage1213: `{torque_command_published_by_stage1213}`
- control_law_changed: `{control_law_changed}`

Stage 12.13 只冻结 bounded publish-call source patch preflight baseline，不加入 publish call，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 12.13 Bounded Publish-call Source Patch Preflight Freeze"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 12.13] bounded publish-call source patch preflight freeze")
    print(f"pass={all_pass}")
    print(f"missing_file_count={len(missing_files)}")
    print(f"bounded_publish_call_source_patch_preflight_frozen={bounded_publish_call_source_patch_preflight_frozen}")
    print(f"current_source_has_create_publisher={current_source_has_create_publisher}")
    print(f"current_source_has_publish_call={current_source_has_publish_call}")
    print(f"active_ros_publisher_path_exists={active_ros_publisher_path_exists}")
    print(f"manual_enable_active={manual_enable_active}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print(f"control_law_changed={control_law_changed}")
    print(f"torque_publisher_enabled={torque_publisher_enabled}")
    print(f"torque_command_published_by_stage1213={torque_command_published_by_stage1213}")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
    print(f"hash_csv={HASH_PATH.relative_to(ROOT)}")
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
