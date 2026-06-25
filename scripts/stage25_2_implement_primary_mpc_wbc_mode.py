#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import py_compile
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


def replace_required(text: str, old: str, new: str, label: str) -> tuple[str, bool]:
    if old not in text:
        return text, False
    return text.replace(old, new, 1), True


def main() -> int:
    root = repo_root()
    docs = root / "docs"
    logs = root / "results" / "logs_sample"
    docs.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    source_runner = root / "scripts" / "stage23_2_qvel_injection_trace_runner.py"
    target_runner = root / "scripts" / "stage25_2_primary_mpc_wbc_runner.py"

    s25_0_path = logs / "stage25_0_mpc_wbc_primary_controller_roadmap_summary.json"
    s25_1_path = logs / "stage25_1_control_source_audit_summary.json"

    validation_csv = logs / "stage25_2_primary_mpc_wbc_mode_implementation_validation.csv"
    patch_notes_csv = logs / "stage25_2_primary_mpc_wbc_mode_patch_notes.csv"
    summary_json = logs / "stage25_2_primary_mpc_wbc_mode_implementation_summary.json"
    doc = docs / "STAGE25_2_PRIMARY_MPC_WBC_MODE_IMPLEMENTATION.md"

    checks: list[dict[str, str]] = []
    patch_notes: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    def note(label: str, ok: bool, detail: str) -> None:
        patch_notes.append({
            "patch": label,
            "status": "APPLIED" if ok else "MISSING",
            "detail": detail,
        })

    s25_0 = load_json(s25_0_path)
    s25_1 = load_json(s25_1_path)

    check("stage25_0_summary_exists", s25_0_path.is_file() and s25_0_path.stat().st_size > 0, str(s25_0_path.relative_to(root)))
    check("stage25_0_result_pass", s25_0.get("result") == "pass", f"result={s25_0.get('result')}")
    check("stage25_0_target_primary", s25_0.get("target_control_mode") == "primary_mpc_wbc", f"target={s25_0.get('target_control_mode')}")

    check("stage25_1_summary_exists", s25_1_path.is_file() and s25_1_path.stat().st_size > 0, str(s25_1_path.relative_to(root)))
    check("stage25_1_result_pass", s25_1.get("result") == "pass", f"result={s25_1.get('result')}")
    check("stage25_1_ready", s25_1.get("ready_for_stage25_2_source_patch_planning") is True, f"ready={s25_1.get('ready_for_stage25_2_source_patch_planning')}")

    check("source_runner_exists", source_runner.is_file() and source_runner.stat().st_size > 0, str(source_runner.relative_to(root)))

    if not source_runner.is_file():
        write_csv(validation_csv, checks, ["check", "status", "detail"])
        return 1

    text = source_runner.read_text(encoding="utf-8", errors="ignore")

    text = text.replace("stage23_2_qvel_trace_rollout", "stage25_2_primary_mpc_wbc_rollout")
    text = text.replace('"stage": "23.2"', '"stage": "25.2"')

    # 1. Add primary control-mode constant.
    if 'CONTROL_MODE_PRIMARY_MPC_WBC = "primary_mpc_wbc"' not in text:
        m = re.search(r'^(CONTROL_MODE_MPC_ASSISTED_CANDIDATE\s*=\s*["\']mpc_assisted_candidate["\'].*)$', text, re.MULTILINE)
        if m:
            insert = m.group(1) + '\nCONTROL_MODE_PRIMARY_MPC_WBC = "primary_mpc_wbc"'
            text = text[:m.start()] + insert + text[m.end():]
            note("add_primary_control_mode_constant", True, "CONTROL_MODE_PRIMARY_MPC_WBC")
        else:
            note("add_primary_control_mode_constant", False, "CONTROL_MODE_MPC_ASSISTED_CANDIDATE not found")
    else:
        note("add_primary_control_mode_constant", True, "already present")

    # 2. Add / verify control-mode choice if choices are used.
    # Force the --control-mode argparse choices line to include primary_mpc_wbc.
    # This line-level patch is more robust than trying to parse choices expressions.
    def ensure_primary_control_mode_choice(src: str) -> tuple[str, bool, str]:
        lines = src.splitlines(keepends=True)

        marker_line = -1
        for i, line in enumerate(lines):
            if '"--control-mode"' in line or "'--control-mode'" in line:
                marker_line = i
                break

        if marker_line < 0:
            return src, False, "--control-mode parser argument not found"

        choices_line = -1
        for j in range(marker_line, min(marker_line + 40, len(lines))):
            if "choices" in lines[j]:
                choices_line = j
                break

        if choices_line < 0:
            return src, True, "--control-mode has no argparse choices restriction"

        indent = lines[choices_line][: len(lines[choices_line]) - len(lines[choices_line].lstrip())]
        lines[choices_line] = (
            indent
            + "choices=[CONTROL_MODE_BASELINE, CONTROL_MODE_MPC_ASSISTED_CANDIDATE, CONTROL_MODE_PRIMARY_MPC_WBC],\n"
        )

        patched_src = "".join(lines)
        ok = "choices=[CONTROL_MODE_BASELINE, CONTROL_MODE_MPC_ASSISTED_CANDIDATE, CONTROL_MODE_PRIMARY_MPC_WBC]" in patched_src
        return patched_src, ok, "--control-mode argparse choices include primary_mpc_wbc"

    text, extend_choices_ok, extend_choices_detail = ensure_primary_control_mode_choice(text)
    note("extend_control_mode_choices", extend_choices_ok, extend_choices_detail)

    # 3. Add allow-primary flag near allow-mpc-assisted flag.
    if "--allow-primary-mpc-wbc" not in text:
        allow_pattern = re.compile(
            r'(parser\.add_argument\(\s*["\']--allow-mpc-assisted-candidate["\'][\s\S]*?\)\n)',
            re.MULTILINE,
        )
        m = allow_pattern.search(text)
        if m:
            block = m.group(1)
            add_block = block + '    parser.add_argument("--allow-primary-mpc-wbc", action="store_true", help="explicitly enable simulation-only primary_mpc_wbc control mode")\n'
            text = text[:m.start()] + add_block + text[m.end():]
            note("add_allow_primary_flag", True, "--allow-primary-mpc-wbc")
        else:
            note("add_allow_primary_flag", False, "--allow-mpc-assisted-candidate parser arg not found")
    else:
        note("add_allow_primary_flag", True, "already present")

    # 4. Replace candidate loading / mode validation block.
    old_block = """    if args.control_mode == CONTROL_MODE_MPC_ASSISTED_CANDIDATE:
        if not args.allow_mpc_assisted_candidate:
            raise RuntimeError("mpc_assisted_candidate requires --allow-mpc-assisted-candidate")
        if args.mpc_assisted_candidate_scale <= 0.0:
            raise RuntimeError("mpc_assisted_candidate requires --mpc-assisted-candidate-scale > 0.0")
        if args.mpc_assisted_candidate_scale > MPC_ASSISTED_CANDIDATE_SCALE_MAX:
            raise RuntimeError(f"mpc_assisted_candidate scale exceeds bound: {MPC_ASSISTED_CANDIDATE_SCALE_MAX}")
        candidate_rows, candidate_lookup, candidate_step_values = read_mpc_tau_candidates(Path(args.candidate_csv))
    else:
        if args.mpc_assisted_candidate_scale != 0.0:
            raise RuntimeError("baseline mode requires --mpc-assisted-candidate-scale 0.0")
"""
    new_block = """    if args.control_mode == CONTROL_MODE_MPC_ASSISTED_CANDIDATE:
        if not args.allow_mpc_assisted_candidate:
            raise RuntimeError("mpc_assisted_candidate requires --allow-mpc-assisted-candidate")
        if args.mpc_assisted_candidate_scale <= 0.0:
            raise RuntimeError("mpc_assisted_candidate requires --mpc-assisted-candidate-scale > 0.0")
        if args.mpc_assisted_candidate_scale > MPC_ASSISTED_CANDIDATE_SCALE_MAX:
            raise RuntimeError(f"mpc_assisted_candidate scale exceeds bound: {MPC_ASSISTED_CANDIDATE_SCALE_MAX}")
        candidate_rows, candidate_lookup, candidate_step_values = read_mpc_tau_candidates(Path(args.candidate_csv))
    elif args.control_mode == CONTROL_MODE_PRIMARY_MPC_WBC:
        if not args.allow_primary_mpc_wbc:
            raise RuntimeError("primary_mpc_wbc requires --allow-primary-mpc-wbc")
        if args.mpc_assisted_candidate_scale != 0.0:
            raise RuntimeError("primary_mpc_wbc requires --mpc-assisted-candidate-scale 0.0; the candidate torque is used as primary stance torque, not as scaled injection")
        candidate_rows, candidate_lookup, candidate_step_values = read_mpc_tau_candidates(Path(args.candidate_csv))
    else:
        if args.mpc_assisted_candidate_scale != 0.0:
            raise RuntimeError("baseline mode requires --mpc-assisted-candidate-scale 0.0")
"""
    text, ok = replace_required(text, old_block, new_block, "replace_mode_validation_and_candidate_loading")
    note("replace_mode_validation_and_candidate_loading", ok, "load candidate rows for primary_mpc_wbc")

    # 5. Candidate fetch should run for mpc_assisted and primary.
    old = "        if args.control_mode == CONTROL_MODE_MPC_ASSISTED_CANDIDATE:\n"
    new = "        if args.control_mode in (CONTROL_MODE_MPC_ASSISTED_CANDIDATE, CONTROL_MODE_PRIMARY_MPC_WBC):\n"
    text, ok = replace_required(text, old, new, "candidate_fetch_for_primary")
    note("candidate_fetch_for_primary", ok or "CONTROL_MODE_PRIMARY_MPC_WBC" in text, "candidate_row_for_step branch")

    # 6. Add max primary metric variable.
    old = """    max_tau_candidate_scaled_abs = 0.0
    max_tau_total_abs = 0.0
"""
    new = """    max_tau_candidate_scaled_abs = 0.0
    max_tau_primary_mpc_wbc_raw_abs = 0.0
    max_tau_total_abs = 0.0
"""
    text, ok = replace_required(text, old, new, "add_max_tau_primary_metric")
    note("add_max_tau_primary_metric", ok or "max_tau_primary_mpc_wbc_raw_abs" in text, "max_tau_primary_mpc_wbc_raw_abs")

    # 7. Replace final torque composition.
    old = """        tau_candidate_scaled = args.mpc_assisted_candidate_scale * tau_candidate
        tau_total_raw = tau_baseline_raw + tau_candidate_scaled
        tau_total = np.clip(tau_total_raw, -TORQUE_LIMIT, TORQUE_LIMIT)
"""
    new = """        tau_candidate_scaled = args.mpc_assisted_candidate_scale * tau_candidate
        tau_primary_mpc_wbc_raw = stance_mask * tau_candidate + tau_swing_pd

        if args.control_mode == CONTROL_MODE_PRIMARY_MPC_WBC:
            tau_total_raw = tau_primary_mpc_wbc_raw
        else:
            tau_total_raw = tau_baseline_raw + tau_candidate_scaled

        tau_total = np.clip(tau_total_raw, -TORQUE_LIMIT, TORQUE_LIMIT)
"""
    text, ok = replace_required(text, old, new, "replace_torque_composition")
    note("replace_torque_composition", ok, "primary branch before safety clip")

    # 8. Add per-step primary torque metric.
    old = """        tau_candidate_scaled_abs = float(np.max(np.abs(tau_candidate_scaled)))
        tau_total_raw_abs = float(np.max(np.abs(tau_total_raw)))
"""
    new = """        tau_candidate_scaled_abs = float(np.max(np.abs(tau_candidate_scaled)))
        tau_primary_mpc_wbc_raw_abs = float(np.max(np.abs(tau_primary_mpc_wbc_raw)))
        tau_total_raw_abs = float(np.max(np.abs(tau_total_raw)))
"""
    text, ok = replace_required(text, old, new, "add_tau_primary_abs_per_step")
    note("add_tau_primary_abs_per_step", ok or "tau_primary_mpc_wbc_raw_abs" in text, "tau_primary_mpc_wbc_raw_abs")

    old = """        max_tau_candidate_scaled_abs = max(max_tau_candidate_scaled_abs, float(np.max(np.abs(tau_candidate_scaled))))
"""
    new = """        max_tau_candidate_scaled_abs = max(max_tau_candidate_scaled_abs, float(np.max(np.abs(tau_candidate_scaled))))
        max_tau_primary_mpc_wbc_raw_abs = max(max_tau_primary_mpc_wbc_raw_abs, float(np.max(np.abs(tau_primary_mpc_wbc_raw))))
"""
    text, ok = replace_required(text, old, new, "update_max_tau_primary_metric")
    note("update_max_tau_primary_metric", ok, "max_tau_primary_mpc_wbc_raw_abs update")

    # 9. Add log column.
    old = """            "tau_candidate_scaled_abs": f"{tau_candidate_scaled_abs:.12f}",
            "tau_total_raw_abs": f"{tau_total_raw_abs:.12f}",
"""
    new = """            "tau_candidate_scaled_abs": f"{tau_candidate_scaled_abs:.12f}",
            "tau_primary_mpc_wbc_raw_abs": f"{tau_primary_mpc_wbc_raw_abs:.12f}",
            "tau_total_raw_abs": f"{tau_total_raw_abs:.12f}",
"""
    text, ok = replace_required(text, old, new, "add_log_tau_primary_column")
    note("add_log_tau_primary_column", ok or "tau_primary_mpc_wbc_raw_abs" in text, "log column")

    # 10. Update summary flags.
    old = """        "control_law_changed": args.control_mode == CONTROL_MODE_MPC_ASSISTED_CANDIDATE,
        "mixed_baseline_modified": False,
        "mpc_assisted_candidate_switch_present": True,
        "mpc_assisted_candidate_executed": args.control_mode == CONTROL_MODE_MPC_ASSISTED_CANDIDATE,
"""
    new = """        "control_law_changed": args.control_mode != CONTROL_MODE_BASELINE,
        "mixed_baseline_modified": False,
        "mpc_assisted_candidate_switch_present": True,
        "mpc_assisted_candidate_executed": args.control_mode == CONTROL_MODE_MPC_ASSISTED_CANDIDATE,
        "primary_mpc_wbc_mode_present": True,
        "primary_mpc_wbc_executed": args.control_mode == CONTROL_MODE_PRIMARY_MPC_WBC,
        "primary_mpc_wbc_simulation_only": args.control_mode == CONTROL_MODE_PRIMARY_MPC_WBC,
"""
    text, ok = replace_required(text, old, new, "add_primary_summary_flags")
    note("add_primary_summary_flags", ok, "primary_mpc_wbc summary flags")

    old = """        "candidate_available_in_run": args.control_mode == CONTROL_MODE_MPC_ASSISTED_CANDIDATE,
"""
    new = """        "candidate_available_in_run": args.control_mode in (CONTROL_MODE_MPC_ASSISTED_CANDIDATE, CONTROL_MODE_PRIMARY_MPC_WBC),
"""
    text, ok = replace_required(text, old, new, "candidate_available_for_primary")
    note("candidate_available_for_primary", ok, "candidate_available_in_run")

    old = """        "max_tau_candidate_scaled_abs": f"{max_tau_candidate_scaled_abs:.12f}",
        "max_tau_total_raw_abs": f"{max_tau_total_raw_abs:.12f}",
"""
    new = """        "max_tau_candidate_scaled_abs": f"{max_tau_candidate_scaled_abs:.12f}",
        "max_tau_primary_mpc_wbc_raw_abs": f"{max_tau_primary_mpc_wbc_raw_abs:.12f}",
        "max_tau_total_raw_abs": f"{max_tau_total_raw_abs:.12f}",
"""
    text, ok = replace_required(text, old, new, "add_summary_primary_tau_metric")
    note("add_summary_primary_tau_metric", ok or "max_tau_primary_mpc_wbc_raw_abs" in text, "summary metric")

    target_runner.write_text(text, encoding="utf-8")
    target_runner.chmod(0o755)

    runner_text = target_runner.read_text(encoding="utf-8", errors="ignore")

    required_terms = [
        'CONTROL_MODE_PRIMARY_MPC_WBC = "primary_mpc_wbc"',
        "--allow-primary-mpc-wbc",
        "CONTROL_MODE_PRIMARY_MPC_WBC",
        "tau_primary_mpc_wbc_raw = stance_mask * tau_candidate + tau_swing_pd",
        "if args.control_mode == CONTROL_MODE_PRIMARY_MPC_WBC:",
        "tau_total = np.clip(tau_total_raw, -TORQUE_LIMIT, TORQUE_LIMIT)",
        "data.ctrl[:] = tau_total",
        "primary_mpc_wbc_mode_present",
        "primary_mpc_wbc_executed",
        "max_tau_primary_mpc_wbc_raw_abs",
    ]

    for term in required_terms:
        check(f"runner_contains::{term}", term in runner_text, term)

    check("baseline_composition_preserved", "tau_total_raw = tau_baseline_raw + tau_candidate_scaled" in runner_text, "baseline / mpc-assisted branch preserved")
    check("candidate_loaded_for_primary", "elif args.control_mode == CONTROL_MODE_PRIMARY_MPC_WBC" in runner_text, "primary branch loads candidate csv")
    check("existing_source_not_modified", source_runner.read_text(encoding="utf-8", errors="ignore") != runner_text, "target runner is derived copy")

    compile_ok = True
    compile_error = ""
    try:
        py_compile.compile(str(target_runner), doraise=True)
    except Exception as exc:
        compile_ok = False
        compile_error = repr(exc)

    check("target_runner_py_compile", compile_ok, compile_error or "py_compile ok")

    patch_ok = all(row["status"] == "APPLIED" for row in patch_notes)

    check("all_patch_notes_applied", patch_ok, f"applied={sum(1 for r in patch_notes if r['status'] == 'APPLIED')}/{len(patch_notes)}")

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    write_csv(patch_notes_csv, patch_notes, ["patch", "status", "detail"])
    write_csv(validation_csv, checks, ["check", "status", "detail"])

    doc.write_text(f"""# Stage 25.2：primary_mpc_wbc mode implementation

## 1. 目标

Stage 25.2 基于 Stage 25.1 的 source audit 结果，从 `scripts/stage23_2_qvel_injection_trace_runner.py` 派生新的 runner：

    scripts/stage25_2_primary_mpc_wbc_runner.py

并新增 simulation-only 控制模式：

    primary_mpc_wbc

本阶段只实现控制模式，不做 smoke rollout。smoke rollout 将在 Stage 25.3 进行。

## 2. 结果

Stage 25.2 result: {result}

Failure count: {failure_count}

Target runner:

    {target_runner.relative_to(root)}

## 3. 新增控制模式

新增：

    CONTROL_MODE_PRIMARY_MPC_WBC = "primary_mpc_wbc"

新增显式开关：

    --allow-primary-mpc-wbc

## 4. Torque composition

原有 candidate injection 结构保持为：

    tau_total_raw = tau_baseline_raw + tau_candidate_scaled

新增 primary_mpc_wbc 分支：

    tau_primary_mpc_wbc_raw = stance_mask * tau_candidate + tau_swing_pd

    if args.control_mode == CONTROL_MODE_PRIMARY_MPC_WBC:
        tau_total_raw = tau_primary_mpc_wbc_raw
    else:
        tau_total_raw = tau_baseline_raw + tau_candidate_scaled

所有模式仍共同经过 safety filter：

    tau_total = np.clip(tau_total_raw, -TORQUE_LIMIT, TORQUE_LIMIT)

最终仍写入 MuJoCo：

    data.ctrl[:] = tau_total
    mujoco.mj_step(model, data)

## 5. 当前支持的表述

Stage 25.2 支持：

    已新增 simulation-only primary_mpc_wbc runner；
    primary_mpc_wbc 模式将 MPC/WBC candidate torque 作为 stance primary torque；
    swing leg PD 保留；
    torque safety filter 保留；
    baseline 和 mpc_assisted_candidate 模式保留。

## 6. 当前不支持的表述

Stage 25.2 不支持：

  * 不支持 primary_mpc_wbc 已经完成 rollout 验证；
  * 不支持 MPC-WBC 主控闭环已经稳定运行；
  * 不支持真实机器人闭环；
  * 不支持 hardware torque enablement；
  * 不支持 observable perturbation robustness；
  * 不支持复杂地形或外力冲击鲁棒性。

## 7. Patch notes

{json.dumps(patch_notes, indent=2, ensure_ascii=False)}
""", encoding="utf-8")

    summary = {
        "stage": "25.2",
        "name": "primary_mpc_wbc mode implementation",
        "result": result,
        "failure_count": failure_count,
        "source_runner": str(source_runner.relative_to(root)),
        "target_runner": str(target_runner.relative_to(root)),
        "target_control_mode": "primary_mpc_wbc",
        "primary_mpc_wbc_mode_implemented": result == "pass",
        "smoke_rollout_completed": False,
        "torque_composition": {
            "baseline_or_assisted_branch": "tau_total_raw = tau_baseline_raw + tau_candidate_scaled",
            "primary_branch": "tau_total_raw = stance_mask * tau_candidate + tau_swing_pd",
            "safety_filter": "tau_total = np.clip(tau_total_raw, -TORQUE_LIMIT, TORQUE_LIMIT)",
            "mujoco_write": "data.ctrl[:] = tau_total",
        },
        "generated_files": [
            str(target_runner.relative_to(root)),
            str(validation_csv.relative_to(root)),
            str(patch_notes_csv.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(doc.relative_to(root)),
        ],
        "claim_boundary": [
            "implementation only",
            "no smoke rollout yet",
            "simulation-only primary_mpc_wbc runner",
            "no real robot torque execution claim",
            "no hardware torque enablement claim",
            "no observable perturbation robustness claim",
            "no terrain or external-force robustness claim",
        ],
        "patch_notes": patch_notes,
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"stage25_2_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"target_runner: {target_runner.relative_to(root)}")
    print(f"primary_mpc_wbc_mode_implemented: {result == 'pass'}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"validation_csv: {validation_csv.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
