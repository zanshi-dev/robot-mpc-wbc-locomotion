#!/usr/bin/env python3
from pathlib import Path
import csv
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE8_FREEZE_SUMMARY = LOG_DIR / "stage08_freeze_integrity_check_summary.csv"
STAGE9_FREEZE_SUMMARY = LOG_DIR / "stage09_0_6_interface_mirror_freeze_summary.csv"

CPP_MIRROR_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_interface/src/interface_mirror_node.cpp"

DOC_PATH = ROOT / "docs/STAGE10_CONTROLLER_IMPLEMENTATION_PLAN_AND_SAFETY_GATE.md"
LOG_PATH = LOG_DIR / "stage10_controller_implementation_plan_and_safety_gate_log.csv"
SUMMARY_PATH = LOG_DIR / "stage10_controller_implementation_plan_and_safety_gate_summary.csv"
PLAN_CSV = LOG_DIR / "stage10_controller_implementation_plan.csv"
SAFETY_GATE_CSV = LOG_DIR / "stage10_torque_publisher_safety_gate.csv"


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

    stage8 = load_summary(STAGE8_FREEZE_SUMMARY)
    stage9 = load_summary(STAGE9_FREEZE_SUMMARY)

    stage8_pass = as_bool(stage8.get("pass", "False"))
    stage9_pass = as_bool(stage9.get("pass", "False"))
    stage9_mirror_frozen = as_bool(stage9.get("ros2_cpp_interface_mirror_frozen", "False"))

    stage8_control_changed = as_bool(stage8.get("control_law_changed", "True"))
    stage9_control_changed = as_bool(stage9.get("control_law_changed", "True"))
    stage9_torque_published = as_bool(stage9.get("torque_command_published_by_stage97", "True"))

    add_check(checks, "stage8_freeze_summary_exists", STAGE8_FREEZE_SUMMARY.exists(), True, STAGE8_FREEZE_SUMMARY.exists(), str(STAGE8_FREEZE_SUMMARY))
    add_check(checks, "stage8_freeze_pass", stage8_pass, True, stage8_pass)
    add_check(checks, "stage8_control_law_changed", stage8_control_changed, False, not stage8_control_changed)

    add_check(checks, "stage9_freeze_summary_exists", STAGE9_FREEZE_SUMMARY.exists(), True, STAGE9_FREEZE_SUMMARY.exists(), str(STAGE9_FREEZE_SUMMARY))
    add_check(checks, "stage9_freeze_pass", stage9_pass, True, stage9_pass)
    add_check(checks, "stage9_interface_mirror_frozen", stage9_mirror_frozen, True, stage9_mirror_frozen)
    add_check(checks, "stage9_control_law_changed", stage9_control_changed, False, not stage9_control_changed)
    add_check(checks, "stage9_torque_published", stage9_torque_published, False, not stage9_torque_published)

    cpp_exists = CPP_MIRROR_SOURCE.exists()
    cpp_text = CPP_MIRROR_SOURCE.read_text(errors="replace") if cpp_exists else ""

    source_has_create_publisher = "create_publisher" in cpp_text
    source_has_publish_call = ".publish(" in cpp_text or "->publish(" in cpp_text
    source_observes_torque_topic = "/go1/joint_torque_cmd" in cpp_text and "create_subscription" in cpp_text

    add_check(checks, "cpp_mirror_source_exists", cpp_exists, True, cpp_exists, str(CPP_MIRROR_SOURCE))
    add_check(checks, "cpp_mirror_source_has_no_create_publisher", source_has_create_publisher, False, not source_has_create_publisher)
    add_check(checks, "cpp_mirror_source_has_no_publish_call", source_has_publish_call, False, not source_has_publish_call)
    add_check(checks, "cpp_mirror_observes_torque_topic_only", source_observes_torque_topic, True, source_observes_torque_topic)

    plan_rows = [
        {
            "stage": "Stage 10.1",
            "name": "disabled controller skeleton",
            "allowed": True,
            "torque_publisher_enabled": False,
            "control_law_changed": False,
            "description": "Create C++ controller skeleton with subscriptions and internal state cache only. No torque publisher.",
            "exit_criteria": "Build passes; source check confirms no create_publisher and no publish call.",
        },
        {
            "stage": "Stage 10.2",
            "name": "state cache and schema validator",
            "allowed": True,
            "torque_publisher_enabled": False,
            "control_law_changed": False,
            "description": "Mirror joint/base/imu/contact/sim_time into C++ state cache and validate sizes/orders.",
            "exit_criteria": "Runtime guard shows topic schema stable; no torque publisher.",
        },
        {
            "stage": "Stage 10.3",
            "name": "zero torque dry-run command object",
            "allowed": True,
            "torque_publisher_enabled": False,
            "control_law_changed": False,
            "description": "Compute internal zero torque vector but do not publish it.",
            "exit_criteria": "Internal vector length 12; no ROS publisher; logs only.",
        },
        {
            "stage": "Stage 10.4",
            "name": "Python baseline replay comparison",
            "allowed": True,
            "torque_publisher_enabled": False,
            "control_law_changed": False,
            "description": "Compare C++ state cache observations against Stage 8 frozen Python baseline logs.",
            "exit_criteria": "Field/order checks pass; no controller output used.",
        },
        {
            "stage": "Stage 10.5",
            "name": "torque publisher enable proposal",
            "allowed": False,
            "torque_publisher_enabled": False,
            "control_law_changed": False,
            "description": "Only prepare proposal and explicit gate conditions. Do not enable publisher.",
            "exit_criteria": "Manual approval required before any torque publisher appears in source.",
        },
    ]

    with PLAN_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "stage",
                "name",
                "allowed",
                "torque_publisher_enabled",
                "control_law_changed",
                "description",
                "exit_criteria",
            ],
        )
        writer.writeheader()
        writer.writerows(plan_rows)

    safety_rows = [
        {
            "gate": "G0",
            "name": "Stage 8 frozen Python baseline valid",
            "required_before_torque_publish": True,
            "current_status": stage8_pass and not stage8_control_changed,
            "evidence": str(STAGE8_FREEZE_SUMMARY.relative_to(ROOT)),
        },
        {
            "gate": "G1",
            "name": "Stage 9 interface mirror frozen",
            "required_before_torque_publish": True,
            "current_status": stage9_pass and stage9_mirror_frozen,
            "evidence": str(STAGE9_FREEZE_SUMMARY.relative_to(ROOT)),
        },
        {
            "gate": "G2",
            "name": "C++ source has no torque publisher",
            "required_before_torque_publish": True,
            "current_status": not source_has_create_publisher,
            "evidence": str(CPP_MIRROR_SOURCE.relative_to(ROOT)),
        },
        {
            "gate": "G3",
            "name": "C++ source has no publish call",
            "required_before_torque_publish": True,
            "current_status": not source_has_publish_call,
            "evidence": str(CPP_MIRROR_SOURCE.relative_to(ROOT)),
        },
        {
            "gate": "G4",
            "name": "Explicit manual enable flag design exists",
            "required_before_torque_publish": True,
            "current_status": False,
            "evidence": "not implemented in Stage 10.0",
        },
        {
            "gate": "G5",
            "name": "Torque command clamp and watchdog implemented",
            "required_before_torque_publish": True,
            "current_status": False,
            "evidence": "not implemented in Stage 10.0",
        },
        {
            "gate": "G6",
            "name": "Zero torque dry-run regression completed",
            "required_before_torque_publish": True,
            "current_status": False,
            "evidence": "future Stage 10.3",
        },
        {
            "gate": "G7",
            "name": "Python frozen baseline A/B regression still passes",
            "required_before_torque_publish": True,
            "current_status": False,
            "evidence": "must be rerun before enabling publisher",
        },
    ]

    with SAFETY_GATE_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "gate",
                "name",
                "required_before_torque_publish",
                "current_status",
                "evidence",
            ],
        )
        writer.writeheader()
        writer.writerows(safety_rows)

    torque_enable_ready = all(row["current_status"] for row in safety_rows)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)
    add_check(checks, "stage10_control_law_changed", False, False, True)
    add_check(checks, "stage10_torque_publisher_enabled", False, False, True)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    DOC_PATH.write_text(f"""# Stage 10.0 Controller Implementation Plan and Safety Gate

## 一、结论

Stage 10.0 只生成 C++ controller implementation plan 与 torque publisher safety gate。

本阶段不写 controller，不创建 torque publisher，不调用 publish，不改变控制律。

当前 baseline 仍是 mixed online control baseline，不是 pure full WBC locomotion。

## 二、前置冻结状态

Stage 8 frozen Python baseline:

- summary: `results/logs_sample/stage08_freeze_integrity_check_summary.csv`
- pass: `{stage8_pass}`
- control_law_changed: `{stage8_control_changed}`

Stage 9 ROS2/C++ interface mirror baseline:

- summary: `results/logs_sample/stage09_0_6_interface_mirror_freeze_summary.csv`
- pass: `{stage9_pass}`
- ros2_cpp_interface_mirror_frozen: `{stage9_mirror_frozen}`
- control_law_changed: `{stage9_control_changed}`
- torque_published: `{stage9_torque_published}`

## 三、当前 C++ mirror 安全状态

Source:

    ros2_ws/src/robot_mpc_wbc_cpp_interface/src/interface_mirror_node.cpp

Checks:

- source_has_create_publisher: `{source_has_create_publisher}`
- source_has_publish_call: `{source_has_publish_call}`
- observes /go1/joint_torque_cmd as subscriber: `{source_observes_torque_topic}`

## 四、Stage 10 建议路线

1. Stage 10.1: disabled controller skeleton
2. Stage 10.2: state cache and schema validator
3. Stage 10.3: zero torque dry-run command object
4. Stage 10.4: Python baseline replay comparison
5. Stage 10.5: torque publisher enable proposal

Stage 10.1–10.5 默认 torque publisher disabled。

## 五、Torque publisher safety gate

Safety gate CSV:

    results/logs_sample/stage10_torque_publisher_safety_gate.csv

当前结论：

- torque_enable_ready: `{torque_enable_ready}`

该值必须保持 False，直到显式完成 clamp、watchdog、zero torque dry-run、Python baseline regression 和人工确认。

## 六、禁止事项

Stage 10.0 禁止：

- 创建 /go1/joint_torque_cmd publisher；
- 调用 publish；
- 写入 MuJoCo torque command；
- 声称 ROS2/C++ real-time controller 已完成；
- 声称 pure full WBC locomotion 已完成；
- 改 Stage 8/9 frozen baseline。

## 七、输出文件

- Log: `results/logs_sample/stage10_controller_implementation_plan_and_safety_gate_log.csv`
- Plan CSV: `results/logs_sample/stage10_controller_implementation_plan.csv`
- Safety gate CSV: `results/logs_sample/stage10_torque_publisher_safety_gate.csv`
- Summary: `results/logs_sample/stage10_controller_implementation_plan_and_safety_gate_summary.csv`
- Docs: `docs/STAGE10_CONTROLLER_IMPLEMENTATION_PLAN_AND_SAFETY_GATE.md`

## 八、结果

- pass: `{all_pass}`
- control_law_changed: `False`
- torque_publisher_enabled: `False`
- torque_enable_ready: `{torque_enable_ready}`
""")

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 10.0"])
        writer.writerow(["test_name", "controller_implementation_plan_and_safety_gate"])
        writer.writerow(["stage8_freeze_pass", stage8_pass])
        writer.writerow(["stage9_freeze_pass", stage9_pass])
        writer.writerow(["ros2_cpp_interface_mirror_frozen", stage9_mirror_frozen])
        writer.writerow(["cpp_mirror_source_has_no_create_publisher", not source_has_create_publisher])
        writer.writerow(["cpp_mirror_source_has_no_publish_call", not source_has_publish_call])
        writer.writerow(["cpp_mirror_observes_torque_topic_only", source_observes_torque_topic])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_publisher_enabled", False])
        writer.writerow(["torque_command_published_by_stage100", False])
        writer.writerow(["stage10_scope", "controller_planning_and_safety_gate_only"])
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
        writer.writerow(["safety_gate_csv", str(SAFETY_GATE_CSV.relative_to(ROOT))])
        writer.writerow(["summary_csv", str(SUMMARY_PATH.relative_to(ROOT))])
        writer.writerow(["doc", str(DOC_PATH.relative_to(ROOT))])

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 10.0 Controller Implementation Plan and Safety Gate

