#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import py_compile
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


def replace_once(text: str, old: str, new: str, name: str, notes: list[dict[str, str]]) -> str:
    ok = old in text
    notes.append({
        "patch": name,
        "status": "APPLIED" if ok else "MISSING",
        "detail": name,
    })
    if not ok:
        return text
    return text.replace(old, new, 1)


def patch_choices_line(text: str, notes: list[dict[str, str]]) -> str:
    lines = text.splitlines(keepends=True)
    target = "CONTROL_MODE_STABILIZED_PRIMARY_MPC_WBC"

    found = False
    patched = False

    for i, line in enumerate(lines):
        if "choices=" not in line:
            continue
        if "CONTROL_MODE_PRIMARY_MPC_WBC" not in line:
            continue

        found = True
        if target not in line:
            if line.rstrip().endswith("],"):
                line = line.rstrip()[:-2] + f", {target}],\n"
            elif line.rstrip().endswith("]"):
                line = line.rstrip()[:-1] + f", {target}]\n"
            else:
                line = line.rstrip() + f"  # includes {target}\n"
            lines[i] = line
        patched = target in lines[i]
        break

    notes.append({
        "patch": "extend_control_mode_choices_for_stabilized",
        "status": "APPLIED" if found and patched else "MISSING",
        "detail": "--control-mode choices include stabilized_primary_mpc_wbc",
    })

    return "".join(lines)


