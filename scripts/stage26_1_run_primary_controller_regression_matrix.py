#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


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


def as_bool(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "pass"}


def tag_float(value: float) -> str:
    return f"{value:.2f}".replace("-", "m").replace(".", "p")


def newest(paths: list[Path]) -> Path | None:
    existing = [p for p in paths if p.is_file()]
    if not existing:
        return None
    return max(existing, key=lambda p: p.stat().st_mtime)


def expected_paths(logs: Path, control_mode: str, perturbation_id: str, scale_tag: str) -> tuple[Path, Path]:
    if control_mode == "primary_mpc_wbc":
        prefix = "stage25_2_primary_mpc_wbc_rollout"
    else:
        prefix = "stage25_5_stabilized_primary_mpc_wbc_rollout"

    summary = logs / f"{prefix}_{perturbation_id}_{scale_tag}_{control_mode}_summary.csv"
    log = logs / f"{prefix}_{perturbation_id}_{scale_tag}_{control_mode}_log.csv"
    return summary, log


def build_command(
    root: Path,
    logs: Path,
    control_mode: str,
    target_vx: float,
    run_id: str,
    perturbation_id: str,
    scale_tag: str,
) -> list[str]:
    if control_mode == "primary_mpc_wbc":
        runner = root / "scripts" / "stage25_2_primary_mpc_wbc_runner.py"
    else:
        runner = root / "scripts" / "stage25_5_stabilized_primary_mpc_wbc_runner.py"

    trace_csv = logs / f"stage26_1_trace_{run_id}.csv"

    cmd = [
        sys.executable,
        str(runner),
        "--control-mode",
        control_mode,
        "--mpc-assisted-candidate-scale",
        "0.0",
        "--target-vx",
        f"{target_vx:.3f}",
        "--scale-tag",
        scale_tag,
        "--run-id",
        run_id,
        "--perturbation-id",
        perturbation_id,
        "--perturbation-type",
        "none",
        "--perturb-vx",
        "0.0",
        "--perturb-vy",
        "0.0",
        "--perturb-yawrate",
        "0.0",
        "--trace-csv",
        str(trace_csv),
        "--trace-steps",
        "6",
    ]

    if control_mode == "primary_mpc_wbc":
        cmd.extend(["--allow-primary-mpc-wbc"])

    if control_mode == "stabilized_primary_mpc_wbc":
        cmd.extend(
            [
                "--allow-stabilized-primary-mpc-wbc",
                "--stabilized-primary-scale",
                "0.05",
                "--stabilized-primary-ramp-steps",
                "600",
                "--stabilized-posture-residual-scale",
                "1.0",
                "--stabilized-wbc-residual-scale",
                "1.0",
            ]
        )

    return cmd


