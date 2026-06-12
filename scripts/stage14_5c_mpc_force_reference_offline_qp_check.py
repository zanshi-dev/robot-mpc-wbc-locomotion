#!/usr/bin/env python3
from pathlib import Path
import csv
import datetime as dt
import importlib.util
import json
import math
import re
from typing import Dict, List, Tuple

import numpy as np
import scipy.sparse as sp

ROOT = Path.cwd()
STAGE = "14.5C"

SUMMARY_14_5A = ROOT / "results/logs_sample/stage14_5a_mpc_wbc_integration_preflight_summary.json"
SUMMARY_14_5B = ROOT / "results/logs_sample/stage14_5b_offline_mpc_force_to_torque_candidate_summary.json"

OUT_CSV = ROOT / "results/logs_sample/stage14_5c_mpc_force_reference_offline_qp_check.csv"
OUT_SUMMARY = ROOT / "results/logs_sample/stage14_5c_mpc_force_reference_offline_qp_summary.json"
OUT_DOC = ROOT / "docs/stage14_5c_mpc_force_reference_offline_qp_check.md"

LEG_ORDER = ["FR", "FL", "RR", "RL"]
AXES = ["x", "y", "z"]
JOINT_ORDER = ["hip", "thigh", "calf"]

MU = 0.60
FZ_MIN = 5.0
FZ_MAX = 120.0
TOTAL_FZ_MAX = 240.0
TORQUE_LIMIT = 23.7
SWING_FZ_EPS = 1e-5
TRACKING_PASS_ABS_MAX = 1e-4

STANDING_Q = {
    "hip": 0.0,
    "thigh": 0.9,
    "calf": -1.8,
}


def read_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def import_osqp():
    if importlib.util.find_spec("osqp") is None:
        raise ImportError("osqp Python module not found")
    import osqp
    return osqp


def import_pinocchio():
    if importlib.util.find_spec("pinocchio") is None:
        raise ImportError("pinocchio Python module not found")
    import pinocchio as pin
    return pin


