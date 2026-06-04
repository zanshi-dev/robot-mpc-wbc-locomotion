#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE_SUMMARIES = {
    "Stage 12.0": LOG_DIR / "stage12_active_publisher_construction_planning_summary.csv",
    "Stage 12.1": LOG_DIR / "stage12_pre_construction_source_runtime_guard_summary.csv",
    "Stage 12.2": LOG_DIR / "stage12_publisher_construction_source_patch_design_summary.csv",
    "Stage 12.3": LOG_DIR / "stage12_construction_stage_preflight_freeze_summary.csv",
    "Stage 12.4": LOG_DIR / "stage12_publisher_construction_source_patch_without_publish_summary.csv",
}

FINAL_GATE = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage124.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
SAFETY_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

DOC_PATH = ROOT / "docs/STAGE12_PUBLISHER_CONSTRUCTION_NO_PUBLISH_FREEZE.md"
SUMMARY_PATH = LOG_DIR / "stage12_publisher_construction_no_publish_freeze_summary.csv"
LOG_PATH = LOG_DIR / "stage12_publisher_construction_no_publish_freeze_log.csv"
HASH_PATH = LOG_DIR / "stage12_publisher_construction_no_publish_freeze_hashes.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage12_torque_publisher_safety_gate_after_stage125.csv"

TORQUE_TOPIC = "/go1/joint_torque_cmd"

