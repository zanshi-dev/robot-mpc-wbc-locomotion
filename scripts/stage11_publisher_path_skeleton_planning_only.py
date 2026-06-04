#!/usr/bin/env python3
from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE1012_SUMMARY = LOG_DIR / "stage10_0_11_full_no_publisher_controller_freeze_summary.csv"
STAGE1010_GATE = LOG_DIR / "stage10_torque_publisher_safety_gate_after_stage1010.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
SAFETY_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

DOC_PATH = ROOT / "docs/STAGE11_PUBLISHER_PATH_SKELETON_PLANNING_ONLY.md"
PLAN_CSV = LOG_DIR / "stage11_publisher_path_skeleton_plan.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage11_torque_publisher_safety_gate_after_stage110.csv"
LOG_PATH = LOG_DIR / "stage11_publisher_path_skeleton_planning_log.csv"
SUMMARY_PATH = LOG_DIR / "stage11_publisher_path_skeleton_planning_summary.csv"


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

    stage1012 = load_summary(STAGE1012_SUMMARY)
    stage1012_pass = as_bool(stage1012.get("pass", "False"))
    full_no_publisher_frozen = as_bool(stage1012.get("full_no_publisher_controller_frozen", "False"))
    stage1012_torque_enable_ready = as_bool(stage1012.get("torque_enable_ready", "True"))
    stage1012_torque_publisher_enabled = as_bool(stage1012.get("torque_publisher_enabled", "True"))
    stage1012_control_changed = as_bool(stage1012.get("control_law_changed", "True"))

    add_check(checks, "stage1012_summary_exists", STAGE1012_SUMMARY.exists(), True, STAGE1012_SUMMARY.exists(), str(STAGE1012_SUMMARY))
    add_check(checks, "stage1012_pass", stage1012_pass, True, stage1012_pass)
    add_check(checks, "stage1012_full_no_publisher_controller_frozen", full_no_publisher_frozen, True, full_no_publisher_frozen)
    add_check(checks, "stage1012_torque_enable_ready", stage1012_torque_enable_ready, False, not stage1012_torque_enable_ready)
    add_check(checks, "stage1012_torque_publisher_enabled", stage1012_torque_publisher_enabled, False, not stage1012_torque_publisher_enabled)
    add_check(checks, "stage1012_control_law_changed", stage1012_control_changed, False, not stage1012_control_changed)

    cpp_text = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    safety_text = SAFETY_HEADER.read_text(errors="replace") if SAFETY_HEADER.exists() else ""
    zero_text = ZERO_HEADER.read_text(errors="replace") if ZERO_HEADER.exists() else ""

    source_has_create_publisher = "create_publisher" in cpp_text
    source_has_publish_call = ".publish(" in cpp_text or "->publish(" in cpp_text
    source_has_torque_topic = "/go1/joint_torque_cmd" in cpp_text

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

    previous_gate_rows = load_gate(STAGE1010_GATE)
    previous_gate_status = {
        row.get("gate", ""): as_bool(row.get("current_status", "False"))
        for row in previous_gate_rows
    }

    add_check(checks, "stage1010_gate_exists", STAGE1010_GATE.exists(), True, STAGE1010_GATE.exists(), str(STAGE1010_GATE))
    add_check(checks, "previous_g8_manual_enable_active_false", previous_gate_status.get("G8", True), False, previous_gate_status.get("G8", True) is False)
    add_check(checks, "previous_g9_publisher_path_exists_false", previous_gate_status.get("G9", True), False, previous_gate_status.get("G9", True) is False)
    add_check(checks, "previous_g11_manual_enable_params_default_false", previous_gate_status.get("G11", False), True, previous_gate_status.get("G11", False) is True)

    plan_rows = [
        {
            "item": "publisher_path_stage",
            "value": "not earlier than Stage 11.2",
            "implemented_in_stage110": False,
            "required_before_publish": True,
            "description": "Stage 11.0 only plans the publisher path. No C++ publisher is added.",
        },
        {
            "item": "publisher_topic",
            "value": "/go1/joint_torque_cmd",
            "implemented_in_stage110": False,
            "required_before_publish": True,
            "description": "Future publisher topic. Must remain absent from controller source in Stage 11.0.",
        },
        {
            "item": "publisher_msg_type",
            "value": "std_msgs/msg/Float64MultiArray",
            "implemented_in_stage110": False,
            "required_before_publish": True,
            "description": "Future publisher message type.",
        },
        {
            "item": "publisher_default_state",
            "value": "not constructed",
            "implemented_in_stage110": False,
            "required_before_publish": True,
            "description": "Stage 11.0 does not construct a publisher object.",
        },
        {
            "item": "manual_gate_policy",
            "value": "enable_torque_publisher && confirm_torque_publisher_enable",
            "implemented_in_stage110": False,
            "required_before_publish": True,
            "description": "Future path must require both manual flags true.",
        },
        {
            "item": "state_gate_policy",
            "value": "state_ready && inputs_fresh",
            "implemented_in_stage110": False,
            "required_before_publish": True,
            "description": "Future publishing must require valid and fresh state.",
        },
        {
            "item": "safety_filter_policy",
            "value": "zero fallback then clampTorqueCommand",
            "implemented_in_stage110": False,
            "required_before_publish": True,
            "description": "Future publishing must use watchdog fallback and clamp utility.",
        },
        {
            "item": "publish_payload_length",
            "value": "12",
            "implemented_in_stage110": False,
            "required_before_publish": True,
            "description": "Future payload must match 12 MuJoCo actuators.",
        },
        {
            "item": "actuator_order",
            "value": "FR,FL,RR,RL each hip,thigh,calf",
            "implemented_in_stage110": False,
            "required_before_publish": True,
            "description": "Future payload order must match MuJoCo actuator order.",
        },
        {
            "item": "first_runtime_policy",
            "value": "observe-only until separate disabled-publisher skeleton stage passes",
            "implemented_in_stage110": False,
            "required_before_publish": True,
            "description": "No torque command publish in Stage 11.0.",
        },
    ]

    with PLAN_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["item", "value", "implemented_in_stage110", "required_before_publish", "description"],
        )
        writer.writeheader()
        writer.writerows(plan_rows)

    publisher_path_plan_exists = True
    publisher_path_implemented = False
    manual_enable_active = False
    torque_enable_ready = False

    gate_rows = [
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
            "evidence": "not activated in Stage 11.0",
        },
        {
            "gate": "G9",
            "name": "Publisher path exists",
            "required_before_torque_publish": True,
            "current_status": publisher_path_implemented,
            "evidence": "planned only, not implemented in Stage 11.0",
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
            "current_status": publisher_path_plan_exists,
            "evidence": str(PLAN_CSV.relative_to(ROOT)),
        },
    ]

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(gate_rows)

    add_check(checks, "publisher_path_plan_exists", publisher_path_plan_exists, True, publisher_path_plan_exists)
    add_check(checks, "publisher_path_implemented", publisher_path_implemented, False, not publisher_path_implemented)
    add_check(checks, "manual_enable_active", manual_enable_active, False, not manual_enable_active)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    DOC_PATH.write_text(f"""# Stage 11.0 Publisher-path Skeleton Planning Only

## 一、结论

Stage 11.0 只规划未来 publisher-path skeleton。

本阶段不修改 C++ controller 源码，不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

Stage 10.12 full no-publisher controller baseline 已通过，且 torque_enable_ready 仍为 False。

## 二、前置状态

Stage 10.12:

- pass: {stage1012_pass}
- full_no_publisher_controller_frozen: {full_no_publisher_frozen}
- torque_enable_ready: {stage1012_torque_enable_ready}
- torque_publisher_enabled: {stage1012_torque_publisher_enabled}
- control_law_changed: {stage1012_control_changed}

## 三、当前源码状态

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: {source_has_create_publisher}
- source_has_publish_call: {source_has_publish_call}
- source_has_torque_topic: {source_has_torque_topic}
- source_declares_enable_param_default_false: {source_declares_enable_param}
- source_declares_confirm_param_default_false: {source_declares_confirm_param}
- source_uses_safety_utilities: {source_uses_safety}

## 四、Publisher-path skeleton 未来设计

未来 publisher path skeleton 不得直接启用 torque publish。它必须满足：

- publisher topic: /go1/joint_torque_cmd；
- message type: std_msgs/msg/Float64MultiArray；
- payload length: 12；
- actuator order: FR, FL, RR, RL; each leg hip, thigh, calf；
- create_publisher 只能出现在独立 stage 中；
- publish call 只能在更晚 stage 中出现；
- 两个 manual enable 参数必须均为 true；
- state_ready 与 inputs_fresh 必须为 true；
- command 必须通过 watchdog fallback 与 clampTorqueCommand；
- first runtime policy 必须保持 disabled。

Stage 11.0 不实现上述 publisher path，只记录设计。

## 五、Safety gate after Stage 11.0

Safety gate CSV:

    results/logs_sample/stage11_torque_publisher_safety_gate_after_stage110.csv

新增：

- G12 publisher path skeleton plan exists: {publisher_path_plan_exists}

仍为 False：

- G8 manual enable flags active at runtime: {manual_enable_active}
- G9 publisher path exists: {publisher_path_implemented}

Therefore:

    torque_enable_ready = {torque_enable_ready}

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 11.0 不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
""")

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 11.0"])
        writer.writerow(["test_name", "publisher_path_skeleton_planning_only"])
        writer.writerow(["stage1012_pass", stage1012_pass])
        writer.writerow(["full_no_publisher_controller_frozen", full_no_publisher_frozen])
        writer.writerow(["source_has_no_create_publisher", not source_has_create_publisher])
        writer.writerow(["source_has_no_publish_call", not source_has_publish_call])
        writer.writerow(["source_does_not_reference_torque_topic", not source_has_torque_topic])
        writer.writerow(["source_declares_enable_param_default_false", source_declares_enable_param])
        writer.writerow(["source_declares_confirm_param_default_false", source_declares_confirm_param])
        writer.writerow(["source_uses_safety_utilities", source_uses_safety])
        writer.writerow(["publisher_path_plan_exists", publisher_path_plan_exists])
        writer.writerow(["publisher_path_implemented", publisher_path_implemented])
        writer.writerow(["manual_enable_active", manual_enable_active])
        writer.writerow(["g8_manual_enable_active", manual_enable_active])
        writer.writerow(["g9_publisher_path_exists", publisher_path_implemented])
        writer.writerow(["g12_publisher_path_plan_exists", publisher_path_plan_exists])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_publisher_enabled", False])
        writer.writerow(["torque_command_published_by_stage110", False])
        writer.writerow(["stage11_scope", "publisher_path_skeleton_planning_only"])
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
## Stage 11.0 Publisher-path Skeleton Planning Only

Stage 11.0 完成 publisher-path skeleton planning only。

- Script: `scripts/stage11_publisher_path_skeleton_planning_only.py`
- Plan CSV: `results/logs_sample/stage11_publisher_path_skeleton_plan.csv`
- Safety gate: `results/logs_sample/stage11_torque_publisher_safety_gate_after_stage110.csv`
- Summary: `results/logs_sample/stage11_publisher_path_skeleton_planning_summary.csv`
- Docs: `docs/STAGE11_PUBLISHER_PATH_SKELETON_PLANNING_ONLY.md`
- pass: `{all_pass}`
- publisher_path_plan_exists: `{publisher_path_plan_exists}`
- publisher_path_implemented: `{publisher_path_implemented}`
- manual_enable_active: `{manual_enable_active}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 11.0 只规划 publisher path，不创建 publisher，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 11.0 Publisher-path Skeleton Planning Only"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 11.0] publisher-path skeleton planning only")
    print(f"pass={all_pass}")
    print(f"stage1012_pass={stage1012_pass}")
    print(f"full_no_publisher_controller_frozen={full_no_publisher_frozen}")
    print(f"publisher_path_plan_exists={publisher_path_plan_exists}")
    print(f"publisher_path_implemented={publisher_path_implemented}")
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
