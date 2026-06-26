#!/usr/bin/env python3

from __future__ import annotations

import json
import py_compile
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SENSITIVE_PATTERNS = [
    "面试",
    "实习",
    "防守",
    "简历",
    "interview",
    "resume",
    "包装",
    "候 选",
    "表述 为",
    "都 归纳",
]

REQUIRED_FILES = [
    "README.md",
    "docs/STAGE27_1_COMMAND_AND_QVEL_PERTURBATION_REGRESSION.md",
    "results/logs_sample/stage27_1_command_qvel_regression_matrix.csv",
    "results/logs_sample/stage27_1_command_qvel_regression_summary.json",
    "scripts/stage27_1_run_command_and_qvel_perturbation_regression.py",
    "scripts/stage27_2_update_readme_stage27_1_summary.py",
    "scripts/stage27_3_neutralize_public_repository_wording.py",
]

TEXT_SUFFIXES = {".md", ".py", ".txt", ".json", ".yaml", ".yml", ".csv"}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def iter_public_text_files() -> list[Path]:
    roots = [ROOT / "README.md", ROOT / "docs", ROOT / "scripts"]

    files: list[Path] = []
    for item in roots:
        if not item.exists():
            continue
        if item.is_file():
            files.append(item)
            continue
        for path in item.rglob("*"):
            if path.is_file() and path.suffix in TEXT_SUFFIXES:
                files.append(path)

    return sorted(files)


def check_sensitive_words() -> dict[str, object]:
    hits = []

    for path in iter_public_text_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pattern in SENSITIVE_PATTERNS:
                if pattern in line:
                    hits.append(
                        {
                            "file": rel(path),
                            "line": lineno,
                            "pattern": pattern,
                            "text": line.strip()[:240],
                        }
                    )

    return {
        "name": "sensitive_word_scan",
        "pass": len(hits) == 0,
        "hits": hits,
    }


def check_required_files() -> dict[str, object]:
    missing = []

    for item in REQUIRED_FILES:
        path = ROOT / item
        if not path.exists():
            missing.append(item)

    return {
        "name": "required_file_check",
        "pass": len(missing) == 0,
        "missing": missing,
    }


def check_python_compile() -> dict[str, object]:
    failures = []

    for path in sorted((ROOT / "scripts").glob("*.py")):
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            failures.append(
                {
                    "file": rel(path),
                    "error": str(exc),
                }
            )

    return {
        "name": "python_syntax_compile",
        "pass": len(failures) == 0,
        "failures": failures,
    }


def is_external_link(link: str) -> bool:
    lower = link.lower()
    return (
        lower.startswith("http://")
        or lower.startswith("https://")
        or lower.startswith("mailto:")
        or lower.startswith("#")
        or lower.startswith("tel:")
    )


def normalize_link(link: str) -> str:
    link = link.strip()

    if "#" in link:
        link = link.split("#", 1)[0]

    if "?" in link:
        link = link.split("?", 1)[0]

    return link.strip()


def check_markdown_local_links() -> dict[str, object]:
    broken = []
    markdown_files = [ROOT / "README.md"] + sorted((ROOT / "docs").rglob("*.md"))

    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

    for md in markdown_files:
        if not md.exists():
            continue

        text = md.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in link_pattern.finditer(line):
                raw_link = match.group(1).strip()

                if is_external_link(raw_link):
                    continue

                link = normalize_link(raw_link)
                if not link:
                    continue

                if link.startswith("<") and link.endswith(">"):
                    link = link[1:-1]

                candidate = (md.parent / link).resolve()

                try:
                    candidate.relative_to(ROOT)
                except ValueError:
                    broken.append(
                        {
                            "file": rel(md),
                            "line": lineno,
                            "link": raw_link,
                            "reason": "link escapes repository root",
                        }
                    )
                    continue

                if not candidate.exists():
                    broken.append(
                        {
                            "file": rel(md),
                            "line": lineno,
                            "link": raw_link,
                            "reason": "target not found",
                        }
                    )

    return {
        "name": "markdown_local_link_check",
        "pass": len(broken) == 0,
        "broken": broken,
    }


def check_no_stage27_raw_traces() -> dict[str, object]:
    patterns = [
        "results/logs_sample/stage27_1_trace_*.csv",
        "results/logs_sample/stage25_2_*stage27_1*.csv",
        "results/logs_sample/stage25_5_*stage27_1*.csv",
    ]

    matches = []
    for pattern in patterns:
        for path in ROOT.glob(pattern):
            if path.exists():
                matches.append(rel(path))

    allowed = {
        "results/logs_sample/stage27_1_command_qvel_regression_matrix.csv",
        "results/logs_sample/stage27_1_command_qvel_regression_summary.json",
    }

    residual = [item for item in matches if item not in allowed]

    return {
        "name": "stage27_raw_trace_cleanup_check",
        "pass": len(residual) == 0,
        "residual_files": residual,
    }


def check_git_clean() -> dict[str, object]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    lines = [line for line in result.stdout.splitlines() if line.strip()]

    return {
        "name": "git_worktree_clean_check",
        "pass": result.returncode == 0 and len(lines) == 0,
        "returncode": result.returncode,
        "status_lines": lines,
        "stderr": result.stderr.strip(),
    }


def write_summary(summary: dict[str, object]) -> None:
    out = ROOT / "results" / "logs_sample" / "stage27_4_public_repo_final_audit_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    checks = [
        check_sensitive_words(),
        check_required_files(),
        check_python_compile(),
        check_markdown_local_links(),
        check_no_stage27_raw_traces(),
        check_git_clean(),
    ]

    summary = {
        "stage": "27.4",
        "name": "public repository final audit",
        "result": "pass" if all(item["pass"] for item in checks) else "fail",
        "checks": checks,
    }

    write_summary(summary)

    print(json.dumps(summary, indent=2, ensure_ascii=False))

    return 0 if summary["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