def main() -> int:
    root = repo_root()
    logs = root / "results" / "logs_sample"
    logs.mkdir(parents=True, exist_ok=True)

    controllers = [
        "baseline",
        "primary_mpc_wbc",
        "stabilized_primary_mpc_wbc",
    ]
    target_vx_values = [0.0, 0.1, 0.2]

    matrix_rows: list[dict[str, str]] = []

    for control_mode in controllers:
        for target_vx in target_vx_values:
            vx_tag = tag_float(target_vx)
            mode_tag = (
                "base"
                if control_mode == "baseline"
                else "primary"
                if control_mode == "primary_mpc_wbc"
                else "stab"
            )
            perturbation_id = f"stage26_nominal_vx{vx_tag}"
            scale_tag = f"stage26_{mode_tag}_vx{vx_tag}"
            run_id = f"stage26_1_{mode_tag}_vx{vx_tag}"

            cmd = build_command(
                root=root,
                logs=logs,
                control_mode=control_mode,
                target_vx=target_vx,
                run_id=run_id,
                perturbation_id=perturbation_id,
                scale_tag=scale_tag,
            )

            print(f"[RUN] {run_id}")
            result = subprocess.run(
                cmd,
                cwd=root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            summary_csv, log_csv = expected_paths(
                logs=logs,
                control_mode=control_mode,
                perturbation_id=perturbation_id,
                scale_tag=scale_tag,
            )

            if not summary_csv.is_file():
                summary_csv = newest(list(logs.glob(f"*{perturbation_id}*{scale_tag}*{control_mode}*summary.csv"))) or summary_csv
            if not log_csv.is_file():
                log_csv = newest(list(logs.glob(f"*{perturbation_id}*{scale_tag}*{control_mode}*log.csv"))) or log_csv

            summary_rows = read_csv_rows(summary_csv)
            runner_summary = summary_rows[0] if summary_rows else {}

            summary_exists = summary_csv.is_file() and summary_csv.stat().st_size > 0
            log_exists = log_csv.is_file() and log_csv.stat().st_size > 0

            if control_mode == "primary_mpc_wbc":
                mode_executed = as_bool(runner_summary.get("primary_mpc_wbc_executed", ""))
                expected_stability = "expected_failure_or_unstable"
            elif control_mode == "stabilized_primary_mpc_wbc":
                mode_executed = as_bool(runner_summary.get("stabilized_primary_mpc_wbc_executed", ""))
                expected_stability = "expected_stable"
            else:
                mode_executed = summary_exists
                expected_stability = "expected_stable"

            stability_pass = as_bool(runner_summary.get("pass", ""))
            evidence_generated = summary_exists and log_exists and mode_executed

            if control_mode == "primary_mpc_wbc":
                regression_evidence_pass = evidence_generated
            else:
                regression_evidence_pass = evidence_generated and stability_pass

            row = {
                "stage": "26.1",
                "run_id": run_id,
                "control_mode": control_mode,
                "target_vx": f"{target_vx:.3f}",
                "perturbation_id": perturbation_id,
                "expected_stability": expected_stability,
                "returncode": str(result.returncode),
                "summary_exists": str(summary_exists),
                "log_exists": str(log_exists),
                "mode_executed": str(mode_executed),
                "stability_pass": str(stability_pass),
                "regression_evidence_pass": str(regression_evidence_pass),
                "qp_fail_steps": str(runner_summary.get("qp_fail_steps", "")),
                "saturation_steps": str(runner_summary.get("saturation_steps", "")),
                "max_abs_roll": str(runner_summary.get("max_abs_roll", "")),
                "max_abs_pitch": str(runner_summary.get("max_abs_pitch", "")),
                "max_tau_total_abs": str(runner_summary.get("max_tau_total_abs", "")),
                "torque_limit": str(runner_summary.get("torque_limit", "")),
                "mean_base_height": str(runner_summary.get("mean_base_height", "")),
                "min_base_height": str(runner_summary.get("min_base_height", "")),
                "mean_vx": str(runner_summary.get("mean_vx", "")),
                "vx_tracking_error": str(runner_summary.get("vx_tracking_error", "")),
                "runner_summary_csv": str(summary_csv.relative_to(root)) if summary_csv.is_file() else "",
                "runner_log_csv": str(log_csv.relative_to(root)) if log_csv.is_file() else "",
                "stdout_tail": (result.stdout or "")[-800:].replace("\n", "\\n"),
                "stderr_tail": (result.stderr or "")[-800:].replace("\n", "\\n"),
                "command": " ".join(cmd),
            }
            matrix_rows.append(row)

    matrix_csv = logs / "stage26_1_primary_controller_regression_matrix.csv"
    fieldnames = list(matrix_rows[0].keys())
    write_csv(matrix_csv, matrix_rows, fieldnames)

    by_controller: dict[str, dict[str, int]] = defaultdict(lambda: {
        "cases": 0,
        "regression_evidence_pass": 0,
        "stability_pass": 0,
        "evidence_generated": 0,
    })

    failed_cases = []

    for row in matrix_rows:
        control_mode = row["control_mode"]
        by_controller[control_mode]["cases"] += 1
        if as_bool(row["regression_evidence_pass"]):
            by_controller[control_mode]["regression_evidence_pass"] += 1
        if as_bool(row["stability_pass"]):
            by_controller[control_mode]["stability_pass"] += 1
        if as_bool(row["summary_exists"]) and as_bool(row["log_exists"]) and as_bool(row["mode_executed"]):
            by_controller[control_mode]["evidence_generated"] += 1
        if not as_bool(row["regression_evidence_pass"]):
            failed_cases.append(
                {
                    "run_id": row["run_id"],
                    "control_mode": row["control_mode"],
                    "target_vx": row["target_vx"],
                    "returncode": row["returncode"],
                    "stability_pass": row["stability_pass"],
                    "runner_summary_csv": row["runner_summary_csv"],
                    "stderr_tail": row["stderr_tail"],
                }
            )

    summary = {
        "stage": "26.1",
        "name": "interview-ready primary controller regression matrix",
        "result": "pass" if not failed_cases else "fail",
        "total_cases": len(matrix_rows),
        "controllers": controllers,
        "target_vx_values": target_vx_values,
        "by_controller": dict(by_controller),
        "failed_cases": failed_cases,
        "matrix_csv": str(matrix_csv.relative_to(root)),
        "claim_boundary": [
            "simulation-only regression matrix",
            "nominal initial state only",
            "target velocity variation only",
            "does not imply terrain robustness",
            "does not imply external-force robustness",
            "does not imply hardware torque enablement",
            "primary_mpc_wbc stability failure is treated as diagnostic evidence if rollout evidence is generated",
        ],
    }

    summary_json = logs / "stage26_1_primary_controller_regression_summary.json"
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print("")
    print(f"stage26_1_result: {summary['result']}")
    print(f"total_cases: {summary['total_cases']}")
    print(f"matrix_csv: {matrix_csv.relative_to(root)}")
    print(f"summary_json: {summary_json.relative_to(root)}")
    print(json.dumps(summary["by_controller"], indent=2, ensure_ascii=False))

    return 0 if summary["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
