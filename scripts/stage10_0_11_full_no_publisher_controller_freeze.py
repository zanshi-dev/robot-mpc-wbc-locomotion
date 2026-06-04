#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE_SUMMARIES = {
    "Stage 10.0": LOG_DIR / "stage10_controller_implementation_plan_and_safety_gate_summary.csv",
    "Stage 10.1": LOG_DIR / "stage10_disabled_cpp_controller_skeleton_check_summary.csv",
    "Stage 10.2": LOG_DIR / "stage10_cpp_state_cache_runtime_validation_summary.csv",
    "Stage 10.3": LOG_DIR / "stage10_zero_torque_dry_run_internal_validation_summary.csv",
    "Stage 10.4": LOG_DIR / "stage10_python_frozen_baseline_ab_regression_summary.csv",
    "Stage 10.5": LOG_DIR / "stage10_torque_publisher_enable_gate_design_summary.csv",
    "Stage 10.6": LOG_DIR / "stage10_0_5_controller_planning_freeze_summary.csv",
    "Stage 10.7": LOG_DIR / "stage10_clamp_watchdog_utility_without_publisher_summary.csv",
    "Stage 10.8": LOG_DIR / "stage10_disabled_controller_uses_safety_utilities_summary.csv",
    "Stage 10.9": LOG_DIR / "stage10_7_8_safety_utility_freeze_summary.csv",
    "Stage 10.10": LOG_DIR / "stage10_manual_enable_params_disabled_without_publisher_summary.csv",
    "Stage 10.11": LOG_DIR / "stage10_manual_enable_param_guard_freeze_summary.csv",
}

FINAL_GATE = LOG_DIR / "stage10_torque_publisher_safety_gate_after_stage1010.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
SAFETY_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

DOC_PATH = ROOT / "docs/STAGE10_0_11_FULL_NO_PUBLISHER_CONTROLLER_FREEZE.md"
SUMMARY_PATH = LOG_DIR / "stage10_0_11_full_no_publisher_controller_freeze_summary.csv"
LOG_PATH = LOG_DIR / "stage10_0_11_full_no_publisher_controller_freeze_log.csv"
HASH_PATH = LOG_DIR / "stage10_0_11_full_no_publisher_controller_freeze_hashes.csv"

