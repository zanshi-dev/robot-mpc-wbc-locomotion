#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def extract_context(lines: list[str], patterns: list[str], radius: int = 4) -> list[str]:
    compiled = [re.compile(p) for p in patterns]
    hit_indices = []
    for i, line in enumerate(lines):
        if any(p.search(line) for p in compiled):
            hit_indices.append(i)

    selected = []
    seen = set()
    for idx in hit_indices:
        for j in range(max(0, idx - radius), min(len(lines), idx + radius + 1)):
            if j not in seen:
                seen.add(j)
                selected.append(f"{j + 1}: {lines[j]}")
        selected.append("")
    return selected


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "status", "detail"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    root = repo_root()
    logs = root / "results" / "logs_sample"
    docs = root / "docs"
    logs.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)

    source_rel = "scripts/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_runner.py"
    source = root / source_rel

    source_text = read_text(source) if source.is_file() else ""
    lines = source_text.splitlines()

    patterns = [
        r"fieldnames",
        r"writerow",
        r"DictWriter",
        r"csv\.writer",
        r"summary",
        r"base_z",
        r"roll",
        r"pitch",
        r"qpos",
        r"qvel",
        r"data\.ctrl",
        r"mj_step",
        r"candidate_scale",
        r"mpc_assisted_candidate",
        r"tau_total",
        r"saturated",
        r"total_steps",
        r"model\.opt\.timestep",
        r"timestep",
    ]

    context_lines = extract_context(lines, patterns, radius=5)

    checks = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    check("source_exists", source.is_file() and source.stat().st_size > 0, source_rel)
    check("source_has_qpos", "qpos" in source_text, "qpos")
    check("source_has_mj_step", "mj_step" in source_text, "mj_step")
    check("source_has_data_ctrl", "data.ctrl" in source_text, "data.ctrl")
    check("source_has_base_z", "base_z" in source_text, "base_z")
    check("source_has_roll_pitch", "roll" in source_text and "pitch" in source_text, "roll,pitch")
    check("source_has_candidate_scale", "candidate_scale" in source_text, "candidate_scale")
    check("source_has_summary", "summary" in source_text, "summary")
    check("source_has_csv_logging", ("writerow" in source_text or "DictWriter" in source_text or "csv.writer" in source_text), "csv logging")
    check("source_lacks_base_x", "base_x" not in source_text, "expected Stage 18 patch target")
    check("source_lacks_base_vx", "base_vx" not in source_text, "expected Stage 18 patch target")
    check("source_lacks_mean_vx", "mean_vx" not in source_text, "expected Stage 18 patch target")

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    context_report = logs / "stage18_2a_velocity_runner_patch_preflight_context.txt"
    validation_csv = logs / "stage18_2a_velocity_runner_patch_preflight_validation.csv"
    summary_json = logs / "stage18_2a_velocity_runner_patch_preflight_summary.json"
    doc = docs / "STAGE18_2A_VELOCITY_RUNNER_PATCH_PREFLIGHT.md"

    context_report.write_text(
        "# Stage 18.2a source context\n\n"
        f"source: {source_rel}\n\n"
        + "\n".join(context_lines)
        + "\n",
        encoding="utf-8",
    )

    write_csv(validation_csv, checks)

    summary = {
        "stage": "18.2a",
        "name": "velocity runner patch preflight",
        "result": result,
        "failure_count": failure_count,
        "source": source_rel,
        "generated_files": [
            str(context_report.relative_to(root)),
            str(validation_csv.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(doc.relative_to(root)),
        ],
        "patch_target": [
            "add base_x / base_y to per-step log",
            "add base_vx_fd from finite difference",
            "optionally add base_vx_qvel if qvel semantics are safe",
            "add target_vx and velocity_error",
            "add mean_vx / mean_abs_velocity_error / final_x / forward_displacement to summary",
        ],
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    doc.write_text(f"""# Stage 18.2a: Velocity Runner Patch Preflight

## 1. Goal

Stage 18.2a inspects the recommended Stage 18.1 source runner before deriving a velocity-tracking runner.

Recommended source:

    {source_rel}

## 2. Result

Stage 18.2a result: {result}

Failure count: {failure_count}

## 3. Patch Target

Stage 18.2 should derive a new runner rather than modifying the existing Stage 14.5d runner in place.

The derived runner should add:

    base_x
    base_y
    base_vx_fd
    base_vx_qvel_if_available
    target_vx
    velocity_error
    mean_vx
    mean_abs_velocity_error
    final_x
    forward_displacement

## 4. Generated Files

    results/logs_sample/stage18_2a_velocity_runner_patch_preflight_context.txt
    results/logs_sample/stage18_2a_velocity_runner_patch_preflight_validation.csv
    results/logs_sample/stage18_2a_velocity_runner_patch_preflight_summary.json
    docs/STAGE18_2A_VELOCITY_RUNNER_PATCH_PREFLIGHT.md

## 5. Claim Boundary

This stage only inspects the source runner. It does not implement velocity tracking yet.
""", encoding="utf-8")

    print(f"stage18_2a_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"context: {context_report.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
