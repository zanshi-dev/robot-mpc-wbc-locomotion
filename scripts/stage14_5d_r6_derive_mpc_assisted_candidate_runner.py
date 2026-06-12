#!/usr/bin/env python3
from pathlib import Path
import datetime as dt
import hashlib
import json
import py_compile
import re
import subprocess
from typing import List

ROOT = Path.cwd()
STAGE = "14.5D-R6"

SUMMARY_R5 = ROOT / "results/logs_sample/stage14_5d_r5_mpc_candidate_injection_design_inspection_summary.json"
R2_RUNNER = ROOT / "scripts/stage14_5d_r2_closed_loop_ab_runner_skeleton.py"
BASELINE_RUNNER = ROOT / "scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py"

R6_RUNNER = ROOT / "scripts/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_runner.py"
OUT_SUMMARY = ROOT / "results/logs_sample/stage14_5d_r6_derive_mpc_assisted_candidate_runner_summary.json"
OUT_DOC = ROOT / "docs/stage14_5d_r6_derive_mpc_assisted_candidate_runner.md"
OUT_PATCH_NOTES = ROOT / "results/logs_sample/stage14_5d_r6_derive_mpc_assisted_candidate_runner_patch_notes.txt"


def git(args: List[str]) -> str:
    proc = subprocess.run(
        ["git"] + args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def read_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def patch_r2_to_r6(src: str):
    notes = []

    header = (
        "# Stage 14.5D-R6 derived simulation-only MPC-assisted candidate runner.\n"
        "# Source-derived from Stage 14.5D-R2 skeleton.\n"
        "# Default mode remains baseline.\n"
        "# MPC-assisted candidate mode is explicit, gated, bounded, logged, and simulation-only.\n"
        "# No hardware deployment, no actuator enablement, no ROS torque publisher.\n"
    )
    src = header + "\n" + src
    notes.append("Inserted Stage 14.5D-R6 safety header.")

    replacements = {
        'LOG_CSV = "results/logs_sample/stage14_5d_r2_closed_loop_ab_baseline_skeleton_log.csv"':
            'LOG_CSV_TEMPLATE = "results/logs_sample/stage14_5d_r6_closed_loop_ab_{control_mode}_log.csv"',
        'SUMMARY_CSV = "results/logs_sample/stage14_5d_r2_closed_loop_ab_baseline_skeleton_summary.csv"':
            'SUMMARY_CSV_TEMPLATE = "results/logs_sample/stage14_5d_r6_closed_loop_ab_{control_mode}_summary.csv"',
    }
    for old, new in replacements.items():
        if old not in src:
            raise RuntimeError(f"missing output path anchor: {old}")
        src = src.replace(old, new, 1)
        notes.append(f"Replaced output path anchor: {old} -> {new}")

    src = re.sub(r"\bLOG_CSV\b", "log_csv", src)
    src = re.sub(r"\bSUMMARY_CSV\b", "summary_csv", src)
    notes.append("Converted LOG_CSV/SUMMARY_CSV runtime references to mode-specific variables.")

    const_anchor = 'MPC_ASSISTED_CANDIDATE_DEFAULT_SCALE = 0.0\n'
    const_block = (
        'MPC_ASSISTED_CANDIDATE_DEFAULT_SCALE = 0.0\n'
        'MPC_ASSISTED_CANDIDATE_SCALE_MAX = 0.25\n'
        'MPC_ASSISTED_CANDIDATE_CSV_DEFAULT = "results/logs_sample/stage14_5b_offline_mpc_force_to_torque_candidates.csv"\n'
        'MPC_ASSISTED_CANDIDATE_STEP_POLICY_REPEAT = "repeat"\n'
        'MPC_ASSISTED_CANDIDATE_STEP_POLICY_CHOICES = [MPC_ASSISTED_CANDIDATE_STEP_POLICY_REPEAT]\n'
        'MPC_CANDIDATE_LEG_ORDER = ["FR", "FL", "RR", "RL"]\n'
        'MPC_CANDIDATE_JOINT_ORDER = ["hip", "thigh", "calf"]\n'
    )
    if const_anchor not in src:
        raise RuntimeError("missing candidate constant anchor")
    src = src.replace(const_anchor, const_block, 1)
    notes.append("Inserted candidate CSV, scale bound, and step policy constants.")

    helper_match = re.search(r"^def\s+leg_indices\s*\([^)]*\):\s*$", src, flags=re.MULTILINE)
    if not helper_match:
        raise RuntimeError("missing leg_indices helper anchor")
    helper_anchor = src[helper_match.start():helper_match.end()] + "\n"
    helper_block = r'''

def read_mpc_tau_candidates(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"MPC candidate CSV not found: {path}")

    rows = []
    lookup = {}
    required_columns = ["step"]
    for leg in MPC_CANDIDATE_LEG_ORDER:
        for joint in MPC_CANDIDATE_JOINT_ORDER:
            required_columns.append(f"{leg}_{joint}_tau_candidate")

    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        columns = set(reader.fieldnames or [])
        missing = sorted(set(required_columns) - columns)
        if missing:
            raise RuntimeError(f"MPC candidate CSV missing required columns: {missing}")

        for row in reader:
            source_step = int(float(row["step"]))
            tau_by_leg = {}
            for leg in MPC_CANDIDATE_LEG_ORDER:
                tau_by_leg[leg] = [
                    float(row[f"{leg}_{joint}_tau_candidate"])
                    for joint in MPC_CANDIDATE_JOINT_ORDER
                ]
            item = {
                "source_step": source_step,
                "tau_by_leg": tau_by_leg,
                "tau_abs_max": float(row.get("tau_abs_max", 0.0) or 0.0),
                "force_total_norm": float(row.get("force_total_norm", 0.0) or 0.0),
            }
            rows.append(item)
            lookup[source_step] = item

    if not rows:
        raise RuntimeError(f"MPC candidate CSV is empty: {path}")

    step_values = sorted(lookup)
    return rows, lookup, step_values


def candidate_row_for_step(step, rows, lookup, step_values, policy):
    if step in lookup:
        return lookup[step]

    if policy == MPC_ASSISTED_CANDIDATE_STEP_POLICY_REPEAT:
        return rows[step % len(rows)]

    raise RuntimeError(f"unsupported candidate step policy: {policy}")


def candidate_tau_vector(row, model_nu):
    tau = np.zeros(model_nu)
    for leg in MPC_CANDIDATE_LEG_ORDER:
        tau[leg_indices(leg)] = np.asarray(row["tau_by_leg"][leg], dtype=float)
    return tau

'''
    src = src[:helper_match.start()] + helper_block + src[helper_match.start():]
    notes.append("Inserted candidate CSV reader and candidate torque vector helpers.")

    old_arg_block = '''    parser.add_argument(
        "--mpc-assisted-candidate-scale",
        type=float,
        default=MPC_ASSISTED_CANDIDATE_DEFAULT_SCALE,
        help="Future candidate scaling placeholder. Default 0.0 in R2.",
    )
    args = parser.parse_args()
'''
    new_arg_block = '''    parser.add_argument(
        "--mpc-assisted-candidate-scale",
        type=float,
        default=MPC_ASSISTED_CANDIDATE_DEFAULT_SCALE,
        help="MPC-assisted candidate torque scale. Baseline mode requires 0.0; candidate mode requires 0.0 < scale <= 0.25.",
    )
    parser.add_argument(
        "--candidate-csv",
        default=MPC_ASSISTED_CANDIDATE_CSV_DEFAULT,
        help="Offline MPC torque candidate CSV used only in explicit candidate mode.",
    )
    parser.add_argument(
        "--candidate-step-policy",
        choices=MPC_ASSISTED_CANDIDATE_STEP_POLICY_CHOICES,
        default=MPC_ASSISTED_CANDIDATE_STEP_POLICY_REPEAT,
        help="Step mapping policy when simulation steps exceed offline candidate rows.",
    )
    args = parser.parse_args()
'''
    if old_arg_block not in src:
        raise RuntimeError("missing mpc candidate scale argparse block")
    src = src.replace(old_arg_block, new_arg_block, 1)
    notes.append("Inserted candidate CSV and candidate step-policy CLI arguments.")

    old_gate = '''    if args.control_mode == CONTROL_MODE_MPC_ASSISTED_CANDIDATE:
        if not args.allow_mpc_assisted_candidate:
            raise RuntimeError("mpc_assisted_candidate requires --allow-mpc-assisted-candidate")
        raise NotImplementedError("Stage 14.5D-R2 only derives the explicit switch skeleton; MPC-assisted torque injection is not implemented yet")

    if args.mpc_assisted_candidate_scale != 0.0:
        raise RuntimeError("Stage 14.5D-R2 baseline mode requires --mpc-assisted-candidate-scale 0.0")

'''
    new_gate = '''    candidate_rows = []
    candidate_lookup = {}
    candidate_step_values = []

    if args.control_mode == CONTROL_MODE_MPC_ASSISTED_CANDIDATE:
        if not args.allow_mpc_assisted_candidate:
            raise RuntimeError("mpc_assisted_candidate requires --allow-mpc-assisted-candidate")
        if args.mpc_assisted_candidate_scale <= 0.0:
            raise RuntimeError("mpc_assisted_candidate requires --mpc-assisted-candidate-scale > 0.0")
        if args.mpc_assisted_candidate_scale > MPC_ASSISTED_CANDIDATE_SCALE_MAX:
            raise RuntimeError(f"mpc_assisted_candidate scale exceeds bound: {MPC_ASSISTED_CANDIDATE_SCALE_MAX}")
        candidate_rows, candidate_lookup, candidate_step_values = read_mpc_tau_candidates(Path(args.candidate_csv))
    else:
        if args.mpc_assisted_candidate_scale != 0.0:
            raise RuntimeError("baseline mode requires --mpc-assisted-candidate-scale 0.0")

    log_csv = LOG_CSV_TEMPLATE.format(control_mode=args.control_mode)
    summary_csv = SUMMARY_CSV_TEMPLATE.format(control_mode=args.control_mode)

'''
    if old_gate not in src:
        raise RuntimeError("missing R2 NotImplemented gate block")
    src = src.replace(old_gate, new_gate, 1)
    notes.append("Replaced R2 NotImplemented gate with bounded simulation-only candidate loader gate.")

    init_anchor = "    max_tau_total_raw_abs = 0.0\n"
    init_block = (
        "    max_tau_total_raw_abs = 0.0\n"
        "    max_tau_baseline_raw_abs = 0.0\n"
        "    max_tau_candidate_abs = 0.0\n"
        "    max_tau_candidate_scaled_abs = 0.0\n"
    )
    if init_anchor not in src:
        raise RuntimeError("missing torque metric initialization anchor")
    src = src.replace(init_anchor, init_block, 1)
    notes.append("Inserted candidate torque metric accumulators.")

    old_torque = "        tau_total_raw = tau_stance_pd + tau_stance_wbc + tau_swing_pd\n        tau_total = np.clip(tau_total_raw, -TORQUE_LIMIT, TORQUE_LIMIT)\n"
    new_torque = '''        tau_baseline_raw = tau_stance_pd + tau_stance_wbc + tau_swing_pd

        candidate_source_step = ""
        candidate_available = False
        tau_candidate = np.zeros(model.nu)
        if args.control_mode == CONTROL_MODE_MPC_ASSISTED_CANDIDATE:
            candidate_row = candidate_row_for_step(
                step,
                candidate_rows,
                candidate_lookup,
                candidate_step_values,
                args.candidate_step_policy,
            )
            tau_candidate = candidate_tau_vector(candidate_row, model.nu)
            candidate_source_step = candidate_row["source_step"]
            candidate_available = True

        tau_candidate_scaled = args.mpc_assisted_candidate_scale * tau_candidate
        tau_total_raw = tau_baseline_raw + tau_candidate_scaled
        tau_total = np.clip(tau_total_raw, -TORQUE_LIMIT, TORQUE_LIMIT)

        max_tau_baseline_raw_abs = max(max_tau_baseline_raw_abs, float(np.max(np.abs(tau_baseline_raw))))
        max_tau_candidate_abs = max(max_tau_candidate_abs, float(np.max(np.abs(tau_candidate))))
        max_tau_candidate_scaled_abs = max(max_tau_candidate_scaled_abs, float(np.max(np.abs(tau_candidate_scaled))))
'''
    if old_torque not in src:
        raise RuntimeError("missing torque composition/clip anchor")
    src = src.replace(old_torque, new_torque, 1)
    notes.append("Inserted candidate torque injection after baseline raw torque composition and before clipping.")

    abs_calc_anchor = "        tau_total_raw_abs = float(np.max(np.abs(tau_total_raw)))\n"
    abs_calc_replacement = (
        "        tau_baseline_raw_abs = float(np.max(np.abs(tau_baseline_raw)))\n"
        "        tau_candidate_abs = float(np.max(np.abs(tau_candidate)))\n"
        "        tau_candidate_scaled_abs = float(np.max(np.abs(tau_candidate_scaled)))\n"
        "        tau_total_raw_abs = float(np.max(np.abs(tau_total_raw)))\n"
    )
    if abs_calc_anchor not in src:
        raise RuntimeError("missing tau_total_raw_abs calculation anchor")
    src = src.replace(abs_calc_anchor, abs_calc_replacement, 1)

    log_dict_anchor = '            "tau_total_raw_abs": f"{tau_total_raw_abs:.12f}",\n'
    log_dict_replacement = (
        '            "control_mode": args.control_mode,\n'
        '            "candidate_available": str(candidate_available),\n'
        '            "candidate_source_step": str(candidate_source_step),\n'
        '            "candidate_scale": f"{args.mpc_assisted_candidate_scale:.12f}",\n'
        '            "tau_baseline_raw_abs": f"{tau_baseline_raw_abs:.12f}",\n'
        '            "tau_candidate_abs": f"{tau_candidate_abs:.12f}",\n'
        '            "tau_candidate_scaled_abs": f"{tau_candidate_scaled_abs:.12f}",\n'
        '            "tau_total_raw_abs": f"{tau_total_raw_abs:.12f}",\n'
    )
    if log_dict_anchor not in src:
        raise RuntimeError("missing log tau_total_raw_abs anchor")
    src = src.replace(log_dict_anchor, log_dict_replacement, 1)

    notes.append("Inserted candidate abs calculations and candidate fields into per-step log rows.")

    src = src.replace('"stage": "14.5D-R2"', '"stage": "14.5D-R6"')
    src = src.replace('"control_law_changed": False,', '"control_law_changed": args.control_mode == CONTROL_MODE_MPC_ASSISTED_CANDIDATE,')
    src = src.replace('"mpc_assisted_candidate_executed": False,', '"mpc_assisted_candidate_executed": args.control_mode == CONTROL_MODE_MPC_ASSISTED_CANDIDATE,')
    notes.append("Updated runtime summary stage and candidate execution flags.")

    old_summary_scale = '        "mpc_assisted_candidate_scale": args.mpc_assisted_candidate_scale,\n'
    new_summary_scale = '''        "mpc_assisted_candidate_scale": args.mpc_assisted_candidate_scale,
        "mpc_assisted_candidate_scale_max": MPC_ASSISTED_CANDIDATE_SCALE_MAX,
        "candidate_csv": args.candidate_csv,
        "candidate_step_policy": args.candidate_step_policy,
        "candidate_row_count": len(candidate_rows),
        "candidate_available_in_run": args.control_mode == CONTROL_MODE_MPC_ASSISTED_CANDIDATE,
        "real_robot_torque_commanded": False,
        "ros_publisher_used": False,
'''
    if old_summary_scale not in src:
        raise RuntimeError("missing summary candidate scale anchor")
    src = src.replace(old_summary_scale, new_summary_scale, 1)
    notes.append("Inserted candidate source and safety fields into summary.")

    metric_anchor = '        "max_tau_total_raw_abs": f"{max_tau_total_raw_abs:.12f}",\n'
    metric_block = '''        "max_tau_baseline_raw_abs": f"{max_tau_baseline_raw_abs:.12f}",
        "max_tau_candidate_abs": f"{max_tau_candidate_abs:.12f}",
        "max_tau_candidate_scaled_abs": f"{max_tau_candidate_scaled_abs:.12f}",
        "max_tau_total_raw_abs": f"{max_tau_total_raw_abs:.12f}",
'''
    if metric_anchor not in src:
        raise RuntimeError("missing summary max_tau_total_raw_abs anchor")
    src = src.replace(metric_anchor, metric_block, 1)
    notes.append("Inserted candidate torque metrics into summary.")

    if "NotImplementedError" in src:
        raise RuntimeError("NotImplementedError remains in R6 candidate runner")

    forbidden = [
        "/go1/joint_torque_cmd",
        "create_publisher",
        "rclpy",
        "hardware_deployment_completed=True",
        "torque_enable_ready=True",
    ]
    forbidden_hits = [tok for tok in forbidden if tok in src]
    if forbidden_hits:
        raise RuntimeError(f"forbidden tokens present in R6 runner: {forbidden_hits}")

    return src, notes


def main() -> int:
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)

    failed_checks = []

    r5 = read_json(SUMMARY_R5)
    if not r5 or r5.get("pass") is not True:
        failed_checks.append("stage14_5d_r5_not_passed_or_missing")

    if not R2_RUNNER.exists():
        failed_checks.append("r2_runner_missing")
        r2_src = ""
    else:
        r2_src = R2_RUNNER.read_text(encoding="utf-8", errors="ignore")

    if not BASELINE_RUNNER.exists():
        failed_checks.append("baseline_runner_missing")

    compile_error = ""
    patch_notes = []
    r6_src = ""

    if r2_src:
        try:
            r6_src, patch_notes = patch_r2_to_r6(r2_src)
            R6_RUNNER.write_text(r6_src, encoding="utf-8")
            py_compile.compile(str(R6_RUNNER), doraise=True)
        except Exception as exc:
            compile_error = str(exc)
            failed_checks.append("r6_patch_or_compile_failed")

    OUT_PATCH_NOTES.write_text("\n".join(patch_notes) + "\n", encoding="utf-8")

    r6_text = R6_RUNNER.read_text(encoding="utf-8", errors="ignore") if R6_RUNNER.exists() else ""
    required_tokens = [
        "read_mpc_tau_candidates",
        "candidate_row_for_step",
        "candidate_tau_vector",
        "MPC_ASSISTED_CANDIDATE_SCALE_MAX = 0.25",
        "candidate_csv",
        "tau_baseline_raw",
        "tau_candidate_scaled",
        "tau_total_raw = tau_baseline_raw + tau_candidate_scaled",
        "np.clip(tau_total_raw, -TORQUE_LIMIT, TORQUE_LIMIT)",
        "real_robot_torque_commanded",
        "ros_publisher_used",
    ]
    missing_required_tokens = [tok for tok in required_tokens if tok not in r6_text]
    if missing_required_tokens:
        failed_checks.append("r6_runner_missing_required_tokens")

    forbidden_tokens = [
        "NotImplementedError",
        "/go1/joint_torque_cmd",
        "create_publisher",
        "rclpy",
    ]
    forbidden_token_hits = [tok for tok in forbidden_tokens if tok in r6_text]
    if forbidden_token_hits:
        failed_checks.append("r6_runner_forbidden_tokens_present")

    source_diff_checks = {}
    for p in [R2_RUNNER, BASELINE_RUNNER]:
        if p.exists():
            rel = str(p.relative_to(ROOT))
            diff = git(["diff", "--", rel])
            source_diff_checks[rel] = {
                "local_diff_empty": diff.strip() == "",
                "diff_len": len(diff),
            }
            if diff.strip():
                failed_checks.append(f"source_file_has_local_diff:{rel}")

    allowed_dirty = {
        "scripts/stage14_5d_r6_derive_mpc_assisted_candidate_runner.py",
        "scripts/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_runner.py",
        "docs/stage14_5d_r6_derive_mpc_assisted_candidate_runner.md",
        "results/logs_sample/stage14_5d_r6_derive_mpc_assisted_candidate_runner_summary.json",
        "results/logs_sample/stage14_5d_r6_derive_mpc_assisted_candidate_runner_patch_notes.txt",
    }

    dirty = git(["status", "--porcelain"])
    dirty_paths = [line[3:].strip() for line in dirty.splitlines() if line.strip()]
    dirty_non_stage = [p for p in dirty_paths if p not in allowed_dirty]
    if dirty_non_stage:
        failed_checks.append("unexpected_dirty_files_present")

    summary = {
        "stage": STAGE,
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "pass": len(failed_checks) == 0,
        "failed_checks": failed_checks,
        "simulation_only_project": True,
        "hardware_deployment_completed": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "real_robot_torque_commanded": False,
        "ros_publisher_used": False,
        "baseline_source_modified": False,
        "r2_runner_source_modified": False,
        "r6_runner_generated": R6_RUNNER.exists(),
        "mujoco_closed_loop_baseline_mode_executed": False,
        "mujoco_closed_loop_candidate_mode_executed": False,
        "mujoco_closed_loop_ab_executed": False,
        "mujoco_sim_data_ctrl_used": False,
        "mpc_assisted_candidate_implemented": R6_RUNNER.exists() and not forbidden_token_hits and not missing_required_tokens,
        "mpc_assisted_candidate_executed": False,
        "stage14_5d_r5_pass": None if not r5 else r5.get("pass"),
        "source_runner": str(R2_RUNNER.relative_to(ROOT)),
        "baseline_runner": str(BASELINE_RUNNER.relative_to(ROOT)),
        "r6_runner": str(R6_RUNNER.relative_to(ROOT)) if R6_RUNNER.exists() else None,
        "r2_runner_sha256": sha256_text(r2_src) if r2_src else None,
        "r6_runner_sha256": sha256_text(r6_text) if r6_text else None,
        "compile_error": compile_error,
        "missing_required_tokens": missing_required_tokens,
        "forbidden_token_hits": forbidden_token_hits,
        "source_diff_checks": source_diff_checks,
        "patch_notes": patch_notes,
        "git": {
            "branch": git(["branch", "--show-current"]),
            "head": git(["rev-parse", "--short", "HEAD"]),
            "status_porcelain": dirty,
            "dirty_non_stage14_5d_r6": dirty_non_stage,
        },
        "generated_files": [
            "scripts/stage14_5d_r6_derive_mpc_assisted_candidate_runner.py",
            "scripts/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_runner.py",
            "docs/stage14_5d_r6_derive_mpc_assisted_candidate_runner.md",
            "results/logs_sample/stage14_5d_r6_derive_mpc_assisted_candidate_runner_summary.json",
            "results/logs_sample/stage14_5d_r6_derive_mpc_assisted_candidate_runner_patch_notes.txt",
        ],
        "notes": [
            "Derivation step only.",
            "R6 generates a new simulation-only candidate-capable runner.",
            "R6 does not execute MuJoCo.",
            "R6 does not execute A/B comparison.",
            "R6 does not modify the frozen baseline runner.",
            "R6 does not modify the R2 skeleton runner.",
            "No real robot torque command is sent.",
        ],
    }

    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    doc = [
        "# Stage 14.5D-R6 Derive MPC-assisted Candidate Runner",
        "",
        "Scope: simulation-only source derivation.",
        "",
        "This step derives a new candidate-capable runner from the Stage 14.5D-R2 skeleton.",
        "",
        "It does not run MuJoCo, does not execute candidate mode, does not execute A/B comparison, does not modify the frozen baseline runner, and does not use ROS torque publishing.",
        "",
        "## Evidence",
        "",
        f"- Summary JSON: `{OUT_SUMMARY.relative_to(ROOT)}`",
        f"- Patch notes: `{OUT_PATCH_NOTES.relative_to(ROOT)}`",
        f"- R6 runner: `{R6_RUNNER.relative_to(ROOT) if R6_RUNNER.exists() else 'not generated'}`",
        "",
        "## Result",
        "",
        f"- pass: {summary['pass']}",
        f"- failed_checks: {summary['failed_checks']}",
        f"- compile_error: `{summary['compile_error']}`",
        f"- mpc_assisted_candidate_implemented: {summary['mpc_assisted_candidate_implemented']}",
        f"- mpc_assisted_candidate_executed: {summary['mpc_assisted_candidate_executed']}",
        "",
        "## Boundary",
        "",
        f"- mujoco_closed_loop_candidate_mode_executed: {summary['mujoco_closed_loop_candidate_mode_executed']}",
        f"- mujoco_closed_loop_ab_executed: {summary['mujoco_closed_loop_ab_executed']}",
        f"- mujoco_sim_data_ctrl_used: {summary['mujoco_sim_data_ctrl_used']}",
        f"- real_robot_torque_commanded: {summary['real_robot_torque_commanded']}",
        f"- ros_publisher_used: {summary['ros_publisher_used']}",
        "",
        "This is implementation-source evidence only. It is not candidate rollout evidence and not A/B evidence.",
        "",
    ]
    OUT_DOC.write_text("\n".join(doc), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
