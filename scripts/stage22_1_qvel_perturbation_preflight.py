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


def extract_context(text: str, patterns: list[str], radius: int = 5, limit: int = 260) -> list[str]:
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
        {"perturbation_id": "nominal", "perturbation_type": "none", "perturb_vx": 0.00, "perturb_vy": 0.00, "perturb_yawrate": 0.00},
        {"perturbation_id": "vx_plus", "perturbation_type": "base_vx", "perturb_vx": 0.05, "perturb_vy": 0.00, "perturb_yawrate": 0.00},
        {"perturbation_id": "vx_minus", "perturbation_type": "base_vx", "perturb_vx": -0.05, "perturb_vy": 0.00, "perturb_yawrate": 0.00},
        {"perturbation_id": "vy_plus", "perturbation_type": "base_vy", "perturb_vx": 0.00, "perturb_vy": 0.03, "perturb_yawrate": 0.00},
        {"perturbation_id": "vy_minus", "perturbation_type": "base_vy", "perturb_vx": 0.00, "perturb_vy": -0.03, "perturb_yawrate": 0.00},
        {"perturbation_id": "yawrate_plus", "perturbation_type": "base_yawrate", "perturb_vx": 0.00, "perturb_vy": 0.00, "perturb_yawrate": 0.05},
        {"perturbation_id": "yawrate_minus", "perturbation_type": "base_yawrate", "perturb_vx": 0.00, "perturb_vy": 0.00, "perturb_yawrate": -0.05},
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
    backup_source_runner = root / "scripts" / "stage21_2_local_perturbation_runner.py"

    stage22_0_summary = logs / "stage22_0_observable_perturbation_roadmap_summary.json"
    stage21_4_summary = logs / "stage21_4_local_robustness_evidence_freeze_summary.json"

    validation_csv = logs / "stage22_1_qvel_perturbation_preflight_validation.csv"
    context_txt = logs / "stage22_1_qvel_perturbation_preflight_context.txt"
    plan_csv = logs / "stage22_1_qvel_perturbation_output_plan.csv"
    summary_json = logs / "stage22_1_qvel_perturbation_preflight_summary.json"
    doc = docs / "STAGE22_1_QVEL_PERTURBATION_PREFLIGHT.md"

    text = read_text(source_runner)
    backup_text = read_text(backup_source_runner)

    s22_0 = load_json(stage22_0_summary)
    s21_4 = load_json(stage21_4_summary)

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    check("stage22_0_summary_pass", s22_0.get("result") == "pass", f"result={s22_0.get('result')}")
    check("stage21_4_summary_pass", s21_4.get("result") == "pass", f"result={s21_4.get('result')}")
    check("source_runner_exists", source_runner.is_file() and source_runner.stat().st_size > 0, str(source_runner.relative_to(root)))
    check("backup_stage21_runner_exists", backup_source_runner.is_file() and backup_source_runner.stat().st_size > 0, str(backup_source_runner.relative_to(root)))

    required_terms = [
        "--run-id",
        "--scale-tag",
        "--target-vx",
        "LOG_CSV_TEMPLATE",
        "SUMMARY_CSV_TEMPLATE",
        "data = mujoco.MjData(model)",
        "mujoco.mj_step",
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

    qvel_in_source = "data.qvel" in text or "qvel" in text
    check("source_qvel_reference_optional", True, f"qvel_reference_present={qvel_in_source}")

    # Stage 22 runner can add qvel writes even if the source runner did not log qvel.
    check("qvel_injection_possible_via_mjdata", "data = mujoco.MjData(model)" in text, "MjData exposes data.qvel")
    check("qvel_injection_before_rollout_possible", "data = mujoco.MjData(model)" in text and "mujoco.mj_step" in text, "inject qvel after MjData creation and before rollout stepping; Stage 22.2 runner will add mj_forward after qvel modification")

    output_plan: list[dict[str, str]] = []
    for pert in perturbation_cases():
        pid = str(pert["perturbation_id"])
        ptype = str(pert["perturbation_type"])
        pvx = float(pert["perturb_vx"])
        pvy = float(pert["perturb_vy"])
        pyawrate = float(pert["perturb_yawrate"])

        for scale in scale_cases():
            scale_value = float(scale["scale"])
            scale_tag = str(scale["scale_tag"])
            mode = str(scale["control_mode"])

            output_plan.append({
                "perturbation_id": pid,
                "perturbation_type": ptype,
                "perturb_vx": f"{pvx:.6f}",
                "perturb_vy": f"{pvy:.6f}",
                "perturb_yawrate": f"{pyawrate:.6f}",
                "scale": f"{scale_value:.3f}",
                "scale_tag": scale_tag,
                "control_mode": mode,
                "log_csv": f"results/logs_sample/stage22_2_observable_perturb_{pid}_{scale_tag}_{mode}_log.csv",
                "summary_csv": f"results/logs_sample/stage22_2_observable_perturb_{pid}_{scale_tag}_{mode}_summary.csv",
            })

    check("planned_perturbation_count_7", len(perturbation_cases()) == 7, f"count={len(perturbation_cases())}")
    check("planned_scale_anchor_count_3", len(scale_cases()) == 3, f"count={len(scale_cases())}")
    check("planned_rollout_count_21", len(output_plan) == 21, f"count={len(output_plan)}")
    check("planned_logs_unique", len({r["log_csv"] for r in output_plan}) == len(output_plan), "unique log outputs")
    check("planned_summaries_unique", len({r["summary_csv"] for r in output_plan}) == len(output_plan), "unique summary outputs")
    check("planned_includes_nominal", any(r["perturbation_id"] == "nominal" for r in output_plan), "nominal")
    check("planned_includes_vx_vy_yawrate_perturbations", all(
        any(r["perturbation_id"] == pid for r in output_plan)
        for pid in ["vx_plus", "vx_minus", "vy_plus", "vy_minus", "yawrate_plus", "yawrate_minus"]
    ), "vx/vy/yawrate perturbations")
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
            r"MjData",
            r"mj_forward",
            r"mj_step",
            r"data\.qpos",
            r"data\.qvel",
            r"base_x",
            r"base_y",
            r"base_vx_fd",
            r"mean_abs_velocity_error",
            r"forward_displacement",
            r"candidate_scale",
        ],
    )

    backup_context_lines = extract_context(
        backup_text,
        [
            r"perturbation_id",
            r"perturb_x",
            r"perturb_y",
            r"perturb_yaw",
            r"_apply_initial_perturbation",
            r"data\.qpos",
            r"mj_forward",
        ],
        radius=3,
        limit=80,
    )

    context_txt.write_text(
        "# Stage 22.1 qvel perturbation preflight context\n\n"
        f"source_runner: {source_runner.relative_to(root)}\n"
        f"backup_stage21_runner: {backup_source_runner.relative_to(root)}\n\n"
        "## Source runner context\n\n"
        + "\n".join(context_lines)
        + "\n\n## Stage 21 perturbation runner context\n\n"
        + "\n".join(backup_context_lines)
        + "\n",
        encoding="utf-8",
    )

    write_csv(
        plan_csv,
        output_plan,
        [
            "perturbation_id",
            "perturbation_type",
            "perturb_vx",
            "perturb_vy",
            "perturb_yawrate",
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
        "stage": "22.1",
        "name": "observable qvel perturbation preflight",
        "result": result,
        "failure_count": failure_count,
        "source_runner": str(source_runner.relative_to(root)),
        "backup_stage21_runner": str(backup_source_runner.relative_to(root)),
        "qvel_reference_present_in_source": qvel_in_source,
        "planned_perturbations": perturbation_cases(),
        "scale_anchors": scale_cases(),
        "planned_rollout_count": len(output_plan),
        "output_plan": output_plan,
        "qvel_injection_plan": [
            "derive Stage 22.2 runner from Stage 20.2 replay runner",
            "add --perturbation-id / --perturbation-type / --perturb-vx / --perturb-vy / --perturb-yawrate",
            "inject velocity perturbations after mujoco.MjData(model) and before rollout logging / stepping",
            "use data.qvel[0] += perturb_vx when available",
            "use data.qvel[1] += perturb_vy when available",
            "use data.qvel[5] += perturb_yawrate when qvel has at least 6 elements",
            "Stage 22.2 derived runner should add mujoco.mj_forward(model, data) after qvel modification",
            "record perturb_vx / perturb_vy / perturb_yawrate in per-step log and summary CSV",
        ],
        "key_findings": [
            "Stage 20.2 runner has the required velocity and stability metrics.",
            "Stage 22.2 should derive an observable-perturbation-specific runner instead of reusing Stage 20 or Stage 21 filenames.",
            "Initial qvel perturbations can be injected through MuJoCo MjData before rollout stepping.",
            "Stage 22.3 must explicitly check perturbation_metric_variability_detected; without observable metric variation, Stage 22 cannot support observable robustness claims.",
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
            "no new observable perturbation rollout generated yet",
            "qvel index semantics are treated as simulation-only MuJoCo free-joint perturbation anchors",
            "no real robot perturbation claim",
            "no full MPC-WBC velocity controller claim",
            "no hardware torque enablement claim",
            "no terrain or external-force robustness claim",
        ],
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    plan_md_lines = [
        "| perturbation_id | perturb_vx | perturb_vy | perturb_yawrate | scale | control_mode | log_csv | summary_csv |",
        "|---|---:|---:|---:|---:|---|---|---|",
    ]
    for row in output_plan:
        plan_md_lines.append(
            f"| {row['perturbation_id']} | {row['perturb_vx']} | {row['perturb_vy']} | {row['perturb_yawrate']} | {row['scale']} | {row['control_mode']} | `{row['log_csv']}` | `{row['summary_csv']}` |"
        )
    plan_md = "\n".join(plan_md_lines)

    doc.write_text(f"""# Stage 22.1：qvel 可观测扰动注入预检查

## 1. 目标

Stage 22.1 检查 Stage 20.2 replay runner 是否可派生为 Stage 22 observable perturbation robustness audit runner。

本阶段不运行新仿真，只检查 qvel 初始速度扰动注入点、输出命名需求和 Stage 22.2 的 rollout 输出计划。

## 2. 结果

Stage 22.1 result: {result}

Failure count: {failure_count}

## 3. 关键发现

  * Stage 20.2 runner 已经记录 `target_vx`、`base_vx_fd`、`mean_vx`、`mean_abs_velocity_error`、`forward_displacement` 和稳定性边界指标。
  * Stage 22.2 应派生 observable-perturbation-specific runner，避免复用 Stage 20 或 Stage 21 输出命名空间。
  * Stage 22.2 的输出文件名应同时包含 `perturbation_id` 和 `scale_tag`。
  * 初始速度扰动应在 `mujoco.MjData(model)` 创建后、rollout 开始前注入。
  * Stage 22.2 派生 runner 应新增 `mujoco.mj_forward(model, data)`，用于 qvel 修改后的状态同步。
  * Stage 22.3 必须检查 `perturbation_metric_variability_detected`，否则不能声明 observable perturbation robustness。

## 4. qvel 注入计划

    data.qvel[0] += perturb_vx
    data.qvel[1] += perturb_vy
    data.qvel[5] += perturb_yawrate

边界说明：

    这些 qvel index 只作为 MuJoCo free-joint simulation-only 初始速度扰动 anchor。
    不对应真实机器人速度扰动接口。
    不对应硬件扰动测试。

## 5. Stage 22.2 输出计划

{plan_md}

## 6. 结论边界

Stage 22.1 只是预检查，不生成新 observable perturbation rollout，不声明 scale=0.010 可直接用于真实机器人，也不声明完整 MPC-WBC 速度控制器完成。
""", encoding="utf-8")

    print(f"stage22_1_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"plan: {plan_csv.relative_to(root)}")
    print(f"context: {context_txt.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
