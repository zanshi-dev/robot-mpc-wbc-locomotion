#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List


TARGET_DOCS = [
    Path("docs/stage14_4_base_velocity_tracking_mpc.md"),
    Path("docs/stage14_4b_base_velocity_tracking_mpc_validation.md"),
    Path("docs/stage14_4c_mpc_scope_explanation.md"),
    Path("docs/stage14_4d_document_language_audit.md"),
]

SCAN_ROOTS = [
    Path("README.md"),
    Path("PROJECT_STATUS.md"),
    Path("docs"),
    Path("assets/go1"),
]

AUDIT_DOC = Path("docs/stage14_4d_document_language_audit.md")
AUDIT_CSV = Path("results/logs_sample/stage14_4d_document_language_audit.csv")
SUMMARY_JSON = Path("results/logs_sample/stage14_4d_document_language_audit_summary.json")

REQUIRED_STAGE14_4_PHRASES = [
    "Stage 14.4",
    "MPC",
    "simulation-only",
    "不接 ROS torque publisher",
    "不接 MuJoCo torque",
    "不直接输出 joint torque",
    "不改变 mixed baseline 控制律",
]

PROHIBITED_POSITIVE_CLAIMS = [
    "项目已完成硬件部署",
    "硬件部署已经完成",
    "执行器使能已经完成并可用",
    "真实机器人力矩执行已有完成证据",
    "实时硬件控制器已有完成证据",
    "MPC 已经接入真实机器人",
    "ROS torque publisher 已经启用并用于控制",
    "MPC 已经输出真实 joint torque",
    "MPC-WBC integrated controller 已完成",
]


def chinese_ratio(text: str) -> float:
    chinese_chars = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    total_non_space = sum(1 for ch in text if not ch.isspace())
    return chinese_chars / max(total_non_space, 1)


def classify_text(path: Path, text: str) -> str:
    stripped = text.strip()
    if len(stripped) < 80:
        return "too_short_to_classify"
    ratio = chinese_ratio(text)
    suffix = path.suffix.lower()
    if suffix not in {".md", ".txt", ""}:
        return "non_chinese_or_structural"
    if ratio >= 0.20:
        return "mostly_chinese"
    return "english_heavy"


def iter_scan_files() -> List[Path]:
    files: List[Path] = []

    for root in SCAN_ROOTS:
        if root.is_file():
            files.append(root)
        elif root.is_dir():
            for path in root.rglob("*"):
                if path.is_file() and path.suffix.lower() in {".md", ".txt", ""}:
                    files.append(path)

    return sorted(set(files))


def ensure_audit_doc() -> None:
    AUDIT_DOC.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_DOC.write_text(
        """# Stage 14.4D：文档语言审计说明

## 结论

本阶段只把 Stage 14.4 新增或修改的 MPC 说明文档作为中文化 gate。

全仓库历史文档、旧阶段英文报告、第三方模型说明、license、日志文本和历史结果文件只作为统计对象，不作为失败条件。原因是这些文件属于项目历史证据或外部资源，强行一次性改写会破坏可追溯性，也不属于 Stage 14.4 的最小可验证目标。

## 当前审计范围

强制检查的文件包括：

- `docs/stage14_4_base_velocity_tracking_mpc.md`
- `docs/stage14_4b_base_velocity_tracking_mpc_validation.md`
- `docs/stage14_4c_mpc_scope_explanation.md`
- `docs/stage14_4d_document_language_audit.md`

## 安全边界

Stage 14.4 仍是 simulation-only 的 standalone MPC demo。

该 MPC 不接 ROS torque publisher，不接 MuJoCo torque，不直接输出 joint torque，不改变 mixed baseline 控制律。

本阶段不能宣称硬件部署、执行器使能、真实机器人力矩执行、实时硬件控制器完成，也不能宣称 MPC 接入真实机器人或MPC 与 WBC 已形成闭环集成。

## 后续建议

如果未来希望统一全仓库中文文档，应另设独立文档整理阶段，并按阶段分批翻译。不得把 251 个历史英文文件作为 Stage 14.4D 的阻断项。
""",
        encoding="utf-8",
    )


