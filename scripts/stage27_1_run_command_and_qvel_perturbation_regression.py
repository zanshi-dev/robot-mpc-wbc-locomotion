#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def as_bool(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "pass"}


def tag_float(value: float) -> str:
    return f"{value:.2f}".replace("-", "m").replace(".", "p")


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


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


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
    perturbation: dict[str, object],
    run_id: str,
    perturbation_id: str,
    scale_tag: str,
) -> list[str]:
    if control_mode == "primary_mpc_wbc":
        runner = root / "scripts" / "stage25_2_primary_mpc_wbc_runner.py"
    else:
        runner = root / "scripts" / "stage25_5_stabilized_primary_mpc_wbc_runner.py"

    trace_csv = logs / f"stage27_1_trace_{run_id}.csv"

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
        str(perturbation["type"]),
        "--perturb-vx",
        f"{float(perturbation['vx']):.6f}",
        "--perturb-vy",
        f"{float(perturbation['vy']):.6f}",
        "--perturb-yawrate",
        f"{float(perturbation['yawrate']):.6f}",
        "--trace-csv",
        str(trace_csv),
        "--trace-steps",
        "24",
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


def to_float(row: dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        value = row.get(key, "")
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def audit_transition_window(log_csv: Path, window: int = 10) -> dict[str, str]:
    rows = read_csv_rows(log_csv)
    if not rows:
        return {
            "transition_count_log": "",
            "near_transition_window_steps": str(window),
            "near_transition_row_count": "0",
            "max_tau_total_abs_near_transition": "",
            "max_tau_step_jump_abs_near_transition": "",
            "max_tau_step_jump_norm_near_transition": "",
            "max_abs_roll_near_transition": "",
            "max_abs_pitch_near_transition": "",
            "min_z_near_transition": "",
            "saturation_steps_near_transition": "",
        }

    transition_steps = [
        int(float(row["step"]))
        for row in rows
        if as_bool(row.get("is_transition", ""))
    ]

    near_rows = []
    for row in rows:
        step = int(float(row.get("step", "0")))
        if any(abs(step - t) <= window for t in transition_steps):
            near_rows.append(row)

    if not near_rows:
        return {
            "transition_count_log": str(len(transition_steps)),
            "near_transition_window_steps": str(window),
            "near_transition_row_count": "0",
            "max_tau_total_abs_near_transition": "",
            "max_tau_step_jump_abs_near_transition": "",
            "max_tau_step_jump_norm_near_transition": "",
            "max_abs_roll_near_transition": "",
            "max_abs_pitch_near_transition": "",
            "min_z_near_transition": "",
            "saturation_steps_near_transition": "0",
        }

    return {
        "transition_count_log": str(len(transition_steps)),
        "near_transition_window_steps": str(window),
        "near_transition_row_count": str(len(near_rows)),
        "max_tau_total_abs_near_transition": f"{max(to_float(r, 'tau_total_abs') for r in near_rows):.12f}",
        "max_tau_step_jump_abs_near_transition": f"{max(to_float(r, 'tau_step_jump_abs') for r in near_rows):.12f}",
        "max_tau_step_jump_norm_near_transition": f"{max(to_float(r, 'tau_step_jump_norm') for r in near_rows):.12f}",
        "max_abs_roll_near_transition": f"{max(abs(to_float(r, 'roll')) for r in near_rows):.12f}",
        "max_abs_pitch_near_transition": f"{max(abs(to_float(r, 'pitch')) for r in near_rows):.12f}",
        "min_z_near_transition": f"{min(to_float(r, 'base_z') for r in near_rows):.12f}",
        "saturation_steps_near_transition": str(sum(1 for r in near_rows if as_bool(r.get("saturated", "")))),
    }


def mode_tag(control_mode: str) -> str:
    if control_mode == "baseline":
        return "base"
    if control_mode == "primary_mpc_wbc":
        return "primary"
    if control_mode == "stabilized_primary_mpc_wbc":
        return "stab"
    return control_mode.replace("_", "")


def make_doc(summary: dict[str, object], matrix_csv: Path, summary_json: Path, doc_path: Path, root: Path) -> None:
    by_controller = summary["by_controller"]

    lines = [
        "# Stage 27.1 命令速度与初始速度扰动回归矩阵",
        "",
        "本阶段在 Stage 26.1 控制模式回归矩阵基础上，扩展速度命令与初始 qvel/yawrate 扰动组合。",
        "",
        "该阶段目标是记录三种控制模式在固定 MuJoCo 仿真设置下的行为差异：",
        "",
        "- baseline",
        "- `primary_mpc_wbc`",
        "- `stabilized_primary_mpc_wbc`",
        "",
        "## 1. 验证范围",
        "",
        "- 速度命令变化：`target_vx` 小范围扫描；",
        "- 初始速度扰动：`perturb_vx`、`perturb_vy`、`perturb_yawrate`；",
        "- 接触切换窗口审计：统计接触模式切换前后 torque jump、roll、pitch、base_z 和 saturation。",
        "",
        "本阶段不修改底层控制律，不新增真实机器人接口，不声明复杂地形、外力扰动或硬件部署鲁棒性。",
        "",
        "## 2. 汇总结果",
        "",
        f"- result: `{summary['result']}`",
        f"- total_cases: `{summary['total_cases']}`",
        f"- matrix_csv: `{matrix_csv.relative_to(root)}`",
        f"- summary_json: `{summary_json.relative_to(root)}`",
        "",
        "| control_mode | cases | evidence_generated | stability_pass | regression_evidence_pass |",
        "|---|---:|---:|---:|---:|",
    ]

    for controller, item in by_controller.items():
        lines.append(
            f"| `{controller}` | {item['cases']} | {item['evidence_generated']} | "
            f"{item['stability_pass']} | {item['regression_evidence_pass']} |"
        )

    lines.extend(
        [
            "",
            "## 3. 判断规则",
            "",
            "- `baseline` 和 `stabilized_primary_mpc_wbc`：需要生成 summary/log，且稳定性检查通过。",
            "- `primary_mpc_wbc`：直接主控已知可能不稳定，因此只要求生成闭环执行证据；稳定性失败作为诊断证据保留。",
            "",
            "## 4. 结论边界",
            "",
            "本阶段只能说明：在固定 MuJoCo 仿真设置下，项目已经补充速度命令与初始速度扰动维度下的控制模式回归证据。",
            "",
            "不能说明：",
            "",
            "- 真实机器人部署完成；",
            "- 硬件力矩使能安全；",
            "- 复杂地形鲁棒；",
            "- 外力扰动鲁棒；",
            "- `stabilized_primary_mpc_wbc` 已经达到工程级成熟 locomotion controller。",
            "",
        ]
    )

    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="run larger Stage 27.1 matrix")
    args = parser.parse_args()

    root = repo_root()
    logs = root / "results" / "logs_sample"
    docs = root / "docs"
    logs.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)

    controllers = [
        "baseline",
        "primary_mpc_wbc",
        "stabilized_primary_mpc_wbc",
    ]

    if args.full:
        target_vx_values = [0.0, 0.1, 0.2, 0.3, 0.4]
        perturbations = [
            {"id": "nominal", "type": "none", "vx": 0.0, "vy": 0.0, "yawrate": 0.0},
            {"id": "vx_plus_0p05", "type": "initial_qvel", "vx": 0.05, "vy": 0.0, "yawrate": 0.0},
            {"id": "vx_minus_0p05", "type": "initial_qvel", "vx": -0.05, "vy": 0.0, "yawrate": 0.0},
            {"id": "vy_plus_0p03", "type": "initial_qvel", "vx": 0.0, "vy": 0.03, "yawrate": 0.0},
            {"id": "yaw_plus_0p10", "type": "initial_qvel", "vx": 0.0, "vy": 0.0, "yawrate": 0.10},
        ]
    else:
        target_vx_values = [0.0, 0.2, 0.3]
        perturbations = [
            {"id": "nominal", "type": "none", "vx": 0.0, "vy": 0.0, "yawrate": 0.0},
            {"id": "vx_plus_0p05", "type": "initial_qvel", "vx": 0.05, "vy": 0.0, "yawrate": 0.0},
            {"id": "yaw_plus_0p10", "type": "initial_qvel", "vx": 0.0, "vy": 0.0, "yawrate": 0.10},
        ]

    matrix_rows: list[dict[str, str]] = []

    for control_mode in controllers:
        for target_vx in target_vx_values:
            for perturbation in perturbations:
                vx_tag = tag_float(target_vx)
                mtag = mode_tag(control_mode)

                perturbation_id = f"stage27_1_{perturbation['id']}_vx{vx_tag}"
                scale_tag = f"stage27_1_{mtag}_vx{vx_tag}_{perturbation['id']}"
                run_id = f"stage27_1_{mtag}_vx{vx_tag}_{perturbation['id']}"

                cmd = build_command(
                    root=root,
                    logs=logs,
                    control_mode=control_mode,
                    target_vx=target_vx,
                    perturbation=perturbation,
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
                    summary_csv = newest(
                        list(logs.glob(f"*{perturbation_id}*{scale_tag}*{control_mode}*summary.csv"))
                    ) or summary_csv

                if not log_csv.is_file():
                    log_csv = newest(
                        list(logs.glob(f"*{perturbation_id}*{scale_tag}*{control_mode}*log.csv"))
                    ) or log_csv

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

                transition_audit = audit_transition_window(log_csv, window=10)

                row = {
                    "stage": "27.1",
                    "run_id": run_id,
                    "control_mode": control_mode,
                    "target_vx": f"{target_vx:.3f}",
                    "perturbation_id": perturbation_id,
                    "perturbation_type": str(perturbation["type"]),
                    "perturb_vx": f"{float(perturbation['vx']):.6f}",
                    "perturb_vy": f"{float(perturbation['vy']):.6f}",
                    "perturb_yawrate": f"{float(perturbation['yawrate']):.6f}",
                    "expected_stability": expected_stability,
                    "returncode": str(result.returncode),
                    "summary_exists": str(summary_exists),
                    "log_exists": str(log_exists),
                    "mode_executed": str(mode_executed),
                    "stability_pass": str(stability_pass),
                    "evidence_generated": str(evidence_generated),
                    "regression_evidence_pass": str(regression_evidence_pass),
                    "mean_vx": str(runner_summary.get("mean_vx", "")),
                    "mean_abs_velocity_error": str(runner_summary.get("mean_abs_velocity_error", "")),
                    "max_abs_velocity_error": str(runner_summary.get("max_abs_velocity_error", "")),
                    "qp_fail_steps": str(runner_summary.get("qp_fail_steps", "")),
                    "saturation_steps": str(runner_summary.get("saturation_steps", "")),
                    "max_abs_roll": str(runner_summary.get("max_abs_roll", "")),
                    "max_abs_pitch": str(runner_summary.get("max_abs_pitch", "")),
                    "min_z": str(runner_summary.get("min_z", "")),
                    "max_tau_total_abs": str(runner_summary.get("max_tau_total_abs", "")),
                    "transition_count_summary": str(runner_summary.get("transition_count", "")),
                    **transition_audit,
                    "runner_summary_csv": str(summary_csv.relative_to(root)) if summary_csv.is_file() else "",
                    "runner_log_csv": str(log_csv.relative_to(root)) if log_csv.is_file() else "",
                    "stdout_tail": (result.stdout or "")[-800:].replace("\n", "\\n"),
                    "stderr_tail": (result.stderr or "")[-800:].replace("\n", "\\n"),
                    "command": " ".join(cmd),
                }

                matrix_rows.append(row)

    matrix_csv = logs / "stage27_1_command_qvel_regression_matrix.csv"
    write_csv(matrix_csv, matrix_rows, list(matrix_rows[0].keys()))

    by_controller: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "cases": 0,
            "evidence_generated": 0,
            "stability_pass": 0,
            "regression_evidence_pass": 0,
        }
    )

    failed_cases = []

    for row in matrix_rows:
        control_mode = row["control_mode"]
        by_controller[control_mode]["cases"] += 1

        if as_bool(row["evidence_generated"]):
            by_controller[control_mode]["evidence_generated"] += 1

        if as_bool(row["stability_pass"]):
            by_controller[control_mode]["stability_pass"] += 1

        if as_bool(row["regression_evidence_pass"]):
            by_controller[control_mode]["regression_evidence_pass"] += 1
        else:
            failed_cases.append(
                {
                    "run_id": row["run_id"],
                    "control_mode": row["control_mode"],
                    "target_vx": row["target_vx"],
                    "perturbation_id": row["perturbation_id"],
                    "returncode": row["returncode"],
                    "stability_pass": row["stability_pass"],
                    "runner_summary_csv": row["runner_summary_csv"],
                    "stderr_tail": row["stderr_tail"],
                }
            )

    summary = {
        "stage": "27.1",
        "name": "command velocity and initial qvel perturbation regression matrix",
        "result": "pass" if not failed_cases else "fail",
        "total_cases": len(matrix_rows),
        "controllers": controllers,
        "target_vx_values": target_vx_values,
        "perturbations": perturbations,
        "by_controller": dict(by_controller),
        "failed_cases": failed_cases,
        "matrix_csv": str(matrix_csv.relative_to(root)),
        "claim_boundary": [
            "simulation-only regression matrix",
            "fixed MuJoCo setup only",
            "target velocity variation",
            "initial qvel/yawrate perturbation only",
            "contact transition window audit from existing rollout logs",
            "does not imply terrain robustness",
            "does not imply external-force robustness",
            "does not imply hardware torque enablement",
            "primary_mpc_wbc stability failure is diagnostic evidence if rollout evidence is generated",
        ],
    }

    summary_json = logs / "stage27_1_command_qvel_regression_summary.json"
    write_json(summary_json, summary)

    doc_path = docs / "STAGE27_1_COMMAND_AND_QVEL_PERTURBATION_REGRESSION.md"
    make_doc(summary, matrix_csv, summary_json, doc_path, root)

    print("")
    print(f"stage27_1_result: {summary['result']}")
    print(f"total_cases: {summary['total_cases']}")
    print(f"matrix_csv: {matrix_csv.relative_to(root)}")
    print(f"summary_json: {summary_json.relative_to(root)}")
    print(f"doc: {doc_path.relative_to(root)}")
    print(json.dumps(summary["by_controller"], indent=2, ensure_ascii=False))

    return 0 if summary["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
