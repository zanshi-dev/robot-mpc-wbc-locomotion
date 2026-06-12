#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import scipy.sparse as sp

try:
    import osqp
except ImportError as exc:
    raise SystemExit(
        "Missing Python dependency: osqp. Install/enable the project Python environment before running Stage 14.4A."
    ) from exc


@dataclass(frozen=True)
class MpcConfig:
    dt: float = 0.02
    horizon: int = 20
    rollout_steps: int = 100
    mass: float = 12.0
    z_ref: float = 0.30
    vx_ref: float = 0.35
    vy_ref: float = 0.0
    fz_min: float = 5.0
    fz_max: float = 120.0
    total_fz_max: float = 240.0
    mu: float = 0.60
    gait_half_period_steps: int = 10
    q_z: float = 700.0
    q_vx: float = 120.0
    q_vy: float = 80.0
    q_vz: float = 40.0
    r_force: float = 2.0e-5
    r_smooth: float = 2.0e-4
    solver_eps_abs: float = 1.0e-7
    solver_eps_rel: float = 1.0e-7
    solver_max_iter: int = 10000


FOOT_NAMES = ["FR", "FL", "RR", "RL"]
AXIS_NAMES = ["fx", "fy", "fz"]
NX = 6
NU = 12
OK_STATUSES = {"solved", "solved inaccurate"}


