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
STAGE = "14.5D-R2"

BASELINE_RUNNER = ROOT / "scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py"
SUMMARY_R1 = ROOT / "results/logs_sample/stage14_5d_r1_baseline_runner_structure_inspection_summary.json"

DERIVED_RUNNER = ROOT / "scripts/stage14_5d_r2_closed_loop_ab_runner_skeleton.py"
OUT_SUMMARY = ROOT / "results/logs_sample/stage14_5d_r2_closed_loop_ab_runner_skeleton_summary.json"
OUT_DOC = ROOT / "docs/stage14_5d_r2_closed_loop_ab_runner_skeleton.md"
OUT_PATCH_NOTES = ROOT / "results/logs_sample/stage14_5d_r2_closed_loop_ab_runner_skeleton_patch_notes.txt"


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


def patch_source(src: str):
    notes = []

    if "from pathlib import Path\n" not in src:
        raise RuntimeError("missing import anchor: from pathlib import Path")
    src = src.replace(
        "from pathlib import Path\n",
        "from pathlib import Path\nimport argparse\n",
        1,
    )
    notes.append("Inserted argparse import.")

    header = (
        "# Stage 14.5D-R2 derived simulation-only A/B runner skeleton.\n"
        "# Source-derived from the frozen mixed baseline runner.\n"
        "# Default control mode remains baseline.\n"
        "# The MPC-assisted candidate mode is explicitly gated and intentionally not implemented in R2.\n"
        "# No hardware deployment, no actuator enablement, no ROS torque publisher.\n"
    )
    src = header + "\n" + src
    notes.append("Inserted Stage 14.5D-R2 safety header.")

    replacements = {
        'LOG_CSV = "results/logs_sample/stage13_2_2400step_mixed_baseline_log.csv"':
            'LOG_CSV = "results/logs_sample/stage14_5d_r2_closed_loop_ab_baseline_skeleton_log.csv"',
        'SUMMARY_CSV = "results/logs_sample/stage13_2_2400step_mixed_baseline_summary.csv"':
            'SUMMARY_CSV = "results/logs_sample/stage14_5d_r2_closed_loop_ab_baseline_skeleton_summary.csv"',
    }

    for old, new in replacements.items():
        if old not in src:
            raise RuntimeError(f"missing output path anchor: {old}")
        src = src.replace(old, new, 1)
        notes.append(f"Replaced output path anchor: {old} -> {new}")

    torque_limit_anchor = "TORQUE_LIMIT = 23.7\n"
    if torque_limit_anchor not in src:
        raise RuntimeError("missing TORQUE_LIMIT anchor")
    switch_block = (
        "TORQUE_LIMIT = 23.7\n"
        "\n"
        "CONTROL_MODE_BASELINE = \"baseline\"\n"
        "CONTROL_MODE_MPC_ASSISTED_CANDIDATE = \"mpc_assisted_candidate\"\n"
        "CONTROL_MODE_CHOICES = [CONTROL_MODE_BASELINE, CONTROL_MODE_MPC_ASSISTED_CANDIDATE]\n"
        "DEFAULT_CONTROL_MODE = CONTROL_MODE_BASELINE\n"
        "MPC_ASSISTED_CANDIDATE_DEFAULT_SCALE = 0.0\n"
    )
    src = src.replace(torque_limit_anchor, switch_block, 1)
    notes.append("Inserted explicit control-mode constants after TORQUE_LIMIT.")

    main_anchor = "def main():\n"
    if main_anchor not in src:
        raise RuntimeError("missing main anchor")
    main_block = (
        "def main():\n"
        "    parser = argparse.ArgumentParser(description=\"Stage 14.5D-R2 simulation-only A/B runner skeleton\")\n"
        "    parser.add_argument(\n"
        "        \"--control-mode\",\n"
        "        choices=CONTROL_MODE_CHOICES,\n"
        "        default=DEFAULT_CONTROL_MODE,\n"
        "        help=\"Explicit simulation-only control mode. Default is baseline.\",\n"
        "    )\n"
        "    parser.add_argument(\n"
        "        \"--allow-mpc-assisted-candidate\",\n"
        "        action=\"store_true\",\n"
        "        help=\"Explicit gate for future MPC-assisted candidate mode. R2 still does not implement candidate torque injection.\",\n"
        "    )\n"
        "    parser.add_argument(\n"
        "        \"--mpc-assisted-candidate-scale\",\n"
        "        type=float,\n"
        "        default=MPC_ASSISTED_CANDIDATE_DEFAULT_SCALE,\n"
        "        help=\"Future candidate scaling placeholder. Default 0.0 in R2.\",\n"
        "    )\n"
        "    args = parser.parse_args()\n"
        "\n"
        "    if args.control_mode == CONTROL_MODE_MPC_ASSISTED_CANDIDATE:\n"
        "        if not args.allow_mpc_assisted_candidate:\n"
        "            raise RuntimeError(\"mpc_assisted_candidate requires --allow-mpc-assisted-candidate\")\n"
        "        raise NotImplementedError(\"Stage 14.5D-R2 only derives the explicit switch skeleton; MPC-assisted torque injection is not implemented yet\")\n"
        "\n"
        "    if args.mpc_assisted_candidate_scale != 0.0:\n"
        "        raise RuntimeError(\"Stage 14.5D-R2 baseline mode requires --mpc-assisted-candidate-scale 0.0\")\n"
        "\n"
    )
    src = src.replace(main_anchor, main_block, 1)
    notes.append("Inserted argparse control-mode gate at main entry.")

    summary_anchor = "    summary = {\n"
    if summary_anchor not in src:
        raise RuntimeError("missing summary dict anchor")
    summary_block = (
        "    summary = {\n"
        "        \"stage\": \"14.5D-R2\",\n"
        "        \"control_mode\": args.control_mode,\n"
        "        \"simulation_only_project\": True,\n"
        "        \"hardware_deployment_completed\": False,\n"
        "        \"torque_enable_ready\": False,\n"
        "        \"torque_publisher_enabled\": False,\n"
        "        \"control_law_changed\": False,\n"
        "        \"mixed_baseline_modified\": False,\n"
        "        \"mpc_assisted_candidate_switch_present\": True,\n"
        "        \"mpc_assisted_candidate_executed\": False,\n"
        "        \"mpc_assisted_candidate_scale\": args.mpc_assisted_candidate_scale,\n"
    )
    src = src.replace(summary_anchor, summary_block, 1)
    notes.append("Inserted Stage 14.5D-R2 safety fields into derived runner summary.")

    forbidden = [
        "/go1/joint_torque_cmd",
        "create_publisher",
        "rclpy",
        "torque_enable_ready=True",
        "hardware_deployment_completed=True",
    ]
    forbidden_hits = [item for item in forbidden if item in src]
    if forbidden_hits:
        raise RuntimeError(f"forbidden tokens in derived skeleton: {forbidden_hits}")

    return src, notes


