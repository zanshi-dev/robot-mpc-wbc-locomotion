#!/usr/bin/env python3
"""Stage 15.10 MuJoCo short-horizon torque-smoke policy comparison.

Compares three actuator-command policies under identical short-horizon conditions:
1. zero_ctrl
2. Stage 15.8 deterministic smoke waveform
3. Stage 15.9 J^T f candidate injection

This is a safety/compatibility comparison, not a stable locomotion benchmark.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
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

SMOKE_STEPS = 200
TARGET_MAX_CTRL = 0.08
AUDIT_CTRL_LIMIT = 0.25
POLICIES = ("zero_ctrl", "deterministic_waveform", "jtf_candidate")


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
        if bool(model.actuator_ctrllimited[aid]):
            cr = model.actuator_ctrlrange[aid]
            lower = max(lower, float(cr[0]))
            upper = min(upper, float(cr[1]))
    except Exception:
        pass
    if lower > upper:
        lower, upper = -AUDIT_CTRL_LIMIT, AUDIT_CTRL_LIMIT
    return lower, upper


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
    mapping = sorted(mapping, key=lambda x: (x["candidate_order"], x["actuator_id"]))
    seen = set()
    out = []
    for item in mapping:
        if item["actuator_id"] in seen:
            continue
        seen.add(item["actuator_id"])
        out.append(item)
    return out


def prepare_jtf_context(repo_root: Path, stage15_5_path: Path):
    m9 = load_module(repo_root / "scripts/stage15_9_mujoco_jtf_candidate_injection.py", "stage15_9_module")
    m6, _report, loaded = m9.build_stage15_6_context(repo_root, stage15_5_path)
    return m9, m6, loaded


def deterministic_tau12(repo_root: Path, step: int) -> np.ndarray:
    m8 = load_module(repo_root / "scripts/stage15_8_mujoco_torque_smoke_test.py", "stage15_8_module")
    return np.asarray(m8.ordered_candidate_tau(step), dtype=float)


def jtf_tau12(m9, m6, loaded: Dict[str, Any], step: int) -> np.ndarray:
    tau12, _meta = m9.pinocchio_tau_candidate_12(m6, loaded, step)
    return np.asarray(tau12, dtype=float)


def scale_to_target(tau12: np.ndarray, reference_max: float) -> float:
    ref = float(reference_max)
    if not np.isfinite(ref) or ref <= 1e-12:
        ref = float(np.max(np.abs(tau12))) if tau12.size else 1.0
    if ref <= 1e-12:
        return 0.0
    return min(1.0, TARGET_MAX_CTRL / ref)


def set_policy_ctrl(model, data, policy: str, step: int, actuator_map: List[Dict[str, Any]], repo_root: Path, contexts: Dict[str, Any]) -> Tuple[float, float, bool]:
    if model.nu:
        data.ctrl[:] = 0.0
    if policy == "zero_ctrl":
        return 0.0, 0.0, False
    if policy == "deterministic_waveform":
        tau12 = deterministic_tau12(repo_root, step)
        scale = scale_to_target(tau12, 18.0)
    elif policy == "jtf_candidate":
        tau12 = jtf_tau12(contexts["m9"], contexts["m6"], contexts["loaded"], step)
        scale = scale_to_target(tau12, contexts["jtf_reference_max"])
    else:
        raise ValueError(f"unknown policy: {policy}")

    saturated = False
    for item in actuator_map:
        aid = int(item["actuator_id"])
        order = int(item["candidate_order"])
        if aid < 0 or aid >= model.nu or order < 0 or order >= tau12.size:
            continue
        raw = float(scale * tau12[order])
        lower, upper = actuator_ctrl_limits(model, aid)
        clipped = float(np.clip(raw, lower, upper))
        if abs(clipped - raw) > 1e-12:
            saturated = True
        data.ctrl[aid] = clipped
    tau_max = float(np.max(np.abs(tau12))) if tau12.size else 0.0
    ctrl_max = float(np.max(np.abs(data.ctrl))) if model.nu else 0.0
    return tau_max, ctrl_max, saturated


def run_policy(model, policy: str, actuator_map: List[Dict[str, Any]], repo_root: Path, contexts: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    data = mujoco.MjData(model)
    initial_state(model, data)
    rows: List[Dict[str, Any]] = []
    nonfinite_steps = 0
    nonzero_ctrl_steps = 0
    saturation_steps = 0
    max_abs_ctrl = 0.0
    max_abs_tau12 = 0.0
    max_abs_qvel = 0.0
    min_base_z = float("inf")
    max_ncon = 0
    ctrl_l2_accum = 0.0

    for step in range(SMOKE_STEPS):
        tau_max, ctrl_max, saturated = set_policy_ctrl(model, data, policy, step, actuator_map, repo_root, contexts)
        max_abs_tau12 = max(max_abs_tau12, tau_max)
        max_abs_ctrl = max(max_abs_ctrl, ctrl_max)
        ctrl_l2_accum += float(np.sum(np.square(data.ctrl))) if model.nu else 0.0
        if ctrl_max > 1e-12:
            nonzero_ctrl_steps += 1
        if saturated:
            saturation_steps += 1
        mujoco.mj_step(model, data)
        if not (np.all(np.isfinite(data.qpos)) and np.all(np.isfinite(data.qvel))):
            nonfinite_steps += 1
        max_abs_qvel = max(max_abs_qvel, float(np.max(np.abs(data.qvel))) if model.nv else 0.0)
        base_z = float(data.qpos[2]) if model.nq >= 3 else 0.0
        min_base_z = min(min_base_z, base_z)
        max_ncon = max(max_ncon, int(data.ncon))
        if step % 10 == 0 or step == SMOKE_STEPS - 1:
            rows.append(
                {
                    "policy": policy,
                    "step": step,
                    "tau12_max_abs": tau_max,
                    "ctrl_max_abs": ctrl_max,
                    "qpos_finite": int(bool(np.all(np.isfinite(data.qpos)))),
                    "qvel_finite": int(bool(np.all(np.isfinite(data.qvel)))),
                    "base_z": base_z,
                    "qvel_max_abs": float(np.max(np.abs(data.qvel))) if model.nv else 0.0,
                    "ncon": int(data.ncon),
                }
            )
    summary = {
        "policy": policy,
        "steps": SMOKE_STEPS,
        "nonzero_ctrl_steps": int(nonzero_ctrl_steps),
        "nonfinite_steps": int(nonfinite_steps),
        "saturation_steps": int(saturation_steps),
        "max_abs_ctrl": float(max_abs_ctrl),
        "max_abs_tau12": float(max_abs_tau12),
        "max_abs_qvel": float(max_abs_qvel),
        "min_base_z": float(min_base_z),
        "max_ncon": int(max_ncon),
        "ctrl_l2_accum": float(ctrl_l2_accum),
    }
    return summary, rows


def run_comparison(repo_root: Path, stage15_5_path: Path, stage15_7_path: Path, stage15_9_path: Path, output_csv: Path, output_json: Path) -> Dict[str, Any]:
    if mujoco is None:
        raise RuntimeError(f"MuJoCo import failed: {MUJOCO_IMPORT_ERROR}")
    stage15_7 = load_json(stage15_7_path)
    stage15_9 = load_json(stage15_9_path)
    mjcf_model_path = resolve_repo_path(repo_root, stage15_7.get("mjcf_model_path", ""))
    if not mjcf_model_path.exists():
        raise RuntimeError(f"missing MJCF model: {mjcf_model_path}")
    model = mujoco.MjModel.from_xml_path(str(mjcf_model_path))
    actuator_map = actuator_mapping_from_stage15_7(stage15_7)
    m9, m6, loaded = prepare_jtf_context(repo_root, stage15_5_path)
    contexts = {
        "m9": m9,
        "m6": m6,
        "loaded": loaded,
        "jtf_reference_max": float(stage15_9.get("max_abs_tau12", 100.0)),
    }

    policy_summaries: List[Dict[str, Any]] = []
    all_rows: List[Dict[str, Any]] = []
    for policy in POLICIES:
        p_summary, rows = run_policy(model, policy, actuator_map, repo_root, contexts)
        policy_summaries.append(p_summary)
        all_rows.extend(rows)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["policy", "step", "tau12_max_abs", "ctrl_max_abs", "qpos_finite", "qvel_finite", "base_z", "qvel_max_abs", "ncon"],
        )
        writer.writeheader()
        writer.writerows(all_rows)

    summary = {
        "stage": "15.10",
        "name": "mujoco_torque_smoke_policy_comparison",
        "mujoco_imported": mujoco is not None,
        "mujoco_import_error": MUJOCO_IMPORT_ERROR,
        "mujoco_model_loaded": True,
        "mjcf_model_path": str(mjcf_model_path.relative_to(repo_root)) if mjcf_model_path.is_relative_to(repo_root) else str(mjcf_model_path),
        "policies": list(POLICIES),
        "steps_per_policy": SMOKE_STEPS,
        "target_max_ctrl": TARGET_MAX_CTRL,
        "audit_ctrl_limit": AUDIT_CTRL_LIMIT,
        "mapped_actuator_count": int(len(actuator_map)),
        "policy_summaries": policy_summaries,
        "jtf_candidate_used": True,
        "deterministic_waveform_used_for_comparison": True,
        "zero_ctrl_baseline_used": True,
        "stable_locomotion_claimed": False,
        "comparison_type": "short_horizon_safety_and_compatibility_only",
        "boundary": {
            "ros_publisher_used": False,
            "frozen_mixed_baseline_modified": False,
            "torque_enable_ready_claimed": False,
            "hardware_deployment_claimed": False,
            "stable_locomotion_claimed": False,
            "short_horizon_only": True,
        },
        "notes": [
            "This comparison reports safety/compatibility metrics only.",
            "It must not be interpreted as a stable locomotion benchmark.",
        ],
    }
    output_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--stage15-5-report", type=Path, default=None)
    parser.add_argument("--stage15-7-summary", type=Path, default=None)
    parser.add_argument("--stage15-9-summary", type=Path, default=None)
    parser.add_argument("--output-csv", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    log_dir = repo_root / "results/logs_sample"
    stage15_5_path = args.stage15_5_report or log_dir / "stage15_5_model_readiness_audit.json"
    stage15_7_path = args.stage15_7_summary or log_dir / "stage15_7_mujoco_candidate_compatibility_audit_summary.json"
    stage15_9_path = args.stage15_9_summary or log_dir / "stage15_9_mujoco_jtf_candidate_injection_summary.json"
    output_csv = args.output_csv or log_dir / "stage15_10_mujoco_torque_smoke_policy_comparison.csv"
    output_json = args.output_json or log_dir / "stage15_10_mujoco_torque_smoke_policy_comparison_summary.json"

    summary = run_comparison(repo_root, stage15_5_path, stage15_7_path, stage15_9_path, output_csv, output_json)
    print("stage15_10_comparison_completed: true")
    print(f"mjcf_model_path: {summary['mjcf_model_path']}")
    print(f"policies: {summary['policies']}")
    print(f"mapped_actuator_count: {summary['mapped_actuator_count']}")
    for item in summary["policy_summaries"]:
        print(f"policy={item['policy']} max_abs_ctrl={item['max_abs_ctrl']} nonfinite={item['nonfinite_steps']} saturation={item['saturation_steps']}")
    print(f"output_json: {output_json}")
    print(f"output_csv: {output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