FREEZE_FILES = [
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp",
    "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp",

    "docs/STAGE12_ACTIVE_PUBLISHER_CONSTRUCTION_PLANNING_ONLY.md",
    "docs/STAGE12_PRE_CONSTRUCTION_SOURCE_RUNTIME_GUARD.md",
    "docs/STAGE12_PUBLISHER_CONSTRUCTION_SOURCE_PATCH_DESIGN_ONLY.md",
    "docs/STAGE12_CONSTRUCTION_STAGE_PREFLIGHT_FREEZE.md",
    "docs/STAGE12_PUBLISHER_CONSTRUCTION_SOURCE_PATCH_WITHOUT_PUBLISH.md",

    "results/logs_sample/stage12_active_publisher_construction_plan.csv",
    "results/logs_sample/stage12_pre_construction_topic_observations.csv",
    "results/logs_sample/stage12_publisher_construction_source_patch_design.csv",
    "results/logs_sample/stage12_construction_stage_preflight_freeze_hashes.csv",
    "results/logs_sample/stage12_publisher_construction_without_publish_topic_observations.csv",

    "results/logs_sample/stage12_active_publisher_construction_planning_summary.csv",
    "results/logs_sample/stage12_pre_construction_source_runtime_guard_summary.csv",
    "results/logs_sample/stage12_publisher_construction_source_patch_design_summary.csv",
    "results/logs_sample/stage12_construction_stage_preflight_freeze_summary.csv",
    "results/logs_sample/stage12_publisher_construction_source_patch_without_publish_summary.csv",

    "results/logs_sample/stage12_torque_publisher_safety_gate_after_stage120.csv",
    "results/logs_sample/stage12_torque_publisher_safety_gate_after_stage121.csv",
    "results/logs_sample/stage12_torque_publisher_safety_gate_after_stage122.csv",
    "results/logs_sample/stage12_torque_publisher_safety_gate_after_stage124.csv",

    "results/logs_sample/stage12_disabled_controller_node_before_stage124.cpp",
    "results/logs_sample/stage12_disabled_controller_node_after_stage124.cpp",
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

    s120 = summaries["Stage 12.0"]
    s121 = summaries["Stage 12.1"]
    s122 = summaries["Stage 12.2"]
    s123 = summaries["Stage 12.3"]
    s124 = summaries["Stage 12.4"]

    add_check(checks, "stage120_planning_complete", as_bool(s120.get("active_publisher_construction_planning_complete", "False")), True, as_bool(s120.get("active_publisher_construction_planning_complete", "False")))
    add_check(checks, "stage121_pre_construction_guard_passed", as_bool(s121.get("pre_construction_source_runtime_guard_passed", "False")), True, as_bool(s121.get("pre_construction_source_runtime_guard_passed", "False")))
    add_check(checks, "stage122_patch_design_complete", as_bool(s122.get("publisher_construction_source_patch_design_complete", "False")), True, as_bool(s122.get("publisher_construction_source_patch_design_complete", "False")))
    add_check(checks, "stage123_preflight_frozen", as_bool(s123.get("construction_stage_preflight_frozen", "False")), True, as_bool(s123.get("construction_stage_preflight_frozen", "False")))

    stage124_required = {
        "source_patch_applied": True,
        "post_source_has_create_publisher": True,
        "post_source_has_publish_call": False,
        "post_source_references_torque_topic": True,
        "post_source_has_active_publisher_member": True,
        "post_source_has_stage124_marker": True,
        "colcon_build_returncode": "0",
        "enable_param_default_false": True,
        "confirm_param_default_false": True,
        "torque_publishers_positive_all_samples": True,
        "active_ros_publisher_path_exists": True,
        "manual_enable_active": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "torque_command_published_by_stage124": False,
    }

    for key, expected in stage124_required.items():
        raw = s124.get(key, "")
        if isinstance(expected, bool):
            value = as_bool(raw)
        else:
            value = raw
        add_check(checks, f"stage124_{key}", value, expected, value == expected)

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
    add_check(checks, "safety_header_exists", SAFETY_HEADER.exists(), True, SAFETY_HEADER.exists(), str(SAFETY_HEADER))
    add_check(checks, "zero_header_exists", ZERO_HEADER.exists(), True, ZERO_HEADER.exists(), str(ZERO_HEADER))
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

    obs = load_dicts(LOG_DIR / "stage12_publisher_construction_without_publish_topic_observations.csv")
    obs_count = len(obs)
    obs_all_pub_positive = all(as_bool(row.get("publisher_count_positive", "False")) for row in obs)
    obs_all_sub_positive = all(as_bool(row.get("subscription_count_positive", "False")) for row in obs)
    obs_all_rc_zero = all(str(row.get("topic_info_returncode", "")) == "0" for row in obs)

    add_check(checks, "runtime_observation_row_count", obs_count, 6, obs_count == 6)
    add_check(checks, "runtime_observation_publishers_positive_all_rows", obs_all_pub_positive, True, obs_all_pub_positive)
    add_check(checks, "runtime_observation_subscribers_positive_all_rows", obs_all_sub_positive, True, obs_all_sub_positive)
    add_check(checks, "runtime_observation_returncode_zero_all_rows", obs_all_rc_zero, True, obs_all_rc_zero)

    gate_rows = load_dicts(FINAL_GATE)
    gate_status = {row.get("gate", ""): as_bool(row.get("current_status", "False")) for row in gate_rows}

    expected_gate_status = {
        "G0": True,
        "G1": True,
        "G2": False,
        "G3": True,
        "G4": True,
        "G5": True,
        "G6": True,
        "G7": True,
        "G8": False,
        "G9": True,
        "G10": True,
        "G11": True,
        "G12": True,
        "G13": True,
        "G14": True,
        "G15": True,
        "G16": True,
        "G17": True,
        "G18": True,
        "G19": True,
        "G20": True,
        "G21": True,
        "G22": True,
    }

    add_check(checks, "stage124_safety_gate_exists", FINAL_GATE.exists(), True, FINAL_GATE.exists(), str(FINAL_GATE))
    for gate, expected in expected_gate_status.items():
        value = gate_status.get(gate, None)
        add_check(checks, f"{gate}_status_after_stage124", value, expected, value == expected)

    manual_enable_active = gate_status.get("G8", True)
    active_ros_publisher_path_exists = gate_status.get("G9", False)
    g22_ok = gate_status.get("G22", False)

    no_publish_integrity_passed = (
        all(as_bool(m.get("pass", "False")) for m in summaries.values()) and
        current_source_has_create_publisher and
        not current_source_has_publish_call and
        current_source_references_torque_topic and
        current_source_has_active_member and
        current_source_has_stage124_marker and
        obs_count == 6 and
        obs_all_pub_positive and
        obs_all_sub_positive and
        active_ros_publisher_path_exists and
        not manual_enable_active and
        g22_ok
    )

    torque_enable_ready = False
    torque_publisher_enabled = False

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
        "gate": "G23",
        "name": "Publisher construction no-publish freeze passed",
        "required_before_torque_publish": True,
        "current_status": no_publish_integrity_passed,
        "evidence": str(LOG_PATH.relative_to(ROOT)),
    })

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(gate_out_rows)

    add_check(checks, "publisher_construction_no_publish_integrity_passed", no_publish_integrity_passed, True, no_publish_integrity_passed)
    add_check(checks, "manual_enable_active", manual_enable_active, False, not manual_enable_active)
    add_check(checks, "active_ros_publisher_path_exists", active_ros_publisher_path_exists, True, active_ros_publisher_path_exists)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)
    add_check(checks, "torque_publisher_enabled", torque_publisher_enabled, False, not torque_publisher_enabled)

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

    DOC_PATH.write_text(f"""# Stage 12.5 Publisher Construction No-publish Freeze

## 一、冻结结论

Stage 12.5 完成 publisher construction freeze and no-publish integrity check。

当前状态：

- active ROS publisher path exists: {active_ros_publisher_path_exists}
- publish call exists: {current_source_has_publish_call}
- manual enable active: {manual_enable_active}
- torque_enable_ready: {torque_enable_ready}
- torque_publisher_enabled: {torque_publisher_enabled}

本阶段不修改 C++ source，不调用 publish，不发布 torque，不改变控制律。

## 二、Stage 12.0–12.4 汇总

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

## 四、Runtime observation integrity

Observation CSV:

    results/logs_sample/stage12_publisher_construction_without_publish_topic_observations.csv

Results:

- runtime_observation_row_count: {obs_count}
- runtime_observation_publishers_positive_all_rows: {obs_all_pub_positive}
- runtime_observation_subscribers_positive_all_rows: {obs_all_sub_positive}
- runtime_observation_returncode_zero_all_rows: {obs_all_rc_zero}

## 五、Safety gate after Stage 12.5

- G2 no publisher construction: {gate_status.get("G2")}
- G3 no publish call: {gate_status.get("G3")}
- G8 manual enable active: {gate_status.get("G8")}
- G9 active ROS publisher path exists: {gate_status.get("G9")}
- G22 publisher construction implemented without publish call: {gate_status.get("G22")}
- G23 publisher construction no-publish freeze passed: {no_publish_integrity_passed}

Therefore:

    torque_enable_ready = {torque_enable_ready}

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.5 没有完成：

- publish call；
- torque command publishing；
- manual torque enable；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。
""")

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 12.5"])
        writer.writerow(["test_name", "publisher_construction_no_publish_freeze"])
        writer.writerow(["stage120_pass", s120.get("pass", "False")])
        writer.writerow(["stage121_pass", s121.get("pass", "False")])
        writer.writerow(["stage122_pass", s122.get("pass", "False")])
        writer.writerow(["stage123_pass", s123.get("pass", "False")])
        writer.writerow(["stage124_pass", s124.get("pass", "False")])
        writer.writerow(["freeze_file_count", len(FREEZE_FILES)])
        writer.writerow(["missing_file_count", len(missing_files)])
        writer.writerow(["current_source_has_create_publisher", current_source_has_create_publisher])
        writer.writerow(["current_source_has_publish_call", current_source_has_publish_call])
        writer.writerow(["current_source_references_torque_topic", current_source_references_torque_topic])
        writer.writerow(["current_source_has_active_publisher_member", current_source_has_active_member])
        writer.writerow(["current_source_has_stage124_marker", current_source_has_stage124_marker])
        writer.writerow(["runtime_observation_row_count", obs_count])
        writer.writerow(["runtime_observation_publishers_positive_all_rows", obs_all_pub_positive])
        writer.writerow(["runtime_observation_subscribers_positive_all_rows", obs_all_sub_positive])
        writer.writerow(["runtime_observation_returncode_zero_all_rows", obs_all_rc_zero])
        writer.writerow(["publisher_construction_no_publish_integrity_passed", no_publish_integrity_passed])
        writer.writerow(["manual_enable_active", manual_enable_active])
        writer.writerow(["active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g2_no_publisher_construction", gate_status.get("G2", False)])
        writer.writerow(["g3_no_publish_call", gate_status.get("G3", False)])
        writer.writerow(["g8_manual_enable_active", gate_status.get("G8", False)])
        writer.writerow(["g9_active_ros_publisher_path_exists", gate_status.get("G9", False)])
        writer.writerow(["g22_publisher_construction_implemented_without_publish_call", gate_status.get("G22", False)])
        writer.writerow(["g23_publisher_construction_no_publish_freeze_passed", no_publish_integrity_passed])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_publisher_enabled", torque_publisher_enabled])
        writer.writerow(["torque_command_published_by_stage125", False])
        writer.writerow(["stage12_scope", "publisher_construction_no_publish_freeze_only"])
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
## Stage 12.5 Publisher Construction No-publish Freeze

