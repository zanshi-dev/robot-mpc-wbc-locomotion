#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def perturbation_cases():
    return [
        {"id": "nominal", "type": "none", "x": 0.00, "y": 0.00, "yaw": 0.00},
        {"id": "x_plus", "type": "base_x", "x": 0.02, "y": 0.00, "yaw": 0.00},
        {"id": "x_minus", "type": "base_x", "x": -0.02, "y": 0.00, "yaw": 0.00},
        {"id": "y_plus", "type": "base_y", "x": 0.00, "y": 0.02, "yaw": 0.00},
        {"id": "y_minus", "type": "base_y", "x": 0.00, "y": -0.02, "yaw": 0.00},
        {"id": "yaw_plus", "type": "base_yaw", "x": 0.00, "y": 0.00, "yaw": 0.03},
        {"id": "yaw_minus", "type": "base_yaw", "x": 0.00, "y": 0.00, "yaw": -0.03},
    ]


def scale_cases():
    return [
        {"scale": 0.000, "tag": "0p000", "mode": "baseline"},
        {"scale": 0.010, "tag": "0p010", "mode": "mpc_assisted_candidate"},
        {"scale": 0.020, "tag": "0p020", "mode": "mpc_assisted_candidate"},
    ]


def main() -> int:
    root = repo_root()
    logs = root / "results" / "logs_sample"
    logs.mkdir(parents=True, exist_ok=True)

    runner = root / "scripts" / "stage21_2_local_perturbation_runner.py"
    execution_csv = logs / "stage21_2_local_perturbation_execution.csv"
    execution_json = logs / "stage21_2_local_perturbation_execution_summary.json"

    rows = []
    all_ok = True

    for pert in perturbation_cases():
        for scale_case in scale_cases():
            pid = pert["id"]
            ptype = pert["type"]
            px = float(pert["x"])
            py = float(pert["y"])
            pyaw = float(pert["yaw"])

            scale = float(scale_case["scale"])
            tag = scale_case["tag"]
            mode = scale_case["mode"]

            log_csv = logs / f"stage21_2_local_perturb_{pid}_{tag}_{mode}_log.csv"
            summary_csv = logs / f"stage21_2_local_perturb_{pid}_{tag}_{mode}_summary.csv"

            for p in [log_csv, summary_csv]:
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
                tag,
                "--run-id",
                pid,
                "--perturbation-id",
                pid,
                "--perturbation-type",
                ptype,
                "--perturb-x",
                f"{px:.6f}",
                "--perturb-y",
                f"{py:.6f}",
                "--perturb-yaw",
                f"{pyaw:.6f}",
                "--target-vx",
                "0.2",
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

            ok = proc.returncode == 0 and log_csv.is_file() and summary_csv.is_file()
            all_ok = all_ok and ok

            rows.append({
                "perturbation_id": pid,
                "perturbation_type": ptype,
                "perturb_x": f"{px:.6f}",
                "perturb_y": f"{py:.6f}",
                "perturb_yaw": f"{pyaw:.6f}",
                "scale": f"{scale:.3f}",
                "scale_tag": tag,
                "control_mode": mode,
                "returncode": str(proc.returncode),
                "ok": str(ok),
                "log_csv": str(log_csv.relative_to(root)),
                "summary_csv": str(summary_csv.relative_to(root)),
                "stdout_tail": proc.stdout[-500:].replace("\n", "\\n"),
                "stderr_tail": proc.stderr[-500:].replace("\n", "\\n"),
            })

            if not ok:
                print(proc.stdout)
                print(proc.stderr, file=sys.stderr)
                break

        if not all_ok:
            break

    with execution_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "perturbation_id",
                "perturbation_type",
                "perturb_x",
                "perturb_y",
                "perturb_yaw",
                "scale",
                "scale_tag",
                "control_mode",
                "returncode",
                "ok",
                "log_csv",
                "summary_csv",
                "stdout_tail",
                "stderr_tail",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "stage": "21.2-run",
        "name": "local perturbation rollout execution",
        "result": "pass" if all_ok else "fail",
        "case_count": len(rows),
        "planned_case_count": len(perturbation_cases()) * len(scale_cases()),
        "execution_csv": str(execution_csv.relative_to(root)),
        "rows": rows,
    }
    execution_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"stage21_2_execution_result: {summary['result']}")
    print(f"case_count: {len(rows)}")
    print(f"execution_csv: {execution_csv.relative_to(root)}")
    print(f"execution_summary: {execution_json.relative_to(root)}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
