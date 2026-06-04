#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE1217_SUMMARY = LOG_DIR / "stage12_continuous_torque_streaming_preflight_freeze_summary.csv"
STAGE1217_GATE = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage1217.csv"
STAGE1216_DESIGN = LOG_DIR / "stage12_continuous_torque_streaming_design.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"

DESIGN_CSV = LOG_DIR / "stage12_continuous_torque_streaming_source_patch_design.csv"
LOG_PATH = LOG_DIR / "stage12_continuous_torque_streaming_source_patch_design_log.csv"
SUMMARY_PATH = LOG_DIR / "stage12_continuous_torque_streaming_source_patch_design_summary.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage1218.csv"
DOC_PATH = ROOT / "docs/STAGE12_CONTINUOUS_TORQUE_STREAMING_SOURCE_PATCH_DESIGN_ONLY.md"

TORQUE_TOPIC = "/go1/joint_torque_cmd"


def load_summary(path: Path):
    out = {}
    if not path.exists():
        return out
    with path.open(newline="") as f:
        rows = list(csv.reader(f))
    if rows and len(rows[0]) >= 2 and rows[0][0] == "metric":
        for row in rows[1:]:
            if len(row) >= 2:
                out[row[0]] = row[1]
    return out


def load_dicts(path: Path):
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def as_bool(x):
    return str(x).strip().lower() in {"true", "1", "yes"}


