#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np

try:
    import pinocchio as pin
except ImportError as exc:
    raise SystemExit(
        "Missing Python dependency: pinocchio. Install/enable the project Pinocchio environment before running Stage 15.4."
    ) from exc

FOOT_NAMES = ["FR", "FL", "RR", "RL"]
AXIS_NAMES = ["fx", "fy", "fz"]
ALPHA_VALUES = [0.00, 0.02, 0.05, 0.10, 0.20]


@dataclass(frozen=True)
class PinocchioCandidateConfig:
    dt: float = 0.02
    total_steps: int = 2400
    mass: float = 12.7434
    gravity: float = 9.81
    target_vx: float = 0.30
    target_z: float = 0.30
    vx_kp: float = 2.0
    z_kp: float = 20.0
    z_kd: float = 4.0
    ax_limit: float = 1.5
    az_limit: float = 2.0
    mu: float = 0.60
    fz_min: float = 5.0
    fz_max: float = 120.0
    gait_half_period_steps: int = 200
    torque_limit: float = 23.7
    finite_difference_eps: float = 1.0e-7
    upper_leg_length: float = 0.213
    lower_leg_length: float = 0.213


@dataclass
class CandidateState:
    px: float = 0.0
    pz: float = 0.28
    vx: float = 0.0
    vz: float = 0.0


@dataclass(frozen=True)
class FootSpec:
    name: str
    knee_joint_id: int
    foot_offset_local: np.ndarray


def se3_xyz(x: float, y: float, z: float) -> pin.SE3:
    return pin.SE3(np.eye(3), np.array([x, y, z], dtype=float))


def build_synthetic_go1_like_pinocchio_model(cfg: PinocchioCandidateConfig) -> Tuple[pin.Model, List[FootSpec]]:
    """Build a small Pinocchio kinematic audit model.

    This model is not a full Go1 URDF. It is a deterministic 12-DoF kinematic model
    used to verify Pinocchio FK/Jacobian plumbing before connecting the real model.
    """
    model = pin.Model()
    inertia = pin.Inertia.Zero()
    foot_specs: List[FootSpec] = []

    # Approximate body-to-hip locations, ordered as FR, FL, RR, RL.
    hip_locations = {
        "FR": np.array([0.188, -0.047, 0.0]),
        "FL": np.array([0.188, 0.047, 0.0]),
        "RR": np.array([-0.188, -0.047, 0.0]),
        "RL": np.array([-0.188, 0.047, 0.0]),
    }

    for foot_name in FOOT_NAMES:
        hip = hip_locations[foot_name]
        hip_abd = model.addJoint(
            0,
            pin.JointModelRZ(),
            se3_xyz(float(hip[0]), float(hip[1]), float(hip[2])),
            f"{foot_name}_hip_abduction",
        )
        model.appendBodyToJoint(hip_abd, inertia, pin.SE3.Identity())

        hip_pitch = model.addJoint(
            hip_abd,
            pin.JointModelRY(),
            pin.SE3.Identity(),
            f"{foot_name}_hip_pitch",
        )
        model.appendBodyToJoint(hip_pitch, inertia, pin.SE3.Identity())

        knee_pitch = model.addJoint(
            hip_pitch,
            pin.JointModelRY(),
            se3_xyz(0.0, 0.0, -cfg.upper_leg_length),
            f"{foot_name}_knee_pitch",
        )
        model.appendBodyToJoint(knee_pitch, inertia, pin.SE3.Identity())

        foot_specs.append(
            FootSpec(
                name=foot_name,
                knee_joint_id=knee_pitch,
                foot_offset_local=np.array([0.0, 0.0, -cfg.lower_leg_length], dtype=float),
            )
        )

    return model, foot_specs


def nominal_joint_configuration(model: pin.Model) -> np.ndarray:
    q = np.zeros(model.nq, dtype=float)
    for leg in range(4):
        q[3 * leg + 0] = 0.0
        q[3 * leg + 1] = 0.80
        q[3 * leg + 2] = -1.60
    return q


def foot_positions(model: pin.Model, data: pin.Data, q: np.ndarray, foot_specs: List[FootSpec]) -> np.ndarray:
    pin.forwardKinematics(model, data, q)
    positions = []
    for spec in foot_specs:
        positions.append(np.asarray(data.oMi[spec.knee_joint_id].act(spec.foot_offset_local), dtype=float))
    return np.vstack(positions)


