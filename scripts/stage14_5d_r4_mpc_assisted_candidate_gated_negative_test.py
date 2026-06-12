#!/usr/bin/env python3
from pathlib import Path
import datetime as dt
import json
import subprocess
from typing import List

ROOT = Path.cwd()
STAGE = "14.5D-R4"

SUMMARY_R3 = ROOT / "results/logs_sample/stage14_5d_r3_baseline_mode_derived_runner_dry_run_summary.json"
DERIVED_RUNNER = ROOT / "scripts/stage14_5d_r2_closed_loop_ab_runner_skeleton.py"

OUT_SUMMARY = ROOT / "results/logs_sample/stage14_5d_r4_mpc_assisted_candidate_gated_negative_test_summary.json"
OUT_DOC = ROOT / "docs/stage14_5d_r4_mpc_assisted_candidate_gated_negative_test.md"
OUT_STDOUT_NO_ALLOW = ROOT / "results/logs_sample/stage14_5d_r4_candidate_no_allow_stdout.txt"
OUT_STDERR_NO_ALLOW = ROOT / "results/logs_sample/stage14_5d_r4_candidate_no_allow_stderr.txt"
OUT_STDOUT_WITH_ALLOW = ROOT / "results/logs_sample/stage14_5d_r4_candidate_with_allow_stdout.txt"
OUT_STDERR_WITH_ALLOW = ROOT / "results/logs_sample/stage14_5d_r4_candidate_with_allow_stderr.txt"


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


