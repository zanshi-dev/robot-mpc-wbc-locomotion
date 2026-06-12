#!/usr/bin/env python3
from pathlib import Path
import ast
import datetime as dt
import json
import re
import subprocess
from typing import Dict, List

ROOT = Path.cwd()
STAGE = "14.5D-R1"

BASELINE_RUNNER = ROOT / "scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py"
FALLBACK_RUNNERS = [
    ROOT / "scripts/stage13_1b_rerun_1200step_simulation_only_mixed_baseline.py",
    ROOT / "scripts/stage13_2b_run_2400step_simulation_only_robustness_regression.py",
    ROOT / "scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py",
]

OUT_SUMMARY = ROOT / "results/logs_sample/stage14_5d_r1_baseline_runner_structure_inspection_summary.json"
OUT_DOC = ROOT / "docs/stage14_5d_r1_baseline_runner_structure_inspection.md"
OUT_SNIPPETS = ROOT / "results/logs_sample/stage14_5d_r1_baseline_runner_structure_snippets.txt"

SUMMARY_14_5D_R0 = ROOT / "results/logs_sample/stage14_5d_r0_closed_loop_ab_anchor_inspection_summary.json"


def git(args: List[str]) -> str:
    proc = subprocess.run(
        ["git"] + args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def read_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def choose_runner() -> Path:
    if BASELINE_RUNNER.exists():
        return BASELINE_RUNNER
    for p in FALLBACK_RUNNERS:
        if p.exists():
            return p
    raise FileNotFoundError("No baseline runner candidate found")


def line_text(lines: List[str], lineno: int, radius: int = 3) -> List[str]:
    start = max(1, lineno - radius)
    end = min(len(lines), lineno + radius)
    out = []
    for i in range(start, end + 1):
        out.append(f"{i}: {lines[i - 1]}")
    return out


def collect_ast_symbols(tree: ast.AST) -> Dict:
    functions = []
    classes = []
    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append({
                "name": node.name,
                "lineno": node.lineno,
                "end_lineno": getattr(node, "end_lineno", node.lineno),
                "arg_count": len(node.args.args),
            })
        elif isinstance(node, ast.ClassDef):
            classes.append({
                "name": node.name,
                "lineno": node.lineno,
                "end_lineno": getattr(node, "end_lineno", node.lineno),
            })
        elif isinstance(node, ast.Import):
            imports.append({
                "lineno": node.lineno,
                "names": [alias.name for alias in node.names],
            })
        elif isinstance(node, ast.ImportFrom):
            imports.append({
                "lineno": node.lineno,
                "module": node.module,
                "names": [alias.name for alias in node.names],
            })

    return {
        "functions": sorted(functions, key=lambda x: x["lineno"]),
        "classes": sorted(classes, key=lambda x: x["lineno"]),
        "imports": sorted(imports, key=lambda x: x["lineno"]),
    }


def pattern_hits(lines: List[str], patterns: Dict[str, List[str]]) -> Dict[str, List[Dict]]:
    hits = {k: [] for k in patterns}
    for i, line in enumerate(lines, start=1):
        for key, pats in patterns.items():
            if any(re.search(p, line, re.IGNORECASE) for p in pats):
                hits[key].append({"lineno": i, "text": line.rstrip()})
    return hits


def main() -> int:
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)

    failed_checks = []

    r0 = read_json(SUMMARY_14_5D_R0)
    if not r0 or r0.get("pass") is not True:
        failed_checks.append("stage14_5d_r0_not_passed_or_missing")

    try:
        runner = choose_runner()
    except Exception as exc:
        runner = None
        failed_checks.append("baseline_runner_not_found")
        runner_error = str(exc)
    else:
        runner_error = ""

    ast_error = ""
    symbols = {"functions": [], "classes": [], "imports": []}
    hits = {}

    if runner:
        text = runner.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()

        try:
            tree = ast.parse(text)
            symbols = collect_ast_symbols(tree)
        except Exception as exc:
            ast_error = str(exc)
            failed_checks.append("baseline_runner_ast_parse_failed")

        patterns = {
            "main_or_entry": [
                r"if __name__ == [\"']__main__[\"']",
                r"def main\(",
                r"argparse",
            ],
            "mujoco_model_data": [
                r"mujoco",
                r"MjModel",
                r"MjData",
                r"mj_step",
                r"scene\.xml",
            ],
            "simulation_loop": [
                r"for .*step",
                r"while .*step",
                r"total_steps",
                r"range\(.*steps",
            ],
            "torque_write": [
                r"data\.ctrl",
                r"\.ctrl\[",
                r"tau",
                r"torque",
            ],
            "baseline_control_terms": [
                r"stance",
                r"swing",
                r"wbc",
                r"pd",
                r"feedforward",
            ],
            "metrics_summary": [
                r"summary",
                r"pass",
                r"min_z",
                r"max_abs_roll",
                r"max_abs_pitch",
                r"qp_fail",
                r"saturation",
                r"json",
            ],
            "file_outputs": [
                r"results/logs_sample",
                r"write_text",
                r"json\.dump",
                r"csv",
            ],
        }
        hits = pattern_hits(lines, patterns)

        for key, values in hits.items():
            if not values:
                failed_checks.append(f"missing_pattern_hits:{key}")

        snippet_lines = [
            "Stage 14.5D-R1 baseline runner structure snippets",
            f"timestamp_utc: {dt.datetime.now(dt.timezone.utc).isoformat()}",
            f"runner: {runner.relative_to(ROOT)}",
            "",
        ]

        for key, values in hits.items():
            snippet_lines.append(f"[{key}] count={len(values)}")
            for item in values[:40]:
                snippet_lines.extend(line_text(lines, item["lineno"], radius=2))
                snippet_lines.append("")
            snippet_lines.append("")

        OUT_SNIPPETS.write_text("\n".join(snippet_lines), encoding="utf-8")
    else:
        lines = []
        OUT_SNIPPETS.write_text("No runner found.\n", encoding="utf-8")

    dirty = git(["status", "--porcelain"])
    dirty_paths = [line[3:].strip() for line in dirty.splitlines() if line.strip()]
    allowed_dirty = {
        "scripts/stage14_5d_r1_baseline_runner_structure_inspection.py",
        "docs/stage14_5d_r1_baseline_runner_structure_inspection.md",
        "results/logs_sample/stage14_5d_r1_baseline_runner_structure_inspection_summary.json",
        "results/logs_sample/stage14_5d_r1_baseline_runner_structure_snippets.txt",
    }
    dirty_non_stage = [p for p in dirty_paths if p not in allowed_dirty]
    if dirty_non_stage:
        failed_checks.append("unexpected_dirty_files_present")

    summary = {
        "stage": STAGE,
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "pass": len(failed_checks) == 0,
        "failed_checks": failed_checks,
        "simulation_only_project": True,
        "hardware_deployment_completed": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "control_law_changed": False,
        "mixed_baseline_modified": False,
        "mujoco_closed_loop_ab_executed": False,
        "mujoco_torque_used": False,
        "ros_publisher_used": False,
        "mpc_assisted_switch_added": False,
        "stage14_5d_r0_pass": None if not r0 else r0.get("pass"),
        "baseline_runner": None if runner is None else str(runner.relative_to(ROOT)),
        "baseline_runner_error": runner_error,
        "ast_error": ast_error,
        "line_count": len(lines),
        "symbols": symbols,
        "pattern_hit_counts": {k: len(v) for k, v in hits.items()},
        "pattern_hits_first20": {k: v[:20] for k, v in hits.items()},
        "git": {
            "branch": git(["branch", "--show-current"]),
            "head": git(["rev-parse", "--short", "HEAD"]),
            "status_porcelain": dirty,
            "dirty_non_stage14_5d_r1": dirty_non_stage,
        },
        "generated_files": [
            "scripts/stage14_5d_r1_baseline_runner_structure_inspection.py",
            "docs/stage14_5d_r1_baseline_runner_structure_inspection.md",
            "results/logs_sample/stage14_5d_r1_baseline_runner_structure_snippets.txt",
            "results/logs_sample/stage14_5d_r1_baseline_runner_structure_inspection_summary.json",
        ],
        "notes": [
            "Structure inspection only.",
            "No MuJoCo rollout is executed.",
            "No MPC-assisted switch is added.",
            "No baseline source file is modified.",
            "No ROS torque publisher is used.",
        ],
    }

    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    doc = [
        "# Stage 14.5D-R1 Baseline Runner Structure Inspection",
        "",
        "Scope: simulation-only source structure inspection.",
        "",
        "This step inspects the exact baseline runner source structure before deriving a Stage 14.5D closed-loop A/B script.",
        "",
        "It does not run MuJoCo, does not modify the frozen mixed baseline, does not add an MPC-assisted switch, and does not use ROS torque publishing.",
        "",
        "## Evidence",
        "",
        f"- Summary JSON: `{OUT_SUMMARY.relative_to(ROOT)}`",
        f"- Snippets: `{OUT_SNIPPETS.relative_to(ROOT)}`",
        "",
        "## Result",
        "",
        f"- pass: {summary['pass']}",
        f"- failed_checks: {summary['failed_checks']}",
        f"- baseline_runner: `{summary['baseline_runner']}`",
        f"- line_count: {summary['line_count']}",
        "",
        "## Pattern hit counts",
        "",
    ]

    for key, count in summary["pattern_hit_counts"].items():
        doc.append(f"- {key}: {count}")

    doc += [
        "",
        "## Functions",
        "",
    ]

    for fn in symbols.get("functions", [])[:80]:
        doc.append(f"- `{fn['name']}` lines {fn['lineno']}-{fn['end_lineno']}")

    doc += [
        "",
        "## Boundary",
        "",
        "This is source-structure evidence only. It is not MPC-assisted closed-loop locomotion evidence.",
        "",
    ]

    OUT_DOC.write_text("\n".join(doc), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
