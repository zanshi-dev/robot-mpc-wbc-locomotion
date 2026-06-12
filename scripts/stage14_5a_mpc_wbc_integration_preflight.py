#!/usr/bin/env python3
from pathlib import Path
import datetime as _dt
import json
import re
import subprocess
from typing import Dict, List, Set

ROOT = Path.cwd()
STAGE = "14.5A"

SCRIPT_REL = "scripts/stage14_5a_mpc_wbc_integration_preflight.py"
DOC_REL = "docs/stage14_5a_mpc_wbc_integration_preflight.md"
CANDIDATE_REL = "results/logs_sample/stage14_5a_candidate_files.txt"
SUMMARY_REL = "results/logs_sample/stage14_5a_mpc_wbc_integration_preflight_summary.json"

DOC_PATH = ROOT / DOC_REL
CANDIDATE_PATH = ROOT / CANDIDATE_REL
SUMMARY_PATH = ROOT / SUMMARY_REL

SKIP_DIRS = {
    ".git",
    "build",
    "install",
    "log",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "demo_videos",
}

TEXT_EXTS = {
    ".py", ".cpp", ".cc", ".cxx", ".hpp", ".hh", ".h",
    ".md", ".txt", ".json", ".yaml", ".yml", ".xml",
    ".launch", ".urdf", ".xacro", ".cmake",
}

SPECIAL_NAMES = {
    "CMakeLists.txt",
    "package.xml",
}

GENERATED_PREFIXES = (
    "docs/stage14_5a_",
    "results/logs_sample/stage14_5a_",
    "scripts/stage14_5a_",
)

CATEGORY_PATTERNS: Dict[str, List[str]] = {
    "stage14_4_mpc": [
        r"stage14[_\-]?4",
        r"base[_\-]?velocity[_\-]?tracking[_\-]?mpc",
        r"receding[\- ]horizon",
        r"contact[\- ]force[\- ]mpc",
    ],
    "mujoco_or_baseline": [
        r"mujoco",
        r"mixed[\- ]baseline",
        r"frozen[\- ]baseline",
        r"standing[\- ]pd",
        r"locomotion[\- ]baseline",
        r"scene\.xml",
    ],
    "wbc_or_qp": [
        r"\bwbc\b",
        r"whole[\- ]body",
        r"\bqp\b",
        r"osqp",
        r"contact[\- ]force[\- ]qp",
        r"wrench[\- ]tracking",
    ],
    "torque_mapping": [
        r"force[\- ]to[\- ]torque",
        r"j[\^ ]?t[\- ]?f",
        r"j transpose",
        r"jacobian",
        r"pinocchio",
        r"tau",
        r"torque[\- ]mapping",
    ],
}

ALLOWED_DIRTY_PATHS = {
    SCRIPT_REL,
    DOC_REL,
    CANDIDATE_REL,
    SUMMARY_REL,
}

SENSITIVE_DIRTY_RE = re.compile(
    r"(mixed|baseline|controller|mujoco|wbc|qp|torque|disabled_controller_node|bridge)",
    re.IGNORECASE,
)


def run_git(args: List[str]) -> str:
    proc = subprocess.run(
        ["git"] + args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def should_scan(path: Path) -> bool:
    try:
        rel = path.relative_to(ROOT).as_posix()
    except ValueError:
        return False

    if any(rel.startswith(prefix) for prefix in GENERATED_PREFIXES):
        return False

    parts = set(rel.split("/"))
    if parts & SKIP_DIRS:
        return False

    if not path.is_file():
        return False

    if path.name in SPECIAL_NAMES:
        return True

    if path.suffix.lower() not in TEXT_EXTS:
        return False

    try:
        if path.stat().st_size > 2_000_000:
            return False
    except OSError:
        return False

    return True


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def parse_dirty_paths(status_text: str) -> List[str]:
    paths = []
    for line in status_text.splitlines():
        if not line.strip():
            continue
        raw = line[3:].strip()
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1].strip()
        paths.append(raw)
    return paths