def contact_schedule(step: int, cfg: MpcConfig) -> np.ndarray:
    phase = (step // cfg.gait_half_period_steps) % 2
    if phase == 0:
        return np.array([True, False, False, True], dtype=bool)
    return np.array([False, True, True, False], dtype=bool)


def contact_mode_name(contacts: np.ndarray) -> str:
    stance = [name for name, active in zip(FOOT_NAMES, contacts) if active]
    return "_".join(stance)


def x_index(k: int) -> int:
    return k * NX


def u_index(k: int, horizon: int) -> int:
    return (horizon + 1) * NX + k * NU


def nominal_force_reference(cfg: MpcConfig, contacts: np.ndarray) -> np.ndarray:
    u_ref = np.zeros(NU)
    stance_count = int(np.sum(contacts))
    if stance_count <= 0:
        return u_ref
    nominal_fz = cfg.mass * 9.81 / stance_count
    for foot in range(4):
        if contacts[foot]:
            u_ref[3 * foot + 2] = nominal_fz
    return u_ref


def add_sparse_row(
    rows: List[int],
    cols: List[int],
    data: List[float],
    lower: List[float],
    upper: List[float],
    row_id: int,
    terms: List[Tuple[int, float]],
    lb: float,
    ub: float,
) -> int:
    for col, val in terms:
        if abs(val) > 0.0:
            rows.append(row_id)
            cols.append(col)
            data.append(float(val))
    lower.append(float(lb))
    upper.append(float(ub))
    return row_id + 1


def build_qp(x0: np.ndarray, prev_u: np.ndarray, rollout_step: int, cfg: MpcConfig):
    n_x_vars = (cfg.horizon + 1) * NX
    n_u_vars = cfg.horizon * NU
    n_vars = n_x_vars + n_u_vars

    P = sp.lil_matrix((n_vars, n_vars), dtype=float)
    q = np.zeros(n_vars)

    x_ref = np.array([0.0, 0.0, cfg.z_ref, cfg.vx_ref, cfg.vy_ref, 0.0])
    q_diag = np.array([0.0, 0.0, cfg.q_z, cfg.q_vx, cfg.q_vy, cfg.q_vz])

    for k in range(1, cfg.horizon + 1):
        factor = 5.0 if k == cfg.horizon else 1.0
        base = x_index(k)
        for i, weight in enumerate(q_diag):
            if weight > 0.0:
                P[base + i, base + i] += factor * weight
                q[base + i] -= factor * weight * x_ref[i]

    for k in range(cfg.horizon):
        base = u_index(k, cfg.horizon)
        contacts = contact_schedule(rollout_step + k, cfg)
        u_ref = nominal_force_reference(cfg, contacts)
        for j in range(NU):
            P[base + j, base + j] += cfg.r_force
            q[base + j] -= cfg.r_force * u_ref[j]

    for k in range(cfg.horizon):
        base = u_index(k, cfg.horizon)
        if k == 0:
            for j in range(NU):
                P[base + j, base + j] += cfg.r_smooth
                q[base + j] -= cfg.r_smooth * prev_u[j]
        else:
            prev_base = u_index(k - 1, cfg.horizon)
            for j in range(NU):
                P[base + j, base + j] += cfg.r_smooth
                P[prev_base + j, prev_base + j] += cfg.r_smooth
                P[base + j, prev_base + j] -= cfg.r_smooth
                P[prev_base + j, base + j] -= cfg.r_smooth

    P.setdiag(P.diagonal() + 1.0e-9)

    rows: List[int] = []
    cols: List[int] = []
    data: List[float] = []
    lower: List[float] = []
    upper: List[float] = []
    row_id = 0

    for i in range(NX):
        row_id = add_sparse_row(
            rows, cols, data, lower, upper, row_id,
            [(x_index(0) + i, 1.0)],
            x0[i], x0[i]
        )

    A_d = np.eye(NX)
    A_d[0, 3] = cfg.dt
    A_d[1, 4] = cfg.dt
    A_d[2, 5] = cfg.dt

    B_d = np.zeros((NX, NU))
    for foot in range(4):
        for dim in range(3):
            B_d[3 + dim, 3 * foot + dim] = cfg.dt / cfg.mass

    gravity = np.array([0.0, 0.0, -9.81])
    c_d = np.array([0.0, 0.0, 0.0, cfg.dt * gravity[0], cfg.dt * gravity[1], cfg.dt * gravity[2]])

    for k in range(cfg.horizon):
        for r in range(NX):
            terms: List[Tuple[int, float]] = [(x_index(k + 1) + r, 1.0)]

            for j in range(NX):
                if abs(A_d[r, j]) > 0.0:
                    terms.append((x_index(k) + j, -A_d[r, j]))

            for j in range(NU):
                if abs(B_d[r, j]) > 0.0:
                    terms.append((u_index(k, cfg.horizon) + j, -B_d[r, j]))

            row_id = add_sparse_row(
                rows, cols, data, lower, upper, row_id,
                terms, c_d[r], c_d[r]
            )

    for k in range(cfg.horizon):
        contacts = contact_schedule(rollout_step + k, cfg)
        u_base = u_index(k, cfg.horizon)

        for foot in range(4):
            fx = u_base + 3 * foot + 0
            fy = u_base + 3 * foot + 1
            fz = u_base + 3 * foot + 2

            if not contacts[foot]:
                row_id = add_sparse_row(rows, cols, data, lower, upper, row_id, [(fx, 1.0)], 0.0, 0.0)
                row_id = add_sparse_row(rows, cols, data, lower, upper, row_id, [(fy, 1.0)], 0.0, 0.0)
                row_id = add_sparse_row(rows, cols, data, lower, upper, row_id, [(fz, 1.0)], 0.0, 0.0)
            else:
                row_id = add_sparse_row(rows, cols, data, lower, upper, row_id, [(fz, 1.0)], cfg.fz_min, cfg.fz_max)
                row_id = add_sparse_row(rows, cols, data, lower, upper, row_id, [(fx, 1.0), (fz, -cfg.mu)], -np.inf, 0.0)
                row_id = add_sparse_row(rows, cols, data, lower, upper, row_id, [(fx, -1.0), (fz, -cfg.mu)], -np.inf, 0.0)
                row_id = add_sparse_row(rows, cols, data, lower, upper, row_id, [(fy, 1.0), (fz, -cfg.mu)], -np.inf, 0.0)
                row_id = add_sparse_row(rows, cols, data, lower, upper, row_id, [(fy, -1.0), (fz, -cfg.mu)], -np.inf, 0.0)

        total_fz_terms = [(u_base + 3 * foot + 2, 1.0) for foot in range(4)]
        row_id = add_sparse_row(
            rows, cols, data, lower, upper, row_id,
            total_fz_terms, -np.inf, cfg.total_fz_max
        )

    A_cons = sp.coo_matrix((data, (rows, cols)), shape=(row_id, n_vars)).tocsc()

    return P.tocsc(), q, A_cons, np.array(lower), np.array(upper)


def solve_mpc(x0: np.ndarray, prev_u: np.ndarray, rollout_step: int, cfg: MpcConfig):
    P, q, A, lower, upper = build_qp(x0, prev_u, rollout_step, cfg)

    solver = osqp.OSQP()
    solver.setup(
        P=P,
        q=q,
        A=A,
        l=lower,
        u=upper,
        verbose=False,
        polish=True,
        eps_abs=cfg.solver_eps_abs,
        eps_rel=cfg.solver_eps_rel,
        max_iter=cfg.solver_max_iter,
    )
    result = solver.solve()
    status = str(result.info.status).lower()
    solve_time = float(getattr(result.info, "run_time", math.nan))

    if result.x is None or status not in OK_STATUSES:
        return status, solve_time, np.full(NU, np.nan)

    u0 = np.asarray(result.x[u_index(0, cfg.horizon):u_index(0, cfg.horizon) + NU], dtype=float)
    return status, solve_time, u0


def force_metrics(u: np.ndarray, contacts: np.ndarray, cfg: MpcConfig) -> Dict[str, float]:
    forces = u.reshape(4, 3)
    swing_norms = []
    stance_fz = []
    friction_violations = []

    for foot in range(4):
        fx, fy, fz = forces[foot]
        if contacts[foot]:
            stance_fz.append(fz)
            friction_violations.append(max(abs(fx) - cfg.mu * fz, abs(fy) - cfg.mu * fz, 0.0))
        else:
            swing_norms.append(float(np.linalg.norm(forces[foot])))

    sum_force = np.sum(forces, axis=0)
    return {
        "sum_fx": float(sum_force[0]),
        "sum_fy": float(sum_force[1]),
        "sum_fz": float(sum_force[2]),
        "max_swing_force_norm": float(max(swing_norms) if swing_norms else 0.0),
        "min_stance_fz": float(min(stance_fz) if stance_fz else math.nan),
        "max_stance_fz": float(max(stance_fz) if stance_fz else math.nan),
        "max_friction_violation": float(max(friction_violations) if friction_violations else math.nan),
        "total_fz_upper_violation": float(max(sum_force[2] - cfg.total_fz_max, 0.0)),
    }


def step_dynamics(x: np.ndarray, u: np.ndarray, cfg: MpcConfig) -> np.ndarray:
    forces = u.reshape(4, 3)
    sum_force = np.sum(forces, axis=0)
    gravity = np.array([0.0, 0.0, -9.81])

    x_next = np.zeros(NX)
    x_next[0:3] = x[0:3] + cfg.dt * x[3:6]
    x_next[3:6] = x[3:6] + cfg.dt * (sum_force / cfg.mass + gravity)
    return x_next


def make_summary(logs: List[Dict[str, float]], cfg: MpcConfig, csv_path: Path, summary_path: Path) -> Dict[str, object]:
    failed_checks: List[str] = []

    def check(condition: bool, label: str) -> None:
        if not condition:
            failed_checks.append(label)

    if not logs:
        failed_checks.append("no rollout logs generated")
        return {
            "stage": "14.4A",
            "pass": False,
            "failed_checks": failed_checks,
            "simulation_only_project": True,
            "hardware_deployment_completed": False,
            "torque_enable_ready": False,
            "torque_publisher_enabled": False,
            "control_law_changed": False,
            "rollout_csv": str(csv_path),
            "summary_json": str(summary_path),
            "config": asdict(cfg),
        }

    statuses = [str(row["status"]).lower() for row in logs]
    status_counts = {status: statuses.count(status) for status in sorted(set(statuses))}

    force_keys = [f"u0_{foot}_{axis}" for foot in FOOT_NAMES for axis in AXIS_NAMES]
    numeric_keys = ["px", "py", "pz", "vx", "vy", "vz", "sum_fx", "sum_fy", "sum_fz"] + force_keys
    all_finite = all(math.isfinite(float(row[key])) for row in logs for key in numeric_keys)

    max_swing = max(float(row["max_swing_force_norm"]) for row in logs)
    min_stance_fz = min(float(row["min_stance_fz"]) for row in logs)
    max_stance_fz = max(float(row["max_stance_fz"]) for row in logs)
    max_friction = max(float(row["max_friction_violation"]) for row in logs)
    max_total_fz_violation = max(float(row["total_fz_upper_violation"]) for row in logs)
    max_force_delta_norm = max(float(row["force_delta_norm"]) for row in logs)

    final = logs[-1]
    initial_vx_error = abs(float(logs[0]["vx"]) - cfg.vx_ref)
    final_vx_error = abs(float(final["vx"]) - cfg.vx_ref)
    final_vy_abs = abs(float(final["vy"]))
    final_z_error = abs(float(final["pz"]) - cfg.z_ref)
    max_abs_vy = max(abs(float(row["vy"])) for row in logs)
    max_abs_z_error = max(abs(float(row["pz"]) - cfg.z_ref) for row in logs)

    last_window = logs[-min(20, len(logs)):]
    mean_abs_vx_error_last_window = float(
        np.mean([abs(float(row["vx"]) - cfg.vx_ref) for row in last_window])
    )

    solve_times = [float(row["solve_time"]) for row in logs if math.isfinite(float(row["solve_time"]))]
    mean_solve_time = float(np.mean(solve_times)) if solve_times else math.nan
    max_solve_time = float(np.max(solve_times)) if solve_times else math.nan

    check(all(status in OK_STATUSES for status in statuses), "OSQP status must be solved or solved inaccurate")
    check(all_finite, "all states and forces must be finite")
    check(max_swing <= 1.0e-6, "swing leg force norm must be <= 1e-6")
    check(min_stance_fz >= cfg.fz_min - 1.0e-5, "stance fz must stay above fz_min")
    check(max_stance_fz <= cfg.fz_max + 1.0e-5, "stance fz must stay below fz_max")
    check(max_friction <= 1.0e-5, "friction pyramid violation must be near zero")
    check(max_total_fz_violation <= 1.0e-5, "total fz upper violation must be near zero")
    check(final_vx_error < initial_vx_error, "vx must move closer to vx_ref")
    check(final_vx_error <= 0.08, "final vx tracking error must be <= 0.08 m/s")
    check(final_vy_abs <= 0.03, "final |vy| must be <= 0.03 m/s")
    check(final_z_error <= 0.03, "final z error must be <= 0.03 m")

    return {
        "stage": "14.4A",
        "description": "standalone simplified 3D base velocity tracking receding-horizon MPC demo",
        "pass": len(failed_checks) == 0,
        "failed_checks": failed_checks,
        "simulation_only_project": True,
        "hardware_deployment_completed": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "control_law_changed": False,
        "mixed_baseline_modified": False,
        "ros_publisher_used": False,
        "mujoco_torque_used": False,
        "total_steps": len(logs),
        "horizon": cfg.horizon,
        "dt": cfg.dt,
        "contact_modes": sorted(set(str(row["contact_mode"]) for row in logs)),
        "status_counts": status_counts,
        "max_swing_force_norm": max_swing,
        "min_stance_fz": min_stance_fz,
        "max_stance_fz": max_stance_fz,
        "max_friction_violation": max_friction,
        "max_total_fz_violation": max_total_fz_violation,
        "max_force_delta_norm": max_force_delta_norm,
        "initial_vx_error_abs": initial_vx_error,
        "final_vx": float(final["vx"]),
        "final_vx_error_abs": final_vx_error,
        "mean_abs_vx_error_last_20": mean_abs_vx_error_last_window,
        "final_vy": float(final["vy"]),
        "max_abs_vy": max_abs_vy,
        "final_z": float(final["pz"]),
        "final_z_error_abs": final_z_error,
        "max_abs_z_error": max_abs_z_error,
        "mean_solve_time_s": mean_solve_time,
        "max_solve_time_s": max_solve_time,
        "all_force_and_state_values_finite": all_finite,
        "rollout_csv": str(csv_path),
        "summary_json": str(summary_path),
        "config": asdict(cfg),
    }


def write_csv(logs: List[Dict[str, float]], csv_path: Path) -> None:
    if not logs:
        return
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(logs[0].keys()))
        writer.writeheader()
        writer.writerows(logs)