def run_cmd(cmd: List[str], stdout_path: Path, stderr_path: Path):
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout_path": str(stdout_path.relative_to(ROOT)),
        "stderr_path": str(stderr_path.relative_to(ROOT)),
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def main() -> int:
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)

    failed_checks = []

    r3 = read_json(SUMMARY_R3)
    if not r3 or r3.get("pass") is not True:
        failed_checks.append("stage14_5d_r3_not_passed_or_missing")

    if not DERIVED_RUNNER.exists():
        failed_checks.append("derived_runner_missing")

    derived_diff_before = git(["diff", "--", str(DERIVED_RUNNER.relative_to(ROOT))])
    if derived_diff_before.strip():
        failed_checks.append("derived_runner_has_local_diff_before_test")

    no_allow = None
    with_allow = None

    if DERIVED_RUNNER.exists():
        no_allow = run_cmd(
            [
                "/usr/bin/python3",
                str(DERIVED_RUNNER.relative_to(ROOT)),
                "--control-mode",
                "mpc_assisted_candidate",
            ],
            OUT_STDOUT_NO_ALLOW,
            OUT_STDERR_NO_ALLOW,
        )

        with_allow = run_cmd(
            [
                "/usr/bin/python3",
                str(DERIVED_RUNNER.relative_to(ROOT)),
                "--control-mode",
                "mpc_assisted_candidate",
                "--allow-mpc-assisted-candidate",
            ],
            OUT_STDOUT_WITH_ALLOW,
            OUT_STDERR_WITH_ALLOW,
        )
    else:
        no_allow = {"returncode": None, "stdout": "", "stderr": ""}
        with_allow = {"returncode": None, "stdout": "", "stderr": ""}

    if no_allow["returncode"] == 0:
        failed_checks.append("candidate_without_allow_unexpectedly_succeeded")

    if "requires --allow-mpc-assisted-candidate" not in no_allow["stderr"]:
        failed_checks.append("candidate_without_allow_missing_expected_gate_message")

    if with_allow["returncode"] == 0:
        failed_checks.append("candidate_with_allow_unexpectedly_succeeded")

    if "NotImplementedError" not in with_allow["stderr"]:
        failed_checks.append("candidate_with_allow_missing_notimplemented_error")

    if "only derives the explicit switch skeleton" not in with_allow["stderr"]:
        failed_checks.append("candidate_with_allow_missing_expected_skeleton_message")

    combined_output = "\n".join([
        no_allow.get("stdout", ""),
        no_allow.get("stderr", ""),
        with_allow.get("stdout", ""),
        with_allow.get("stderr", ""),
    ])

    forbidden_success_tokens = [
        "saved_log=",
        "saved_summary=",
        "PASS",
        "pass_test",
        "baseline_mode_pass",
    ]
    forbidden_hits = [t for t in forbidden_success_tokens if t in combined_output]
    if forbidden_hits:
        failed_checks.append(f"candidate_negative_test_contains_success_tokens:{forbidden_hits}")

    derived_diff_after = git(["diff", "--", str(DERIVED_RUNNER.relative_to(ROOT))])
    if derived_diff_after.strip():
        failed_checks.append("derived_runner_has_local_diff_after_test")

    allowed_dirty = {
        "scripts/stage14_5d_r4_mpc_assisted_candidate_gated_negative_test.py",
        "docs/stage14_5d_r4_mpc_assisted_candidate_gated_negative_test.md",
        "results/logs_sample/stage14_5d_r4_mpc_assisted_candidate_gated_negative_test_summary.json",
        "results/logs_sample/stage14_5d_r4_candidate_no_allow_stdout.txt",
        "results/logs_sample/stage14_5d_r4_candidate_no_allow_stderr.txt",
        "results/logs_sample/stage14_5d_r4_candidate_with_allow_stdout.txt",
        "results/logs_sample/stage14_5d_r4_candidate_with_allow_stderr.txt",
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
        "derived_runner_source_modified": False,
        "mujoco_closed_loop_baseline_mode_executed": False,
        "mujoco_closed_loop_ab_executed": False,
        "mujoco_sim_data_ctrl_used": False,
        "mpc_assisted_candidate_executed": False,
        "mpc_assisted_candidate_safely_rejected": len(failed_checks) == 0,
        "stage14_5d_r3_pass": None if not r3 else r3.get("pass"),
        "derived_runner": str(DERIVED_RUNNER.relative_to(ROOT)),
        "negative_tests": {
            "candidate_without_allow": {
                "cmd": no_allow.get("cmd"),
                "returncode": no_allow.get("returncode"),
                "expected_nonzero": True,
                "expected_message": "requires --allow-mpc-assisted-candidate",
                "stdout_path": no_allow.get("stdout_path"),
                "stderr_path": no_allow.get("stderr_path"),
            },
            "candidate_with_allow": {
                "cmd": with_allow.get("cmd"),
                "returncode": with_allow.get("returncode"),
                "expected_nonzero": True,
                "expected_message": "NotImplementedError: Stage 14.5D-R2 only derives the explicit switch skeleton",
                "stdout_path": with_allow.get("stdout_path"),
                "stderr_path": with_allow.get("stderr_path"),
            },
        },
        "forbidden_success_token_hits": forbidden_hits,
        "git": {
            "branch": git(["branch", "--show-current"]),
            "head": git(["rev-parse", "--short", "HEAD"]),
            "status_porcelain": dirty,
            "dirty_non_stage14_5d_r4": dirty_non_stage,
        },
        "generated_files": [
            "scripts/stage14_5d_r4_mpc_assisted_candidate_gated_negative_test.py",
            "docs/stage14_5d_r4_mpc_assisted_candidate_gated_negative_test.md",
            "results/logs_sample/stage14_5d_r4_mpc_assisted_candidate_gated_negative_test_summary.json",
            "results/logs_sample/stage14_5d_r4_candidate_no_allow_stdout.txt",
            "results/logs_sample/stage14_5d_r4_candidate_no_allow_stderr.txt",
            "results/logs_sample/stage14_5d_r4_candidate_with_allow_stdout.txt",
            "results/logs_sample/stage14_5d_r4_candidate_with_allow_stderr.txt",
        ],
        "notes": [
            "Negative gate test only.",
            "The MPC-assisted candidate path must fail safely before rollout.",
            "No MuJoCo rollout is executed.",
            "No A/B comparison is executed.",
            "No MPC-assisted torque candidate is injected.",
            "No real robot torque command is sent.",
        ],
    }

    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    doc = [
        "# Stage 14.5D-R4 MPC-assisted Candidate Gated Negative Test",
        "",
        "Scope: simulation-only negative gate validation.",
        "",
        "This step verifies that `mpc_assisted_candidate` is safely rejected before implementation.",
        "",
        "It does not run MuJoCo rollout, does not execute A/B comparison, does not inject MPC-assisted torque candidates, and does not use ROS torque publishing.",
        "",
        "## Evidence",
        "",
        f"- Summary JSON: `{OUT_SUMMARY.relative_to(ROOT)}`",
        f"- No-allow stdout: `{OUT_STDOUT_NO_ALLOW.relative_to(ROOT)}`",
        f"- No-allow stderr: `{OUT_STDERR_NO_ALLOW.relative_to(ROOT)}`",
        f"- With-allow stdout: `{OUT_STDOUT_WITH_ALLOW.relative_to(ROOT)}`",
        f"- With-allow stderr: `{OUT_STDERR_WITH_ALLOW.relative_to(ROOT)}`",
        "",
        "## Result",
        "",
        f"- pass: {summary['pass']}",
        f"- failed_checks: {summary['failed_checks']}",
        f"- candidate_without_allow_returncode: {summary['negative_tests']['candidate_without_allow']['returncode']}",
        f"- candidate_with_allow_returncode: {summary['negative_tests']['candidate_with_allow']['returncode']}",
        f"- mpc_assisted_candidate_safely_rejected: {summary['mpc_assisted_candidate_safely_rejected']}",
        "",
        "## Boundary",
        "",
        f"- mujoco_closed_loop_ab_executed: {summary['mujoco_closed_loop_ab_executed']}",
        f"- mujoco_sim_data_ctrl_used: {summary['mujoco_sim_data_ctrl_used']}",
        f"- mpc_assisted_candidate_executed: {summary['mpc_assisted_candidate_executed']}",
        f"- real_robot_torque_commanded: {summary['real_robot_torque_commanded']}",
        "",
        "This is negative gate evidence only, not MPC-assisted closed-loop evidence.",
        "",
    ]

    OUT_DOC.write_text("\n".join(doc), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
