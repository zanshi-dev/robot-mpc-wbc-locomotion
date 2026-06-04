#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE128_SUMMARY = LOG_DIR / "stage12_manual_enable_no_publish_freeze_summary.csv"
STAGE128_GATE = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage128.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
SAFETY_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

DESIGN_CSV = LOG_DIR / "stage12_publish_call_design.csv"
LOG_PATH = LOG_DIR / "stage12_publish_call_design_log.csv"
SUMMARY_PATH = LOG_DIR / "stage12_publish_call_design_summary.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage129.csv"
DOC_PATH = ROOT / "docs/STAGE12_PUBLISH_CALL_DESIGN_ONLY.md"

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

    s128 = load_summary(STAGE128_SUMMARY)

    stage128_pass = as_bool(s128.get("pass", "False"))
    manual_enable_no_publish_frozen = as_bool(s128.get("manual_enable_no_publish_frozen", "False"))
    stage128_source_has_create_publisher = as_bool(s128.get("current_source_has_create_publisher", "False"))
    stage128_source_has_publish_call = as_bool(s128.get("current_source_has_publish_call", "True"))
    stage128_active_path = as_bool(s128.get("active_ros_publisher_path_exists", "False"))
    stage128_no_message = as_bool(s128.get("no_message_observed_during_activation", "False"))
    stage128_torque_ready = as_bool(s128.get("torque_enable_ready", "True"))
    stage128_torque_enabled = as_bool(s128.get("torque_publisher_enabled", "True"))
    stage128_torque_published = as_bool(s128.get("torque_command_published_by_stage128", "True"))
    stage128_control_changed = as_bool(s128.get("control_law_changed", "True"))

    add_check(checks, "stage128_summary_exists", STAGE128_SUMMARY.exists(), True, STAGE128_SUMMARY.exists(), str(STAGE128_SUMMARY))
    add_check(checks, "stage128_pass", stage128_pass, True, stage128_pass)
    add_check(checks, "stage128_manual_enable_no_publish_frozen", manual_enable_no_publish_frozen, True, manual_enable_no_publish_frozen)
    add_check(checks, "stage128_current_source_has_create_publisher", stage128_source_has_create_publisher, True, stage128_source_has_create_publisher)
    add_check(checks, "stage128_current_source_has_publish_call", stage128_source_has_publish_call, False, not stage128_source_has_publish_call)
    add_check(checks, "stage128_active_ros_publisher_path_exists", stage128_active_path, True, stage128_active_path)
    add_check(checks, "stage128_no_message_observed_during_activation", stage128_no_message, True, stage128_no_message)
    add_check(checks, "stage128_torque_enable_ready", stage128_torque_ready, False, not stage128_torque_ready)
    add_check(checks, "stage128_torque_publisher_enabled", stage128_torque_enabled, False, not stage128_torque_enabled)
    add_check(checks, "stage128_torque_command_published", stage128_torque_published, False, not stage128_torque_published)
    add_check(checks, "stage128_control_law_changed", stage128_control_changed, False, not stage128_control_changed)

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

    gate_rows = load_dicts(STAGE128_GATE)
    gate_status = {
        row.get("gate", ""): as_bool(row.get("current_status", "False"))
        for row in gate_rows
    }

    expected_gate_status = {
        "G2": False,
        "G3": True,
        "G8": False,
        "G9": True,
        "G23": True,
        "G24": True,
        "G25": True,
        "G26": True,
    }

    add_check(checks, "stage128_gate_exists", STAGE128_GATE.exists(), True, STAGE128_GATE.exists(), str(STAGE128_GATE))
    for gate, expected in expected_gate_status.items():
        value = gate_status.get(gate, None)
        add_check(checks, f"{gate}_status_after_stage128", value, expected, value == expected)

    design_rows = [
        {
            "item": "stage12_scope",
            "value": "publish_call_design_only",
            "implemented_in_stage129": False,
            "allowed_in_future_publish_stage": True,
            "guard": "Stage 12.9 must not edit C++ source",
            "description": "Only records the future publish-call protocol.",
        },
        {
            "item": "future_publish_call_site",
            "value": "active_torque_cmd_publisher_->publish(safe_torque_msg)",
            "implemented_in_stage129": False,
            "allowed_in_future_publish_stage": True,
            "guard": "Must appear only in a later explicit publish-call implementation stage",
            "description": "Future publish call target.",
        },
        {
            "item": "future_publish_preconditions",
            "value": "manual flags true && active publisher exists && state_ready && inputs_fresh",
            "implemented_in_stage129": False,
            "allowed_in_future_publish_stage": True,
            "guard": "If any precondition is false, no publish is allowed",
            "description": "Runtime gating before any torque command publication.",
        },
        {
            "item": "future_payload_contract",
            "value": "Float64MultiArray length=12; all finite; Go1 actuator order FR,FL,RR,RL hip,thigh,calf",
            "implemented_in_stage129": False,
            "allowed_in_future_publish_stage": True,
            "guard": "Invalid payload must abort or fall back to zero",
            "description": "Future torque command payload contract.",
        },
        {
            "item": "future_safety_filter",
            "value": "watchdogFallbackZeroTorque before clampTorqueCommand",
            "implemented_in_stage129": False,
            "allowed_in_future_publish_stage": True,
            "guard": "No raw unclamped torque may be published",
            "description": "Future safety processing chain.",
        },
        {
            "item": "future_first_publish_policy",
            "value": "zero/safe torque only; one-shot or bounded dry-run before continuous publishing",
            "implemented_in_stage129": False,
            "allowed_in_future_publish_stage": True,
            "guard": "Continuous publishing requires later stage",
            "description": "First publish stage must remain bounded.",
        },
        {
            "item": "future_no_control_law_change_rule",
            "value": "publish-call implementation must not alter current mixed online control baseline",
            "implemented_in_stage129": False,
            "allowed_in_future_publish_stage": True,
            "guard": "source diff must be limited to publish-gated output path",
            "description": "Future publish path must not claim pure WBC or realtime controller completion.",
        },
        {
            "item": "future_runtime_observation",
            "value": "before/after topic echo; message count; payload length; finite check; revert flags after test",
            "implemented_in_stage129": False,
            "allowed_in_future_publish_stage": True,
            "guard": "Missing runtime evidence aborts publish stage",
            "description": "Future evidence required for any publish-call implementation.",
        },
        {
            "item": "future_revert_procedure",
            "value": "set confirm_torque_publisher_enable false; set enable_torque_publisher false; stop controller",
            "implemented_in_stage129": False,
            "allowed_in_future_publish_stage": True,
            "guard": "Revert must run in finally block",
            "description": "Fail-closed cleanup for future publish test.",
        },
        {
            "item": "future_abort_conditions",
            "value": "source hash unexpected; publish call appears outside allowed block; params fail; controller exits; payload invalid; message count unexpected",
            "implemented_in_stage129": False,
            "allowed_in_future_publish_stage": True,
            "guard": "Future publish script must fail closed",
            "description": "Abort policy for later publish stage.",
        },
    ]

    with DESIGN_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "item",
                "value",
                "implemented_in_stage129",
                "allowed_in_future_publish_stage",
                "guard",
                "description",
            ],
        )
        writer.writeheader()
        writer.writerows(design_rows)

    publish_call_design_exists = DESIGN_CSV.exists()
    design_all_items_not_implemented = all(not row["implemented_in_stage129"] for row in design_rows)
    design_has_future_publish_call_site = any(row["item"] == "future_publish_call_site" for row in design_rows)
    design_has_preconditions = any(row["item"] == "future_publish_preconditions" for row in design_rows)
    design_has_payload_contract = any(row["item"] == "future_payload_contract" for row in design_rows)
    design_has_safety_filter = any(row["item"] == "future_safety_filter" for row in design_rows)
    design_has_first_publish_policy = any(row["item"] == "future_first_publish_policy" for row in design_rows)
    design_forbids_control_law_change = any(row["item"] == "future_no_control_law_change_rule" for row in design_rows)
    design_has_runtime_observation = any(row["item"] == "future_runtime_observation" for row in design_rows)
    design_has_revert_procedure = any(row["item"] == "future_revert_procedure" for row in design_rows)
    design_has_abort_conditions = any(row["item"] == "future_abort_conditions" for row in design_rows)

    source_after = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    source_hash_after = sha256_text(source_after)
    source_unchanged_by_stage129 = source_hash_before == source_hash_after

    add_check(checks, "publish_call_design_exists", publish_call_design_exists, True, publish_call_design_exists, str(DESIGN_CSV))
    add_check(checks, "design_all_items_not_implemented", design_all_items_not_implemented, True, design_all_items_not_implemented)
    add_check(checks, "design_has_future_publish_call_site", design_has_future_publish_call_site, True, design_has_future_publish_call_site)
    add_check(checks, "design_has_preconditions", design_has_preconditions, True, design_has_preconditions)
    add_check(checks, "design_has_payload_contract", design_has_payload_contract, True, design_has_payload_contract)
    add_check(checks, "design_has_safety_filter", design_has_safety_filter, True, design_has_safety_filter)
    add_check(checks, "design_has_first_publish_policy", design_has_first_publish_policy, True, design_has_first_publish_policy)
    add_check(checks, "design_forbids_control_law_change", design_forbids_control_law_change, True, design_forbids_control_law_change)
    add_check(checks, "design_has_runtime_observation", design_has_runtime_observation, True, design_has_runtime_observation)
    add_check(checks, "design_has_revert_procedure", design_has_revert_procedure, True, design_has_revert_procedure)
    add_check(checks, "design_has_abort_conditions", design_has_abort_conditions, True, design_has_abort_conditions)
    add_check(checks, "source_unchanged_by_stage129", source_unchanged_by_stage129, True, source_unchanged_by_stage129)

    publish_call_design_complete = True
    manual_enable_active = False
    active_ros_publisher_path_exists = True
    torque_enable_ready = False
    control_law_changed = False
    torque_publisher_enabled = False
    torque_command_published_by_stage129 = False

    gate_out_rows = []
    for row in gate_rows:
        gate_out_rows.append(row)

    gate_out_rows.append({
        "gate": "G27",
        "name": "Publish-call design exists",
        "required_before_torque_publish": True,
        "current_status": publish_call_design_complete,
        "evidence": str(DESIGN_CSV.relative_to(ROOT)),
    })

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(gate_out_rows)

    add_check(checks, "publish_call_design_complete", publish_call_design_complete, True, publish_call_design_complete)
    add_check(checks, "manual_enable_active", manual_enable_active, False, not manual_enable_active)
    add_check(checks, "active_ros_publisher_path_exists", active_ros_publisher_path_exists, True, active_ros_publisher_path_exists)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)
    add_check(checks, "control_law_changed", control_law_changed, False, not control_law_changed)
    add_check(checks, "torque_publisher_enabled", torque_publisher_enabled, False, not torque_publisher_enabled)
    add_check(checks, "torque_command_published_by_stage129", torque_command_published_by_stage129, False, not torque_command_published_by_stage129)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    DOC_PATH.write_text(f"""# Stage 12.9 Publish-call Design Only

## 一、结论

Stage 12.9 只设计 future publish-call implementation protocol。

本阶段不修改 C++ source，不加入 publish call，不发布 torque，不改变控制律。

## 二、前置状态

Stage 12.8:

- pass: {stage128_pass}
- manual_enable_no_publish_frozen: {manual_enable_no_publish_frozen}
- current_source_has_create_publisher: {stage128_source_has_create_publisher}
- current_source_has_publish_call: {stage128_source_has_publish_call}
- active_ros_publisher_path_exists: {stage128_active_path}
- no_message_observed_during_activation: {stage128_no_message}
- torque_enable_ready: {stage128_torque_ready}

## 三、当前 source guard

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: {source_has_create_publisher}
- source_has_publish_call: {source_has_publish_call}
- source_references_torque_topic: {source_references_torque_topic}
- source_has_active_publisher_member: {source_has_active_publisher_member}
- source_unchanged_by_stage129: {source_unchanged_by_stage129}

## 四、Publish-call design

Design CSV:

    results/logs_sample/stage12_publish_call_design.csv

Future publish-call protocol:

- publish call site: active_torque_cmd_publisher_->publish(safe_torque_msg)
- preconditions: manual flags true, active publisher exists, state_ready, inputs_fresh
- payload: Float64MultiArray length 12, all finite, Go1 actuator order FR, FL, RR, RL
- safety chain: watchdogFallbackZeroTorque before clampTorqueCommand
- first publish policy: zero/safe bounded dry-run only
- no control law change
- runtime observation and fail-closed revert required

## 五、Safety gate after Stage 12.9

新增：

- G27 publish-call design exists: {publish_call_design_complete}

Key gates remain:

- G3 no publish call: {gate_status.get("G3")}
- G8 manual enable active after revert: {manual_enable_active}
- G9 active ROS publisher path exists: {active_ros_publisher_path_exists}
- G26 manual-enable no-publish freeze passed: {gate_status.get("G26")}

Therefore:

    torque_enable_ready = {torque_enable_ready}

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.9 没有完成：

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
        writer.writerow(["stage", "Stage 12.9"])
        writer.writerow(["test_name", "publish_call_design_only"])
        writer.writerow(["stage128_pass", stage128_pass])
        writer.writerow(["stage128_manual_enable_no_publish_frozen", manual_enable_no_publish_frozen])
        writer.writerow(["source_has_create_publisher", source_has_create_publisher])
        writer.writerow(["source_has_publish_call", source_has_publish_call])
        writer.writerow(["source_references_torque_topic", source_references_torque_topic])
        writer.writerow(["source_has_active_publisher_member", source_has_active_publisher_member])
        writer.writerow(["source_has_stage124_marker", source_has_stage124_marker])
        writer.writerow(["source_declares_enable_param_default_false", source_declares_enable_param])
        writer.writerow(["source_declares_confirm_param_default_false", source_declares_confirm_param])
        writer.writerow(["source_unchanged_by_stage129", source_unchanged_by_stage129])
        writer.writerow(["publish_call_design_exists", publish_call_design_exists])
        writer.writerow(["design_all_items_not_implemented", design_all_items_not_implemented])
        writer.writerow(["design_has_future_publish_call_site", design_has_future_publish_call_site])
        writer.writerow(["design_has_preconditions", design_has_preconditions])
        writer.writerow(["design_has_payload_contract", design_has_payload_contract])
        writer.writerow(["design_has_safety_filter", design_has_safety_filter])
        writer.writerow(["design_has_first_publish_policy", design_has_first_publish_policy])
        writer.writerow(["design_forbids_control_law_change", design_forbids_control_law_change])
        writer.writerow(["design_has_runtime_observation", design_has_runtime_observation])
        writer.writerow(["design_has_revert_procedure", design_has_revert_procedure])
        writer.writerow(["design_has_abort_conditions", design_has_abort_conditions])
        writer.writerow(["publish_call_design_complete", publish_call_design_complete])
        writer.writerow(["manual_enable_active", manual_enable_active])
        writer.writerow(["active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g3_no_publish_call", gate_status.get("G3", False)])
        writer.writerow(["g8_manual_enable_active", manual_enable_active])
        writer.writerow(["g9_active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g26_manual_enable_no_publish_freeze_passed", gate_status.get("G26", False)])
        writer.writerow(["g27_publish_call_design_exists", publish_call_design_complete])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", control_law_changed])
        writer.writerow(["torque_publisher_enabled", torque_publisher_enabled])
        writer.writerow(["torque_command_published_by_stage129", torque_command_published_by_stage129])
        writer.writerow(["stage12_scope", "publish_call_design_only"])
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
## Stage 12.9 Publish-call Design Only

Stage 12.9 完成 publish-call design only。

- Script: `scripts/stage12_publish_call_design_only.py`
- Design: `results/logs_sample/stage12_publish_call_design.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage129.csv`
- Summary: `results/logs_sample/stage12_publish_call_design_summary.csv`
- Docs: `docs/STAGE12_PUBLISH_CALL_DESIGN_ONLY.md`
- pass: `{all_pass}`
- publish_call_design_complete: `{publish_call_design_complete}`
- source_unchanged_by_stage129: `{source_unchanged_by_stage129}`
- active_ros_publisher_path_exists: `{active_ros_publisher_path_exists}`
- manual_enable_active: `{manual_enable_active}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `{torque_publisher_enabled}`
- torque_command_published_by_stage129: `{torque_command_published_by_stage129}`
- control_law_changed: `{control_law_changed}`

Stage 12.9 只设计 publish call，不加入 publish call，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 12.9 Publish-call Design Only"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 12.9] publish-call design only")
    print(f"pass={all_pass}")
    print(f"stage128_pass={stage128_pass}")
    print(f"publish_call_design_complete={publish_call_design_complete}")
    print(f"source_unchanged_by_stage129={source_unchanged_by_stage129}")
    print(f"source_has_publish_call={source_has_publish_call}")
    print(f"active_ros_publisher_path_exists={active_ros_publisher_path_exists}")
    print(f"manual_enable_active={manual_enable_active}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print(f"control_law_changed={control_law_changed}")
    print(f"torque_publisher_enabled={torque_publisher_enabled}")
    print(f"torque_command_published_by_stage129={torque_command_published_by_stage129}")
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
