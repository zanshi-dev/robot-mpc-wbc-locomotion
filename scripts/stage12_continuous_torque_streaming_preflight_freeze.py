#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE1215_SUMMARY = LOG_DIR / "stage12_bounded_one_shot_publish_call_freeze_regression_summary.csv"
STAGE1216_SUMMARY = LOG_DIR / "stage12_continuous_torque_streaming_design_summary.csv"
STAGE1216_GATE = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage1216.csv"
STAGE1216_DESIGN = LOG_DIR / "stage12_continuous_torque_streaming_design.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
SAFETY_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

SUMMARY_PATH = LOG_DIR / "stage12_continuous_torque_streaming_preflight_freeze_summary.csv"
LOG_PATH = LOG_DIR / "stage12_continuous_torque_streaming_preflight_freeze_log.csv"
HASH_PATH = LOG_DIR / "stage12_continuous_torque_streaming_preflight_freeze_hashes.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage1217.csv"
DOC_PATH = ROOT / "docs/STAGE12_CONTINUOUS_TORQUE_STREAMING_PREFLIGHT_FREEZE.md"

TORQUE_TOPIC = "/go1/joint_torque_cmd"

FREEZE_FILES = [
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp",

    "results/logs_sample/stage12_bounded_one_shot_publish_call_freeze_regression_summary.csv",
    "results/logs_sample/stage12_bounded_one_shot_publish_call_freeze_regression_log.csv",
    "results/logs_sample/stage12_bounded_one_shot_publish_call_freeze_regression_hashes.csv",
    "results/logs_sample/stage12_bounded_one_shot_publish_call_freeze_enabled_echo1_stdout.txt",
    "results/logs_sample/stage12_bounded_one_shot_publish_call_freeze_enabled_echo2_stdout.txt",

    "results/logs_sample/stage12_continuous_torque_streaming_design_summary.csv",
    "results/logs_sample/stage12_continuous_torque_streaming_design_log.csv",
    "results/logs_sample/stage12_continuous_torque_streaming_design.csv",

    "results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1215.csv",
    "results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1216.csv",

    "docs/STAGE12_BOUNDED_ONE_SHOT_PUBLISH_CALL_FREEZE_REGRESSION.md",
    "docs/STAGE12_CONTINUOUS_TORQUE_STREAMING_DESIGN_ONLY.md",
]


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


