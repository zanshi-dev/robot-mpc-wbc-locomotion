#!/usr/bin/env python3
from pathlib import Path
import csv
import sys
import numpy as np

try:
    import mujoco
except Exception as e:
    print(f"[FAIL] import mujoco failed: {e}")
    sys.exit(2)

try:
    import pinocchio as pin
except Exception as e:
    print(f"[FAIL] import pinocchio failed: {e}")
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from common.go1_runtime_interface import (  # noqa: E402
    CONTRACT,
    MJ_JOINT_LABELS,
    PIN_JOINT_LABELS,
    FOOT_LEGS,
    PIN_FOOT_FRAMES,
    detect_joint_label_from_name,
    make_nominal_mujoco_qpos,
    mujoco_qpos_to_pinocchio,
    pinocchio_qpos_to_mujoco,
    mujoco_qvel_to_pinocchio,
    pinocchio_qvel_to_mujoco,
    mujoco_tau_to_pinocchio,
    pinocchio_tau_to_mujoco,
    roundtrip_errors,
)

MJCF_PATH = ROOT / "assets/go1/scene.xml"
URDF_PATH = ROOT / "assets/go1/urdf/go1.urdf"

LOG_DIR = ROOT / "results/logs_sample"
LOG_PATH = LOG_DIR / "stage08_runtime_interface_adapter_module_check_log.csv"
SUMMARY_PATH = LOG_DIR / "stage08_runtime_interface_adapter_module_check_summary.csv"
DOC_PATH = ROOT / "docs/STAGE08_RUNTIME_INTERFACE_ADAPTER_MODULE_CHECK.md"


def mj_name2id(model, obj_type, name: str) -> int:
    try:
        return mujoco.mj_name2id(model, obj_type, name)
    except Exception:
        return -1


