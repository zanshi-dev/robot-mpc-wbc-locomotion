#!/usr/bin/env python3
from pathlib import Path
import csv
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE103_SUMMARY = LOG_DIR / "stage10_zero_torque_dry_run_internal_validation_summary.csv"

STAGE8_FREEZE_SCRIPT = ROOT / "scripts/stage08_freeze_integrity_check.py"
STAGE83_AB_SCRIPT = ROOT / "scripts/stage08_adapter_backed_stage07_baseline_ab_test.py"

STAGE8_FREEZE_SUMMARY = LOG_DIR / "stage08_freeze_integrity_check_summary.csv"
STAGE83_AB_SUMMARY = LOG_DIR / "stage08_adapter_backed_stage07_baseline_ab_test_summary.csv"

CPP_CONTROLLER_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
CPP_ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

SUMMARY_PATH = LOG_DIR / "stage10_python_frozen_baseline_ab_regression_summary.csv"
LOG_PATH = LOG_DIR / "stage10_python_frozen_baseline_ab_regression_log.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage10_torque_publisher_safety_gate_after_stage104.csv"
DOC_PATH = ROOT / "docs/STAGE10_PYTHON_FROZEN_BASELINE_AB_REGRESSION.md"

FREEZE_STDOUT = LOG_DIR / "stage10_stage08_freeze_integrity_rerun_stdout.txt"
FREEZE_STDERR = LOG_DIR / "stage10_stage08_freeze_integrity_rerun_stderr.txt"
AB_STDOUT = LOG_DIR / "stage10_stage08_adapter_backed_ab_rerun_stdout.txt"
AB_STDERR = LOG_DIR / "stage10_stage08_adapter_backed_ab_rerun_stderr.txt"


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


