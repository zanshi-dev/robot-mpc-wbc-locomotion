#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE_SUMMARIES = {
    "Stage 10.7": LOG_DIR / "stage10_clamp_watchdog_utility_without_publisher_summary.csv",
    "Stage 10.8": LOG_DIR / "stage10_disabled_controller_uses_safety_utilities_summary.csv",
}

SAFETY_GATE = LOG_DIR / "stage10_torque_publisher_safety_gate_after_stage108.csv"

CPP_CONTROLLER_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"
SAFETY_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"

FREEZE_FILES = [
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/torque_safety_contract_check.cpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/CMakeLists.txt",
    "docs/STAGE10_CLAMP_WATCHDOG_UTILITY_WITHOUT_PUBLISHER.md",
    "docs/STAGE10_DISABLED_CONTROLLER_USES_SAFETY_UTILITIES.md",
    "results/logs_sample/stage10_clamp_watchdog_utility_without_publisher_summary.csv",
    "results/logs_sample/stage10_disabled_controller_uses_safety_utilities_summary.csv",
    "results/logs_sample/stage10_clamp_watchdog_utility_clamped_vector.csv",
    "results/logs_sample/stage10_torque_publisher_safety_gate_after_stage107.csv",
    "results/logs_sample/stage10_torque_publisher_safety_gate_after_stage108.csv",
]

