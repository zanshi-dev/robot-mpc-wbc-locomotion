#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE1215_SUMMARY = LOG_DIR / "stage12_bounded_one_shot_publish_call_freeze_regression_summary.csv"
STAGE1215_GATE = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage1215.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"

DESIGN_CSV = LOG_DIR / "stage12_continuous_torque_streaming_design.csv"
LOG_PATH = LOG_DIR / "stage12_continuous_torque_streaming_design_log.csv"
SUMMARY_PATH = LOG_DIR / "stage12_continuous_torque_streaming_design_summary.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage1216.csv"
DOC_PATH = ROOT / "docs/STAGE12_CONTINUOUS_TORQUE_STREAMING_DESIGN_ONLY.md"

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

    s1215 = load_summary(STAGE1215_SUMMARY)
    stage1215_pass = as_bool(s1215.get("pass", "False"))
    freeze_regression_passed = as_bool(s1215.get("bounded_one_shot_publish_call_freeze_regression_passed", "False"))
    default_disabled_passed = as_bool(s1215.get("default_disabled_regression_passed", "False"))
    enabled_bounded_passed = as_bool(s1215.get("enabled_bounded_publish_regression_passed", "False"))
    previous_no_streaming = not as_bool(s1215.get("continuous_torque_streaming_enabled", "True"))
    previous_publish_count_one = str(s1215.get("publish_call_count", "")) == "1"
    previous_source_unchanged = as_bool(s1215.get("source_unchanged_by_stage1215", "False"))
    previous_torque_ready = as_bool(s1215.get("torque_enable_ready", "True"))
    previous_torque_enabled = as_bool(s1215.get("torque_publisher_enabled", "True"))
    previous_control_changed = as_bool(s1215.get("control_law_changed", "True"))

    add_check(checks, "stage1215_summary_exists", STAGE1215_SUMMARY.exists(), True, STAGE1215_SUMMARY.exists(), str(STAGE1215_SUMMARY))
    add_check(checks, "stage1215_pass", stage1215_pass, True, stage1215_pass)
    add_check(checks, "stage1215_freeze_regression_passed", freeze_regression_passed, True, freeze_regression_passed)
    add_check(checks, "stage1215_default_disabled_regression_passed", default_disabled_passed, True, default_disabled_passed)
    add_check(checks, "stage1215_enabled_bounded_publish_regression_passed", enabled_bounded_passed, True, enabled_bounded_passed)
    add_check(checks, "stage1215_no_continuous_streaming", previous_no_streaming, True, previous_no_streaming)
    add_check(checks, "stage1215_publish_call_count_one", previous_publish_count_one, True, previous_publish_count_one)
    add_check(checks, "stage1215_source_unchanged", previous_source_unchanged, True, previous_source_unchanged)
    add_check(checks, "stage1215_torque_enable_ready", previous_torque_ready, False, not previous_torque_ready)
    add_check(checks, "stage1215_torque_publisher_enabled", previous_torque_enabled, False, not previous_torque_enabled)
    add_check(checks, "stage1215_control_law_changed", previous_control_changed, False, not previous_control_changed)

    gate_rows = load_dicts(STAGE1215_GATE)
    gate_status = {
        row.get("gate", ""): as_bool(row.get("current_status", "False"))
        for row in gate_rows
    }

    expected_gate_status = {
        "G3": False,
        "G8": False,
        "G9": True,
        "G32": True,
        "G34": True,
        "G35": True,
    }

    add_check(checks, "stage1215_gate_exists", STAGE1215_GATE.exists(), True, STAGE1215_GATE.exists(), str(STAGE1215_GATE))
    for gate, expected in expected_gate_status.items():
        value = gate_status.get(gate, None)
        add_check(checks, f"{gate}_status_after_stage1215", value, expected, value == expected)

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

    design_rows = [
        {
            "item": "stage12_scope",
            "value": "continuous_torque_streaming_design_only",
            "implemented_in_stage1216": False,
            "allowed_in_future_streaming_stage": True,
            "guard": "Stage 12.16 must not edit C++ source and must not add publish calls",
            "description": "Only records the future continuous torque streaming protocol.",
        },
        {
            "item": "future_continuous_streaming_flags",
            "value": "enable_continuous_torque_streaming=false; confirm_continuous_torque_streaming=false by default",
            "implemented_in_stage1216": False,
            "allowed_in_future_streaming_stage": True,
            "guard": "continuous streaming requires a separate two-flag confirmation",
            "description": "Do not reuse one-shot enable as continuous streaming authorization.",
        },
        {
            "item": "future_rate_limit",
            "value": "initial continuous dry-run rate <= 10 Hz; later rates require separate stage",
            "implemented_in_stage1216": False,
            "allowed_in_future_streaming_stage": True,
            "guard": "no high-rate streaming in first continuous design implementation",
            "description": "Future continuous mode must be rate-limited.",
        },
        {
            "item": "future_duration_limit",
            "value": "initial continuous dry-run duration <= 3 seconds",
            "implemented_in_stage1216": False,
            "allowed_in_future_streaming_stage": True,
            "guard": "unbounded streaming forbidden",
            "description": "Future test must be finite-duration.",
        },
        {
            "item": "future_payload_contract",
            "value": "Float64MultiArray length=12; all finite; zero/safe torque first; Go1 order FR,FL,RR,RL hip,thigh,calf",
            "implemented_in_stage1216": False,
            "allowed_in_future_streaming_stage": True,
            "guard": "invalid payload aborts streaming before publish",
            "description": "Future continuous payload contract.",
        },
        {
            "item": "future_safety_chain",
            "value": "watchdogFallbackZeroTorque then clampTorqueCommand before every publish",
            "implemented_in_stage1216": False,
            "allowed_in_future_streaming_stage": True,
            "guard": "no raw unclamped torque may be streamed",
            "description": "Future safety processing on every cycle.",
        },
        {
            "item": "future_watchdog",
            "value": "inputs must remain fresh; stale inputs force zero/safe output or stop streaming",
            "implemented_in_stage1216": False,
            "allowed_in_future_streaming_stage": True,
            "guard": "watchdog violation must fail closed",
            "description": "Future runtime watchdog policy.",
        },
        {
            "item": "future_start_stop_protocol",
            "value": "start only after two flags true; stop by reverting confirm then enable; timer cancelled on stop",
            "implemented_in_stage1216": False,
            "allowed_in_future_streaming_stage": True,
            "guard": "streaming timer must not survive flag revert",
            "description": "Future lifecycle rule.",
        },
        {
            "item": "future_runtime_evidence",
            "value": "topic echo message count equals bounded duration/rate; payload length=12; finite; zero/safe; no messages after stop",
            "implemented_in_stage1216": False,
            "allowed_in_future_streaming_stage": True,
            "guard": "missing runtime evidence aborts future streaming stage",
            "description": "Evidence required for future continuous dry-run.",
        },
        {
            "item": "future_no_hardware_rule",
            "value": "simulation/ROS topic dry-run only; no hardware deployment",
            "implemented_in_stage1216": False,
            "allowed_in_future_streaming_stage": True,
            "guard": "hardware interface remains out of scope",
            "description": "Future streaming test stays off hardware.",
        },
        {
            "item": "future_no_control_law_change_rule",
            "value": "do not modify estimator, MPC, WBC, gait, or baseline control computation",
            "implemented_in_stage1216": False,
            "allowed_in_future_streaming_stage": True,
            "guard": "future diff limited to streaming output path and guards",
            "description": "Continuous streaming is output plumbing, not controller completion.",
        },
        {
            "item": "future_abort_conditions",
            "value": "unexpected publish count; timer not cancellable; param set failure; invalid payload; unexpected message count; controller exits",
            "implemented_in_stage1216": False,
            "allowed_in_future_streaming_stage": True,
            "guard": "future streaming script must fail closed",
            "description": "Abort policy for future continuous streaming stage.",
        },
    ]

    with DESIGN_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "item",
                "value",
                "implemented_in_stage1216",
                "allowed_in_future_streaming_stage",
                "guard",
                "description",
            ],
        )
        writer.writeheader()
        writer.writerows(design_rows)

    design_exists = DESIGN_CSV.exists()
    design_all_not_implemented = all(not row["implemented_in_stage1216"] for row in design_rows)
    design_has_manual_flags = any(row["item"] == "future_continuous_streaming_flags" for row in design_rows)
    design_has_rate_limit = any(row["item"] == "future_rate_limit" for row in design_rows)
    design_has_duration_limit = any(row["item"] == "future_duration_limit" for row in design_rows)
    design_has_payload_contract = any(row["item"] == "future_payload_contract" for row in design_rows)
    design_has_safety_chain = any(row["item"] == "future_safety_chain" for row in design_rows)
    design_has_watchdog = any(row["item"] == "future_watchdog" for row in design_rows)
    design_has_start_stop = any(row["item"] == "future_start_stop_protocol" for row in design_rows)
    design_has_runtime_evidence = any(row["item"] == "future_runtime_evidence" for row in design_rows)
    design_forbids_hardware = any(row["item"] == "future_no_hardware_rule" for row in design_rows)
    design_forbids_control_law_change = any(row["item"] == "future_no_control_law_change_rule" for row in design_rows)
    design_has_abort_conditions = any(row["item"] == "future_abort_conditions" for row in design_rows)

    source_after = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    source_hash_after = sha256_text(source_after)
    source_unchanged_by_stage1216 = source_hash_before == source_hash_after

    continuous_torque_streaming_design_complete = (
        design_exists and
        design_all_not_implemented and
        design_has_manual_flags and
        design_has_rate_limit and
        design_has_duration_limit and
        design_has_payload_contract and
        design_has_safety_chain and
        design_has_watchdog and
        design_has_start_stop and
        design_has_runtime_evidence and
        design_forbids_hardware and
        design_forbids_control_law_change and
        design_has_abort_conditions
    )

    add_check(checks, "continuous_torque_streaming_design_exists", design_exists, True, design_exists, str(DESIGN_CSV))
    add_check(checks, "design_all_items_not_implemented", design_all_not_implemented, True, design_all_not_implemented)
    add_check(checks, "design_has_manual_flags", design_has_manual_flags, True, design_has_manual_flags)
    add_check(checks, "design_has_rate_limit", design_has_rate_limit, True, design_has_rate_limit)
    add_check(checks, "design_has_duration_limit", design_has_duration_limit, True, design_has_duration_limit)
    add_check(checks, "design_has_payload_contract", design_has_payload_contract, True, design_has_payload_contract)
    add_check(checks, "design_has_safety_chain", design_has_safety_chain, True, design_has_safety_chain)
    add_check(checks, "design_has_watchdog", design_has_watchdog, True, design_has_watchdog)
    add_check(checks, "design_has_start_stop", design_has_start_stop, True, design_has_start_stop)
    add_check(checks, "design_has_runtime_evidence", design_has_runtime_evidence, True, design_has_runtime_evidence)
    add_check(checks, "design_forbids_hardware", design_forbids_hardware, True, design_forbids_hardware)
    add_check(checks, "design_forbids_control_law_change", design_forbids_control_law_change, True, design_forbids_control_law_change)
    add_check(checks, "design_has_abort_conditions", design_has_abort_conditions, True, design_has_abort_conditions)
    add_check(checks, "continuous_torque_streaming_design_complete", continuous_torque_streaming_design_complete, True, continuous_torque_streaming_design_complete)
    add_check(checks, "source_unchanged_by_stage1216", source_unchanged_by_stage1216, True, source_unchanged_by_stage1216)

    manual_enable_active = False
    active_ros_publisher_path_exists = gate_status.get("G9", False)
    continuous_torque_streaming_completed = False
    torque_enable_ready = False
    control_law_changed = False
    torque_publisher_enabled = False
    torque_command_published_by_stage1216 = False

    gate_rows_out = []
    for row in gate_rows:
        gate_rows_out.append(row)

    gate_rows_out.append({
        "gate": "G36",
        "name": "Continuous torque streaming design exists",
        "required_before_torque_publish": True,
        "current_status": continuous_torque_streaming_design_complete,
        "evidence": str(DESIGN_CSV.relative_to(ROOT)),
    })

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(gate_rows_out)

    add_check(checks, "manual_enable_active", manual_enable_active, False, not manual_enable_active)
    add_check(checks, "active_ros_publisher_path_exists", active_ros_publisher_path_exists, True, active_ros_publisher_path_exists)
    add_check(checks, "continuous_torque_streaming_completed", continuous_torque_streaming_completed, False, not continuous_torque_streaming_completed)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)
    add_check(checks, "control_law_changed", control_law_changed, False, not control_law_changed)
    add_check(checks, "torque_publisher_enabled", torque_publisher_enabled, False, not torque_publisher_enabled)
    add_check(checks, "torque_command_published_by_stage1216", torque_command_published_by_stage1216, False, not torque_command_published_by_stage1216)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    DOC_PATH.write_text(f"""# Stage 12.16 Continuous Torque Streaming Design Only

## 一、结论

Stage 12.16 只设计 future continuous torque streaming protocol。

本阶段不修改 C++ source，不新增 publish call，不启动连续 torque streaming。

Current source state:

- publish_call_count: {publish_call_count}
- source_has_delayed_one_shot_timer: {source_has_delayed_one_shot_timer}
- source_has_zero_safe_message_helper: {source_has_zero_safe_message_helper}
- source_unchanged_by_stage1216: {source_unchanged_by_stage1216}

## 二、前置状态

Stage 12.15:

- pass: {stage1215_pass}
- bounded_one_shot_publish_call_freeze_regression_passed: {freeze_regression_passed}
- default_disabled_regression_passed: {default_disabled_passed}
- enabled_bounded_publish_regression_passed: {enabled_bounded_passed}
- previous_no_continuous_streaming: {previous_no_streaming}

## 三、Continuous streaming design

Design CSV:

    results/logs_sample/stage12_continuous_torque_streaming_design.csv

Future protocol:

- separate two-flag confirmation for continuous streaming;
- initial dry-run rate <= 10 Hz;
- initial dry-run duration <= 3 seconds;
- payload length 12, finite, zero/safe first;
- watchdog and clamp on every cycle;
- timer must stop after duration and after flag revert;
- no messages after stop;
- no hardware deployment;
- no control law, estimator, MPC, WBC, or gait changes.

## 四、Safety gate after Stage 12.16

新增：

- G36 continuous torque streaming design exists: {continuous_torque_streaming_design_complete}

Key gates:

- G3 no publish call: {gate_status.get("G3")}
- G8 manual enable active after revert: {manual_enable_active}
- G9 active ROS publisher path exists: {active_ros_publisher_path_exists}
- G35 bounded one-shot freeze and regression passed: {gate_status.get("G35")}

Therefore:

    torque_enable_ready = {torque_enable_ready}

## 五、边界

当前 baseline 仍是 mixed_online_control_baseline。

Stage 12.16 没有完成：

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
        writer.writerow(["stage", "Stage 12.16"])
        writer.writerow(["test_name", "continuous_torque_streaming_design_only"])
        writer.writerow(["stage1215_pass", stage1215_pass])
        writer.writerow(["stage1215_freeze_regression_passed", freeze_regression_passed])
        writer.writerow(["stage1215_default_disabled_regression_passed", default_disabled_passed])
        writer.writerow(["stage1215_enabled_bounded_publish_regression_passed", enabled_bounded_passed])
        writer.writerow(["stage1215_no_continuous_streaming", previous_no_streaming])
        writer.writerow(["source_hash_before", source_hash_before])
        writer.writerow(["source_hash_after", source_hash_after])
        writer.writerow(["source_unchanged_by_stage1216", source_unchanged_by_stage1216])
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
        writer.writerow(["continuous_torque_streaming_design_exists", design_exists])
        writer.writerow(["design_all_items_not_implemented", design_all_not_implemented])
        writer.writerow(["design_has_manual_flags", design_has_manual_flags])
        writer.writerow(["design_has_rate_limit", design_has_rate_limit])
        writer.writerow(["design_has_duration_limit", design_has_duration_limit])
        writer.writerow(["design_has_payload_contract", design_has_payload_contract])
        writer.writerow(["design_has_safety_chain", design_has_safety_chain])
        writer.writerow(["design_has_watchdog", design_has_watchdog])
        writer.writerow(["design_has_start_stop", design_has_start_stop])
        writer.writerow(["design_has_runtime_evidence", design_has_runtime_evidence])
        writer.writerow(["design_forbids_hardware", design_forbids_hardware])
        writer.writerow(["design_forbids_control_law_change", design_forbids_control_law_change])
        writer.writerow(["design_has_abort_conditions", design_has_abort_conditions])
        writer.writerow(["continuous_torque_streaming_design_complete", continuous_torque_streaming_design_complete])
        writer.writerow(["manual_enable_active", manual_enable_active])
        writer.writerow(["active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g3_no_publish_call", gate_status.get("G3", False)])
        writer.writerow(["g8_manual_enable_active_after_revert", manual_enable_active])
        writer.writerow(["g9_active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g35_bounded_one_shot_publish_call_freeze_regression_passed", gate_status.get("G35", False)])
        writer.writerow(["g36_continuous_torque_streaming_design_exists", continuous_torque_streaming_design_complete])
        writer.writerow(["continuous_torque_streaming_completed", continuous_torque_streaming_completed])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", control_law_changed])
        writer.writerow(["torque_publisher_enabled", torque_publisher_enabled])
        writer.writerow(["torque_command_published_by_stage1216", torque_command_published_by_stage1216])
        writer.writerow(["stage12_scope", "continuous_torque_streaming_design_only"])
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
## Stage 12.16 Continuous Torque Streaming Design Only

Stage 12.16 完成 continuous torque streaming design only。

- Script: `scripts/stage12_continuous_torque_streaming_design_only.py`
- Design: `results/logs_sample/stage12_continuous_torque_streaming_design.csv`
- Summary: `results/logs_sample/stage12_continuous_torque_streaming_design_summary.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1216.csv`
- pass: `{all_pass}`
- continuous_torque_streaming_design_complete: `{continuous_torque_streaming_design_complete}`
- source_unchanged_by_stage1216: `{source_unchanged_by_stage1216}`
- publish_call_count: `{publish_call_count}`
- continuous_torque_streaming_completed: `{continuous_torque_streaming_completed}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `{torque_publisher_enabled}`
- torque_command_published_by_stage1216: `{torque_command_published_by_stage1216}`
- control_law_changed: `{control_law_changed}`

Stage 12.16 只设计连续 streaming，不实现连续 streaming，不改变控制律，不部署硬件。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 12.16 Continuous Torque Streaming Design Only"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 12.16] continuous torque streaming design only")
    print(f"pass={all_pass}")
    print(f"stage1215_pass={stage1215_pass}")
    print(f"source_unchanged_by_stage1216={source_unchanged_by_stage1216}")
    print(f"publish_call_count={publish_call_count}")
    print(f"source_has_delayed_one_shot_timer={source_has_delayed_one_shot_timer}")
    print(f"continuous_torque_streaming_design_complete={continuous_torque_streaming_design_complete}")
    print(f"continuous_torque_streaming_completed={continuous_torque_streaming_completed}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print(f"control_law_changed={control_law_changed}")
    print(f"torque_publisher_enabled={torque_publisher_enabled}")
    print(f"torque_command_published_by_stage1216={torque_command_published_by_stage1216}")
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
