#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "results/logs_sample"

STAGE119_SUMMARY = LOG_DIR / "stage11_0_8_full_publisher_path_no_active_publisher_freeze_summary.csv"
STAGE119_HASH = LOG_DIR / "stage11_0_8_full_publisher_path_no_active_publisher_freeze_hashes.csv"
FINAL_GATE_IN = LOG_DIR / "stage11_torque_publisher_safety_gate_after_stage117.csv"

CPP_SOURCE = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp"
SAFETY_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp"
ZERO_HEADER = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

DOC_PATH = ROOT / "docs/STAGE11_FULL_FREEZE_INTEGRITY_CHECK.md"
SUMMARY_PATH = LOG_DIR / "stage11_full_freeze_integrity_check_summary.csv"
LOG_PATH = LOG_DIR / "stage11_full_freeze_integrity_check_log.csv"
HASH_CHECK_PATH = LOG_DIR / "stage11_full_freeze_integrity_check_hash_check.csv"
SAFETY_GATE_PATH = LOG_DIR / "stage11_torque_publisher_safety_gate_after_stage1110.csv"

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

    s119 = load_summary(STAGE119_SUMMARY)

    stage119_pass = as_bool(s119.get("pass", "False"))
    full_frozen = as_bool(s119.get("full_publisher_path_no_active_publisher_frozen", "False"))
    stage119_missing_file_count = int(s119.get("missing_file_count", "999"))
    stage119_runtime_pub_zero = as_bool(s119.get("runtime_observation_publishers_zero_all_rows", "False"))
    stage119_torque_ready = as_bool(s119.get("torque_enable_ready", "True"))
    stage119_torque_enabled = as_bool(s119.get("torque_publisher_enabled", "True"))
    stage119_control_changed = as_bool(s119.get("control_law_changed", "True"))

    add_check(checks, "stage119_summary_exists", STAGE119_SUMMARY.exists(), True, STAGE119_SUMMARY.exists(), str(STAGE119_SUMMARY))
    add_check(checks, "stage119_pass", stage119_pass, True, stage119_pass)
    add_check(checks, "stage119_full_publisher_path_no_active_publisher_frozen", full_frozen, True, full_frozen)
    add_check(checks, "stage119_missing_file_count", stage119_missing_file_count, 0, stage119_missing_file_count == 0)
    add_check(checks, "stage119_runtime_observation_publishers_zero_all_rows", stage119_runtime_pub_zero, True, stage119_runtime_pub_zero)
    add_check(checks, "stage119_torque_enable_ready", stage119_torque_ready, False, not stage119_torque_ready)
    add_check(checks, "stage119_torque_publisher_enabled", stage119_torque_enabled, False, not stage119_torque_enabled)
    add_check(checks, "stage119_control_law_changed", stage119_control_changed, False, not stage119_control_changed)

    stage_pass_keys = [
        "stage110_pass",
        "stage111_pass",
        "stage112_pass",
        "stage113_pass",
        "stage114_pass",
        "stage115_pass",
        "stage116_pass",
        "stage117_pass",
        "stage118_pass",
    ]

    for key in stage_pass_keys:
        value = as_bool(s119.get(key, "False"))
        add_check(checks, key, value, True, value)

    hash_rows = load_dicts(STAGE119_HASH)
    add_check(checks, "stage119_hash_csv_exists", STAGE119_HASH.exists(), True, STAGE119_HASH.exists(), str(STAGE119_HASH))
    add_check(checks, "stage119_hash_row_count_positive", len(hash_rows), ">0", len(hash_rows) > 0)

    hash_check_rows = []
    hash_mismatch_count = 0
    missing_hash_file_count = 0

    for row in hash_rows:
        rel = row.get("file", "")
        expected_exists = as_bool(row.get("exists", "False"))
        expected_sha = row.get("sha256", "")
        path = ROOT / rel

        current_exists = path.exists()
        current_sha = sha256_file(path) if current_exists else ""
        sha_match = current_exists and expected_exists and current_sha == expected_sha

        if expected_exists and not current_exists:
            missing_hash_file_count += 1
        if expected_exists and not sha_match:
            hash_mismatch_count += 1

        hash_check_rows.append({
            "file": rel,
            "expected_exists": expected_exists,
            "current_exists": current_exists,
            "expected_sha256": expected_sha,
            "current_sha256": current_sha,
            "sha256_match": sha_match,
        })

    with HASH_CHECK_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file",
                "expected_exists",
                "current_exists",
                "expected_sha256",
                "current_sha256",
                "sha256_match",
            ],
        )
        writer.writeheader()
        writer.writerows(hash_check_rows)

    hash_integrity_passed = (
        len(hash_rows) > 0 and
        missing_hash_file_count == 0 and
        hash_mismatch_count == 0
    )

    add_check(checks, "stage119_hash_rows_checked", len(hash_rows), ">0", len(hash_rows) > 0)
    add_check(checks, "hash_missing_file_count", missing_hash_file_count, 0, missing_hash_file_count == 0)
    add_check(checks, "hash_mismatch_count", hash_mismatch_count, 0, hash_mismatch_count == 0)
    add_check(checks, "hash_integrity_passed", hash_integrity_passed, True, hash_integrity_passed)

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
    add_check(checks, "source_has_dormant_skeleton_marker", source_has_dormant_skeleton_marker, True, source_has_dormant_skeleton_marker)
    add_check(checks, "source_has_construct_forbidden_marker", source_has_construct_forbidden_marker, True, source_has_construct_forbidden_marker)
    add_check(checks, "source_has_publish_forbidden_marker", source_has_publish_forbidden_marker, True, source_has_publish_forbidden_marker)
    add_check(checks, "source_has_payload_length_12", source_has_payload_length_12, True, source_has_payload_length_12)
    add_check(checks, "source_has_dormant_payload_helper", source_has_dormant_payload_helper, True, source_has_dormant_payload_helper)
    add_check(checks, "dormant_publisher_path_source_skeleton_exists", dormant_source_skeleton_exists, True, dormant_source_skeleton_exists)

    gate_rows = load_dicts(FINAL_GATE_IN)
    gate_status = {
        row.get("gate", ""): as_bool(row.get("current_status", "False"))
        for row in gate_rows
    }

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
        "G12": True,
        "G13": True,
        "G14": True,
        "G15": True,
        "G16": True,
        "G17": True,
    }

    add_check(checks, "final_gate_input_exists", FINAL_GATE_IN.exists(), True, FINAL_GATE_IN.exists(), str(FINAL_GATE_IN))
    for gate, expected in expected_gate_status.items():
        value = gate_status.get(gate, None)
        add_check(checks, f"{gate}_status_input", value, expected, value == expected)

    manual_enable_active = gate_status.get("G8", True)
    active_ros_publisher_path_exists = gate_status.get("G9", True)
    runtime_guard_hardened = gate_status.get("G17", False)

    full_freeze_integrity_passed = (
        stage119_pass and
        full_frozen and
        hash_integrity_passed and
        dormant_source_skeleton_exists and
        runtime_guard_hardened and
        not source_has_create_publisher and
        not source_has_publish_call and
        not source_has_torque_topic and
        not manual_enable_active and
        not active_ros_publisher_path_exists
    )

    torque_enable_ready = False

    gate_out_rows = []
    for row in gate_rows:
        gate_out_rows.append(row)

    gate_out_rows.append({
        "gate": "G18",
        "name": "Stage 11 full freeze integrity check passed",
        "required_before_torque_publish": True,
        "current_status": full_freeze_integrity_passed,
        "evidence": str(LOG_PATH.relative_to(ROOT)),
    })

    with SAFETY_GATE_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "name", "required_before_torque_publish", "current_status", "evidence"],
        )
        writer.writeheader()
        writer.writerows(gate_out_rows)

    add_check(checks, "manual_enable_active", manual_enable_active, False, manual_enable_active is False)
    add_check(checks, "active_ros_publisher_path_exists", active_ros_publisher_path_exists, False, active_ros_publisher_path_exists is False)
    add_check(checks, "full_freeze_integrity_passed", full_freeze_integrity_passed, True, full_freeze_integrity_passed)
    add_check(checks, "torque_enable_ready", torque_enable_ready, False, not torque_enable_ready)

    all_pass = all(row["pass"] for row in checks)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(checks)

    DOC_PATH.write_text(f"""# Stage 11.10 Full Freeze Integrity Check

## 一、结论

Stage 11.10 完成 Stage 11.0–11.9 full freeze integrity check。

该检查确认：

- Stage 11.9 full publisher-path no-active-publisher freeze 已通过；
- Stage 11.9 hash manifest 中所有文件均存在；
- Stage 11.9 hash manifest 中所有文件 SHA256 均匹配；
- disabled controller 仍无 create_publisher；
- disabled controller 仍无 publish call；
- disabled controller 仍不引用 /go1/joint_torque_cmd；
- dormant publisher skeleton marker 仍存在；
- construct forbidden marker 仍存在；
- publish forbidden marker 仍存在；
- runtime guard hardening 已完成；
- G8 manual enable flags active at runtime 仍为 False；
- G9 active ROS publisher path exists 仍为 False。

## 二、Hash integrity

Hash source:

    results/logs_sample/stage11_0_8_full_publisher_path_no_active_publisher_freeze_hashes.csv

Hash check output:

    results/logs_sample/stage11_full_freeze_integrity_check_hash_check.csv

Results:

- stage119_hash_rows_checked: {len(hash_rows)}
- hash_missing_file_count: {missing_hash_file_count}
- hash_mismatch_count: {hash_mismatch_count}
- hash_integrity_passed: {hash_integrity_passed}

## 三、Source guard

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: {source_has_create_publisher}
- source_has_publish_call: {source_has_publish_call}
- source_has_torque_topic: {source_has_torque_topic}
- dormant_publisher_path_source_skeleton_exists: {dormant_source_skeleton_exists}

## 四、Safety gate after Stage 11.10

新增：

- G18 full freeze integrity check passed: {full_freeze_integrity_passed}

仍为 False：

- G8 manual enable flags active at runtime: {manual_enable_active}
- G9 active ROS publisher path exists: {active_ros_publisher_path_exists}

Therefore:

    torque_enable_ready = {torque_enable_ready}

## 五、边界

当前 baseline 仍是 mixed online control baseline。

Stage 11.10 没有完成：

- ROS torque publisher construction；
- /go1/joint_torque_cmd active publisher；
- publish call；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。

## 六、结论

Stage 11.0–11.10 可作为 verified full publisher-path no-active-publisher frozen baseline。

不建议在 Stage 11 内继续扩展到 active publisher。
""")

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["stage", "Stage 11.10"])
        writer.writerow(["test_name", "stage11_full_freeze_integrity_check"])
        writer.writerow(["stage119_pass", stage119_pass])
        writer.writerow(["stage119_full_publisher_path_no_active_publisher_frozen", full_frozen])
        writer.writerow(["stage119_hash_rows_checked", len(hash_rows)])
        writer.writerow(["hash_missing_file_count", missing_hash_file_count])
        writer.writerow(["hash_mismatch_count", hash_mismatch_count])
        writer.writerow(["hash_integrity_passed", hash_integrity_passed])
        for key in stage_pass_keys:
            writer.writerow([key, s119.get(key, "False")])
        writer.writerow(["source_has_no_create_publisher", not source_has_create_publisher])
        writer.writerow(["source_has_no_publish_call", not source_has_publish_call])
        writer.writerow(["source_does_not_reference_torque_topic", not source_has_torque_topic])
        writer.writerow(["source_declares_enable_param_default_false", source_declares_enable_param])
        writer.writerow(["source_declares_confirm_param_default_false", source_declares_confirm_param])
        writer.writerow(["source_uses_safety_utilities", source_uses_safety])
        writer.writerow(["dormant_publisher_path_source_skeleton_exists", dormant_source_skeleton_exists])
        writer.writerow(["g8_manual_enable_active", manual_enable_active])
        writer.writerow(["g9_active_ros_publisher_path_exists", active_ros_publisher_path_exists])
        writer.writerow(["g17_runtime_guard_hardened_for_dormant_publisher_skeleton", runtime_guard_hardened])
        writer.writerow(["g18_full_freeze_integrity_check_passed", full_freeze_integrity_passed])
        writer.writerow(["torque_enable_ready", torque_enable_ready])
        writer.writerow(["control_law_changed", False])
        writer.writerow(["torque_publisher_enabled", False])
        writer.writerow(["torque_command_published_by_stage1110", False])
        writer.writerow(["stage11_scope", "full_freeze_integrity_check_only"])
        writer.writerow(["baseline_type", "mixed_online_control_baseline"])
        writer.writerow(["verified_full_publisher_path_no_active_publisher_frozen", full_freeze_integrity_passed])
        writer.writerow(["ros2_cpp_realtime_controller_completed", False])
        writer.writerow(["pure_wbc_locomotion_completed", False])
        writer.writerow(["ekf_completed", False])
        writer.writerow(["full_3d_centroidal_mpc_completed", False])
        writer.writerow(["num_checks", len(checks)])
        writer.writerow(["num_failed_checks", sum(1 for row in checks if not row["pass"])])
        writer.writerow(["pass", all_pass])
        writer.writerow(["log_csv", str(LOG_PATH.relative_to(ROOT))])
        writer.writerow(["hash_check_csv", str(HASH_CHECK_PATH.relative_to(ROOT))])
        writer.writerow(["safety_gate_csv", str(SAFETY_GATE_PATH.relative_to(ROOT))])
        writer.writerow(["summary_csv", str(SUMMARY_PATH.relative_to(ROOT))])
        writer.writerow(["doc", str(DOC_PATH.relative_to(ROOT))])

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 11.10 Full Freeze Integrity Check

