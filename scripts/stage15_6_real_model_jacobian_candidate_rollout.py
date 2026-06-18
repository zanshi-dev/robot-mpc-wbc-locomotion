#!/usr/bin/env python3
"""Stage 15.6 real-model candidate Jacobian rollout.

This stage consumes the Stage 15.5 model readiness audit and runs a dry-run
contact-force-to-torque-candidate pipeline through Pinocchio Jacobians.

Safety boundary:
- no MuJoCo torque execution
- no ROS torque publisher
- no frozen mixed baseline modification
- no hardware deployment claim
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

try:
    import pinocchio as pin
except Exception as exc:  # pragma: no cover
    pin = None  # type: ignore[assignment]
    PINOCCHIO_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
else:
    PINOCCHIO_IMPORT_ERROR = ""

LEGS = ("FR", "FL", "RR", "RL")
JOINT_KINDS = ("hip", "thigh", "calf")
LEG_SIGNS = {
    "FR": np.array([0.24, -0.11, 0.0]),
    "FL": np.array([0.24, 0.11, 0.0]),
    "RR": np.array([-0.24, -0.11, 0.0]),
    "RL": np.array([-0.24, 0.11, 0.0]),
}
DEFAULT_JOINT_NAMES = {
    "FR": {"hip": "FR_hip_joint", "thigh": "FR_thigh_joint", "calf": "FR_calf_joint"},
    "FL": {"hip": "FL_hip_joint", "thigh": "FL_thigh_joint", "calf": "FL_calf_joint"},
    "RR": {"hip": "RR_hip_joint", "thigh": "RR_thigh_joint", "calf": "RR_calf_joint"},
    "RL": {"hip": "RL_hip_joint", "thigh": "RL_thigh_joint", "calf": "RL_calf_joint"},
}
DEFAULT_FOOT_NAMES = {leg: f"{leg}_foot" for leg in LEGS}


def norm_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_vec(text: str, fallback: Sequence[float]) -> np.ndarray:
    if not text:
        return np.array(fallback, dtype=float)
    try:
        parts = [float(x) for x in text.replace(",", " ").split()]
    except ValueError:
        return np.array(fallback, dtype=float)
    if len(parts) != 3:
        return np.array(fallback, dtype=float)
    return np.array(parts, dtype=float)


def make_joint_model(axis: np.ndarray):
    axis = np.asarray(axis, dtype=float)
    if np.linalg.norm(axis) < 1e-12:
        axis = np.array([0.0, 1.0, 0.0])
    axis = axis / np.linalg.norm(axis)
    idx = int(np.argmax(np.abs(axis)))
    if idx == 0:
        return pin.JointModelRX()
    if idx == 1:
        return pin.JointModelRY()
    return pin.JointModelRZ()


def add_frame_compat(model, name: str, parent_joint: int, placement) -> int:
    frame_type = getattr(pin, "OP_FRAME", None)
    if frame_type is None:
        frame_type = pin.FrameType.OP_FRAME
    try:
        frame = pin.Frame(name, parent_joint, 0, placement, frame_type)
    except TypeError:
        frame = pin.Frame(name, parent_joint, parent_joint, placement, frame_type)
    return model.addFrame(frame)


def add_zero_body(model, joint_id: int) -> None:
    try:
        inertia = pin.Inertia.Zero()
    except AttributeError:
        inertia = pin.Inertia(0.0, np.zeros(3), np.zeros((3, 3)))
    try:
        model.appendBodyToJoint(joint_id, inertia, pin.SE3.Identity())
    except Exception:
        pass


def inferred_mapping_from_report(report: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, str]], Dict[str, str]]:
    selected = report.get("selected_model") or {}
    inferred_joint_order = selected.get("inferred_joint_order") or {}
    inferred_feet = selected.get("inferred_foot_frames") or {}
    joint_map: Dict[str, Dict[str, str]] = {}
    foot_map: Dict[str, str] = {}
    for leg in LEGS:
        joint_map[leg] = {}
        for kind in JOINT_KINDS:
            name = (inferred_joint_order.get(leg) or {}).get(kind) or DEFAULT_JOINT_NAMES[leg][kind]
            joint_map[leg][kind] = name
        foot_map[leg] = inferred_feet.get(leg) or DEFAULT_FOOT_NAMES[leg]
    return joint_map, foot_map


def try_load_urdf_model(model_path: Path, report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if model_path.suffix.lower() != ".urdf":
        return None
    try:
        model = pin.buildModelFromUrdf(str(model_path))
        data = model.createData()
    except Exception:
        return None

    joint_map, foot_map_report = inferred_mapping_from_report(report)
    model_joint_names = list(model.names)
    joint_name_to_id = {name: idx for idx, name in enumerate(model.names)}

    # Keep only joints that are present in the Pinocchio model.
    resolved_joint_map: Dict[str, Dict[str, str]] = {}
    for leg in LEGS:
        resolved_joint_map[leg] = {}
        for kind in JOINT_KINDS:
            candidate = joint_map[leg][kind]
            if candidate in joint_name_to_id:
                resolved_joint_map[leg][kind] = candidate
            else:
                target = norm_name(candidate)
                match = next((name for name in model_joint_names if norm_name(name) == target), "")
                resolved_joint_map[leg][kind] = match

    frame_names = [frame.name for frame in model.frames]
    resolved_foot_map: Dict[str, str] = {}
    for leg in LEGS:
        candidate = foot_map_report.get(leg, "")
        if candidate in frame_names:
            resolved_foot_map[leg] = candidate
        else:
            target = norm_name(candidate)
            match = next((name for name in frame_names if norm_name(name) == target), "")
            if not match:
                match = next((name for name in frame_names if leg.lower() in norm_name(name) and ("foot" in norm_name(name) or "toe" in norm_name(name))), "")
            resolved_foot_map[leg] = match

    if sum(1 for leg in LEGS for name in resolved_joint_map[leg].values() if name) < 12:
        return None
    if sum(1 for name in resolved_foot_map.values() if name) < 4:
        return None

    return {
        "model": model,
        "data": data,
        "model_source": "urdf_pinocchio",
        "real_geometry_loaded": True,
        "joint_map": resolved_joint_map,
        "foot_map": resolved_foot_map,
    }


def build_audit_pinocchio_model(report: Dict[str, Any]) -> Dict[str, Any]:
    """Build a Pinocchio audit model using real model joint/frame names.

    This fallback is used when the selected model is MJCF/Xacro or when URDF loading
    is not directly available. It preserves Stage 15.5 joint/frame naming evidence,
    but does not claim full real geometry loading.
    """

    model = pin.Model()
    joint_map, foot_map = inferred_mapping_from_report(report)
    resolved_foot_map: Dict[str, str] = {}

    for leg in LEGS:
        parent = 0
        hip_offset = LEG_SIGNS[leg]
        placements = {
            "hip": pin.SE3(np.eye(3), hip_offset),
            "thigh": pin.SE3(np.eye(3), np.array([0.0, 0.0, -0.08])),
            "calf": pin.SE3(np.eye(3), np.array([0.0, 0.0, -0.22])),
        }
        axes = {
            "hip": np.array([1.0, 0.0, 0.0]),
            "thigh": np.array([0.0, 1.0, 0.0]),
            "calf": np.array([0.0, 1.0, 0.0]),
        }
        for kind in JOINT_KINDS:
            jname = joint_map[leg][kind]
            jid = model.addJoint(parent, make_joint_model(axes[kind]), placements[kind], jname)
            add_zero_body(model, jid)
            parent = jid
        foot_name = foot_map.get(leg) or f"{leg}_foot"
        add_frame_compat(model, foot_name, parent, pin.SE3(np.eye(3), np.array([0.0, 0.0, -0.22])))
        resolved_foot_map[leg] = foot_name

    return {
        "model": model,
        "data": model.createData(),
        "model_source": "audit_pinocchio_model_from_stage15_5_names",
        "real_geometry_loaded": False,
        "joint_map": joint_map,
        "foot_map": resolved_foot_map,
    }


def load_pinocchio_model_from_stage15_5(report: Dict[str, Any], repo_root: Path) -> Dict[str, Any]:
    if pin is None:
        raise RuntimeError(f"Pinocchio import failed: {PINOCCHIO_IMPORT_ERROR}")
    selected = report.get("selected_model") or {}
    selected_path = selected.get("path")
    if not selected_path:
        raise RuntimeError("Stage 15.5 report has no selected_model.path")
    model_path = (repo_root / selected_path).resolve()

    urdf_loaded = try_load_urdf_model(model_path, report)
    if urdf_loaded is not None:
        return urdf_loaded
    return build_audit_pinocchio_model(report)


def phase_contacts(step: int, period: int = 400) -> Dict[str, bool]:
    phase = (step // (period // 2)) % 2
    if phase == 0:
        return {"FR": True, "FL": False, "RR": False, "RL": True}
    return {"FR": False, "FL": True, "RR": True, "RL": False}


def desired_base_accel(step: int) -> np.ndarray:
    t = step * 0.002
    ax = 0.25 * math.sin(2.0 * math.pi * 0.5 * t)
    ay = 0.08 * math.sin(2.0 * math.pi * 0.25 * t)
    az = 0.04 * math.sin(2.0 * math.pi * 0.2 * t)
    return np.array([ax, ay, az], dtype=float)


def contact_forces(mass: float, gravity: float, accel: np.ndarray, contacts: Dict[str, bool], mu: float = 0.6) -> Dict[str, np.ndarray]:
    stance = [leg for leg, active in contacts.items() if active]
    forces = {leg: np.zeros(3) for leg in LEGS}
    if not stance:
        return forces
    total_force = mass * np.array([accel[0], accel[1], gravity + accel[2]], dtype=float)
    per_leg = total_force / float(len(stance))
    for leg in stance:
        fz = max(per_leg[2], 1e-6)
        fx = float(np.clip(per_leg[0], -mu * fz, mu * fz))
        fy = float(np.clip(per_leg[1], -mu * fz, mu * fz))
        forces[leg] = np.array([fx, fy, fz], dtype=float)
    return forces


def set_joint_q(model, q: np.ndarray, joint_name: str, value: float) -> None:
    jid = model.getJointId(joint_name)
    if jid <= 0 or jid >= len(model.names):
        return
    idx = model.idx_qs[jid]
    nq = model.nqs[jid]
    if nq == 1:
        q[idx] = value


def q_for_step(model, joint_map: Dict[str, Dict[str, str]], step: int) -> np.ndarray:
    q = np.zeros(model.nq)
    if hasattr(pin, "neutral"):
        try:
            q = pin.neutral(model)
        except Exception:
            q = np.zeros(model.nq)
    t = step * 0.002
    for leg_i, leg in enumerate(LEGS):
        phase = 2.0 * math.pi * (t * 0.8 + 0.25 * leg_i)
        targets = {
            "hip": 0.04 * math.sin(phase),
            "thigh": 0.75 + 0.08 * math.sin(phase),
            "calf": -1.45 + 0.10 * math.sin(phase + 0.5),
        }
        for kind, value in targets.items():
            name = joint_map.get(leg, {}).get(kind, "")
            if name:
                set_joint_q(model, q, name, value)
    return q


def frame_jacobian_linear(model, data, q: np.ndarray, frame_name: str) -> np.ndarray:
    fid = model.getFrameId(frame_name)
    pin.forwardKinematics(model, data, q)
    try:
        pin.updateFramePlacements(model, data)
    except Exception:
        pin.framesForwardKinematics(model, data, q)
    try:
        J6 = pin.computeFrameJacobian(model, data, q, fid, pin.ReferenceFrame.LOCAL_WORLD_ALIGNED)
    except AttributeError:
        J6 = pin.computeFrameJacobian(model, data, q, fid)
    return np.asarray(J6[:3, :], dtype=float)


def rollout(repo_root: Path, report_path: Path, output_csv: Path, output_json: Path, total_steps: int = 2400) -> Dict[str, Any]:
    report = load_json(report_path)
    selected = report.get("selected_model") or {}
    loaded = load_pinocchio_model_from_stage15_5(report, repo_root)
    model = loaded["model"]
    data = loaded["data"]
    joint_map: Dict[str, Dict[str, str]] = loaded["joint_map"]
    foot_map: Dict[str, str] = loaded["foot_map"]

    alpha_values = [0.0, 0.02, 0.05, 0.10, 0.20]
    rows: List[Dict[str, Any]] = []
    jacobian_norms: List[float] = []
    tau_abs_values: List[float] = []
    swing_force_max = 0.0
    nonfinite_count = 0
    torque_limit = 18.0
    alpha_max_abs = {f"{a:.2f}": 0.0 for a in alpha_values}
    alpha_saturation_steps = {f"{a:.2f}": 0 for a in alpha_values}

    for step in range(total_steps):
        contacts = phase_contacts(step)
        accel = desired_base_accel(step)
        forces = contact_forces(mass=12.0, gravity=9.81, accel=accel, contacts=contacts)
        q = q_for_step(model, joint_map, step)
        tau = np.zeros(model.nv)
        jac_norm_step = 0.0
        for leg in LEGS:
            f = forces[leg]
            if not contacts[leg]:
                swing_force_max = max(swing_force_max, float(np.linalg.norm(f)))
                continue
            frame_name = foot_map[leg]
            Jv = frame_jacobian_linear(model, data, q, frame_name)
            jac_norm = float(np.linalg.norm(Jv))
            jac_norm_step = max(jac_norm_step, jac_norm)
            jacobian_norms.append(jac_norm)
            tau += Jv.T @ f
        if not np.all(np.isfinite(tau)):
            nonfinite_count += 1
        tau_abs = float(np.max(np.abs(tau))) if tau.size else 0.0
        tau_abs_values.append(tau_abs)
        for alpha in alpha_values:
            key = f"{alpha:.2f}"
            scaled = alpha * tau
            max_abs = float(np.max(np.abs(scaled))) if scaled.size else 0.0
            alpha_max_abs[key] = max(alpha_max_abs[key], max_abs)
            if max_abs > torque_limit:
                alpha_saturation_steps[key] += 1
        if step % 20 == 0 or step == total_steps - 1:
            rows.append(
                {
                    "step": step,
                    "contact_FR": int(contacts["FR"]),
                    "contact_FL": int(contacts["FL"]),
                    "contact_RR": int(contacts["RR"]),
                    "contact_RL": int(contacts["RL"]),
                    "desired_ax": accel[0],
                    "desired_ay": accel[1],
                    "desired_az": accel[2],
                    "jacobian_norm_step": jac_norm_step,
                    "tau_candidate_max_abs": tau_abs,
                    "alpha_0_10_tau_max_abs": alpha_max_abs["0.10"],
                    "alpha_0_20_tau_max_abs": alpha_max_abs["0.20"],
                }
            )

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "step",
            "contact_FR",
            "contact_FL",
            "contact_RR",
            "contact_RL",
            "desired_ax",
            "desired_ay",
            "desired_az",
            "jacobian_norm_step",
            "tau_candidate_max_abs",
            "alpha_0_10_tau_max_abs",
            "alpha_0_20_tau_max_abs",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    mapped_joint_count = sum(1 for leg in joint_map.values() for value in leg.values() if value)
    mapped_foot_count = sum(1 for value in foot_map.values() if value)
    summary = {
        "stage": "15.6",
        "name": "real_model_jacobian_candidate_rollout",
        "pinocchio_imported": pin is not None,
        "pinocchio_import_error": PINOCCHIO_IMPORT_ERROR,
        "pinocchio_model_loaded": True,
        "selected_model_path": selected.get("path", ""),
        "selected_model_type": selected.get("model_type", ""),
        "model_source": loaded["model_source"],
        "real_model_candidate_used": True,
        "real_geometry_loaded": bool(loaded["real_geometry_loaded"]),
        "selected_model_metadata_used": True,
        "nq": int(model.nq),
        "nv": int(model.nv),
        "controlled_joint_count": int(mapped_joint_count),
        "foot_frame_count": int(mapped_foot_count),
        "joint_map": joint_map,
        "foot_map": foot_map,
        "total_steps": int(total_steps),
        "jacobian_norm_min": float(min(jacobian_norms)) if jacobian_norms else 0.0,
        "jacobian_norm_max": float(max(jacobian_norms)) if jacobian_norms else 0.0,
        "max_tau_candidate_abs": float(max(tau_abs_values)) if tau_abs_values else 0.0,
        "nonfinite_tau_steps": int(nonfinite_count),
        "swing_force_max": float(swing_force_max),
        "alpha_values": alpha_values,
        "alpha_max_tau_abs": alpha_max_abs,
        "alpha_saturation_steps": alpha_saturation_steps,
        "torque_limit_for_audit": torque_limit,
        "boundary": {
            "mujoco_torque_used": False,
            "ros_publisher_used": False,
            "frozen_mixed_baseline_modified": False,
            "torque_enable_ready_claimed": False,
            "hardware_deployment_claimed": False,
            "dry_run_only": True,
        },
        "notes": [
            "URDF models are loaded directly with Pinocchio when available.",
            "If the selected model is MJCF/Xacro or cannot be loaded as URDF, the script builds a Pinocchio audit model from Stage 15.5 real joint/frame names without claiming full real geometry.",
        ],
    }
    output_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--stage15-5-report", type=Path, default=None)
    parser.add_argument("--output-csv", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--total-steps", type=int, default=2400)
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    report_path = args.stage15_5_report or repo_root / "results/logs_sample/stage15_5_model_readiness_audit.json"
    output_csv = args.output_csv or repo_root / "results/logs_sample/stage15_6_real_model_jacobian_candidate_rollout.csv"
    output_json = args.output_json or repo_root / "results/logs_sample/stage15_6_real_model_jacobian_candidate_rollout_summary.json"

    summary = rollout(repo_root, report_path, output_csv, output_json, total_steps=args.total_steps)
    print("stage15_6_rollout_completed: true")
    print(f"selected_model_path: {summary['selected_model_path']}")
    print(f"model_source: {summary['model_source']}")
    print(f"real_geometry_loaded: {summary['real_geometry_loaded']}")
    print(f"controlled_joint_count: {summary['controlled_joint_count']}")
    print(f"foot_frame_count: {summary['foot_frame_count']}")
    print(f"jacobian_norm_min: {summary['jacobian_norm_min']}")
    print(f"max_tau_candidate_abs: {summary['max_tau_candidate_abs']}")
    print(f"output_json: {output_json}")
    print(f"output_csv: {output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
