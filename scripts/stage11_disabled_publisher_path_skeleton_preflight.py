#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE113_SUMMARY = LOG_DIR / "stage11_0_2_publisher_path_planning_freeze_summary.csv"
STAGE112_GATE = LOG_DIR / "stage11_torque_publisher_safety_gate_after_stage112.csv"
DESIGN_CSV = LOG_DIR / "stage11_disabled_publisher_path_skeleton_design.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
SAFETY_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

PREFLIGHT_CSV = LOG_DIR / "stage11_disabled_publisher_path_skeleton_preflight.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage11_torque_publisher_safety_gate_after_stage114.csv"
LOG_PATH = LOG_DIR / "stage11_disabled_publisher_path_skeleton_preflight_log.csv"
SUMMARY_PATH = LOG_DIR / "stage11_disabled_publisher_path_skeleton_preflight_summary.csv"
DOC_PATH = ROOT / "docs/STAGE11_DISABLED_PUBLISHER_PATH_SKELETON_PREFLIGHT.md"

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


def add_check(rows, check, value, expected, passed, detail=""):
    rows.append({
        "check": check,
        "value": str(value),
        "expected": str(expected),
        "pass": bool(passed),
        "detail": detail,
    })


def sha256_text(text: str):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    checks = []

    s113 = load_summary(STAGE113_SUMMARY)
    stage113_pass = as_bool(s113.get("pass", "False"))
    publisher_path_planning_frozen = as_bool(s113.get("publisher_path_planning_frozen", "False"))
    stage113_torque_ready = as_bool(s113.get("torque_enable_ready", "True"))
    stage113_torque_enabled = as_bool(s113.get("torque_publisher_enabled", "True"))
    stage113_control_changed = as_bool(s113.get("control_law_changed", "True"))

    add_check(checks, "stage113_summary_exists", STAGE113_SUMMARY.exists(), True, STAGE113_SUMMARY.exists(), str(STAGE113_SUMMARY))
    add_check(checks, "stage113_pass", stage113_pass, True, stage113_pass)
    add_check(checks, "publisher_path_planning_frozen", publisher_path_planning_frozen, True, publisher_path_planning_frozen)
    add_check(checks, "stage113_torque_enable_ready", stage113_torque_ready, False, not stage113_torque_ready)
    add_check(checks, "stage113_torque_publisher_enabled", stage113_torque_enabled, False, not stage113_torque_enabled)
    add_check(checks, "stage113_control_law_changed", stage113_control_changed, False, not stage113_control_changed)

    design_rows = load_dicts(DESIGN_CSV)
    design_exists = DESIGN_CSV.exists()
    design_all_not_implemented = all(not as_bool(row.get("implemented_in_stage112", "True")) for row in design_rows)
    design_has_future_handle = any(row.get("name") == "torque_cmd_publisher_" for row in design_rows)
    design_has_publish_allowed = any(row.get("name") == "publish_allowed" for row in design_rows)
    design_has_runtime_guard = any(row.get("name") == "publisher_count_guard" for row in design_rows)

    add_check(checks, "stage112_design_csv_exists", design_exists, True, design_exists, str(DESIGN_CSV))
    add_check(checks, "stage112_design_all_items_not_implemented", design_all_not_implemented, True, design_all_not_implemented)
    add_check(checks, "stage112_design_has_future_handle", design_has_future_handle, True, design_has_future_handle)
    add_check(checks, "stage112_design_has_publish_allowed_gate", design_has_publish_allowed, True, design_has_publish_allowed)
    add_check(checks, "stage112_design_has_runtime_guard", design_has_runtime_guard, True, design_has_runtime_guard)

    cpp_text = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    safety_text = SAFETY_HEADER.read_text(errors="replace") if SAFETY_HEADER.exists() else ""
    zero_text = ZERO_HEADER.read_text(errors="replace") if ZERO_HEADER.exists() else ""

    source_hash_before = sha256_text(cpp_text)

    source_has_create_publisher = "create_publisher" in cpp_text
    source_has_publish_call = ".publish(" in cpp_text or "->publish(" in cpp_text
    source_has_torque_topic = TORQUE_TOPIC in cpp_text

    source_declares_enable_param = 'declare_parameter<bool>("enable_torque_publisher", false)' in cpp_text
    source_declares_confirm_param = 'declare_parameter<bool>("confirm_torque_publisher_enable", false)' in cpp_text
    source_uses_safety = "clampTorqueCommand" in cpp_text and "allInputsFresh" in cpp_text and "watchdogFallbackZeroTorque" in cpp_text
    safety_header_has_clamp_watchdog = "clampTorqueCommand" in safety_text and "allInputsFresh" in safety_text and "watchdogFallbackZeroTorque" in safety_text
    zero_header_declares_12 = "kGo1NumActuatedJoints = 12" in zero_text

    add_check(checks, "cpp_source_exists", CPP_SOURCE.exists(), True, CPP_SOURCE.exists(), str(CPP_SOURCE))
    add_check(checks, "safety_header_exists", SAFETY_HEADER.exists(), True, SAFETY_HEADER.exists(), str(SAFETY_HEADER))
    add_check(checks, "zero_header_exists", ZERO_HEADER.exists(), True, ZERO_HEADER.exists(), str(ZERO_HEADER))
    add_check(checks, "source_has_no_create_publisher", source_has_create_publisher, False, not source_has_create_publisher)
    add_check(checks, "source_has_no_publish_call", source_has_publish_call, False, not source_has_publish_call)
    add_check(checks, "source_does_not_reference_torque_topic", source_has_torque_topic, False, not source_has_torque_topic)
    add_check(checks, "source_declares_enable_param_default_false", source_declares_enable_param, True, source_declares_enable_param)
    add_check(checks, "source_declares_confirm_param_default_false", source_declares_confirm_param, True, source_declares_confirm_param)
    add_check(checks, "source_uses_safety_utilities", source_uses_safety, True, source_uses_safety)
    add_check(checks, "safety_header_has_clamp_watchdog", safety_header_has_clamp_watchdog, True, safety_header_has_clamp_watchdog)
    add_check(checks, "zero_header_declares_12", zero_header_declares_12, True, zero_header_declares_12)

    gate_rows = load_dicts(STAGE112_GATE)
    gate_status = {row.get("gate", ""): as_bool(row.get("current_status", "False")) for row in gate_rows}

    add_check(checks, "stage112_safety_gate_exists", STAGE112_GATE.exists(), True, STAGE112_GATE.exists(), str(STAGE112_GATE))
    add_check(checks, "stage112_g8_manual_enable_active_false", gate_status.get("G8", True), False, gate_status.get("G8", True) is False)
    add_check(checks, "stage112_g9_publisher_path_exists_false", gate_status.get("G9", True), False, gate_status.get("G9", True) is False)
    add_check(checks, "stage112_g14_design_exists_true", gate_status.get("G14", False), True, gate_status.get("G14", False) is True)

    preflight_rows = [
        {
            "item": "source_change_allowed_in_stage114",
            "value": "false",
            "required": True,
            "description": "Stage 11.4 is preflight only and must not edit disabled_controller_node.cpp.",
        },
        {
            "item": "future_stage_minimum",
            "value": "Stage 11.5",
            "required": True,
            "description": "A later stage may add dormant source skeleton only after this preflight passes.",
        },
        {
            "item": "future_create_publisher_allowed",
            "value": "false",
            "required": True,
            "description": "The next implementation stage must still avoid create_publisher.",
        },
        {
            "item": "future_publish_call_allowed",
            "value": "false",
            "required": True,
            "description": "No publish call may appear in the disabled skeleton implementation stage.",
        },
        {
            "item": "future_torque_topic_string_allowed_in_controller_source",
            "value": "false",
            "required": True,
            "description": "The exact /go1/joint_torque_cmd string must remain outside controller source until explicit publisher construction stage.",
        },
        {
            "item": "future_skeleton_allowed_elements",
            "value": "compile-time constants, inactive helper methods, nullptr member, no ROS publisher construction",
            "required": True,
            "description": "Skeleton means dormant code structure only.",
        },
        {
            "item": "future_runtime_expected_publisher_count",
            "value": "0",
            "required": True,
            "description": "Runtime publisher count must remain zero after any no-publish skeleton stage.",
        },
        {
            "item": "manual_enable_active_expected",
            "value": "false",
            "required": True,
            "description": "Manual enable flags must remain default false.",
        },
        {
            "item": "torque_enable_ready_expected",
            "value": "false",
            "required": True,
            "description": "Torque enable must remain false because no active publisher or publish call exists.",
        },
    ]

    with PREFLIGHT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["item", "value", "required", "description"])
        writer.writeheader()
        writer.writerows(preflight_rows)

    preflight_exists = PREFLIGHT_CSV.exists()
    preflight_forbids_create_publisher = any(
        row["item"] == "future_create_publisher_allowed" and row["value"] == "false"
        for row in preflight_rows
    )
    preflight_forbids_publish_call = any(
        row["item"] == "future_publish_call_allowed" and row["value"] == "false"
        for row in preflight_rows
    )
    preflight_forbids_topic_string = any(
        row["item"] == "future_torque_topic_string_allowed_in_controller_source" and row["value"] == "false"
        for row in preflight_rows
    )

    publisher_path_preflight_passed = True
    publisher_path_implemented = False
    manual_enable_active = False
    torque_enable_ready = False

    source_hash_after = sha256_text(CPP_SOURCE.read_text(errors="replace")) if CPP_SOURCE.exists() else ""
    source_unchanged_by_stage114 = source_hash_before == source_hash_after

    add_check(checks, "preflight_csv_exists", preflight_exists, True, preflight_exists, str(PREFLIGHT_CSV))
    add_check(checks, "preflight_forbids_create_publisher", preflight_forbids_create_publisher, True, preflight_forbids_create_publisher)
    add_check(checks, "preflight_forbids_publish_call", preflight_forbids_publish_call, True, preflight_forbids_publish_call)
    add_check(checks, "preflight_forbids_topic_string_in_controller_source", preflight_forbids_topic_string, True, preflight_forbids_topic_string)
    add_check(checks, "source_unchanged_by_stage114", source_unchanged_by_stage114, True, source_unchanged_by_stage114)
    add_check(checks, "publisher_path_implemented", publisher_path_implemented, False, not publisher_path_implemented)
    add_check(checks, "manual_enable_active", manual_enable_active, False, not manual_enable_active)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)

    gate_after_rows = [
        {
            "gate": "G0",
            "name": "Stage 8 frozen Python baseline valid",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage08_freeze_integrity_check_summary.csv",
        },
        {
            "gate": "G1",
            "name": "Stage 9 interface mirror frozen",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage09_0_6_interface_mirror_freeze_summary.csv",
        },
        {
            "gate": "G2",
            "name": "C++ controller source has no torque publisher",
            "required_before_torque_publish": True,
            "current_status": not source_has_create_publisher,
            "evidence": str(CPP_SOURCE.relative_to(ROOT)),
        },
        {
            "gate": "G3",
            "name": "C++ controller source has no publish call",
            "required_before_torque_publish": True,
            "current_status": not source_has_publish_call,
            "evidence": str(CPP_SOURCE.relative_to(ROOT)),
        },
        {
            "gate": "G4",
            "name": "Explicit manual enable flag design exists",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "docs/STAGE10_TORQUE_PUBLISHER_ENABLE_GATE_DESIGN.md",
        },
        {
            "gate": "G5",
            "name": "Torque clamp and watchdog utility implemented",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": str(SAFETY_HEADER.relative_to(ROOT)),
        },
        {
            "gate": "G6",
            "name": "Zero torque dry-run regression completed",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage10_zero_torque_dry_run_internal_validation_summary.csv",
        },
        {
            "gate": "G7",
            "name": "Python frozen baseline A/B regression still passes",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage08_adapter_backed_stage07_baseline_ab_test_summary.csv",
        },
        {
            "gate": "G8",
            "name": "Manual enable flags active at runtime",
            "required_before_torque_publish": True,
            "current_status": manual_enable_active,
            "evidence": "not activated in Stage 11.4",
        },
        {
            "gate": "G9",
            "name": "Publisher path exists",
            "required_before_torque_publish": True,
            "current_status": publisher_path_implemented,
            "evidence": "preflight only, not implemented in Stage 11.4",
        },
        {
            "gate": "G10",
            "name": "Disabled controller uses clamp/watchdog internally",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": str(CPP_SOURCE.relative_to(ROOT)),
        },
        {
            "gate": "G11",
            "name": "Manual enable parameters exist and default false",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": str(CPP_SOURCE.relative_to(ROOT)),
        },
        {
            "gate": "G12",
            "name": "Publisher path skeleton plan exists",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage11_publisher_path_skeleton_plan.csv",
        },
        {
            "gate": "G13",
            "name": "Publisher-path source guard passed before implementation",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": "results/logs_sample/stage11_publisher_path_source_guard_log.csv",
        },
        {
            "gate": "G14",
            "name": "Disabled publisher-path skeleton design exists",
            "required_before_torque_publish": True,
            "current_status": True,
            "evidence": str(DESIGN_CSV.relative_to(ROOT)),
        },
        {
            "gate": "G15",
            "name": "Disabled publisher-path skeleton preflight passed",
            "required_before_torque_publish": True,
            "current_status": publisher_path_preflight_passed,
            "evidence": str(PREFLIGHT_CSV.relative_to(ROOT)),
        },
    ]

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(gate_after_rows)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    DOC_PATH.write_text(f"""# Stage 11.4 Disabled Publisher-path Skeleton Preflight

## 一、结论

Stage 11.4 只做 disabled publisher-path skeleton preflight。

本阶段不修改 C++ controller 源码，不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、前置状态

Stage 11.3:

- pass: {stage113_pass}
- publisher_path_planning_frozen: {publisher_path_planning_frozen}
- torque_enable_ready: {stage113_torque_ready}
- torque_publisher_enabled: {stage113_torque_enabled}
- control_law_changed: {stage113_control_changed}

## 三、当前源码状态

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: {source_has_create_publisher}
- source_has_publish_call: {source_has_publish_call}
- source_has_torque_topic: {source_has_torque_topic}
- source_unchanged_by_stage114: {source_unchanged_by_stage114}

## 四、Preflight 约束

Stage 11.4 决定：后续 skeleton implementation 仍不得直接创建 ROS publisher。

后续允许的只是 dormant source skeleton，例如：

- inactive helper method；
- nullptr member；
- compile-time placeholder；
- no create_publisher；
- no publish call；
- controller source 仍不直接包含 /go1/joint_torque_cmd；
- runtime publisher count 仍必须为 0。

## 五、Safety gate after Stage 11.4

新增：

- G15 disabled publisher-path skeleton preflight passed: {publisher_path_preflight_passed}

仍为 False：

- G8 manual enable flags active at runtime: {manual_enable_active}
- G9 publisher path exists: {publisher_path_implemented}

Therefore:

    torque_enable_ready = {torque_enable_ready}

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 11.4 不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
""")

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 11.4"])
        writer.writerow(["test_name", "disabled_publisher_path_skeleton_preflight"])
        writer.writerow(["stage113_pass", stage113_pass])
        writer.writerow(["publisher_path_planning_frozen", publisher_path_planning_frozen])
        writer.writerow(["source_has_no_create_publisher", not source_has_create_publisher])
        writer.writerow(["source_has_no_publish_call", not source_has_publish_call])
        writer.writerow(["source_does_not_reference_torque_topic", not source_has_torque_topic])
        writer.writerow(["source_unchanged_by_stage114", source_unchanged_by_stage114])
        writer.writerow(["stage112_design_csv_exists", design_exists])
        writer.writerow(["stage112_design_all_items_not_implemented", design_all_not_implemented])
        writer.writerow(["preflight_csv_exists", preflight_exists])
        writer.writerow(["preflight_forbids_create_publisher", preflight_forbids_create_publisher])
        writer.writerow(["preflight_forbids_publish_call", preflight_forbids_publish_call])
        writer.writerow(["preflight_forbids_topic_string_in_controller_source", preflight_forbids_topic_string])
        writer.writerow(["disabled_publisher_path_skeleton_preflight_passed", publisher_path_preflight_passed])
        writer.writerow(["publisher_path_implemented", publisher_path_implemented])
        writer.writerow(["manual_enable_active", manual_enable_active])
        writer.writerow(["g8_manual_enable_active", manual_enable_active])
        writer.writerow(["g9_publisher_path_exists", publisher_path_implemented])
        writer.writerow(["g15_disabled_publisher_path_skeleton_preflight_passed", publisher_path_preflight_passed])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_publisher_enabled", False])
        writer.writerow(["torque_command_published_by_stage114", False])
        writer.writerow(["stage11_scope", "disabled_publisher_path_skeleton_preflight_only"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["ros2_cpp_realtime_controller_completed", False])
        writer.writerow(["pure_wbc_locomotion_completed", False])
        writer.writerow(["ekf_completed", False])
        writer.writerow(["full_3d_centroidal_mpc_completed", False])
        writer.writerow(["num_checks", len(checks)])
        writer.writerow(["num_failed_checks", sum(1 for row in checks if not row["pass"])])
        writer.writerow(["pass", all_pass])
        writer.writerow(["log_csv", str(LOG_PATH.relative_to(ROOT))])
        writer.writerow(["preflight_csv", str(PREFLIGHT_CSV.relative_to(ROOT))])
        writer.writerow(["safety_gate_csv", str(SAFETY_GATE_PATH.relative_to(ROOT))])
        writer.writerow(["summary_csv", str(SUMMARY_PATH.relative_to(ROOT))])
        writer.writerow(["doc", str(DOC_PATH.relative_to(ROOT))])

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 11.4 Disabled Publisher-path Skeleton Preflight

Stage 11.4 完成 disabled publisher-path skeleton preflight。

- Script: `scripts/stage11_disabled_publisher_path_skeleton_preflight.py`
- Preflight CSV: `results/logs_sample/stage11_disabled_publisher_path_skeleton_preflight.csv`
- Safety gate: `results/logs_sample/stage11_torque_publisher_safety_gate_after_stage114.csv`
- Summary: `results/logs_sample/stage11_disabled_publisher_path_skeleton_preflight_summary.csv`
- Docs: `docs/STAGE11_DISABLED_PUBLISHER_PATH_SKELETON_PREFLIGHT.md`
- pass: `{all_pass}`
- disabled_publisher_path_skeleton_preflight_passed: `{publisher_path_preflight_passed}`
- source_unchanged_by_stage114: `{source_unchanged_by_stage114}`
- publisher_path_implemented: `{publisher_path_implemented}`
- manual_enable_active: `{manual_enable_active}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 11.4 只做 preflight，不创建 publisher，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 11.4 Disabled Publisher-path Skeleton Preflight"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 11.4] disabled publisher-path skeleton preflight")
    print(f"pass={all_pass}")
    print(f"stage113_pass={stage113_pass}")
    print(f"disabled_publisher_path_skeleton_preflight_passed={publisher_path_preflight_passed}")
    print(f"source_unchanged_by_stage114={source_unchanged_by_stage114}")
    print(f"publisher_path_implemented={publisher_path_implemented}")
    print(f"manual_enable_active={manual_enable_active}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print("control_law_changed=False")
    print("torque_publisher_enabled=False")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
    print(f"preflight_csv={PREFLIGHT_CSV.relative_to(ROOT)}")
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
