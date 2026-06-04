#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE_SUMMARIES = {
    "Stage 12.4": LOG_DIR / "stage12_publisher_construction_source_patch_without_publish_summary.csv",
    "Stage 12.5": LOG_DIR / "stage12_publisher_construction_no_publish_freeze_summary.csv",
    "Stage 12.6": LOG_DIR / "stage12_manual_enable_activation_design_summary.csv",
    "Stage 12.7": LOG_DIR / "stage12_manual_enable_runtime_activation_without_publish_summary.csv",
}

FINAL_GATE_IN = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage127.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
SAFETY_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

PARAM_OBS = LOG_DIR / "stage12_manual_enable_runtime_activation_param_observations.csv"
TOPIC_OBS = LOG_DIR / "stage12_manual_enable_runtime_activation_topic_observations.csv"
ECHO_STDOUT = LOG_DIR / "stage12_manual_enable_runtime_activation_topic_echo_stdout.txt"
ECHO_STDERR = LOG_DIR / "stage12_manual_enable_runtime_activation_topic_echo_stderr.txt"

DOC_PATH = ROOT / "docs/STAGE12_MANUAL_ENABLE_NO_PUBLISH_FREEZE.md"
SUMMARY_PATH = LOG_DIR / "stage12_manual_enable_no_publish_freeze_summary.csv"
LOG_PATH = LOG_DIR / "stage12_manual_enable_no_publish_freeze_log.csv"
HASH_PATH = LOG_DIR / "stage12_manual_enable_no_publish_freeze_hashes.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage128.csv"

TORQUE_TOPIC = "/go1/joint_torque_cmd"

