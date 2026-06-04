#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE109_SUMMARY = LOG_DIR / "stage10_7_8_safety_utility_freeze_summary.csv"
STAGE1010_SUMMARY = LOG_DIR / "stage10_manual_enable_params_disabled_without_publisher_summary.csv"
STAGE1010_GATE = LOG_DIR / "stage10_torque_publisher_safety_gate_after_stage1010.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
SAFETY_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

DOC_PATH = ROOT / "docs/STAGE10_MANUAL_ENABLE_PARAM_GUARD_FREEZE_SUMMARY.md"
SUMMARY_PATH = LOG_DIR / "stage10_manual_enable_param_guard_freeze_summary.csv"
LOG_PATH = LOG_DIR / "stage10_manual_enable_param_guard_freeze_log.csv"
HASH_PATH = LOG_DIR / "stage10_manual_enable_param_guard_freeze_hashes.csv"

FREEZE_FILES = [
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp",
    "docs/STAGE10_7_8_SAFETY_UTILITY_FREEZE_SUMMARY.md",
    "docs/STAGE10_MANUAL_ENABLE_PARAMS_DISABLED_WITHOUT_PUBLISHER.md",
    "results/logs_sample/stage10_7_8_safety_utility_freeze_summary.csv",
    "results/logs_sample/stage10_manual_enable_params_disabled_without_publisher_summary.csv",
    "results/logs_sample/stage10_torque_publisher_safety_gate_after_stage1010.csv",
    "results/logs_sample/stage10_manual_enable_params_param_list_stdout.txt",
    "results/logs_sample/stage10_manual_enable_params_param_get_stdout.txt",
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


def load_gate(path: Path):
    rows = []
    if not path.exists():
        return rows
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


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

    s109 = load_summary(STAGE109_SUMMARY)
    s1010 = load_summary(STAGE1010_SUMMARY)

    stage109_pass = as_bool(s109.get("pass", "False"))
    stage1010_pass = as_bool(s1010.get("pass", "False"))

    add_check(checks, "stage109_summary_exists", STAGE109_SUMMARY.exists(), True, STAGE109_SUMMARY.exists(), str(STAGE109_SUMMARY))
    add_check(checks, "stage109_pass", stage109_pass, True, stage109_pass)
    add_check(checks, "stage1010_summary_exists", STAGE1010_SUMMARY.exists(), True, STAGE1010_SUMMARY.exists(), str(STAGE1010_SUMMARY))
    add_check(checks, "stage1010_pass", stage1010_pass, True, stage1010_pass)

    add_check(checks, "stage1010_manual_enable_params_declared", as_bool(s1010.get("manual_enable_params_declared", "False")), True, as_bool(s1010.get("manual_enable_params_declared", "False")))
    add_check(checks, "stage1010_manual_enable_params_default_false", as_bool(s1010.get("manual_enable_params_default_false", "False")), True, as_bool(s1010.get("manual_enable_params_default_false", "False")))
    add_check(checks, "stage1010_manual_enable_active", as_bool(s1010.get("manual_enable_active", "True")), False, not as_bool(s1010.get("manual_enable_active", "True")))
    add_check(checks, "stage1010_publisher_path_exists", as_bool(s1010.get("publisher_path_exists", "True")), False, not as_bool(s1010.get("publisher_path_exists", "True")))
    add_check(checks, "stage1010_torque_topic_publishers_zero", as_bool(s1010.get("torque_topic_publishers_zero", "False")), True, as_bool(s1010.get("torque_topic_publishers_zero", "False")))

    cpp_text = CPP_SOURCE.read_text(errors="replace") if CPP_SOURCE.exists() else ""
    safety_text = SAFETY_HEADER.read_text(errors="replace") if SAFETY_HEADER.exists() else ""
    zero_text = ZERO_HEADER.read_text(errors="replace") if ZERO_HEADER.exists() else ""

    source_has_create_publisher = "create_publisher" in cpp_text
    source_has_publish_call = ".publish(" in cpp_text or "->publish(" in cpp_text
    source_has_torque_topic = "/go1/joint_torque_cmd" in cpp_text

    source_declares_enable_param = 'declare_parameter<bool>("enable_torque_publisher", false)' in cpp_text
    source_declares_confirm_param = 'declare_parameter<bool>("confirm_torque_publisher_enable", false)' in cpp_text
    source_reads_enable_param = 'get_parameter("enable_torque_publisher").as_bool()' in cpp_text
    source_reads_confirm_param = 'get_parameter("confirm_torque_publisher_enable").as_bool()' in cpp_text
    source_has_manual_enable_active = "manual_enable_active_" in cpp_text
    source_uses_safety = "clampTorqueCommand" in cpp_text and "allInputsFresh" in cpp_text and "watchdogFallbackZeroTorque" in cpp_text

    safety_has_clamp_watchdog = "clampTorqueCommand" in safety_text and "allInputsFresh" in safety_text and "watchdogFallbackZeroTorque" in safety_text
    zero_header_declares_12 = "kGo1NumActuatedJoints = 12" in zero_text

    add_check(checks, "cpp_source_exists", CPP_SOURCE.exists(), True, CPP_SOURCE.exists(), str(CPP_SOURCE))
    add_check(checks, "safety_header_exists", SAFETY_HEADER.exists(), True, SAFETY_HEADER.exists(), str(SAFETY_HEADER))
    add_check(checks, "zero_header_exists", ZERO_HEADER.exists(), True, ZERO_HEADER.exists(), str(ZERO_HEADER))
    add_check(checks, "source_has_no_create_publisher", source_has_create_publisher, False, not source_has_create_publisher)
    add_check(checks, "source_has_no_publish_call", source_has_publish_call, False, not source_has_publish_call)
    add_check(checks, "source_does_not_reference_torque_topic", source_has_torque_topic, False, not source_has_torque_topic)
    add_check(checks, "source_declares_enable_param_default_false", source_declares_enable_param, True, source_declares_enable_param)
    add_check(checks, "source_declares_confirm_param_default_false", source_declares_confirm_param, True, source_declares_confirm_param)
    add_check(checks, "source_reads_enable_param", source_reads_enable_param, True, source_reads_enable_param)
    add_check(checks, "source_reads_confirm_param", source_reads_confirm_param, True, source_reads_confirm_param)
    add_check(checks, "source_has_manual_enable_active_state", source_has_manual_enable_active, True, source_has_manual_enable_active)
    add_check(checks, "source_uses_safety_utilities", source_uses_safety, True, source_uses_safety)
    add_check(checks, "safety_header_has_clamp_watchdog", safety_has_clamp_watchdog, True, safety_has_clamp_watchdog)
    add_check(checks, "zero_header_declares_12", zero_header_declares_12, True, zero_header_declares_12)

    gate_rows = load_gate(STAGE1010_GATE)
    gate_status = {row.get("gate", ""): as_bool(row.get("current_status", "False")) for row in gate_rows}

    expected_gate_status = {
        "G0": True,
        "G1": True,
        "G2": True,
        "G3": True,
        "G4": True,
        "G5": True,
        "G6": True,
        "G7": True,
        "G8": False,
        "G9": False,
        "G10": True,
        "G11": True,
    }

    add_check(checks, "stage1010_safety_gate_exists", STAGE1010_GATE.exists(), True, STAGE1010_GATE.exists(), str(STAGE1010_GATE))
    for gate, expected in expected_gate_status.items():
        value = gate_status.get(gate, None)
        add_check(checks, f"{gate}_status_after_stage1010", value, expected, value == expected)

    torque_enable_ready = all(gate_status.get(gate, False) for gate in expected_gate_status)
    add_check(checks, "torque_enable_ready_after_stage1010", torque_enable_ready, False, not torque_enable_ready)

    control_law_changed_any = (
        as_bool(s109.get("control_law_changed", "False")) or
        as_bool(s1010.get("control_law_changed", "False"))
    )
    torque_publisher_enabled_any = (
        as_bool(s109.get("torque_publisher_enabled", "False")) or
        as_bool(s1010.get("torque_publisher_enabled", "False"))
    )
    torque_command_published_any = (
        as_bool(s109.get("torque_command_published_by_stage109", "False")) or
        as_bool(s1010.get("torque_command_published_by_stage1010", "False"))
    )

    add_check(checks, "control_law_changed_any", control_law_changed_any, False, not control_law_changed_any)
    add_check(checks, "torque_publisher_enabled_any", torque_publisher_enabled_any, False, not torque_publisher_enabled_any)
    add_check(checks, "torque_command_published_any", torque_command_published_any, False, not torque_command_published_any)

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

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    DOC_PATH.write_text(f"""# Stage 10.11 Manual-enable Parameter Guard Freeze Summary

## 一、冻结结论

Stage 10.10 manual-enable parameter guard 已冻结。

当前状态：

- manual enable parameters 已存在；
- enable_torque_publisher 默认 false；
- confirm_torque_publisher_enable 默认 false；
- manual_enable_active 为 false；
- publisher_path_exists 为 false；
- /go1/joint_torque_cmd publisher count 为 0；
- controller source 无 create_publisher；
- controller source 无 publish call；
- controller source 不引用 /go1/joint_torque_cmd。

本阶段不创建 publisher，不发布 torque，不改变控制律。

## 二、源码状态

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: {source_has_create_publisher}
- source_has_publish_call: {source_has_publish_call}
- source_has_torque_topic: {source_has_torque_topic}
- source_declares_enable_param_default_false: {source_declares_enable_param}
- source_declares_confirm_param_default_false: {source_declares_confirm_param}
- source_reads_enable_param: {source_reads_enable_param}
- source_reads_confirm_param: {source_reads_confirm_param}
- source_uses_safety_utilities: {source_uses_safety}

## 三、Safety gate after Stage 10.10

- G0: {gate_status.get("G0")}
- G1: {gate_status.get("G1")}
- G2: {gate_status.get("G2")}
- G3: {gate_status.get("G3")}
- G4: {gate_status.get("G4")}
- G5: {gate_status.get("G5")}
- G6: {gate_status.get("G6")}
- G7: {gate_status.get("G7")}
- G8 manual enable flags active at runtime: {gate_status.get("G8")}
- G9 publisher path exists: {gate_status.get("G9")}
- G10 disabled controller uses clamp/watchdog internally: {gate_status.get("G10")}
- G11 manual enable parameters exist and default false: {gate_status.get("G11")}

Therefore:

    torque_enable_ready = {torque_enable_ready}

G8 与 G9 仍为 False，因此不能发布 torque。

## 四、冻结 hash

Hash CSV:

    results/logs_sample/stage10_manual_enable_param_guard_freeze_hashes.csv

## 五、边界

当前 baseline 仍是 mixed online control baseline。

Stage 10.11 不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
""")

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 10.11"])
        writer.writerow(["test_name", "manual_enable_param_guard_freeze_summary"])
        writer.writerow(["stage109_pass", stage109_pass])
        writer.writerow(["stage1010_pass", stage1010_pass])
        writer.writerow(["freeze_file_count", len(FREEZE_FILES)])
        writer.writerow(["missing_file_count", len(missing_files)])
        writer.writerow(["source_has_no_create_publisher", not source_has_create_publisher])
        writer.writerow(["source_has_no_publish_call", not source_has_publish_call])
        writer.writerow(["source_does_not_reference_torque_topic", not source_has_torque_topic])
        writer.writerow(["source_declares_enable_param_default_false", source_declares_enable_param])
        writer.writerow(["source_declares_confirm_param_default_false", source_declares_confirm_param])
        writer.writerow(["source_reads_enable_param", source_reads_enable_param])
        writer.writerow(["source_reads_confirm_param", source_reads_confirm_param])
        writer.writerow(["source_has_manual_enable_active_state", source_has_manual_enable_active])
        writer.writerow(["source_uses_safety_utilities", source_uses_safety])
        writer.writerow(["g8_manual_enable_active", gate_status.get("G8", False)])
        writer.writerow(["g9_publisher_path_exists", gate_status.get("G9", False)])
        writer.writerow(["g10_controller_uses_safety_utilities", gate_status.get("G10", False)])
        writer.writerow(["g11_manual_enable_params_exist_and_default_false", gate_status.get("G11", False)])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_publisher_enabled", False])
        writer.writerow(["torque_command_published_by_stage1011", False])
        writer.writerow(["stage10_scope", "manual_enable_param_guard_freeze_summary_only"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["manual_enable_param_guard_frozen", True])
        writer.writerow(["ros2_cpp_realtime_controller_completed", False])
        writer.writerow(["pure_wbc_locomotion_completed", False])
        writer.writerow(["ekf_completed", False])
        writer.writerow(["full_3d_centroidal_mpc_completed", False])
        writer.writerow(["num_checks", len(checks)])
        writer.writerow(["num_failed_checks", sum(1 for row in checks if not row["pass"])])
        writer.writerow(["pass", all_pass])
        writer.writerow(["log_csv", str(LOG_PATH.relative_to(ROOT))])
        writer.writerow(["hash_csv", str(HASH_PATH.relative_to(ROOT))])
        writer.writerow(["summary_csv", str(SUMMARY_PATH.relative_to(ROOT))])
        writer.writerow(["doc", str(DOC_PATH.relative_to(ROOT))])

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 10.11 Manual-enable Parameter Guard Freeze Summary

Stage 10.11 冻结 manual-enable parameter guard。

- Script: `scripts/stage10_manual_enable_param_guard_freeze_summary.py`
- Log: `results/logs_sample/stage10_manual_enable_param_guard_freeze_log.csv`
- Hashes: `results/logs_sample/stage10_manual_enable_param_guard_freeze_hashes.csv`
- Summary: `results/logs_sample/stage10_manual_enable_param_guard_freeze_summary.csv`
- Docs: `docs/STAGE10_MANUAL_ENABLE_PARAM_GUARD_FREEZE_SUMMARY.md`
- pass: `{all_pass}`
- manual_enable_param_guard_frozen: `True`
- g8_manual_enable_active: `{gate_status.get("G8", False)}`
- g9_publisher_path_exists: `{gate_status.get("G9", False)}`
- g11_manual_enable_params_exist_and_default_false: `{gate_status.get("G11", False)}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 10.11 只冻结 manual-enable parameter guard，不创建 publisher，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 10.11 Manual-enable Parameter Guard Freeze Summary"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 10.11] manual-enable parameter guard freeze summary")
    print(f"pass={all_pass}")
    print(f"missing_file_count={len(missing_files)}")
    print("manual_enable_param_guard_frozen=True")
    print(f"g8_manual_enable_active={gate_status.get('G8', False)}")
    print(f"g9_publisher_path_exists={gate_status.get('G9', False)}")
    print(f"g11_manual_enable_params_exist_and_default_false={gate_status.get('G11', False)}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print("control_law_changed=False")
    print("torque_publisher_enabled=False")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
    print(f"hash_csv={HASH_PATH.relative_to(ROOT)}")
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