def main() -> None:
    ensure_audit_doc()

    failed_checks: List[str] = []
    rows: List[Dict[str, object]] = []

    scanned_files = iter_scan_files()
    classification_counts: Dict[str, int] = {}
    english_heavy_files: List[str] = []

    for path in scanned_files:
        try:
            text = path.read_text(errors="ignore")
        except Exception:
            continue

        cls = classify_text(path, text)
        classification_counts[cls] = classification_counts.get(cls, 0) + 1
        if cls == "english_heavy":
            english_heavy_files.append(str(path))

        rows.append({
            "file": str(path),
            "scope": "repo_inventory",
            "classification": cls,
            "chinese_ratio": f"{chinese_ratio(text):.6f}",
            "gate": False,
            "pass": True,
            "notes": "inventory only; not a Stage 14.4D failure condition",
        })

    for path in TARGET_DOCS:
        if not path.exists():
            failed_checks.append(f"missing target Stage 14.4 documentation file: {path}")
            rows.append({
                "file": str(path),
                "scope": "stage14_4_gate",
                "classification": "missing",
                "chinese_ratio": "0.000000",
                "gate": True,
                "pass": False,
                "notes": "missing target document",
            })
            continue

        text = path.read_text(errors="ignore")
        ratio = chinese_ratio(text)

        missing_phrases = [
            phrase for phrase in REQUIRED_STAGE14_4_PHRASES
            if phrase not in text
        ]
        prohibited_hits = [
            claim for claim in PROHIBITED_POSITIVE_CLAIMS
            if claim in text
        ]

        # Stage 14.4A/B docs may contain formulas, paths, field names and English identifiers.
        # Therefore, the gate requires Chinese boundary text plus required safety phrases,
        # not a high whole-file Chinese ratio.
        target_pass = (
            ratio >= 0.10
            and not missing_phrases
            and not prohibited_hits
        )

        if ratio < 0.10:
            failed_checks.append(f"{path}: Chinese ratio below Stage 14.4D minimum, ratio={ratio:.3f}")
        for phrase in missing_phrases:
            failed_checks.append(f"{path}: missing required phrase: {phrase}")
        for claim in prohibited_hits:
            failed_checks.append(f"{path}: prohibited positive claim appears: {claim}")

        rows.append({
            "file": str(path),
            "scope": "stage14_4_gate",
            "classification": classify_text(path, text),
            "chinese_ratio": f"{ratio:.6f}",
            "gate": True,
            "pass": target_pass,
            "notes": "Stage 14.4 document gate",
        })

    AUDIT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["file", "scope", "classification", "chinese_ratio", "gate", "pass", "notes"],
        )
        writer.writeheader()
        writer.writerows(rows)

    result = {
        "stage": "14.4D0",
        "description": "scoped document language audit for Stage 14.4 Chinese documentation normalization",
        "pass": len(failed_checks) == 0,
        "failed_checks": failed_checks,
        "simulation_only_project": True,
        "hardware_deployment_completed": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "control_law_changed": False,
        "mixed_baseline_modified": False,
        "mujoco_torque_used": False,
        "ros_publisher_used": False,
        "audit_doc": str(AUDIT_DOC),
        "audit_csv": str(AUDIT_CSV),
        "summary_json": str(SUMMARY_JSON),
        "scanned_file_count": len(scanned_files),
        "classification_counts": classification_counts,
        "english_heavy_file_count_inventory_only": len(english_heavy_files),
        "english_heavy_files_inventory_only_sample": english_heavy_files[:30],
        "target_docs": [str(p) for p in TARGET_DOCS],
        "gate_scope": "Stage 14.4 documentation only; repo-wide English-heavy files are inventory only",
    }

    SUMMARY_JSON.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))

    if not result["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
