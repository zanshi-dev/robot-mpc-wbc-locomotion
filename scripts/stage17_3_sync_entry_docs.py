#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


START = "<!-- STAGE17_ENTRY_DOCS_SYNC_START -->"
END = "<!-- STAGE17_ENTRY_DOCS_SYNC_END -->"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def replace_marked_block(text: str, block: str) -> str:
    if START in text and END in text:
        before = text.split(START)[0].rstrip()
        after = text.split(END, 1)[1].lstrip()
        return before + "\n\n" + block.rstrip() + "\n\n" + after
    return text.rstrip() + "\n\n" + block.rstrip() + "\n"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "status", "detail"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    root = repo_root()
    docs = root / "docs"
    log_dir = root / "results" / "logs_sample"

    readme = root / "README.md"
    project_status = root / "PROJECT_STATUS.md"
    artifact_index = docs / "ARTIFACT_INDEX.md"

    stage17_0_summary = log_dir / "stage17_0_closed_loop_roadmap_validation_summary.json"
    stage17_1_summary = log_dir / "stage17_1_conservative_closed_loop_rollout_summary.json"
    stage17_2_summary = log_dir / "stage17_2_conservative_rollout_metrics_summary.json"

    required = [
        docs / "STAGE17_CLOSED_LOOP_ROADMAP.md",
        docs / "STAGE17_1_CONSERVATIVE_CLOSED_LOOP_ROLLOUT.md",
        docs / "STAGE17_2_CONSERVATIVE_ROLLOUT_METRICS_TABLE.md",
        stage17_0_summary,
        stage17_1_summary,
        stage17_2_summary,
        log_dir / "stage17_2_conservative_rollout_metrics_table.csv",
        log_dir / "stage17_2_conservative_rollout_metrics_table.md",
    ]

    s17_0 = load_json(stage17_0_summary)
    s17_1 = load_json(stage17_1_summary)
    s17_2 = load_json(stage17_2_summary)

    readme_block = f"""{START}
## Stage 17 — Conservative MPC/WBC Closed-Loop Rollout Evidence

Stage 17 packages the existing simulation-only MPC/WBC candidate path into conservative closed-loop rollout evidence.

Current evidence chain:

- **Stage 17.0**: closed-loop rollout roadmap and claim boundaries. See `docs/STAGE17_CLOSED_LOOP_ROADMAP.md`.
- **Stage 17.1**: conservative `scale=0.02` MPC/WBC candidate injection validation. See `docs/STAGE17_1_CONSERVATIVE_CLOSED_LOOP_ROLLOUT.md`.
- **Stage 17.2**: readable rollout metrics table for `scale=0.00 / 0.02 / 0.05 / 0.10`. See `docs/STAGE17_2_CONSERVATIVE_ROLLOUT_METRICS_TABLE.md`.

Current Stage 17 status:

```text
Stage 17.0 result: {s17_0.get("result", "unknown")}
Stage 17.1 result: {s17_1.get("result", "unknown")}
Stage 17.2 result: {s17_2.get("result", "unknown")}
```

Claim boundary:

- Simulation-only evidence.
- Conservative low-scale candidate injection.
- No real robot torque command.
- No hardware torque enablement claim.
- No velocity tracking metric in the Stage 14.5e evidence table.
- No claim that MPC/WBC comprehensively outperforms the baseline.
{END}
"""

    status_block = f"""{START}
## Stage 17 Status: Conservative Closed-Loop Rollout Evidence

Status: completed through Stage 17.2.

| Stage | Result | Evidence |
|---|---:|---|
| 17.0 | {s17_0.get("result", "unknown")} | `docs/STAGE17_CLOSED_LOOP_ROADMAP.md` |
| 17.1 | {s17_1.get("result", "unknown")} | `docs/STAGE17_1_CONSERVATIVE_CLOSED_LOOP_ROLLOUT.md` |
| 17.2 | {s17_2.get("result", "unknown")} | `docs/STAGE17_2_CONSERVATIVE_ROLLOUT_METRICS_TABLE.md` |

Stage 17 currently supports this statement:

> The project has simulation-only conservative closed-loop rollout evidence for low-scale MPC/WBC candidate injection. The evidence validates that candidate injection did not break height, attitude, QP failure, or torque saturation boundaries in the recorded sweep.

Stage 17 does not support these statements:

- Full hardware MPC-WBC controller completed.
- Real robot torque execution completed.
- High-performance locomotion controller completed.
- MPC/WBC fully outperforms the baseline.
- Velocity tracking performance has been evaluated in the Stage 14.5e evidence table.
{END}
"""

    artifact_block = f"""{START}
## Stage 17 Artifacts

All Stage 17 artifacts listed below are simulation-only evidence artifacts.

| Stage | Artifact | Purpose |
|---|---|---|
| 17.0 | `docs/STAGE17_CLOSED_LOOP_ROADMAP.md` | Closed-loop rollout roadmap and claim boundary |
| 17.0 | `results/logs_sample/stage17_0_closed_loop_roadmap_validation_summary.json` | Stage 17.0 validation summary |
| 17.1 | `scripts/stage17_1_validate_conservative_closed_loop_rollout.py` | Conservative rollout evidence validator |
| 17.1 | `docs/STAGE17_1_CONSERVATIVE_CLOSED_LOOP_ROLLOUT.md` | Stage 17.1 evidence explanation |
| 17.1 | `results/logs_sample/stage17_1_conservative_closed_loop_rollout_validation.csv` | Stage 17.1 validation checks |
| 17.1 | `results/logs_sample/stage17_1_conservative_closed_loop_rollout_summary.json` | Stage 17.1 validation summary |
| 17.2 | `scripts/stage17_2_generate_conservative_rollout_metrics_table.py` | Metrics table generator |
| 17.2 | `docs/STAGE17_2_CONSERVATIVE_ROLLOUT_METRICS_TABLE.md` | Human-readable metrics table and claim boundary |
| 17.2 | `results/logs_sample/stage17_2_conservative_rollout_metrics_table.csv` | Machine-readable Stage 17.2 metrics table |
| 17.2 | `results/logs_sample/stage17_2_conservative_rollout_metrics_table.md` | Markdown metrics table |
| 17.2 | `results/logs_sample/stage17_2_conservative_rollout_metrics_summary.json` | Stage 17.2 summary |
{END}
"""

    readme_text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    status_text = project_status.read_text(encoding="utf-8") if project_status.is_file() else ""
    index_text = artifact_index.read_text(encoding="utf-8") if artifact_index.is_file() else ""

    write(readme, replace_marked_block(readme_text, readme_block))
    write(project_status, replace_marked_block(status_text, status_block))
    write(artifact_index, replace_marked_block(index_text, artifact_block))

    stage17_3_doc = docs / "STAGE17_3_ENTRY_DOCS_SYNC.md"
    stage17_3_doc.write_text(f"""# Stage 17.3: Entry Documentation Sync

## 1. Goal

Stage 17.3 synchronizes Stage 17.0–17.2 evidence into project entry documents:

```text
README.md
PROJECT_STATUS.md
docs/ARTIFACT_INDEX.md
```

## 2. Synced claim

The synchronized documentation supports the following claim:

> The project has simulation-only conservative closed-loop rollout evidence for low-scale MPC/WBC candidate injection. The evidence validates that candidate injection did not break height, attitude, QP failure, or torque saturation boundaries in the recorded sweep.

## 3. Claim boundary

The synchronized documentation does not claim:

- real robot torque execution;
- hardware torque enablement;
- high-performance MPC-WBC locomotion;
- comprehensive superiority over the baseline;
- velocity tracking performance in the Stage 14.5e evidence table.

## 4. Generated / updated files

```text
README.md
PROJECT_STATUS.md
docs/ARTIFACT_INDEX.md
docs/STAGE17_3_ENTRY_DOCS_SYNC.md
results/logs_sample/stage17_3_entry_docs_sync_validation.csv
results/logs_sample/stage17_3_entry_docs_sync_summary.json
```
""", encoding="utf-8")

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    for path in required:
        check(f"required_exists::{path.name}", path.is_file() and path.stat().st_size > 0, str(path.relative_to(root)))

    entry_files = [readme, project_status, artifact_index]
    updated_files = [readme, project_status, artifact_index, stage17_3_doc]

    for path in entry_files:
        text = path.read_text(encoding="utf-8")
        check(f"marker_start::{path.name}", START in text, str(path.relative_to(root)))
        check(f"marker_end::{path.name}", END in text, str(path.relative_to(root)))
        check(f"mentions_simulation_only::{path.name}", "simulation-only" in text, str(path.relative_to(root)))
        check(f"mentions_stage17::{path.name}", "Stage 17" in text, str(path.relative_to(root)))

    stage17_3_text = stage17_3_doc.read_text(encoding="utf-8")
    check("stage17_3_doc_exists", stage17_3_doc.is_file() and stage17_3_doc.stat().st_size > 0, str(stage17_3_doc.relative_to(root)))
    check("mentions_simulation_only::STAGE17_3_ENTRY_DOCS_SYNC.md", "simulation-only" in stage17_3_text, str(stage17_3_doc.relative_to(root)))
    check("mentions_stage17::STAGE17_3_ENTRY_DOCS_SYNC.md", "Stage 17" in stage17_3_text, str(stage17_3_doc.relative_to(root)))

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    validation_csv = log_dir / "stage17_3_entry_docs_sync_validation.csv"
    summary_json = log_dir / "stage17_3_entry_docs_sync_summary.json"

    write_csv(validation_csv, checks)

    summary = {
        "stage": "17.3",
        "name": "entry docs sync",
        "result": result,
        "failure_count": failure_count,
        "updated_files": [str(p.relative_to(root)) for p in updated_files],
        "source_summaries": [
            str(stage17_0_summary.relative_to(root)),
            str(stage17_1_summary.relative_to(root)),
            str(stage17_2_summary.relative_to(root)),
        ],
        "validation_csv": str(validation_csv.relative_to(root)),
        "claim_boundary": [
            "simulation-only conservative closed-loop rollout evidence",
            "no real robot torque execution",
            "no hardware torque enablement",
            "no high-performance locomotion claim",
            "no comprehensive MPC/WBC superiority claim",
            "no velocity tracking metric in Stage 14.5e evidence table",
        ],
        "checks": checks,
    }

    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"stage17_3_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"updated: {', '.join(str(p.relative_to(root)) for p in updated_files)}")
    print(f"summary: {summary_json.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