def main() -> None:
    cfg = MpcConfig()

    out_dir = Path("results/logs_sample")
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "stage14_4_base_velocity_tracking_mpc_rollout.csv"
    summary_path = out_dir / "stage14_4_base_velocity_tracking_mpc_summary.json"

    x = np.array([0.0, 0.0, 0.28, 0.0, 0.0, 0.0], dtype=float)
    prev_u = np.zeros(NU)
    logs: List[Dict[str, float]] = []

    force_field_names = [f"u0_{foot}_{axis}" for foot in FOOT_NAMES for axis in AXIS_NAMES]

    for step in range(cfg.rollout_steps):
        contacts = contact_schedule(step, cfg)
        status, solve_time, u0 = solve_mpc(x, prev_u, step, cfg)

        row: Dict[str, float] = {
            "step": step,
            "contact_mode": contact_mode_name(contacts),
            "px": float(x[0]),
            "py": float(x[1]),
            "pz": float(x[2]),
            "vx": float(x[3]),
            "vy": float(x[4]),
            "vz": float(x[5]),
            "status": status,
            "solve_time": solve_time,
        }

        for name, value in zip(force_field_names, u0):
            row[name] = float(value)

        if np.all(np.isfinite(u0)):
            metrics = force_metrics(u0, contacts, cfg)
            row.update(metrics)
            row["force_delta_norm"] = float(np.linalg.norm(u0 - prev_u))
            logs.append(row)

            x = step_dynamics(x, u0, cfg)
            prev_u = u0.copy()
        else:
            for key in [
                "sum_fx",
                "sum_fy",
                "sum_fz",
                "max_swing_force_norm",
                "min_stance_fz",
                "max_stance_fz",
                "max_friction_violation",
                "total_fz_upper_violation",
                "force_delta_norm",
            ]:
                row[key] = math.nan
            logs.append(row)
            break

    write_csv(logs, csv_path)
    summary = make_summary(logs, cfg, csv_path, summary_path)

    with summary_path.open("w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
