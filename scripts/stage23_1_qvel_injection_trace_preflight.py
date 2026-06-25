#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


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


def line_context(text: str, pattern: str, radius: int = 4) -> str:
    lines = text.splitlines()
    hits = [i for i, line in enumerate(lines) if pattern in line]
    chunks = []
    for idx in hits[:8]:
        start = max(0, idx - radius)
        end = min(len(lines), idx + radius + 1)
        chunks.append(f"--- context for {pattern!r}, line {idx + 1} ---")
        for j in range(start, end):
            chunks.append(f"{j + 1:04d}: {lines[j]}")
    return "\n".join(chunks)


def planned_trace_cases():
    return [
        {
            "trace_case_id": "nominal_0p010",
            "perturbation_id": "nominal",
            "perturbation_type": "none",
            "perturb_vx": 0.0,
            "perturb_vy": 0.0,
            "perturb_yawrate": 0.0,
            "scale": 0.010,
            "scale_tag": "0p010",
            "control_mode": "mpc_assisted_candidate",
        },
        {
            "trace_case_id": "vx_plus_0p010",
            "perturbation_id": "vx_plus",
            "perturbation_type": "base_vx",
            "perturb_vx": 0.05,
            "perturb_vy": 0.0,
            "perturb_yawrate": 0.0,
            "scale": 0.010,
            "scale_tag": "0p010",
            "control_mode": "mpc_assisted_candidate",
        },
        {
            "trace_case_id": "vx_minus_0p010",
            "perturbation_id": "vx_minus",
            "perturbation_type": "base_vx",
            "perturb_vx": -0.05,
            "perturb_vy": 0.0,
            "perturb_yawrate": 0.0,
            "scale": 0.010,
            "scale_tag": "0p010",
            "control_mode": "mpc_assisted_candidate",
        },
        {
            "trace_case_id": "vy_plus_0p010",
            "perturbation_id": "vy_plus",
            "perturbation_type": "base_vy",
            "perturb_vx": 0.0,
            "perturb_vy": 0.03,
            "perturb_yawrate": 0.0,
            "scale": 0.010,
            "scale_tag": "0p010",
            "control_mode": "mpc_assisted_candidate",
        },
        {
            "trace_case_id": "vy_minus_0p010",
            "perturbation_id": "vy_minus",
            "perturbation_type": "base_vy",
            "perturb_vx": 0.0,
            "perturb_vy": -0.03,
            "perturb_yawrate": 0.0,
            "scale": 0.010,
            "scale_tag": "0p010",
            "control_mode": "mpc_assisted_candidate",
        },
        {
            "trace_case_id": "yawrate_plus_0p010",
            "perturbation_id": "yawrate_plus",
            "perturbation_type": "base_yawrate",
            "perturb_vx": 0.0,
            "perturb_vy": 0.0,
            "perturb_yawrate": 0.05,
            "scale": 0.010,
            "scale_tag": "0p010",
            "control_mode": "mpc_assisted_candidate",
        },
        {
            "trace_case_id": "yawrate_minus_0p010",
            "perturbation_id": "yawrate_minus",
            "perturbation_type": "base_yawrate",
            "perturb_vx": 0.0,
            "perturb_vy": 0.0,
            "perturb_yawrate": -0.05,
            "scale": 0.010,
            "scale_tag": "0p010",
            "control_mode": "mpc_assisted_candidate",
        },
    ]


