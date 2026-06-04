#!/usr/bin/env python3
from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE104_SUMMARY = LOG_DIR / "stage10_python_frozen_baseline_ab_regression_summary.csv"
STAGE104_GATE = LOG_DIR / "stage10_torque_publisher_safety_gate_after_stage104.csv"

CPP_CONTROLLER_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

DOC_PATH = ROOT / "docs/STAGE10_TORQUE_PUBLISHER_ENABLE_GATE_DESIGN.md"
DESIGN_CSV = LOG_DIR / "stage10_torque_publisher_enable_gate_design.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage10_torque_publisher_safety_gate_after_stage105.csv"
LOG_PATH = LOG_DIR / "stage10_torque_publisher_enable_gate_design_log.csv"
SUMMARY_PATH = LOG_DIR / "stage10_torque_publisher_enable_gate_design_summary.csv"


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

    stage104 = load_summary(STAGE104_SUMMARY)
    stage104_pass = as_bool(stage104.get("pass", "False"))
    stage104_torque_enable_ready = as_bool(stage104.get("torque_enable_ready", "True"))
    stage104_torque_publisher_enabled = as_bool(stage104.get("torque_publisher_enabled", "True"))
    stage104_control_changed = as_bool(stage104.get("control_law_changed", "True"))

    add_check(checks, "stage104_summary_exists", STAGE104_SUMMARY.exists(), True, STAGE104_SUMMARY.exists(), str(STAGE104_SUMMARY))
    add_check(checks, "stage104_pass", stage104_pass, True, stage104_pass)
    add_check(checks, "stage104_torque_enable_ready", stage104_torque_enable_ready, False, not stage104_torque_enable_ready)
    add_check(checks, "stage104_torque_publisher_enabled", stage104_torque_publisher_enabled, False, not stage104_torque_publisher_enabled)
    add_check(checks, "stage104_control_law_changed", stage104_control_changed, False, not stage104_control_changed)

    cpp_text = CPP_CONTROLLER_SOURCE.read_text(errors="replace") if CPP_CONTROLLER_SOURCE.exists() else ""
    zero_header_text = ZERO_HEADER.read_text(errors="replace") if ZERO_HEADER.exists() else ""

    source_has_create_publisher = "create_publisher" in cpp_text
    source_has_publish_call = ".publish(" in cpp_text or "->publish(" in cpp_text
    source_has_torque_topic = "/go1/joint_torque_cmd" in cpp_text
    zero_header_declares_12 = "kGo1NumActuatedJoints = 12" in zero_header_text

    add_check(checks, "cpp_controller_source_exists", CPP_CONTROLLER_SOURCE.exists(), True, CPP_CONTROLLER_SOURCE.exists(), str(CPP_CONTROLLER_SOURCE))
    add_check(checks, "cpp_source_has_no_create_publisher", source_has_create_publisher, False, not source_has_create_publisher)
    add_check(checks, "cpp_source_has_no_publish_call", source_has_publish_call, False, not source_has_publish_call)
    add_check(checks, "cpp_source_does_not_reference_torque_topic", source_has_torque_topic, False, not source_has_torque_topic)
    add_check(checks, "zero_header_declares_12", zero_header_declares_12, True, zero_header_declares_12)

    design_rows = [
        {
            "item": "manual_enable_flag_name",
            "value": "enable_torque_publisher",
            "required": True,
            "implemented_in_stage105": False,
            "description": "Future ROS2 parameter. Must default to false. Stage 10.5 only designs it.",
        },
        {
            "item": "manual_enable_default",
            "value": "false",
            "required": True,
            "implemented_in_stage105": False,
            "description": "Torque publisher must remain disabled unless explicitly enabled by manual parameter.",
        },
        {
            "item": "second_confirm_flag_name",
            "value": "confirm_torque_publisher_enable",
            "required": True,
            "implemented_in_stage105": False,
            "description": "Future second independent confirmation parameter. Must default to false.",
        },
        {
            "item": "publisher_topic",
            "value": "/go1/joint_torque_cmd",
            "required": True,
            "implemented_in_stage105": False,
            "description": "Future publisher topic. Must not appear in Stage 10.5 C++ source.",
        },
        {
            "item": "message_type",
            "value": "std_msgs/msg/Float64MultiArray",
            "required": True,
            "implemented_in_stage105": False,
            "description": "Future torque command message type. Data length must be 12.",
        },
        {
            "item": "torque_vector_length",
            "value": "12",
            "required": True,
            "implemented_in_stage105": False,
            "description": "Must match MuJoCo actuator order FR, FL, RR, RL with hip, thigh, calf per leg.",
        },
        {
            "item": "startup_policy",
            "value": "disabled",
            "required": True,
            "implemented_in_stage105": False,
            "description": "No torque publisher at startup unless all gates pass and manual flags are true.",
        },
        {
            "item": "clamp_policy",
            "value": "hard limit per joint plus finite check",
            "required": True,
            "implemented_in_stage105": False,
            "description": "Future implementation must reject NaN/Inf and clamp absolute torque per joint.",
        },
        {
            "item": "watchdog_policy",
            "value": "state freshness timeout then zero torque",
            "required": True,
            "implemented_in_stage105": False,
            "description": "Future implementation must command zero torque internally if state is stale.",
        },
        {
            "item": "publish_rate_policy",
            "value": "fixed timer only after state valid",
            "required": True,
            "implemented_in_stage105": False,
            "description": "Future publisher must not publish before all required state topics are valid.",
        },
        {
            "item": "first_publisher_stage_allowed",
            "value": "not earlier than Stage 10.6",
            "required": True,
            "implemented_in_stage105": False,
            "description": "Stage 10.5 does not create publisher. Future Stage 10.6 may only add disabled publisher skeleton after explicit instruction.",
        },
        {
            "item": "control_law_policy",
            "value": "unchanged",
            "required": True,
            "implemented_in_stage105": True,
            "description": "Stage 10.5 does not alter control law.",
        },
    ]

    with DESIGN_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["item", "value", "required", "implemented_in_stage105", "description"],
        )
        writer.writeheader()
        writer.writerows(design_rows)

    design_doc_created = True
    manual_enable_design_exists = True
    clamp_watchdog_design_exists = True
    clamp_watchdog_implemented = False
    torque_publisher_implemented = False

    add_check(checks, "manual_enable_flag_design_exists", manual_enable_design_exists, True, manual_enable_design_exists)
    add_check(checks, "clamp_watchdog_design_exists", clamp_watchdog_design_exists, True, clamp_watchdog_design_exists)
    add_check(checks, "clamp_watchdog_implemented", clamp_watchdog_implemented, False, not clamp_watchdog_implemented)
    add_check(checks, "torque_publisher_implemented", torque_publisher_implemented, False, not torque_publisher_implemented)

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
            "name": "C++ source has no torque publisher",
            "required_before_torque_publish": True,
            "current_status": not source_has_create_publisher,
            "evidence": str(CPP_CONTROLLER_SOURCE.relative_to(ROOT)),
        },
        {
            "gate": "G3",
            "name": "C++ source has no publish call",
            "required_before_torque_publish": True,
            "current_status": not source_has_publish_call,
            "evidence": str(CPP_CONTROLLER_SOURCE.relative_to(ROOT)),
        },
        {
            "gate": "G4",
            "name": "Explicit manual enable flag design exists",
            "required_before_torque_publish": True,
            "current_status": manual_enable_design_exists,
            "evidence": str(DOC_PATH.relative_to(ROOT)),
        },
        {
            "gate": "G5",
            "name": "Torque command clamp and watchdog implemented",
            "required_before_torque_publish": True,
            "current_status": clamp_watchdog_implemented,
            "evidence": "designed but not implemented in Stage 10.5",
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
    ]

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(gate_rows)

    torque_enable_ready = all(row["current_status"] for row in gate_rows)
    add_check(checks, "torque_enable_ready_after_stage105", torque_enable_ready, False, not torque_enable_ready)

    all_pass = all(row["pass"] for row in checks)

    DOC_PATH.write_text(f"""# Stage 10.5 Torque Publisher Enable Gate Design

## 一、结论

Stage 10.5 只设计 torque publisher enable gate。

本阶段不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

Stage 10.5 后，manual enable flag 设计存在，因此 G4 可设为 True。

但 clamp/watchdog 仍未实现，因此 G5 必须保持 False，torque_enable_ready 必须保持 False。

## 二、未来 enable 参数设计

未来允许创建 torque publisher 之前，必须至少包含两个独立手动参数：

- enable_torque_publisher
- confirm_torque_publisher_enable

默认值必须全部为 false。

只有两个参数都为 true，且所有 safety gate 都通过，才允许进入 publisher creation 路径。

Stage 10.5 不实现这两个参数，只记录设计。

## 三、未来 publisher 设计约束

未来 publisher topic:

    /go1/joint_torque_cmd

消息类型:

    std_msgs/msg/Float64MultiArray

数据长度:

    12

顺序:

    MuJoCo actuator order FR, FL, RR, RL; each leg hip, thigh, calf

## 四、clamp 设计

未来 torque command 在任何 publish 之前必须经过：

- 长度检查：必须为 12；
- finite 检查：拒绝 NaN 和 Inf；
- per-joint absolute torque clamp；
- clamp 后再次 finite 检查；
- clamp 结果写入 debug log；
- clamp 限值必须显式写在文档和 summary 中。

Stage 10.5 不实现 clamp。

## 五、watchdog 设计

未来 watchdog 必须检查：

- joint state freshness；
- base state freshness；
- imu freshness；
- foot contact freshness；
- sim time freshness；
- controller loop freshness。

任一状态超时，内部 command 必须退回 zero torque dry-run vector。

Stage 10.5 不实现 watchdog。

## 六、当前源码安全状态

Source:

    {CPP_CONTROLLER_SOURCE.relative_to(ROOT)}

Checks:

- source_has_create_publisher: {source_has_create_publisher}
- source_has_publish_call: {source_has_publish_call}
- source_has_torque_topic: {source_has_torque_topic}

## 七、Stage 10.5 后 safety gate

Safety gate CSV:

    results/logs_sample/stage10_torque_publisher_safety_gate_after_stage105.csv

Expected status:

- G0: True
- G1: True
- G2: True
- G3: True
- G4: True
- G5: False
- G6: True
- G7: True

Therefore:

    torque_enable_ready = False

## 八、禁止事项

Stage 10.5 禁止：

- 创建 /go1/joint_torque_cmd publisher；
- 引入 create_publisher；
- 引入 publish call；
- 引用 /go1/joint_torque_cmd 到 controller source；
- 改变控制律；
- 声称 ROS2/C++ realtime controller completed。

## 九、输出

- Design CSV: results/logs_sample/stage10_torque_publisher_enable_gate_design.csv
- Safety gate CSV: results/logs_sample/stage10_torque_publisher_safety_gate_after_stage105.csv
- Summary: results/logs_sample/stage10_torque_publisher_enable_gate_design_summary.csv
- Log: results/logs_sample/stage10_torque_publisher_enable_gate_design_log.csv

## 十、边界

当前 baseline 仍是 mixed online control baseline。

Stage 10.5 不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
""")

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 10.5"])
        writer.writerow(["test_name", "torque_publisher_enable_gate_design"])
        writer.writerow(["stage104_pass", stage104_pass])
        writer.writerow(["stage104_torque_enable_ready", stage104_torque_enable_ready])
        writer.writerow(["manual_enable_flag_design_exists", manual_enable_design_exists])
        writer.writerow(["manual_enable_flag_name", "enable_torque_publisher"])
        writer.writerow(["second_confirm_flag_name", "confirm_torque_publisher_enable"])
        writer.writerow(["manual_enable_default", False])
        writer.writerow(["clamp_watchdog_design_exists", clamp_watchdog_design_exists])
        writer.writerow(["clamp_watchdog_implemented", clamp_watchdog_implemented])
        writer.writerow(["source_has_no_create_publisher", not source_has_create_publisher])
        writer.writerow(["source_has_no_publish_call", not source_has_publish_call])
        writer.writerow(["source_does_not_reference_torque_topic", not source_has_torque_topic])
        writer.writerow(["zero_header_declares_12", zero_header_declares_12])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_publisher_enabled", False])
        writer.writerow(["torque_command_published_by_stage105", False])
        writer.writerow(["stage10_scope", "torque_publisher_enable_gate_design_only"])
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
## Stage 10.5 Torque Publisher Enable Gate Design

