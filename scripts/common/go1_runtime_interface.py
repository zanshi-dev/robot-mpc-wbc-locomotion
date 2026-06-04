#!/usr/bin/env python3
"""
Go1 MuJoCo <-> Pinocchio runtime interface adapter.

This module centralizes:
- MuJoCo actuator/qpos/qvel order: FR, FL, RR, RL
- Pinocchio actuated joint order: FL, FR, RL, RR
- MuJoCo free joint quaternion: [x, y, z, qw, qx, qy, qz]
- Pinocchio free-flyer quaternion: [x, y, z, qx, qy, qz, qw]
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np


MJ_NQ = 19
MJ_NV = 18
MJ_NU = 12

PIN_NQ = 19
PIN_NV = 18
PIN_NU = 12

TORQUE_LIMIT = 23.7

MJ_LEG_ORDER = ["FR", "FL", "RR", "RL"]
PIN_LEG_ORDER = ["FL", "FR", "RL", "RR"]
JOINT_ORDER = ["hip", "thigh", "calf"]

FOOT_LEGS = ["FR", "FL", "RR", "RL"]
PIN_FOOT_FRAMES = [f"{leg}_foot" for leg in FOOT_LEGS]


def make_joint_labels(leg_order: List[str]) -> List[str]:
    return [f"{leg}_{joint}" for leg in leg_order for joint in JOINT_ORDER]


MJ_JOINT_LABELS = make_joint_labels(MJ_LEG_ORDER)
PIN_JOINT_LABELS = make_joint_labels(PIN_LEG_ORDER)

MJ_QPOS_IDX: Dict[str, int] = {label: 7 + i for i, label in enumerate(MJ_JOINT_LABELS)}
PIN_QPOS_IDX: Dict[str, int] = {label: 7 + i for i, label in enumerate(PIN_JOINT_LABELS)}

MJ_QVEL_IDX: Dict[str, int] = {label: 6 + i for i, label in enumerate(MJ_JOINT_LABELS)}
PIN_QVEL_IDX: Dict[str, int] = {label: 6 + i for i, label in enumerate(PIN_JOINT_LABELS)}

MJ_TAU_IDX: Dict[str, int] = {label: i for i, label in enumerate(MJ_JOINT_LABELS)}
PIN_TAU_IDX: Dict[str, int] = {label: i for i, label in enumerate(PIN_JOINT_LABELS)}


@dataclass(frozen=True)
class RuntimeInterfaceContract:
    mj_nq: int = MJ_NQ
    mj_nv: int = MJ_NV
    mj_nu: int = MJ_NU
    pin_nq: int = PIN_NQ
    pin_nv: int = PIN_NV
    pin_nu: int = PIN_NU
    torque_limit: float = TORQUE_LIMIT
    mujoco_leg_order: tuple = tuple(MJ_LEG_ORDER)
    pinocchio_leg_order: tuple = tuple(PIN_LEG_ORDER)
    joint_order: tuple = tuple(JOINT_ORDER)


CONTRACT = RuntimeInterfaceContract()


def _as_vector(x: np.ndarray, expected_shape: tuple, name: str) -> np.ndarray:
    arr = np.asarray(x, dtype=float)
    if arr.shape != expected_shape:
        raise ValueError(f"{name} shape mismatch: got {arr.shape}, expected {expected_shape}")
    return arr


def normalize_quat_wxyz(quat_wxyz: np.ndarray) -> np.ndarray:
    quat = _as_vector(quat_wxyz, (4,), "quat_wxyz")
    norm = float(np.linalg.norm(quat))
    if norm <= 0.0:
        raise ValueError("Quaternion norm must be positive.")
    return quat / norm


def mujoco_qpos_to_pinocchio(q_mj: np.ndarray) -> np.ndarray:
    q_mj = _as_vector(q_mj, (MJ_NQ,), "q_mj")
    q_pin = np.zeros(PIN_NQ)

    q_pin[0:3] = q_mj[0:3]

    # MuJoCo:     [x, y, z, qw, qx, qy, qz]
    # Pinocchio: [x, y, z, qx, qy, qz, qw]
    q_pin[3:6] = q_mj[4:7]
    q_pin[6] = q_mj[3]

    for label in MJ_JOINT_LABELS:
        q_pin[PIN_QPOS_IDX[label]] = q_mj[MJ_QPOS_IDX[label]]

    return q_pin


def pinocchio_qpos_to_mujoco(q_pin: np.ndarray) -> np.ndarray:
    q_pin = _as_vector(q_pin, (PIN_NQ,), "q_pin")
    q_mj = np.zeros(MJ_NQ)

    q_mj[0:3] = q_pin[0:3]

    q_mj[3] = q_pin[6]
    q_mj[4:7] = q_pin[3:6]

    for label in PIN_JOINT_LABELS:
        q_mj[MJ_QPOS_IDX[label]] = q_pin[PIN_QPOS_IDX[label]]

    return q_mj


def mujoco_qvel_to_pinocchio(v_mj: np.ndarray) -> np.ndarray:
    v_mj = _as_vector(v_mj, (MJ_NV,), "v_mj")
    v_pin = np.zeros(PIN_NV)

    v_pin[0:6] = v_mj[0:6]

    for label in MJ_JOINT_LABELS:
        v_pin[PIN_QVEL_IDX[label]] = v_mj[MJ_QVEL_IDX[label]]

    return v_pin


def pinocchio_qvel_to_mujoco(v_pin: np.ndarray) -> np.ndarray:
    v_pin = _as_vector(v_pin, (PIN_NV,), "v_pin")
    v_mj = np.zeros(MJ_NV)

    v_mj[0:6] = v_pin[0:6]

    for label in PIN_JOINT_LABELS:
        v_mj[MJ_QVEL_IDX[label]] = v_pin[PIN_QVEL_IDX[label]]

    return v_mj


def mujoco_tau_to_pinocchio(tau_mj: np.ndarray) -> np.ndarray:
    tau_mj = _as_vector(tau_mj, (MJ_NU,), "tau_mj")
    tau_pin = np.zeros(PIN_NU)

    for label in MJ_JOINT_LABELS:
        tau_pin[PIN_TAU_IDX[label]] = tau_mj[MJ_TAU_IDX[label]]

    return tau_pin


def pinocchio_tau_to_mujoco(tau_pin: np.ndarray) -> np.ndarray:
    tau_pin = _as_vector(tau_pin, (PIN_NU,), "tau_pin")
    tau_mj = np.zeros(MJ_NU)

    for label in PIN_JOINT_LABELS:
        tau_mj[MJ_TAU_IDX[label]] = tau_pin[PIN_TAU_IDX[label]]

    return tau_mj


def detect_joint_label_from_name(name: str) -> Optional[str]:
    if not name:
        return None

    for leg in FOOT_LEGS:
        for joint in JOINT_ORDER:
            if leg in name and joint in name:
                return f"{leg}_{joint}"

    return None


def make_nominal_mujoco_qpos(
    base_xyz=(0.0, 0.0, 0.286),
    quat_wxyz=(1.0, 0.0, 0.0, 0.0),
    one_leg_q=(0.0, 0.9, -1.8),
) -> np.ndarray:
    q_mj = np.zeros(MJ_NQ)
    q_mj[0:3] = np.asarray(base_xyz, dtype=float)
    q_mj[3:7] = normalize_quat_wxyz(np.asarray(quat_wxyz, dtype=float))
    q_mj[7:] = np.tile(np.asarray(one_leg_q, dtype=float), 4)
    return q_mj


def roundtrip_errors(q_mj: np.ndarray, v_mj: np.ndarray, tau_mj: np.ndarray) -> Dict[str, float]:
    q_mj = _as_vector(q_mj, (MJ_NQ,), "q_mj")
    v_mj = _as_vector(v_mj, (MJ_NV,), "v_mj")
    tau_mj = _as_vector(tau_mj, (MJ_NU,), "tau_mj")

    q_rt = pinocchio_qpos_to_mujoco(mujoco_qpos_to_pinocchio(q_mj))
    v_rt = pinocchio_qvel_to_mujoco(mujoco_qvel_to_pinocchio(v_mj))
    tau_rt = pinocchio_tau_to_mujoco(mujoco_tau_to_pinocchio(tau_mj))

    return {
        "qpos_roundtrip_max_abs": float(np.max(np.abs(q_rt - q_mj))),
        "qvel_roundtrip_max_abs": float(np.max(np.abs(v_rt - v_mj))),
        "torque_roundtrip_max_abs": float(np.max(np.abs(tau_rt - tau_mj))),
    }
