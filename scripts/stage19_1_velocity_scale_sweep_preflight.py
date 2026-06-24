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


def extract_context(text: str, patterns: list[str], radius: int = 3, limit: int = 160) -> list[str]:
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

    runner = root / "scripts" / "stage18_2_velocity_tracking_rollout_runner.py"
    stage19_0_summary = root / "results/logs_sample/stage19_0_velocity_aware_scale_sweep_roadmap_summary.json"
    stage18_2_summary = root / "results/logs_sample/stage18_2_velocity_tracking_rollout_summary.json"
    candidate_csv = root / "results/logs_sample/stage14_5b_offline_mpc_force_to_torque_candidates.csv"

    validation_csv = logs / "stage19_1_velocity_scale_sweep_preflight_validation.csv"
    context_txt = logs / "stage19_1_velocity_scale_sweep_preflight_context.txt"
    summary_json = logs / "stage19_1_velocity_scale_sweep_preflight_summary.json"
    doc = docs / "STAGE19_1_VELOCITY_SCALE_SWEEP_PREFLIGHT.md"

    text = read_text(runner)

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    s19_0 = load_json(stage19_0_summary)
    s18_2 = load_json(stage18_2_summary)

    check("stage19_0_summary_pass", s19_0.get("result") == "pass", f"result={s19_0.get('result')}")
    check("stage18_2_summary_pass", s18_2.get("result") == "pass", f"result={s18_2.get('result')}")
    check("runner_exists", runner.is_file() and runner.stat().st_size > 0, str(runner.relative_to(root)))
    check("candidate_csv_exists", candidate_csv.is_file() and candidate_csv.stat().st_size > 0, str(candidate_csv.relative_to(root)))

    required_terms = [
        "--target-vx",
        "base_vx_fd",
        "mean_vx",
        "mean_abs_velocity_error",
        "forward_displacement",
        "CONTROL_MODE_BASELINE",
        "CONTROL_MODE_MPC_ASSISTED_CANDIDATE",
        "mpc_assisted_candidate_scale",
        "candidate_scale",
        "LOG_CSV_TEMPLATE",
        "SUMMARY_CSV_TEMPLATE",
    ]

    for term in required_terms:
        check(f"runner_contains::{term}", term in text, term)

    log_template_has_control_mode = "{control_mode}" in text
    log_template_has_scale_tag = "{scale" in text or "scale_tag" in text

    check("runner_output_uses_control_mode", log_template_has_control_mode, "expected Stage 18.2 behavior")
    check("runner_output_lacks_scale_tag", not log_template_has_scale_tag, "expected overwrite risk for direct sweep reuse")

    planned_scales = [0.0, 0.005, 0.010, 0.020, 0.050]
    planned_scale_tags = ["0p000", "0p005", "0p010", "0p020", "0p050"]

    output_plan = []
    for scale, tag in zip(planned_scales, planned_scale_tags):
        if scale == 0.0:
            mode = "baseline"
        else:
            mode = "mpc_assisted_candidate"
        output_plan.append({
            "scale": f"{scale:.3f}",
            "scale_tag": tag,
            "control_mode": mode,
            "log_csv": f"results/logs_sample/stage19_2_velocity_scale_{tag}_{mode}_log.csv",
            "summary_csv": f"results/logs_sample/stage19_2_velocity_scale_{tag}_{mode}_summary.csv",
        })

    unique_logs = len({row["log_csv"] for row in output_plan}) == len(output_plan)
    unique_summaries = len({row["summary_csv"] for row in output_plan}) == len(output_plan)

    check("planned_log_outputs_unique", unique_logs, f"count={len(output_plan)}")
    check("planned_summary_outputs_unique", unique_summaries, f"count={len(output_plan)}")
    check("planned_scales_include_stage18_scale", 0.020 in planned_scales, "scale=0.020")
    check("planned_scales_include_smaller_than_0p02", any(0.0 < s < 0.020 for s in planned_scales), str(planned_scales))
    check("planned_scales_include_larger_than_0p02", any(s > 0.020 for s in planned_scales), str(planned_scales))

    context_lines = extract_context(
        text,
        [
            r"LOG_CSV_TEMPLATE",
            r"SUMMARY_CSV_TEMPLATE",
            r"--target-vx",
            r"mpc_assisted_candidate_scale",
            r"base_vx_fd",
            r"mean_vx",
            r"summary",
            r"candidate_scale",
        ],
    )

    context_txt.write_text(
        "# Stage 19.1 velocity scale sweep preflight context\n\n"
        f"runner: {runner.relative_to(root)}\n\n"
        + "\n".join(context_lines)
        + "\n",
        encoding="utf-8",
    )

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    write_csv(validation_csv, checks, ["check", "status", "detail"])

    summary = {
        "stage": "19.1",
        "name": "velocity-aware scale sweep preflight",
        "result": result,
        "failure_count": failure_count,
        "source_runner": str(runner.relative_to(root)),
        "planned_scales": planned_scales,
        "planned_scale_tags": planned_scale_tags,
        "output_plan": output_plan,
        "key_findings": [
            "Stage 18.2 runner already records target_vx, base_vx_fd, mean_vx, mean_abs_velocity_error and forward_displacement.",
            "Stage 18.2 runner output names are based on control_mode and would overwrite files if reused directly for multiple candidate scales.",
            "Stage 19.2 should derive a scale-sweep runner with scale-tagged output filenames.",
        ],
        "generated_files": [
            str(validation_csv.relative_to(root)),
            str(context_txt.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(doc.relative_to(root)),
        ],
        "claim_boundary": [
            "preflight only",
            "no new rollout generated yet",
            "no candidate velocity improvement claim",
            "no full MPC-WBC velocity controller claim",
            "no real robot torque execution claim",
        ],
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    plan_md_lines = [
        "| scale | scale_tag | control_mode | log_csv | summary_csv |",
        "|---:|---|---|---|---|",
    ]
    for row in output_plan:
        plan_md_lines.append(
            f"| {row['scale']} | {row['scale_tag']} | {row['control_mode']} | `{row['log_csv']}` | `{row['summary_csv']}` |"
        )
    plan_md = "\n".join(plan_md_lines)

    doc.write_text(f"""# Stage 19.1：速度感知 scale sweep 预检查

## 1. 目标

Stage 19.1 检查 Stage 18.2 的 velocity tracking runner 是否可以作为 Stage 19 scale sweep 的派生源。

本阶段不运行新仿真，只检查 runner 能力、输出命名风险和 Stage 19.2 的输出计划。

## 2. 结果

Stage 19.1 result: {result}

Failure count: {failure_count}

## 3. 关键发现

  * Stage 18.2 runner 已经记录 `target_vx`、`base_vx_fd`、`mean_vx`、`mean_abs_velocity_error` 和 `forward_displacement`。
  * Stage 18.2 runner 当前输出文件名只按 `control_mode` 区分。
  * 如果直接循环多个 candidate scale，会覆盖同一个 `mpc_assisted_candidate` 输出文件。
  * Stage 19.2 应派生 scale-tagged runner，使每个 scale 独立输出 log 和 summary。

## 4. Stage 19.2 输出计划

{plan_md}

## 5. 结论边界

Stage 19.1 只是预检查，不生成新 rollout，不声明 candidate 改善速度跟踪，也不声明完整 MPC-WBC 速度控制器完成。
""", encoding="utf-8")

    print(f"stage19_1_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"context: {context_txt.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