Stage 12.5 完成 publisher construction no-publish freeze。

- Script: `scripts/stage12_publisher_construction_no_publish_freeze.py`
- Log: `results/logs_sample/stage12_publisher_construction_no_publish_freeze_log.csv`
- Hashes: `results/logs_sample/stage12_publisher_construction_no_publish_freeze_hashes.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage125.csv`
- Summary: `results/logs_sample/stage12_publisher_construction_no_publish_freeze_summary.csv`
- Docs: `docs/STAGE12_PUBLISHER_CONSTRUCTION_NO_PUBLISH_FREEZE.md`
- pass: `{all_pass}`
- publisher_construction_no_publish_integrity_passed: `{no_publish_integrity_passed}`
- active_ros_publisher_path_exists: `{active_ros_publisher_path_exists}`
- manual_enable_active: `{manual_enable_active}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `{torque_publisher_enabled}`
- control_law_changed: `False`

Stage 12.5 只冻结 publisher construction no-publish baseline，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 12.5 Publisher Construction No-publish Freeze"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 12.5] publisher construction no-publish freeze")
    print(f"pass={all_pass}")
    print(f"missing_file_count={len(missing_files)}")
    print(f"publisher_construction_no_publish_integrity_passed={no_publish_integrity_passed}")
    print(f"current_source_has_create_publisher={current_source_has_create_publisher}")
    print(f"current_source_has_publish_call={current_source_has_publish_call}")
    print(f"active_ros_publisher_path_exists={active_ros_publisher_path_exists}")
    print(f"manual_enable_active={manual_enable_active}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print("control_law_changed=False")
    print(f"torque_publisher_enabled={torque_publisher_enabled}")
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
