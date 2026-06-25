#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    root = repo_root()
    logs = root / "results" / "logs_sample"
    plan_csv = logs / "stage23_1_qvel_injection_trace_plan.csv"
    runner = root / "scripts" / "stage23_2_qvel_injection_trace_runner.py"

    execution_csv = logs / "stage23_2_qvel_injection_trace_execution.csv"
    execution_json = logs / "stage23_2_qvel_injection_trace_execution_summary.json"

    if not plan_csv.is_file():
        raise SystemExit(f"missing trace plan: {plan_csv}")
    if not runner.is_file():
        raise SystemExit(f"missing trace runner: {runner}")

    plan_rows = read_rows(plan_csv)
    rows = []
    all_ok = True

    for case in plan_rows:
        trace_case_id = case["trace_case_id"]
        trace_csv = root / case["trace_csv"]
        case_summary_json = root / case["summary_json"]

        scale = float(case["scale"])
        mode = case["control_mode"]

        normal_log = logs / f"stage23_2_qvel_trace_rollout_{case['perturbation_id']}_{case['scale_tag']}_{mode}_log.csv"
        normal_summary = logs / f"stage23_2_qvel_trace_rollout_{case['perturbation_id']}_{case['scale_tag']}_{mode}_summary.csv"

        for p in [trace_csv, case_summary_json, normal_log, normal_summary]:
            if p.exists():
                p.unlink()

        cmd = [
            sys.executable,
            str(runner.relative_to(root)),
            "--control-mode",
            mode,
            "--mpc-assisted-candidate-scale",
            f"{scale:.3f}",
            "--scale-tag",
            case["scale_tag"],
            "--run-id",
            trace_case_id,
            "--perturbation-id",
            case["perturbation_id"],
            "--perturbation-type",
            case["perturbation_type"],
            "--perturb-vx",
            case["perturb_vx"],
            "--perturb-vy",
            case["perturb_vy"],
            "--perturb-yawrate",
            case["perturb_yawrate"],
            "--target-vx",
            "0.2",
            "--trace-csv",
            str(trace_csv.relative_to(root)),
            "--trace-steps",
            "12",
        ]

        if mode == "mpc_assisted_candidate":
            cmd.append("--allow-mpc-assisted-candidate")

        print("running:", " ".join(cmd), flush=True)

        proc = subprocess.run(
            cmd,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        ok = (
            proc.returncode == 0
            and trace_csv.is_file()
            and trace_csv.stat().st_size > 0
            and normal_log.is_file()
            and normal_summary.is_file()
        )
        all_ok = all_ok and ok

        case_summary = {
            "trace_case_id": trace_case_id,
            "result": "pass" if ok else "fail",
            "returncode": proc.returncode,
            "trace_csv": str(trace_csv.relative_to(root)),
            "normal_log_csv": str(normal_log.relative_to(root)),
            "normal_summary_csv": str(normal_summary.relative_to(root)),
            "command": cmd,
            "stdout_tail": proc.stdout[-1000:],
            "stderr_tail": proc.stderr[-1000:],
        }
        case_summary_json.write_text(json.dumps(case_summary, indent=2, ensure_ascii=False), encoding="utf-8")

        rows.append({
            "trace_case_id": trace_case_id,
            "perturbation_id": case["perturbation_id"],
            "perturbation_type": case["perturbation_type"],
            "perturb_vx": case["perturb_vx"],
            "perturb_vy": case["perturb_vy"],
            "perturb_yawrate": case["perturb_yawrate"],
            "scale": case["scale"],
            "scale_tag": case["scale_tag"],
            "control_mode": mode,
            "returncode": str(proc.returncode),
            "ok": str(ok),
            "trace_csv": str(trace_csv.relative_to(root)),
            "case_summary_json": str(case_summary_json.relative_to(root)),
            "normal_log_csv": str(normal_log.relative_to(root)),
            "normal_summary_csv": str(normal_summary.relative_to(root)),
            "stdout_tail": proc.stdout[-500:].replace("\n", "\\n"),
            "stderr_tail": proc.stderr[-500:].replace("\n", "\\n"),
        })

        if not ok:
            print(proc.stdout)
            print(proc.stderr, file=sys.stderr)
            break

    write_csv(
        execution_csv,
        rows,
        [
            "trace_case_id",
            "perturbation_id",
            "perturbation_type",
            "perturb_vx",
            "perturb_vy",
            "perturb_yawrate",
            "scale",
            "scale_tag",
            "control_mode",
            "returncode",
            "ok",
            "trace_csv",
            "case_summary_json",
            "normal_log_csv",
            "normal_summary_csv",
            "stdout_tail",
            "stderr_tail",
        ],
    )

    summary = {
        "stage": "23.2-run",
        "name": "qvel injection trace diagnostic execution",
        "result": "pass" if all_ok else "fail",
        "case_count": len(rows),
        "planned_case_count": len(plan_rows),
        "execution_csv": str(execution_csv.relative_to(root)),
        "rows": rows,
    }
    execution_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"stage23_2_execution_result: {summary['result']}")
    print(f"case_count: {len(rows)}")
    print(f"execution_csv: {execution_csv.relative_to(root)}")
    print(f"execution_summary: {execution_json.relative_to(root)}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
