#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
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


def safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def should_scan(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    parts = set(rel.parts)

    if ".git" in parts or "__pycache__" in parts:
        return False
    if "results" in parts:
        return False
    if rel.suffix not in {".py", ".cpp", ".cc", ".cxx", ".h", ".hpp"}:
        return False
    if rel.name.startswith("stage25_0_") or rel.name.startswith("stage25_1_"):
        return False

    return True


def category_patterns() -> dict[str, list[str]]:
    return {
        "baseline_torque_generation": [
            "baseline", "tau_pd", "tau_baseline", "stance_pd", "posture", "kp", "kd"
        ],
        "mpc_wbc_candidate_torque": [
            "mpc", "wbc", "candidate", "mpc_assisted", "tau_wbc", "tau_candidate", "feedforward", "contact_force"
        ],
        "candidate_scale_or_blending": [
            "candidate_scale", "mpc_assisted_candidate_scale", "alpha", "scale", "blend", "mixed", "tau_total"
        ],
        "swing_leg_pd": [
            "swing", "swing_pd", "swing_target", "foot_target", "target_foot", "swing_leg", "swing_tau"
        ],
        "safety_filter_or_saturation": [
            "safety", "filter", "clip", "np.clip", "torque_limit", "tau_limit", "saturation", "max_tau"
        ],
        "mujoco_torque_write_or_step": [
            "data.ctrl", ".ctrl", "mj_step", "mujoco.mj_step", "actuator", "ctrl["
        ],
        "control_mode_or_runner_args": [
            "control_mode", "control-mode", "add_argument", "argparse", "baseline", "mpc_assisted", "candidate"
        ],
        "qp_osqp_solve_path": [
            "osqp", "qp", "qp_fail", "solve", "solver", "constraint", "friction", "objective"
        ],
        "contact_gait_state": [
            "contact", "gait", "stance", "phase", "duty", "contact_sequence", "contact_plan"
        ],
        "state_reading_mapping": [
            "qpos", "qvel", "base", "roll", "pitch", "velocity", "state"
        ],
        "pinocchio_kinematics_dynamics": [
            "pinocchio", "jacobian", "mass_matrix", "bias", "kinematics", "dynamics", "rnea", "crba"
        ],
        "primary_mpc_wbc_existing_mode": [
            "primary_mpc_wbc", "mpc_wbc_primary", "primary_controller"
        ],
    }


def line_hits(path: Path, root: Path, category: str, terms: list[str]) -> list[dict[str, str]]:
    text = safe_read(path)
    if not text:
        return []

    pattern = re.compile("|".join(re.escape(t) for t in terms), re.IGNORECASE)
    rows: list[dict[str, str]] = []

    for idx, line in enumerate(text.splitlines(), start=1):
        if not pattern.search(line):
            continue

        snippet = line.strip()
        if len(snippet) > 220:
            snippet = snippet[:217] + "..."

        rows.append({
            "category": category,
            "path": str(path.relative_to(root)),
            "line": str(idx),
            "snippet": snippet,
        })

    return rows


def markdown_table(rows: list[dict[str, str]], cols: list[str], max_rows: int | None = None) -> str:
    use_rows = rows if max_rows is None else rows[:max_rows]
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for row in use_rows:
        lines.append("| " + " | ".join(str(row.get(c, "")) for c in cols) + " |")
    return "\n".join(lines)


def main() -> int:
    root = repo_root()
    docs = root / "docs"
    logs = root / "results" / "logs_sample"
    docs.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    s25_0_path = logs / "stage25_0_mpc_wbc_primary_controller_roadmap_summary.json"

    hits_csv = logs / "stage25_1_control_source_audit_hits.csv"
    category_summary_csv = logs / "stage25_1_control_source_audit_category_summary.csv"
    candidate_files_csv = logs / "stage25_1_control_source_audit_candidate_files.csv"
    validation_csv = logs / "stage25_1_control_source_audit_validation.csv"
    summary_json = logs / "stage25_1_control_source_audit_summary.json"
    doc = docs / "STAGE25_1_CONTROL_SOURCE_AUDIT.md"

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    s25_0 = load_json(s25_0_path)

    check("stage25_0_summary_exists", s25_0_path.is_file() and s25_0_path.stat().st_size > 0, str(s25_0_path.relative_to(root)))
    check("stage25_0_result_pass", s25_0.get("result") == "pass", f"result={s25_0.get('result')}")
    check("stage25_0_target_mode_primary", s25_0.get("target_control_mode") == "primary_mpc_wbc", f"target={s25_0.get('target_control_mode')}")

    scan_files = sorted([p for p in root.rglob("*") if p.is_file() and should_scan(p, root)])
    check("scan_file_count_positive", len(scan_files) > 0, f"count={len(scan_files)}")

    patterns = category_patterns()
    hit_rows: list[dict[str, str]] = []

    for path in scan_files:
        for category, terms in patterns.items():
            hit_rows.extend(line_hits(path, root, category, terms))

    limited_hits: list[dict[str, str]] = []
    seen_counter: dict[tuple[str, str], int] = defaultdict(int)
    for row in hit_rows:
        key = (row["category"], row["path"])
        if seen_counter[key] >= 80:
            continue
        seen_counter[key] += 1
        limited_hits.append(row)

    hit_rows = limited_hits

    category_to_hits: dict[str, list[dict[str, str]]] = defaultdict(list)
    file_to_categories: dict[str, set[str]] = defaultdict(set)
    file_to_hit_count: dict[str, int] = defaultdict(int)

    for row in hit_rows:
        category_to_hits[row["category"]].append(row)
        file_to_categories[row["path"]].add(row["category"])
        file_to_hit_count[row["path"]] += 1

    category_rows: list[dict[str, str]] = []
    for category in patterns:
        rows = category_to_hits.get(category, [])
        files = sorted({r["path"] for r in rows})
        top_files = sorted(
            files,
            key=lambda p: sum(1 for r in rows if r["path"] == p),
            reverse=True,
        )[:5]
        category_rows.append({
            "category": category,
            "hit_count": str(len(rows)),
            "file_count": str(len(files)),
            "top_files": "; ".join(top_files),
        })

    candidate_file_rows: list[dict[str, str]] = []
    for path, cats in sorted(file_to_categories.items(), key=lambda kv: file_to_hit_count[kv[0]], reverse=True):
        cat_set = set(cats)
        score_candidate = int("mpc_wbc_candidate_torque" in cat_set) + int("candidate_scale_or_blending" in cat_set) + int("mujoco_torque_write_or_step" in cat_set)
        score_runner = int("control_mode_or_runner_args" in cat_set) + int("mujoco_torque_write_or_step" in cat_set)
        score_safety = int("safety_filter_or_saturation" in cat_set) + int("mujoco_torque_write_or_step" in cat_set)
        score_swing = int("swing_leg_pd" in cat_set) + int("mujoco_torque_write_or_step" in cat_set)
        score_qp = int("qp_osqp_solve_path" in cat_set) + int("mpc_wbc_candidate_torque" in cat_set)

        role_scores = {
            "candidate_controller_patch_point": score_candidate,
            "runner_arg_patch_point": score_runner,
            "safety_patch_point": score_safety,
            "swing_patch_point": score_swing,
            "qp_patch_point": score_qp,
        }
        likely_role = max(role_scores, key=role_scores.get)
        role_score = role_scores[likely_role]

        candidate_file_rows.append({
            "path": path,
            "hit_count": str(file_to_hit_count[path]),
            "category_count": str(len(cat_set)),
            "categories": "; ".join(sorted(cat_set)),
            "likely_role": likely_role if role_score > 0 else "general_reference",
            "role_score": str(role_score),
        })

    core_categories = [
        "mpc_wbc_candidate_torque",
        "candidate_scale_or_blending",
        "swing_leg_pd",
        "safety_filter_or_saturation",
        "mujoco_torque_write_or_step",
        "control_mode_or_runner_args",
    ]

    for category in core_categories:
        check(
            f"core_category_has_hits::{category}",
            len(category_to_hits.get(category, [])) > 0,
            f"hits={len(category_to_hits.get(category, []))}",
        )

    primary_hits = category_to_hits.get("primary_mpc_wbc_existing_mode", [])
    primary_mode_already_present = len(primary_hits) > 0
    ready_for_stage25_2 = all(len(category_to_hits.get(c, [])) > 0 for c in core_categories)

    check("ready_for_stage25_2_source_patch_planning", ready_for_stage25_2, str(ready_for_stage25_2))
    check("candidate_files_generated", len(candidate_file_rows) > 0, f"rows={len(candidate_file_rows)}")
    check("category_summary_generated", len(category_rows) == len(patterns), f"rows={len(category_rows)}")

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    write_csv(hits_csv, hit_rows, ["category", "path", "line", "snippet"])
    write_csv(category_summary_csv, category_rows, ["category", "hit_count", "file_count", "top_files"])
    write_csv(candidate_files_csv, candidate_file_rows, ["path", "hit_count", "category_count", "categories", "likely_role", "role_score"])
    write_csv(validation_csv, checks, ["check", "status", "detail"])

    category_md = markdown_table(category_rows, ["category", "hit_count", "file_count", "top_files"])
    candidate_md = markdown_table(candidate_file_rows, ["path", "hit_count", "category_count", "likely_role", "categories"], max_rows=25)

    strategy_text = """
Stage 25.2 implementation strategy:

1. Select the highest-confidence runner / controller patch point from stage25_1_control_source_audit_candidate_files.csv.
2. Add a new control mode named primary_mpc_wbc.
3. Preserve existing baseline and mpc-assisted candidate injection behavior.
4. Keep three explicit final torque composition branches:
   baseline: tau_total = tau_baseline + tau_swing_pd
   mpc_assisted_candidate: tau_total = tau_baseline + alpha * tau_mpc_wbc_candidate + tau_swing_pd
   primary_mpc_wbc: tau_total = tau_mpc_wbc_candidate_as_primary_stance + tau_swing_pd
5. Keep torque safety filter after all torque composition modes.
6. If QP / WBC solve fails, record the failure and use a safe fallback.
7. Add smoke rollout evidence before baseline comparison.
""".strip()

    doc.write_text(f"""# Stage 25.1：control source audit

## 1. 目标

Stage 25.1 审计当前控制链路源码入口，为 Stage 25.2 新增 primary_mpc_wbc 控制模式做准备。

本阶段只做 source audit，不修改控制器，不新增 rollout。

## 2. 结果

Stage 25.1 result: {result}

Failure count: {failure_count}

Scanned source files: {len(scan_files)}

Total audit hits: {len(hit_rows)}

Ready for Stage 25.2 source patch planning: {ready_for_stage25_2}

Existing primary_mpc_wbc mode found in scanned non-Stage25 source: {primary_mode_already_present}

## 3. Category summary

{category_md}

## 4. Candidate patch files

{candidate_md}

## 5. Stage 25.2 implementation strategy

{strategy_text}

## 6. 当前支持的表述

Stage 25.1 支持：

    已完成控制源码入口审计；
    已定位 baseline / MPC-WBC candidate / scale blending / swing PD / safety filter / MuJoCo step / runner args 的候选源码位置；
    可以进入 Stage 25.2 新增 simulation-only primary_mpc_wbc 控制模式。

## 7. 当前不支持的表述

Stage 25.1 不支持：

  * 不支持 primary_mpc_wbc 已实现；
  * 不支持 MPC-WBC 已作为主控闭环运行；
  * 不支持真实机器人闭环；
  * 不支持 hardware torque enablement；
  * 不支持 observable perturbation robustness；
  * 不支持复杂地形或外力冲击鲁棒性。
""", encoding="utf-8")

    summary = {
        "stage": "25.1",
        "name": "control source audit",
        "result": result,
        "failure_count": failure_count,
        "scanned_source_file_count": len(scan_files),
        "hit_count": len(hit_rows),
        "category_count": len(category_rows),
        "candidate_file_count": len(candidate_file_rows),
        "ready_for_stage25_2_source_patch_planning": ready_for_stage25_2,
        "primary_mpc_wbc_existing_mode_found": primary_mode_already_present,
        "core_categories": core_categories,
        "category_summary": category_rows,
        "candidate_files": candidate_file_rows[:50],
        "stage25_2_strategy": strategy_text,
        "claim_boundary": [
            "source audit only",
            "no controller modification yet",
            "no new rollout generated",
            "no primary_mpc_wbc closure claim yet",
            "no real robot torque execution claim",
            "no hardware torque enablement claim",
            "no observable perturbation robustness claim",
            "no terrain or external-force robustness claim",
        ],
        "generated_files": [
            str(hits_csv.relative_to(root)),
            str(category_summary_csv.relative_to(root)),
            str(candidate_files_csv.relative_to(root)),
            str(validation_csv.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(doc.relative_to(root)),
        ],
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"stage25_1_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"scanned_source_file_count: {len(scan_files)}")
    print(f"hit_count: {len(hit_rows)}")
    print(f"ready_for_stage25_2_source_patch_planning: {ready_for_stage25_2}")
    print(f"primary_mpc_wbc_existing_mode_found: {primary_mode_already_present}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"candidate_files: {candidate_files_csv.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