def main() -> int:
    root = repo_root()
    docs = root / "docs"
    logs = root / "results" / "logs_sample"
    docs.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    source_runner = root / "scripts" / "stage25_2_primary_mpc_wbc_runner.py"
    target_runner = root / "scripts" / "stage25_5_stabilized_primary_mpc_wbc_runner.py"

    s25_4_summary_path = logs / "stage25_4_primary_mpc_wbc_failure_diagnosis_summary.json"

    validation_csv = logs / "stage25_5_stabilized_primary_mpc_wbc_mode_validation.csv"
    patch_notes_csv = logs / "stage25_5_stabilized_primary_mpc_wbc_mode_patch_notes.csv"
    summary_json = logs / "stage25_5_stabilized_primary_mpc_wbc_mode_summary.json"
    doc = docs / "STAGE25_5_STABILIZED_PRIMARY_MPC_WBC_MODE.md"

    checks: list[dict[str, str]] = []
    notes: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail})

    s25_4 = load_json(s25_4_summary_path)

    check("stage25_4_summary_exists", s25_4_summary_path.is_file() and s25_4_summary_path.stat().st_size > 0, str(s25_4_summary_path.relative_to(root)))
    check("stage25_4_result_pass", s25_4.get("result") == "pass", f"result={s25_4.get('result')}")
    check("stage25_4_failure_class_expected", s25_4.get("failure_class") == "posture_limit_violation_with_torque_saturation_no_qp_failure", str(s25_4.get("failure_class")))
    check("source_runner_exists", source_runner.is_file() and source_runner.stat().st_size > 0, str(source_runner.relative_to(root)))

    if not source_runner.is_file():
        write_csv(validation_csv, checks, ["check", "status", "detail"])
        return 1

    text = source_runner.read_text(encoding="utf-8", errors="ignore")

    text = text.replace("stage25_2_primary_mpc_wbc_rollout", "stage25_5_stabilized_primary_mpc_wbc_rollout")
    text = text.replace('"stage": "25.2"', '"stage": "25.5"')

    text = replace_once(
        text,
        'CONTROL_MODE_PRIMARY_MPC_WBC = "primary_mpc_wbc"\n',
        'CONTROL_MODE_PRIMARY_MPC_WBC = "primary_mpc_wbc"\nCONTROL_MODE_STABILIZED_PRIMARY_MPC_WBC = "stabilized_primary_mpc_wbc"\n',
        "add_stabilized_control_mode_constant",
        notes,
    )

    text = patch_choices_line(text, notes)

    text = replace_once(
        text,
        '    parser.add_argument("--allow-primary-mpc-wbc", action="store_true", help="explicitly enable simulation-only primary_mpc_wbc control mode")\n',
        '''    parser.add_argument("--allow-primary-mpc-wbc", action="store_true", help="explicitly enable simulation-only primary_mpc_wbc control mode")
    parser.add_argument("--allow-stabilized-primary-mpc-wbc", action="store_true", help="explicitly enable simulation-only stabilized_primary_mpc_wbc control mode")
    parser.add_argument("--stabilized-primary-scale", type=float, default=0.05, help="candidate stance torque scale for stabilized_primary_mpc_wbc")
    parser.add_argument("--stabilized-primary-ramp-steps", type=int, default=600, help="ramp steps for stabilized primary candidate torque")
    parser.add_argument("--stabilized-posture-residual-scale", type=float, default=1.0, help="stance posture residual scale for stabilized primary mode")
    parser.add_argument("--stabilized-wbc-residual-scale", type=float, default=1.0, help="online stance WBC residual scale for stabilized primary mode")
''',
        "add_stabilized_primary_args",
        notes,
    )

    text = replace_once(
        text,
        '''    elif args.control_mode == CONTROL_MODE_PRIMARY_MPC_WBC:
        if not args.allow_primary_mpc_wbc:
            raise RuntimeError("primary_mpc_wbc requires --allow-primary-mpc-wbc")
        if args.mpc_assisted_candidate_scale != 0.0:
            raise RuntimeError("primary_mpc_wbc requires --mpc-assisted-candidate-scale 0.0; the candidate torque is used as primary stance torque, not as scaled injection")
        candidate_rows, candidate_lookup, candidate_step_values = read_mpc_tau_candidates(Path(args.candidate_csv))
    else:
''',
        '''    elif args.control_mode == CONTROL_MODE_PRIMARY_MPC_WBC:
        if not args.allow_primary_mpc_wbc:
            raise RuntimeError("primary_mpc_wbc requires --allow-primary-mpc-wbc")
        if args.mpc_assisted_candidate_scale != 0.0:
            raise RuntimeError("primary_mpc_wbc requires --mpc-assisted-candidate-scale 0.0; the candidate torque is used as primary stance torque, not as scaled injection")
        candidate_rows, candidate_lookup, candidate_step_values = read_mpc_tau_candidates(Path(args.candidate_csv))
    elif args.control_mode == CONTROL_MODE_STABILIZED_PRIMARY_MPC_WBC:
        if not args.allow_stabilized_primary_mpc_wbc:
            raise RuntimeError("stabilized_primary_mpc_wbc requires --allow-stabilized-primary-mpc-wbc")
        if args.mpc_assisted_candidate_scale != 0.0:
            raise RuntimeError("stabilized_primary_mpc_wbc requires --mpc-assisted-candidate-scale 0.0")
        if not (0.0 <= args.stabilized_primary_scale <= 1.0):
            raise RuntimeError("--stabilized-primary-scale must be in [0, 1]")
        if args.stabilized_primary_ramp_steps < 1:
            raise RuntimeError("--stabilized-primary-ramp-steps must be >= 1")
        if not (0.0 <= args.stabilized_posture_residual_scale <= 2.0):
            raise RuntimeError("--stabilized-posture-residual-scale must be in [0, 2]")
        if not (0.0 <= args.stabilized_wbc_residual_scale <= 2.0):
            raise RuntimeError("--stabilized-wbc-residual-scale must be in [0, 2]")
        candidate_rows, candidate_lookup, candidate_step_values = read_mpc_tau_candidates(Path(args.candidate_csv))
    else:
''',
        "extend_mode_validation_for_stabilized",
        notes,
    )

    text = replace_once(
        text,
        "        if args.control_mode in (CONTROL_MODE_MPC_ASSISTED_CANDIDATE, CONTROL_MODE_PRIMARY_MPC_WBC):\n",
        "        if args.control_mode in (CONTROL_MODE_MPC_ASSISTED_CANDIDATE, CONTROL_MODE_PRIMARY_MPC_WBC, CONTROL_MODE_STABILIZED_PRIMARY_MPC_WBC):\n",
        "candidate_fetch_for_stabilized",
        notes,
    )

    text = replace_once(
        text,
        "    max_tau_primary_mpc_wbc_raw_abs = 0.0\n    max_tau_total_abs = 0.0\n",
        "    max_tau_primary_mpc_wbc_raw_abs = 0.0\n    max_tau_stabilized_primary_mpc_wbc_raw_abs = 0.0\n    max_tau_total_abs = 0.0\n",
        "add_stabilized_max_metric",
        notes,
    )

    text = replace_once(
        text,
        '''        tau_candidate_scaled = args.mpc_assisted_candidate_scale * tau_candidate
        tau_primary_mpc_wbc_raw = stance_mask * tau_candidate + tau_swing_pd

        if args.control_mode == CONTROL_MODE_PRIMARY_MPC_WBC:
            tau_total_raw = tau_primary_mpc_wbc_raw
        else:
            tau_total_raw = tau_baseline_raw + tau_candidate_scaled

        tau_total = np.clip(tau_total_raw, -TORQUE_LIMIT, TORQUE_LIMIT)
''',
        '''        tau_candidate_scaled = args.mpc_assisted_candidate_scale * tau_candidate
        tau_primary_mpc_wbc_raw = stance_mask * tau_candidate + tau_swing_pd

        stabilized_ramp = min(1.0, float(step + 1) / float(max(1, args.stabilized_primary_ramp_steps)))
        tau_stabilized_primary_candidate = args.stabilized_primary_scale * stabilized_ramp * stance_mask * tau_candidate
        tau_stabilized_posture_residual = args.stabilized_posture_residual_scale * tau_stance_pd
        tau_stabilized_wbc_residual = args.stabilized_wbc_residual_scale * tau_stance_wbc
        tau_stabilized_primary_mpc_wbc_raw = (
            tau_stabilized_primary_candidate
            + tau_stabilized_posture_residual
            + tau_stabilized_wbc_residual
            + tau_swing_pd
        )

        if args.control_mode == CONTROL_MODE_PRIMARY_MPC_WBC:
            tau_total_raw = tau_primary_mpc_wbc_raw
        elif args.control_mode == CONTROL_MODE_STABILIZED_PRIMARY_MPC_WBC:
            tau_total_raw = tau_stabilized_primary_mpc_wbc_raw
        else:
            tau_total_raw = tau_baseline_raw + tau_candidate_scaled

        tau_total = np.clip(tau_total_raw, -TORQUE_LIMIT, TORQUE_LIMIT)
''',
        "replace_torque_composition_for_stabilized",
        notes,
    )

    text = replace_once(
        text,
        "        max_tau_primary_mpc_wbc_raw_abs = max(max_tau_primary_mpc_wbc_raw_abs, float(np.max(np.abs(tau_primary_mpc_wbc_raw))))\n",
        "        max_tau_primary_mpc_wbc_raw_abs = max(max_tau_primary_mpc_wbc_raw_abs, float(np.max(np.abs(tau_primary_mpc_wbc_raw))))\n        max_tau_stabilized_primary_mpc_wbc_raw_abs = max(max_tau_stabilized_primary_mpc_wbc_raw_abs, float(np.max(np.abs(tau_stabilized_primary_mpc_wbc_raw))))\n",
        "update_stabilized_max_metric",
        notes,
    )

    text = replace_once(
        text,
        '''        tau_primary_mpc_wbc_raw_abs = float(np.max(np.abs(tau_primary_mpc_wbc_raw)))
        tau_total_raw_abs = float(np.max(np.abs(tau_total_raw)))
''',
        '''        tau_primary_mpc_wbc_raw_abs = float(np.max(np.abs(tau_primary_mpc_wbc_raw)))
        tau_stabilized_primary_mpc_wbc_raw_abs = float(np.max(np.abs(tau_stabilized_primary_mpc_wbc_raw)))
        tau_total_raw_abs = float(np.max(np.abs(tau_total_raw)))
''',
        "add_stabilized_abs_per_step",
        notes,
    )

    text = replace_once(
        text,
        '''            "tau_primary_mpc_wbc_raw_abs": f"{tau_primary_mpc_wbc_raw_abs:.12f}",
            "tau_total_raw_abs": f"{tau_total_raw_abs:.12f}",
''',
        '''            "tau_primary_mpc_wbc_raw_abs": f"{tau_primary_mpc_wbc_raw_abs:.12f}",
            "tau_stabilized_primary_mpc_wbc_raw_abs": f"{tau_stabilized_primary_mpc_wbc_raw_abs:.12f}",
            "stabilized_primary_scale": f"{args.stabilized_primary_scale:.12f}",
            "stabilized_ramp": f"{stabilized_ramp:.12f}",
            "tau_total_raw_abs": f"{tau_total_raw_abs:.12f}",
''',
        "add_stabilized_log_columns",
        notes,
    )

    text = replace_once(
        text,
        '''        "primary_mpc_wbc_executed": args.control_mode == CONTROL_MODE_PRIMARY_MPC_WBC,
        "primary_mpc_wbc_simulation_only": args.control_mode == CONTROL_MODE_PRIMARY_MPC_WBC,
''',
        '''        "primary_mpc_wbc_executed": args.control_mode == CONTROL_MODE_PRIMARY_MPC_WBC,
        "primary_mpc_wbc_simulation_only": args.control_mode == CONTROL_MODE_PRIMARY_MPC_WBC,
        "stabilized_primary_mpc_wbc_mode_present": True,
        "stabilized_primary_mpc_wbc_executed": args.control_mode == CONTROL_MODE_STABILIZED_PRIMARY_MPC_WBC,
        "stabilized_primary_mpc_wbc_simulation_only": args.control_mode == CONTROL_MODE_STABILIZED_PRIMARY_MPC_WBC,
        "stabilized_primary_scale": args.stabilized_primary_scale,
        "stabilized_primary_ramp_steps": args.stabilized_primary_ramp_steps,
        "stabilized_posture_residual_scale": args.stabilized_posture_residual_scale,
        "stabilized_wbc_residual_scale": args.stabilized_wbc_residual_scale,
''',
        "add_stabilized_summary_flags",
        notes,
    )

    text = replace_once(
        text,
        '''        "candidate_available_in_run": args.control_mode in (CONTROL_MODE_MPC_ASSISTED_CANDIDATE, CONTROL_MODE_PRIMARY_MPC_WBC),
''',
        '''        "candidate_available_in_run": args.control_mode in (CONTROL_MODE_MPC_ASSISTED_CANDIDATE, CONTROL_MODE_PRIMARY_MPC_WBC, CONTROL_MODE_STABILIZED_PRIMARY_MPC_WBC),
''',
        "candidate_available_for_stabilized",
        notes,
    )

    text = replace_once(
        text,
        '''        "max_tau_primary_mpc_wbc_raw_abs": f"{max_tau_primary_mpc_wbc_raw_abs:.12f}",
        "max_tau_total_raw_abs": f"{max_tau_total_raw_abs:.12f}",
''',
        '''        "max_tau_primary_mpc_wbc_raw_abs": f"{max_tau_primary_mpc_wbc_raw_abs:.12f}",
        "max_tau_stabilized_primary_mpc_wbc_raw_abs": f"{max_tau_stabilized_primary_mpc_wbc_raw_abs:.12f}",
        "max_tau_total_raw_abs": f"{max_tau_total_raw_abs:.12f}",
''',
        "add_stabilized_summary_metric",
        notes,
    )

    target_runner.write_text(text, encoding="utf-8")
    target_runner.chmod(0o755)

    runner_text = target_runner.read_text(encoding="utf-8", errors="ignore")

    required_terms = [
        'CONTROL_MODE_STABILIZED_PRIMARY_MPC_WBC = "stabilized_primary_mpc_wbc"',
        "--allow-stabilized-primary-mpc-wbc",
        "--stabilized-primary-scale",
        "tau_stabilized_primary_mpc_wbc_raw",
        "if args.control_mode == CONTROL_MODE_STABILIZED_PRIMARY_MPC_WBC:",
        "stabilized_primary_mpc_wbc_executed",
        "max_tau_stabilized_primary_mpc_wbc_raw_abs",
        "tau_total = np.clip(tau_total_raw, -TORQUE_LIMIT, TORQUE_LIMIT)",
        "data.ctrl[:] = tau_total",
    ]

    for term in required_terms:
        check(f"runner_contains::{term}", term in runner_text, term)

    compile_ok = True
    compile_detail = "py_compile ok"
    try:
        py_compile.compile(str(target_runner), doraise=True)
    except Exception as exc:
        compile_ok = False
        compile_detail = repr(exc)

    check("target_runner_py_compile", compile_ok, compile_detail)

    all_notes_applied = all(n["status"] == "APPLIED" for n in notes)
    check("all_patch_notes_applied", all_notes_applied, f"applied={sum(1 for n in notes if n['status'] == 'APPLIED')}/{len(notes)}")

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    write_csv(patch_notes_csv, notes, ["patch", "status", "detail"])
    write_csv(validation_csv, checks, ["check", "status", "detail"])

    doc.write_text(f"""# Stage 25.5：stabilized_primary_mpc_wbc mode implementation

## 1. 目标

Stage 25.5 基于 Stage 25.4 的失败诊断，实现一个 stabilized primary_mpc_wbc variant。

该模式名称为：

    stabilized_primary_mpc_wbc

本阶段只实现 runner，不做 rollout。rollout 将在下一阶段进行。

## 2. 设计动机

Stage 25.4 表明，直接 primary_mpc_wbc 模式失败类型为：

    {s25_4.get("failure_class")}

关键问题是：

  * posture limit violation；
  * torque saturation；
  * qp_fail_steps=0；
  * direct primary torque 没有稳定化机制。

因此 Stage 25.5 添加：

  * primary candidate torque scale；
  * primary candidate torque ramp；
  * stance posture residual；
  * online WBC residual；
  * 保留 swing PD；
  * 保留 torque safety filter。

## 3. Torque composition

新增模式：

    stabilized_primary_mpc_wbc

其 torque composition 为：

    stabilized_ramp = min(1.0, (step + 1) / ramp_steps)

    tau_stabilized_primary_candidate =
        stabilized_primary_scale * stabilized_ramp * stance_mask * tau_candidate

    tau_stabilized_primary_mpc_wbc_raw =
        tau_stabilized_primary_candidate
        + stabilized_posture_residual_scale * tau_stance_pd
        + stabilized_wbc_residual_scale * tau_stance_wbc
        + tau_swing_pd

所有模式仍共同经过 safety filter：

    tau_total = np.clip(tau_total_raw, -TORQUE_LIMIT, TORQUE_LIMIT)

## 4. 默认保守参数

    stabilized_primary_scale = 0.05
    stabilized_primary_ramp_steps = 600
    stabilized_posture_residual_scale = 1.0
    stabilized_wbc_residual_scale = 1.0

该默认参数的意图不是证明 full primary torque 已经稳定，而是先得到一个从 baseline residual 到 primary candidate torque 的保守稳定化入口。

## 5. 当前支持的表述

Stage 25.5 支持：

    已实现 stabilized_primary_mpc_wbc runner；
    已加入 ramp / scale / posture residual / WBC residual；
    baseline、mpc_assisted_candidate、primary_mpc_wbc 均保留；
    torque safety filter 保留。

## 6. 当前不支持的表述

Stage 25.5 不支持：

  * 不支持 stabilized_primary_mpc_wbc 已经 rollout 通过；
  * 不支持 full primary_mpc_wbc 已经稳定；
  * 不支持真实机器人闭环；
  * 不支持 hardware torque enablement；
  * 不支持复杂地形或外力冲击鲁棒性。
""", encoding="utf-8")

    summary = {
        "stage": "25.5",
        "name": "stabilized_primary_mpc_wbc mode implementation",
        "result": result,
        "failure_count": failure_count,
        "source_runner": str(source_runner.relative_to(root)),
        "target_runner": str(target_runner.relative_to(root)),
        "target_control_mode": "stabilized_primary_mpc_wbc",
        "stabilized_primary_mpc_wbc_mode_implemented": result == "pass",
        "rollout_completed": False,
        "default_parameters": {
            "stabilized_primary_scale": 0.05,
            "stabilized_primary_ramp_steps": 600,
            "stabilized_posture_residual_scale": 1.0,
            "stabilized_wbc_residual_scale": 1.0,
        },
        "stage25_4_failure_class": s25_4.get("failure_class"),
        "generated_files": [
            str(target_runner.relative_to(root)),
            str(validation_csv.relative_to(root)),
            str(patch_notes_csv.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(doc.relative_to(root)),
        ],
        "claim_boundary": [
            "implementation only",
            "no stabilized rollout yet",
            "simulation-only",
            "no stable primary closure claim yet",
            "no real robot torque execution",
            "no hardware torque enablement",
            "no terrain or external-force robustness",
        ],
        "patch_notes": notes,
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"stage25_5_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"target_runner: {target_runner.relative_to(root)}")
    print(f"stabilized_primary_mpc_wbc_mode_implemented: {result == 'pass'}")
    print(f"summary: {summary_json.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