def add_check(rows, name, value, expected, passed, detail=""):
    rows.append({
        "check": name,
        "value": str(value),
        "expected": str(expected),
        "pass": bool(passed),
        "detail": detail,
    })


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    add_check(rows, "module_import", True, True, True, "common.go1_runtime_interface")
    add_check(rows, "mjcf_exists", MJCF_PATH.exists(), True, MJCF_PATH.exists(), str(MJCF_PATH))
    add_check(rows, "urdf_exists", URDF_PATH.exists(), True, URDF_PATH.exists(), str(URDF_PATH))

    if not MJCF_PATH.exists() or not URDF_PATH.exists():
        raise FileNotFoundError("Required model files are missing.")

    mj_model = mujoco.MjModel.from_xml_path(str(MJCF_PATH))
    pin_model = pin.buildModelFromUrdf(str(URDF_PATH), pin.JointModelFreeFlyer())

    add_check(rows, "mujoco_nq_contract", mj_model.nq, CONTRACT.mj_nq, mj_model.nq == CONTRACT.mj_nq)
    add_check(rows, "mujoco_nv_contract", mj_model.nv, CONTRACT.mj_nv, mj_model.nv == CONTRACT.mj_nv)
    add_check(rows, "mujoco_nu_contract", mj_model.nu, CONTRACT.mj_nu, mj_model.nu == CONTRACT.mj_nu)
    add_check(rows, "pinocchio_nq_contract", pin_model.nq, CONTRACT.pin_nq, pin_model.nq == CONTRACT.pin_nq)
    add_check(rows, "pinocchio_nv_contract", pin_model.nv, CONTRACT.pin_nv, pin_model.nv == CONTRACT.pin_nv)

    mj_actuator_names = [
        mujoco.mj_id2name(mj_model, mujoco.mjtObj.mjOBJ_ACTUATOR, i) or ""
        for i in range(mj_model.nu)
    ]
    detected_mj_order = [detect_joint_label_from_name(name) for name in mj_actuator_names]

    add_check(
        rows,
        "mujoco_actuator_order_from_module",
        detected_mj_order,
        MJ_JOINT_LABELS,
        detected_mj_order == MJ_JOINT_LABELS,
        "actuator_names=" + repr(mj_actuator_names),
    )

    detected_pin_order = []
    for name in list(pin_model.names):
        label = detect_joint_label_from_name(name)
        if label is not None:
            detected_pin_order.append(label)

    add_check(
        rows,
        "pinocchio_joint_order_from_module",
        detected_pin_order,
        PIN_JOINT_LABELS,
        detected_pin_order == PIN_JOINT_LABELS,
        "pin_joint_names=" + repr(list(pin_model.names)),
    )

    for leg, frame_name in zip(FOOT_LEGS, PIN_FOOT_FRAMES):
        site_id = mj_name2id(mj_model, mujoco.mjtObj.mjOBJ_SITE, leg)
        geom_id = mj_name2id(mj_model, mujoco.mjtObj.mjOBJ_GEOM, leg)
        has_mj_object = site_id >= 0 or geom_id >= 0

        frame_id = pin_model.getFrameId(frame_name)
        has_pin_frame = frame_id < len(pin_model.frames)

        add_check(
            rows,
            f"foot_name_contract_from_module_{leg}",
            {"mujoco_site_id": site_id, "mujoco_geom_id": geom_id, "pin_frame_id": frame_id if has_pin_frame else -1},
            {"mujoco_site_or_geom": leg, "pin_frame": frame_name},
            has_mj_object and has_pin_frame,
        )

    q_mj = make_nominal_mujoco_qpos(
        base_xyz=(0.12, -0.03, 0.286),
        quat_wxyz=(1.0, 0.01, -0.02, 0.015),
        one_leg_q=(0.0, 0.9, -1.8),
    )
    q_mj[7:] += np.linspace(-0.03, 0.03, 12)

    v_mj = np.linspace(-0.17, 0.19, CONTRACT.mj_nv)
    tau_mj = np.linspace(-5.0, 5.0, CONTRACT.mj_nu)

    q_pin = mujoco_qpos_to_pinocchio(q_mj)
    q_rt = pinocchio_qpos_to_mujoco(q_pin)

    v_pin = mujoco_qvel_to_pinocchio(v_mj)
    v_rt = pinocchio_qvel_to_mujoco(v_pin)

    tau_pin = mujoco_tau_to_pinocchio(tau_mj)
    tau_rt = pinocchio_tau_to_mujoco(tau_pin)

    errors = roundtrip_errors(q_mj, v_mj, tau_mj)

    add_check(rows, "qpos_roundtrip_module_max_abs", errors["qpos_roundtrip_max_abs"], "<=1e-12", errors["qpos_roundtrip_max_abs"] <= 1e-12)
    add_check(rows, "qvel_roundtrip_module_max_abs", errors["qvel_roundtrip_max_abs"], "<=1e-12", errors["qvel_roundtrip_max_abs"] <= 1e-12)
    add_check(rows, "torque_roundtrip_module_max_abs", errors["torque_roundtrip_max_abs"], "<=1e-12", errors["torque_roundtrip_max_abs"] <= 1e-12)

    add_check(rows, "qpos_direct_roundtrip_allclose", bool(np.allclose(q_rt, q_mj, atol=1e-12)), True, np.allclose(q_rt, q_mj, atol=1e-12))
    add_check(rows, "qvel_direct_roundtrip_allclose", bool(np.allclose(v_rt, v_mj, atol=1e-12)), True, np.allclose(v_rt, v_mj, atol=1e-12))
    add_check(rows, "tau_direct_roundtrip_allclose", bool(np.allclose(tau_rt, tau_mj, atol=1e-12)), True, np.allclose(tau_rt, tau_mj, atol=1e-12))

    quat_pass = np.allclose(q_pin[3:6], q_mj[4:7], atol=1e-15) and np.isclose(q_pin[6], q_mj[3], atol=1e-15)
    add_check(
        rows,
        "quaternion_contract_from_module",
        {"mj_qw_qx_qy_qz": q_mj[3:7].tolist(), "pin_qx_qy_qz_qw": q_pin[3:7].tolist()},
        {"pin[3:6]": "mj[4:7]", "pin[6]": "mj[3]"},
        quat_pass,
    )

    max_tau_abs = float(np.max(np.abs(tau_mj)))
    add_check(rows, "sample_tau_within_contract_limit", max_tau_abs, f"<={CONTRACT.torque_limit}", max_tau_abs <= CONTRACT.torque_limit)

    all_pass = all(row["pass"] for row in rows)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(rows)

    summary_rows = [
        ("stage", "Stage 8.1"),
        ("test_name", "runtime_interface_adapter_module_check"),
        ("module", "scripts/common/go1_runtime_interface.py"),
        ("mujoco_nq", mj_model.nq),
        ("mujoco_nv", mj_model.nv),
        ("mujoco_nu", mj_model.nu),
        ("pinocchio_nq", pin_model.nq),
        ("pinocchio_nv", pin_model.nv),
        ("qpos_roundtrip_max_abs", errors["qpos_roundtrip_max_abs"]),
        ("qvel_roundtrip_max_abs", errors["qvel_roundtrip_max_abs"]),
        ("torque_roundtrip_max_abs", errors["torque_roundtrip_max_abs"]),
        ("num_checks", len(rows)),
        ("num_failed_checks", sum(1 for row in rows if not row["pass"])),
        ("pass", all_pass),
        ("log_csv", str(LOG_PATH.relative_to(ROOT))),
        ("summary_csv", str(SUMMARY_PATH.relative_to(ROOT))),
    ]

    with SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerows(summary_rows)

    DOC_PATH.write_text(f"""# Stage 8.1 Runtime Interface Adapter Module Check

## Target

Extract the MuJoCo/Pinocchio runtime state mapping from the Stage 8.0 one-off contract check into a reusable Python module.

## Module

- `scripts/common/go1_runtime_interface.py`

## Verified contracts

1. MuJoCo model dimensions.
2. Pinocchio model dimensions.
3. MuJoCo actuator order.
4. Pinocchio actuated joint order.
5. Floating-base quaternion order conversion.
6. qpos / qvel / torque round-trip.
7. MuJoCo foot object and Pinocchio foot frame naming.

## Outputs

- Log CSV: `results/logs_sample/stage08_runtime_interface_adapter_module_check_log.csv`
- Summary CSV: `results/logs_sample/stage08_runtime_interface_adapter_module_check_summary.csv`

## Result

- pass: `{all_pass}`
- qpos_roundtrip_max_abs: `{errors["qpos_roundtrip_max_abs"]}`
- qvel_roundtrip_max_abs: `{errors["qvel_roundtrip_max_abs"]}`
- torque_roundtrip_max_abs: `{errors["torque_roundtrip_max_abs"]}`

## Boundary

This stage only creates and validates the Python runtime adapter module.

It does not complete ROS2/C++ migration, EKF, base velocity tracking, full MPC, or pure full WBC locomotion.
""")

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 8.1 Runtime Interface Adapter Module Check

