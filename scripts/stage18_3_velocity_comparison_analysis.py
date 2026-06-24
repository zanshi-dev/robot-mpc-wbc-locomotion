#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def f(row: dict[str, str], key: str) -> float:
    return float(row[key])


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(row.get(c, "")) for c in columns) + " |")
    return "\n".join([header, sep] + body)


def main() -> int:
    root = repo_root()
    logs = root / "results" / "logs_sample"
    docs = root / "docs"

    comparison_csv = logs / "stage18_2_velocity_tracking_rollout_comparison.csv"
    stage18_2_summary = logs / "stage18_2_velocity_tracking_rollout_summary.json"

    out_csv = logs / "stage18_3_velocity_comparison_analysis.csv"
    out_md = logs / "stage18_3_velocity_comparison_analysis.md"
    validation_csv = logs / "stage18_3_velocity_comparison_analysis_validation.csv"
    summary_json = logs / "stage18_3_velocity_comparison_analysis_summary.json"
    doc = docs / "STAGE18_3_VELOCITY_COMPARISON_ANALYSIS.md"

    rows = read_csv_rows(comparison_csv)
    by_mode = {row["control_mode"]: row for row in rows}

    baseline = by_mode.get("baseline")
    candidate = by_mode.get("mpc_assisted_candidate")

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    check("stage18_2_summary_exists", stage18_2_summary.is_file() and stage18_2_summary.stat().st_size > 0, str(stage18_2_summary.relative_to(root)))
    check("comparison_csv_exists", comparison_csv.is_file() and comparison_csv.stat().st_size > 0, str(comparison_csv.relative_to(root)))
    check("has_baseline_row", baseline is not None, "baseline")
    check("has_candidate_row", candidate is not None, "mpc_assisted_candidate")

    analysis_rows: list[dict[str, str]] = []

    if baseline and candidate:
        baseline_mean_vx = f(baseline, "mean_vx")
        candidate_mean_vx = f(candidate, "mean_vx")
        baseline_error = f(baseline, "mean_abs_velocity_error")
        candidate_error = f(candidate, "mean_abs_velocity_error")
        baseline_disp = f(baseline, "forward_displacement")
        candidate_disp = f(candidate, "forward_displacement")

        delta_mean_vx = candidate_mean_vx - baseline_mean_vx
        delta_error = candidate_error - baseline_error
        delta_disp = candidate_disp - baseline_disp

        candidate_velocity_better = candidate_error < baseline_error
        both_stability_pass = baseline.get("pass") == "True" and candidate.get("pass") == "True"

        analysis_rows = [
            {
                "metric": "mean_vx",
                "baseline": f"{baseline_mean_vx:.6f}",
                "candidate": f"{candidate_mean_vx:.6f}",
                "candidate_minus_baseline": f"{delta_mean_vx:.6f}",
                "interpretation": "candidate slower than baseline" if delta_mean_vx < 0 else "candidate faster than baseline",
            },
            {
                "metric": "mean_abs_velocity_error",
                "baseline": f"{baseline_error:.6f}",
                "candidate": f"{candidate_error:.6f}",
                "candidate_minus_baseline": f"{delta_error:.6f}",
                "interpretation": "candidate worse velocity tracking" if delta_error > 0 else "candidate better velocity tracking",
            },
            {
                "metric": "forward_displacement",
                "baseline": f"{baseline_disp:.6f}",
                "candidate": f"{candidate_disp:.6f}",
                "candidate_minus_baseline": f"{delta_disp:.6f}",
                "interpretation": "candidate lower displacement" if delta_disp < 0 else "candidate higher displacement",
            },
        ]

        check("both_rows_pass_stability_boundary", both_stability_pass, f"baseline={baseline.get('pass')}, candidate={candidate.get('pass')}")
        check("candidate_velocity_result_identified", candidate_velocity_better is False, "candidate velocity tracking is not better than baseline in Stage 18.2")
        check("candidate_error_higher_than_baseline", delta_error > 0, f"delta_error={delta_error:.6f}")
        check("candidate_mean_vx_lower_than_baseline", delta_mean_vx < 0, f"delta_mean_vx={delta_mean_vx:.6f}")
        check("candidate_displacement_lower_than_baseline", delta_disp < 0, f"delta_displacement={delta_disp:.6f}")

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    if analysis_rows:
        write_csv(
            out_csv,
            analysis_rows,
            ["metric", "baseline", "candidate", "candidate_minus_baseline", "interpretation"],
        )
    else:
        write_csv(
            out_csv,
            [],
            ["metric", "baseline", "candidate", "candidate_minus_baseline", "interpretation"],
        )

    write_csv(validation_csv, checks, ["check", "status", "detail"])

    columns = ["metric", "baseline", "candidate", "candidate_minus_baseline", "interpretation"]
    table_md = markdown_table(analysis_rows, columns) if analysis_rows else ""
    out_md.write_text(table_md + "\n", encoding="utf-8")

    conclusion = (
        "The Stage 18.2 candidate injection case remains stable but does not improve velocity tracking. "
        "At target_vx=0.2 m/s, the baseline has higher mean_vx, lower mean_abs_velocity_error, and larger forward displacement."
    )

    doc.write_text(f"""# Stage 18.3: Velocity Comparison Analysis

## 1. Goal

Stage 18.3 converts the Stage 18.2 velocity rollout evidence into a clear comparison analysis.

This stage exists to prevent over-claiming. It separates two claims:

- stability boundary: both baseline and candidate pass;
- velocity tracking: baseline is better in the current Stage 18.2 evidence.

## 2. Result

Stage 18.3 result: {result}

Failure count: {failure_count}

## 3. Comparison

{table_md}

## 4. Conclusion

{conclusion}

## 5. Supported Statement

The project can state:

    Stage 18 adds simulation-only velocity evidence. In the current target_vx=0.2 m/s test, both baseline and low-scale MPC/WBC candidate injection pass stability and safety checks, but the baseline has better forward velocity tracking.

## 6. Unsupported Statement

The project cannot state:

    The low-scale MPC/WBC candidate improves velocity tracking over the baseline.

## 7. Claim Boundary

This is simulation-only evidence based on finite-difference velocity from qpos[0]. It is not hardware execution, not a full MPC-WBC velocity controller, and not proof that MPC/WBC comprehensively outperforms the baseline.
""", encoding="utf-8")

    summary = {
        "stage": "18.3",
        "name": "velocity comparison analysis",
        "result": result,
        "failure_count": failure_count,
        "source": str(comparison_csv.relative_to(root)),
        "generated_files": [
            str(out_csv.relative_to(root)),
            str(out_md.relative_to(root)),
            str(validation_csv.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(doc.relative_to(root)),
        ],
        "conclusion": conclusion,
        "claim_boundary": [
            "simulation-only velocity evidence",
            "finite-difference velocity from qpos[0]",
            "candidate remains stable but is not better on velocity tracking",
            "no real robot torque execution",
            "no comprehensive MPC/WBC superiority claim",
        ],
        "analysis_rows": analysis_rows,
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"stage18_3_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"analysis_csv: {out_csv.relative_to(root)}")
    print(f"summary: {summary_json.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
