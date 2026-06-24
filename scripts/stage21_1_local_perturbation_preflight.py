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


def extract_context(text: str, patterns: list[str], radius: int = 4, limit: int = 220) -> list[str]:
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


def perturbation_cases() -> list[dict[str, object]]:
    return [
        {"perturbation_id": "nominal", "perturbation_type": "none", "perturb_x": 0.00, "perturb_y": 0.00, "perturb_yaw": 0.00},
        {"perturbation_id": "x_plus", "perturbation_type": "base_x", "perturb_x": 0.02, "perturb_y": 0.00, "perturb_yaw": 0.00},
        {"perturbation_id": "x_minus", "perturbation_type": "base_x", "perturb_x": -0.02, "perturb_y": 0.00, "perturb_yaw": 0.00},
        {"perturbation_id": "y_plus", "perturbation_type": "base_y", "perturb_x": 0.00, "perturb_y": 0.02, "perturb_yaw": 0.00},
        {"perturbation_id": "y_minus", "perturbation_type": "base_y", "perturb_x": 0.00, "perturb_y": -0.02, "perturb_yaw": 0.00},
        {"perturbation_id": "yaw_plus", "perturbation_type": "base_yaw", "perturb_x": 0.00, "perturb_y": 0.00, "perturb_yaw": 0.03},
        {"perturbation_id": "yaw_minus", "perturbation_type": "base_yaw", "perturb_x": 0.00, "perturb_y": 0.00, "perturb_yaw": -0.03},
    ]


def scale_cases() -> list[dict[str, object]]:
    return [
        {"scale": 0.000, "scale_tag": "0p000", "control_mode": "baseline"},
        {"scale": 0.010, "scale_tag": "0p010", "control_mode": "mpc_assisted_candidate"},
        {"scale": 0.020, "scale_tag": "0p020", "control_mode": "mpc_assisted_candidate"},
    ]