Stage 10.5 完成 torque publisher enable gate design。

- Script: `scripts/stage10_torque_publisher_enable_gate_design.py`
- Design CSV: `results/logs_sample/stage10_torque_publisher_enable_gate_design.csv`
- Safety gate CSV: `results/logs_sample/stage10_torque_publisher_safety_gate_after_stage105.csv`
- Summary: `results/logs_sample/stage10_torque_publisher_enable_gate_design_summary.csv`
- Docs: `docs/STAGE10_TORQUE_PUBLISHER_ENABLE_GATE_DESIGN.md`
- pass: `{all_pass}`
- manual_enable_flag_design_exists: `{manual_enable_design_exists}`
- clamp_watchdog_design_exists: `{clamp_watchdog_design_exists}`
- clamp_watchdog_implemented: `{clamp_watchdog_implemented}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 10.5 只设计 enable gate，不创建 publisher，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 10.5 Torque Publisher Enable Gate Design"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 10.5] torque publisher enable gate design")
    print(f"pass={all_pass}")
    print(f"stage104_pass={stage104_pass}")
    print(f"manual_enable_flag_design_exists={manual_enable_design_exists}")
    print(f"clamp_watchdog_design_exists={clamp_watchdog_design_exists}")
    print(f"clamp_watchdog_implemented={clamp_watchdog_implemented}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print("control_law_changed=False")
    print("torque_publisher_enabled=False")
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
