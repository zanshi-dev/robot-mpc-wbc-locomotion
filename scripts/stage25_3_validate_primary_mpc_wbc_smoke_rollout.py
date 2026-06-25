#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
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


def main() -> int:
    root = repo_root()
    docs = root / "docs"
    logs = root / "results" / "logs_sample"
    docs.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    execution_summary_path = logs / "stage25_3_primary_mpc_wbc_smoke_execution_summary.json"
    execution_csv = logs / "stage25_3_primary_mpc_wbc_smoke_execution.csv"
    s25_2_summary_path = logs / "stage25_2_primary_mpc_wbc_mode_implementation_summary.json"

    validation_csv = logs / "stage25_3_primary_mpc_wbc_smoke_validation.csv"
    summary_json = logs / "stage25_3_primary_mpc_wbc_smoke_summary.json"
    doc = docs / "STAGE25_3_PRIMARY_MPC_WBC_SMOKE_ROLLOUT.md"

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail})

    s25_2 = load_json(s25_2_summary_path)
    exe = load_json(execution_summary_path)

    check("stage25_2_summary_exists", s25_2_summary_path.is_file() and s25_2_summary_path.stat().st_size > 0, str(s25_2_summary_path.relative_to(root)))
    check("stage25_2_result_pass", s25_2.get("result") == "pass", f"result={s25_2.get('result')}")
    check("stage25_2_primary_implemented", s25_2.get("primary_mpc_wbc_mode_implemented") is True, str(s25_2.get("primary_mpc_wbc_mode_implemented")))

    check("execution_summary_exists", execution_summary_path.is_file() and execution_summary_path.stat().st_size > 0, str(execution_summary_path.relative_to(root)))
    check("execution_csv_exists", execution_csv.is_file() and execution_csv.stat().st_size > 0, str(execution_csv.relative_to(root)))

    check("execution_result_pass", exe.get("result") == "pass", f"result={exe.get('result')}")
    check("rollout_evidence_generated", exe.get("rollout_evidence_generated") is True, str(exe.get("rollout_evidence_generated")))
    check("runner_summary_exists", exe.get("summary_exists") is True, str(exe.get("summary_exists")))
    check("runner_log_exists", exe.get("log_exists") is True, str(exe.get("log_exists")))
    check("primary_mpc_wbc_executed", exe.get("primary_mpc_wbc_executed") is True, str(exe.get("primary_mpc_wbc_executed")))
    check("simulation_only_project", exe.get("simulation_only_project") is True, str(exe.get("simulation_only_project")))

    runner_summary_csv = root / exe.get("runner_summary_csv", "")
    runner_log_csv = root / exe.get("runner_log_csv", "")

    runner_summary_rows = read_csv_rows(runner_summary_csv)
    runner_log_rows = read_csv_rows(runner_log_csv)

    check("runner_summary_csv_exists", runner_summary_csv.is_file() and runner_summary_csv.stat().st_size > 0, str(runner_summary_csv.relative_to(root)) if runner_summary_csv.exists() else str(runner_summary_csv))
    check("runner_log_csv_exists", runner_log_csv.is_file() and runner_log_csv.stat().st_size > 0, str(runner_log_csv.relative_to(root)) if runner_log_csv.exists() else str(runner_log_csv))
    check("runner_summary_one_row", len(runner_summary_rows) == 1, f"rows={len(runner_summary_rows)}")
    check("runner_log_nonempty", len(runner_log_rows) > 0, f"rows={len(runner_log_rows)}")

    runner_summary = runner_summary_rows[0] if runner_summary_rows else {}

    required_fields = [
        "control_mode",
        "primary_mpc_wbc_mode_present",
        "primary_mpc_wbc_executed",
        "primary_mpc_wbc_simulation_only",
        "candidate_available_in_run",
        "max_tau_primary_mpc_wbc_raw_abs",
        "max_tau_total_abs",
        "qp_fail_steps",
        "saturation_steps",
        "pass",
    ]

    for field in required_fields:
        check(f"summary_has::{field}", field in runner_summary, field)

    smoke_stability_pass = str(runner_summary.get("pass", "")).lower() == "true"

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    write_csv(validation_csv, checks, ["check", "status", "detail"])

    summary = {
        "stage": "25.3",
        "name": "primary_mpc_wbc smoke rollout validation",
        "result": result,
        "failure_count": failure_count,
        "primary_mpc_wbc_executed": exe.get("primary_mpc_wbc_executed"),
        "rollout_evidence_generated": exe.get("rollout_evidence_generated"),
        "runner_returncode": exe.get("runner_returncode"),
        "runner_process_returned_stability_failure": exe.get("runner_process_returned_stability_failure"),
        "smoke_stability_pass": smoke_stability_pass,
        "runner_summary": runner_summary,
        "runner_log_row_count": len(runner_log_rows),
        "runner_summary_csv": exe.get("runner_summary_csv"),
        "runner_log_csv": exe.get("runner_log_csv"),
        "execution_summary": str(execution_summary_path.relative_to(root)),
        "generated_files": [
            str(validation_csv.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(doc.relative_to(root)),
        ],
        "claim_boundary": [
            "smoke rollout evidence",
            "simulation-only",
            "stability pass recorded separately",
            "no real robot torque execution",
            "no hardware torque enablement",
            "no terrain or external-force robustness",
        ],
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    doc.write_text(f"""# Stage 25.3：primary_mpc_wbc smoke rollout

## 1. 目标

Stage 25.3 运行 simulation-only `primary_mpc_wbc` smoke rollout，验证 Stage 25.2 新增的控制模式是否能进入 MuJoCo torque loop。

本阶段不做真实机器人实验，不做硬件 torque enablement。

## 2. 结果

Stage 25.3 result: {result}

Failure count: {failure_count}

primary_mpc_wbc_executed: {exe.get("primary_mpc_wbc_executed")}

rollout_evidence_generated: {exe.get("rollout_evidence_generated")}

runner_returncode: {exe.get("runner_returncode")}

runner_process_returned_stability_failure: {exe.get("runner_process_returned_stability_failure")}

smoke_stability_pass: {smoke_stability_pass}

runner_log_row_count: {len(runner_log_rows)}

runner_summary_csv:

    {exe.get("runner_summary_csv")}

runner_log_csv:

    {exe.get("runner_log_csv")}

## 3. 关键 summary

{json.dumps(runner_summary, indent=2, ensure_ascii=False)}

## 4. 当前支持的表述

Stage 25.3 支持：

    primary_mpc_wbc 模式已被实际执行；
    MPC/WBC candidate torque 已作为 primary stance torque 进入 simulation-only MuJoCo torque loop；
    swing leg PD 和 torque safety filter 仍在链路中；
    已生成 smoke rollout log / summary 证据；
    当前 smoke_stability_pass=False，说明 primary_mpc_wbc 直接主控模式尚未稳定。

## 5. 当前不支持的表述

Stage 25.3 不支持：

  * 不支持真实机器人闭环；
  * 不支持 hardware torque enablement；
  * 不支持复杂地形或外力冲击鲁棒性；
  * 如果 smoke_stability_pass=False，则不支持 primary_mpc_wbc 已稳定闭环运行。
""", encoding="utf-8")

    print(f"stage25_3_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"primary_mpc_wbc_executed: {exe.get('primary_mpc_wbc_executed')}")
    print(f"smoke_stability_pass: {smoke_stability_pass}")
    print(f"runner_log_row_count: {len(runner_log_rows)}")
    print(f"summary: {summary_json.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