def main() -> int:
    root = repo_root()
    docs = root / "docs"
    logs = root / "results" / "logs_sample"
    docs.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    source_runner = root / "scripts" / "stage20_2_replay_reproducibility_runner.py"
    stage21_0_summary = logs / "stage21_0_local_robustness_roadmap_summary.json"
    stage20_3_summary = logs / "stage20_3_reproducibility_summary.json"

    validation_csv = logs / "stage21_1_local_perturbation_preflight_validation.csv"
    context_txt = logs / "stage21_1_local_perturbation_preflight_context.txt"
    plan_csv = logs / "stage21_1_local_perturbation_output_plan.csv"
    summary_json = logs / "stage21_1_local_perturbation_preflight_summary.json"
    doc = docs / "STAGE21_1_LOCAL_PERTURBATION_PREFLIGHT.md"

    text = read_text(source_runner)
    s21_0 = load_json(stage21_0_summary)
    s20_3 = load_json(stage20_3_summary)

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    check("stage21_0_summary_pass", s21_0.get("result") == "pass", f"result={s21_0.get('result')}")
    check("stage20_3_summary_pass", s20_3.get("result") == "pass", f"result={s20_3.get('result')}")
    check("stage20_3_recommendation_stable", s20_3.get("recommendation_stable") is True, f"recommendation_stable={s20_3.get('recommendation_stable')}")
    check("source_runner_exists", source_runner.is_file() and source_runner.stat().st_size > 0, str(source_runner.relative_to(root)))

    required_terms = [
        "--run-id",
        "--scale-tag",
        "--target-vx",
        "LOG_CSV_TEMPLATE",
        "SUMMARY_CSV_TEMPLATE",
        "data.qpos",
        "base_x",
        "base_y",
        "base_vx_fd",
        "mean_vx",
        "mean_abs_velocity_error",
        "forward_displacement",
        "candidate_scale",
        "max_tau_candidate_scaled_abs",
        "mujoco",
    ]

    for term in required_terms:
        check(f"source_runner_contains::{term}", term in text, term)

    # These are not used as proof of correctness, but they indicate safe injection anchors.
    has_qpos_0 = "data.qpos[0]" in text or "qpos[0]" in text
    has_qpos_1 = "data.qpos[1]" in text or "qpos[1]" in text
    has_qpos_quat = ("data.qpos[3" in text or "qpos[3" in text) and ("data.qpos[6" in text or "qpos[6" in text)

    check("has_base_x_qpos_anchor", has_qpos_0, "qpos[0] base_x anchor")
    check("has_base_y_qpos_anchor", has_qpos_1, "qpos[1] base_y anchor")
    check("has_quaternion_or_base_orientation_context", has_qpos_quat or "quat" in text.lower() or "yaw" in text.lower(), "qpos[3:7] / quat / yaw context")

    output_plan: list[dict[str, str]] = []
    for pert in perturbation_cases():
        pid = str(pert["perturbation_id"])
        ptype = str(pert["perturbation_type"])
        px = float(pert["perturb_x"])
        py = float(pert["perturb_y"])
        pyaw = float(pert["perturb_yaw"])

        for scale in scale_cases():
            scale_value = float(scale["scale"])
            scale_tag = str(scale["scale_tag"])
            mode = str(scale["control_mode"])

            output_plan.append({
                "perturbation_id": pid,
                "perturbation_type": ptype,
                "perturb_x": f"{px:.6f}",
                "perturb_y": f"{py:.6f}",
                "perturb_yaw": f"{pyaw:.6f}",
                "scale": f"{scale_value:.3f}",
                "scale_tag": scale_tag,
                "control_mode": mode,
                "log_csv": f"results/logs_sample/stage21_2_local_perturb_{pid}_{scale_tag}_{mode}_log.csv",
                "summary_csv": f"results/logs_sample/stage21_2_local_perturb_{pid}_{scale_tag}_{mode}_summary.csv",
            })

    check("planned_perturbation_count_7", len(perturbation_cases()) == 7, f"count={len(perturbation_cases())}")
    check("planned_scale_anchor_count_3", len(scale_cases()) == 3, f"count={len(scale_cases())}")
    check("planned_rollout_count_21", len(output_plan) == 21, f"count={len(output_plan)}")
    check("planned_logs_unique", len({r["log_csv"] for r in output_plan}) == len(output_plan), "unique log outputs")
    check("planned_summaries_unique", len({r["summary_csv"] for r in output_plan}) == len(output_plan), "unique summary outputs")
    check("planned_includes_nominal", any(r["perturbation_id"] == "nominal" for r in output_plan), "nominal")
    check("planned_includes_x_y_yaw_perturbations", all(
        any(r["perturbation_id"] == pid for r in output_plan)
        for pid in ["x_plus", "x_minus", "y_plus", "y_minus", "yaw_plus", "yaw_minus"]
    ), "x/y/yaw perturbations")
    check("planned_includes_recommended_0p010", any(r["scale_tag"] == "0p010" for r in output_plan), "0p010")
    check("planned_includes_regression_anchor_0p020", any(r["scale_tag"] == "0p020" for r in output_plan), "0p020")

    context_lines = extract_context(
        text,
        [
            r"LOG_CSV_TEMPLATE",
            r"SUMMARY_CSV_TEMPLATE",
            r"--run-id",
            r"--scale-tag",
            r"--target-vx",
            r"data\.qpos",
            r"qpos",
            r"base_x",
            r"base_y",
            r"base_vx_fd",
            r"mean_abs_velocity_error",
            r"forward_displacement",
            r"mujoco",
        ],
    )

    context_txt.write_text(
        "# Stage 21.1 local perturbation preflight context\n\n"
        f"source_runner: {source_runner.relative_to(root)}\n\n"
        + "\n".join(context_lines)
        + "\n",
        encoding="utf-8",
    )

    write_csv(
        plan_csv,
        output_plan,
        [
            "perturbation_id",
            "perturbation_type",
            "perturb_x",
            "perturb_y",
            "perturb_yaw",
            "scale",
            "scale_tag",
            "control_mode",
            "log_csv",
            "summary_csv",
        ],
    )

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    write_csv(validation_csv, checks, ["check", "status", "detail"])

    summary = {
        "stage": "21.1",
        "name": "recommended scale local perturbation preflight",
        "result": result,
        "failure_count": failure_count,
        "source_runner": str(source_runner.relative_to(root)),
        "planned_perturbations": perturbation_cases(),
        "scale_anchors": scale_cases(),
        "planned_rollout_count": len(output_plan),
        "output_plan": output_plan,
        "key_findings": [
            "Stage 20.2 replay runner has the required velocity and stability metrics.",
            "Stage 21.2 should derive a perturbation-specific runner instead of reusing Stage 20 filenames.",
            "Initial base_x/base_y/yaw perturbations should be injected before rollout logging and before simulation stepping.",
            "Stage 21.2 output filenames should include perturbation_id and scale_tag.",
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
            "no new perturbation rollout generated yet",
            "no real robot perturbation claim",
            "no full MPC-WBC velocity controller claim",
            "no hardware torque enablement claim",
            "no terrain or external-force robustness claim",
        ],
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    plan_md_lines = [
        "| perturbation_id | perturb_x | perturb_y | perturb_yaw | scale | control_mode | log_csv | summary_csv |",
        "|---|---:|---:|---:|---:|---|---|---|",
    ]
    for row in output_plan:
        plan_md_lines.append(
            f"| {row['perturbation_id']} | {row['perturb_x']} | {row['perturb_y']} | {row['perturb_yaw']} | {row['scale']} | {row['control_mode']} | `{row['log_csv']}` | `{row['summary_csv']}` |"
        )
    plan_md = "\n".join(plan_md_lines)

    doc.write_text(f"""# Stage 21.1：局部扰动注入预检查

## 1. 目标

Stage 21.1 检查 Stage 20.2 replay runner 是否可派生为 Stage 21 local perturbation robustness audit runner。

本阶段不运行新仿真，只检查扰动注入点、输出命名需求和 Stage 21.2 的 rollout 输出计划。

## 2. 结果

Stage 21.1 result: {result}

Failure count: {failure_count}

## 3. 关键发现

  * Stage 20.2 runner 已经记录 `target_vx`、`base_vx_fd`、`mean_vx`、`mean_abs_velocity_error`、`forward_displacement` 和稳定性边界指标。
  * Stage 21.2 应派生 perturbation-specific runner，避免复用 Stage 20 输出命名空间。
  * Stage 21.2 的输出文件名应同时包含 `perturbation_id` 和 `scale_tag`。
  * 初始状态扰动应在 rollout 开始前注入，并记录到 summary 和 per-step log 中。

## 4. Stage 21.2 输出计划

{plan_md}

## 5. 结论边界

Stage 21.1 只是预检查，不生成新 local perturbation rollout，不声明 scale=0.010 可直接用于真实机器人，也不声明完整 MPC-WBC 速度控制器完成。
""", encoding="utf-8")

    print(f"stage21_1_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"plan: {plan_csv.relative_to(root)}")
    print(f"context: {context_txt.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
