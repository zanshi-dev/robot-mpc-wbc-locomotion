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
MJCF_PATH = ROOT / "assets/go1/scene.xml"
URDF_PATH = ROOT / "assets/go1/urdf/go1.urdf"

LOG_DIR = ROOT / "results/logs_sample"
DOC_PATH = ROOT / "docs/STAGE08_RUNTIME_INTERFACE_CONTRACT_CHECK.md"
LOG_PATH = LOG_DIR / "stage08_runtime_interface_contract_check_log.csv"
SUMMARY_PATH = LOG_DIR / "stage08_runtime_interface_contract_check_summary.csv"

EXPECTED_MJ_NQ = 19
EXPECTED_MJ_NV = 18
EXPECTED_MJ_NU = 12
EXPECTED_PIN_NQ = 19
EXPECTED_PIN_NV = 18
TORQUE_LIMIT = 23.7

MJ_LEG_ORDER = ["FR", "FL", "RR", "RL"]
PIN_LEG_ORDER = ["FL", "FR", "RL", "RR"]
JOINT_ORDER = ["hip", "thigh", "calf"]

MJ_LABELS = [f"{leg}_{joint}" for leg in MJ_LEG_ORDER for joint in JOINT_ORDER]
PIN_LABELS = [f"{leg}_{joint}" for leg in PIN_LEG_ORDER for joint in JOINT_ORDER]

MJ_Q_IDX = {label: 7 + i for i, label in enumerate(MJ_LABELS)}
PIN_Q_IDX = {label: 7 + i for i, label in enumerate(PIN_LABELS)}

MJ_V_IDX = {label: 6 + i for i, label in enumerate(MJ_LABELS)}
PIN_V_IDX = {label: 6 + i for i, label in enumerate(PIN_LABELS)}

MJ_TAU_IDX = {label: i for i, label in enumerate(MJ_LABELS)}
PIN_TAU_IDX = {label: i for i, label in enumerate(PIN_LABELS)}


def mj_qpos_to_pin(q_mj: np.ndarray) -> np.ndarray:
    q_mj = np.asarray(q_mj, dtype=float)
    q_pin = np.zeros(19)

    q_pin[0:3] = q_mj[0:3]

    # MuJoCo free joint: [x, y, z, qw, qx, qy, qz]
    # Pinocchio free-flyer: [x, y, z, qx, qy, qz, qw]
    q_pin[3:6] = q_mj[4:7]
    q_pin[6] = q_mj[3]

    for label in MJ_LABELS:
        q_pin[PIN_Q_IDX[label]] = q_mj[MJ_Q_IDX[label]]

    return q_pin


def pin_qpos_to_mj(q_pin: np.ndarray) -> np.ndarray:
    q_pin = np.asarray(q_pin, dtype=float)
    q_mj = np.zeros(19)

    q_mj[0:3] = q_pin[0:3]

    q_mj[3] = q_pin[6]
    q_mj[4:7] = q_pin[3:6]

    for label in PIN_LABELS:
        q_mj[MJ_Q_IDX[label]] = q_pin[PIN_Q_IDX[label]]

    return q_mj


def mj_qvel_to_pin(v_mj: np.ndarray) -> np.ndarray:
    v_mj = np.asarray(v_mj, dtype=float)
    v_pin = np.zeros(18)

    v_pin[0:6] = v_mj[0:6]

    for label in MJ_LABELS:
        v_pin[PIN_V_IDX[label]] = v_mj[MJ_V_IDX[label]]

    return v_pin


def pin_qvel_to_mj(v_pin: np.ndarray) -> np.ndarray:
    v_pin = np.asarray(v_pin, dtype=float)
    v_mj = np.zeros(18)

    v_mj[0:6] = v_pin[0:6]

    for label in PIN_LABELS:
        v_mj[MJ_V_IDX[label]] = v_pin[PIN_V_IDX[label]]

    return v_mj


def mj_tau_to_pin(tau_mj: np.ndarray) -> np.ndarray:
    tau_mj = np.asarray(tau_mj, dtype=float)
    tau_pin = np.zeros(12)

    for label in MJ_LABELS:
        tau_pin[PIN_TAU_IDX[label]] = tau_mj[MJ_TAU_IDX[label]]

    return tau_pin


def pin_tau_to_mj(tau_pin: np.ndarray) -> np.ndarray:
    tau_pin = np.asarray(tau_pin, dtype=float)
    tau_mj = np.zeros(12)

    for label in PIN_LABELS:
        tau_mj[MJ_TAU_IDX[label]] = tau_pin[PIN_TAU_IDX[label]]

    return tau_mj


