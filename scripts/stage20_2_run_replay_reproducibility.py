#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def replay_cases() -> list[dict[str, object]]:
    cases = []
    for run_id in ["run_00", "run_01", "run_02"]:
        cases.extend([
            {"run_id": run_id, "scale": 0.000, "tag": "0p000", "mode": "baseline"},
            {"run_id": run_id, "scale": 0.010, "tag": "0p010", "mode": "mpc_assisted_candidate"},
            {"run_id": run_id, "scale": 0.020, "tag": "0p020", "mode": "mpc_assisted_candidate"},
        ])
    return cases


def main() -> int:
    root = repo_root()
    logs = root / "results" / "logs_sample"
    logs.mkdir(parents=True, exist_ok=True)

    runner = root / "scripts" / "stage20_2_replay_reproducibility_runner.py"
    execution_csv = logs / "stage20_2_replay_reproducibility_execution.csv"
    execution_json = logs / "stage20_2_replay_reproducibility_execution_summary.json"

    rows = []
    all_ok = True

    for case in replay_cases():
        run_id = str(case["run_id"])
        scale = float(case["scale"])
        tag = str(case["tag"])
        mode = str(case["mode"])

        log_csv = logs / f"stage20_2_replay_{run_id}_{tag}_{mode}_log.csv"
        summary_csv = logs / f"stage20_2_replay_{run_id}_{tag}_{mode}_summary.csv"

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
            run_id,
            "--target-vx",
            "0.2",
        ]

        if mode == "mpc_assisted_candidate":
            cmd.extend(["--allow-mpc-assisted-candidate"])

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
            "run_id": run_id,
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

    with execution_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "run_id",
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
        "stage": "20.2-run",
        "name": "recommended scale replay reproducibility execution",
        "result": "pass" if all_ok else "fail",
        "case_count": len(rows),
        "planned_case_count": len(replay_cases()),
        "execution_csv": str(execution_csv.relative_to(root)),
        "rows": rows,
    }
    execution_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"stage20_2_execution_result: {summary['result']}")
    print(f"case_count: {len(rows)}")
    print(f"execution_csv: {execution_csv.relative_to(root)}")
    print(f"execution_summary: {execution_json.relative_to(root)}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