def sha256_text(text: str):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def count_publish_calls(text: str):
    return len(re.findall(r"(?:->|\.)publish\s*\(", text))


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

    s1217 = load_summary(STAGE1217_SUMMARY)

    stage1217_pass = as_bool(s1217.get("pass", "False"))
    stage1217_preflight_frozen = as_bool(s1217.get("continuous_torque_streaming_preflight_frozen", "False"))
    stage1217_source_no_streaming_flags = as_bool(s1217.get("source_has_no_continuous_streaming_flags", "False"))
    stage1217_source_no_streaming_timer = as_bool(s1217.get("source_has_no_continuous_streaming_timer", "False"))
    stage1217_publish_count_one = str(s1217.get("publish_call_count", "")) == "1"
    stage1217_streaming_completed = as_bool(s1217.get("continuous_torque_streaming_completed", "True"))
    stage1217_torque_ready = as_bool(s1217.get("torque_enable_ready", "True"))
    stage1217_torque_enabled = as_bool(s1217.get("torque_publisher_enabled", "True"))
    stage1217_torque_published = as_bool(s1217.get("torque_command_published_by_stage1217", "True"))
    stage1217_control_changed = as_bool(s1217.get("control_law_changed", "True"))

    add_check(checks, "stage1217_summary_exists", STAGE1217_SUMMARY.exists(), True, STAGE1217_SUMMARY.exists(), str(STAGE1217_SUMMARY))
    add_check(checks, "stage1217_pass", stage1217_pass, True, stage1217_pass)
    add_check(checks, "stage1217_preflight_frozen", stage1217_preflight_frozen, True, stage1217_preflight_frozen)
    add_check(checks, "stage1217_source_no_streaming_flags", stage1217_source_no_streaming_flags, True, stage1217_source_no_streaming_flags)
    add_check(checks, "stage1217_source_no_streaming_timer", stage1217_source_no_streaming_timer, True, stage1217_source_no_streaming_timer)
    add_check(checks, "stage1217_publish_call_count_one", stage1217_publish_count_one, True, stage1217_publish_count_one)
    add_check(checks, "stage1217_continuous_streaming_completed", stage1217_streaming_completed, False, not stage1217_streaming_completed)
    add_check(checks, "stage1217_torque_enable_ready", stage1217_torque_ready, False, not stage1217_torque_ready)
    add_check(checks, "stage1217_torque_publisher_enabled", stage1217_torque_enabled, False, not stage1217_torque_enabled)
    add_check(checks, "stage1217_torque_command_published", stage1217_torque_published, False, not stage1217_torque_published)
    add_check(checks, "stage1217_control_law_changed", stage1217_control_changed, False, not stage1217_control_changed)

    source_before = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    source_hash_before = sha256_text(source_before)

    publish_call_count = count_publish_calls(source_before)
    source_has_exactly_one_publish_call = publish_call_count == 1
    source_has_delayed_one_shot_timer = (
        "stage1214_one_shot_publish_timer_ = this->create_wall_timer" in source_before and
        "std::chrono::milliseconds(2500)" in source_before
    )
    source_has_timer_member = "rclcpp::TimerBase::SharedPtr stage1214_one_shot_publish_timer_" in source_before
    source_timer_cancels_itself = "stage1214_one_shot_publish_timer_->cancel()" in source_before
    source_has_zero_safe_message_helper = "makeStage1214ZeroSafeTorqueCommandMessage" in source_before
    source_uses_zero_safe_message_helper = "auto msg = makeStage1214ZeroSafeTorqueCommandMessage();" in source_before
    source_has_stage1214_marker = (
        "kStage1214BoundedPublishCallImplemented = true" in source_before and
        "kStage1214ContinuousPublishImplemented = false" in source_before
    )
    source_has_stage124_marker = (
        "kStage124PublisherConstructionImplemented" in source_before and
        "kStage124PublishCallImplemented = false" in source_before
    )
    source_references_torque_topic = TORQUE_TOPIC in source_before
    source_has_active_publisher_member = "active_torque_cmd_publisher_" in source_before
    source_has_no_continuous_streaming_flags = (
        "enable_continuous_torque_streaming" not in source_before and
        "confirm_continuous_torque_streaming" not in source_before
    )
    source_has_no_continuous_streaming_timer = (
        "continuous_torque_streaming_timer_" not in source_before and
        "continuousTorqueStreaming" not in source_before
    )

    add_check(checks, "cpp_source_exists", CPP_SOURCE.exists(), True, CPP_SOURCE.exists(), str(CPP_SOURCE))
    add_check(checks, "publish_call_count", publish_call_count, 1, publish_call_count == 1)
    add_check(checks, "source_has_exactly_one_publish_call", source_has_exactly_one_publish_call, True, source_has_exactly_one_publish_call)
    add_check(checks, "source_has_delayed_one_shot_timer", source_has_delayed_one_shot_timer, True, source_has_delayed_one_shot_timer)
    add_check(checks, "source_has_timer_member", source_has_timer_member, True, source_has_timer_member)
    add_check(checks, "source_timer_cancels_itself", source_timer_cancels_itself, True, source_timer_cancels_itself)
    add_check(checks, "source_has_zero_safe_message_helper", source_has_zero_safe_message_helper, True, source_has_zero_safe_message_helper)
    add_check(checks, "source_uses_zero_safe_message_helper", source_uses_zero_safe_message_helper, True, source_uses_zero_safe_message_helper)
    add_check(checks, "source_has_stage1214_marker", source_has_stage1214_marker, True, source_has_stage1214_marker)
    add_check(checks, "source_has_stage124_marker", source_has_stage124_marker, True, source_has_stage124_marker)
    add_check(checks, "source_references_torque_topic", source_references_torque_topic, True, source_references_torque_topic)
    add_check(checks, "source_has_active_publisher_member", source_has_active_publisher_member, True, source_has_active_publisher_member)
    add_check(checks, "source_has_no_continuous_streaming_flags", source_has_no_continuous_streaming_flags, True, source_has_no_continuous_streaming_flags)
    add_check(checks, "source_has_no_continuous_streaming_timer", source_has_no_continuous_streaming_timer, True, source_has_no_continuous_streaming_timer)

    prior_design_rows = load_dicts(STAGE1216_DESIGN)
    prior_design_all_not_implemented = all(not as_bool(row.get("implemented_in_stage1216", "True")) for row in prior_design_rows)
    prior_design_has_rate_limit = any(row.get("item") == "future_rate_limit" for row in prior_design_rows)
    prior_design_has_duration_limit = any(row.get("item") == "future_duration_limit" for row in prior_design_rows)
    prior_design_has_abort_conditions = any(row.get("item") == "future_abort_conditions" for row in prior_design_rows)

    add_check(checks, "stage1216_design_csv_exists", STAGE1216_DESIGN.exists(), True, STAGE1216_DESIGN.exists(), str(STAGE1216_DESIGN))
    add_check(checks, "stage1216_design_all_not_implemented", prior_design_all_not_implemented, True, prior_design_all_not_implemented)
    add_check(checks, "stage1216_design_has_rate_limit", prior_design_has_rate_limit, True, prior_design_has_rate_limit)
    add_check(checks, "stage1216_design_has_duration_limit", prior_design_has_duration_limit, True, prior_design_has_duration_limit)
    add_check(checks, "stage1216_design_has_abort_conditions", prior_design_has_abort_conditions, True, prior_design_has_abort_conditions)

    gate_rows = load_dicts(STAGE1217_GATE)
    gate_status = {
        row.get("gate", ""): as_bool(row.get("current_status", "False"))
        for row in gate_rows
    }

    expected_gate_status = {
        "G3": False,
        "G8": False,
        "G9": True,
        "G35": True,
        "G36": True,
        "G37": True,
    }

    add_check(checks, "stage1217_gate_exists", STAGE1217_GATE.exists(), True, STAGE1217_GATE.exists(), str(STAGE1217_GATE))
    for gate, expected in expected_gate_status.items():
        value = gate_status.get(gate, None)
        add_check(checks, f"{gate}_status_after_stage1217", value, expected, value == expected)

    design_rows = [
        {
            "item": "stage12_scope",
            "value": "continuous_torque_streaming_source_patch_design_only",
            "applied_in_stage1218": False,
            "allowed_in_future_patch_stage": True,
            "guard": "Stage 12.18 must not edit C++ source and must not add publish calls",
            "description": "Only records the future continuous streaming source patch design.",
        },
        {
            "item": "future_patch_target",
            "value": "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp",
            "applied_in_stage1218": False,
            "allowed_in_future_patch_stage": True,
            "guard": "future source hash must match Stage 12.17 preflight hash before patch",
            "description": "Future source patch target.",
        },
        {
            "item": "future_stage_marker",
            "value": "kStage1219ContinuousTorqueStreamingImplemented = true; kStage1219HardwareDeploymentImplemented = false",
            "applied_in_stage1218": False,
            "allowed_in_future_patch_stage": True,
            "guard": "marker must separate continuous dry-run from hardware deployment",
            "description": "Future marker for continuous dry-run source patch.",
        },
        {
            "item": "future_continuous_params",
            "value": "enable_continuous_torque_streaming=false; confirm_continuous_torque_streaming=false",
            "applied_in_stage1218": False,
            "allowed_in_future_patch_stage": True,
            "guard": "both params default false; no streaming unless both true",
            "description": "Future continuous streaming manual enable parameters.",
        },
        {
            "item": "future_four_flag_gate",
            "value": "enable_torque_publisher && confirm_torque_publisher_enable && enable_continuous_torque_streaming && confirm_continuous_torque_streaming",
            "applied_in_stage1218": False,
            "allowed_in_future_patch_stage": True,
            "guard": "future continuous streaming requires both existing publish flags and both streaming flags",
            "description": "Four-flag gate for future continuous streaming.",
        },
        {
            "item": "future_timer_member",
            "value": "rclcpp::TimerBase::SharedPtr continuous_torque_streaming_timer_",
            "applied_in_stage1218": False,
            "allowed_in_future_patch_stage": True,
            "guard": "timer must be cancellable and stopped after duration or flag revert",
            "description": "Future continuous streaming timer member.",
        },
        {
            "item": "future_timer_rate",
            "value": "std::chrono::milliseconds(100); initial dry-run <= 10 Hz",
            "applied_in_stage1218": False,
            "allowed_in_future_patch_stage": True,
            "guard": "higher rates require separate later stage",
            "description": "Initial continuous dry-run rate limit.",
        },
        {
            "item": "future_duration_limit",
            "value": "max_streaming_ticks <= 30; max duration <= 3 seconds at 10 Hz",
            "applied_in_stage1218": False,
            "allowed_in_future_patch_stage": True,
            "guard": "unbounded streaming forbidden",
            "description": "Initial continuous dry-run duration limit.",
        },
        {
            "item": "future_reuse_single_publish_call",
            "value": "reuse existing bounded publish helper; source publish call count should remain 1",
            "applied_in_stage1218": False,
            "allowed_in_future_patch_stage": True,
            "guard": "future source patch should not add a second publish() call unless a separate design change is approved",
            "description": "Future continuous timer should call the existing bounded safe publish helper.",
        },
        {
            "item": "future_streaming_tick_helper",
            "value": "runContinuousTorqueStreamingTickIfAllowed()",
            "applied_in_stage1218": False,
            "allowed_in_future_patch_stage": True,
            "guard": "helper returns false and publishes nothing if any gate fails",
            "description": "Future helper called by the timer.",
        },
        {
            "item": "future_message_payload",
            "value": "Float64MultiArray length=12; all finite; zero/safe torque dry-run first; Go1 order FR,FL,RR,RL hip,thigh,calf",
            "applied_in_stage1218": False,
            "allowed_in_future_patch_stage": True,
            "guard": "invalid payload aborts before publish",
            "description": "Future payload contract.",
        },
        {
            "item": "future_safety_chain",
            "value": "watchdogFallbackZeroTorque then clampTorqueCommand before every timer tick publish",
            "applied_in_stage1218": False,
            "allowed_in_future_patch_stage": True,
            "guard": "no raw unclamped torque may be published",
            "description": "Future safety chain on every tick.",
        },
        {
            "item": "future_stop_conditions",
            "value": "stop when tick limit reached, flag reverted, watchdog stale, payload invalid, or controller shutdown",
            "applied_in_stage1218": False,
            "allowed_in_future_patch_stage": True,
            "guard": "timer cancel required on every stop path",
            "description": "Future fail-closed stop policy.",
        },
        {
            "item": "future_runtime_evidence",
            "value": "expect bounded message count 1..30; payload length 12; finite; zero/safe; no messages after stop",
            "applied_in_stage1218": False,
            "allowed_in_future_patch_stage": True,
            "guard": "missing evidence aborts future streaming implementation stage",
            "description": "Future runtime evidence requirement.",
        },
        {
            "item": "future_no_hardware_rule",
            "value": "simulation/ROS topic dry-run only; hardware deployment remains false",
            "applied_in_stage1218": False,
            "allowed_in_future_patch_stage": True,
            "guard": "no hardware interface or actuator bridge enablement",
            "description": "Future stage remains non-hardware.",
        },
        {
            "item": "future_no_control_law_change_rule",
            "value": "do not modify estimator, MPC, WBC, gait, or baseline control computation",
            "applied_in_stage1218": False,
            "allowed_in_future_patch_stage": True,
            "guard": "future diff limited to output gating/timer plumbing",
            "description": "Continuous streaming is not controller completion.",
        },
        {
            "item": "future_abort_conditions",
            "value": "unexpected source hash; publish call count not 1; timer not cancellable; params fail; invalid payload; unexpected message count; controller exits",
            "applied_in_stage1218": False,
            "allowed_in_future_patch_stage": True,
            "guard": "future patch script must fail closed",
            "description": "Abort policy for future source patch implementation.",
        },
    ]

    with DESIGN_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "item",
                "value",
                "applied_in_stage1218",
                "allowed_in_future_patch_stage",
                "guard",
                "description",
            ],
        )
        writer.writeheader()
        writer.writerows(design_rows)

    design_exists = DESIGN_CSV.exists()
    design_all_not_applied = all(not row["applied_in_stage1218"] for row in design_rows)
    design_has_patch_target = any(row["item"] == "future_patch_target" for row in design_rows)
    design_has_stage_marker = any(row["item"] == "future_stage_marker" for row in design_rows)
    design_has_continuous_params = any(row["item"] == "future_continuous_params" for row in design_rows)
    design_has_four_flag_gate = any(row["item"] == "future_four_flag_gate" for row in design_rows)
    design_has_timer_member = any(row["item"] == "future_timer_member" for row in design_rows)
    design_has_timer_rate = any(row["item"] == "future_timer_rate" for row in design_rows)
    design_has_duration_limit = any(row["item"] == "future_duration_limit" for row in design_rows)
    design_reuses_single_publish_call = any(row["item"] == "future_reuse_single_publish_call" for row in design_rows)
    design_has_streaming_tick_helper = any(row["item"] == "future_streaming_tick_helper" for row in design_rows)
    design_has_message_payload = any(row["item"] == "future_message_payload" for row in design_rows)
    design_has_safety_chain = any(row["item"] == "future_safety_chain" for row in design_rows)
    design_has_stop_conditions = any(row["item"] == "future_stop_conditions" for row in design_rows)
    design_has_runtime_evidence = any(row["item"] == "future_runtime_evidence" for row in design_rows)
    design_forbids_hardware = any(row["item"] == "future_no_hardware_rule" for row in design_rows)
    design_forbids_control_law_change = any(row["item"] == "future_no_control_law_change_rule" for row in design_rows)
    design_has_abort_conditions = any(row["item"] == "future_abort_conditions" for row in design_rows)

    source_after = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    source_hash_after = sha256_text(source_after)
    source_unchanged_by_stage1218 = source_hash_before == source_hash_after

    source_patch_design_complete = (
        design_exists and
        design_all_not_applied and
        design_has_patch_target and
        design_has_stage_marker and
        design_has_continuous_params and
        design_has_four_flag_gate and
        design_has_timer_member and
        design_has_timer_rate and
        design_has_duration_limit and
        design_reuses_single_publish_call and
        design_has_streaming_tick_helper and
        design_has_message_payload and
        design_has_safety_chain and
        design_has_stop_conditions and
        design_has_runtime_evidence and
        design_forbids_hardware and
        design_forbids_control_law_change and
        design_has_abort_conditions
    )

    add_check(checks, "continuous_torque_streaming_source_patch_design_exists", design_exists, True, design_exists, str(DESIGN_CSV))
    add_check(checks, "design_all_items_not_applied", design_all_not_applied, True, design_all_not_applied)
    add_check(checks, "design_has_patch_target", design_has_patch_target, True, design_has_patch_target)
    add_check(checks, "design_has_stage_marker", design_has_stage_marker, True, design_has_stage_marker)
    add_check(checks, "design_has_continuous_params", design_has_continuous_params, True, design_has_continuous_params)
    add_check(checks, "design_has_four_flag_gate", design_has_four_flag_gate, True, design_has_four_flag_gate)
    add_check(checks, "design_has_timer_member", design_has_timer_member, True, design_has_timer_member)
    add_check(checks, "design_has_timer_rate", design_has_timer_rate, True, design_has_timer_rate)
    add_check(checks, "design_has_duration_limit", design_has_duration_limit, True, design_has_duration_limit)
    add_check(checks, "design_reuses_single_publish_call", design_reuses_single_publish_call, True, design_reuses_single_publish_call)
    add_check(checks, "design_has_streaming_tick_helper", design_has_streaming_tick_helper, True, design_has_streaming_tick_helper)
    add_check(checks, "design_has_message_payload", design_has_message_payload, True, design_has_message_payload)
    add_check(checks, "design_has_safety_chain", design_has_safety_chain, True, design_has_safety_chain)
    add_check(checks, "design_has_stop_conditions", design_has_stop_conditions, True, design_has_stop_conditions)
    add_check(checks, "design_has_runtime_evidence", design_has_runtime_evidence, True, design_has_runtime_evidence)
    add_check(checks, "design_forbids_hardware", design_forbids_hardware, True, design_forbids_hardware)
    add_check(checks, "design_forbids_control_law_change", design_forbids_control_law_change, True, design_forbids_control_law_change)
    add_check(checks, "design_has_abort_conditions", design_has_abort_conditions, True, design_has_abort_conditions)
    add_check(checks, "continuous_torque_streaming_source_patch_design_complete", source_patch_design_complete, True, source_patch_design_complete)
    add_check(checks, "source_unchanged_by_stage1218", source_unchanged_by_stage1218, True, source_unchanged_by_stage1218)

    manual_enable_active = False
    active_ros_publisher_path_exists = gate_status.get("G9", False)
    continuous_torque_streaming_completed = False
    torque_enable_ready = False
    control_law_changed = False
    torque_publisher_enabled = False
    torque_command_published_by_stage1218 = False

    add_check(checks, "manual_enable_active", manual_enable_active, False, not manual_enable_active)
    add_check(checks, "active_ros_publisher_path_exists", active_ros_publisher_path_exists, True, active_ros_publisher_path_exists)
    add_check(checks, "continuous_torque_streaming_completed", continuous_torque_streaming_completed, False, not continuous_torque_streaming_completed)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)
    add_check(checks, "control_law_changed", control_law_changed, False, not control_law_changed)
    add_check(checks, "torque_publisher_enabled", torque_publisher_enabled, False, not torque_publisher_enabled)
    add_check(checks, "torque_command_published_by_stage1218", torque_command_published_by_stage1218, False, not torque_command_published_by_stage1218)

    all_pass = all(row["pass"] for row in checks)

    gate_rows_out = []
    for row in gate_rows:
        gate_rows_out.append(row)

    gate_rows_out.append({
        "gate": "G38",
        "name": "Continuous torque streaming source patch design exists",
        "required_before_torque_publish": True,
        "current_status": source_patch_design_complete,
        "evidence": str(DESIGN_CSV.relative_to(ROOT)),
    })

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(gate_rows_out)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    DOC_PATH.write_text(f"""# Stage 12.18 Continuous Torque Streaming Source Patch Design Only

## 一、结论

Stage 12.18 only designs the future continuous torque streaming source patch.

本阶段不修改 C++ source，不新增 publish call，不创建 continuous streaming timer，不发布连续 torque。

Current source state:

- source_unchanged_by_stage1218: {source_unchanged_by_stage1218}
- publish_call_count: {publish_call_count}
- source_has_no_continuous_streaming_flags: {source_has_no_continuous_streaming_flags}
- source_has_no_continuous_streaming_timer: {source_has_no_continuous_streaming_timer}

## 二、Future patch design

Design CSV:

    results/logs_sample/stage12_continuous_torque_streaming_source_patch_design.csv

Future patch constraints:

- add two continuous streaming params, default false;
- require four-flag gate before streaming;
- add cancellable continuous_torque_streaming_timer_;
- initial rate <= 10 Hz;
- initial duration <= 3 seconds or <= 30 ticks;
- reuse existing single safe publish call path; source publish call count should remain 1;
- payload length 12, finite, zero/safe dry-run first;
- watchdog and clamp every tick;
- cancel timer after tick limit, flag revert, stale watchdog, invalid payload, or shutdown;
- collect runtime evidence: bounded message count and no messages after stop;
- no hardware deployment;
- no control law, estimator, MPC, WBC, or gait changes.

## 三、Safety gate after Stage 12.18

新增：

- G38 continuous torque streaming source patch design exists: {source_patch_design_complete}

Key gates:

- G37 continuous torque streaming preflight freeze passed: {gate_status.get("G37")}
- G36 continuous torque streaming design exists: {gate_status.get("G36")}
- G9 active ROS publisher path exists: {active_ros_publisher_path_exists}

Therefore:

    torque_enable_ready = {torque_enable_ready}

## 四、边界

当前 baseline 仍是 mixed_online_control_baseline。

Stage 12.18 没有完成：

- continuous torque streaming；
- torque streaming controller；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。
""")

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 12.18"])
        writer.writerow(["test_name", "continuous_torque_streaming_source_patch_design_only"])
        writer.writerow(["stage1217_pass", stage1217_pass])
        writer.writerow(["stage1217_continuous_torque_streaming_preflight_frozen", stage1217_preflight_frozen])
        writer.writerow(["stage1217_source_no_streaming_flags", stage1217_source_no_streaming_flags])
        writer.writerow(["stage1217_source_no_streaming_timer", stage1217_source_no_streaming_timer])
        writer.writerow(["stage1217_publish_call_count_one", stage1217_publish_count_one])
        writer.writerow(["source_hash_before", source_hash_before])
        writer.writerow(["source_hash_after", source_hash_after])
        writer.writerow(["source_unchanged_by_stage1218", source_unchanged_by_stage1218])
        writer.writerow(["publish_call_count", publish_call_count])
        writer.writerow(["source_has_exactly_one_publish_call", source_has_exactly_one_publish_call])
        writer.writerow(["source_has_delayed_one_shot_timer", source_has_delayed_one_shot_timer])
        writer.writerow(["source_has_timer_member", source_has_timer_member])
        writer.writerow(["source_timer_cancels_itself", source_timer_cancels_itself])
        writer.writerow(["source_has_zero_safe_message_helper", source_has_zero_safe_message_helper])
        writer.writerow(["source_uses_zero_safe_message_helper", source_uses_zero_safe_message_helper])
        writer.writerow(["source_has_stage1214_marker", source_has_stage1214_marker])
        writer.writerow(["source_has_stage124_marker", source_has_stage124_marker])
        writer.writerow(["source_references_torque_topic", source_references_torque_topic])
        writer.writerow(["source_has_active_publisher_member", source_has_active_publisher_member])
        writer.writerow(["source_has_no_continuous_streaming_flags", source_has_no_continuous_streaming_flags])
        writer.writerow(["source_has_no_continuous_streaming_timer", source_has_no_continuous_streaming_timer])
        writer.writerow(["continuous_torque_streaming_source_patch_design_exists", design_exists])
        writer.writerow(["design_all_items_not_applied", design_all_not_applied])
        writer.writerow(["design_has_patch_target", design_has_patch_target])
        writer.writerow(["design_has_stage_marker", design_has_stage_marker])
        writer.writerow(["design_has_continuous_params", design_has_continuous_params])
        writer.writerow(["design_has_four_flag_gate", design_has_four_flag_gate])
        writer.writerow(["design_has_timer_member", design_has_timer_member])
        writer.writerow(["design_has_timer_rate", design_has_timer_rate])
        writer.writerow(["design_has_duration_limit", design_has_duration_limit])
        writer.writerow(["design_reuses_single_publish_call", design_reuses_single_publish_call])
        writer.writerow(["design_has_streaming_tick_helper", design_has_streaming_tick_helper])
        writer.writerow(["design_has_message_payload", design_has_message_payload])
        writer.writerow(["design_has_safety_chain", design_has_safety_chain])
        writer.writerow(["design_has_stop_conditions", design_has_stop_conditions])
        writer.writerow(["design_has_runtime_evidence", design_has_runtime_evidence])
        writer.writerow(["design_forbids_hardware", design_forbids_hardware])
        writer.writerow(["design_forbids_control_law_change", design_forbids_control_law_change])
        writer.writerow(["design_has_abort_conditions", design_has_abort_conditions])
        writer.writerow(["continuous_torque_streaming_source_patch_design_complete", source_patch_design_complete])
        writer.writerow(["manual_enable_active", manual_enable_active])
        writer.writerow(["active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g37_continuous_torque_streaming_preflight_freeze_passed", gate_status.get("G37", False)])
        writer.writerow(["g38_continuous_torque_streaming_source_patch_design_exists", source_patch_design_complete])
        writer.writerow(["continuous_torque_streaming_completed", continuous_torque_streaming_completed])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", control_law_changed])
        writer.writerow(["torque_publisher_enabled", torque_publisher_enabled])
        writer.writerow(["torque_command_published_by_stage1218", torque_command_published_by_stage1218])
        writer.writerow(["stage12_scope", "continuous_torque_streaming_source_patch_design_only"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["ros2_cpp_realtime_controller_completed", False])
        writer.writerow(["pure_wbc_locomotion_completed", False])
        writer.writerow(["ekf_completed", False])
        writer.writerow(["full_3d_centroidal_mpc_completed", False])
        writer.writerow(["hardware_deployment_completed", False])
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
## Stage 12.18 Continuous Torque Streaming Source Patch Design Only

Stage 12.18 完成 continuous torque streaming source patch design only。

- Script: `scripts/stage12_continuous_torque_streaming_source_patch_design_only.py`
- Design: `results/logs_sample/stage12_continuous_torque_streaming_source_patch_design.csv`
- Summary: `results/logs_sample/stage12_continuous_torque_streaming_source_patch_design_summary.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1218.csv`
- pass: `{all_pass}`
- continuous_torque_streaming_source_patch_design_complete: `{source_patch_design_complete}`
- source_unchanged_by_stage1218: `{source_unchanged_by_stage1218}`
- publish_call_count: `{publish_call_count}`
- continuous_torque_streaming_completed: `{continuous_torque_streaming_completed}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `{torque_publisher_enabled}`
- torque_command_published_by_stage1218: `{torque_command_published_by_stage1218}`
- control_law_changed: `{control_law_changed}`

Stage 12.18 只设计连续 streaming source patch，不实现连续 streaming，不改变控制律，不部署硬件。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 12.18 Continuous Torque Streaming Source Patch Design Only"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 12.18] continuous torque streaming source patch design only")
    print(f"pass={all_pass}")
    print(f"stage1217_pass={stage1217_pass}")
    print(f"source_unchanged_by_stage1218={source_unchanged_by_stage1218}")
    print(f"publish_call_count={publish_call_count}")
    print(f"source_has_no_continuous_streaming_flags={source_has_no_continuous_streaming_flags}")
    print(f"source_has_no_continuous_streaming_timer={source_has_no_continuous_streaming_timer}")
    print(f"continuous_torque_streaming_source_patch_design_complete={source_patch_design_complete}")
    print(f"continuous_torque_streaming_completed={continuous_torque_streaming_completed}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print(f"control_law_changed={control_law_changed}")
    print(f"torque_publisher_enabled={torque_publisher_enabled}")
    print(f"torque_command_published_by_stage1218={torque_command_published_by_stage1218}")
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