def detect_label_from_name(name: str):
    if not name:
        return None
    for leg in ["FR", "FL", "RR", "RL"]:
        for joint in JOINT_ORDER:
            if leg in name and joint in name:
                return f"{leg}_{joint}"
    return None


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
    (ROOT / "docs").mkdir(parents=True, exist_ok=True)

    rows = []

    add_check(rows, "mjcf_exists", MJCF_PATH.exists(), True, MJCF_PATH.exists(), str(MJCF_PATH))
    add_check(rows, "urdf_exists", URDF_PATH.exists(), True, URDF_PATH.exists(), str(URDF_PATH))

    if not MJCF_PATH.exists() or not URDF_PATH.exists():
        raise FileNotFoundError("Required model files are missing.")

    mj_model = mujoco.MjModel.from_xml_path(str(MJCF_PATH))
    pin_model = pin.buildModelFromUrdf(str(URDF_PATH), pin.JointModelFreeFlyer())

    add_check(rows, "mujoco_nq", mj_model.nq, EXPECTED_MJ_NQ, mj_model.nq == EXPECTED_MJ_NQ)
    add_check(rows, "mujoco_nv", mj_model.nv, EXPECTED_MJ_NV, mj_model.nv == EXPECTED_MJ_NV)
    add_check(rows, "mujoco_nu", mj_model.nu, EXPECTED_MJ_NU, mj_model.nu == EXPECTED_MJ_NU)
    add_check(rows, "pinocchio_nq", pin_model.nq, EXPECTED_PIN_NQ, pin_model.nq == EXPECTED_PIN_NQ)
    add_check(rows, "pinocchio_nv", pin_model.nv, EXPECTED_PIN_NV, pin_model.nv == EXPECTED_PIN_NV)

    mj_actuator_names = [
        mujoco.mj_id2name(mj_model, mujoco.mjtObj.mjOBJ_ACTUATOR, i) or ""
        for i in range(mj_model.nu)
    ]
    detected_mj_order = [detect_label_from_name(name) for name in mj_actuator_names]
    add_check(
        rows,
        "mujoco_actuator_order",
        detected_mj_order,
        MJ_LABELS,
        detected_mj_order == MJ_LABELS,
        "actuator_names=" + repr(mj_actuator_names),
    )

    pin_joint_names = list(pin_model.names)
    detected_pin_order = []
    for name in pin_joint_names:
        label = detect_label_from_name(name)
        if label is not None:
            detected_pin_order.append(label)

    add_check(
        rows,
        "pinocchio_actuated_joint_order",
        detected_pin_order,
        PIN_LABELS,
        detected_pin_order == PIN_LABELS,
        "pin_joint_names=" + repr(pin_joint_names),
    )

    for leg in ["FR", "FL", "RR", "RL"]:
        site_id = mj_name2id(mj_model, mujoco.mjtObj.mjOBJ_SITE, leg)
        geom_id = mj_name2id(mj_model, mujoco.mjtObj.mjOBJ_GEOM, leg)
        has_mj_foot_object = site_id >= 0 or geom_id >= 0

        frame_name = f"{leg}_foot"
        frame_id = pin_model.getFrameId(frame_name)
        has_pin_frame = frame_id < len(pin_model.frames)

        add_check(
            rows,
            f"foot_name_contract_{leg}",
            {
                "mujoco_site_id": site_id,
                "mujoco_geom_id": geom_id,
                "pin_frame_id": frame_id if has_pin_frame else -1,
            },
            {
                "mujoco_site_or_geom": leg,
                "pin_frame": frame_name,
            },
            has_mj_foot_object and has_pin_frame,
        )

    # Deterministic runtime sample.
    q_mj = np.zeros(19)
    q_mj[0:3] = np.array([0.12, -0.03, 0.286])
    quat_wxyz = np.array([1.0, 0.01, -0.02, 0.015])
    quat_wxyz /= np.linalg.norm(quat_wxyz)
    q_mj[3:7] = quat_wxyz

    nominal_one_leg = np.array([0.0, 0.9, -1.8])
    q_mj[7:] = np.tile(nominal_one_leg, 4)
    q_mj[7:] += np.linspace(-0.03, 0.03, 12)

    v_mj = np.linspace(-0.17, 0.19, 18)
    tau_mj = np.linspace(-5.0, 5.0, 12)

    q_pin = mj_qpos_to_pin(q_mj)
    q_mj_roundtrip = pin_qpos_to_mj(q_pin)
    q_roundtrip_max_abs = float(np.max(np.abs(q_mj_roundtrip - q_mj)))

    v_pin = mj_qvel_to_pin(v_mj)
    v_mj_roundtrip = pin_qvel_to_mj(v_pin)
    v_roundtrip_max_abs = float(np.max(np.abs(v_mj_roundtrip - v_mj)))

    tau_pin = mj_tau_to_pin(tau_mj)
    tau_mj_roundtrip = pin_tau_to_mj(tau_pin)
    tau_roundtrip_max_abs = float(np.max(np.abs(tau_mj_roundtrip - tau_mj)))

    quat_contract_value = {
        "mj_qw_qx_qy_qz": q_mj[3:7].tolist(),
        "pin_qx_qy_qz_qw": q_pin[3:7].tolist(),
    }
    quat_contract_expected = {
        "pin[3:6]": "mj[4:7]",
        "pin[6]": "mj[3]",
    }
    quat_pass = (
        np.allclose(q_pin[3:6], q_mj[4:7], atol=1e-15)
        and np.isclose(q_pin[6], q_mj[3], atol=1e-15)
    )

    add_check(rows, "floating_base_quaternion_contract", quat_contract_value, quat_contract_expected, quat_pass)
    add_check(rows, "qpos_roundtrip_max_abs", q_roundtrip_max_abs, "<=1e-12", q_roundtrip_max_abs <= 1e-12)
    add_check(rows, "qvel_roundtrip_max_abs", v_roundtrip_max_abs, "<=1e-12", v_roundtrip_max_abs <= 1e-12)
    add_check(rows, "torque_roundtrip_max_abs", tau_roundtrip_max_abs, "<=1e-12", tau_roundtrip_max_abs <= 1e-12)

    add_check(
        rows,
        "torque_sample_within_limit",
        float(np.max(np.abs(tau_mj))),
        f"<={TORQUE_LIMIT}",
        float(np.max(np.abs(tau_mj))) <= TORQUE_LIMIT,
    )

    all_pass = all(row["pass"] for row in rows)

    with LOG_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "value", "expected", "pass", "detail"])
        writer.writeheader()
        writer.writerows(rows)

    summary_rows = [
        ("stage", "Stage 8.0"),
        ("test_name", "runtime_interface_contract_check"),
        ("mjcf_path", str(MJCF_PATH.relative_to(ROOT))),
        ("urdf_path", str(URDF_PATH.relative_to(ROOT))),
        ("mujoco_nq", mj_model.nq),
        ("mujoco_nv", mj_model.nv),
        ("mujoco_nu", mj_model.nu),
        ("pinocchio_nq", pin_model.nq),
        ("pinocchio_nv", pin_model.nv),
        ("qpos_roundtrip_max_abs", q_roundtrip_max_abs),
        ("qvel_roundtrip_max_abs", v_roundtrip_max_abs),
        ("torque_roundtrip_max_abs", tau_roundtrip_max_abs),
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

    doc = f"""# Stage 8.0 Runtime Interface Contract Check

## Target

Stage 8 starts with a minimal runtime interface contract check before ROS2/C++ migration.

This test verifies:

1. MuJoCo model dimensions.
2. Pinocchio model dimensions.
3. MuJoCo actuator order.
4. Pinocchio actuated joint order.
5. Floating-base quaternion conversion.
6. qpos / qvel / torque reorder round-trip.
7. MuJoCo foot object and Pinocchio foot frame naming contract.

## Inputs

- MuJoCo model: `assets/go1/scene.xml`
- Pinocchio URDF: `assets/go1/urdf/go1.urdf`

## Outputs

- Log CSV: `results/logs_sample/stage08_runtime_interface_contract_check_log.csv`
- Summary CSV: `results/logs_sample/stage08_runtime_interface_contract_check_summary.csv`

## Result

- pass: `{all_pass}`
- qpos_roundtrip_max_abs: `{q_roundtrip_max_abs}`
- qvel_roundtrip_max_abs: `{v_roundtrip_max_abs}`
- torque_roundtrip_max_abs: `{tau_roundtrip_max_abs}`

## Interpretation

Passing this check means Stage 8 can safely build runtime state adapters on top of the existing Stage 7 mixed baseline.

It does not mean ROS2/C++ real-time control, EKF, MPC velocity tracking, or pure full WBC locomotion is complete.
"""

    DOC_PATH.write_text(doc)

    status_path = ROOT / "PROJECT_STATUS.md"
    block = f"""
## Stage 8.0 Runtime Interface Contract Check

Stage 8 has started with a minimal runtime interface contract check.

- Script: `scripts/stage08_runtime_interface_contract_check.py`
- Log: `results/logs_sample/stage08_runtime_interface_contract_check_log.csv`
- Summary: `results/logs_sample/stage08_runtime_interface_contract_check_summary.csv`
- Docs: `docs/STAGE08_RUNTIME_INTERFACE_CONTRACT_CHECK.md`
- pass: `{all_pass}`
- qpos_roundtrip_max_abs: `{q_roundtrip_max_abs}`
- qvel_roundtrip_max_abs: `{v_roundtrip_max_abs}`
- torque_roundtrip_max_abs: `{tau_roundtrip_max_abs}`

This check only validates the MuJoCo/Pinocchio runtime interface contract. It does not complete ROS2/C++ migration or pure WBC locomotion.
""".strip()

    old_status = status_path.read_text() if status_path.exists() else ""
    marker = "## Stage 8.0 Runtime Interface Contract Check"
    if marker not in old_status:
        status_path.write_text(old_status.rstrip() + "\n\n" + block + "\n")

    print("[Stage 8.0] runtime interface contract check")
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