def main() -> int:
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)

    failed_checks = []

    r1 = read_json(SUMMARY_R1)
    if not r1 or r1.get("pass") is not True:
        failed_checks.append("stage14_5d_r1_not_passed_or_missing")

    if not BASELINE_RUNNER.exists():
        failed_checks.append("baseline_runner_missing")
        baseline_src = ""
        derived_src = ""
        patch_notes = []
        compile_error = "baseline runner missing"
    else:
        baseline_src = BASELINE_RUNNER.read_text(encoding="utf-8", errors="ignore")
        try:
            derived_src, patch_notes = patch_source(baseline_src)
            DERIVED_RUNNER.write_text(derived_src, encoding="utf-8")
            py_compile.compile(str(DERIVED_RUNNER), doraise=True)
            compile_error = ""
        except Exception as exc:
            derived_src = ""
            patch_notes = []
            compile_error = str(exc)
            failed_checks.append("derive_or_compile_failed")

    if DERIVED_RUNNER.exists():
        derived_text = DERIVED_RUNNER.read_text(encoding="utf-8", errors="ignore")
        required_tokens = [
            "CONTROL_MODE_BASELINE",
            "CONTROL_MODE_MPC_ASSISTED_CANDIDATE",
            "--control-mode",
            "--allow-mpc-assisted-candidate",
            "NotImplementedError",
            "mpc_assisted_candidate_switch_present",
            "mpc_assisted_candidate_executed",
        ]
        missing_tokens = [t for t in required_tokens if t not in derived_text]
        if missing_tokens:
            failed_checks.append("derived_runner_missing_required_tokens")
    else:
        derived_text = ""
        missing_tokens = ["derived runner missing"]

    OUT_PATCH_NOTES.write_text("\n".join(patch_notes) + "\n", encoding="utf-8")

    dirty = git(["status", "--porcelain"])
    dirty_paths = [line[3:].strip() for line in dirty.splitlines() if line.strip()]
    allowed_dirty = {
        "scripts/stage14_5d_r2_derive_closed_loop_ab_runner_skeleton.py",
        "scripts/stage14_5d_r2_closed_loop_ab_runner_skeleton.py",
        "docs/stage14_5d_r2_closed_loop_ab_runner_skeleton.md",
        "results/logs_sample/stage14_5d_r2_closed_loop_ab_runner_skeleton_summary.json",
        "results/logs_sample/stage14_5d_r2_closed_loop_ab_runner_skeleton_patch_notes.txt",
    }
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
        "control_law_changed": False,
        "mixed_baseline_modified": False,
        "baseline_source_modified": False,
        "mujoco_closed_loop_ab_executed": False,
        "mujoco_torque_used": False,
        "ros_publisher_used": False,
        "mpc_assisted_switch_added_to_derived_runner": DERIVED_RUNNER.exists(),
        "mpc_assisted_candidate_executed": False,
        "stage14_5d_r1_pass": None if not r1 else r1.get("pass"),
        "baseline_runner": str(BASELINE_RUNNER.relative_to(ROOT)),
        "derived_runner": str(DERIVED_RUNNER.relative_to(ROOT)) if DERIVED_RUNNER.exists() else None,
        "baseline_runner_sha256": sha256_text(baseline_src) if baseline_src else None,
        "derived_runner_sha256": sha256_text(derived_text) if derived_text else None,
        "compile_error": compile_error,
        "missing_required_tokens": missing_tokens,
        "patch_notes": patch_notes,
        "git": {
            "branch": git(["branch", "--show-current"]),
            "head": git(["rev-parse", "--short", "HEAD"]),
            "status_porcelain": dirty,
            "dirty_non_stage14_5d_r2": dirty_non_stage,
        },
        "generated_files": [
            "scripts/stage14_5d_r2_derive_closed_loop_ab_runner_skeleton.py",
            "scripts/stage14_5d_r2_closed_loop_ab_runner_skeleton.py",
            "docs/stage14_5d_r2_closed_loop_ab_runner_skeleton.md",
            "results/logs_sample/stage14_5d_r2_closed_loop_ab_runner_skeleton_summary.json",
            "results/logs_sample/stage14_5d_r2_closed_loop_ab_runner_skeleton_patch_notes.txt",
        ],
        "notes": [
            "Derivation/skeleton step only.",
            "No MuJoCo rollout is executed.",
            "No A/B result is produced in R2.",
            "The original frozen mixed baseline runner is not modified.",
            "The derived runner defaults to baseline mode.",
            "MPC-assisted candidate mode is explicitly gated and intentionally not implemented in R2.",
        ],
    }

    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    doc = [
        "# Stage 14.5D-R2 Closed-loop A/B Runner Skeleton",
        "",
        "Scope: simulation-only derived runner skeleton.",
        "",
        "This step derives a new runner skeleton from the frozen mixed baseline runner and adds an explicit simulation-only control-mode switch.",
        "",
        "It does not execute MuJoCo closed-loop A/B, does not inject MPC-assisted torque candidates, does not modify the frozen mixed baseline source, and does not use ROS torque publishing.",
        "",
        "## Evidence",
        "",
        f"- Summary JSON: `{OUT_SUMMARY.relative_to(ROOT)}`",
        f"- Patch notes: `{OUT_PATCH_NOTES.relative_to(ROOT)}`",
        f"- Derived runner: `{DERIVED_RUNNER.relative_to(ROOT) if DERIVED_RUNNER.exists() else 'not generated'}`",
        "",
        "## Result",
        "",
        f"- pass: {summary['pass']}",
        f"- failed_checks: {summary['failed_checks']}",
        f"- baseline_runner: `{summary['baseline_runner']}`",
        f"- derived_runner: `{summary['derived_runner']}`",
        f"- compile_error: `{summary['compile_error']}`",
        "",
        "## Safety flags",
        "",
        f"- simulation_only_project: {summary['simulation_only_project']}",
        f"- hardware_deployment_completed: {summary['hardware_deployment_completed']}",
        f"- torque_enable_ready: {summary['torque_enable_ready']}",
        f"- torque_publisher_enabled: {summary['torque_publisher_enabled']}",
        f"- control_law_changed: {summary['control_law_changed']}",
        f"- mixed_baseline_modified: {summary['mixed_baseline_modified']}",
        f"- baseline_source_modified: {summary['baseline_source_modified']}",
        f"- mujoco_closed_loop_ab_executed: {summary['mujoco_closed_loop_ab_executed']}",
        f"- mujoco_torque_used: {summary['mujoco_torque_used']}",
        f"- ros_publisher_used: {summary['ros_publisher_used']}",
        f"- mpc_assisted_candidate_executed: {summary['mpc_assisted_candidate_executed']}",
        "",
        "## Boundary",
        "",
        "This is source derivation evidence only. It is not MPC-assisted closed-loop locomotion evidence and not hardware-readiness evidence.",
        "",
    ]
    OUT_DOC.write_text("\n".join(doc), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