def main() -> int:
    (ROOT / "docs").mkdir(parents=True, exist_ok=True)
    (ROOT / "results/logs_sample").mkdir(parents=True, exist_ok=True)

    inspected_files: List[str] = []
    matches: Dict[str, List[str]] = {key: [] for key in CATEGORY_PATTERNS}

    for path in sorted(ROOT.rglob("*")):
        if not should_scan(path):
            continue
        rel = path.relative_to(ROOT).as_posix()
        text = read_text(path)
        haystack = rel + "\n" + text

        inspected_files.append(rel)

        for category, patterns in CATEGORY_PATTERNS.items():
            if any(re.search(pattern, haystack, re.IGNORECASE) for pattern in patterns):
                matches[category].append(rel)

    for category in matches:
        matches[category] = sorted(set(matches[category]))

    all_candidate_files: List[str] = sorted(
        set(path for paths in matches.values() for path in paths)
    )

    git_status = run_git(["status", "--porcelain"])
    dirty_paths = parse_dirty_paths(git_status)
    dirty_non_stage14_5a = [
        p for p in dirty_paths
        if p not in ALLOWED_DIRTY_PATHS
    ]
    sensitive_dirty_paths = [
        p for p in dirty_non_stage14_5a
        if SENSITIVE_DIRTY_RE.search(p)
    ]

    failed_checks: List[str] = []

    if not inspected_files:
        failed_checks.append("no_text_files_inspected")

    for category, files in matches.items():
        if not files:
            failed_checks.append(f"missing_match:{category}")

    if sensitive_dirty_paths:
        failed_checks.append("sensitive_preexisting_dirty_files_detected")

    summary = {
        "stage": STAGE,
        "timestamp_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
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
        "candidate_file_count": len(all_candidate_files),
        "inspected_file_count": len(inspected_files),
        "matches": {
            category: {
                "count": len(files),
                "files": files,
            }
            for category, files in matches.items()
        },
        "all_candidate_files": all_candidate_files,
        "git": {
            "branch": run_git(["branch", "--show-current"]),
            "head": run_git(["rev-parse", "--short", "HEAD"]),
            "status_porcelain": git_status,
            "dirty_non_stage14_5a": dirty_non_stage14_5a,
            "sensitive_dirty_paths": sensitive_dirty_paths,
        },
        "generated_files": [
            SCRIPT_REL,
            DOC_REL,
            CANDIDATE_REL,
            SUMMARY_REL,
        ],
        "notes": [
            "Stage 14.5A performs inventory only.",
            "No MuJoCo closed-loop execution is performed.",
            "No WBC/QP execution is performed.",
            "No joint torque candidate is generated.",
            "No ROS torque publisher is used.",
            "No frozen mixed baseline control law is modified.",
        ],
    }

    candidate_lines: List[str] = []
    candidate_lines.append("Stage 14.5A MPC-WBC/MuJoCo integration preflight candidate files")
    candidate_lines.append(f"timestamp_utc: {summary['timestamp_utc']}")
    candidate_lines.append(f"candidate_file_count: {summary['candidate_file_count']}")
    candidate_lines.append("")
    for category, files in matches.items():
        candidate_lines.append(f"[{category}] count={len(files)}")
        for file in files:
            candidate_lines.append(file)
        candidate_lines.append("")

    CANDIDATE_PATH.write_text("\n".join(candidate_lines) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    doc_lines: List[str] = []
    doc_lines.append("# Stage 14.5A MPC-to-WBC / MuJoCo Integration Preflight")
    doc_lines.append("")
    doc_lines.append("Scope: simulation-only inventory preflight.")
    doc_lines.append("")
    doc_lines.append("This stage does not run MuJoCo closed-loop simulation, does not run WBC/QP, does not generate joint torque candidates, and does not modify the frozen mixed baseline control law.")
    doc_lines.append("")
    doc_lines.append("## Generated evidence")
    doc_lines.append("")
    doc_lines.append(f"- Candidate file list: `{CANDIDATE_REL}`")
    doc_lines.append(f"- Summary JSON: `{SUMMARY_REL}`")
    doc_lines.append("")
    doc_lines.append("## Safety flags")
    doc_lines.append("")
    for key in [
        "simulation_only_project",
        "hardware_deployment_completed",
        "torque_enable_ready",
        "torque_publisher_enabled",
        "control_law_changed",
        "mixed_baseline_modified",
        "mujoco_torque_used",
        "ros_publisher_used",
    ]:
        doc_lines.append(f"- {key}: {summary[key]}")
    doc_lines.append("")
    doc_lines.append("## Inventory summary")
    doc_lines.append("")
    doc_lines.append(f"- pass: {summary['pass']}")
    doc_lines.append(f"- failed_checks: {summary['failed_checks']}")
    doc_lines.append(f"- inspected_file_count: {summary['inspected_file_count']}")
    doc_lines.append(f"- candidate_file_count: {summary['candidate_file_count']}")
    doc_lines.append("")
    doc_lines.append("## Category matches")
    doc_lines.append("")
    for category, data in summary["matches"].items():
        doc_lines.append(f"### {category}")
        doc_lines.append("")
        doc_lines.append(f"count: {data['count']}")
        doc_lines.append("")
        for file in data["files"]:
            doc_lines.append(f"- `{file}`")
        doc_lines.append("")
    doc_lines.append("## Boundary")
    doc_lines.append("")
    doc_lines.append("The output of this stage is an interface/file inventory only. It is not MPC-WBC integration evidence, not closed-loop locomotion evidence, not hardware readiness evidence, and not real robot torque execution evidence.")
    doc_lines.append("")

    DOC_PATH.write_text("\n".join(doc_lines), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