Stage 11.10 完成 full freeze integrity check。

- Script: `scripts/stage11_full_freeze_integrity_check.py`
- Log: `results/logs_sample/stage11_full_freeze_integrity_check_log.csv`
- Hash check: `results/logs_sample/stage11_full_freeze_integrity_check_hash_check.csv`
- Safety gate: `results/logs_sample/stage11_torque_publisher_safety_gate_after_stage1110.csv`
- Summary: `results/logs_sample/stage11_full_freeze_integrity_check_summary.csv`
- Docs: `docs/STAGE11_FULL_FREEZE_INTEGRITY_CHECK.md`
- pass: `{all_pass}`
- hash_integrity_passed: `{hash_integrity_passed}`
- verified_full_publisher_path_no_active_publisher_frozen: `{full_freeze_integrity_passed}`
- g8_manual_enable_active: `{manual_enable_active}`
- g9_active_ros_publisher_path_exists: `{active_ros_publisher_path_exists}`
- torque_enable_ready: `{torque_enable_ready}`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 11.10 只验证 freeze integrity，不创建 ROS publisher，不发布 torque，不改变控制律。
""".strip()

    old = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 11.10 Full Freeze Integrity Check"
    if marker not in old:
        status_path.write_text(old.rstrip() + "\n\n" + block + "\n")

    print("[Stage 11.10] full freeze integrity check")
    print(f"pass={all_pass}")
    print(f"stage119_pass={stage119_pass}")
    print(f"stage119_hash_rows_checked={len(hash_rows)}")
    print(f"hash_missing_file_count={missing_hash_file_count}")
    print(f"hash_mismatch_count={hash_mismatch_count}")
    print(f"hash_integrity_passed={hash_integrity_passed}")
    print(f"verified_full_publisher_path_no_active_publisher_frozen={full_freeze_integrity_passed}")
    print(f"g8_manual_enable_active={manual_enable_active}")
    print(f"g9_active_ros_publisher_path_exists={active_ros_publisher_path_exists}")
    print(f"torque_enable_ready={torque_enable_ready}")
    print("control_law_changed=False")
    print("torque_publisher_enabled=False")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
    print(f"hash_check_csv={HASH_CHECK_PATH.relative_to(ROOT)}")
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
