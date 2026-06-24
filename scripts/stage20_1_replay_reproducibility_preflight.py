#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def extract_context(text: str, patterns: list[str], radius: int = 3, limit: int = 180) -> list[str]:
    lines = text.splitlines()
    compiled = [re.compile(p) for p in patterns]
    hits = []

    for i, line in enumerate(lines):
        if any(p.search(line) for p in compiled):
            hits.append(i)

    out = []
    seen = set()
    for i in hits:
        for j in range(max(0, i - radius), min(len(lines), i + radius + 1)):
            if j not in seen:
                seen.add(j)
                out.append(f"{j + 1}: {lines[j]}")
            if len(out) >= limit:
                return out
        out.append("")
    return out


def main() -> int:
    root = repo_root()
    docs = root / "docs"
    logs = root / "results" / "logs_sample"
    docs.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    source_runner = root / "scripts" / "stage19_2_velocity_scale_sweep_runner.py"
    stage20_0_summary = logs / "stage20_0_recommended_scale_reproducibility_roadmap_summary.json"
    stage19_3_summary = logs / "stage19_3_velocity_stability_tradeoff_summary.json"

    validation_csv = logs / "stage20_1_replay_reproducibility_preflight_validation.csv"
    context_txt = logs / "stage20_1_replay_reproducibility_preflight_context.txt"
    plan_csv = logs / "stage20_1_replay_reproducibility_output_plan.csv"
    summary_json = logs / "stage20_1_replay_reproducibility_preflight_summary.json"
    doc = docs / "STAGE20_1_REPLAY_REPRODUCIBILITY_PREFLIGHT.md"

    text = read_text(source_runner)
    s20_0 = load_json(stage20_0_summary)
    s19_3 = load_json(stage19_3_summary)

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    check("stage20_0_summary_pass", s20_0.get("result") == "pass", f"result={s20_0.get('result')}")
    check("stage19_3_summary_pass", s19_3.get("result") == "pass", f"result={s19_3.get('result')}")
    check("stage19_3_best_scale_0p010", str(s19_3.get("best_candidate_scale")) == "0.010", f"best={s19_3.get('best_candidate_scale')}")
    check("source_runner_exists", source_runner.is_file() and source_runner.stat().st_size > 0, str(source_runner.relative_to(root)))

    required_terms = [
        "--scale-tag",
        "--target-vx",
        "LOG_CSV_TEMPLATE",
        "SUMMARY_CSV_TEMPLATE",
        "base_vx_fd",
        "mean_vx",
        "mean_abs_velocity_error",
        "forward_displacement",
        "candidate_scale",
        "max_tau_candidate_scaled_abs",
        "CONTROL_MODE_BASELINE",
        "CONTROL_MODE_MPC_ASSISTED_CANDIDATE",
    ]

    for term in required_terms:
        check(f"source_runner_contains::{term}", term in text, term)

    check(
        "source_output_is_stage19_namespace",
        "stage19_2_velocity_scale_{scale_tag}_{control_mode}_log.csv" in text,
        "Stage 20.2 should derive a replay-specific output template",
    )

    replay_cases = []
    run_ids = ["run_00", "run_01", "run_02"]
    scale_cases = [
        {"scale": 0.000, "scale_tag": "0p000", "control_mode": "baseline"},
        {"scale": 0.010, "scale_tag": "0p010", "control_mode": "mpc_assisted_candidate"},
        {"scale": 0.020, "scale_tag": "0p020", "control_mode": "mpc_assisted_candidate"},
    ]

    for run_id in run_ids:
        for case in scale_cases:
            scale_tag = case["scale_tag"]
            mode = case["control_mode"]
            replay_cases.append({
                "run_id": run_id,
                "scale": f"{case['scale']:.3f}",
                "scale_tag": scale_tag,
                "control_mode": mode,
                "log_csv": f"results/logs_sample/stage20_2_replay_{run_id}_{scale_tag}_{mode}_log.csv",
                "summary_csv": f"results/logs_sample/stage20_2_replay_{run_id}_{scale_tag}_{mode}_summary.csv",
            })

    unique_logs = len({r["log_csv"] for r in replay_cases}) == len(replay_cases)
    unique_summaries = len({r["summary_csv"] for r in replay_cases}) == len(replay_cases)

    check("planned_case_count_9", len(replay_cases) == 9, f"count={len(replay_cases)}")
    check("planned_log_outputs_unique", unique_logs, f"count={len(replay_cases)}")
    check("planned_summary_outputs_unique", unique_summaries, f"count={len(replay_cases)}")
    check("planned_includes_baseline_0p000", any(r["scale_tag"] == "0p000" for r in replay_cases), "0p000")
    check("planned_includes_recommended_0p010", any(r["scale_tag"] == "0p010" for r in replay_cases), "0p010")
    check("planned_includes_regression_anchor_0p020", any(r["scale_tag"] == "0p020" for r in replay_cases), "0p020")

    context_lines = extract_context(
        text,
        [
            r"LOG_CSV_TEMPLATE",
            r"SUMMARY_CSV_TEMPLATE",
            r"--scale-tag",
            r"--target-vx",
            r"base_vx_fd",
            r"mean_vx",
            r"mean_abs_velocity_error",
            r"forward_displacement",
            r"candidate_scale",
        ],
    )

    context_txt.write_text(
        "# Stage 20.1 replay reproducibility preflight context\n\n"
        f"source_runner: {source_runner.relative_to(root)}\n\n"
        + "\n".join(context_lines)
        + "\n",
        encoding="utf-8",
    )

    write_csv(
        plan_csv,
        replay_cases,
        ["run_id", "scale", "scale_tag", "control_mode", "log_csv", "summary_csv"],
    )

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    write_csv(validation_csv, checks, ["check", "status", "detail"])

    summary = {
        "stage": "20.1",
        "name": "recommended scale replay reproducibility preflight",
        "result": result,
        "failure_count": failure_count,
        "source_runner": str(source_runner.relative_to(root)),
        "planned_run_ids": run_ids,
        "planned_scales": [0.000, 0.010, 0.020],
        "planned_case_count": len(replay_cases),
        "output_plan": replay_cases,
        "key_findings": [
            "Stage 19.2 scale-tagged runner has the required velocity and stability metrics.",
            "Stage 19.2 runner output namespace should not be reused directly for Stage 20.",
            "Stage 20.2 should derive a replay-specific runner with run_id and scale_tag in output filenames.",
        ],
        "generated_files": [
            str(validation_csv.relative_to(root)),
            str(context_txt.relative_to(root)),
            str(plan_csv.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(doc.relative_to(root)),
        ],
        "claim_boundary": [
            "preflight only",
            "no new replay rollout generated yet",
            "no full MPC-WBC velocity controller claim",
            "no real robot torque execution claim",
            "no hardware torque enablement claim",
        ],
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    plan_md_lines = [
        "| run_id | scale | scale_tag | control_mode | log_csv | summary_csv |",
        "|---|---:|---|---|---|---|",
    ]
    for row in replay_cases:
        plan_md_lines.append(
            f"| {row['run_id']} | {row['scale']} | {row['scale_tag']} | {row['control_mode']} | `{row['log_csv']}` | `{row['summary_csv']}` |"
        )
    plan_md = "\n".join(plan_md_lines)

    doc.write_text(f"""# Stage 20.1：推荐 scale replay 可复现性预检查

## 1. 目标

Stage 20.1 检查 Stage 19.2 的 scale-tagged velocity sweep runner 是否可作为 Stage 20 replay reproducibility audit 的派生源。

本阶段不运行新仿真，只检查 runner 能力、输出命名需求和 Stage 20.2 的 replay 输出计划。

## 2. 结果

Stage 20.1 result: {result}

Failure count: {failure_count}

## 3. 关键发现

  * Stage 19.2 runner 已经记录 `target_vx`、`base_vx_fd`、`mean_vx`、`mean_abs_velocity_error`、`forward_displacement` 和稳定性边界指标。
  * Stage 19.2 runner 的输出文件属于 Stage 19 命名空间，不应直接用于 Stage 20 证据。
  * Stage 20.2 应派生 replay-specific runner，在输出文件名中同时包含 `run_id` 和 `scale_tag`。
  * Stage 20.2 只 replay 三个锚点：baseline 0.000、recommended scale 0.010、regression anchor 0.020。

## 4. Stage 20.2 输出计划

{plan_md}

## 5. 结论边界

Stage 20.1 只是预检查，不生成新 replay rollout，不声明 scale=0.010 可直接用于真实机器人，也不声明完整 MPC-WBC 速度控制器完成。
""", encoding="utf-8")

    print(f"stage20_1_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"plan: {plan_csv.relative_to(root)}")
    print(f"context: {context_txt.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