Stage 8.1 extracted the MuJoCo/Pinocchio runtime mapping logic into a reusable Python module.

- Module: `scripts/common/go1_runtime_interface.py`
- Script: `scripts/stage08_runtime_interface_adapter_module_check.py`
- Log: `results/logs_sample/stage08_runtime_interface_adapter_module_check_log.csv`
- Summary: `results/logs_sample/stage08_runtime_interface_adapter_module_check_summary.csv`
- Docs: `docs/STAGE08_RUNTIME_INTERFACE_ADAPTER_MODULE_CHECK.md`
- pass: `{all_pass}`
- qpos_roundtrip_max_abs: `{errors["qpos_roundtrip_max_abs"]}`
- qvel_roundtrip_max_abs: `{errors["qvel_roundtrip_max_abs"]}`
- torque_roundtrip_max_abs: `{errors["torque_roundtrip_max_abs"]}`

This stage only validates the reusable runtime adapter. It does not complete ROS2/C++ migration or pure WBC locomotion.
""".strip()

    old_status = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 8.1 Runtime Interface Adapter Module Check"
    if marker not in old_status:
        status_path.write_text(old_status.rstrip() + "\n\n" + block + "\n")

    print("[Stage 8.1] runtime interface adapter module check")
    print(f"pass={all_pass}")
    print(f"log_csv={LOG_PATH.relative_to(ROOT)}")
    print(f"summary_csv={SUMMARY_PATH.relative_to(ROOT)}")
    print(f"doc={DOC_PATH.relative_to(ROOT)}")

    if not all_pass:
        print("\nFailed checks:")
        for row in rows:
            if not row["pass"]:
                print(f"- {row['check']}: value={row['value']} expected={row['expected']} detail={row['detail']}")
        sys.exit(2)


if __name__ == "__main__":
    main()