def main() -> int:
    root = repo_root()
    docs = root / "docs"
    logs = root / "results" / "logs_sample"
    docs.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    stage23_0_summary = logs / "stage23_0_perturbation_observability_roadmap_summary.json"
    stage22_4_summary = logs / "stage22_4_observable_perturbation_evidence_freeze_summary.json"
    stage22_runner = root / "scripts" / "stage22_2_observable_perturbation_runner.py"
    stage22_table = logs / "stage22_2_observable_perturbation_table.csv"
    stage22_variability = logs / "stage22_3_observable_perturbation_variability.csv"

    validation_csv = logs / "stage23_1_qvel_injection_trace_preflight_validation.csv"
    context_txt = logs / "stage23_1_qvel_injection_trace_preflight_context.txt"
    trace_plan_csv = logs / "stage23_1_qvel_injection_trace_plan.csv"
    summary_json = logs / "stage23_1_qvel_injection_trace_preflight_summary.json"
    doc = docs / "STAGE23_1_QVEL_INJECTION_TRACE_PREFLIGHT.md"

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    s23_0 = load_json(stage23_0_summary)
    s22_4 = load_json(stage22_4_summary)

    check("stage23_0_summary_exists", stage23_0_summary.is_file() and stage23_0_summary.stat().st_size > 0, str(stage23_0_summary.relative_to(root)))
    check("stage23_0_result_pass", s23_0.get("result") == "pass", f"result={s23_0.get('result')}")
    check("stage22_4_summary_exists", stage22_4_summary.is_file() and stage22_4_summary.stat().st_size > 0, str(stage22_4_summary.relative_to(root)))
    check("stage22_4_result_pass", s22_4.get("result") == "pass", f"result={s22_4.get('result')}")
    check("stage22_4_observable_false", s22_4.get("perturbation_metric_variability_detected") is False, f"perturbation_metric_variability_detected={s22_4.get('perturbation_metric_variability_detected')}")
    check("stage22_4_recommendation_observable_false", s22_4.get("recommendation_observable_robust") is False, f"recommendation_observable_robust={s22_4.get('recommendation_observable_robust')}")

    check("stage22_runner_exists", stage22_runner.is_file() and stage22_runner.stat().st_size > 0, str(stage22_runner.relative_to(root)))
    check("stage22_table_exists", stage22_table.is_file() and stage22_table.stat().st_size > 0, str(stage22_table.relative_to(root)))
    check("stage22_variability_exists", stage22_variability.is_file() and stage22_variability.stat().st_size > 0, str(stage22_variability.relative_to(root)))

    text = stage22_runner.read_text(encoding="utf-8") if stage22_runner.is_file() else ""

    required_runner_terms = [
        "--perturbation-id",
        "--perturbation-type",
        "--perturb-vx",
        "--perturb-vy",
        "--perturb-yawrate",
        "args.perturb_vx",
        "args.perturb_vy",
        "args.perturb_yawrate",
        "data.qvel",
        "data.qvel[0]",
        "data.qvel[1]",
        "data.qvel[5]",
        "mujoco.mj_forward",
        "mujoco.mj_step",
        "data.qpos",
        "base_x",
        "base_y",
        "base_vx_fd",
        "mean_vx",
        "mean_abs_velocity_error",
        "forward_displacement",
    ]

    for term in required_runner_terms:
        check(f"runner_contains::{term}", term in text, term)

    # These are not necessarily failures; they are diagnostic flags for Stage 23.2.
    diagnostic_flags = {
        "contains_mj_resetData": "mj_resetData" in text,
        "contains_data_qvel_zero_assignment": bool(re.search(r"data\.qvel\s*\[\s*:\s*\]\s*=", text)),
        "contains_data_qpos_zero_assignment": bool(re.search(r"data\.qpos\s*\[\s*:\s*\]\s*=", text)),
        "contains_new_MjData": "mujoco.MjData(model)" in text,
        "contains_state_reset_word": "reset" in text.lower(),
        "contains_qvel_trace_fields": "qvel_before_injection" in text or "qvel_after_injection" in text,
    }

    # Stage 23.2 should add trace fields; existing runner is not required to have them.
    check("runner_does_not_need_existing_trace_fields", True, f"contains_qvel_trace_fields={diagnostic_flags['contains_qvel_trace_fields']}")

    context_patterns = [
        "mujoco.MjData(model)",
        "data.qvel",
        "data.qpos",
        "mujoco.mj_forward",
        "mujoco.mj_step",
        "base_vx_fd",
        "perturb_vx",
        "perturb_yawrate",
        "mean_abs_velocity_error",
        "summary",
    ]

    context_parts = []
    for pattern in context_patterns:
        ctx = line_context(text, pattern)
        if ctx:
            context_parts.append(ctx)

    context_parts.append("\n--- diagnostic flags ---")
    for k, v in diagnostic_flags.items():
        context_parts.append(f"{k}: {v}")

    context_txt.write_text("\n\n".join(context_parts) + "\n", encoding="utf-8")

    trace_rows = []
    for case in planned_trace_cases():
        cid = case["trace_case_id"]
        row = {
            **case,
            "perturb_vx": f"{case['perturb_vx']:.6f}",
            "perturb_vy": f"{case['perturb_vy']:.6f}",
            "perturb_yawrate": f"{case['perturb_yawrate']:.6f}",
            "scale": f"{case['scale']:.3f}",
            "trace_csv": f"results/logs_sample/stage23_2_qvel_injection_trace_{cid}.csv",
            "summary_json": f"results/logs_sample/stage23_2_qvel_injection_trace_{cid}_summary.json",
        }
        trace_rows.append(row)

    write_csv(
        trace_plan_csv,
        trace_rows,
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
            "trace_csv",
            "summary_json",
        ],
    )

    check("planned_trace_case_count_7", len(trace_rows) == 7, f"count={len(trace_rows)}")
    check("planned_trace_includes_nominal", any(r["perturbation_id"] == "nominal" for r in trace_rows), "nominal")
    check("planned_trace_includes_vx", any(r["perturbation_id"] == "vx_plus" for r in trace_rows) and any(r["perturbation_id"] == "vx_minus" for r in trace_rows), "vx +/-")
    check("planned_trace_includes_vy", any(r["perturbation_id"] == "vy_plus" for r in trace_rows) and any(r["perturbation_id"] == "vy_minus" for r in trace_rows), "vy +/-")
    check("planned_trace_includes_yawrate", any(r["perturbation_id"] == "yawrate_plus" for r in trace_rows) and any(r["perturbation_id"] == "yawrate_minus" for r in trace_rows), "yawrate +/-")
    check("planned_trace_scale_0p010_only", all(r["scale_tag"] == "0p010" for r in trace_rows), "scale=0.010")
    check("planned_trace_outputs_unique", len({r["trace_csv"] for r in trace_rows}) == len(trace_rows), "unique trace csv")

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    write_csv(validation_csv, checks, ["check", "status", "detail"])

    summary = {
        "stage": "23.1",
        "name": "qvel injection trace preflight",
        "result": result,
        "failure_count": failure_count,
        "stage22_negative_evidence_context": {
            "observable_perturbation_pass": s22_4.get("observable_perturbation_pass"),
            "perturbation_metric_variability_detected": s22_4.get("perturbation_metric_variability_detected"),
            "recommendation_relation_stable": s22_4.get("recommendation_relation_stable"),
            "recommendation_observable_robust": s22_4.get("recommendation_observable_robust"),
        },
        "diagnostic_flags": diagnostic_flags,
        "planned_trace_cases": trace_rows,
        "stage23_2_trace_requirements": [
            "record qvel before injection",
            "record qvel immediately after injection",
            "record qvel after mujoco.mj_forward",
            "record qvel/qpos/base_x/base_y/base_vx_fd/base_vy_fd for the first several mj_step calls",
            "compare nominal against vx/vy/yawrate perturbation cases",
            "identify whether perturbation was not written, overwritten, or hidden by summary metrics",
        ],
        "generated_files": [
            str(validation_csv.relative_to(root)),
            str(context_txt.relative_to(root)),
            str(trace_plan_csv.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(doc.relative_to(root)),
        ],
        "claim_boundary": [
            "preflight only",
            "no new diagnostic rollout generated yet",
            "no observable perturbation robustness claim",
            "no full MPC-WBC velocity controller claim",
            "no real robot torque execution claim",
            "no hardware torque enablement claim",
            "no terrain or external-force robustness claim",
        ],
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    doc.write_text(f"""# Stage 23.1：qvel injection trace preflight

## 1. 目标

Stage 23.1 检查 Stage 22.2 runner 是否具备派生 qvel injection trace diagnostic 的基础条件。

本阶段不运行新仿真，只做：

  * 检查 Stage 22.4 negative evidence 是否已冻结；
  * 检查 Stage 22.2 runner 中 qvel 注入、mj_forward、mj_step 和 summary 指标相关代码；
  * 输出 Stage 23.2 trace diagnostic 的 case 计划；
  * 记录潜在状态覆盖点和 trace 需求。

## 2. 结果

Stage 23.1 result: {result}

Failure count: {failure_count}

## 3. Stage 22 negative evidence 背景

    observable_perturbation_pass={s22_4.get("observable_perturbation_pass")}
    perturbation_metric_variability_detected={s22_4.get("perturbation_metric_variability_detected")}
    recommendation_relation_stable={s22_4.get("recommendation_relation_stable")}
    recommendation_observable_robust={s22_4.get("recommendation_observable_robust")}

## 4. 诊断标志

| flag | value |
|---|---:|
""" + "\n".join(f"| {k} | {v} |" for k, v in diagnostic_flags.items()) + f"""

## 5. Stage 23.2 trace 计划

| trace_case_id | perturbation_id | perturb_vx | perturb_vy | perturb_yawrate | scale | trace_csv |
|---|---|---:|---:|---:|---:|---|
""" + "\n".join(
        f"| {r['trace_case_id']} | {r['perturbation_id']} | {r['perturb_vx']} | {r['perturb_vy']} | {r['perturb_yawrate']} | {r['scale']} | `{r['trace_csv']}` |"
        for r in trace_rows
    ) + """

## 6. Stage 23.2 必须记录的字段

Stage 23.2 应至少记录：

    qvel_before_injection
    qvel_after_injection
    qvel_after_mj_forward
    qvel_after_first_step
    qpos_before_injection
    qpos_after_first_step
    base_x
    base_y
    base_vx_fd
    base_vy_fd
    qvel_0
    qvel_1
    qvel_5
    qpos_0
    qpos_1
    qpos_2

## 7. 结论边界

Stage 23.1 只是 preflight，不新增 rollout，不声明 observable perturbation robustness，不声明完整 MPC-WBC 速度控制器完成，不涉及真实机器人和硬件 torque enablement。
""", encoding="utf-8")

    print(f"stage23_1_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"context: {context_txt.relative_to(root)}")
    print(f"trace_plan: {trace_plan_csv.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
