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


def read_csv_header(path: Path) -> list[str]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        return next(reader, [])


def read_csv_first_row(path: Path) -> list[str]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)
        return next(reader, [])


def find_anchor_lines(text: str, patterns: list[str], context: int = 1, limit: int = 120) -> list[str]:
    lines = text.splitlines()
    hits: list[int] = []
    compiled = [re.compile(p) for p in patterns]

    for i, line in enumerate(lines):
        if any(p.search(line) for p in compiled):
            hits.append(i)

    selected: list[str] = []
    seen = set()
    for i in hits:
        for j in range(max(0, i - context), min(len(lines), i + context + 1)):
            if j not in seen:
                seen.add(j)
                selected.append(f"{j + 1}: {lines[j]}")
            if len(selected) >= limit:
                return selected
    return selected


def has_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text) for p in patterns)


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    root = repo_root()
    logs = root / "results" / "logs_sample"
    docs = root / "docs"
    logs.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)

    candidate_scripts = [
        "scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py",
        "scripts/stage13_2_2400step_online_full_wbc_scheduler_runner.py",
        "scripts/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_runner.py",
        "scripts/stage14_5e_r1_candidate_robustness_scale_sweep_runner.py",
    ]

    evidence_csvs = [
        "results/logs_sample/stage14_5e_r1_scale_0p00_baseline_reference_log.csv",
        "results/logs_sample/stage14_5e_r1_scale_0p02_candidate_log.csv",
        "results/logs_sample/stage14_5e_r1_scale_0p00_baseline_reference_summary.csv",
        "results/logs_sample/stage14_5e_r1_scale_0p02_candidate_summary.csv",
        "results/logs_sample/stage14_5e_r1_candidate_robustness_scale_sweep_table.csv",
    ]

    patterns = [
        r"qpos",
        r"qvel",
        r"data\.ctrl",
        r"mj_step",
        r"writerow",
        r"DictWriter",
        r"csv",
        r"summary",
        r"base_z",
        r"roll",
        r"pitch",
        r"model\.opt\.timestep",
        r"timestep",
        r"candidate_scale",
        r"mpc_assisted_candidate",
        r"tau_total",
        r"saturated",
    ]

    inspection_rows: list[dict[str, str]] = []
    anchor_report_lines: list[str] = []
    recommended_source = None

    for rel in candidate_scripts:
        path = root / rel
        text = read_text(path)

        row = {
            "script": rel,
            "exists": str(path.is_file()),
            "has_qpos": str(has_any(text, [r"qpos"])),
            "has_qvel": str(has_any(text, [r"qvel"])),
            "has_mj_step": str(has_any(text, [r"mj_step"])),
            "has_data_ctrl": str(has_any(text, [r"data\.ctrl"])),
            "has_csv_logging": str(has_any(text, [r"csv", r"writerow", r"DictWriter"])),
            "has_summary": str(has_any(text, [r"summary"])),
            "has_candidate_mode": str(has_any(text, [r"mpc_assisted_candidate", r"candidate_scale"])),
            "has_base_z": str(has_any(text, [r"base_z"])),
            "has_roll_pitch": str(has_any(text, [r"roll", r"pitch"])),
        }
        inspection_rows.append(row)

        if path.is_file():
            anchor_report_lines.append(f"# {rel}")
            anchor_report_lines.extend(find_anchor_lines(text, patterns, context=1, limit=140))
            anchor_report_lines.append("")

        if (
            path.is_file()
            and row["has_qpos"] == "True"
            and row["has_mj_step"] == "True"
            and row["has_csv_logging"] == "True"
            and row["has_candidate_mode"] == "True"
        ):
            if recommended_source is None:
                recommended_source = rel

    csv_header_rows: list[dict[str, str]] = []
    for rel in evidence_csvs:
        path = root / rel
        header = read_csv_header(path)
        first_row = read_csv_first_row(path)
        csv_header_rows.append({
            "csv": rel,
            "exists": str(path.is_file()),
            "columns": ",".join(header),
            "first_row": ",".join(first_row[:12]),
            "has_base_x": str("base_x" in header),
            "has_base_vx": str("base_vx" in header),
            "has_mean_vx": str("mean_vx" in header),
            "has_base_z": str("base_z" in header or "min_z" in header),
            "has_roll_pitch": str(("roll" in header and "pitch" in header) or ("max_abs_roll" in header and "max_abs_pitch" in header)),
        })

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    roadmap = root / "results/logs_sample/stage18_0_velocity_tracking_roadmap_summary.json"
    check("stage18_0_summary_exists", roadmap.is_file() and roadmap.stat().st_size > 0, str(roadmap.relative_to(root)))

    existing_scripts = [r for r in inspection_rows if r["exists"] == "True"]
    check("runner_sources_exist", len(existing_scripts) >= 2, f"count={len(existing_scripts)}")

    qpos_sources = [r["script"] for r in inspection_rows if r["has_qpos"] == "True"]
    mj_step_sources = [r["script"] for r in inspection_rows if r["has_mj_step"] == "True"]
    csv_sources = [r["script"] for r in inspection_rows if r["has_csv_logging"] == "True"]
    candidate_sources = [r["script"] for r in inspection_rows if r["has_candidate_mode"] == "True"]

    check("qpos_sources_found", len(qpos_sources) >= 1, ",".join(qpos_sources))
    check("mj_step_sources_found", len(mj_step_sources) >= 1, ",".join(mj_step_sources))
    check("csv_logging_sources_found", len(csv_sources) >= 1, ",".join(csv_sources))
    check("candidate_sources_found", len(candidate_sources) >= 1, ",".join(candidate_sources))
    check("recommended_source_found", recommended_source is not None, str(recommended_source))

    stage14_5e_candidate_log_header = read_csv_header(root / "results/logs_sample/stage14_5e_r1_scale_0p02_candidate_log.csv")
    check("stage14_5e_candidate_log_has_base_z", "base_z" in stage14_5e_candidate_log_header, "base_z")
    check("stage14_5e_candidate_log_lacks_base_vx", "base_vx" not in stage14_5e_candidate_log_header, "expected Stage 18 gap")
    check("stage14_5e_candidate_log_lacks_mean_vx", "mean_vx" not in stage14_5e_candidate_log_header, "expected Stage 18 gap")

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    inspection_csv = logs / "stage18_1_velocity_source_inspection.csv"
    csv_headers_csv = logs / "stage18_1_velocity_existing_csv_headers.csv"
    anchor_report = logs / "stage18_1_velocity_source_anchor_report.txt"
    validation_csv = logs / "stage18_1_velocity_source_inspection_validation.csv"
    summary_json = logs / "stage18_1_velocity_source_inspection_summary.json"
    doc = docs / "STAGE18_1_VELOCITY_SOURCE_INSPECTION.md"

    write_csv(
        inspection_csv,
        inspection_rows,
        [
            "script",
            "exists",
            "has_qpos",
            "has_qvel",
            "has_mj_step",
            "has_data_ctrl",
            "has_csv_logging",
            "has_summary",
            "has_candidate_mode",
            "has_base_z",
            "has_roll_pitch",
        ],
    )

    write_csv(
        csv_headers_csv,
        csv_header_rows,
        [
            "csv",
            "exists",
            "columns",
            "first_row",
            "has_base_x",
            "has_base_vx",
            "has_mean_vx",
            "has_base_z",
            "has_roll_pitch",
        ],
    )

    write_csv(validation_csv, checks, ["check", "status", "detail"])
    anchor_report.write_text("\n".join(anchor_report_lines) + "\n", encoding="utf-8")

    summary = {
        "stage": "18.1",
        "name": "velocity source inspection",
        "result": result,
        "failure_count": failure_count,
        "recommended_source": recommended_source,
        "qpos_sources": qpos_sources,
        "mj_step_sources": mj_step_sources,
        "csv_logging_sources": csv_sources,
        "candidate_sources": candidate_sources,
        "generated_files": [
            str(inspection_csv.relative_to(root)),
            str(csv_headers_csv.relative_to(root)),
            str(anchor_report.relative_to(root)),
            str(validation_csv.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(doc.relative_to(root)),
        ],
        "stage18_gap": [
            "existing Stage 14.5e candidate log has base_z / roll / pitch / torque fields",
            "existing Stage 14.5e candidate log does not include base_x / base_vx / mean_vx",
            "Stage 18.2 should derive a runner that adds base position and velocity metrics",
        ],
        "checks": checks,
    }
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    doc.write_text(f"""# Stage 18.1: Velocity Source Inspection

## 1. Goal

Stage 18.1 inspects existing rollout runners and evidence CSV files to determine how to add velocity tracking metrics without rewriting the controller.

## 2. Result

Stage 18.1 result: {result}

Recommended source runner:

    {recommended_source}

## 3. Findings

Existing Stage 14.5e evidence already records stability and torque-injection fields such as base height, roll, pitch, candidate scale, torque magnitude, QP failure steps, and saturation steps.

However, the existing candidate log does not include base_x, base_vx, mean_vx, or mean_abs_velocity_error. This is the main Stage 18 gap.

## 4. Generated Files

    results/logs_sample/stage18_1_velocity_source_inspection.csv
    results/logs_sample/stage18_1_velocity_existing_csv_headers.csv
    results/logs_sample/stage18_1_velocity_source_anchor_report.txt
    results/logs_sample/stage18_1_velocity_source_inspection_validation.csv
    results/logs_sample/stage18_1_velocity_source_inspection_summary.json
    docs/STAGE18_1_VELOCITY_SOURCE_INSPECTION.md

## 5. Stage 18.2 Recommendation

Derive a new Stage 18.2 runner from the recommended source runner.

The runner should add:

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

The finite-difference velocity should be treated as the auditable primary metric if qvel coordinate semantics are uncertain.

## 6. Claim Boundary

Stage 18.1 is source inspection only. It does not implement velocity tracking, does not rerun the controller, and does not claim hardware deployment.
""", encoding="utf-8")

    print(f"stage18_1_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"recommended_source: {recommended_source}")
    print(f"summary: {summary_json.relative_to(root)}")
    print(f"inspection_csv: {inspection_csv.relative_to(root)}")
    print(f"anchor_report: {anchor_report.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