Stage 10.0 生成了 controller implementation plan 与 torque publisher safety gate。

- Script: `scripts/stage10_controller_implementation_plan_and_safety_gate.py`
- Log: `results/logs_sample/stage10_controller_implementation_plan_and_safety_gate_log.csv`
- Plan CSV: `results/logs_sample/stage10_controller_implementation_plan.csv`
- Safety gate CSV: `results/logs_sample/stage10_torque_publisher_safety_gate.csv`
- Summary: `results/logs_sample/stage10_controller_implementation_plan_and_safety_gate_summary.csv`
- Docs: `docs/STAGE10_CONTROLLER_IMPLEMENTATION_PLAN_AND_SAFETY_GATE.md`
- pass: `{all_pass}`
- torque_enable_ready: `{torque_enable_ready}`
- control_law_changed: `False`
- torque_publisher_enabled: `False`
- torque_command_published_by_stage100: `False`
- stage10_scope: `controller_planning_and_safety_gate_only`

Stage 10.0 不写 controller，不发布 torque，不改变控制律。后续 Stage 10.1 只能创建 disabled-by-default controller skeleton。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 10.0 Controller Implementation Plan and Safety Gate"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 10.0] controller implementation plan and safety gate")
    print(f"pass={all_pass}")
    print(f"stage8_freeze_pass={stage8_pass}")
    print(f"stage9_freeze_pass={stage9_pass}")
    print(f"ros2_cpp_interface_mirror_frozen={stage9_mirror_frozen}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print("control_law_changed=False")
    print("torque_publisher_enabled=False")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
    print(f"plan_csv={PLAN_CSV.relative_to(ROOT)}")
    print(f"safety_gate_csv={SAFETY_GATE_CSV.relative_to(ROOT)}")
    print(f"summary_csv={SUMMARY_PATH.relative_to(ROOT)}")
    print(f"doc={DOC_PATH.relative_to(ROOT)}")

    if not all_pass:
        print("\\nFailed checks:")
        for row in checks:
            if not row["pass"]:
                print(f"- {row['check']}: value={row['value']} expected={row['expected']} detail={row['detail']}")
        sys.exit(2)


if __name__ == "__main__":
    main()