FREEZE_FILES = [
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/package.xml",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/CMakeLists.txt",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/zero_torque_dry_run_contract_check.cpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/torque_safety_contract_check.cpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/launch/disabled_controller.launch.py",

    "docs/STAGE10_CONTROLLER_IMPLEMENTATION_PLAN_AND_SAFETY_GATE.md",
    "docs/STAGE10_DISABLED_CPP_CONTROLLER_SKELETON.md",
    "docs/STAGE10_CPP_STATE_CACHE_RUNTIME_VALIDATION.md",
    "docs/STAGE10_ZERO_TORQUE_DRY_RUN_INTERNAL_VALIDATION.md",
    "docs/STAGE10_PYTHON_FROZEN_BASELINE_AB_REGRESSION.md",
    "docs/STAGE10_TORQUE_PUBLISHER_ENABLE_GATE_DESIGN.md",
    "docs/STAGE10_0_5_CONTROLLER_PLANNING_FREEZE_SUMMARY.md",
    "docs/STAGE10_CLAMP_WATCHDOG_UTILITY_WITHOUT_PUBLISHER.md",
    "docs/STAGE10_DISABLED_CONTROLLER_USES_SAFETY_UTILITIES.md",
    "docs/STAGE10_7_8_SAFETY_UTILITY_FREEZE_SUMMARY.md",
    "docs/STAGE10_MANUAL_ENABLE_PARAMS_DISABLED_WITHOUT_PUBLISHER.md",
    "docs/STAGE10_MANUAL_ENABLE_PARAM_GUARD_FREEZE_SUMMARY.md",

    "results/logs_sample/stage10_controller_implementation_plan_and_safety_gate_summary.csv",
    "results/logs_sample/stage10_disabled_cpp_controller_skeleton_check_summary.csv",
    "results/logs_sample/stage10_cpp_state_cache_runtime_validation_summary.csv",
    "results/logs_sample/stage10_zero_torque_dry_run_internal_validation_summary.csv",
    "results/logs_sample/stage10_python_frozen_baseline_ab_regression_summary.csv",
    "results/logs_sample/stage10_torque_publisher_enable_gate_design_summary.csv",
    "results/logs_sample/stage10_0_5_controller_planning_freeze_summary.csv",
    "results/logs_sample/stage10_clamp_watchdog_utility_without_publisher_summary.csv",
    "results/logs_sample/stage10_disabled_controller_uses_safety_utilities_summary.csv",
    "results/logs_sample/stage10_7_8_safety_utility_freeze_summary.csv",
    "results/logs_sample/stage10_manual_enable_params_disabled_without_publisher_summary.csv",
    "results/logs_sample/stage10_manual_enable_param_guard_freeze_summary.csv",

    "results/logs_sample/stage10_torque_publisher_safety_gate.csv",
    "results/logs_sample/stage10_torque_publisher_safety_gate_after_stage104.csv",
    "results/logs_sample/stage10_torque_publisher_safety_gate_after_stage105.csv",
    "results/logs_sample/stage10_torque_publisher_safety_gate_after_stage107.csv",
    "results/logs_sample/stage10_torque_publisher_safety_gate_after_stage108.csv",
    "results/logs_sample/stage10_torque_publisher_safety_gate_after_stage1010.csv",
    "results/logs_sample/stage10_zero_torque_dry_run_vector.csv",
    "results/logs_sample/stage10_clamp_watchdog_utility_clamped_vector.csv",
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

    control_law_changed_any = any(as_bool(m.get("control_law_changed", "False")) for m in summaries.values())
    torque_publisher_enabled_any = any(as_bool(m.get("torque_publisher_enabled", "False")) for m in summaries.values())

    torque_command_published_any = False
    for metrics in summaries.values():
        for key, value in metrics.items():
            if key.startswith("torque_command_published_by_stage") and as_bool(value):
                torque_command_published_any = True

    realtime_controller_completed_any = any(
        as_bool(m.get("ros2_cpp_realtime_controller_completed", "False")) for m in summaries.values()
    )
    pure_wbc_completed_any = any(
        as_bool(m.get("pure_wbc_locomotion_completed", "False")) for m in summaries.values()
    )
    ekf_completed_any = any(
        as_bool(m.get("ekf_completed", "False")) for m in summaries.values()
    )
    full_mpc_completed_any = any(
        as_bool(m.get("full_3d_centroidal_mpc_completed", "False")) for m in summaries.values()
    )

    add_check(checks, "control_law_changed_any", control_law_changed_any, False, not control_law_changed_any)
    add_check(checks, "torque_publisher_enabled_any", torque_publisher_enabled_any, False, not torque_publisher_enabled_any)
    add_check(checks, "torque_command_published_any", torque_command_published_any, False, not torque_command_published_any)
    add_check(checks, "ros2_cpp_realtime_controller_completed_any", realtime_controller_completed_any, False, not realtime_controller_completed_any)
    add_check(checks, "pure_wbc_locomotion_completed_any", pure_wbc_completed_any, False, not pure_wbc_completed_any)
    add_check(checks, "ekf_completed_any", ekf_completed_any, False, not ekf_completed_any)
    add_check(checks, "full_3d_centroidal_mpc_completed_any", full_mpc_completed_any, False, not full_mpc_completed_any)

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
    add_check(checks, "source_reads_enable_param", source_reads_enable_param, True, source_reads_enable_param)
    add_check(checks, "source_reads_confirm_param", source_reads_confirm_param, True, source_reads_confirm_param)
    add_check(checks, "source_has_manual_enable_active_state", source_has_manual_enable_active, True, source_has_manual_enable_active)
    add_check(checks, "source_uses_safety_utilities", source_uses_safety, True, source_uses_safety)
    add_check(checks, "safety_header_has_clamp_watchdog", safety_header_has_clamp_watchdog, True, safety_header_has_clamp_watchdog)
    add_check(checks, "zero_header_declares_12", zero_header_declares_12, True, zero_header_declares_12)

    gate_rows = load_gate(FINAL_GATE)
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

    add_check(checks, "final_safety_gate_exists", FINAL_GATE.exists(), True, FINAL_GATE.exists(), str(FINAL_GATE))
    for gate, expected in expected_gate_status.items():
        value = gate_status.get(gate, None)
        add_check(checks, f"{gate}_status_final", value, expected, value == expected)

    torque_enable_ready = all(gate_status.get(gate, False) for gate in expected_gate_status)
    add_check(checks, "torque_enable_ready_final", torque_enable_ready, False, not torque_enable_ready)

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

    DOC_PATH.write_text(f"""# Stage 10.0–10.11 Full No-publisher Controller Baseline Freeze

## 一、冻结结论

Stage 10.0–10.11 已形成 full no-publisher controller baseline。

该 baseline 包含：

- controller implementation plan；
- disabled-by-default C++ controller skeleton；
- state cache runtime validation；
- zero torque dry-run command；
- Python frozen baseline A/B regression；
- torque publisher enable gate design；
- clamp/watchdog utilities；
- disabled controller 内部接入 safety utilities；
- manual enable parameters，默认 false；
- manual-enable parameter guard freeze。

该 baseline 不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、Stage 10.0–10.11 汇总

| 阶段 | 测试名 | scope | pass | torque_publisher_enabled | control_law_changed |
|---|---|---|---:|---:|---:|
{chr(10).join(stage_rows)}

## 三、最终源码安全状态

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

## 四、最终 safety gate

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
- G11 Manual enable parameters exist and default false: {gate_status.get("G11")}

Therefore:

    torque_enable_ready = {torque_enable_ready}

G8 与 G9 仍为 False，因此不能发布 torque。

## 五、冻结 hash

Hash CSV:

    results/logs_sample/stage10_0_11_full_no_publisher_controller_freeze_hashes.csv

## 六、明确边界

当前 baseline 仍是 mixed online control baseline。

Stage 10.0–10.11 没有完成：

- ROS2/C++ realtime controller；
- torque publisher；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- base velocity tracking；
- hardware deployment。

## 七、结论

Stage 10.0–10.11 可作为 full no-publisher controller frozen baseline。

如后续继续，下一阶段应单独设计 publisher path skeleton，并默认 disabled；不得直接启用 torque publish。
""")

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 10.12"])
        writer.writerow(["test_name", "stage10_0_11_full_no_publisher_controller_freeze"])
        for stage in STAGE_SUMMARIES:
            key = stage.lower().replace(" ", "").replace(".", "")
            writer.writerow([f"{key}_pass", summaries[stage].get("pass", "False")])
        writer.writerow(["freeze_file_count", len(FREEZE_FILES)])
        writer.writerow(["missing_file_count", len(missing_files)])
        writer.writerow(["source_has_no_create_publisher", not source_has_create_publisher])
        writer.writerow(["source_has_no_publish_call", not source_has_publish_call])
        writer.writerow(["source_does_not_reference_torque_topic", not source_has_torque_topic])
        writer.writerow(["source_declares_enable_param_default_false", source_declares_enable_param])
        writer.writerow(["source_declares_confirm_param_default_false", source_declares_confirm_param])
        writer.writerow(["source_reads_enable_param", source_reads_enable_param])
        writer.writerow(["source_reads_confirm_param", source_reads_confirm_param])
        writer.writerow(["source_uses_safety_utilities", source_uses_safety])
        writer.writerow(["g8_manual_enable_active", gate_status.get("G8", False)])
        writer.writerow(["g9_publisher_path_exists", gate_status.get("G9", False)])
        writer.writerow(["g10_controller_uses_safety_utilities", gate_status.get("G10", False)])
        writer.writerow(["g11_manual_enable_params_exist_and_default_false", gate_status.get("G11", False)])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_publisher_enabled", False])
        writer.writerow(["torque_command_published_by_stage1012", False])
        writer.writerow(["stage10_scope", "full_no_publisher_controller_freeze_only"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["full_no_publisher_controller_frozen", True])
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
## Stage 10.12 Stage 10.0–10.11 Full No-publisher Controller Freeze

Stage 10.12 冻结 Stage 10.0–10.11 full no-publisher controller baseline。

- Script: `scripts/stage10_0_11_full_no_publisher_controller_freeze.py`
- Log: `results/logs_sample/stage10_0_11_full_no_publisher_controller_freeze_log.csv`
- Hashes: `results/logs_sample/stage10_0_11_full_no_publisher_controller_freeze_hashes.csv`
- Summary: `results/logs_sample/stage10_0_11_full_no_publisher_controller_freeze_summary.csv`
- Docs: `docs/STAGE10_0_11_FULL_NO_PUBLISHER_CONTROLLER_FREEZE.md`
- pass: `{all_pass}`
- full_no_publisher_controller_frozen: `True`
- g8_manual_enable_active: `{gate_status.get("G8", False)}`
- g9_publisher_path_exists: `{gate_status.get("G9", False)}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 10.0–10.11 只形成 no-publisher controller baseline，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 10.12 Stage 10.0–10.11 Full No-publisher Controller Freeze"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 10.12] Stage 10.0-10.11 full no-publisher controller freeze")
    print(f"pass={all_pass}")
    print(f"missing_file_count={len(missing_files)}")
    print("full_no_publisher_controller_frozen=True")
    print(f"g8_manual_enable_active={gate_status.get('G8', False)}")
    print(f"g9_publisher_path_exists={gate_status.get('G9', False)}")
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
