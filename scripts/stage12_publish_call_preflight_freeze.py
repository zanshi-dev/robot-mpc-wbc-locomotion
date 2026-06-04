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
    "Stage 12.8": LOG_DIR / "stage12_manual_enable_no_publish_freeze_summary.csv",
    "Stage 12.9": LOG_DIR / "stage12_publish_call_design_summary.csv",
}

FINAL_GATE_IN = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage129.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
SAFETY_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

PUBLISH_DESIGN = LOG_DIR / "stage12_publish_call_design.csv"

DOC_PATH = ROOT / "docs/STAGE12_PUBLISH_CALL_PREFLIGHT_FREEZE.md"
SUMMARY_PATH = LOG_DIR / "stage12_publish_call_preflight_freeze_summary.csv"
LOG_PATH = LOG_DIR / "stage12_publish_call_preflight_freeze_log.csv"
HASH_PATH = LOG_DIR / "stage12_publish_call_preflight_freeze_hashes.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage1210.csv"

TORQUE_TOPIC = "/go1/joint_torque_cmd"

FREEZE_FILES = [
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp",

    "docs/STAGE12_PUBLISHER_CONSTRUCTION_SOURCE_PATCH_WITHOUT_PUBLISH.md",
    "docs/STAGE12_PUBLISHER_CONSTRUCTION_NO_PUBLISH_FREEZE.md",
    "docs/STAGE12_MANUAL_ENABLE_ACTIVATION_DESIGN_ONLY.md",
    "docs/STAGE12_MANUAL_ENABLE_RUNTIME_ACTIVATION_WITHOUT_PUBLISH.md",
    "docs/STAGE12_MANUAL_ENABLE_NO_PUBLISH_FREEZE.md",
    "docs/STAGE12_PUBLISH_CALL_DESIGN_ONLY.md",

    "results/logs_sample/stage12_publisher_construction_source_patch_without_publish_summary.csv",
    "results/logs_sample/stage12_publisher_construction_no_publish_freeze_summary.csv",
    "results/logs_sample/stage12_manual_enable_activation_design_summary.csv",
    "results/logs_sample/stage12_manual_enable_runtime_activation_without_publish_summary.csv",
    "results/logs_sample/stage12_manual_enable_no_publish_freeze_summary.csv",
    "results/logs_sample/stage12_publish_call_design_summary.csv",

    "results/logs_sample/stage12_publisher_construction_without_publish_topic_observations.csv",
    "results/logs_sample/stage12_manual_enable_runtime_activation_param_observations.csv",
    "results/logs_sample/stage12_manual_enable_runtime_activation_topic_observations.csv",
    "results/logs_sample/stage12_manual_enable_runtime_activation_topic_echo_stdout.txt",

    "results/logs_sample/stage12_publish_call_design.csv",

    "results/logs_sample/stage12_torque_publisher_safety_gate_after_stage124.csv",
    "results/logs_sample/stage12_torque_publisher_safety_gate_after_stage125.csv",
    "results/logs_sample/stage12_torque_publisher_safety_gate_after_stage126.csv",
    "results/logs_sample/stage12_torque_publisher_safety_gate_after_stage127.csv",
    "results/logs_sample/stage12_torque_publisher_safety_gate_after_stage128.csv",
    "results/logs_sample/stage12_torque_publisher_safety_gate_after_stage129.csv",
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
    s128 = summaries["Stage 12.8"]
    s129 = summaries["Stage 12.9"]

    add_check(checks, "stage124_publisher_construction_without_publish", as_bool(s124.get("publisher_construction_implemented_without_publish_call", "False")), True, as_bool(s124.get("publisher_construction_implemented_without_publish_call", "False")))
    add_check(checks, "stage125_no_publish_integrity_passed", as_bool(s125.get("publisher_construction_no_publish_integrity_passed", "False")), True, as_bool(s125.get("publisher_construction_no_publish_integrity_passed", "False")))
    add_check(checks, "stage126_manual_enable_design_complete", as_bool(s126.get("manual_enable_activation_design_complete", "False")), True, as_bool(s126.get("manual_enable_activation_design_complete", "False")))
    add_check(checks, "stage127_manual_enable_activation_without_publish_passed", as_bool(s127.get("manual_enable_runtime_activation_without_publish_passed", "False")), True, as_bool(s127.get("manual_enable_runtime_activation_without_publish_passed", "False")))
    add_check(checks, "stage128_manual_enable_no_publish_frozen", as_bool(s128.get("manual_enable_no_publish_frozen", "False")), True, as_bool(s128.get("manual_enable_no_publish_frozen", "False")))
    add_check(checks, "stage129_publish_call_design_complete", as_bool(s129.get("publish_call_design_complete", "False")), True, as_bool(s129.get("publish_call_design_complete", "False")))

    required_stage129 = {
        "source_has_create_publisher": True,
        "source_has_publish_call": False,
        "source_references_torque_topic": True,
        "source_has_active_publisher_member": True,
        "source_has_stage124_marker": True,
        "source_unchanged_by_stage129": True,
        "publish_call_design_exists": True,
        "design_all_items_not_implemented": True,
        "design_has_future_publish_call_site": True,
        "design_has_preconditions": True,
        "design_has_payload_contract": True,
        "design_has_safety_filter": True,
        "design_has_first_publish_policy": True,
        "design_forbids_control_law_change": True,
        "design_has_runtime_observation": True,
        "design_has_revert_procedure": True,
        "design_has_abort_conditions": True,
        "manual_enable_active": False,
        "active_ros_publisher_path_exists": True,
        "torque_enable_ready": False,
        "control_law_changed": False,
        "torque_publisher_enabled": False,
        "torque_command_published_by_stage129": False,
    }

    for key, expected in required_stage129.items():
        value = as_bool(s129.get(key, "False"))
        add_check(checks, f"stage129_{key}", value, expected, value == expected)

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

    design_rows = load_dicts(PUBLISH_DESIGN)
    design_all_not_implemented = all(not as_bool(row.get("implemented_in_stage129", "True")) for row in design_rows)
    design_has_publish_call_site = any(row.get("item") == "future_publish_call_site" for row in design_rows)
    design_has_preconditions = any(row.get("item") == "future_publish_preconditions" for row in design_rows)
    design_has_payload_contract = any(row.get("item") == "future_payload_contract" for row in design_rows)
    design_has_safety_filter = any(row.get("item") == "future_safety_filter" for row in design_rows)
    design_has_first_publish_policy = any(row.get("item") == "future_first_publish_policy" for row in design_rows)
    design_has_abort_conditions = any(row.get("item") == "future_abort_conditions" for row in design_rows)

    add_check(checks, "publish_design_csv_exists", PUBLISH_DESIGN.exists(), True, PUBLISH_DESIGN.exists(), str(PUBLISH_DESIGN))
    add_check(checks, "publish_design_all_items_not_implemented", design_all_not_implemented, True, design_all_not_implemented)
    add_check(checks, "publish_design_has_publish_call_site", design_has_publish_call_site, True, design_has_publish_call_site)
    add_check(checks, "publish_design_has_preconditions", design_has_preconditions, True, design_has_preconditions)
    add_check(checks, "publish_design_has_payload_contract", design_has_payload_contract, True, design_has_payload_contract)
    add_check(checks, "publish_design_has_safety_filter", design_has_safety_filter, True, design_has_safety_filter)
    add_check(checks, "publish_design_has_first_publish_policy", design_has_first_publish_policy, True, design_has_first_publish_policy)
    add_check(checks, "publish_design_has_abort_conditions", design_has_abort_conditions, True, design_has_abort_conditions)

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
        "G26": True,
        "G27": True,
    }

    add_check(checks, "stage129_safety_gate_exists", FINAL_GATE_IN.exists(), True, FINAL_GATE_IN.exists(), str(FINAL_GATE_IN))
    for gate, expected in expected_gate_status.items():
        value = gate_status.get(gate, None)
        add_check(checks, f"{gate}_status_after_stage129", value, expected, value == expected)

    active_ros_publisher_path_exists = gate_status.get("G9", False)
    manual_enable_active = gate_status.get("G8", True)

    publish_call_preflight_frozen = (
        all(as_bool(m.get("pass", "False")) for m in summaries.values()) and
        current_source_has_create_publisher and
        not current_source_has_publish_call and
        current_source_references_torque_topic and
        current_source_has_active_member and
        current_source_has_stage124_marker and
        design_all_not_implemented and
        design_has_publish_call_site and
        design_has_preconditions and
        design_has_payload_contract and
        design_has_safety_filter and
        design_has_first_publish_policy and
        design_has_abort_conditions and
        active_ros_publisher_path_exists and
        not manual_enable_active and
        gate_status.get("G27", False)
    )

    torque_enable_ready = False
    torque_publisher_enabled = False
    torque_command_published_by_stage1210 = False
    control_law_changed = False

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
        "gate": "G28",
        "name": "Publish-call preflight freeze passed",
        "required_before_torque_publish": True,
        "current_status": publish_call_preflight_frozen,
        "evidence": str(LOG_PATH.relative_to(ROOT)),
    })

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(gate_out_rows)

    add_check(checks, "publish_call_preflight_frozen", publish_call_preflight_frozen, True, publish_call_preflight_frozen)
    add_check(checks, "manual_enable_active", manual_enable_active, False, not manual_enable_active)
    add_check(checks, "active_ros_publisher_path_exists", active_ros_publisher_path_exists, True, active_ros_publisher_path_exists)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)
    add_check(checks, "torque_publisher_enabled", torque_publisher_enabled, False, not torque_publisher_enabled)
    add_check(checks, "torque_command_published_by_stage1210", torque_command_published_by_stage1210, False, not torque_command_published_by_stage1210)
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

    DOC_PATH.write_text(f"""# Stage 12.10 Publish-call Preflight Freeze

## 一、冻结结论

Stage 12.10 冻结 publish-call preflight baseline。

当前状态：

- active ROS publisher path exists: {active_ros_publisher_path_exists}
- current_source_has_create_publisher: {current_source_has_create_publisher}
- current_source_has_publish_call: {current_source_has_publish_call}
- manual_enable_active: {manual_enable_active}
- torque_enable_ready: {torque_enable_ready}
- torque_command_published_by_stage1210: {torque_command_published_by_stage1210}

本阶段不修改 C++ source，不加入 publish call，不发布 torque，不改变控制律。

## 二、Stage 12.4–12.9 汇总

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

## 四、Publish-call design integrity

Design CSV:

    results/logs_sample/stage12_publish_call_design.csv

Checks:

- publish_design_all_items_not_implemented: {design_all_not_implemented}
- publish_design_has_publish_call_site: {design_has_publish_call_site}
- publish_design_has_preconditions: {design_has_preconditions}
- publish_design_has_payload_contract: {design_has_payload_contract}
- publish_design_has_safety_filter: {design_has_safety_filter}
- publish_design_has_first_publish_policy: {design_has_first_publish_policy}
- publish_design_has_abort_conditions: {design_has_abort_conditions}

## 五、Safety gate after Stage 12.10

新增：

- G28 publish-call preflight freeze passed: {publish_call_preflight_frozen}

Key gates:

- G3 no publish call: {gate_status.get("G3")}
- G8 manual enable active after revert: {gate_status.get("G8")}
- G9 active ROS publisher path exists: {gate_status.get("G9")}
- G27 publish-call design exists: {gate_status.get("G27")}

Therefore:

    torque_enable_ready = {torque_enable_ready}

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.10 没有完成：

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
        writer.writerow(["stage", "Stage 12.10"])
        writer.writerow(["test_name", "publish_call_preflight_freeze"])
        writer.writerow(["stage124_pass", s124.get("pass", "False")])
        writer.writerow(["stage125_pass", s125.get("pass", "False")])
        writer.writerow(["stage126_pass", s126.get("pass", "False")])
        writer.writerow(["stage127_pass", s127.get("pass", "False")])
        writer.writerow(["stage128_pass", s128.get("pass", "False")])
        writer.writerow(["stage129_pass", s129.get("pass", "False")])
        writer.writerow(["freeze_file_count", len(FREEZE_FILES)])
        writer.writerow(["missing_file_count", len(missing_files)])
        writer.writerow(["current_source_has_create_publisher", current_source_has_create_publisher])
        writer.writerow(["current_source_has_publish_call", current_source_has_publish_call])
        writer.writerow(["current_source_references_torque_topic", current_source_references_torque_topic])
        writer.writerow(["current_source_has_active_publisher_member", current_source_has_active_member])
        writer.writerow(["current_source_has_stage124_marker", current_source_has_stage124_marker])
        writer.writerow(["publish_design_all_items_not_implemented", design_all_not_implemented])
        writer.writerow(["publish_design_has_publish_call_site", design_has_publish_call_site])
        writer.writerow(["publish_design_has_preconditions", design_has_preconditions])
        writer.writerow(["publish_design_has_payload_contract", design_has_payload_contract])
        writer.writerow(["publish_design_has_safety_filter", design_has_safety_filter])
        writer.writerow(["publish_design_has_first_publish_policy", design_has_first_publish_policy])
        writer.writerow(["publish_design_has_abort_conditions", design_has_abort_conditions])
        writer.writerow(["publish_call_preflight_frozen", publish_call_preflight_frozen])
        writer.writerow(["manual_enable_active", manual_enable_active])
        writer.writerow(["active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g3_no_publish_call", gate_status.get("G3", False)])
        writer.writerow(["g8_manual_enable_active_after_revert", gate_status.get("G8", False)])
        writer.writerow(["g9_active_ros_publisher_path_exists", gate_status.get("G9", False)])
        writer.writerow(["g26_manual_enable_no_publish_freeze_passed", gate_status.get("G26", False)])
        writer.writerow(["g27_publish_call_design_exists", gate_status.get("G27", False)])
        writer.writerow(["g28_publish_call_preflight_freeze_passed", publish_call_preflight_frozen])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", control_law_changed])
        writer.writerow(["torque_publisher_enabled", torque_publisher_enabled])
        writer.writerow(["torque_command_published_by_stage1210", torque_command_published_by_stage1210])
        writer.writerow(["stage12_scope", "publish_call_preflight_freeze_only"])
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
## Stage 12.10 Publish-call Preflight Freeze

Stage 12.10 冻结 publish-call preflight baseline。

- Script: `scripts/stage12_publish_call_preflight_freeze.py`
- Log: `results/logs_sample/stage12_publish_call_preflight_freeze_log.csv`
- Hashes: `results/logs_sample/stage12_publish_call_preflight_freeze_hashes.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1210.csv`
- Summary: `results/logs_sample/stage12_publish_call_preflight_freeze_summary.csv`
- Docs: `docs/STAGE12_PUBLISH_CALL_PREFLIGHT_FREEZE.md`
- pass: `{all_pass}`
- publish_call_preflight_frozen: `{publish_call_preflight_frozen}`
- active_ros_publisher_path_exists: `{active_ros_publisher_path_exists}`
- current_source_has_publish_call: `{current_source_has_publish_call}`
- manual_enable_active: `{manual_enable_active}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `{torque_publisher_enabled}`
- torque_command_published_by_stage1210: `{torque_command_published_by_stage1210}`
- control_law_changed: `{control_law_changed}`

Stage 12.10 只冻结 publish-call preflight baseline，不加入 publish call，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 12.10 Publish-call Preflight Freeze"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 12.10] publish-call preflight freeze")
    print(f"pass={all_pass}")
    print(f"missing_file_count={len(missing_files)}")
    print(f"publish_call_preflight_frozen={publish_call_preflight_frozen}")
    print(f"current_source_has_create_publisher={current_source_has_create_publisher}")
    print(f"current_source_has_publish_call={current_source_has_publish_call}")
    print(f"active_ros_publisher_path_exists={active_ros_publisher_path_exists}")
    print(f"manual_enable_active={manual_enable_active}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print(f"control_law_changed={control_law_changed}")
    print(f"torque_publisher_enabled={torque_publisher_enabled}")
    print(f"torque_command_published_by_stage1210={torque_command_published_by_stage1210}")
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
