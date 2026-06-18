#!/usr/bin/env python3
"""Stage 15.7 MuJoCo compatibility audit for Jacobian torque candidates.

This stage connects prior model/Jacobian audit outputs to a MuJoCo model in an
offline, zero-torque, kinematic-forward path. It does not call mj_step for
dynamic torque execution and does not publish ROS torque.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

try:
    import mujoco
except Exception as exc:  # pragma: no cover
    mujoco = None  # type: ignore[assignment]
    MUJOCO_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
else:
    MUJOCO_IMPORT_ERROR = ""

LEGS = ("FR", "FL", "RR", "RL")
JOINT_KINDS = ("hip", "thigh", "calf")


def norm_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def mj_name(model, obj_type, idx: int) -> str:
    name = mujoco.mj_id2name(model, obj_type, idx)
    return name or ""


def list_mujoco_joints(model) -> List[Dict[str, Any]]:
    rows = []
    for jid in range(model.njnt):
        name = mj_name(model, mujoco.mjtObj.mjOBJ_JOINT, jid)
        jtype = int(model.jnt_type[jid])
        qposadr = int(model.jnt_qposadr[jid])
        dofadr = int(model.jnt_dofadr[jid])
        rows.append({"id": jid, "name": name, "type": jtype, "qposadr": qposadr, "dofadr": dofadr})
    return rows


def list_mujoco_actuators(model) -> List[Dict[str, Any]]:
    rows = []
    for aid in range(model.nu):
        name = mj_name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, aid)
        trnid0 = int(model.actuator_trnid[aid, 0]) if model.actuator_trnid.size else -1
        joint_name = ""
        if 0 <= trnid0 < model.njnt:
            joint_name = mj_name(model, mujoco.mjtObj.mjOBJ_JOINT, trnid0)
        rows.append({"id": aid, "name": name, "joint_id": trnid0, "joint_name": joint_name})
    return rows


def ordered_joint_names(stage15_6: Dict[str, Any]) -> List[str]:
    joint_map = stage15_6.get("joint_map") or {}
    names: List[str] = []
    for leg in LEGS:
        leg_map = joint_map.get(leg) or {}
        for kind in JOINT_KINDS:
            name = leg_map.get(kind)
            if name:
                names.append(name)
    return names


def select_mjcf_path(repo_root: Path, stage15_5: Dict[str, Any], stage15_6: Dict[str, Any]) -> Path:
    selected_path = stage15_6.get("selected_model_path") or ""
    selected_type = (stage15_6.get("selected_model_type") or "").lower()
    if selected_path and (selected_path.endswith(".xml") or selected_path.endswith(".mjcf") or "mujoco" in selected_type or "mjcf" in selected_type):
        return (repo_root / selected_path).resolve()
    candidates = stage15_5.get("candidate_models") or []
    for cand in candidates:
        ctype = (cand.get("model_type") or "").lower()
        cpath = cand.get("path") or ""
        if cpath and (cpath.endswith(".xml") or cpath.endswith(".mjcf") or "mujoco" in ctype or "mjcf" in ctype):
            return (repo_root / cpath).resolve()
    raise RuntimeError("No MJCF/MuJoCo XML candidate found in Stage 15.5 report")


def match_joints(target_names: Sequence[str], mj_joints: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_exact = {j["name"]: j for j in mj_joints}
    by_norm = {norm_name(j["name"]): j for j in mj_joints if j["name"]}
    out = []
    for order_idx, name in enumerate(target_names):
        matched = by_exact.get(name)
        if matched is None:
            matched = by_norm.get(norm_name(name))
        out.append(
            {
                "candidate_order": order_idx,
                "candidate_joint_name": name,
                "matched": matched is not None,
                "mujoco_joint_id": matched["id"] if matched else -1,
                "mujoco_joint_name": matched["name"] if matched else "",
                "qposadr": matched["qposadr"] if matched else -1,
                "dofadr": matched["dofadr"] if matched else -1,
            }
        )
    return out


def match_actuators(matched_joints: Sequence[Dict[str, Any]], actuators: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_joint_id: Dict[int, Dict[str, Any]] = {}
    by_joint_name: Dict[str, Dict[str, Any]] = {}
    for actuator in actuators:
        by_joint_id[actuator["joint_id"]] = actuator
        by_joint_name[actuator["joint_name"]] = actuator
    out = []
    for mj in matched_joints:
        act = by_joint_id.get(mj["mujoco_joint_id"]) or by_joint_name.get(mj["mujoco_joint_name"])
        out.append(
            {
                "candidate_order": mj["candidate_order"],
                "candidate_joint_name": mj["candidate_joint_name"],
                "matched_joint_name": mj["mujoco_joint_name"],
                "matched": act is not None,
                "actuator_id": act["id"] if act else -1,
                "actuator_name": act["name"] if act else "",
            }
        )
    return out


def set_free_base_if_present(model, data, z: float = 0.32) -> None:
    for jid in range(model.njnt):
        if int(model.jnt_type[jid]) == int(mujoco.mjtJoint.mjJNT_FREE):
            adr = int(model.jnt_qposadr[jid])
            if adr + 7 <= model.nq:
                data.qpos[adr + 0] = 0.0
                data.qpos[adr + 1] = 0.0
                data.qpos[adr + 2] = z
                data.qpos[adr + 3] = 1.0
                data.qpos[adr + 4] = 0.0
                data.qpos[adr + 5] = 0.0
                data.qpos[adr + 6] = 0.0
            return


def set_kinematic_pose(model, data, matched_joints: Sequence[Dict[str, Any]], step: int) -> None:
    set_free_base_if_present(model, data)
    t = step * 0.002
    for item in matched_joints:
        if not item["matched"]:
            continue
        adr = int(item["qposadr"])
        if adr < 0 or adr >= model.nq:
            continue
        order = int(item["candidate_order"])
        kind = JOINT_KINDS[order % 3]
        leg_i = order // 3
        phase = 2.0 * math.pi * (0.8 * t + 0.25 * leg_i)
        if kind == "hip":
            value = 0.04 * math.sin(phase)
        elif kind == "thigh":
            value = 0.75 + 0.08 * math.sin(phase)
        else:
            value = -1.45 + 0.10 * math.sin(phase + 0.5)
        data.qpos[adr] = value


def torque_candidate_compatibility(stage15_6: Dict[str, Any], matched_joint_count: int) -> Dict[str, Any]:
    alpha_max = stage15_6.get("alpha_max_tau_abs") or {}
    torque_limit = float(stage15_6.get("torque_limit_for_audit", 18.0))
    return {
        "candidate_joint_count": matched_joint_count,
        "stage15_6_max_tau_candidate_abs": float(stage15_6.get("max_tau_candidate_abs", 0.0)),
        "stage15_6_alpha_max_tau_abs": alpha_max,
        "torque_limit_for_audit": torque_limit,
        "alpha_0_10_within_limit": float(alpha_max.get("0.10", 0.0)) <= torque_limit,
        "alpha_0_20_within_limit": float(alpha_max.get("0.20", 0.0)) <= torque_limit,
    }


def run_audit(repo_root: Path, stage15_5_path: Path, stage15_6_path: Path, output_csv: Path, output_json: Path, total_steps: int) -> Dict[str, Any]:
    if mujoco is None:
        raise RuntimeError(f"MuJoCo import failed: {MUJOCO_IMPORT_ERROR}")
    stage15_5 = load_json(stage15_5_path)
    stage15_6 = load_json(stage15_6_path)
    mjcf_path = select_mjcf_path(repo_root, stage15_5, stage15_6)
    if not mjcf_path.exists():
        raise RuntimeError(f"MJCF candidate path does not exist: {mjcf_path}")

    model = mujoco.MjModel.from_xml_path(str(mjcf_path))
    data = mujoco.MjData(model)
    mj_joints = list_mujoco_joints(model)
    actuators = list_mujoco_actuators(model)
    candidate_joint_names = ordered_joint_names(stage15_6)
    matched_joints = match_joints(candidate_joint_names, mj_joints)
    matched_actuators = match_actuators(matched_joints, actuators)
    mapped_joint_count = sum(1 for item in matched_joints if item["matched"])
    mapped_actuator_count = sum(1 for item in matched_actuators if item["matched"])

    qpos_finite = True
    qvel_finite = True
    nonzero_ctrl_steps = 0
    rows: List[Dict[str, Any]] = []
    base_z_min = float("inf")
    base_z_max = float("-inf")

    if model.nu:
        data.ctrl[:] = 0.0

    for step in range(total_steps):
        set_kinematic_pose(model, data, matched_joints, step)
        if model.nu:
            data.ctrl[:] = 0.0
        mujoco.mj_forward(model, data)
        if model.nu and float(np.max(np.abs(data.ctrl))) > 1e-12:
            nonzero_ctrl_steps += 1
        qpos_finite = qpos_finite and bool(np.all(np.isfinite(data.qpos)))
        qvel_finite = qvel_finite and bool(np.all(np.isfinite(data.qvel)))
        base_z = float(data.qpos[2]) if model.nq >= 3 else 0.0
        base_z_min = min(base_z_min, base_z)
        base_z_max = max(base_z_max, base_z)
        if step % 20 == 0 or step == total_steps - 1:
            rows.append(
                {
                    "step": step,
                    "qpos_finite": int(bool(np.all(np.isfinite(data.qpos)))),
                    "qvel_finite": int(bool(np.all(np.isfinite(data.qvel)))),
                    "ctrl_max_abs": float(np.max(np.abs(data.ctrl))) if model.nu else 0.0,
                    "base_z": base_z,
                    "mapped_joint_count": mapped_joint_count,
                    "mapped_actuator_count": mapped_actuator_count,
                }
            )

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["step", "qpos_finite", "qvel_finite", "ctrl_max_abs", "base_z", "mapped_joint_count", "mapped_actuator_count"],
        )
        writer.writeheader()
        writer.writerows(rows)

    compat = torque_candidate_compatibility(stage15_6, mapped_joint_count)
    summary = {
        "stage": "15.7",
        "name": "mujoco_candidate_compatibility_audit",
        "mujoco_imported": mujoco is not None,
        "mujoco_import_error": MUJOCO_IMPORT_ERROR,
        "mujoco_model_loaded": True,
        "mjcf_model_path": str(mjcf_path.relative_to(repo_root)) if mjcf_path.is_relative_to(repo_root) else str(mjcf_path),
        "nq": int(model.nq),
        "nv": int(model.nv),
        "nu": int(model.nu),
        "njnt": int(model.njnt),
        "candidate_joint_names": candidate_joint_names,
        "matched_joints": matched_joints,
        "matched_actuators": matched_actuators,
        "mapped_joint_count": int(mapped_joint_count),
        "mapped_actuator_count": int(mapped_actuator_count),
        "kinematic_forward_steps": int(total_steps),
        "mj_forward_called": True,
        "mj_step_called": False,
        "qpos_finite": bool(qpos_finite),
        "qvel_finite": bool(qvel_finite),
        "base_z_min": float(base_z_min),
        "base_z_max": float(base_z_max),
        "nonzero_ctrl_steps": int(nonzero_ctrl_steps),
        "torque_candidate_compatibility": compat,
        "boundary": {
            "mujoco_torque_used": False,
            "mujoco_dynamics_step_used": False,
            "ros_publisher_used": False,
            "frozen_mixed_baseline_modified": False,
            "torque_enable_ready_claimed": False,
            "hardware_deployment_claimed": False,
            "dry_run_only": True,
        },
        "notes": [
            "This stage loads the MuJoCo model and calls mj_forward for kinematic compatibility only.",
            "It does not call mj_step and does not apply candidate torque to MuJoCo.",
            "The purpose is joint/actuator/order compatibility before a future torque-in-the-loop simulation stage.",
        ],
    }
    output_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--stage15-5-report", type=Path, default=None)
    parser.add_argument("--stage15-6-summary", type=Path, default=None)
    parser.add_argument("--output-csv", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--total-steps", type=int, default=2400)
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    log_dir = repo_root / "results/logs_sample"
    stage15_5_path = args.stage15_5_report or log_dir / "stage15_5_model_readiness_audit.json"
    stage15_6_path = args.stage15_6_summary or log_dir / "stage15_6_real_model_jacobian_candidate_rollout_summary.json"
    output_csv = args.output_csv or log_dir / "stage15_7_mujoco_candidate_compatibility_audit.csv"
    output_json = args.output_json or log_dir / "stage15_7_mujoco_candidate_compatibility_audit_summary.json"

    summary = run_audit(repo_root, stage15_5_path, stage15_6_path, output_csv, output_json, args.total_steps)
    print("stage15_7_audit_completed: true")
    print(f"mjcf_model_path: {summary['mjcf_model_path']}")
    print(f"mujoco_nq_nv_nu: {summary['nq']} / {summary['nv']} / {summary['nu']}")
    print(f"mapped_joint_count: {summary['mapped_joint_count']}")
    print(f"mapped_actuator_count: {summary['mapped_actuator_count']}")
    print(f"mj_step_called: {summary['mj_step_called']}")
    print(f"nonzero_ctrl_steps: {summary['nonzero_ctrl_steps']}")
    print(f"output_json: {output_json}")
    print(f"output_csv: {output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
