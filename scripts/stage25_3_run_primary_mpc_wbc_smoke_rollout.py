#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def newest(paths: list[Path]) -> Path | None:
    existing = [p for p in paths if p.is_file()]
    if not existing:
        return None
    return max(existing, key=lambda p: p.stat().st_mtime)


def main() -> int:
    root = repo_root()
    logs = root / "results" / "logs_sample"
    logs.mkdir(parents=True, exist_ok=True)

    runner = root / "scripts" / "stage25_2_primary_mpc_wbc_runner.py"
    s25_2_summary_path = logs / "stage25_2_primary_mpc_wbc_mode_implementation_summary.json"

    execution_csv = logs / "stage25_3_primary_mpc_wbc_smoke_execution.csv"
    execution_summary_json = logs / "stage25_3_primary_mpc_wbc_smoke_execution_summary.json"

    s25_2 = load_json(s25_2_summary_path)

    run_id = "stage25_3_primary_mpc_wbc_smoke"
    perturbation_id = "nominal"
    scale_tag = "primary"
    control_mode = "primary_mpc_wbc"

    trace_csv = logs / "stage25_3_primary_mpc_wbc_smoke_trace.csv"

    cmd = [
        sys.executable,
        str(runner),
        "--control-mode", control_mode,
        "--allow-primary-mpc-wbc",
        "--mpc-assisted-candidate-scale", "0.0",
        "--scale-tag", scale_tag,
        "--run-id", run_id,
        "--perturbation-id", perturbation_id,
        "--perturbation-type", "none",
        "--perturb-vx", "0.0",
        "--perturb-vy", "0.0",
        "--perturb-yawrate", "0.0",
        "--trace-csv", str(trace_csv),
        "--trace-steps", "12",
    ]

    result = subprocess.run(
        cmd,
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    expected_summary = logs / f"stage25_2_primary_mpc_wbc_rollout_{perturbation_id}_{scale_tag}_{control_mode}_summary.csv"
    expected_log = logs / f"stage25_2_primary_mpc_wbc_rollout_{perturbation_id}_{scale_tag}_{control_mode}_log.csv"

    summary_candidates = list(logs.glob(f"stage25_2_primary_mpc_wbc_rollout_*_{scale_tag}_{control_mode}_summary.csv"))
    log_candidates = list(logs.glob(f"stage25_2_primary_mpc_wbc_rollout_*_{scale_tag}_{control_mode}_log.csv"))

    runner_summary_csv = expected_summary if expected_summary.is_file() else newest(summary_candidates)
    runner_log_csv = expected_log if expected_log.is_file() else newest(log_candidates)

    runner_summary_csv_str = str(runner_summary_csv.relative_to(root)) if runner_summary_csv else ""
    runner_log_csv_str = str(runner_log_csv.relative_to(root)) if runner_log_csv else ""

    summary_rows = read_csv_rows(runner_summary_csv) if runner_summary_csv else []
    runner_summary = summary_rows[0] if summary_rows else {}

    runner_completed = result.returncode == 0
    runner_process_returned_stability_failure = result.returncode == 2
    summary_exists = runner_summary_csv is not None and runner_summary_csv.is_file() and runner_summary_csv.stat().st_size > 0
    log_exists = runner_log_csv is not None and runner_log_csv.is_file() and runner_log_csv.stat().st_size > 0

    primary_executed = str(runner_summary.get("primary_mpc_wbc_executed", "")).lower() == "true"
    primary_present = str(runner_summary.get("primary_mpc_wbc_mode_present", "")).lower() == "true"
    simulation_only = str(runner_summary.get("simulation_only_project", "")).lower() == "true"
    smoke_stability_pass = str(runner_summary.get("pass", "")).lower() == "true"

    def as_int(value, default=-1) -> int:
        try:
            return int(float(value))
        except Exception:
            return default

    qp_fail_steps = as_int(runner_summary.get("qp_fail_steps", -1))
    saturation_steps = as_int(runner_summary.get("saturation_steps", -1))

    execution_rows = [{
        "run_id": run_id,
        "control_mode": control_mode,
        "perturbation_id": perturbation_id,
        "command": " ".join(cmd),
        "returncode": str(result.returncode),
        "stdout_tail": (result.stdout or "")[-1500:].replace("\n", "\\n"),
        "stderr_tail": (result.stderr or "")[-1500:].replace("\n", "\\n"),
        "runner_summary_csv": runner_summary_csv_str,
        "runner_log_csv": runner_log_csv_str,
        "trace_csv": str(trace_csv.relative_to(root)) if trace_csv.is_file() else "",
    }]

    write_csv(
        execution_csv,
        execution_rows,
        ["run_id", "control_mode", "perturbation_id", "command", "returncode", "stdout_tail", "stderr_tail", "runner_summary_csv", "runner_log_csv", "trace_csv"],
    )

    # Stage 25.3 is an evidence-generation stage.
    # Return code 2 is accepted when the runner produced log/summary evidence
    # and primary_mpc_wbc was executed; it means stability failed, not that
    # the mode failed to enter the MuJoCo torque loop.
    rollout_evidence_generated = summary_exists and log_exists and primary_executed
    execution_result = "pass" if rollout_evidence_generated else "fail"

    execution_summary = {
        "stage": "25.3",
        "name": "primary_mpc_wbc smoke rollout execution",
        "result": execution_result,
        "runner_returncode": result.returncode,
        "runner_completed": runner_completed,
        "runner_process_returned_stability_failure": runner_process_returned_stability_failure,
        "rollout_evidence_generated": rollout_evidence_generated,
        "summary_exists": summary_exists,
        "log_exists": log_exists,
        "primary_mpc_wbc_mode_present": primary_present,
        "primary_mpc_wbc_executed": primary_executed,
        "simulation_only_project": simulation_only,
        "smoke_stability_pass": smoke_stability_pass,
        "qp_fail_steps": qp_fail_steps,
        "saturation_steps": saturation_steps,
        "runner_summary": runner_summary,
        "command": cmd,
        "execution_csv": str(execution_csv.relative_to(root)),
        "runner_summary_csv": runner_summary_csv_str,
        "runner_log_csv": runner_log_csv_str,
        "trace_csv": str(trace_csv.relative_to(root)) if trace_csv.is_file() else "",
        "stage25_2_result": s25_2.get("result"),
        "stage25_2_primary_mpc_wbc_mode_implemented": s25_2.get("primary_mpc_wbc_mode_implemented"),
        "claim_boundary": [
            "smoke rollout only",
            "simulation-only primary_mpc_wbc runner",
            "does not imply real robot torque execution",
            "does not imply hardware torque enablement",
            "does not imply terrain or external-force robustness",
            "does not imply production-grade MPC-WBC controller maturity",
            "returncode 2 is treated as stability-failure evidence when log/summary are generated",
        ],
    }

    execution_summary_json.write_text(json.dumps(execution_summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"stage25_3_execution_result: {execution_result}")
    print(f"runner_returncode: {result.returncode}")
    print(f"runner_completed: {runner_completed}")
    print(f"runner_process_returned_stability_failure: {runner_process_returned_stability_failure}")
    print(f"rollout_evidence_generated: {rollout_evidence_generated}")
    print(f"summary_exists: {summary_exists}")
    print(f"log_exists: {log_exists}")
    print(f"primary_mpc_wbc_executed: {primary_executed}")
    print(f"smoke_stability_pass: {smoke_stability_pass}")
    print(f"qp_fail_steps: {qp_fail_steps}")
    print(f"saturation_steps: {saturation_steps}")
    print(f"summary: {execution_summary_json.relative_to(root)}")
    print(f"runner_summary_csv: {runner_summary_csv_str}")
    print(f"runner_log_csv: {runner_log_csv_str}")

    return 0 if execution_result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