FREEZE_FILES = [
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp",

    "docs/STAGE12_PUBLISHER_CONSTRUCTION_SOURCE_PATCH_WITHOUT_PUBLISH.md",
    "docs/STAGE12_PUBLISHER_CONSTRUCTION_NO_PUBLISH_FREEZE.md",
    "docs/STAGE12_MANUAL_ENABLE_ACTIVATION_DESIGN_ONLY.md",
    "docs/STAGE12_MANUAL_ENABLE_RUNTIME_ACTIVATION_WITHOUT_PUBLISH.md",

    "results/logs_sample/stage12_publisher_construction_source_patch_without_publish_summary.csv",
    "results/logs_sample/stage12_publisher_construction_no_publish_freeze_summary.csv",
    "results/logs_sample/stage12_manual_enable_activation_design_summary.csv",
    "results/logs_sample/stage12_manual_enable_runtime_activation_without_publish_summary.csv",

    "results/logs_sample/stage12_publisher_construction_without_publish_topic_observations.csv",
    "results/logs_sample/stage12_manual_enable_runtime_activation_param_observations.csv",
    "results/logs_sample/stage12_manual_enable_runtime_activation_topic_observations.csv",
    "results/logs_sample/stage12_manual_enable_runtime_activation_topic_echo_stdout.txt",
    "results/logs_sample/stage12_manual_enable_runtime_activation_topic_echo_stderr.txt",

    "results/logs_sample/stage12_torque_publisher_safety_gate_after_stage124.csv",
    "results/logs_sample/stage12_torque_publisher_safety_gate_after_stage125.csv",
    "results/logs_sample/stage12_torque_publisher_safety_gate_after_stage126.csv",
    "results/logs_sample/stage12_torque_publisher_safety_gate_after_stage127.csv",
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
    summaries = {}

    for stage, path in STAGE_SUMMARIES.items():
        exists = path.exists()
        add_check(checks, f"{stage}_summary_exists", exists, True, exists, str(path))
        metrics = load_summary(path)
        summaries[stage] = metrics
        stage_pass = as_bool(metrics.get("pass", "False"))
        add_check(checks, f"{stage}_pass", stage_pass, True, stage_pass)

    s124 = summaries["Stage 12.4"]
    s125 = summaries["Stage 12.5"]
    s126 = summaries["Stage 12.6"]
    s127 = summaries["Stage 12.7"]

    add_check(checks, "stage124_publisher_construction_without_publish", as_bool(s124.get("publisher_construction_implemented_without_publish_call", "False")), True, as_bool(s124.get("publisher_construction_implemented_without_publish_call", "False")))
    add_check(checks, "stage125_no_publish_integrity_passed", as_bool(s125.get("publisher_construction_no_publish_integrity_passed", "False")), True, as_bool(s125.get("publisher_construction_no_publish_integrity_passed", "False")))
    add_check(checks, "stage126_manual_enable_design_complete", as_bool(s126.get("manual_enable_activation_design_complete", "False")), True, as_bool(s126.get("manual_enable_activation_design_complete", "False")))
    add_check(checks, "stage127_manual_enable_activation_without_publish_passed", as_bool(s127.get("manual_enable_runtime_activation_without_publish_passed", "False")), True, as_bool(s127.get("manual_enable_runtime_activation_without_publish_passed", "False")))

    required_stage127 = {
        "source_has_create_publisher": True,
        "source_has_publish_call": False,
        "source_references_torque_topic": True,
        "source_has_active_publisher_member": True,
        "source_has_stage124_marker": True,
        "source_unchanged_by_stage127": True,
        "initial_enable_param_false": True,
        "initial_confirm_param_false": True,
        "activated_enable_param_true": True,
        "activated_confirm_param_true": True,
        "manual_enable_active_during_test": True,
        "reverted_enable_param_false": True,
        "reverted_confirm_param_false": True,
        "manual_enable_reverted_false": True,
        "torque_publishers_positive_all_samples": True,
        "no_message_observed_during_activation": True,
        "controller_alive_after_activation": True,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "torque_command_published_by_stage127": False,
        "control_law_changed": False,
    }

    for key, expected in required_stage127.items():
        value = as_bool(s127.get(key, "False"))
        add_check(checks, f"stage127_{key}", value, expected, value == expected)

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

    param_rows = load_dicts(PARAM_OBS)
    topic_rows = load_dicts(TOPIC_OBS)
    echo_stdout = ECHO_STDOUT.read_text(errors="replace") if ECHO_STDOUT.exists() else ""

    initial_enable_false = any(row.get("phase") == "initial" and row.get("param") == "enable_torque_publisher" and row.get("value") == "False" for row in param_rows)
    initial_confirm_false = any(row.get("phase") == "initial" and row.get("param") == "confirm_torque_publisher_enable" and row.get("value") == "False" for row in param_rows)
    activated_enable_true = any(row.get("phase") == "activated" and row.get("param") == "enable_torque_publisher" and row.get("value") == "True" for row in param_rows)
    activated_confirm_true = any(row.get("phase") == "activated" and row.get("param") == "confirm_torque_publisher_enable" and row.get("value") == "True" for row in param_rows)
    reverted_enable_false = any(row.get("phase") == "reverted" and row.get("param") == "enable_torque_publisher" and row.get("value") == "False" for row in param_rows)
    reverted_confirm_false = any(row.get("phase") == "reverted" and row.get("param") == "confirm_torque_publisher_enable" and row.get("value") == "False" for row in param_rows)

    topic_row_count = len(topic_rows)
    topic_rc_all_zero = all(str(row.get("topic_info_returncode", "")) == "0" for row in topic_rows)
    topic_pub_positive_all = all(as_bool(row.get("publisher_count_positive", "False")) for row in topic_rows)
    topic_sub_positive_all = all(as_bool(row.get("subscription_count_positive", "False")) for row in topic_rows)
    activated_topic_rows = [row for row in topic_rows if row.get("phase") == "activated"]

    add_check(checks, "param_observations_exists", PARAM_OBS.exists(), True, PARAM_OBS.exists(), str(PARAM_OBS))
    add_check(checks, "topic_observations_exists", TOPIC_OBS.exists(), True, TOPIC_OBS.exists(), str(TOPIC_OBS))
    add_check(checks, "initial_enable_false_observed", initial_enable_false, True, initial_enable_false)
    add_check(checks, "initial_confirm_false_observed", initial_confirm_false, True, initial_confirm_false)
    add_check(checks, "activated_enable_true_observed", activated_enable_true, True, activated_enable_true)
    add_check(checks, "activated_confirm_true_observed", activated_confirm_true, True, activated_confirm_true)
    add_check(checks, "reverted_enable_false_observed", reverted_enable_false, True, reverted_enable_false)
    add_check(checks, "reverted_confirm_false_observed", reverted_confirm_false, True, reverted_confirm_false)
    add_check(checks, "topic_observation_row_count", topic_row_count, 6, topic_row_count == 6)
    add_check(checks, "activated_topic_observation_row_count", len(activated_topic_rows), 4, len(activated_topic_rows) == 4)
    add_check(checks, "topic_observation_returncode_zero_all_rows", topic_rc_all_zero, True, topic_rc_all_zero)
    add_check(checks, "topic_observation_publishers_positive_all_rows", topic_pub_positive_all, True, topic_pub_positive_all)
    add_check(checks, "topic_observation_subscribers_positive_all_rows", topic_sub_positive_all, True, topic_sub_positive_all)
    add_check(checks, "topic_echo_stdout_empty", echo_stdout.strip() == "", True, echo_stdout.strip() == "")

    gate_rows = load_dicts(FINAL_GATE_IN)
    gate_status = {row.get("gate", ""): as_bool(row.get("current_status", "False")) for row in gate_rows}

    expected_gate_status = {
        "G2": False,
        "G3": True,
        "G8": False,
        "G9": True,
        "G22": True,
        "G23": True,
        "G24": True,
        "G25": True,
    }

    add_check(checks, "stage127_safety_gate_exists", FINAL_GATE_IN.exists(), True, FINAL_GATE_IN.exists(), str(FINAL_GATE_IN))
    for gate, expected in expected_gate_status.items():
        value = gate_status.get(gate, None)
        add_check(checks, f"{gate}_status_after_stage127", value, expected, value == expected)

    manual_enable_active_during_test = activated_enable_true and activated_confirm_true
    manual_enable_reverted_false = reverted_enable_false and reverted_confirm_false
    active_ros_publisher_path_exists = topic_pub_positive_all
    no_message_observed_during_activation = as_bool(s127.get("no_message_observed_during_activation", "False")) and echo_stdout.strip() == ""

    torque_enable_ready = False
    torque_publisher_enabled = False
    torque_command_published_by_stage128 = False
    control_law_changed = False

    manual_enable_no_publish_frozen = (
        all(as_bool(m.get("pass", "False")) for m in summaries.values()) and
        current_source_has_create_publisher and
        not current_source_has_publish_call and
        current_source_references_torque_topic and
        current_source_has_active_member and
        current_source_has_stage124_marker and
        manual_enable_active_during_test and
        manual_enable_reverted_false and
        active_ros_publisher_path_exists and
        no_message_observed_during_activation and
        gate_status.get("G25", False)
    )

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

    gate_out_rows = []
    for row in gate_rows:
        gate_out_rows.append(row)

    gate_out_rows.append({
        "gate": "G26",
        "name": "Manual-enable no-publish freeze passed",
        "required_before_torque_publish": True,
        "current_status": manual_enable_no_publish_frozen,
        "evidence": str(LOG_PATH.relative_to(ROOT)),
    })

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(gate_out_rows)

    add_check(checks, "manual_enable_active_during_test", manual_enable_active_during_test, True, manual_enable_active_during_test)
    add_check(checks, "manual_enable_reverted_false", manual_enable_reverted_false, True, manual_enable_reverted_false)
    add_check(checks, "active_ros_publisher_path_exists", active_ros_publisher_path_exists, True, active_ros_publisher_path_exists)
    add_check(checks, "no_message_observed_during_activation", no_message_observed_during_activation, True, no_message_observed_during_activation)
    add_check(checks, "manual_enable_no_publish_frozen", manual_enable_no_publish_frozen, True, manual_enable_no_publish_frozen)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)
    add_check(checks, "torque_publisher_enabled", torque_publisher_enabled, False, not torque_publisher_enabled)
    add_check(checks, "torque_command_published_by_stage128", torque_command_published_by_stage128, False, not torque_command_published_by_stage128)
    add_check(checks, "control_law_changed", control_law_changed, False, not control_law_changed)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    stage_rows = []
    for stage, metrics in summaries.items():
        stage_rows.append(
            f"| {stage} | {metrics.get('test_name', '')} | {metrics.get('stage12_scope', '')} | {metrics.get('pass', '')} | {metrics.get('torque_publisher_enabled', '')} | {metrics.get('control_law_changed', '')} |"
        )

    DOC_PATH.write_text(f"""# Stage 12.8 Manual-enable No-publish Freeze

## 一、冻结结论

Stage 12.8 冻结 Stage 12.7 manual enable runtime activation without publish 的结果。

当前状态：

- active ROS publisher path exists: {active_ros_publisher_path_exists}
- manual_enable_active_during_test: {manual_enable_active_during_test}
- manual_enable_reverted_false: {manual_enable_reverted_false}
- source_has_publish_call: {current_source_has_publish_call}
- no_message_observed_during_activation: {no_message_observed_during_activation}
- torque_command_published_by_stage128: {torque_command_published_by_stage128}

本阶段不修改 C++ source，不加入 publish call，不发布 torque，不改变控制律。

## 二、Stage 12.4–12.7 汇总

| 阶段 | 测试名 | scope | pass | torque_publisher_enabled | control_law_changed |
|---|---|---|---:|---:|---:|
{chr(10).join(stage_rows)}

## 三、Source integrity

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- current_source_has_create_publisher: {current_source_has_create_publisher}
- current_source_has_publish_call: {current_source_has_publish_call}
- current_source_references_torque_topic: {current_source_references_torque_topic}
- current_source_has_active_publisher_member: {current_source_has_active_member}
- current_source_has_stage124_marker: {current_source_has_stage124_marker}

## 四、Runtime activation evidence

Parameter observations:

    results/logs_sample/stage12_manual_enable_runtime_activation_param_observations.csv

Topic observations:

    results/logs_sample/stage12_manual_enable_runtime_activation_topic_observations.csv

Evidence:

- initial_enable_false_observed: {initial_enable_false}
- initial_confirm_false_observed: {initial_confirm_false}
- activated_enable_true_observed: {activated_enable_true}
- activated_confirm_true_observed: {activated_confirm_true}
- reverted_enable_false_observed: {reverted_enable_false}
- reverted_confirm_false_observed: {reverted_confirm_false}
- topic_observation_publishers_positive_all_rows: {topic_pub_positive_all}
- topic_echo_stdout_empty: {echo_stdout.strip() == ""}

## 五、Safety gate after Stage 12.8

新增：

- G26 manual-enable no-publish freeze passed: {manual_enable_no_publish_frozen}

Key gates:

- G3 no publish call: {gate_status.get("G3")}
- G8 manual enable active at runtime after revert: {gate_status.get("G8")}
- G9 active ROS publisher path exists: {gate_status.get("G9")}
- G25 manual enable runtime activation without publish passed: {gate_status.get("G25")}

Therefore:

    torque_enable_ready = {torque_enable_ready}

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.8 没有完成：

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
        writer.writerow(["stage", "Stage 12.8"])
        writer.writerow(["test_name", "manual_enable_no_publish_freeze"])
        writer.writerow(["stage124_pass", s124.get("pass", "False")])
        writer.writerow(["stage125_pass", s125.get("pass", "False")])
        writer.writerow(["stage126_pass", s126.get("pass", "False")])
        writer.writerow(["stage127_pass", s127.get("pass", "False")])
        writer.writerow(["freeze_file_count", len(FREEZE_FILES)])
        writer.writerow(["missing_file_count", len(missing_files)])
        writer.writerow(["current_source_has_create_publisher", current_source_has_create_publisher])
        writer.writerow(["current_source_has_publish_call", current_source_has_publish_call])
        writer.writerow(["current_source_references_torque_topic", current_source_references_torque_topic])
        writer.writerow(["current_source_has_active_publisher_member", current_source_has_active_member])
        writer.writerow(["current_source_has_stage124_marker", current_source_has_stage124_marker])
        writer.writerow(["initial_enable_false_observed", initial_enable_false])
        writer.writerow(["initial_confirm_false_observed", initial_confirm_false])
        writer.writerow(["activated_enable_true_observed", activated_enable_true])
        writer.writerow(["activated_confirm_true_observed", activated_confirm_true])
        writer.writerow(["manual_enable_active_during_test", manual_enable_active_during_test])
        writer.writerow(["reverted_enable_false_observed", reverted_enable_false])
        writer.writerow(["reverted_confirm_false_observed", reverted_confirm_false])
        writer.writerow(["manual_enable_reverted_false", manual_enable_reverted_false])
        writer.writerow(["topic_observation_row_count", topic_row_count])
        writer.writerow(["activated_topic_observation_row_count", len(activated_topic_rows)])
        writer.writerow(["topic_observation_returncode_zero_all_rows", topic_rc_all_zero])
        writer.writerow(["topic_observation_publishers_positive_all_rows", topic_pub_positive_all])
        writer.writerow(["topic_observation_subscribers_positive_all_rows", topic_sub_positive_all])
        writer.writerow(["topic_echo_stdout_empty", echo_stdout.strip() == ""])
        writer.writerow(["no_message_observed_during_activation", no_message_observed_during_activation])
        writer.writerow(["active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g3_no_publish_call", gate_status.get("G3", False)])
        writer.writerow(["g8_manual_enable_active_after_revert", gate_status.get("G8", False)])
        writer.writerow(["g9_active_ros_publisher_path_exists", gate_status.get("G9", False)])
        writer.writerow(["g23_publisher_construction_no_publish_freeze_passed", gate_status.get("G23", False)])
        writer.writerow(["g24_manual_enable_activation_design_exists", gate_status.get("G24", False)])
        writer.writerow(["g25_manual_enable_runtime_activation_without_publish_passed", gate_status.get("G25", False)])
        writer.writerow(["g26_manual_enable_no_publish_freeze_passed", manual_enable_no_publish_frozen])
        writer.writerow(["manual_enable_no_publish_frozen", manual_enable_no_publish_frozen])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", control_law_changed])
        writer.writerow(["torque_publisher_enabled", torque_publisher_enabled])
        writer.writerow(["torque_command_published_by_stage128", torque_command_published_by_stage128])
        writer.writerow(["stage12_scope", "manual_enable_no_publish_freeze_only"])
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
## Stage 12.8 Manual-enable No-publish Freeze

Stage 12.8 冻结 manual-enable no-publish baseline。

- Script: `scripts/stage12_manual_enable_no_publish_freeze.py`
- Log: `results/logs_sample/stage12_manual_enable_no_publish_freeze_log.csv`
- Hashes: `results/logs_sample/stage12_manual_enable_no_publish_freeze_hashes.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage128.csv`
- Summary: `results/logs_sample/stage12_manual_enable_no_publish_freeze_summary.csv`
- Docs: `docs/STAGE12_MANUAL_ENABLE_NO_PUBLISH_FREEZE.md`
- pass: `{all_pass}`
- manual_enable_no_publish_frozen: `{manual_enable_no_publish_frozen}`
- manual_enable_active_during_test: `{manual_enable_active_during_test}`
- manual_enable_reverted_false: `{manual_enable_reverted_false}`
- active_ros_publisher_path_exists: `{active_ros_publisher_path_exists}`
- no_message_observed_during_activation: `{no_message_observed_during_activation}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `{torque_publisher_enabled}`
- torque_command_published_by_stage128: `{torque_command_published_by_stage128}`
- control_law_changed: `{control_law_changed}`

Stage 12.8 只冻结 manual-enable no-publish baseline，不加入 publish call，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 12.8 Manual-enable No-publish Freeze"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 12.8] manual-enable no-publish freeze")
    print(f"pass={all_pass}")
    print(f"missing_file_count={len(missing_files)}")
    print(f"manual_enable_no_publish_frozen={manual_enable_no_publish_frozen}")
    print(f"manual_enable_active_during_test={manual_enable_active_during_test}")
    print(f"manual_enable_reverted_false={manual_enable_reverted_false}")
    print(f"active_ros_publisher_path_exists={active_ros_publisher_path_exists}")
    print(f"current_source_has_publish_call={current_source_has_publish_call}")
    print(f"no_message_observed_during_activation={no_message_observed_during_activation}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print(f"control_law_changed={control_law_changed}")
    print(f"torque_publisher_enabled={torque_publisher_enabled}")
    print(f"torque_command_published_by_stage128={torque_command_published_by_stage128}")
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