def finite_difference_foot_jacobians(
    model: pin.Model,
    q: np.ndarray,
    foot_specs: List[FootSpec],
    eps: float,
) -> np.ndarray:
    data = model.createData()
    base_positions = foot_positions(model, data, q, foot_specs)
    jacobians = np.zeros((4, 3, model.nv), dtype=float)

    for col in range(model.nv):
        q_perturbed = q.copy()
        q_perturbed[col] += eps
        perturbed_positions = foot_positions(model, data, q_perturbed, foot_specs)
        jacobians[:, :, col] = (perturbed_positions - base_positions) / eps

    return jacobians


def contact_schedule(step: int, cfg: PinocchioCandidateConfig) -> np.ndarray:
    phase = (step // cfg.gait_half_period_steps) % 2
    if phase == 0:
        return np.array([True, False, False, True], dtype=bool)
    return np.array([False, True, True, False], dtype=bool)


def contact_mode_name(contacts: np.ndarray) -> str:
    return "_".join(name for name, active in zip(FOOT_NAMES, contacts) if bool(active))


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


def desired_acceleration(state: CandidateState, cfg: PinocchioCandidateConfig) -> Tuple[float, float]:
    ax = clamp(cfg.vx_kp * (cfg.target_vx - state.vx), -cfg.ax_limit, cfg.ax_limit)
    az = clamp(cfg.z_kp * (cfg.target_z - state.pz) - cfg.z_kd * state.vz, -cfg.az_limit, cfg.az_limit)
    return ax, az


def solve_projected_contact_force(
    desired_ax: float,
    desired_az: float,
    contacts: np.ndarray,
    cfg: PinocchioCandidateConfig,
) -> np.ndarray:
    forces = np.zeros((4, 3), dtype=float)
    stance_count = int(np.sum(contacts))
    if stance_count <= 0:
        return forces

    desired_net_force = np.array(
        [cfg.mass * desired_ax, 0.0, cfg.mass * (desired_az + cfg.gravity)],
        dtype=float,
    )
    nominal = desired_net_force / float(stance_count)

    for foot in range(4):
        if not contacts[foot]:
            continue
        fz = clamp(float(nominal[2]), cfg.fz_min, cfg.fz_max)
        tangent_limit = cfg.mu * fz
        forces[foot, 0] = clamp(float(nominal[0]), -tangent_limit, tangent_limit)
        forces[foot, 1] = clamp(float(nominal[1]), -tangent_limit, tangent_limit)
        forces[foot, 2] = fz

    return forces


def pinocchio_jacobian_transpose_force_map(forces: np.ndarray, foot_jacobians: np.ndarray) -> np.ndarray:
    tau = np.zeros(foot_jacobians.shape[2], dtype=float)
    for foot in range(4):
        tau += foot_jacobians[foot].T @ forces[foot]
    return tau


def force_constraint_metrics(forces: np.ndarray, contacts: np.ndarray, cfg: PinocchioCandidateConfig) -> Dict[str, float]:
    swing_norms: List[float] = []
    stance_fz: List[float] = []
    friction_violations: List[float] = []
    normal_violations: List[float] = []

    for foot in range(4):
        fx, fy, fz = forces[foot]
        if contacts[foot]:
            stance_fz.append(float(fz))
            friction_violations.append(float(max(abs(fx) - cfg.mu * fz, abs(fy) - cfg.mu * fz, 0.0)))
            normal_violations.append(float(max(cfg.fz_min - fz, fz - cfg.fz_max, 0.0)))
        else:
            swing_norms.append(float(np.linalg.norm(forces[foot])))

    net_force = np.sum(forces, axis=0)
    return {
        "sum_fx": float(net_force[0]),
        "sum_fy": float(net_force[1]),
        "sum_fz": float(net_force[2]),
        "max_swing_force_norm": max(swing_norms) if swing_norms else 0.0,
        "min_stance_fz": min(stance_fz) if stance_fz else math.nan,
        "max_stance_fz": max(stance_fz) if stance_fz else math.nan,
        "max_friction_violation": max(friction_violations) if friction_violations else math.nan,
        "max_normal_force_violation": max(normal_violations) if normal_violations else math.nan,
    }


def step_state(state: CandidateState, forces: np.ndarray, cfg: PinocchioCandidateConfig) -> CandidateState:
    net_force = np.sum(forces, axis=0)
    ax = float(net_force[0] / cfg.mass)
    az = float(net_force[2] / cfg.mass - cfg.gravity)
    return CandidateState(
        px=state.px + cfg.dt * state.vx,
        pz=state.pz + cfg.dt * state.vz,
        vx=state.vx + cfg.dt * ax,
        vz=state.vz + cfg.dt * az,
    )


def alpha_key(alpha: float) -> str:
    return str(alpha).replace(".", "p")


def rollout(cfg: PinocchioCandidateConfig) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    model, foot_specs = build_synthetic_go1_like_pinocchio_model(cfg)
    q_nominal = nominal_joint_configuration(model)
    foot_jacobians = finite_difference_foot_jacobians(model, q_nominal, foot_specs, cfg.finite_difference_eps)
    foot_jacobian_norms = [float(np.linalg.norm(foot_jacobians[i])) for i in range(4)]

    state = CandidateState()
    rows: List[Dict[str, object]] = []
    prev_tau = np.zeros(model.nv, dtype=float)
    max_tau_candidate_abs = 0.0
    max_tau_candidate_delta_abs = 0.0
    per_alpha_max_scaled = {alpha: 0.0 for alpha in ALPHA_VALUES}
    per_alpha_max_delta = {alpha: 0.0 for alpha in ALPHA_VALUES}

    for step in range(cfg.total_steps):
        contacts = contact_schedule(step, cfg)
        desired_ax, desired_az = desired_acceleration(state, cfg)
        forces = solve_projected_contact_force(desired_ax, desired_az, contacts, cfg)
        tau_candidate = pinocchio_jacobian_transpose_force_map(forces, foot_jacobians)
        tau_delta = tau_candidate - prev_tau
        metrics = force_constraint_metrics(forces, contacts, cfg)

        max_tau_candidate_abs = max(max_tau_candidate_abs, float(np.max(np.abs(tau_candidate))))
        max_tau_candidate_delta_abs = max(max_tau_candidate_delta_abs, float(np.max(np.abs(tau_delta))))

        row: Dict[str, object] = {
            "step": step,
            "contact_mode": contact_mode_name(contacts),
            "px": state.px,
            "pz": state.pz,
            "vx": state.vx,
            "vz": state.vz,
            "desired_ax": desired_ax,
            "desired_az": desired_az,
            "max_tau_candidate_abs": float(np.max(np.abs(tau_candidate))),
            "max_tau_candidate_delta_abs": float(np.max(np.abs(tau_delta))),
            **metrics,
        }

        for foot_name, force in zip(FOOT_NAMES, forces):
            for axis_name, value in zip(AXIS_NAMES, force):
                row[f"force_{foot_name}_{axis_name}"] = float(value)

        for idx, value in enumerate(tau_candidate):
            row[f"tau_pinocchio_candidate_{idx:02d}"] = float(value)

        for alpha in ALPHA_VALUES:
            scaled = alpha * tau_candidate
            scaled_delta = alpha * tau_delta
            max_scaled = float(np.max(np.abs(scaled)))
            max_delta = float(np.max(np.abs(scaled_delta)))
            per_alpha_max_scaled[alpha] = max(per_alpha_max_scaled[alpha], max_scaled)
            per_alpha_max_delta[alpha] = max(per_alpha_max_delta[alpha], max_delta)
            key = alpha_key(alpha)
            row[f"max_tau_scaled_abs_alpha_{key}"] = max_scaled
            row[f"max_tau_scaled_delta_abs_alpha_{key}"] = max_delta

        rows.append(row)
        state = step_state(state, forces, cfg)
        prev_tau = tau_candidate.copy()

    max_swing_force_norm = max(float(row["max_swing_force_norm"]) for row in rows)
    max_friction_violation = max(float(row["max_friction_violation"]) for row in rows)
    max_normal_force_violation = max(float(row["max_normal_force_violation"]) for row in rows)
    min_stance_fz = min(float(row["min_stance_fz"]) for row in rows)
    max_stance_fz = max(float(row["max_stance_fz"]) for row in rows)
    final_vx = float(rows[-1]["vx"])
    final_z = float(rows[-1]["pz"])
    final_vx_error = abs(final_vx - cfg.target_vx)
    final_z_error = abs(final_z - cfg.target_z)
    max_abs_z_error = max(abs(float(row["pz"]) - cfg.target_z) for row in rows)
    all_finite = all(
        math.isfinite(float(value))
        for row in rows
        for value in row.values()
        if isinstance(value, (int, float))
    )

    alpha_results = {}
    for alpha in ALPHA_VALUES:
        key = alpha_key(alpha)
        alpha_results[key] = {
            "alpha": alpha,
            "max_tau_scaled_abs": per_alpha_max_scaled[alpha],
            "max_tau_scaled_delta_abs": per_alpha_max_delta[alpha],
            "torque_limit": cfg.torque_limit,
            "pass": per_alpha_max_scaled[alpha] <= cfg.torque_limit + 1e-9,
        }

    failed_checks: List[str] = []

    def check(condition: bool, label: str) -> None:
        if not condition:
            failed_checks.append(label)

    check(model.nv == 12, "Pinocchio audit model must expose 12 velocity DoF")
    check(len(rows) == cfg.total_steps, "rollout row count must match total_steps")
    check(all_finite, "all numeric values must be finite")
    check(max(foot_jacobian_norms) > 1.0e-6, "foot Jacobian norms must be nonzero")
    check(max_swing_force_norm <= 1.0e-9, "swing leg force must remain zero")
    check(max_friction_violation <= 1.0e-9, "friction violation must be zero")
    check(max_normal_force_violation <= 1.0e-9, "normal force violation must be zero")
    check(min_stance_fz >= cfg.fz_min - 1.0e-9, "stance fz must stay above fz_min")
    check(max_stance_fz <= cfg.fz_max + 1.0e-9, "stance fz must stay below fz_max")
    check(final_vx_error <= 0.03, "final vx error must be <= 0.03 m/s")
    check(final_z_error <= 0.02, "final z error must be <= 0.02 m")
    check(max_abs_z_error <= 0.04, "max z error must be <= 0.04 m")
    check(alpha_results[alpha_key(0.10)]["pass"], "alpha 0.10 scaled torque must stay within limit")
    check(alpha_results[alpha_key(0.20)]["pass"], "alpha 0.20 scaled torque must stay within limit")

    passing_alphas = [alpha for alpha in ALPHA_VALUES if alpha_results[alpha_key(alpha)]["pass"]]

    summary = {
        "stage": "15.4",
        "description": "Pinocchio Jacobian based contact-force-to-torque candidate rollout",
        "pass": len(failed_checks) == 0,
        "failed_checks": failed_checks,
        "simulation_only_project": True,
        "hardware_deployment_completed": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "real_robot_torque_execution_completed": False,
        "mixed_baseline_modified": False,
        "frozen_mixed_baseline_modified": False,
        "ros_publisher_used": False,
        "mujoco_torque_used": False,
        "pinocchio_imported": True,
        "pinocchio_jacobian_used": True,
        "synthetic_kinematic_model": True,
        "real_go1_urdf_used": False,
        "pinocchio_model_source": "synthetic_go1_like_12dof_kinematic_audit_model",
        "pinocchio_model_nq": model.nq,
        "pinocchio_model_nv": model.nv,
        "foot_jacobian_norms": foot_jacobian_norms,
        "total_steps": len(rows),
        "contact_modes": sorted({str(row["contact_mode"]) for row in rows}),
        "max_swing_force_norm": max_swing_force_norm,
        "max_friction_violation": max_friction_violation,
        "max_normal_force_violation": max_normal_force_violation,
        "min_stance_fz": min_stance_fz,
        "max_stance_fz": max_stance_fz,
        "max_tau_candidate_abs": max_tau_candidate_abs,
        "max_tau_candidate_delta_abs": max_tau_candidate_delta_abs,
        "final_vx": final_vx,
        "final_vx_error_abs": final_vx_error,
        "final_z": final_z,
        "final_z_error_abs": final_z_error,
        "max_abs_z_error": max_abs_z_error,
        "alpha_results": alpha_results,
        "validated_candidate_scale_max_simulation_only": max(passing_alphas) if passing_alphas else 0.0,
        "config": asdict(cfg),
    }
    return rows, summary


def write_csv(rows: Iterable[Dict[str, object]], path: Path) -> None:
    rows = list(rows)
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    cfg = PinocchioCandidateConfig()
    out_dir = Path("results/logs_sample")
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "stage15_4_pinocchio_jacobian_candidate_rollout.csv"
    summary_path = out_dir / "stage15_4_pinocchio_jacobian_candidate_rollout_summary.json"

    rows, summary = rollout(cfg)
    summary["rollout_csv"] = str(csv_path)
    summary["summary_json"] = str(summary_path)

    write_csv(rows, csv_path)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True))
    print(json.dumps(summary, indent=2, sort_keys=True))

    if not summary.get("pass", False):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
