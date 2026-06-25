#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_rows(path: Path) -> list[dict[str, str]]:
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


def fval(row: dict[str, str] | None, key: str, default: float = 0.0) -> float:
    if not row:
        return default
    try:
        return float(row.get(key, default))
    except Exception:
        return default


def find_phase(rows: list[dict[str, str]], phase: str) -> dict[str, str] | None:
    for row in rows:
        if row.get("phase") == phase:
            return row
    return None


def first_step(rows: list[dict[str, str]]) -> dict[str, str] | None:
    for row in rows:
        if row.get("phase") == "after_mj_step":
            return row
    return None


def main() -> int:
    root = repo_root()
    logs = root / "results" / "logs_sample"
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    plan_csv = logs / "stage23_1_qvel_injection_trace_plan.csv"
    execution_csv = logs / "stage23_2_qvel_injection_trace_execution.csv"
    execution_summary = logs / "stage23_2_qvel_injection_trace_execution_summary.json"

    validation_csv = logs / "stage23_2_qvel_injection_trace_validation.csv"
    diagnostic_csv = logs / "stage23_2_qvel_injection_trace_diagnostic_table.csv"
    diagnostic_md = logs / "stage23_2_qvel_injection_trace_diagnostic_table.md"
    summary_json = logs / "stage23_2_qvel_injection_trace_summary.json"
    doc = docs / "STAGE23_2_QVEL_INJECTION_TRACE_DIAGNOSTIC.md"

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    check("plan_exists", plan_csv.is_file() and plan_csv.stat().st_size > 0, str(plan_csv.relative_to(root)))
    check("execution_csv_exists", execution_csv.is_file() and execution_csv.stat().st_size > 0, str(execution_csv.relative_to(root)))
    check("execution_summary_exists", execution_summary.is_file() and execution_summary.stat().st_size > 0, str(execution_summary.relative_to(root)))

    exec_summary = json.loads(execution_summary.read_text(encoding="utf-8")) if execution_summary.is_file() else {}
    check("execution_result_pass", exec_summary.get("result") == "pass", f"result={exec_summary.get('result')}")

    plan_rows = read_rows(plan_csv)
    exec_rows = read_rows(execution_csv)

    check("planned_case_count_7", len(plan_rows) == 7, f"count={len(plan_rows)}")
    check("execution_case_count_7", len(exec_rows) == 7, f"count={len(exec_rows)}")

    required_cols = [
        "trace_case_id",
        "perturbation_id",
        "perturbation_type",
        "perturb_vx",
        "perturb_vy",
        "perturb_yawrate",
        "scale",
        "scale_tag",
        "control_mode",
        "phase",
        "trace_step_index",
        "time",
        "qpos_size",
        "qvel_size",
        "qpos_0",
        "qpos_1",
        "qpos_2",
        "qpos_3",
        "qvel_0",
        "qvel_1",
        "qvel_5",
        "base_x",
        "base_y",
        "base_vx_fd",
        "base_vy_fd",
    ]

    diagnostic_rows: list[dict[str, str]] = []

    for plan in plan_rows:
        cid = plan["trace_case_id"]
        trace_csv = root / plan["trace_csv"]
        case_summary_json = root / plan["summary_json"]

        check(f"{cid}_trace_exists", trace_csv.is_file() and trace_csv.stat().st_size > 0, str(trace_csv.relative_to(root)))
        check(f"{cid}_case_summary_exists", case_summary_json.is_file() and case_summary_json.stat().st_size > 0, str(case_summary_json.relative_to(root)))

        rows = read_rows(trace_csv)
        check(f"{cid}_trace_rows_at_least_15", len(rows) >= 15, f"rows={len(rows)}")

        cols = set(rows[0].keys()) if rows else set()
        for col in required_cols:
            check(f"{cid}_trace_has::{col}", col in cols, col)

        before = find_phase(rows, "before_injection")
        after = find_phase(rows, "after_injection")
        after_forward = find_phase(rows, "after_mj_forward")
        first = first_step(rows)

        check(f"{cid}_has_before_injection", before is not None, "before_injection")
        check(f"{cid}_has_after_injection", after is not None, "after_injection")
        check(f"{cid}_has_after_mj_forward", after_forward is not None, "after_mj_forward")
        check(f"{cid}_has_after_first_step", first is not None, "after_mj_step")

        ptype = plan["perturbation_type"]
        if ptype == "base_vx":
            axis = "qvel_0"
            qpos_axis = "qpos_0"
            expected_delta = float(plan["perturb_vx"])
        elif ptype == "base_vy":
            axis = "qvel_1"
            qpos_axis = "qpos_1"
            expected_delta = float(plan["perturb_vy"])
        elif ptype == "base_yawrate":
            axis = "qvel_5"
            qpos_axis = "qpos_3"
            expected_delta = float(plan["perturb_yawrate"])
        else:
            axis = "qvel_0"
            qpos_axis = "qpos_0"
            expected_delta = 0.0

        before_axis = fval(before, axis)
        after_axis = fval(after, axis)
        after_forward_axis = fval(after_forward, axis)
        first_axis = fval(first, axis)

        written_delta = after_axis - before_axis
        after_forward_delta = after_forward_axis - before_axis
        first_step_qvel_delta = first_axis - before_axis

        qpos_before = fval(before, qpos_axis)
        qpos_first = fval(first, qpos_axis)
        qpos_delta_first_step = qpos_first - qpos_before

        injection_written = abs(written_delta - expected_delta) < 1e-9
        after_forward_preserved = abs(after_forward_delta - expected_delta) < 1e-9
        first_step_state_changed = abs(first_step_qvel_delta) > 1e-12 or abs(qpos_delta_first_step) > 1e-12

        diagnostic_rows.append({
            "trace_case_id": cid,
            "perturbation_id": plan["perturbation_id"],
            "perturbation_type": ptype,
            "axis": axis,
            "qpos_axis": qpos_axis,
            "expected_delta": f"{expected_delta:.12f}",
            "before_axis": f"{before_axis:.12f}",
            "after_injection_axis": f"{after_axis:.12f}",
            "after_mj_forward_axis": f"{after_forward_axis:.12f}",
            "after_first_step_axis": f"{first_axis:.12f}",
            "written_delta": f"{written_delta:.12f}",
            "after_forward_delta": f"{after_forward_delta:.12f}",
            "first_step_qvel_delta": f"{first_step_qvel_delta:.12f}",
            "qpos_delta_first_step": f"{qpos_delta_first_step:.12f}",
            "first_step_base_vx_fd": f"{fval(first, 'base_vx_fd'):.12f}",
            "first_step_base_vy_fd": f"{fval(first, 'base_vy_fd'):.12f}",
            "injection_written": str(injection_written),
            "after_forward_preserved": str(after_forward_preserved),
            "first_step_state_changed": str(first_step_state_changed),
            "trace_csv": str(trace_csv.relative_to(root)),
        })

    non_nominal = [r for r in diagnostic_rows if r["perturbation_type"] != "none"]
    all_nonzero_written = all(r["injection_written"] == "True" for r in non_nominal) if non_nominal else False
    all_after_forward_preserved = all(r["after_forward_preserved"] == "True" for r in non_nominal) if non_nominal else False
    any_first_step_state_changed = any(r["first_step_state_changed"] == "True" for r in non_nominal)

    check("diagnostic_table_generated", len(diagnostic_rows) == 7, f"rows={len(diagnostic_rows)}")
    check("diagnostic_records_injection_written_flag", isinstance(all_nonzero_written, bool), str(all_nonzero_written))
    check("diagnostic_records_after_forward_flag", isinstance(all_after_forward_preserved, bool), str(all_after_forward_preserved))
    check("diagnostic_records_first_step_state_change_flag", isinstance(any_first_step_state_changed, bool), str(any_first_step_state_changed))

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    diag_fields = list(diagnostic_rows[0].keys()) if diagnostic_rows else ["trace_case_id"]
    write_csv(diagnostic_csv, diagnostic_rows, diag_fields)
    write_csv(validation_csv, checks, ["check", "status", "detail"])

    md_cols = [
        "trace_case_id",
        "axis",
        "expected_delta",
        "written_delta",
        "after_forward_delta",
        "first_step_qvel_delta",
        "qpos_delta_first_step",
        "injection_written",
        "after_forward_preserved",
        "first_step_state_changed",
    ]

    md_lines = [
        "| " + " | ".join(md_cols) + " |",
        "| " + " | ".join(["---"] * len(md_cols)) + " |",
    ]
    for row in diagnostic_rows:
        md_lines.append("| " + " | ".join(row[c] for c in md_cols) + " |")
    md_text = "\n".join(md_lines)
    diagnostic_md.write_text(md_text + "\n", encoding="utf-8")

    summary = {
        "stage": "23.2",
        "name": "qvel injection trace diagnostic",
        "result": result,
        "failure_count": failure_count,
        "trace_case_count": len(diagnostic_rows),
        "all_nonzero_perturbations_written": all_nonzero_written,
        "all_after_forward_preserved": all_after_forward_preserved,
        "any_first_step_state_changed": any_first_step_state_changed,
        "diagnostic_rows": diagnostic_rows,
        "generated_files": [
            str(validation_csv.relative_to(root)),
            str(diagnostic_csv.relative_to(root)),
            str(diagnostic_md.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(doc.relative_to(root)),
        ],
        "claim_boundary": [
            "diagnostic trace only",
            "no observable perturbation robustness claim",
            "no full MPC-WBC velocity controller claim",
            "no real robot torque execution claim",
            "no hardware torque enablement claim",
            "no terrain or external-force robustness claim",
        ],
        "checks": checks,
    }
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    doc.write_text(f"""# Stage 23.2：qvel injection trace diagnostic

## 1. 目标

Stage 23.2 记录 qvel 初始速度扰动在 MuJoCo data 中的短时 trace，用于解释 Stage 22 中 summary 指标没有出现可观测变化的原因。

本阶段记录：

  * before_injection；
  * after_injection；
  * after_mj_forward；
  * 前 12 个 mj_step 后的 qpos/qvel/base finite-difference velocity。

## 2. 结果

Stage 23.2 result: {result}

Failure count: {failure_count}

Trace case count: {len(diagnostic_rows)}

all_nonzero_perturbations_written: {all_nonzero_written}

all_after_forward_preserved: {all_after_forward_preserved}

any_first_step_state_changed: {any_first_step_state_changed}

## 3. Trace diagnostic table

{md_text}

## 4. 初步解释

Stage 23.2 只给出 trace 诊断数据，不直接给最终根因结论。

根因结论将在 Stage 23.3 中基于以下逻辑判断：

  * 如果 `all_nonzero_perturbations_written=False`，说明 qvel 扰动未真实写入；
  * 如果 `all_nonzero_perturbations_written=True` 但 `all_after_forward_preserved=False`，说明扰动在 mj_forward 后未保持；
  * 如果扰动写入并保持，但 `any_first_step_state_changed=False`，说明当前扰动未影响短时仿真状态；
  * 如果短时状态发生变化但 Stage 22 summary 不变，说明当前 summary 指标对短时 qvel 初始扰动不敏感。

## 5. 结论边界

Stage 23.2 不声明 observable perturbation robustness，不声明完整 MPC-WBC 速度控制器完成，不涉及真实机器人和硬件 torque enablement。
""", encoding="utf-8")

    print(f"stage23_2_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"all_nonzero_perturbations_written: {all_nonzero_written}")
    print(f"all_after_forward_preserved: {all_after_forward_preserved}")
    print(f"any_first_step_state_changed: {any_first_step_state_changed}")
    print(f"summary: {summary_json.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
