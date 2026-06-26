#!/usr/bin/env python3

from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TARGETS = [
    ROOT / "README.md",
    ROOT / "docs",
    ROOT / "scripts",
]

REPLACEMENTS = [
    ("结论表述边界", "结论表述边界"),
    ("结论表述建议", "结论表述建议"),
    ("技术表述", "技术表述"),
    ("技术说明", "技术说明"),
    ("技术说明材料", "技术说明材料"),
    ("技术复查", "技术复查"),
    ("技术问答", "技术问答"),
    ("技术复查", "技术复查"),
    ("可以说明：", "可以说明："),
    ("可以说明", "可以说明"),
    ("可以说明：", "可以说明："),
    ("可以说明", "可以说明"),
    ("技术复查", "技术复查"),
    ("项目技术要点", "项目技术要点"),
    ("工程实践", "工程实践"),
    ("项目材料", "项目材料"),
    ("docs/technical_notes/SYSTEM_3MIN_EXPLANATION.md", "docs/technical_notes/SYSTEM_3MIN_EXPLANATION.md"),
    ("docs/technical_notes", "docs/technical_notes"),
    ("SYSTEM_3MIN_EXPLANATION", "SYSTEM_3MIN_EXPLANATION"),
    ("stage14_2_readme_technical_entry_summary.json", "stage14_2_readme_technical_entry_summary.json"),
    ("review-ready", "review-ready"),
    ("technical reviews", "technical reviews"),
    ("preparing for technical reviews", "preparing for technical reviews"),
    ("how to explain Stage 15 in technical reviews", "how to explain Stage 15 in technical reviews"),
    ("technical reviews", "technical reviews"),
    ("Technical Review", "Technical Review"),
    ("TECHNICAL_REVIEW", "TECHNICAL_REVIEW"),
    ("technical_review", "technical_review"),
    ("project_material", "project_material"),
    ("Project Material", "Project Material"),
]


def iter_text_files() -> list[Path]:
    files: list[Path] = []

    for target in TARGETS:
        if not target.exists():
            continue

        if target.is_file():
            files.append(target)
            continue

        for path in target.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix in {
                ".md",
                ".py",
                ".txt",
                ".json",
                ".yaml",
                ".yml",
                ".csv",
            }:
                files.append(path)

    return files


def replace_content(path: Path) -> bool:
    try:
        old_text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False

    new_text = old_text
    for old, new in REPLACEMENTS:
        new_text = new_text.replace(old, new)

    if new_text != old_text:
        path.write_text(new_text, encoding="utf-8")
        return True

    return False


def safe_rename_path(path: Path) -> Path:
    name = path.name
    new_name = name

    name_replacements = [
        ("TECHNICAL_REVIEW", "TECHNICAL_REVIEW"),
        ("technical_review", "technical_review"),
        ("project_material", "project_material"),
        ("Project Material", "Project_Material"),
        ("技术复查", "技术复查"),
        ("工程实践", "工程实践"),
        ("项目材料", "项目材料"),
    ]

    for old, new in name_replacements:
        new_name = new_name.replace(old, new)

    if new_name == name:
        return path

    new_path = path.with_name(new_name)
    if new_path.exists():
        return path

    path.rename(new_path)
    return new_path


def rename_paths() -> None:
    technical_review_dir = ROOT / "docs" / "technical_review"
    technical_dir = ROOT / "docs" / "technical_notes"

    if technical_review_dir.exists() and technical_review_dir.is_dir():
        technical_dir.mkdir(parents=True, exist_ok=True)
        for child in list(technical_review_dir.iterdir()):
            child.rename(technical_dir / child.name)
        try:
            technical_review_dir.rmdir()
        except OSError:
            pass

    for base in [ROOT / "docs", ROOT / "scripts"]:
        if not base.exists():
            continue

        paths = sorted(base.rglob("*"), key=lambda p: len(p.parts), reverse=True)
        for path in paths:
            if path.exists():
                safe_rename_path(path)


def main() -> int:
    changed_files = []

    rename_paths()

    for path in iter_text_files():
        if replace_content(path):
            changed_files.append(str(path.relative_to(ROOT)))

    rename_paths()

    print("neutralized public repository wording")
    print("changed_files:")
    for item in changed_files:
        print(f"- {item}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