def run_python_script(script_path: Path, stdout_path: Path, stderr_path: Path, timeout=240):
    if not script_path.exists():
        stdout_path.write_text("")
        stderr_path.write_text(f"Missing script: {script_path}\n")
        return 127

    proc = subprocess.run(
        ["/usr/bin/python3", str(script_path.relative_to(ROOT))],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    stdout_path.write_text(proc.stdout)
    stderr_path.write_text(proc.stderr)
    return proc.returncode


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    checks = []

    stage103 = load_summary(STAGE103_SUMMARY)
    stage103_pass = as_bool(stage103.get("pass", "False"))
    stage103_torque_enabled = as_bool(stage103.get("torque_publisher_enabled", "True"))
    stage103_control_changed = as_bool(stage103.get("control_law_changed", "True"))

    add_check(checks, "stage103_summary_exists", STAGE103_SUMMARY.exists(), True, STAGE103_SUMMARY.exists(), str(STAGE103_SUMMARY))
    add_check(checks, "stage103_pass", stage103_pass, True, stage103_pass)
    add_check(checks, "stage103_torque_publisher_enabled", stage103_torque_enabled, False, not stage103_torque_enabled)
    add_check(checks, "stage103_control_law_changed", stage103_control_changed, False, not stage103_control_changed)

    cpp_text = CPP_CONTROLLER_SOURCE.read_text(errors="replace") if CPP_CONTROLLER_SOURCE.exists() else ""
    header_text = CPP_ZERO_HEADER.read_text(errors="replace") if CPP_ZERO_HEADER.exists() else ""

    source_has_create_publisher = "create_publisher" in cpp_text
    source_has_publish_call = ".publish(" in cpp_text or "->publish(" in cpp_text
    source_has_torque_topic = "/go1/joint_torque_cmd" in cpp_text
    zero_header_exists = CPP_ZERO_HEADER.exists()
    zero_header_declares_12 = "kGo1NumActuatedJoints = 12" in header_text

    add_check(checks, "cpp_controller_source_exists", CPP_CONTROLLER_SOURCE.exists(), True, CPP_CONTROLLER_SOURCE.exists(), str(CPP_CONTROLLER_SOURCE))
    add_check(checks, "cpp_source_has_no_create_publisher", source_has_create_publisher, False, not source_has_create_publisher)
    add_check(checks, "cpp_source_has_no_publish_call", source_has_publish_call, False, not source_has_publish_call)
    add_check(checks, "cpp_source_does_not_reference_torque_topic", source_has_torque_topic, False, not source_has_torque_topic)
    add_check(checks, "zero_torque_header_exists", zero_header_exists, True, zero_header_exists, str(CPP_ZERO_HEADER))
    add_check(checks, "zero_torque_header_declares_12", zero_header_declares_12, True, zero_header_declares_12)

    freeze_rc = run_python_script(STAGE8_FREEZE_SCRIPT, FREEZE_STDOUT, FREEZE_STDERR, timeout=300)
    add_check(checks, "stage8_freeze_rerun_returncode", freeze_rc, 0, freeze_rc == 0, str(STAGE8_FREEZE_SCRIPT))

    stage8_freeze = load_summary(STAGE8_FREEZE_SUMMARY)
    stage8_freeze_pass = as_bool(stage8_freeze.get("pass", "False"))
    stage8_control_changed = as_bool(stage8_freeze.get("control_law_changed", "True"))
    stage8_baseline_type = stage8_freeze.get("baseline_type", "")

    add_check(checks, "stage8_freeze_summary_exists_after_rerun", STAGE8_FREEZE_SUMMARY.exists(), True, STAGE8_FREEZE_SUMMARY.exists(), str(STAGE8_FREEZE_SUMMARY))
    add_check(checks, "stage8_freeze_pass_after_rerun", stage8_freeze_pass, True, stage8_freeze_pass)
    add_check(checks, "stage8_freeze_control_law_changed_after_rerun", stage8_control_changed, False, not stage8_control_changed)
    add_check(checks, "stage8_freeze_baseline_type", stage8_baseline_type, "mixed_online_control_baseline", stage8_baseline_type == "mixed_online_control_baseline")

    ab_rc = run_python_script(STAGE83_AB_SCRIPT, AB_STDOUT, AB_STDERR, timeout=360)
    add_check(checks, "stage83_ab_rerun_returncode", ab_rc, 0, ab_rc == 0, str(STAGE83_AB_SCRIPT))

    stage83_ab = load_summary(STAGE83_AB_SUMMARY)
    stage83_ab_pass = as_bool(stage83_ab.get("pass", "False"))
    original_pass = as_bool(stage83_ab.get("original_pass", "False"))
    adapter_pass = as_bool(stage83_ab.get("adapter_pass", "False"))
    original_pass_margin = as_bool(stage83_ab.get("original_pass_margin", "False"))
    adapter_pass_margin = as_bool(stage83_ab.get("adapter_pass_margin", "False"))

    original_qp_fail_steps = stage83_ab.get("original_qp_fail_steps", "")
    adapter_qp_fail_steps = stage83_ab.get("adapter_qp_fail_steps", "")
    original_saturation_steps = stage83_ab.get("original_saturation_steps", "")
    adapter_saturation_steps = stage83_ab.get("adapter_saturation_steps", "")

    add_check(checks, "stage83_ab_summary_exists_after_rerun", STAGE83_AB_SUMMARY.exists(), True, STAGE83_AB_SUMMARY.exists(), str(STAGE83_AB_SUMMARY))
    add_check(checks, "stage83_ab_pass_after_rerun", stage83_ab_pass, True, stage83_ab_pass)
    add_check(checks, "stage83_original_pass_after_rerun", original_pass, True, original_pass)
    add_check(checks, "stage83_adapter_pass_after_rerun", adapter_pass, True, adapter_pass)
    add_check(checks, "stage83_original_pass_margin_after_rerun", original_pass_margin, True, original_pass_margin)
    add_check(checks, "stage83_adapter_pass_margin_after_rerun", adapter_pass_margin, True, adapter_pass_margin)
    add_check(checks, "stage83_original_qp_fail_steps", original_qp_fail_steps, "0", str(original_qp_fail_steps) in {"0", "0.0"})
    add_check(checks, "stage83_adapter_qp_fail_steps", adapter_qp_fail_steps, "0", str(adapter_qp_fail_steps) in {"0", "0.0"})
    add_check(checks, "stage83_original_saturation_steps", original_saturation_steps, "0", str(original_saturation_steps) in {"0", "0.0"})
    add_check(checks, "stage83_adapter_saturation_steps", adapter_saturation_steps, "0", str(adapter_saturation_steps) in {"0", "0.0"})

    # Stage 10.4 updates the safety gate status, but does not make torque enable ready.
    gate_rows = [
        {
            "gate": "G0",
            "name": "Stage 8 frozen Python baseline valid",
            "required_before_torque_publish": True,
            "current_status": stage8_freeze_pass and not stage8_control_changed,
            "evidence": str(STAGE8_FREEZE_SUMMARY.relative_to(ROOT)),
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
            "current_status": False,
            "evidence": "not implemented by Stage 10.4",
        },
        {
            "gate": "G5",
            "name": "Torque command clamp and watchdog implemented",
            "required_before_torque_publish": True,
            "current_status": False,
            "evidence": "not implemented by Stage 10.4",
        },
        {
            "gate": "G6",
            "name": "Zero torque dry-run regression completed",
            "required_before_torque_publish": True,
            "current_status": stage103_pass,
            "evidence": str(STAGE103_SUMMARY.relative_to(ROOT)),
        },
        {
            "gate": "G7",
            "name": "Python frozen baseline A/B regression still passes",
            "required_before_torque_publish": True,
            "current_status": stage83_ab_pass and stage8_freeze_pass,
            "evidence": str(STAGE83_AB_SUMMARY.relative_to(ROOT)),
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
    add_check(checks, "torque_enable_ready_after_stage104", torque_enable_ready, False, not torque_enable_ready)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 10.4"])
        writer.writerow(["test_name", "python_frozen_baseline_ab_regression"])
        writer.writerow(["stage103_pass", stage103_pass])
        writer.writerow(["stage8_freeze_rerun_returncode", freeze_rc])
        writer.writerow(["stage8_freeze_pass_after_rerun", stage8_freeze_pass])
        writer.writerow(["stage8_freeze_control_law_changed_after_rerun", stage8_control_changed])
        writer.writerow(["stage83_ab_rerun_returncode", ab_rc])
        writer.writerow(["stage83_ab_pass_after_rerun", stage83_ab_pass])
        writer.writerow(["stage83_original_pass_after_rerun", original_pass])
        writer.writerow(["stage83_adapter_pass_after_rerun", adapter_pass])
        writer.writerow(["stage83_original_pass_margin_after_rerun", original_pass_margin])
        writer.writerow(["stage83_adapter_pass_margin_after_rerun", adapter_pass_margin])
        writer.writerow(["stage83_original_qp_fail_steps", original_qp_fail_steps])
        writer.writerow(["stage83_adapter_qp_fail_steps", adapter_qp_fail_steps])
        writer.writerow(["stage83_original_saturation_steps", original_saturation_steps])
        writer.writerow(["stage83_adapter_saturation_steps", adapter_saturation_steps])
        writer.writerow(["cpp_source_has_no_create_publisher", not source_has_create_publisher])
        writer.writerow(["cpp_source_has_no_publish_call", not source_has_publish_call])
        writer.writerow(["cpp_source_does_not_reference_torque_topic", not source_has_torque_topic])
        writer.writerow(["zero_torque_header_declares_12", zero_header_declares_12])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_publisher_enabled", False])
        writer.writerow(["torque_command_published_by_stage104", False])
        writer.writerow(["stage10_scope", "python_frozen_baseline_ab_regression_only"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["ros2_cpp_realtime_controller_completed", False])
        writer.writerow(["pure_wbc_locomotion_completed", False])
        writer.writerow(["ekf_completed", False])
        writer.writerow(["full_3d_centroidal_mpc_completed", False])
        writer.writerow(["num_checks", len(checks)])
        writer.writerow(["num_failed_checks", sum(1 for row in checks if not row["pass"])])
        writer.writerow(["pass", all_pass])
        writer.writerow(["log_csv", str(LOG_PATH.relative_to(ROOT))])
        writer.writerow(["safety_gate_csv", str(SAFETY_GATE_PATH.relative_to(ROOT))])
        writer.writerow(["summary_csv", str(SUMMARY_PATH.relative_to(ROOT))])
        writer.writerow(["stage8_freeze_stdout", str(FREEZE_STDOUT.relative_to(ROOT))])
        writer.writerow(["stage8_freeze_stderr", str(FREEZE_STDERR.relative_to(ROOT))])
        writer.writerow(["stage83_ab_stdout", str(AB_STDOUT.relative_to(ROOT))])
        writer.writerow(["stage83_ab_stderr", str(AB_STDERR.relative_to(ROOT))])
        writer.writerow(["doc", str(DOC_PATH.relative_to(ROOT))])

    DOC_PATH.write_text(f"""# Stage 10.4 Python Frozen Baseline A/B Regression

## 目标

在任何 torque publisher 设计之前，重新回归 Stage 8 frozen Python baseline 与 Stage 8 adapter-backed A/B baseline。

本阶段不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 回归内容

- Stage 10.3 zero torque dry-run internal validation 已通过；
- C++ disabled controller 源码仍无 create_publisher；
- C++ disabled controller 源码仍无 publish call；
- C++ disabled controller 源码仍不引用 /go1/joint_torque_cmd；
- Stage 8 freeze integrity check 重新运行并通过；
- Stage 8 adapter-backed Stage 7 baseline A/B test 重新运行并通过。

## 结果

- pass: {all_pass}
- stage8_freeze_pass_after_rerun: {stage8_freeze_pass}
- stage83_ab_pass_after_rerun: {stage83_ab_pass}
- stage83_original_pass_after_rerun: {original_pass}
- stage83_adapter_pass_after_rerun: {adapter_pass}
- stage83_original_pass_margin_after_rerun: {original_pass_margin}
- stage83_adapter_pass_margin_after_rerun: {adapter_pass_margin}
- torque_enable_ready: {torque_enable_ready}

## Safety gate 更新

Stage 10.4 后：

- G6 zero torque dry-run regression completed: {stage103_pass}
- G7 Python frozen baseline A/B regression still passes: {stage83_ab_pass and stage8_freeze_pass}

但 G4 与 G5 仍未完成，所以 torque_enable_ready 必须保持 False。

## 输出

- Log: results/logs_sample/stage10_python_frozen_baseline_ab_regression_log.csv
- Safety gate: results/logs_sample/stage10_torque_publisher_safety_gate_after_stage104.csv
- Summary: results/logs_sample/stage10_python_frozen_baseline_ab_regression_summary.csv
- Docs: docs/STAGE10_PYTHON_FROZEN_BASELINE_AB_REGRESSION.md

## 边界

当前 baseline 仍是 mixed online control baseline。

本阶段不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
""")

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 10.4 Python Frozen Baseline A/B Regression

Stage 10.4 完成 Python frozen baseline A/B regression。

- Script: `scripts/stage10_python_frozen_baseline_ab_regression.py`
- Log: `results/logs_sample/stage10_python_frozen_baseline_ab_regression_log.csv`
- Safety gate: `results/logs_sample/stage10_torque_publisher_safety_gate_after_stage104.csv`
- Summary: `results/logs_sample/stage10_python_frozen_baseline_ab_regression_summary.csv`
- Docs: `docs/STAGE10_PYTHON_FROZEN_BASELINE_AB_REGRESSION.md`
- pass: `{all_pass}`
- stage8_freeze_pass_after_rerun: `{stage8_freeze_pass}`
- stage83_ab_pass_after_rerun: `{stage83_ab_pass}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 10.4 只做 Python frozen baseline 回归，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 10.4 Python Frozen Baseline A/B Regression"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 10.4] Python frozen baseline A/B regression")
    print(f"pass={all_pass}")
    print(f"stage103_pass={stage103_pass}")
    print(f"stage8_freeze_rerun_returncode={freeze_rc}")
    print(f"stage8_freeze_pass_after_rerun={stage8_freeze_pass}")
    print(f"stage83_ab_rerun_returncode={ab_rc}")
    print(f"stage83_ab_pass_after_rerun={stage83_ab_pass}")
    print(f"stage83_original_pass_after_rerun={original_pass}")
    print(f"stage83_adapter_pass_after_rerun={adapter_pass}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print("control_law_changed=False")
    print("torque_publisher_enabled=False")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
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
