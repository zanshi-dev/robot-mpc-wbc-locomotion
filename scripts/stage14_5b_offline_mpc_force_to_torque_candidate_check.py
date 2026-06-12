#!/usr/bin/env python3
from pathlib import Path
import csv
import datetime as dt
import importlib.util
import json
import math
import re
import subprocess
import sys
from typing import Dict, List, Tuple

import numpy as np

ROOT = Path.cwd()
STAGE = "14.5B"

SUMMARY_14_5A = ROOT / "results/logs_sample/stage14_5a_mpc_wbc_integration_preflight_summary.json"
STAGE14_4_SCRIPT = ROOT / "scripts/stage14_4_base_velocity_tracking_mpc_demo.py"

OUT_CSV = ROOT / "results/logs_sample/stage14_5b_offline_mpc_force_to_torque_candidates.csv"
OUT_SUMMARY = ROOT / "results/logs_sample/stage14_5b_offline_mpc_force_to_torque_candidate_summary.json"
OUT_DOC = ROOT / "docs/stage14_5b_offline_mpc_force_to_torque_candidate_check.md"

LEG_ORDER = ["FR", "FL", "RR", "RL"]
JOINT_ORDER = ["hip", "thigh", "calf"]
TORQUE_LIMIT = 23.7
STANDING_Q = {
    "hip": 0.0,
    "thigh": 0.9,
    "calf": -1.8,
}

FORCE_COLUMN_CANDIDATES = []
for leg in LEG_ORDER:
    for axis in ["x", "y", "z"]:
        FORCE_COLUMN_CANDIDATES.append((leg, axis, [
            f"{leg}_f{axis}",
            f"{leg}_force_{axis}",
            f"{leg}_contact_force_{axis}",
            f"{leg}_{axis}",
            f"u_{leg}_f{axis}",
            f"u_{leg}_{axis}",
            f"{leg}_force_{axis.upper()}",
            f"{leg}_F{axis}",
            f"{leg}_F{axis.upper()}",
        ]))


def run(cmd: List[str]) -> Tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def read_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _csv_header(path: Path) -> List[str]:
    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            return next(reader, [])
    except Exception:
        return []


def _write_force_source_inventory(records: List[Dict], selected: str = "") -> None:
    inv_path = ROOT / "results/logs_sample/stage14_5b_force_rollout_source_inventory.json"
    inv_path.parent.mkdir(parents=True, exist_ok=True)
    inv_path.write_text(
        json.dumps(
            {
                "stage": STAGE,
                "purpose": "Stage 14.5B force-rollout CSV source selection inventory",
                "selected": selected,
                "records": records,
            },
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )


def _candidate_stage14_4_csv_paths() -> List[Path]:
    out = []

    summary_path = ROOT / "results/logs_sample/stage14_4_base_velocity_tracking_mpc_summary.json"
    if summary_path.exists():
        try:
            data = read_json(summary_path)
            for key in [
                "rollout_csv",
                "rollout_csv_path",
                "csv_path",
                "output_csv",
                "rollout_path",
                "output_rollout_csv",
            ]:
                value = data.get(key)
                if isinstance(value, str):
                    q = ROOT / value
                    if q.exists() and q.suffix.lower() == ".csv":
                        out.append(q)
        except Exception:
            pass

    patterns = [
        "results/logs_sample/*stage14_4*base_velocity*mpc*rollout*.csv",
        "results/logs_sample/*stage14_4*mpc*rollout*.csv",
        "results/logs_sample/*stage14_4*base_velocity*mpc*.csv",
        "results/logs_sample/*stage14_4*.csv",
        "results/logs_sample/*mpc*rollout*.csv",
    ]

    for pattern in patterns:
        out.extend(ROOT.glob(pattern))

    unique = []
    seen = set()
    for q in out:
        if not q.exists() or q.suffix.lower() != ".csv":
            continue
        rel = q.relative_to(ROOT).as_posix()
        if rel in seen:
            continue
        seen.add(rel)
        unique.append(q)

    return sorted(unique, key=lambda q: q.stat().st_mtime, reverse=True)


def find_stage14_4_rollout_csv() -> Path:
    def select_force_csv(paths: List[Path]) -> Path:
        records = []
        selected = ""

        for q in paths:
            header = _csv_header(q)
            rec = {
                "path": q.relative_to(ROOT).as_posix(),
                "header": header,
                "is_force_rollout_csv": False,
                "reason": "",
            }

            try:
                resolved = resolve_force_columns(header)
                rec["is_force_rollout_csv"] = True
                rec["resolved_force_columns"] = {f"{k[0]}_f{k[1]}": v for k, v in resolved.items()}
                records.append(rec)
                selected = rec["path"]
                _write_force_source_inventory(records, selected)
                return q
            except Exception as exc:
                rec["reason"] = str(exc)
                records.append(rec)

        _write_force_source_inventory(records, selected)
        raise FileNotFoundError(
            "No Stage 14.4 CSV with 12 contact-force columns was found. "
            "See results/logs_sample/stage14_5b_force_rollout_source_inventory.json"
        )

    candidates = _candidate_stage14_4_csv_paths()

    try:
        return select_force_csv(candidates)
    except FileNotFoundError:
        pass

    if not STAGE14_4_SCRIPT.exists():
        raise FileNotFoundError("Stage 14.4 MPC script not found and no force rollout CSV found.")

    rc, stdout, stderr = run([sys.executable, str(STAGE14_4_SCRIPT)])
    if rc != 0:
        raise RuntimeError("Failed to regenerate Stage 14.4 MPC rollout.\nSTDOUT:\n" + stdout + "\nSTDERR:\n" + stderr)

    candidates = _candidate_stage14_4_csv_paths()
    return select_force_csv(candidates)

def load_csv_rows(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])
    if not rows:
        raise ValueError(f"No rows in CSV: {path}")
    return fieldnames, rows


