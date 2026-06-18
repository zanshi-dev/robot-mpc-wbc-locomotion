#!/usr/bin/env python3
"""Stage 15.8 bounded MuJoCo actuator torque-path smoke test.

This is the first intentionally torque-in-the-loop MuJoCo smoke test in Stage 15.
It is deliberately short, low-amplitude, and safety-clipped. It is not a stable
locomotion claim and it does not modify the frozen mixed baseline.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

try:
    import mujoco
except Exception as exc:  # pragma: no cover
    mujoco = None  # type: ignore[assignment]
    MUJOCO_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
else:
    MUJOCO_IMPORT_ERROR = ""

ALPHAS = [0.0, 0.001, 0.002, 0.005]
SMOKE_STEPS = 200
AUDIT_CTRL_LIMIT = 0.25
LEGS = ("FR", "FL", "RR", "RL")
JOINT_KINDS = ("hip", "thigh", "calf")


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_repo_path(repo_root: Path, rel_or_abs: str) -> Path:
    path = Path(rel_or_abs)
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def initial_state(model, data) -> None:
    data.qpos[:] = 0.0
    data.qvel[:] = 0.0
    if getattr(model, "nkey", 0) > 0:
        data.qpos[:] = np.asarray(model.key_qpos[0]).reshape(-1)[: model.nq]
    else:
        # If there is a free joint, put the base at a conservative nominal height.
        for jid in range(model.njnt):
            if int(model.jnt_type[jid]) == int(mujoco.mjtJoint.mjJNT_FREE):
                adr = int(model.jnt_qposadr[jid])
                if adr + 7 <= model.nq:
                    data.qpos[adr + 0] = 0.0
                    data.qpos[adr + 1] = 0.0
                    data.qpos[adr + 2] = 0.32
                    data.qpos[adr + 3] = 1.0
                    data.qpos[adr + 4] = 0.0
                    data.qpos[adr + 5] = 0.0
                    data.qpos[adr + 6] = 0.0
                break
    if model.nu:
        data.ctrl[:] = 0.0
    mujoco.mj_forward(model, data)


def actuator_ctrl_limits(model, aid: int) -> Tuple[float, float]:
    lower, upper = -AUDIT_CTRL_LIMIT, AUDIT_CTRL_LIMIT
    try:
        limited = bool(model.actuator_ctrllimited[aid])
        if limited:
            cr = model.actuator_ctrlrange[aid]
            lower = max(lower, float(cr[0]))
            upper = min(upper, float(cr[1]))
    except Exception:
        pass
    if lower > upper:
        lower, upper = -AUDIT_CTRL_LIMIT, AUDIT_CTRL_LIMIT
    return lower, upper


def ordered_candidate_tau(step: int) -> np.ndarray:
    t = step * 0.002
    tau = []
    # A deterministic candidate-like waveform. It is only used to exercise the
    # actuator path after alpha scaling and clipping.
    for leg_i, _leg in enumerate(LEGS):
        phase = 2.0 * math.pi * (0.9 * t + 0.25 * leg_i)
        tau.append(8.0 * math.sin(phase))          # hip candidate
        tau.append(18.0 * math.sin(phase + 0.3))  # thigh candidate
        tau.append(14.0 * math.sin(phase + 0.6))  # calf candidate
    return np.asarray(tau, dtype=float)


def actuator_mapping_from_stage15_7(stage15_7: Dict[str, Any]) -> List[Dict[str, Any]]:
    matched_actuators = stage15_7.get("matched_actuators") or []
    mapping = []
    for item in matched_actuators:
        if not item.get("matched"):
            continue
        aid = int(item.get("actuator_id", -1))
        order = int(item.get("candidate_order", -1))
        if aid >= 0 and 0 <= order < 12:
            mapping.append(
                {
                    "candidate_order": order,
                    "actuator_id": aid,
                    "actuator_name": item.get("actuator_name", ""),
                    "joint_name": item.get("matched_joint_name", ""),
                }
            )
    # Preserve candidate order and remove duplicated actuators.
    mapping = sorted(mapping, key=lambda x: (x["candidate_order"], x["actuator_id"]))
    seen = set()
    dedup = []
    for item in mapping:
        if item["actuator_id"] in seen:
            continue
        seen.add(item["actuator_id"])
        dedup.append(item)
    return dedup


def run_one_alpha(model, alpha: float, actuator_map: List[Dict[str, Any]], steps: int) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    data = mujoco.MjData(model)
    initial_state(model, data)
    nonfinite_steps = 0
    nonzero_ctrl_steps = 0
    saturation_steps = 0
    max_abs_ctrl = 0.0
    max_abs_qvel = 0.0
    min_base_z = float("inf")
    max_base_z = float("-inf")
    max_ncon = 0
    rows: List[Dict[str, Any]] = []

    for step in range(steps):
        if model.nu:
            data.ctrl[:] = 0.0
        tau = ordered_candidate_tau(step)
        step_saturated = False
        for item in actuator_map:
            aid = int(item["actuator_id"])
            order = int(item["candidate_order"])
            if aid < 0 or aid >= model.nu:
                continue
            raw = float(alpha * tau[order])
            lower, upper = actuator_ctrl_limits(model, aid)
            clipped = float(np.clip(raw, lower, upper))
            if abs(clipped - raw) > 1e-12:
                step_saturated = True
            data.ctrl[aid] = clipped
        ctrl_max = float(np.max(np.abs(data.ctrl))) if model.nu else 0.0
        if ctrl_max > 1e-12:
            nonzero_ctrl_steps += 1
        if step_saturated:
            saturation_steps += 1
        max_abs_ctrl = max(max_abs_ctrl, ctrl_max)
        mujoco.mj_step(model, data)
        finite = bool(np.all(np.isfinite(data.qpos)) and np.all(np.isfinite(data.qvel)))
        if not finite:
            nonfinite_steps += 1
        max_abs_qvel = max(max_abs_qvel, float(np.max(np.abs(data.qvel))) if model.nv else 0.0)
        base_z = float(data.qpos[2]) if model.nq >= 3 else 0.0
        min_base_z = min(min_base_z, base_z)
        max_base_z = max(max_base_z, base_z)
        max_ncon = max(max_ncon, int(data.ncon))
        if step % 10 == 0 or step == steps - 1:
            rows.append(
                {
                    "alpha": alpha,
                    "step": step,
                    "ctrl_max_abs": ctrl_max,
                    "qpos_finite": int(bool(np.all(np.isfinite(data.qpos)))),
                    "qvel_finite": int(bool(np.all(np.isfinite(data.qvel)))),
                    "base_z": base_z,
                    "qvel_max_abs": float(np.max(np.abs(data.qvel))) if model.nv else 0.0,
                    "ncon": int(data.ncon),
                }
            )
    summary = {
        "alpha": alpha,
        "steps": steps,
        "nonzero_ctrl_steps": nonzero_ctrl_steps,
        "nonfinite_steps": nonfinite_steps,
        "saturation_steps": saturation_steps,
        "max_abs_ctrl": max_abs_ctrl,
        "max_abs_qvel": max_abs_qvel,
        "min_base_z": min_base_z,
        "max_base_z": max_base_z,
        "max_ncon": max_ncon,
    }
    return summary, rows


def run_smoke_test(repo_root: Path, stage15_7_path: Path, output_csv: Path, output_json: Path) -> Dict[str, Any]:
    if mujoco is None:
        raise RuntimeError(f"MuJoCo import failed: {MUJOCO_IMPORT_ERROR}")
    stage15_7 = load_json(stage15_7_path)
    mjcf_model_path = resolve_repo_path(repo_root, stage15_7.get("mjcf_model_path", ""))
    if not mjcf_model_path.exists():
        raise RuntimeError(f"missing MJCF model path from Stage 15.7: {mjcf_model_path}")
    model = mujoco.MjModel.from_xml_path(str(mjcf_model_path))
    actuator_map = actuator_mapping_from_stage15_7(stage15_7)

    all_rows: List[Dict[str, Any]] = []
    alpha_summaries: List[Dict[str, Any]] = []
    for alpha in ALPHAS:
        summary, rows = run_one_alpha(model, alpha, actuator_map, SMOKE_STEPS)
        alpha_summaries.append(summary)
        all_rows.extend(rows)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["alpha", "step", "ctrl_max_abs", "qpos_finite", "qvel_finite", "base_z", "qvel_max_abs", "ncon"],
        )
        writer.writeheader()
        writer.writerows(all_rows)

    nonzero_positive_alpha = sum(s["nonzero_ctrl_steps"] for s in alpha_summaries if s["alpha"] > 0.0)
    total_nonfinite = sum(s["nonfinite_steps"] for s in alpha_summaries)
    total_saturation = sum(s["saturation_steps"] for s in alpha_summaries)
    summary = {
        "stage": "15.8",
        "name": "mujoco_torque_smoke_test",
        "mujoco_imported": mujoco is not None,
        "mujoco_import_error": MUJOCO_IMPORT_ERROR,
        "mujoco_model_loaded": True,
        "mjcf_model_path": str(mjcf_model_path.relative_to(repo_root)) if mjcf_model_path.is_relative_to(repo_root) else str(mjcf_model_path),
        "nq": int(model.nq),
        "nv": int(model.nv),
        "nu": int(model.nu),
        "mapped_actuator_count": int(len(actuator_map)),
        "actuator_map": actuator_map,
        "alphas": ALPHAS,
        "steps_per_alpha": SMOKE_STEPS,
        "mj_step_called": True,
        "mujoco_actuator_command_used": True,
        "torque_path_smoke_test_only": True,
        "stable_locomotion_claimed": False,
        "total_nonzero_ctrl_steps_positive_alpha": int(nonzero_positive_alpha),
        "total_nonfinite_steps": int(total_nonfinite),
        "total_saturation_steps": int(total_saturation),
        "audit_ctrl_limit": AUDIT_CTRL_LIMIT,
        "alpha_summaries": alpha_summaries,
        "boundary": {
            "mujoco_torque_smoke_test_used": True,
            "ros_publisher_used": False,
            "frozen_mixed_baseline_modified": False,
            "torque_enable_ready_claimed": False,
            "hardware_deployment_claimed": False,
            "stable_locomotion_claimed": False,
            "short_horizon_only": True,
        },
        "notes": [
            "This is a short-horizon MuJoCo actuator-command smoke test, not a locomotion controller validation.",
            "The command is alpha-scaled and clipped to a conservative audit limit.",
            "No ROS torque publisher or hardware path is used.",
        ],
    }
    output_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--stage15-7-summary", type=Path, default=None)
    parser.add_argument("--output-csv", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    log_dir = repo_root / "results/logs_sample"
    stage15_7_path = args.stage15_7_summary or log_dir / "stage15_7_mujoco_candidate_compatibility_audit_summary.json"
    output_csv = args.output_csv or log_dir / "stage15_8_mujoco_torque_smoke_test.csv"
    output_json = args.output_json or log_dir / "stage15_8_mujoco_torque_smoke_test_summary.json"
    summary = run_smoke_test(repo_root, stage15_7_path, output_csv, output_json)
    print("stage15_8_smoke_test_completed: true")
    print(f"mjcf_model_path: {summary['mjcf_model_path']}")
    print(f"mapped_actuator_count: {summary['mapped_actuator_count']}")
    print(f"alphas: {summary['alphas']}")
    print(f"total_nonzero_ctrl_steps_positive_alpha: {summary['total_nonzero_ctrl_steps_positive_alpha']}")
    print(f"total_nonfinite_steps: {summary['total_nonfinite_steps']}")
    print(f"total_saturation_steps: {summary['total_saturation_steps']}")
    print(f"output_json: {output_json}")
    print(f"output_csv: {output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
