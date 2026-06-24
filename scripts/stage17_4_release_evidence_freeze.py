#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    root = repo_root()
    docs = root / "docs"
    logs = root / "results" / "logs_sample"

    required = [
        "README.md",
        "PROJECT_STATUS.md",
        "docs/ARTIFACT_INDEX.md",

        "docs/STAGE17_CLOSED_LOOP_ROADMAP.md",
        "docs/STAGE17_1_CONSERVATIVE_CLOSED_LOOP_ROLLOUT.md",
        "docs/STAGE17_2_CONSERVATIVE_ROLLOUT_METRICS_TABLE.md",
        "docs/STAGE17_3_ENTRY_DOCS_SYNC.md",

        "scripts/stage17_0_validate_closed_loop_roadmap.sh",
        "scripts/stage17_1_validate_conservative_closed_loop_rollout.py",
        "scripts/stage17_2_generate_conservative_rollout_metrics_table.py",
        "scripts/stage17_3_sync_entry_docs.py",

        "results/logs_sample/stage17_0_closed_loop_roadmap_validation_summary.json",
        "results/logs_sample/stage17_1_conservative_closed_loop_rollout_summary.json",
        "results/logs_sample/stage17_2_conservative_rollout_metrics_summary.json",
        "results/logs_sample/stage17_3_entry_docs_sync_summary.json",

        "results/logs_sample/stage17_1_conservative_closed_loop_rollout_validation.csv",
        "results/logs_sample/stage17_2_conservative_rollout_metrics_table.csv",
        "results/logs_sample/stage17_2_conservative_rollout_metrics_table.md",
        "results/logs_sample/stage17_3_entry_docs_sync_validation.csv",

        "results/logs_sample/stage14_5e_r1_candidate_robustness_scale_sweep_table.csv",
        "results/logs_sample/stage14_5e_r1_scale_0p02_candidate_log.csv",
        "results/logs_sample/stage14_5e_r1_scale_0p02_candidate_summary.csv",
    ]

    summary_files = [
        "results/logs_sample/stage17_0_closed_loop_roadmap_validation_summary.json",
        "results/logs_sample/stage17_1_conservative_closed_loop_rollout_summary.json",
        "results/logs_sample/stage17_2_conservative_rollout_metrics_summary.json",
        "results/logs_sample/stage17_3_entry_docs_sync_summary.json",
    ]

    checks: list[dict[str, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })

    for rel in required:
        path = root / rel
        check(f"required_exists::{rel}", path.is_file() and path.stat().st_size > 0, rel)

    stage_results = {}
    for rel in summary_files:
        path = root / rel
        if path.is_file():
            data = load_json(path)
            result = data.get("result", "missing")
            stage = data.get("stage", rel)
            stage_results[str(stage)] = result
            check(f"summary_result_pass::{rel}", result == "pass", f"result={result}")
        else:
            check(f"summary_result_pass::{rel}", False, "missing")

    readme_text = (root / "README.md").read_text(encoding="utf-8")
    status_text = (root / "PROJECT_STATUS.md").read_text(encoding="utf-8")
    index_text = (docs / "ARTIFACT_INDEX.md").read_text(encoding="utf-8")

    for name, text in [
        ("README.md", readme_text),
        ("PROJECT_STATUS.md", status_text),
        ("docs/ARTIFACT_INDEX.md", index_text),
    ]:
        check(f"entry_mentions_stage17::{name}", "Stage 17" in text, name)
        check(f"entry_mentions_simulation_only::{name}", "simulation-only" in text, name)
        check(f"entry_has_sync_marker::{name}", "STAGE17_ENTRY_DOCS_SYNC_START" in text and "STAGE17_ENTRY_DOCS_SYNC_END" in text, name)

    hash_rows = []
    manifest_items = []
    for rel in required:
        path = root / rel
        if path.is_file():
            digest = sha256_file(path)
            size = path.stat().st_size
        else:
            digest = ""
            size = 0

        hash_rows.append({
            "path": rel,
            "sha256": digest,
            "size_bytes": str(size),
        })
        manifest_items.append({
            "path": rel,
            "sha256": digest,
            "size_bytes": size,
            "exists": path.is_file(),
        })

    failure_count = sum(1 for c in checks if c["status"] != "PASS")
    result = "pass" if failure_count == 0 else "fail"

    validation_csv = logs / "stage17_4_release_evidence_freeze_validation.csv"
    hashes_csv = logs / "stage17_4_release_evidence_freeze_hashes.csv"
    manifest_json = logs / "stage17_4_release_evidence_manifest.json"
    summary_json = logs / "stage17_4_release_evidence_freeze_summary.json"
    freeze_doc = docs / "STAGE17_4_RELEASE_EVIDENCE_FREEZE.md"

    write_csv(validation_csv, checks, ["check", "status", "detail"])
    write_csv(hashes_csv, hash_rows, ["path", "sha256", "size_bytes"])

    manifest = {
        "stage": "17.4",
        "name": "release evidence freeze",
        "result": result,
        "stage_results": stage_results,
        "artifact_count": len(manifest_items),
        "artifacts": manifest_items,
        "claim_boundary": [
            "simulation-only conservative closed-loop rollout evidence",
            "low-scale MPC/WBC candidate injection evidence",
            "no real robot torque execution",
            "no hardware torque enablement",
            "no high-performance locomotion controller claim",
            "no comprehensive MPC/WBC superiority claim",
            "no velocity tracking metric in Stage 14.5e evidence table",
        ],
    }
    manifest_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = {
        "stage": "17.4",
        "name": "release evidence freeze",
        "result": result,
        "failure_count": failure_count,
        "generated_files": [
            str(validation_csv.relative_to(root)),
            str(hashes_csv.relative_to(root)),
            str(manifest_json.relative_to(root)),
            str(summary_json.relative_to(root)),
            str(freeze_doc.relative_to(root)),
        ],
        "stage_results": stage_results,
        "artifact_count": len(manifest_items),
        "checks": checks,
    }
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    freeze_doc.write_text(f"""# Stage 17.4: Release Evidence Freeze

## 1. Goal

Stage 17.4 freezes the Stage 17 evidence chain into a reproducible release evidence package.

This stage does not add a new controller. It packages and validates existing Stage 17.0–17.3 artifacts.

## 2. Frozen Stage Results

| Stage | Result |
|---|---|
| 17.0 | {stage_results.get("17.0", "unknown")} |
| 17.1 | {stage_results.get("17.1", "unknown")} |
| 17.2 | {stage_results.get("17.2", "unknown")} |
| 17.3 | {stage_results.get("17.3", "unknown")} |

## 3. Generated Evidence Files

```text
results/logs_sample/stage17_4_release_evidence_freeze_validation.csv
results/logs_sample/stage17_4_release_evidence_freeze_hashes.csv
results/logs_sample/stage17_4_release_evidence_manifest.json
results/logs_sample/stage17_4_release_evidence_freeze_summary.json
docs/STAGE17_4_RELEASE_EVIDENCE_FREEZE.md
```

## 4. Supported Claim

The Stage 17 release evidence supports this statement:

> The project has simulation-only conservative closed-loop rollout evidence for low-scale MPC/WBC candidate injection. The evidence validates that candidate injection did not break height, attitude, QP failure, or torque saturation boundaries in the recorded sweep.

## 5. Claim Boundary

Stage 17.4 does not support the following claims:

- real robot torque execution completed;
- hardware torque enablement completed;
- high-performance MPC-WBC locomotion controller completed;
- MPC/WBC comprehensively outperforms the baseline;
- velocity tracking performance evaluated in the Stage 14.5e evidence table.

## 6. Freeze Result

```text
stage17_4_result: {result}
failure_count: {failure_count}
artifact_count: {len(manifest_items)}
```
""", encoding="utf-8")

    print(f"stage17_4_result: {result}")
    print(f"failure_count: {failure_count}")
    print(f"artifact_count: {len(manifest_items)}")
    print(f"manifest: {manifest_json.relative_to(root)}")
    print(f"summary: {summary_json.relative_to(root)}")

    return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