def _norm_col(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")


def resolve_force_columns(fieldnames: List[str]) -> Dict[Tuple[str, str], str]:
    norm_to_actual = {_norm_col(name): name for name in fieldnames}
    resolved = {}

    for leg, axis, candidates in FORCE_COLUMN_CANDIDATES:
        leg_l = leg.lower()
        axis_l = axis.lower()

        expanded = list(candidates) + [
            f"{leg}_f{axis}",
            f"{leg}_force_{axis}",
            f"{leg}_contact_force_{axis}",
            f"{leg}_contact_f{axis}",
            f"force_{leg}_{axis}",
            f"contact_force_{leg}_{axis}",
            f"contact_f_{leg}_{axis}",
            f"mpc_{leg}_f{axis}",
            f"mpc_{leg}_force_{axis}",
            f"u_{leg}_f{axis}",
            f"u_{leg}_{axis}",
            f"u0_{leg}_f{axis}",
            f"u0_{leg}_{axis}",
            f"force_target_{leg}_{axis}",
            f"{leg}_{axis}",
            f"{leg_l}_f{axis_l}",
            f"{leg_l}_force_{axis_l}",
            f"{leg_l}_contact_force_{axis_l}",
        ]

        found = None
        for cand in expanded:
            key = _norm_col(cand)
            if key in norm_to_actual:
                found = norm_to_actual[key]
                break

        if found is None:
            suffixes = [
                _norm_col(f"{leg}_f{axis}"),
                _norm_col(f"{leg}_force_{axis}"),
                _norm_col(f"{leg}_contact_force_{axis}"),
            ]
            for name in fieldnames:
                nl = _norm_col(name)
                if any(nl.endswith(suf) for suf in suffixes):
                    found = name
                    break

        if found is None:
            break

        resolved[(leg, axis)] = found

    if len(resolved) == 12:
        return resolved

    indexed_candidates = []
    for prefix in [
        "u",
        "u0",
        "mpc_u",
        "force",
        "f",
        "contact_force",
        "contact_forces",
        "force_target",
        "u_target",
    ]:
        cols = []
        ok = True
        for idx in range(12):
            names = [
                f"{prefix}_{idx}",
                f"{prefix}{idx}",
                f"{prefix}_{idx:02d}",
                f"{prefix}[{idx}]",
                f"{prefix}.{idx}",
            ]
            found = None
            for name in names:
                key = _norm_col(name)
                if key in norm_to_actual:
                    found = norm_to_actual[key]
                    break
            if found is None:
                ok = False
                break
            cols.append(found)
        if ok:
            indexed_candidates = cols
            break

    if indexed_candidates:
        out = {}
        idx = 0
        for leg in LEG_ORDER:
            for axis in ["x", "y", "z"]:
                out[(leg, axis)] = indexed_candidates[idx]
                idx += 1
        return out

    raise KeyError(
        "Missing 12 contact-force columns. "
        f"Available columns: {fieldnames}"
    )

def import_pinocchio():
    if importlib.util.find_spec("pinocchio") is None:
        raise ImportError("pinocchio Python module not found.")
    import pinocchio as pin
    return pin


def find_urdf() -> Path:
    candidates = []
    for pattern in [
        "assets/go1/*.urdf",
        "assets/**/*.urdf",
        "ros2_ws/src/**/*.urdf",
        "ros2_ws/src/**/*.xacro",
    ]:
        candidates.extend(ROOT.glob(pattern))

    candidates = [p for p in candidates if p.is_file()]
    if not candidates:
        raise FileNotFoundError("No URDF/Xacro candidate found.")

    urdfs = [p for p in candidates if p.suffix == ".urdf"]
    if urdfs:
        preferred = [p for p in urdfs if "go1" in p.as_posix().lower()]
        return sorted(preferred or urdfs, key=lambda p: len(p.as_posix()))[0]

    raise FileNotFoundError("Only xacro candidates found. Provide a generated URDF before Stage 14.5B.")


def build_pin_model(pin, urdf_path: Path):
    model = pin.buildModelFromUrdf(str(urdf_path), pin.JointModelFreeFlyer())
    data = model.createData()
    return model, data


def set_nominal_standing_q(pin, model):
    q = pin.neutral(model)

    if q.shape[0] >= 7:
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
        nq = model.nqs[jid]
        if nq == 1 and iq < q.shape[0]:
            q[iq] = value
            joint_q_assignments[name] = value

    return q, joint_q_assignments


def find_frame_ids(model) -> Dict[str, int]:
    frame_ids = {}
    frame_names = [f.name for f in model.frames]

    for leg in LEG_ORDER:
        exact = f"{leg}_foot"
        if exact in frame_names:
            frame_ids[leg] = model.getFrameId(exact)
            continue

        candidates = []
        for i, frame in enumerate(model.frames):
            name = frame.name.lower()
            if leg.lower() in name and "foot" in name:
                candidates.append(i)
        if not candidates:
            raise KeyError(f"No foot frame found for {leg}. Available foot-like frames: {[n for n in frame_names if 'foot' in n.lower()]}")
        frame_ids[leg] = candidates[0]

    return frame_ids


def find_actuated_velocity_indices(model) -> Dict[Tuple[str, str], int]:
    out = {}
    for leg in LEG_ORDER:
        for joint in JOINT_ORDER:
            matches = []
            for jid, name in enumerate(model.names):
                if jid == 0:
                    continue
                nl = name.lower()
                if leg.lower() in nl and joint in nl and model.nvs[jid] == 1:
                    matches.append(model.idx_vs[jid])
            if not matches:
                raise KeyError(f"No actuated velocity index found for {leg}_{joint}")
            out[(leg, joint)] = matches[0]
    return out


def compute_jacobians(pin, model, data, q, frame_ids):
    pin.forwardKinematics(model, data, q)
    pin.updateFramePlacements(model, data)
    jacobians = {}

    for leg, fid in frame_ids.items():
        J6 = pin.computeFrameJacobian(model, data, q, fid, pin.ReferenceFrame.LOCAL_WORLD_ALIGNED)
        Jlin = np.asarray(J6[:3, :], dtype=float)
        jacobians[leg] = Jlin

    return jacobians


def parse_float(value: str) -> float:
    if value is None or value == "":
        return float("nan")
    return float(value)


def main() -> int:
    failed_checks = []
    ROOT.joinpath("results/logs_sample").mkdir(parents=True, exist_ok=True)
    ROOT.joinpath("docs").mkdir(parents=True, exist_ok=True)

    if not SUMMARY_14_5A.exists():
        failed_checks.append("missing_stage14_5a_summary")
        summary_14_5a = {}
    else:
        summary_14_5a = read_json(SUMMARY_14_5A)
        if summary_14_5a.get("pass") is not True:
            failed_checks.append("stage14_5a_not_passed")

    rollout_csv = None
    fieldnames = []
    rows = []
    force_columns = {}
    urdf_path = None
    model = None
    joint_q_assignments = {}
    frame_ids = {}
    actuated_velocity_indices = {}
    pin_version = None

    torque_rows = []
    force_norms = []
    tau_abs_values = []
    nonfinite_force_count = 0
    nonfinite_tau_count = 0
    torque_limit_violation_count = 0

    try:
        rollout_csv = find_stage14_4_rollout_csv()
        fieldnames, rows = load_csv_rows(rollout_csv)
        force_columns = resolve_force_columns(fieldnames)
    except Exception as exc:
        failed_checks.append("stage14_4_rollout_or_force_columns_unavailable")
        rollout_error = str(exc)
    else:
        rollout_error = ""

    try:
        pin = import_pinocchio()
        pin_version = getattr(pin, "__version__", "unknown")
        urdf_path = find_urdf()
        model, data = build_pin_model(pin, urdf_path)
        q, joint_q_assignments = set_nominal_standing_q(pin, model)
        frame_ids = find_frame_ids(model)
        actuated_velocity_indices = find_actuated_velocity_indices(model)
        jacobians = compute_jacobians(pin, model, data, q, frame_ids)
    except Exception as exc:
        failed_checks.append("pinocchio_or_model_mapping_unavailable")
        pin_error = str(exc)
        jacobians = {}
    else:
        pin_error = ""

    if not failed_checks:
        header = ["step"]
        for leg in LEG_ORDER:
            for axis in ["x", "y", "z"]:
                header.append(f"{leg}_f{axis}")
        for leg in LEG_ORDER:
            for joint in JOINT_ORDER:
                header.append(f"{leg}_{joint}_tau_candidate")
        header += [
            "force_total_norm",
            "tau_abs_max",
            "torque_limit_violation",
        ]

        for step_idx, row in enumerate(rows):
            force_by_leg = {}
            row_force_values = []

            for leg in LEG_ORDER:
                f = np.zeros(3, dtype=float)
                for j, axis in enumerate(["x", "y", "z"]):
                    v = parse_float(row[force_columns[(leg, axis)]])
                    f[j] = v
                    row_force_values.append(v)
                force_by_leg[leg] = f

            if not np.all(np.isfinite(row_force_values)):
                nonfinite_force_count += 1

            tau_by_leg_joint = {}
            for leg in LEG_ORDER:
                tau_full = jacobians[leg].T @ force_by_leg[leg]
                for joint in JOINT_ORDER:
                    vidx = actuated_velocity_indices[(leg, joint)]
                    tau_value = float(tau_full[vidx])
                    tau_by_leg_joint[(leg, joint)] = tau_value
                    tau_abs_values.append(abs(tau_value))
                    if not math.isfinite(tau_value):
                        nonfinite_tau_count += 1

            tau_abs_max = max(abs(v) for v in tau_by_leg_joint.values())
            violation = tau_abs_max > TORQUE_LIMIT
            if violation:
                torque_limit_violation_count += 1

            force_total_norm = float(np.linalg.norm(np.concatenate([force_by_leg[leg] for leg in LEG_ORDER])))
            force_norms.append(force_total_norm)

            out_row = {"step": step_idx}
            for leg in LEG_ORDER:
                for axis, value in zip(["x", "y", "z"], force_by_leg[leg]):
                    out_row[f"{leg}_f{axis}"] = f"{value:.12g}"
            for leg in LEG_ORDER:
                for joint in JOINT_ORDER:
                    out_row[f"{leg}_{joint}_tau_candidate"] = f"{tau_by_leg_joint[(leg, joint)]:.12g}"
            out_row["force_total_norm"] = f"{force_total_norm:.12g}"
            out_row["tau_abs_max"] = f"{tau_abs_max:.12g}"
            out_row["torque_limit_violation"] = str(bool(violation))
            torque_rows.append(out_row)

        with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()
            writer.writerows(torque_rows)

    if nonfinite_force_count:
        failed_checks.append("nonfinite_force_detected")
    if nonfinite_tau_count:
        failed_checks.append("nonfinite_tau_candidate_detected")
    if torque_limit_violation_count:
        failed_checks.append("torque_limit_violation_detected")
    if not torque_rows and "stage14_4_rollout_or_force_columns_unavailable" not in failed_checks and "pinocchio_or_model_mapping_unavailable" not in failed_checks:
        failed_checks.append("no_torque_candidate_rows_generated")

    tau_abs_max_overall = max(tau_abs_values) if tau_abs_values else None
    force_norm_max = max(force_norms) if force_norms else None

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
        "wbc_qp_executed": False,
        "mpc_layer_output": "contact_force_target",
        "mapping_layer_output": "offline_joint_torque_candidate",
        "not_real_robot_torque_command": True,
        "stage14_5a_summary": str(SUMMARY_14_5A.relative_to(ROOT)) if SUMMARY_14_5A.exists() else None,
        "stage14_5a_pass": summary_14_5a.get("pass"),
        "stage14_4_rollout_csv": str(rollout_csv.relative_to(ROOT)) if rollout_csv else None,
        "stage14_4_rollout_error": rollout_error,
        "pinocchio_version": pin_version,
        "pinocchio_error": pin_error,
        "urdf_path": str(urdf_path.relative_to(ROOT)) if urdf_path else None,
        "row_count": len(rows),
        "candidate_row_count": len(torque_rows),
        "force_columns": {f"{k[0]}_f{k[1]}": v for k, v in force_columns.items()},
        "leg_order": LEG_ORDER,
        "joint_order_per_leg": JOINT_ORDER,
        "torque_limit_abs": TORQUE_LIMIT,
        "nonfinite_force_count": nonfinite_force_count,
        "nonfinite_tau_candidate_count": nonfinite_tau_count,
        "torque_limit_violation_count": torque_limit_violation_count,
        "max_force_total_norm": force_norm_max,
        "max_tau_candidate_abs": tau_abs_max_overall,
        "frame_ids": frame_ids,
        "actuated_velocity_indices": {f"{k[0]}_{k[1]}": v for k, v in actuated_velocity_indices.items()},
        "joint_q_assignments": joint_q_assignments,
        "output_csv": str(OUT_CSV.relative_to(ROOT)) if OUT_CSV.exists() else None,
        "output_doc": str(OUT_DOC.relative_to(ROOT)),
        "output_summary": str(OUT_SUMMARY.relative_to(ROOT)),
        "notes": [
            "Offline check only.",
            "MPC output is interpreted as contact-force target.",
            "J^T f output is a joint torque candidate for analysis only.",
            "No MuJoCo closed-loop simulation is run.",
            "No ROS torque publisher is used.",
            "No frozen mixed baseline control law is modified.",
        ],
    }

    write_json(OUT_SUMMARY, summary)

    doc_lines = [
        "# Stage 14.5B Offline MPC Contact-Force to Joint Torque Candidate Check",
        "",
        "Scope: simulation-only offline mapping check.",
        "",
        "This stage reads Stage 14.4 MPC contact-force rollout data and maps contact-force targets through nominal Pinocchio foot Jacobians to produce joint torque candidates for offline analysis.",
        "",
        "It does not run MuJoCo closed-loop simulation, does not run WBC/QP, does not use a ROS torque publisher, and does not modify the frozen mixed baseline control law.",
        "",
        "## Evidence",
        "",
        f"- Summary JSON: `{OUT_SUMMARY.relative_to(ROOT)}`",
        f"- Candidate CSV: `{OUT_CSV.relative_to(ROOT) if OUT_CSV.exists() else 'not generated'}`",
        "",
        "## Result",
        "",
        f"- pass: {summary['pass']}",
        f"- failed_checks: {summary['failed_checks']}",
        f"- row_count: {summary['row_count']}",
        f"- candidate_row_count: {summary['candidate_row_count']}",
        f"- max_tau_candidate_abs: {summary['max_tau_candidate_abs']}",
        f"- torque_limit_abs: {summary['torque_limit_abs']}",
        f"- torque_limit_violation_count: {summary['torque_limit_violation_count']}",
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
        f"- wbc_qp_executed: {summary['wbc_qp_executed']}",
        "",
        "## Boundary",
        "",
        "The generated values are offline joint torque candidates, not real robot torque commands and not hardware execution evidence.",
        "",
    ]
    OUT_DOC.write_text("\n".join(doc_lines), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