DOC_PATH = ROOT / "docs/STAGE10_7_8_SAFETY_UTILITY_FREEZE_SUMMARY.md"
SUMMARY_PATH = LOG_DIR / "stage10_7_8_safety_utility_freeze_summary.csv"
LOG_PATH = LOG_DIR / "stage10_7_8_safety_utility_freeze_log.csv"
HASH_PATH = LOG_DIR / "stage10_7_8_safety_utility_freeze_hashes.csv"


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
    summaries = {}

    for stage, path in STAGE_SUMMARIES.items():
        exists = path.exists()
        add_check(checks, f"{stage}_summary_exists", exists, True, exists, str(path))
        metrics = load_summary(path)
        summaries[stage] = metrics
        stage_pass = as_bool(metrics.get("pass", "False"))
        add_check(checks, f"{stage}_pass", stage_pass, True, stage_pass)

    control_law_changed_any = any(
        as_bool(metrics.get("control_law_changed", "False"))
        for metrics in summaries.values()
    )
    torque_publisher_enabled_any = any(
        as_bool(metrics.get("torque_publisher_enabled", "False"))
        for metrics in summaries.values()
    )
    torque_command_published_any = any(
        as_bool(metrics.get("torque_command_published_by_stage107", "False")) or
        as_bool(metrics.get("torque_command_published_by_stage108", "False"))
        for metrics in summaries.values()
    )

    add_check(checks, "control_law_changed_any", control_law_changed_any, False, not control_law_changed_any)
    add_check(checks, "torque_publisher_enabled_any", torque_publisher_enabled_any, False, not torque_publisher_enabled_any)
    add_check(checks, "torque_command_published_any", torque_command_published_any, False, not torque_command_published_any)

    cpp_text = CPP_CONTROLLER_SOURCE.read_text(errors="replace") if CPP_CONTROLLER_SOURCE.exists() else ""
    safety_text = SAFETY_HEADER.read_text(errors="replace") if SAFETY_HEADER.exists() else ""
    zero_text = ZERO_HEADER.read_text(errors="replace") if ZERO_HEADER.exists() else ""

    source_has_create_publisher = "create_publisher" in cpp_text
    source_has_publish_call = ".publish(" in cpp_text or "->publish(" in cpp_text
    source_has_torque_topic = "/go1/joint_torque_cmd" in cpp_text

    source_includes_safety_header = "torque_safety.hpp" in cpp_text
    source_uses_clamp = "clampTorqueCommand" in cpp_text
    source_uses_watchdog_fresh = "allInputsFresh" in cpp_text
    source_uses_watchdog_fallback = "watchdogFallbackZeroTorque" in cpp_text
    source_has_safe_tau_buffer = "safe_torque_dry_run_" in cpp_text

    safety_has_clamp = "clampTorqueCommand" in safety_text and "TorqueClampConfig" in safety_text
    safety_has_watchdog = "allInputsFresh" in safety_text and "watchdogFallbackZeroTorque" in safety_text
    zero_header_declares_12 = "kGo1NumActuatedJoints = 12" in zero_text

    add_check(checks, "cpp_controller_source_exists", CPP_CONTROLLER_SOURCE.exists(), True, CPP_CONTROLLER_SOURCE.exists(), str(CPP_CONTROLLER_SOURCE))
    add_check(checks, "safety_header_exists", SAFETY_HEADER.exists(), True, SAFETY_HEADER.exists(), str(SAFETY_HEADER))
    add_check(checks, "zero_header_exists", ZERO_HEADER.exists(), True, ZERO_HEADER.exists(), str(ZERO_HEADER))
    add_check(checks, "source_has_no_create_publisher", source_has_create_publisher, False, not source_has_create_publisher)
    add_check(checks, "source_has_no_publish_call", source_has_publish_call, False, not source_has_publish_call)
    add_check(checks, "source_does_not_reference_torque_topic", source_has_torque_topic, False, not source_has_torque_topic)
    add_check(checks, "source_includes_safety_header", source_includes_safety_header, True, source_includes_safety_header)
    add_check(checks, "source_uses_clamp_torque_command", source_uses_clamp, True, source_uses_clamp)
    add_check(checks, "source_uses_watchdog_fresh_check", source_uses_watchdog_fresh, True, source_uses_watchdog_fresh)
    add_check(checks, "source_uses_watchdog_fallback_zero", source_uses_watchdog_fallback, True, source_uses_watchdog_fallback)
    add_check(checks, "source_has_internal_safe_tau_buffer", source_has_safe_tau_buffer, True, source_has_safe_tau_buffer)
    add_check(checks, "safety_header_has_clamp", safety_has_clamp, True, safety_has_clamp)
    add_check(checks, "safety_header_has_watchdog", safety_has_watchdog, True, safety_has_watchdog)
    add_check(checks, "zero_header_declares_12", zero_header_declares_12, True, zero_header_declares_12)

    s107 = summaries["Stage 10.7"]
    s108 = summaries["Stage 10.8"]

    add_check(checks, "stage107_clamp_watchdog_utility_implemented", as_bool(s107.get("clamp_watchdog_utility_implemented", "False")), True, as_bool(s107.get("clamp_watchdog_utility_implemented", "False")))
    add_check(checks, "stage107_torque_topic_publishers_zero", as_bool(s107.get("torque_topic_publishers_zero", "False")), True, as_bool(s107.get("torque_topic_publishers_zero", "False")))
    add_check(checks, "stage108_controller_uses_safety_utilities", as_bool(s108.get("controller_uses_safety_utilities", "False")), True, as_bool(s108.get("controller_uses_safety_utilities", "False")))
    add_check(checks, "stage108_torque_topic_publishers_zero", as_bool(s108.get("torque_topic_publishers_zero", "False")), True, as_bool(s108.get("torque_topic_publishers_zero", "False")))
    add_check(checks, "stage108_manual_enable_active", as_bool(s108.get("manual_enable_active", "True")), False, not as_bool(s108.get("manual_enable_active", "True")))
    add_check(checks, "stage108_publisher_path_exists", as_bool(s108.get("publisher_path_exists", "True")), False, not as_bool(s108.get("publisher_path_exists", "True")))

    gate_rows = load_gate(SAFETY_GATE)
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
    }

    add_check(checks, "stage108_safety_gate_exists", SAFETY_GATE.exists(), True, SAFETY_GATE.exists(), str(SAFETY_GATE))
    for gate, expected in expected_gate_status.items():
        value = gate_status.get(gate, None)
        add_check(checks, f"{gate}_status_after_stage108", value, expected, value == expected)

    torque_enable_ready = all(gate_status.get(gate, False) for gate in expected_gate_status)
    add_check(checks, "torque_enable_ready_after_stage108", torque_enable_ready, False, not torque_enable_ready)

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

    stage_rows = []
    for stage, metrics in summaries.items():
        stage_rows.append(
            f"| {stage} | {metrics.get('test_name', '')} | {metrics.get('stage10_scope', '')} | {metrics.get('pass', '')} | {metrics.get('torque_publisher_enabled', '')} | {metrics.get('control_law_changed', '')} |"
        )

    DOC_PATH.write_text(f"""# Stage 10.7–10.8 Safety Utility Freeze Summary

## 一、冻结结论

Stage 10.7–10.8 已形成 safety-utility frozen baseline。

该 baseline 包含：

- torque clamp utility；
- watchdog freshness utility；
- zero torque fallback；
- disabled controller 内部接入 clamp/watchdog utilities；
- runtime 验证 torque publisher count 仍为 0。

该 baseline 不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、Stage 10.7–10.8 汇总

| 阶段 | 测试名 | scope | pass | torque_publisher_enabled | control_law_changed |
|---|---|---|---:|---:|---:|
{chr(10).join(stage_rows)}

## 三、源码安全状态

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: {source_has_create_publisher}
- source_has_publish_call: {source_has_publish_call}
- source_has_torque_topic: {source_has_torque_topic}
- source_includes_safety_header: {source_includes_safety_header}
- source_uses_clamp_torque_command: {source_uses_clamp}
- source_uses_watchdog_fresh_check: {source_uses_watchdog_fresh}
- source_uses_watchdog_fallback_zero: {source_uses_watchdog_fallback}

## 四、Safety gate after Stage 10.8

- G0 Stage 8 frozen Python baseline valid: {gate_status.get("G0")}
- G1 Stage 9 interface mirror frozen: {gate_status.get("G1")}
- G2 C++ controller source has no torque publisher: {gate_status.get("G2")}
- G3 C++ controller source has no publish call: {gate_status.get("G3")}
- G4 Explicit manual enable flag design exists: {gate_status.get("G4")}
- G5 Torque clamp and watchdog utility implemented: {gate_status.get("G5")}
- G6 Zero torque dry-run regression completed: {gate_status.get("G6")}
- G7 Python frozen baseline A/B regression still passes: {gate_status.get("G7")}
- G8 Manual enable flags active at runtime: {gate_status.get("G8")}
- G9 Publisher path exists: {gate_status.get("G9")}
- G10 Disabled controller uses clamp/watchdog internally: {gate_status.get("G10")}

Therefore:

    torque_enable_ready = {torque_enable_ready}

G8 与 G9 仍为 False，因此不能启用 torque publisher。

## 五、冻结 hash

Hash CSV:

    results/logs_sample/stage10_7_8_safety_utility_freeze_hashes.csv

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 10.7–10.8 没有完成：

- ROS2/C++ realtime controller；
- torque publisher；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。

## 七、结论

Stage 10.7–10.8 可作为 safety-utility frozen baseline。

后续如果继续，应先实现 manual enable parameters disabled-by-default，仍不创建 publisher。
""")

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 10.9"])
        writer.writerow(["test_name", "stage10_7_8_safety_utility_freeze_summary"])
        writer.writerow(["stage107_pass", summaries["Stage 10.7"].get("pass", "False")])
        writer.writerow(["stage108_pass", summaries["Stage 10.8"].get("pass", "False")])
        writer.writerow(["freeze_file_count", len(FREEZE_FILES)])
        writer.writerow(["missing_file_count", len(missing_files)])
        writer.writerow(["source_has_no_create_publisher", not source_has_create_publisher])
        writer.writerow(["source_has_no_publish_call", not source_has_publish_call])
        writer.writerow(["source_does_not_reference_torque_topic", not source_has_torque_topic])
        writer.writerow(["source_includes_safety_header", source_includes_safety_header])
        writer.writerow(["source_uses_clamp_torque_command", source_uses_clamp])
        writer.writerow(["source_uses_watchdog_fresh_check", source_uses_watchdog_fresh])
        writer.writerow(["source_uses_watchdog_fallback_zero", source_uses_watchdog_fallback])
        writer.writerow(["stage107_clamp_watchdog_utility_implemented", s107.get("clamp_watchdog_utility_implemented", "False")])
        writer.writerow(["stage108_controller_uses_safety_utilities", s108.get("controller_uses_safety_utilities", "False")])
        writer.writerow(["g8_manual_enable_active", gate_status.get("G8", False)])
        writer.writerow(["g9_publisher_path_exists", gate_status.get("G9", False)])
        writer.writerow(["g10_controller_uses_safety_utilities", gate_status.get("G10", False)])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_publisher_enabled", False])
        writer.writerow(["torque_command_published_by_stage109", False])
        writer.writerow(["stage10_scope", "safety_utility_freeze_summary_only"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["safety_utility_frozen", True])
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
## Stage 10.9 Stage 10.7–10.8 Safety Utility Freeze Summary

Stage 10.9 冻结 Stage 10.7–10.8 safety-utility baseline。

- Script: `scripts/stage10_7_8_safety_utility_freeze_summary.py`
- Log: `results/logs_sample/stage10_7_8_safety_utility_freeze_log.csv`
- Hashes: `results/logs_sample/stage10_7_8_safety_utility_freeze_hashes.csv`
- Summary: `results/logs_sample/stage10_7_8_safety_utility_freeze_summary.csv`
- Docs: `docs/STAGE10_7_8_SAFETY_UTILITY_FREEZE_SUMMARY.md`
- pass: `{all_pass}`
- safety_utility_frozen: `True`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 10.7–10.8 只形成 safety utility baseline，不创建 publisher，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 10.9 Stage 10.7–10.8 Safety Utility Freeze Summary"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 10.9] Stage 10.7-10.8 safety utility freeze summary")
    print(f"pass={all_pass}")
    print(f"missing_file_count={len(missing_files)}")
    print("safety_utility_frozen=True")
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
