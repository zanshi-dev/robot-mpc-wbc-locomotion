#!/usr/bin/env python3
"""Generate a review-oriented artifact index for Stage 15/16 evidence."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

README_START = "<!-- STAGE16_2_ARTIFACT_INDEX_START -->"
README_END = "<!-- STAGE16_2_ARTIFACT_INDEX_END -->"
PRUNE = {".git", "build", "install", "log", "__pycache__", ".pytest_cache"}


def rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root))


def stage_key(path: Path) -> Optional[str]:
    s = str(path)
    patterns = [
        r"stage(15|16)[_-](\d+)",
        r"STAGE(15|16)[_-](\d+)",
    ]
    for pat in patterns:
        m = re.search(pat, s)
        if m:
            return f"{m.group(1)}.{int(m.group(2))}"
    if "STAGE15_UPGRADE_SUMMARY" in s:
        return "15.11"
    return None


def category(path: Path) -> str:
    p = str(path)
    if p.startswith("scripts/"):
        return "script"
    if p.startswith("docs/") or path.name in {"README.md", "PROJECT_STATUS.md"}:
        return "doc"
    if p.startswith("results/logs_sample/"):
        if path.suffix == ".log":
            return "log"
        return "result"
    return "other"


def description(path: Path, cat: str) -> str:
    name = path.name
    if cat == "script":
        if name.endswith(".sh"):
            return "validation or apply shell entrypoint"
        if "validate" in name:
            return "Python validator"
        return "Python generator or experiment script"
    if cat == "doc":
        if name == "README.md":
            return "public project overview"
        if name == "PROJECT_STATUS.md":
            return "project status summary"
        return "stage documentation"
    if cat == "log":
        return "captured terminal validation log"
    if cat == "result":
        if name.endswith("summary.json"):
            return "machine-readable summary"
        if name.endswith(".csv"):
            return "tabular validation or rollout result"
        if name.endswith(".json"):
            return "machine-readable report"
    return "artifact"


def iter_files(root: Path) -> Iterable[Path]:
    for base, dirs, files in __import__("os").walk(root):
        dirs[:] = [d for d in dirs if d not in PRUNE and not d.startswith(".stage")]
        base_path = Path(base)
        for fn in files:
            path = base_path / fn
            r = rel(path, root)
            if r.startswith("scripts/stage") or r.startswith("docs/STAGE") or r.startswith("docs/ARTIFACT_INDEX") or r.startswith("docs/STAGE15_UPGRADE_SUMMARY") or r.startswith("results/logs_sample/stage"):
                yield path


def collect(root: Path) -> List[Dict[str, Any]]:
    rows = []
    for path in sorted(iter_files(root), key=lambda p: rel(p, root)):
        key = stage_key(path)
        if key is None:
            continue
        c = category(Path(rel(path, root)))
        rows.append(
            {
                "stage": key,
                "category": c,
                "path": rel(path, root),
                "description": description(Path(rel(path, root)), c),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else 0,
            }
        )
    return rows


def stage_sort_key(stage: str) -> tuple[int, int]:
    major, minor = stage.split(".")
    return int(major), int(minor)


def write_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["stage", "category", "path", "description", "exists", "size_bytes"])
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: List[Dict[str, Any]], path: Path) -> None:
    by_stage: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        by_stage.setdefault(row["stage"], []).append(row)
    lines: List[str] = []
    lines.append("# Artifact Index")
    lines.append("")
    lines.append("This index maps Stage 15/16 evidence to scripts, documents, logs and machine-readable results.")
    lines.append("")
    lines.append("## Stage Coverage")
    lines.append("")
    lines.append("| Stage | Scripts | Docs | Results | Logs | Total |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for stage in sorted(by_stage, key=stage_sort_key):
        items = by_stage[stage]
        counts = {cat: sum(1 for item in items if item["category"] == cat) for cat in ["script", "doc", "result", "log"]}
        lines.append(f"| {stage} | {counts['script']} | {counts['doc']} | {counts['result']} | {counts['log']} | {len(items)} |")
    lines.append("")
    lines.append("## Detailed Artifacts")
    lines.append("")
    for stage in sorted(by_stage, key=stage_sort_key):
        lines.append(f"### Stage {stage}")
        lines.append("")
        lines.append("| Category | Path | Description |")
        lines.append("|---|---|---|")
        for item in sorted(by_stage[stage], key=lambda x: (x["category"], x["path"])):
            lines.append(f"| {item['category']} | `{item['path']}` | {item['description']} |")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def upsert_readme_link(repo_root: Path) -> None:
    readme = repo_root / "README.md"
    text = readme.read_text(encoding="utf-8") if readme.exists() else "# robot-mpc-wbc-locomotion\n"
    block = f"""{README_START}
## Evidence artifact index

Stage 15/16 scripts, validation logs, JSON/CSV results and documentation are indexed in:

```text
docs/ARTIFACT_INDEX.md
```

Use this index when reviewing the repository or preparing for technical reviews.
{README_END}"""
    if README_START in text and README_END in text:
        before = text.split(README_START, 1)[0].rstrip()
        after = text.split(README_END, 1)[1].lstrip()
        text = before + "\n\n" + block + "\n\n" + after
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    readme.write_text(text, encoding="utf-8")


def run(repo_root: Path) -> Dict[str, Any]:
    rows = collect(repo_root)
    stages = sorted({row["stage"] for row in rows}, key=stage_sort_key)
    md_path = repo_root / "docs/ARTIFACT_INDEX.md"
    stage_doc = repo_root / "docs/STAGE16_2_ARTIFACT_INDEX.md"
    csv_path = repo_root / "results/logs_sample/stage16_2_artifact_index.csv"
    json_path = repo_root / "results/logs_sample/stage16_2_artifact_index_summary.json"
    write_csv(rows, csv_path)
    write_markdown(rows, md_path)
    upsert_readme_link(repo_root)
    stage_doc.write_text(
        "# Stage 16.2 Artifact Index\n\n"
        "Stage 16.2 generates a review-oriented artifact index for Stage 15/16 scripts, docs, logs and machine-readable results.\n\n"
        "Primary output:\n\n"
        "```text\n"
        "docs/ARTIFACT_INDEX.md\n"
        "```\n\n"
        "Validation command:\n\n"
        "```bash\n"
        "bash scripts/stage16_2_validate_artifact_index.sh\n"
        "```\n",
        encoding="utf-8",
    )
    summary = {
        "stage": "16.2",
        "name": "artifact_index",
        "artifact_count": len(rows),
        "stages": stages,
        "stage_count": len(stages),
        "outputs": {
            "markdown": str(md_path.relative_to(repo_root)),
            "csv": str(csv_path.relative_to(repo_root)),
            "json": str(json_path.relative_to(repo_root)),
            "stage_doc": str(stage_doc.relative_to(repo_root)),
        },
        "rows": rows,
    }
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    summary = run(args.repo_root.resolve())
    print("stage16_2_index_completed: true")
    print(f"artifact_count: {summary['artifact_count']}")
    print(f"stage_count: {summary['stage_count']}")
    print(f"stages: {summary['stages']}")
    print(f"markdown: {summary['outputs']['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