def sha256_file(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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
    s1216 = load_summary(STAGE1216_SUMMARY)

    stage1215_pass = as_bool(s1215.get("pass", "False"))
    stage1215_freeze_regression = as_bool(s1215.get("bounded_one_shot_publish_call_freeze_regression_passed", "False"))
    stage1215_no_streaming = not as_bool(s1215.get("continuous_torque_streaming_enabled", "True"))
    stage1215_publish_count_one = str(s1215.get("publish_call_count", "")) == "1"
    stage1215_torque_ready = as_bool(s1215.get("torque_enable_ready", "True"))
    stage1215_torque_enabled = as_bool(s1215.get("torque_publisher_enabled", "True"))
    stage1215_control_changed = as_bool(s1215.get("control_law_changed", "True"))

    stage1216_pass = as_bool(s1216.get("pass", "False"))
    stage1216_design_complete = as_bool(s1216.get("continuous_torque_streaming_design_complete", "False"))
    stage1216_source_unchanged = as_bool(s1216.get("source_unchanged_by_stage1216", "False"))
    stage1216_no_streaming = not as_bool(s1216.get("continuous_torque_streaming_completed", "True"))
    stage1216_torque_ready = as_bool(s1216.get("torque_enable_ready", "True"))
    stage1216_torque_enabled = as_bool(s1216.get("torque_publisher_enabled", "True"))
    stage1216_control_changed = as_bool(s1216.get("control_law_changed", "True"))
    stage1216_torque_published = as_bool(s1216.get("torque_command_published_by_stage1216", "True"))

    add_check(checks, "stage1215_summary_exists", STAGE1215_SUMMARY.exists(), True, STAGE1215_SUMMARY.exists(), str(STAGE1215_SUMMARY))
    add_check(checks, "stage1215_pass", stage1215_pass, True, stage1215_pass)
    add_check(checks, "stage1215_freeze_regression_passed", stage1215_freeze_regression, True, stage1215_freeze_regression)
    add_check(checks, "stage1215_no_continuous_streaming", stage1215_no_streaming, True, stage1215_no_streaming)
    add_check(checks, "stage1215_publish_count_one", stage1215_publish_count_one, True, stage1215_publish_count_one)
    add_check(checks, "stage1215_torque_enable_ready", stage1215_torque_ready, False, not stage1215_torque_ready)
    add_check(checks, "stage1215_torque_publisher_enabled", stage1215_torque_enabled, False, not stage1215_torque_enabled)
    add_check(checks, "stage1215_control_law_changed", stage1215_control_changed, False, not stage1215_control_changed)

    add_check(checks, "stage1216_summary_exists", STAGE1216_SUMMARY.exists(), True, STAGE1216_SUMMARY.exists(), str(STAGE1216_SUMMARY))
    add_check(checks, "stage1216_pass", stage1216_pass, True, stage1216_pass)
    add_check(checks, "stage1216_design_complete", stage1216_design_complete, True, stage1216_design_complete)
    add_check(checks, "stage1216_source_unchanged", stage1216_source_unchanged, True, stage1216_source_unchanged)
    add_check(checks, "stage1216_continuous_streaming_completed", stage1216_no_streaming, True, stage1216_no_streaming)
    add_check(checks, "stage1216_torque_enable_ready", stage1216_torque_ready, False, not stage1216_torque_ready)
    add_check(checks, "stage1216_torque_publisher_enabled", stage1216_torque_enabled, False, not stage1216_torque_enabled)
    add_check(checks, "stage1216_control_law_changed", stage1216_control_changed, False, not stage1216_control_changed)
    add_check(checks, "stage1216_torque_command_published", stage1216_torque_published, False, not stage1216_torque_published)

    design_rows = load_dicts(STAGE1216_DESIGN)
    design_all_not_implemented = all(not as_bool(row.get("implemented_in_stage1216", "True")) for row in design_rows)
    design_has_manual_flags = any(row.get("item") == "future_continuous_streaming_flags" for row in design_rows)
    design_has_rate_limit = any(row.get("item") == "future_rate_limit" for row in design_rows)
    design_has_duration_limit = any(row.get("item") == "future_duration_limit" for row in design_rows)
    design_has_payload_contract = any(row.get("item") == "future_payload_contract" for row in design_rows)
    design_has_safety_chain = any(row.get("item") == "future_safety_chain" for row in design_rows)
    design_has_watchdog = any(row.get("item") == "future_watchdog" for row in design_rows)
    design_has_start_stop = any(row.get("item") == "future_start_stop_protocol" for row in design_rows)
    design_has_runtime_evidence = any(row.get("item") == "future_runtime_evidence" for row in design_rows)
    design_forbids_hardware = any(row.get("item") == "future_no_hardware_rule" for row in design_rows)
    design_forbids_control_law_change = any(row.get("item") == "future_no_control_law_change_rule" for row in design_rows)
    design_has_abort_conditions = any(row.get("item") == "future_abort_conditions" for row in design_rows)

    add_check(checks, "stage1216_design_csv_exists", STAGE1216_DESIGN.exists(), True, STAGE1216_DESIGN.exists(), str(STAGE1216_DESIGN))
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

    gate_rows = load_dicts(STAGE1216_GATE)
    gate_status = {row.get("gate", ""): as_bool(row.get("current_status", "False")) for row in gate_rows}

    expected_gate_status = {
        "G3": False,
        "G8": False,
        "G9": True,
        "G32": True,
        "G34": True,
        "G35": True,
        "G36": True,
    }

    add_check(checks, "stage1216_gate_exists", STAGE1216_GATE.exists(), True, STAGE1216_GATE.exists(), str(STAGE1216_GATE))
    for gate, expected in expected_gate_status.items():
        value = gate_status.get(gate, None)
        add_check(checks, f"{gate}_status_after_stage1216", value, expected, value == expected)

    source_text = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    source_hash_current = sha256_text(source_text)

    publish_call_count = count_publish_calls(source_text)
    source_has_exactly_one_publish_call = publish_call_count == 1
    source_has_delayed_one_shot_timer = (
        "stage1214_one_shot_publish_timer_ = this->create_wall_timer" in source_text and
        "std::chrono::milliseconds(2500)" in source_text
    )
    source_has_timer_member = "rclcpp::TimerBase::SharedPtr stage1214_one_shot_publish_timer_" in source_text
    source_timer_cancels_itself = "stage1214_one_shot_publish_timer_->cancel()" in source_text
    source_has_zero_safe_message_helper = "makeStage1214ZeroSafeTorqueCommandMessage" in source_text
    source_uses_zero_safe_message_helper = "auto msg = makeStage1214ZeroSafeTorqueCommandMessage();" in source_text
    source_has_stage1214_marker = (
        "kStage1214BoundedPublishCallImplemented = true" in source_text and
        "kStage1214ContinuousPublishImplemented = false" in source_text
    )
    source_has_stage124_marker = (
        "kStage124PublisherConstructionImplemented" in source_text and
        "kStage124PublishCallImplemented = false" in source_text
    )
    source_references_torque_topic = TORQUE_TOPIC in source_text
    source_has_active_publisher_member = "active_torque_cmd_publisher_" in source_text

    stage1216_source_hash_after = s1216.get("source_hash_after", "")
    source_matches_stage1216_hash = bool(stage1216_source_hash_after) and source_hash_current == stage1216_source_hash_after

    source_has_no_continuous_streaming_flags = (
        "enable_continuous_torque_streaming" not in source_text and
        "confirm_continuous_torque_streaming" not in source_text
    )
    source_has_no_continuous_streaming_timer = (
        "continuous_torque_streaming_timer_" not in source_text and
        "continuousTorqueStreaming" not in source_text
    )

    add_check(checks, "cpp_source_exists", CPP_SOURCE.exists(), True, CPP_SOURCE.exists(), str(CPP_SOURCE))
    add_check(checks, "source_matches_stage1216_hash", source_matches_stage1216_hash, True, source_matches_stage1216_hash)
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

    safety_text = SAFETY_HEADER.read_text(errors="replace") if SAFETY_HEADER.exists() else ""
    zero_text = ZERO_HEADER.read_text(errors="replace") if ZERO_HEADER.exists() else ""

    safety_header_has_clamp_watchdog = (
        "clampTorqueCommand" in safety_text and
        "watchdogFallbackZeroTorque" in safety_text and
        "allInputsFresh" in safety_text
    )
    zero_header_declares_12 = "kGo1NumActuatedJoints = 12" in zero_text

    add_check(checks, "safety_header_has_clamp_watchdog", safety_header_has_clamp_watchdog, True, safety_header_has_clamp_watchdog)
    add_check(checks, "zero_header_declares_12", zero_header_declares_12, True, zero_header_declares_12)

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

    with HASH_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "exists", "sha256", "size_bytes"])
        writer.writeheader()
        writer.writerows(hash_rows)

    add_check(checks, "missing_freeze_file_count", len(missing_files), 0, len(missing_files) == 0)

    continuous_torque_streaming_preflight_frozen = (
        stage1215_pass and
        stage1215_freeze_regression and
        stage1215_no_streaming and
        stage1216_pass and
        stage1216_design_complete and
        stage1216_source_unchanged and
        source_matches_stage1216_hash and
        source_has_exactly_one_publish_call and
        source_has_delayed_one_shot_timer and
        source_timer_cancels_itself and
        source_has_zero_safe_message_helper and
        source_uses_zero_safe_message_helper and
        source_has_stage1214_marker and
        source_has_no_continuous_streaming_flags and
        source_has_no_continuous_streaming_timer and
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
        design_has_abort_conditions and
        gate_status.get("G35", False) and
        gate_status.get("G36", False) and
        len(missing_files) == 0
    )

    manual_enable_active = False
    active_ros_publisher_path_exists = gate_status.get("G9", False)
    continuous_torque_streaming_completed = False
    torque_enable_ready = False
    control_law_changed = False
    torque_publisher_enabled = False
    torque_command_published_by_stage1217 = False

    add_check(checks, "continuous_torque_streaming_preflight_frozen", continuous_torque_streaming_preflight_frozen, True, continuous_torque_streaming_preflight_frozen)
    add_check(checks, "manual_enable_active", manual_enable_active, False, not manual_enable_active)
    add_check(checks, "active_ros_publisher_path_exists", active_ros_publisher_path_exists, True, active_ros_publisher_path_exists)
    add_check(checks, "continuous_torque_streaming_completed", continuous_torque_streaming_completed, False, not continuous_torque_streaming_completed)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)
    add_check(checks, "control_law_changed", control_law_changed, False, not control_law_changed)
    add_check(checks, "torque_publisher_enabled", torque_publisher_enabled, False, not torque_publisher_enabled)
    add_check(checks, "torque_command_published_by_stage1217", torque_command_published_by_stage1217, False, not torque_command_published_by_stage1217)

    all_pass = all(row["pass"] for row in checks)

    gate_rows_out = []
    for row in gate_rows:
        gate_rows_out.append(row)

    gate_rows_out.append({
        "gate": "G37",
        "name": "Continuous torque streaming preflight freeze passed",
        "required_before_torque_publish": True,
        "current_status": continuous_torque_streaming_preflight_frozen,
        "evidence": str(LOG_PATH.relative_to(ROOT)),
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

    DOC_PATH.write_text(f"""# Stage 12.17 Continuous Torque Streaming Preflight Freeze

## 一、结论

Stage 12.17 freezes the continuous torque streaming preflight baseline.

本阶段不修改 C++ source，不新增 publish call，不创建 continuous streaming timer，不启动连续 torque streaming。

Current source state:

- source_hash_current: {source_hash_current}
- source_matches_stage1216_hash: {source_matches_stage1216_hash}
- publish_call_count: {publish_call_count}
- source_has_delayed_one_shot_timer: {source_has_delayed_one_shot_timer}
- source_has_no_continuous_streaming_flags: {source_has_no_continuous_streaming_flags}
- source_has_no_continuous_streaming_timer: {source_has_no_continuous_streaming_timer}

## 二、前置状态

Stage 12.15:

- pass: {stage1215_pass}
- bounded one-shot freeze regression passed: {stage1215_freeze_regression}
- no continuous streaming: {stage1215_no_streaming}

Stage 12.16:

- pass: {stage1216_pass}
- continuous streaming design complete: {stage1216_design_complete}
- source unchanged: {stage1216_source_unchanged}

## 三、Design integrity

Design CSV:

    results/logs_sample/stage12_continuous_torque_streaming_design.csv

Checks:

- design_all_items_not_implemented: {design_all_not_implemented}
- design_has_manual_flags: {design_has_manual_flags}
- design_has_rate_limit: {design_has_rate_limit}
- design_has_duration_limit: {design_has_duration_limit}
- design_has_payload_contract: {design_has_payload_contract}
- design_has_safety_chain: {design_has_safety_chain}
- design_has_watchdog: {design_has_watchdog}
- design_has_start_stop: {design_has_start_stop}
- design_has_runtime_evidence: {design_has_runtime_evidence}
- design_forbids_hardware: {design_forbids_hardware}
- design_forbids_control_law_change: {design_forbids_control_law_change}
- design_has_abort_conditions: {design_has_abort_conditions}

## 四、Safety gate after Stage 12.17

新增：

- G37 continuous torque streaming preflight freeze passed: {continuous_torque_streaming_preflight_frozen}

Key gates:

- G35 bounded one-shot freeze and regression passed: {gate_status.get("G35")}
- G36 continuous torque streaming design exists: {gate_status.get("G36")}
- G9 active ROS publisher path exists: {active_ros_publisher_path_exists}

Therefore:

    torque_enable_ready = {torque_enable_ready}

## 五、边界

当前 baseline 仍是 mixed_online_control_baseline。

Stage 12.17 没有完成：

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
        writer.writerow(["stage", "Stage 12.17"])
        writer.writerow(["test_name", "continuous_torque_streaming_preflight_freeze"])
        writer.writerow(["stage1215_pass", stage1215_pass])
        writer.writerow(["stage1215_freeze_regression_passed", stage1215_freeze_regression])
        writer.writerow(["stage1215_no_continuous_streaming", stage1215_no_streaming])
        writer.writerow(["stage1216_pass", stage1216_pass])
        writer.writerow(["stage1216_continuous_torque_streaming_design_complete", stage1216_design_complete])
        writer.writerow(["stage1216_source_unchanged", stage1216_source_unchanged])
        writer.writerow(["freeze_file_count", len(FREEZE_FILES)])
        writer.writerow(["missing_file_count", len(missing_files)])
        writer.writerow(["source_hash_current", source_hash_current])
        writer.writerow(["source_matches_stage1216_hash", source_matches_stage1216_hash])
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
        writer.writerow(["safety_header_has_clamp_watchdog", safety_header_has_clamp_watchdog])
        writer.writerow(["zero_header_declares_12", zero_header_declares_12])
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
        writer.writerow(["continuous_torque_streaming_preflight_frozen", continuous_torque_streaming_preflight_frozen])
        writer.writerow(["manual_enable_active", manual_enable_active])
        writer.writerow(["active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g35_bounded_one_shot_publish_call_freeze_regression_passed", gate_status.get("G35", False)])
        writer.writerow(["g36_continuous_torque_streaming_design_exists", gate_status.get("G36", False)])
        writer.writerow(["g37_continuous_torque_streaming_preflight_freeze_passed", continuous_torque_streaming_preflight_frozen])
        writer.writerow(["continuous_torque_streaming_completed", continuous_torque_streaming_completed])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", control_law_changed])
        writer.writerow(["torque_publisher_enabled", torque_publisher_enabled])
        writer.writerow(["torque_command_published_by_stage1217", torque_command_published_by_stage1217])
        writer.writerow(["stage12_scope", "continuous_torque_streaming_preflight_freeze_only"])
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
        writer.writerow(["hash_csv", str(HASH_PATH.relative_to(ROOT))])
        writer.writerow(["safety_gate_csv", str(SAFETY_GATE_PATH.relative_to(ROOT))])
        writer.writerow(["summary_csv", str(SUMMARY_PATH.relative_to(ROOT))])
        writer.writerow(["doc", str(DOC_PATH.relative_to(ROOT))])

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 12.17 Continuous Torque Streaming Preflight Freeze

Stage 12.17 冻结 continuous torque streaming preflight baseline。

- Script: `scripts/stage12_continuous_torque_streaming_preflight_freeze.py`
- Log: `results/logs_sample/stage12_continuous_torque_streaming_preflight_freeze_log.csv`
- Hashes: `results/logs_sample/stage12_continuous_torque_streaming_preflight_freeze_hashes.csv`
- Summary: `results/logs_sample/stage12_continuous_torque_streaming_preflight_freeze_summary.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1217.csv`
- pass: `{all_pass}`
- continuous_torque_streaming_preflight_frozen: `{continuous_torque_streaming_preflight_frozen}`
- publish_call_count: `{publish_call_count}`
- source_has_no_continuous_streaming_flags: `{source_has_no_continuous_streaming_flags}`
- source_has_no_continuous_streaming_timer: `{source_has_no_continuous_streaming_timer}`
- continuous_torque_streaming_completed: `{continuous_torque_streaming_completed}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `{torque_publisher_enabled}`
- torque_command_published_by_stage1217: `{torque_command_published_by_stage1217}`
- control_law_changed: `{control_law_changed}`

Stage 12.17 不实现连续 streaming，不改变控制律，不部署硬件。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 12.17 Continuous Torque Streaming Preflight Freeze"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 12.17] continuous torque streaming preflight freeze")
    print(f"pass={all_pass}")
    print(f"stage1215_pass={stage1215_pass}")
    print(f"stage1216_pass={stage1216_pass}")
    print(f"missing_file_count={len(missing_files)}")
    print(f"source_matches_stage1216_hash={source_matches_stage1216_hash}")
    print(f"publish_call_count={publish_call_count}")
    print(f"source_has_no_continuous_streaming_flags={source_has_no_continuous_streaming_flags}")
    print(f"source_has_no_continuous_streaming_timer={source_has_no_continuous_streaming_timer}")
    print(f"continuous_torque_streaming_preflight_frozen={continuous_torque_streaming_preflight_frozen}")
    print(f"continuous_torque_streaming_completed={continuous_torque_streaming_completed}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print(f"control_law_changed={control_law_changed}")
    print(f"torque_publisher_enabled={torque_publisher_enabled}")
    print(f"torque_command_published_by_stage1217={torque_command_published_by_stage1217}")
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
