#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


ROLL_LIMIT = 0.20
PITCH_LIMIT = 0.20
MIN_Z_LIMIT = 0.22


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


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


def to_float(row: dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default))
    except Exception:
        return default


def to_int(row: dict[str, str], key: str, default: int = 0) -> int:
    try:
        return int(float(row.get(key, default)))
    except Exception:
        return default


def first_step(rows: list[dict[str, str]], predicate) -> int | None:
    for row in rows:
        if predicate(row):
            return to_int(row, "step", -1)
    return None


def main() -> int:
    root = repo_root()
    docs = root / "docs"
    logs = root / "results" / "logs_sample"
    docs.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    s25_3_summary_path = logs / "stage25_3_primary_mpc_wbc_smoke_summary.json"
    s25_3 = load_json(s25_3_summary_path)

    runner_summary_csv = root / s25_3.get("runner_summary_csv", "")
    runner_log_csv = root / s25_3.get("runner_log_csv", "")

    runner_summary_rows = read_csv_rows(runner_summary_csv)
    runner_log_rows = read_csv_rows(runner_log_csv)
    runner_summary = runner_summary_rows[0] if runner_summary_rows else {}

    diagnosis_csv = logs / "stage25_4_primary_mpc_wbc_failure_diagnosis.csv"
    validation_csv = logs / "stage25_4_primary_mpc_wbc_failure_diagnosis_validation.csv"
    summary_json = logs / "stage25_4_primary_mpc_wbc_failure_diagnosis_summary.json"
    doc = docs / "STAGE25_4_PRIMARY_MPC_WBC_FAILURE_DIAGNOSIS.md"

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail})

    check("stage25_3_summary_exists", s25_3_summary_path.is_file() and s25_3_summary_path.stat().st_size > 0, str(s25_3_summary_path.relative_to(root)))
    check("stage25_3_result_pass", s25_3.get("result") == "pass", f"result={s25_3.get('result')}")
    check("stage25_3_primary_executed", s25_3.get("primary_mpc_wbc_executed") is True, str(s25_3.get("primary_mpc_wbc_executed")))
    check("stage25_3_smoke_stability_false", s25_3.get("smoke_stability_pass") is False, str(s25_3.get("smoke_stability_pass")))

    check("runner_summary_csv_exists", runner_summary_csv.is_file() and runner_summary_csv.stat().st_size > 0, str(runner_summary_csv.relative_to(root)) if runner_summary_csv.exists() else str(runner_summary_csv))
    check("runner_log_csv_exists", runner_log_csv.is_file() and runner_log_csv.stat().st_size > 0, str(runner_log_csv.relative_to(root)) if runner_log_csv.exists() else str(runner_log_csv))
    check("runner_log_nonempty", len(runner_log_rows) > 0, f"rows={len(runner_log_rows)}")

    first_roll_exceed = first_step(runner_log_rows, lambda r: abs(to_float(r, "roll")) > ROLL_LIMIT)
    first_pitch_exceed = first_step(runner_log_rows, lambda r: abs(to_float(r, "pitch")) > PITCH_LIMIT)
    first_z_exceed = first_step(runner_log_rows, lambda r: to_float(r, "base_z") < MIN_Z_LIMIT)
    first_saturation = first_step(runner_log_rows, lambda r: str(r.get("saturated", "")).lower() == "true")

    max_abs_roll = to_float(runner_summary, "max_abs_roll")
    max_abs_pitch = to_float(runner_summary, "max_abs_pitch")
    min_z = to_float(runner_summary, "min_z")
    qp_fail_steps = to_int(runner_summary, "qp_fail_steps")
    saturation_steps = to_int(runner_summary, "saturation_steps")

    max_tau_stance_pd_abs = to_float(runner_summary, "max_tau_stance_pd_abs")
    max_tau_stance_wbc_abs = to_float(runner_summary, "max_tau_stance_wbc_abs")
    max_tau_swing_pd_abs = to_float(runner_summary, "max_tau_swing_pd_abs")
    max_tau_candidate_abs = to_float(runner_summary, "max_tau_candidate_abs")
    max_tau_primary_raw_abs = to_float(runner_summary, "max_tau_primary_mpc_wbc_raw_abs")
    max_tau_total_abs = to_float(runner_summary, "max_tau_total_abs")

    if qp_fail_steps == 0 and saturation_steps > 0 and (max_abs_roll > ROLL_LIMIT or max_abs_pitch > PITCH_LIMIT):
        failure_class = "posture_limit_violation_with_torque_saturation_no_qp_failure"
    elif qp_fail_steps > 0:
        failure_class = "qp_failure_involved"
    elif saturation_steps > 0:
        failure_class = "torque_saturation_involved"
    else:
        failure_class = "unknown_or_metric_only_failure"

    if max_tau_swing_pd_abs >= max_tau_candidate_abs:
        dominant_raw_component = "swing_pd_or_posture_residual_dominates_candidate"
    else:
        dominant_raw_component = "candidate_torque_dominates"

    diagnosis_rows = [{
        "control_mode": runner_summary.get("control_mode", ""),
        "primary_mpc_wbc_executed": runner_summary.get("primary_mpc_wbc_executed", ""),
        "smoke_stability_pass": runner_summary.get("pass", ""),
        "failure_class": failure_class,
        "first_roll_exceed_step": "" if first_roll_exceed is None else str(first_roll_exceed),
        "first_pitch_exceed_step": "" if first_pitch_exceed is None else str(first_pitch_exceed),
        "first_z_exceed_step": "" if first_z_exceed is None else str(first_z_exceed),
        "first_saturation_step": "" if first_saturation is None else str(first_saturation),
        "max_abs_roll": f"{max_abs_roll:.12f}",
        "max_abs_pitch": f"{max_abs_pitch:.12f}",
        "min_z": f"{min_z:.12f}",
        "qp_fail_steps": str(qp_fail_steps),
        "saturation_steps": str(saturation_steps),
        "max_tau_stance_pd_abs": f"{max_tau_stance_pd_abs:.12f}",
        "max_tau_stance_wbc_abs": f"{max_tau_stance_wbc_abs:.12f}",
        "max_tau_swing_pd_abs": f"{max_tau_swing_pd_abs:.12f}",
        "max_tau_candidate_abs": f"{max_tau_candidate_abs:.12f}",
        "max_tau_primary_mpc_wbc_raw_abs": f"{max_tau_primary_raw_abs:.12f}",
        "max_tau_total_abs": f"{max_tau_total_abs:.12f}",
        "dominant_raw_component": dominant_raw_component,
    }]

    write_csv(diagnosis_csv, diagnosis_rows, list(diagnosis_rows[0].keys()))

    check("failure_class_expected", failure_class == "posture_limit_violation_with_torque_saturation_no_qp_failure", failure_class)
    check("qp_fail_steps_zero", qp_fail_steps == 0, str(qp_fail_steps))
    check("saturation_steps_positive", saturation_steps > 0, str(saturation_steps))
    check("roll_or_pitch_exceeded", max_abs_roll > ROLL_LIMIT or max_abs_pitch > PITCH_LIMIT, f"roll={max_abs_roll}, pitch={max_abs_pitch}")
    check("primary_raw_metric_available", max_tau_primary_raw_abs > 0.0, str(max_tau_primary_raw_abs))

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    write_csv(validation_csv, checks, ["check", "status", "detail"])

    summary = {
        "stage": "25.4",
        "name": "primary_mpc_wbc smoke failure diagnosis",
        "result": result,
        "failure_count": failure_count,
        "failure_class": failure_class,
        "primary_mpc_wbc_executed": runner_summary.get("primary_mpc_wbc_executed"),
        "smoke_stability_pass": str(runner_summary.get("pass", "")).lower() == "true",
        "first_roll_exceed_step": first_roll_exceed,
        "first_pitch_exceed_step": first_pitch_exceed,
        "first_z_exceed_step": first_z_exceed,
        "first_saturation_step": first_saturation,
        "max_abs_roll": max_abs_roll,
        "max_abs_pitch": max_abs_pitch,
        "min_z": min_z,
        "qp_fail_steps": qp_fail_steps,
        "saturation_steps": saturation_steps,
        "max_tau_stance_pd_abs": max_tau_stance_pd_abs,
        "max_tau_stance_wbc_abs": max_tau_stance_wbc_abs,
        "max_tau_swing_pd_abs": max_tau_swing_pd_abs,
        "max_tau_candidate_abs": max_tau_candidate_abs,
        "max_tau_primary_mpc_wbc_raw_abs": max_tau_primary_raw_abs,
        "max_tau_total_abs": max_tau_total_abs,
        "dominant_raw_component": dominant_raw_component,
        "recommended_next_stage": "Stage 25.5 implement stabilized primary_mpc_wbc variant with ramp/scale/posture residual/fallback",
        "generated_files": [
            str(diagnosis_csv.relative_to(root)),
            str(validation_csv.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(doc.relative_to(root)),
        ],
        "claim_boundary": [
            "diagnosis only",
            "primary_mpc_wbc executed but smoke stability failed",
            "no stable MPC-WBC primary closure claim",
            "no real robot torque execution",
            "no hardware torque enablement",
            "no terrain or external-force robustness",
        ],
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    doc.write_text(f"""# Stage 25.4：primary_mpc_wbc smoke failure diagnosis

## 1. 目标

Stage 25.4 对 Stage 25.3 的 primary_mpc_wbc smoke rollout 负向结果进行诊断。

本阶段不新增控制器，不新增 rollout，只分析已有 Stage 25.3 log / summary。

## 2. 结果

Stage 25.4 result: {result}

Failure count: {failure_count}

failure_class:

    {failure_class}

## 3. 关键诊断指标

| 指标 | 数值 |
|---|---:|
| primary_mpc_wbc_executed | {runner_summary.get("primary_mpc_wbc_executed")} |
| smoke_stability_pass | {runner_summary.get("pass")} |
| first_roll_exceed_step | {first_roll_exceed} |
| first_pitch_exceed_step | {first_pitch_exceed} |
| first_z_exceed_step | {first_z_exceed} |
| first_saturation_step | {first_saturation} |
| max_abs_roll | {max_abs_roll:.12f} |
| max_abs_pitch | {max_abs_pitch:.12f} |
| min_z | {min_z:.12f} |
| qp_fail_steps | {qp_fail_steps} |
| saturation_steps | {saturation_steps} |
| max_tau_candidate_abs | {max_tau_candidate_abs:.12f} |
| max_tau_primary_mpc_wbc_raw_abs | {max_tau_primary_raw_abs:.12f} |
| max_tau_total_abs | {max_tau_total_abs:.12f} |

## 4. 诊断结论

Stage 25.3 的 primary_mpc_wbc 模式确实进入了 simulation-only MuJoCo torque loop，但未通过稳定性边界。

当前 failure class 为：

    {failure_class}

这说明主要问题不是 QP/WBC 求解失败，而是直接 primary torque 组合后出现姿态超限和 torque saturation。

## 5. 下一阶段建议

Stage 25.5 应实现 stabilized primary_mpc_wbc variant，候选修正包括：

  * primary torque ramp；
  * primary torque scale；
  * stance posture residual；
  * saturation-aware fallback；
  * 更保守的 swing PD 或 swing target scale。

## 6. 当前支持的表述

Stage 25.4 支持：

    primary_mpc_wbc 已实际执行；
    直接主控模式当前不稳定；
    失败主要表现为 posture limit violation + torque saturation；
    当前不是 QP failure 主导；
    下一步需要稳定化 primary controller，而不是继续声明稳定闭环成功。

## 7. 当前不支持的表述

Stage 25.4 不支持：

  * 不支持 primary_mpc_wbc 已稳定闭环运行；
  * 不支持真实机器人闭环；
  * 不支持 hardware torque enablement；
  * 不支持复杂地形或外力冲击鲁棒性。
""", encoding="utf-8")

    print(f"stage25_4_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"failure_class: {failure_class}")
    print(f"first_roll_exceed_step: {first_roll_exceed}")
    print(f"first_pitch_exceed_step: {first_pitch_exceed}")
    print(f"first_saturation_step: {first_saturation}")
    print(f"qp_fail_steps: {qp_fail_steps}")
    print(f"saturation_steps: {saturation_steps}")
    print(f"summary: {summary_json.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
