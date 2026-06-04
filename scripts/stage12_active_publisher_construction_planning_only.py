#!/usr/bin/env python3
from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE1110_SUMMARY = LOG_DIR / "stage11_full_freeze_integrity_check_summary.csv"
STAGE1110_GATE = LOG_DIR / "stage11_torque_publisher_safety_gate_after_stage1110.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
SAFETY_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

PLAN_CSV = LOG_DIR / "stage12_active_publisher_construction_plan.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage120.csv"
LOG_PATH = LOG_DIR / "stage12_active_publisher_construction_planning_log.csv"
SUMMARY_PATH = LOG_DIR / "stage12_active_publisher_construction_planning_summary.csv"
DOC_PATH = ROOT / "docs/STAGE12_ACTIVE_PUBLISHER_CONSTRUCTION_PLANNING_ONLY.md"

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


def load_gate(path: Path):
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


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    checks = []

    s1110 = load_summary(STAGE1110_SUMMARY)
    stage1110_pass = as_bool(s1110.get("pass", "False"))
    verified_frozen = as_bool(s1110.get("verified_full_publisher_path_no_active_publisher_frozen", "False"))
    hash_integrity_passed = as_bool(s1110.get("hash_integrity_passed", "False"))
    stage1110_g8 = as_bool(s1110.get("g8_manual_enable_active", "True"))
    stage1110_g9 = as_bool(s1110.get("g9_active_ros_publisher_path_exists", "True"))
    stage1110_g18 = as_bool(s1110.get("g18_full_freeze_integrity_check_passed", "False"))
    stage1110_torque_ready = as_bool(s1110.get("torque_enable_ready", "True"))
    stage1110_torque_enabled = as_bool(s1110.get("torque_publisher_enabled", "True"))
    stage1110_control_changed = as_bool(s1110.get("control_law_changed", "True"))

    add_check(checks, "stage1110_summary_exists", STAGE1110_SUMMARY.exists(), True, STAGE1110_SUMMARY.exists(), str(STAGE1110_SUMMARY))
    add_check(checks, "stage1110_pass", stage1110_pass, True, stage1110_pass)
    add_check(checks, "stage1110_verified_full_no_active_publisher_frozen", verified_frozen, True, verified_frozen)
    add_check(checks, "stage1110_hash_integrity_passed", hash_integrity_passed, True, hash_integrity_passed)
    add_check(checks, "stage1110_g8_manual_enable_active", stage1110_g8, False, not stage1110_g8)
    add_check(checks, "stage1110_g9_active_ros_publisher_path_exists", stage1110_g9, False, not stage1110_g9)
    add_check(checks, "stage1110_g18_full_freeze_integrity_check_passed", stage1110_g18, True, stage1110_g18)
    add_check(checks, "stage1110_torque_enable_ready", stage1110_torque_ready, False, not stage1110_torque_ready)
    add_check(checks, "stage1110_torque_publisher_enabled", stage1110_torque_enabled, False, not stage1110_torque_enabled)
    add_check(checks, "stage1110_control_law_changed", stage1110_control_changed, False, not stage1110_control_changed)

    cpp_text = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    safety_text = SAFETY_HEADER.read_text(errors="replace") if SAFETY_HEADER.exists() else ""
    zero_text = ZERO_HEADER.read_text(errors="replace") if ZERO_HEADER.exists() else ""

    source_has_create_publisher = "create_publisher" in cpp_text
    source_has_publish_call = ".publish(" in cpp_text or "->publish(" in cpp_text
    source_has_torque_topic = TORQUE_TOPIC in cpp_text

    source_declares_enable_param = 'declare_parameter<bool>("enable_torque_publisher", false)' in cpp_text
    source_declares_confirm_param = 'declare_parameter<bool>("confirm_torque_publisher_enable", false)' in cpp_text
    source_uses_safety = "clampTorqueCommand" in cpp_text and "allInputsFresh" in cpp_text and "watchdogFallbackZeroTorque" in cpp_text

    safety_header_has_clamp_watchdog = "clampTorqueCommand" in safety_text and "allInputsFresh" in safety_text and "watchdogFallbackZeroTorque" in safety_text
    zero_header_declares_12 = "kGo1NumActuatedJoints = 12" in zero_text

    source_has_dormant_skeleton_marker = "kDormantPublisherPathSkeletonPresent" in cpp_text
    source_has_construct_forbidden_marker = "kDormantPublisherConstructionAllowed = false" in cpp_text
    source_has_publish_forbidden_marker = "kDormantPublishCallAllowed = false" in cpp_text
    source_has_payload_length_12 = "kDormantTorquePayloadLength = 12" in cpp_text
    source_has_dormant_payload_helper = "makeDormantSafeTorqueCommandMessage" in cpp_text

    dormant_source_skeleton_exists = (
        source_has_dormant_skeleton_marker and
        source_has_construct_forbidden_marker and
        source_has_publish_forbidden_marker and
        source_has_payload_length_12 and
        source_has_dormant_payload_helper
    )

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
    add_check(checks, "dormant_publisher_path_source_skeleton_exists", dormant_source_skeleton_exists, True, dormant_source_skeleton_exists)

    previous_gate_rows = load_gate(STAGE1110_GATE)
    previous_gate_status = {
        row.get("gate", ""): as_bool(row.get("current_status", "False"))
        for row in previous_gate_rows
    }

    add_check(checks, "stage1110_gate_exists", STAGE1110_GATE.exists(), True, STAGE1110_GATE.exists(), str(STAGE1110_GATE))
    add_check(checks, "stage1110_gate_g8_false", previous_gate_status.get("G8", True), False, previous_gate_status.get("G8", True) is False)
    add_check(checks, "stage1110_gate_g9_false", previous_gate_status.get("G9", True), False, previous_gate_status.get("G9", True) is False)
    add_check(checks, "stage1110_gate_g18_true", previous_gate_status.get("G18", False), True, previous_gate_status.get("G18", False) is True)

    plan_rows = [
        {
            "item": "stage12_scope",
            "value": "active_publisher_construction_planning_only",
            "implemented_in_stage120": False,
            "required_before_any_source_change": True,
            "description": "Stage 12.0 only plans future active publisher construction. It must not edit controller source.",
        },
        {
            "item": "future_active_publisher_topic",
            "value": "/go1/joint_torque_cmd",
            "implemented_in_stage120": False,
            "required_before_any_source_change": True,
            "description": "Future topic name. It remains absent from controller source in Stage 12.0.",
        },
        {
            "item": "future_active_publisher_msg_type",
            "value": "std_msgs/msg/Float64MultiArray",
            "implemented_in_stage120": False,
            "required_before_any_source_change": True,
            "description": "Future message type for 12-element torque payload.",
        },
        {
            "item": "future_payload_contract",
            "value": "length=12; finite; MuJoCo actuator order FR,FL,RR,RL hip,thigh,calf",
            "implemented_in_stage120": False,
            "required_before_any_source_change": True,
            "description": "Any future publisher construction must preserve this payload contract.",
        },
        {
            "item": "future_construction_gate",
            "value": "separate stage only; no publish call in same stage",
            "implemented_in_stage120": False,
            "required_before_any_source_change": True,
            "description": "Publisher construction and publish call must remain separated across stages.",
        },
        {
            "item": "future_manual_gate",
            "value": "enable_torque_publisher && confirm_torque_publisher_enable",
            "implemented_in_stage120": False,
            "required_before_any_source_change": True,
            "description": "Both manual flags must be true before any later active publishing path is considered.",
        },
        {
            "item": "future_state_gate",
            "value": "state_ready && inputs_fresh",
            "implemented_in_stage120": False,
            "required_before_any_source_change": True,
            "description": "Fresh validated state is required before publish permission.",
        },
        {
            "item": "future_safety_filter",
            "value": "watchdogFallbackZeroTorque then clampTorqueCommand",
            "implemented_in_stage120": False,
            "required_before_any_source_change": True,
            "description": "Future torque command must pass watchdog and clamp utilities.",
        },
        {
            "item": "future_runtime_observation",
            "value": "publisher_count observed before and after construction stage",
            "implemented_in_stage120": False,
            "required_before_any_source_change": True,
            "description": "Runtime topic info must be recorded before any publishing stage.",
        },
        {
            "item": "future_abort_conditions",
            "value": "hash mismatch; source guard failure; parameter default violation; publisher count unexpected",
            "implemented_in_stage120": False,
            "required_before_any_source_change": True,
            "description": "Any violation stops Stage 12 before active publisher implementation.",
        },
    ]

    with PLAN_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "item",
                "value",
                "implemented_in_stage120",
                "required_before_any_source_change",
                "description",
            ],
        )
        writer.writeheader()
        writer.writerows(plan_rows)

    active_publisher_construction_plan_exists = PLAN_CSV.exists()
    plan_all_not_implemented = all(not row["implemented_in_stage120"] for row in plan_rows)
    plan_has_topic = any(row["item"] == "future_active_publisher_topic" for row in plan_rows)
    plan_has_separate_construction_and_publish = any(
        row["item"] == "future_construction_gate" and "no publish call" in row["value"]
        for row in plan_rows
    )
    plan_has_abort_conditions = any(row["item"] == "future_abort_conditions" for row in plan_rows)

    add_check(checks, "active_publisher_construction_plan_exists", active_publisher_construction_plan_exists, True, active_publisher_construction_plan_exists, str(PLAN_CSV))
    add_check(checks, "plan_all_items_not_implemented", plan_all_not_implemented, True, plan_all_not_implemented)
    add_check(checks, "plan_has_future_topic", plan_has_topic, True, plan_has_topic)
    add_check(checks, "plan_separates_construction_and_publish_call", plan_has_separate_construction_and_publish, True, plan_has_separate_construction_and_publish)
    add_check(checks, "plan_has_abort_conditions", plan_has_abort_conditions, True, plan_has_abort_conditions)

    manual_enable_active = False
    active_ros_publisher_path_exists = False
    torque_enable_ready = False
    active_publisher_construction_planning_complete = True

    gate_rows = []
    for row in previous_gate_rows:
        gate_rows.append(row)

    gate_rows.append({
        "gate": "G19",
        "name": "Active publisher construction planning exists",
        "required_before_torque_publish": True,
        "current_status": active_publisher_construction_planning_complete,
        "evidence": str(PLAN_CSV.relative_to(ROOT)),
    })

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(gate_rows)

    add_check(checks, "manual_enable_active", manual_enable_active, False, not manual_enable_active)
    add_check(checks, "active_ros_publisher_path_exists", active_ros_publisher_path_exists, False, not active_ros_publisher_path_exists)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)
    add_check(checks, "active_publisher_construction_planning_complete", active_publisher_construction_planning_complete, True, active_publisher_construction_planning_complete)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    DOC_PATH.write_text(f"""# Stage 12.0 Active Publisher Construction Planning Only

## 一、结论

Stage 12.0 只规划 future active publisher construction。

本阶段不修改 C++ controller 源码，不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、前置状态

Stage 11.10:

- pass: {stage1110_pass}
- verified_full_publisher_path_no_active_publisher_frozen: {verified_frozen}
- hash_integrity_passed: {hash_integrity_passed}
- G8 manual_enable_active: {stage1110_g8}
- G9 active_ros_publisher_path_exists: {stage1110_g9}
- G18 full_freeze_integrity_check_passed: {stage1110_g18}
- torque_enable_ready: {stage1110_torque_ready}

## 三、当前 source guard

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: {source_has_create_publisher}
- source_has_publish_call: {source_has_publish_call}
- source_has_torque_topic: {source_has_torque_topic}
- dormant_publisher_path_source_skeleton_exists: {dormant_source_skeleton_exists}

## 四、Stage 12 active publisher construction plan

Plan CSV:

    results/logs_sample/stage12_active_publisher_construction_plan.csv

Stage 12.0 只记录未来策略：

- publisher topic: /go1/joint_torque_cmd；
- message type: std_msgs/msg/Float64MultiArray；
- payload length: 12；
- actuator order: FR, FL, RR, RL; each hip, thigh, calf；
- publisher construction 与 publish call 必须分离到不同阶段；
- future construction stage 仍不得调用 publish；
- publish stage 前必须再次做 source guard、runtime guard、hash check；
- manual enable、state freshness、watchdog、clamp 全部必须通过；
- 任何 hash mismatch、source guard failure、参数默认值异常、publisher count 异常都必须 abort。

## 五、Safety gate after Stage 12.0

新增：

- G19 active publisher construction planning exists: {active_publisher_construction_planning_complete}

仍为 False：

- G8 manual enable flags active at runtime: {manual_enable_active}
- G9 active ROS publisher path exists: {active_ros_publisher_path_exists}

Therefore:

    torque_enable_ready = {torque_enable_ready}

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.0 不是 ROS2/C++ realtime controller，不创建 publisher，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
""")

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 12.0"])
        writer.writerow(["test_name", "active_publisher_construction_planning_only"])
        writer.writerow(["stage1110_pass", stage1110_pass])
        writer.writerow(["stage1110_verified_full_publisher_path_no_active_publisher_frozen", verified_frozen])
        writer.writerow(["stage1110_hash_integrity_passed", hash_integrity_passed])
        writer.writerow(["stage1110_g18_full_freeze_integrity_check_passed", stage1110_g18])
        writer.writerow(["source_has_no_create_publisher", not source_has_create_publisher])
        writer.writerow(["source_has_no_publish_call", not source_has_publish_call])
        writer.writerow(["source_does_not_reference_torque_topic", not source_has_torque_topic])
        writer.writerow(["source_declares_enable_param_default_false", source_declares_enable_param])
        writer.writerow(["source_declares_confirm_param_default_false", source_declares_confirm_param])
        writer.writerow(["source_uses_safety_utilities", source_uses_safety])
        writer.writerow(["dormant_publisher_path_source_skeleton_exists", dormant_source_skeleton_exists])
        writer.writerow(["active_publisher_construction_plan_exists", active_publisher_construction_plan_exists])
        writer.writerow(["plan_all_items_not_implemented", plan_all_not_implemented])
        writer.writerow(["plan_has_future_topic", plan_has_topic])
        writer.writerow(["plan_separates_construction_and_publish_call", plan_has_separate_construction_and_publish])
        writer.writerow(["plan_has_abort_conditions", plan_has_abort_conditions])
        writer.writerow(["active_publisher_construction_planning_complete", active_publisher_construction_planning_complete])
        writer.writerow(["manual_enable_active", manual_enable_active])
        writer.writerow(["active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g8_manual_enable_active", manual_enable_active])
        writer.writerow(["g9_active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g19_active_publisher_construction_planning_exists", active_publisher_construction_planning_complete])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_publisher_enabled", False])
        writer.writerow(["torque_command_published_by_stage120", False])
        writer.writerow(["stage12_scope", "active_publisher_construction_planning_only"])
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
## Stage 12.0 Active Publisher Construction Planning Only

Stage 12.0 完成 active publisher construction planning only。

- Script: `scripts/stage12_active_publisher_construction_planning_only.py`
- Plan: `results/logs_sample/stage12_active_publisher_construction_plan.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage120.csv`
- Summary: `results/logs_sample/stage12_active_publisher_construction_planning_summary.csv`
- Docs: `docs/STAGE12_ACTIVE_PUBLISHER_CONSTRUCTION_PLANNING_ONLY.md`
- pass: `{all_pass}`
- active_publisher_construction_planning_complete: `{active_publisher_construction_planning_complete}`
- active_ros_publisher_path_exists: `{active_ros_publisher_path_exists}`
- manual_enable_active: `{manual_enable_active}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 12.0 只规划 active publisher construction，不创建 publisher，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 12.0 Active Publisher Construction Planning Only"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 12.0] active publisher construction planning only")
    print(f"pass={all_pass}")
    print(f"stage1110_pass={stage1110_pass}")
    print(f"active_publisher_construction_planning_complete={active_publisher_construction_planning_complete}")
    print(f"active_ros_publisher_path_exists={active_ros_publisher_path_exists}")
    print(f"manual_enable_active={manual_enable_active}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print("control_law_changed=False")
    print("torque_publisher_enabled=False")
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