def load_csv(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


def parse_float(x) -> float:
    if x is None or x == "":
        return float("nan")
    return float(x)


def norm_col(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")


def resolve_force_columns(fieldnames: List[str]) -> Dict[Tuple[str, str], str]:
    norm_to_actual = {norm_col(name): name for name in fieldnames}
    out = {}

    for leg in LEG_ORDER:
        for axis in AXES:
            candidates = [
                f"u0_{leg}_f{axis}",
                f"{leg}_f{axis}",
                f"{leg}_force_{axis}",
                f"{leg}_contact_force_{axis}",
                f"mpc_{leg}_f{axis}",
                f"force_target_{leg}_{axis}",
            ]
            found = None
            for c in candidates:
                key = norm_col(c)
                if key in norm_to_actual:
                    found = norm_to_actual[key]
                    break
            if found is None:
                raise KeyError(f"missing force column for {leg}_{axis}; available={fieldnames}")
            out[(leg, axis)] = found

    return out


def find_urdf() -> Path:
    candidates = list(ROOT.glob("assets/go1/**/*.urdf")) + list(ROOT.glob("assets/**/*.urdf"))
    candidates = [p for p in candidates if p.is_file()]
    if not candidates:
        raise FileNotFoundError("No URDF found")
    preferred = [p for p in candidates if "go1" in p.as_posix().lower()]
    return sorted(preferred or candidates, key=lambda p: len(p.as_posix()))[0]


def build_pin_data():
    pin = import_pinocchio()
    urdf = find_urdf()
    model = pin.buildModelFromUrdf(str(urdf), pin.JointModelFreeFlyer())
    data = model.createData()

    q = pin.neutral(model)
    q[0] = 0.0
    q[1] = 0.0
    q[2] = 0.30
    q[3] = 0.0
    q[4] = 0.0
    q[5] = 0.0
    q[6] = 1.0

    joint_q_assignments = {}
    for jid, name in enumerate(model.names):
        if jid == 0:
            continue
        nl = name.lower()
        value = None
        for joint_name, joint_value in STANDING_Q.items():
            if joint_name in nl:
                value = joint_value
                break
        if value is None:
            continue
        iq = model.idx_qs[jid]
        if model.nqs[jid] == 1:
            q[iq] = value
            joint_q_assignments[name] = value

    frame_ids = {}
    frame_names = [f.name for f in model.frames]
    for leg in LEG_ORDER:
        exact = f"{leg}_foot"
        if exact in frame_names:
            frame_ids[leg] = model.getFrameId(exact)
        else:
            hits = [
                i for i, f in enumerate(model.frames)
                if leg.lower() in f.name.lower() and "foot" in f.name.lower()
            ]
            if not hits:
                raise KeyError(f"missing foot frame for {leg}")
            frame_ids[leg] = hits[0]

    actuated_velocity_indices = {}
    for leg in LEG_ORDER:
        for joint in JOINT_ORDER:
            hits = []
            for jid, name in enumerate(model.names):
                if jid == 0:
                    continue
                nl = name.lower()
                if leg.lower() in nl and joint in nl and model.nvs[jid] == 1:
                    hits.append(model.idx_vs[jid])
            if not hits:
                raise KeyError(f"missing actuated velocity index for {leg}_{joint}")
            actuated_velocity_indices[(leg, joint)] = hits[0]

    pin.forwardKinematics(model, data, q)
    pin.updateFramePlacements(model, data)

    jacobians = {}
    for leg, fid in frame_ids.items():
        j6 = pin.computeFrameJacobian(model, data, q, fid, pin.ReferenceFrame.LOCAL_WORLD_ALIGNED)
        jacobians[leg] = np.asarray(j6[:3, :], dtype=float)

    return {
        "pin_version": getattr(pin, "__version__", "unknown"),
        "urdf": urdf,
        "model": model,
        "frame_ids": frame_ids,
        "actuated_velocity_indices": actuated_velocity_indices,
        "joint_q_assignments": joint_q_assignments,
        "jacobians": jacobians,
    }


def force_index(leg: str, axis: str) -> int:
    return LEG_ORDER.index(leg) * 3 + AXES.index(axis)


def vector_from_row(row: Dict[str, str], cols: Dict[Tuple[str, str], str]) -> np.ndarray:
    f = np.zeros(12, dtype=float)
    for leg in LEG_ORDER:
        for axis in AXES:
            f[force_index(leg, axis)] = parse_float(row[cols[(leg, axis)]])
    return f


def contact_from_force(f_ref: np.ndarray) -> Dict[str, bool]:
    out = {}
    for leg in LEG_ORDER:
        fz = f_ref[force_index(leg, "z")]
        out[leg] = bool(abs(fz) > SWING_FZ_EPS)
    return out


def build_tau_map(pin_data: Dict) -> np.ndarray:
    a = np.zeros((12, 12), dtype=float)
    row = 0

    for leg in LEG_ORDER:
        j = pin_data["jacobians"][leg]
        for joint in JOINT_ORDER:
            vidx = pin_data["actuated_velocity_indices"][(leg, joint)]
            a[row, force_index(leg, "x")] = j[0, vidx]
            a[row, force_index(leg, "y")] = j[1, vidx]
            a[row, force_index(leg, "z")] = j[2, vidx]
            row += 1

    return a


def solve_force_reference_qp(osqp, f_ref: np.ndarray, stance: Dict[str, bool], tau_map: np.ndarray):
    p = sp.eye(12, format="csc")
    q = -f_ref.copy()

    rows = []
    lb = []
    ub = []

    def add(coeffs: Dict[int, float], lo: float, hi: float):
        rows.append(coeffs)
        lb.append(lo)
        ub.append(hi)

    for leg in LEG_ORDER:
        ix = force_index(leg, "x")
        iy = force_index(leg, "y")
        iz = force_index(leg, "z")

        if stance[leg]:
            add({iz: 1.0}, FZ_MIN, FZ_MAX)
            add({ix: 1.0, iz: -MU}, -np.inf, 0.0)
            add({ix: -1.0, iz: -MU}, -np.inf, 0.0)
            add({iy: 1.0, iz: -MU}, -np.inf, 0.0)
            add({iy: -1.0, iz: -MU}, -np.inf, 0.0)
        else:
            add({ix: 1.0}, 0.0, 0.0)
            add({iy: 1.0}, 0.0, 0.0)
            add({iz: 1.0}, 0.0, 0.0)

    add({force_index(leg, "z"): 1.0 for leg in LEG_ORDER}, 0.0, TOTAL_FZ_MAX)

    for tau_row in tau_map:
        coeff = {i: float(v) for i, v in enumerate(tau_row) if abs(v) > 1e-14}
        add(coeff, -TORQUE_LIMIT, TORQUE_LIMIT)

    data = []
    row_ind = []
    col_ind = []

    for r, coeffs in enumerate(rows):
        for c, v in coeffs.items():
            row_ind.append(r)
            col_ind.append(c)
            data.append(v)

    a = sp.csc_matrix((data, (row_ind, col_ind)), shape=(len(rows), 12))
    l = np.asarray(lb, dtype=float)
    u = np.asarray(ub, dtype=float)

    solver = osqp.OSQP()
    solver.setup(
        P=p,
        q=q,
        A=a,
        l=l,
        u=u,
        verbose=False,
        polish=True,
        eps_abs=1e-8,
        eps_rel=1e-8,
        max_iter=10000,
    )
    return solver.solve()


def main() -> int:
    ROOT.joinpath("results/logs_sample").mkdir(parents=True, exist_ok=True)
    ROOT.joinpath("docs").mkdir(parents=True, exist_ok=True)

    failed_checks = []

    if not SUMMARY_14_5A.exists():
        failed_checks.append("missing_stage14_5a_summary")
        s145a = {}
    else:
        s145a = read_json(SUMMARY_14_5A)
        if s145a.get("pass") is not True:
            failed_checks.append("stage14_5a_not_passed")

    if not SUMMARY_14_5B.exists():
        failed_checks.append("missing_stage14_5b_summary")
        s145b = {}
    else:
        s145b = read_json(SUMMARY_14_5B)
        if s145b.get("pass") is not True:
            failed_checks.append("stage14_5b_not_passed")

    osqp_error = ""
    pin_error = ""
    rollout_error = ""

    try:
        osqp = import_osqp()
    except Exception as exc:
        osqp = None
        osqp_error = str(exc)
        failed_checks.append("osqp_unavailable")

    try:
        pin_data = build_pin_data()
        tau_map = build_tau_map(pin_data)
    except Exception as exc:
        pin_data = {}
        tau_map = None
        pin_error = str(exc)
        failed_checks.append("pinocchio_or_tau_map_unavailable")

    rows = []
    force_cols = {}
    rollout_csv = None

    try:
        rollout_csv_value = s145b.get("stage14_4_rollout_csv")
        if not rollout_csv_value:
            raise FileNotFoundError("stage14_5b summary has no stage14_4_rollout_csv")
        rollout_csv = ROOT / rollout_csv_value
        fieldnames, rows = load_csv(rollout_csv)
        force_cols = resolve_force_columns(fieldnames)
    except Exception as exc:
        rollout_error = str(exc)
        failed_checks.append("stage14_4_force_rollout_unavailable")

    out_rows = []
    qp_status_counts = {}
    max_tracking_error_inf = 0.0
    max_tau_abs = 0.0
    max_friction_violation = 0.0
    max_swing_force_norm = 0.0
    nonfinite_solution_count = 0
    torque_violation_count = 0
    qp_failure_count = 0
    contact_mismatch_count = 0

    if not failed_checks:
        for i, row in enumerate(rows):
            f_ref = vector_from_row(row, force_cols)
            stance = contact_from_force(f_ref)

            res = solve_force_reference_qp(osqp, f_ref, stance, tau_map)
            status = str(res.info.status)
            qp_status_counts[status] = qp_status_counts.get(status, 0) + 1

            if status.lower() not in {"solved", "solved inaccurate"} or res.x is None:
                qp_failure_count += 1
                f_sol = np.full(12, np.nan)
            else:
                f_sol = np.asarray(res.x, dtype=float)

            if not np.all(np.isfinite(f_sol)):
                nonfinite_solution_count += 1

            err_inf = float(np.max(np.abs(f_sol - f_ref))) if np.all(np.isfinite(f_sol)) else float("inf")
            max_tracking_error_inf = max(max_tracking_error_inf, err_inf)

            tau = tau_map @ f_sol if np.all(np.isfinite(f_sol)) else np.full(12, np.nan)
            tau_abs = float(np.max(np.abs(tau))) if np.all(np.isfinite(tau)) else float("inf")
            max_tau_abs = max(max_tau_abs, tau_abs)

            if tau_abs > TORQUE_LIMIT + 1e-6:
                torque_violation_count += 1

            swing_force_norms = []
            friction_violations = []

            for leg in LEG_ORDER:
                fx = f_sol[force_index(leg, "x")]
                fy = f_sol[force_index(leg, "y")]
                fz = f_sol[force_index(leg, "z")]

                if stance[leg]:
                    friction_violations.append(max(0.0, abs(fx) - MU * fz))
                    friction_violations.append(max(0.0, abs(fy) - MU * fz))
                    if fz <= SWING_FZ_EPS:
                        contact_mismatch_count += 1
                else:
                    swing_force_norms.append(float(np.linalg.norm([fx, fy, fz])))
                    if abs(fz) > SWING_FZ_EPS:
                        contact_mismatch_count += 1

            row_max_friction_violation = max(friction_violations) if friction_violations else 0.0
            row_max_swing_force_norm = max(swing_force_norms) if swing_force_norms else 0.0
            max_friction_violation = max(max_friction_violation, row_max_friction_violation)
            max_swing_force_norm = max(max_swing_force_norm, row_max_swing_force_norm)

            out = {
                "step": i,
                "source_step": row.get("step", i),
                "contact_mode": row.get("contact_mode", ""),
                "qp_status": status,
                "tracking_error_inf": f"{err_inf:.12g}",
                "tau_abs_max": f"{tau_abs:.12g}",
                "max_friction_violation": f"{row_max_friction_violation:.12g}",
                "max_swing_force_norm": f"{row_max_swing_force_norm:.12g}",
            }

            for leg in LEG_ORDER:
                for axis in AXES:
                    idx = force_index(leg, axis)
                    out[f"{leg}_f_ref_{axis}"] = f"{f_ref[idx]:.12g}"
                    out[f"{leg}_f_qp_{axis}"] = f"{f_sol[idx]:.12g}"

            for leg in LEG_ORDER:
                out[f"{leg}_stance"] = str(stance[leg])

            out_rows.append(out)

        with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
            writer.writeheader()
            writer.writerows(out_rows)

    if qp_failure_count:
        failed_checks.append("qp_failure_detected")
    if nonfinite_solution_count:
        failed_checks.append("nonfinite_qp_solution_detected")
    if torque_violation_count:
        failed_checks.append("torque_bound_violation_detected")
    if contact_mismatch_count:
        failed_checks.append("contact_mismatch_detected")
    if max_tracking_error_inf > TRACKING_PASS_ABS_MAX:
        failed_checks.append("force_reference_tracking_error_too_large")
    if max_friction_violation > 1e-6:
        failed_checks.append("friction_violation_detected")
    if max_swing_force_norm > 1e-6:
        failed_checks.append("swing_force_nonzero_detected")
    if not out_rows and "stage14_4_force_rollout_unavailable" not in failed_checks:
        failed_checks.append("no_qp_rows_generated")

    summary = {
        "stage": STAGE,
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "pass": len(failed_checks) == 0,
        "failed_checks": failed_checks,
        "simulation_only_project": True,
        "hardware_deployment_completed": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "control_law_changed": False,
        "mixed_baseline_modified": False,
        "mujoco_closed_loop_used": False,
        "mujoco_torque_used": False,
        "ros_publisher_used": False,
        "wbc_qp_reference_offline_check": True,
        "wbc_qp_replaces_baseline": False,
        "not_real_robot_torque_command": True,
        "mpc_layer_output": "contact_force_target",
        "offline_qp_output": "bounded_contact_force_solution_tracking_mpc_reference",
        "stage14_5a_pass": s145a.get("pass"),
        "stage14_5b_pass": s145b.get("pass"),
        "stage14_4_rollout_csv": str(rollout_csv.relative_to(ROOT)) if rollout_csv else None,
        "stage14_5b_summary": str(SUMMARY_14_5B.relative_to(ROOT)) if SUMMARY_14_5B.exists() else None,
        "pinocchio_version": pin_data.get("pin_version"),
        "pinocchio_error": pin_error,
        "osqp_error": osqp_error,
        "rollout_error": rollout_error,
        "row_count": len(rows),
        "qp_row_count": len(out_rows),
        "qp_status_counts": qp_status_counts,
        "qp_failure_count": qp_failure_count,
        "nonfinite_solution_count": nonfinite_solution_count,
        "contact_mismatch_count": contact_mismatch_count,
        "torque_bound_abs": TORQUE_LIMIT,
        "torque_violation_count": torque_violation_count,
        "max_tau_abs": max_tau_abs,
        "max_tracking_error_inf": max_tracking_error_inf,
        "tracking_pass_abs_max": TRACKING_PASS_ABS_MAX,
        "max_friction_violation": max_friction_violation,
        "max_swing_force_norm": max_swing_force_norm,
        "mu": MU,
        "fz_min": FZ_MIN,
        "fz_max": FZ_MAX,
        "total_fz_max": TOTAL_FZ_MAX,
        "force_columns": {f"{k[0]}_f{k[1]}": v for k, v in force_cols.items()},
        "frame_ids": pin_data.get("frame_ids", {}),
        "actuated_velocity_indices": {
            f"{k[0]}_{k[1]}": v for k, v in pin_data.get("actuated_velocity_indices", {}).items()
        },
        "urdf_path": str(pin_data.get("urdf").relative_to(ROOT)) if pin_data.get("urdf") else None,
        "output_csv": str(OUT_CSV.relative_to(ROOT)) if OUT_CSV.exists() else None,
        "output_summary": str(OUT_SUMMARY.relative_to(ROOT)),
        "output_doc": str(OUT_DOC.relative_to(ROOT)),
        "notes": [
            "Offline QP reference check only.",
            "MPC contact-force target is used as a QP reference.",
            "The QP solution is not inserted into MuJoCo closed-loop control.",
            "No ROS torque publisher is used.",
            "Frozen mixed baseline is not modified.",
        ],
    }

    write_json(OUT_SUMMARY, summary)

    doc_lines = [
        "# Stage 14.5C MPC Force Target as Offline WBC/QP Reference Check",
        "",
        "Scope: simulation-only offline reference QP check.",
        "",
        "This stage uses the Stage 14.4 MPC contact-force target as an offline QP reference and checks whether the reference can be represented as a bounded contact-force solution under contact, friction, vertical force, total vertical force, and nominal `J^T f` torque bounds.",
        "",
        "It does not run MuJoCo closed-loop simulation, does not replace the frozen mixed baseline, does not use a ROS torque publisher, and does not produce real robot torque commands.",
        "",
        "## Evidence",
        "",
        f"- Summary JSON: `{OUT_SUMMARY.relative_to(ROOT)}`",
        f"- QP CSV: `{OUT_CSV.relative_to(ROOT) if OUT_CSV.exists() else 'not generated'}`",
        "",
        "## Result",
        "",
        f"- pass: {summary['pass']}",
        f"- failed_checks: {summary['failed_checks']}",
        f"- row_count: {summary['row_count']}",
        f"- qp_row_count: {summary['qp_row_count']}",
        f"- qp_status_counts: {summary['qp_status_counts']}",
        f"- max_tracking_error_inf: {summary['max_tracking_error_inf']}",
        f"- max_tau_abs: {summary['max_tau_abs']}",
        f"- torque_bound_abs: {summary['torque_bound_abs']}",
        f"- torque_violation_count: {summary['torque_violation_count']}",
        f"- max_friction_violation: {summary['max_friction_violation']}",
        f"- max_swing_force_norm: {summary['max_swing_force_norm']}",
        "",
        "## Safety flags",
        "",
        f"- simulation_only_project: {summary['simulation_only_project']}",
        f"- hardware_deployment_completed: {summary['hardware_deployment_completed']}",
        f"- torque_enable_ready: {summary['torque_enable_ready']}",
        f"- torque_publisher_enabled: {summary['torque_publisher_enabled']}",
        f"- control_law_changed: {summary['control_law_changed']}",
        f"- mixed_baseline_modified: {summary['mixed_baseline_modified']}",
        f"- mujoco_closed_loop_used: {summary['mujoco_closed_loop_used']}",
        f"- mujoco_torque_used: {summary['mujoco_torque_used']}",
        f"- ros_publisher_used: {summary['ros_publisher_used']}",
        f"- wbc_qp_replaces_baseline: {summary['wbc_qp_replaces_baseline']}",
        "",
        "## Boundary",
        "",
        "This is offline WBC/QP-reference compatibility evidence only. It is not MPC-assisted closed-loop locomotion evidence and not hardware-readiness evidence.",
        "",
    ]
    OUT_DOC.write_text("\n".join(doc_lines), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
