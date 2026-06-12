#!/usr/bin/env python3
from pathlib import Path
import datetime as dt
import json
import re
import subprocess

ROOT = Path.cwd()
STAGE = "14.5D-R0"

OUT_SUMMARY = ROOT / "results/logs_sample/stage14_5d_r0_closed_loop_ab_anchor_inspection_summary.json"
OUT_CANDIDATES = ROOT / "results/logs_sample/stage14_5d_r0_closed_loop_ab_anchor_candidates.txt"
OUT_DOC = ROOT / "docs/stage14_5d_r0_closed_loop_ab_anchor_inspection.md"

SUMMARY_14_5A = ROOT / "results/logs_sample/stage14_5a_mpc_wbc_integration_preflight_summary.json"
SUMMARY_14_5B = ROOT / "results/logs_sample/stage14_5b_offline_mpc_force_to_torque_candidate_summary.json"
SUMMARY_14_5C = ROOT / "results/logs_sample/stage14_5c_mpc_force_reference_offline_qp_summary.json"

TEXT_EXTS = {".py", ".md", ".json", ".txt", ".xml", ".yaml", ".yml"}
SKIP_DIRS = {".git", "build", "install", "log", "__pycache__", ".pytest_cache", "demo_videos"}

PATTERNS = {
    "baseline_runner": [
        r"mixed[_\- ]baseline",
        r"stance[_\- ]pd[_\- ]wbc",
        r"stage13_2.*mixed",
        r"stage13_1b.*mixed",
        r"stage07_online_stance_pd_wbc_plus_swing_pd",
    ],
    "mujoco_step_loop": [
        r"mujoco",
        r"\bmj_step\b",
        r"\bdata\.ctrl\b",
        r"\bmodel\.actuator",
        r"scene\.xml",
    ],
    "torque_candidate_or_tau": [
        r"\btau\b",
        r"torque",
        r"tau_total",
        r"joint_torque",
        r"torque_limit",
    ],
    "ab_or_switch_anchor": [
        r"baseline",
        r"variant",
        r"mode",
        r"enable",
        r"argparse",
        r"summary",
        r"pass",
    ],
    "stage14_5_outputs": [
        r"stage14_5b",
        r"stage14_5c",
        r"mpc_force_reference",
        r"offline_mpc_force_to_torque",
        r"torque_candidate",
    ],
}


def read_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def git(args):
    proc = subprocess.run(
        ["git"] + args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def should_scan(path: Path) -> bool:
    if not path.is_file():
        return False
    rel = path.relative_to(ROOT).as_posix()
    if any(part in SKIP_DIRS for part in rel.split("/")):
        return False
    if path.suffix.lower() not in TEXT_EXTS:
        return False
    if path.stat().st_size > 2_000_000:
        return False
    if rel.startswith("results/logs_sample/stage14_5d_r0_"):
        return False
    if rel.startswith("docs/stage14_5d_r0_"):
        return False
    if rel.startswith("scripts/stage14_5d_r0_"):
        return False
    return True


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)

    failed_checks = []

    s145a = read_json(SUMMARY_14_5A)
    s145b = read_json(SUMMARY_14_5B)
    s145c = read_json(SUMMARY_14_5C)

    if not s145a or s145a.get("pass") is not True:
        failed_checks.append("stage14_5a_not_passed_or_missing")
    if not s145b or s145b.get("pass") is not True:
        failed_checks.append("stage14_5b_not_passed_or_missing")
    if not s145c or s145c.get("pass") is not True:
        failed_checks.append("stage14_5c_not_passed_or_missing")

    matches = {k: [] for k in PATTERNS}

    for path in sorted(ROOT.rglob("*")):
        if not should_scan(path):
            continue
        rel = path.relative_to(ROOT).as_posix()
        text = read_text(path)
        haystack = rel + "\n" + text

        for key, patterns in PATTERNS.items():
            if any(re.search(pat, haystack, re.IGNORECASE) for pat in patterns):
                matches[key].append(rel)

    for key in matches:
        matches[key] = sorted(set(matches[key]))

    for key, files in matches.items():
        if not files:
            failed_checks.append(f"missing_anchor:{key}")

    dirty = git(["status", "--porcelain"])
    dirty_paths = []
    for line in dirty.splitlines():
        if line.strip():
            dirty_paths.append(line[3:].strip())

    allowed_dirty = {
        "scripts/stage14_5d_r0_closed_loop_ab_anchor_inspection.py",
        "docs/stage14_5d_r0_closed_loop_ab_anchor_inspection.md",
        "results/logs_sample/stage14_5d_r0_closed_loop_ab_anchor_inspection_summary.json",
        "results/logs_sample/stage14_5d_r0_closed_loop_ab_anchor_candidates.txt",
    }
    dirty_non_stage = [p for p in dirty_paths if p not in allowed_dirty]

    if dirty_non_stage:
        failed_checks.append("unexpected_dirty_files_present")

    candidate_lines = [
        "Stage 14.5D-R0 closed-loop A/B anchor inspection candidates",
        f"timestamp_utc: {dt.datetime.now(dt.timezone.utc).isoformat()}",
        "",
    ]

    for key, files in matches.items():
        candidate_lines.append(f"[{key}] count={len(files)}")
        for f in files:
            candidate_lines.append(f)
        candidate_lines.append("")

    OUT_CANDIDATES.write_text("\n".join(candidate_lines), encoding="utf-8")

    summary = {
        "stage": STAGE,
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "pass": len(failed_checks) == 0,
        "failed_checks": failed_checks,
        "simulation_only_project": True,
        "hardware_deployment_completed": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "control_law_changed": False,
        "mixed_baseline_modified": False,
        "mujoco_closed_loop_ab_executed": False,
        "mujoco_torque_used": False,
        "ros_publisher_used": False,
        "mpc_assisted_switch_added": False,
        "stage14_5a_pass": None if not s145a else s145a.get("pass"),
        "stage14_5b_pass": None if not s145b else s145b.get("pass"),
        "stage14_5c_pass": None if not s145c else s145c.get("pass"),
        "matches": {k: {"count": len(v), "files": v} for k, v in matches.items()},
        "git": {
            "branch": git(["branch", "--show-current"]),
            "head": git(["rev-parse", "--short", "HEAD"]),
            "status_porcelain": dirty,
            "dirty_non_stage14_5d_r0": dirty_non_stage,
        },
        "generated_files": [
            "scripts/stage14_5d_r0_closed_loop_ab_anchor_inspection.py",
            "docs/stage14_5d_r0_closed_loop_ab_anchor_inspection.md",
            "results/logs_sample/stage14_5d_r0_closed_loop_ab_anchor_candidates.txt",
            "results/logs_sample/stage14_5d_r0_closed_loop_ab_anchor_inspection_summary.json",
        ],
        "notes": [
            "Anchor inspection only.",
            "No MuJoCo closed-loop A/B run is executed.",
            "No MPC-assisted switch is added yet.",
            "No joint torque command is sent to hardware.",
            "Frozen mixed baseline is not modified.",
        ],
    }

    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    doc = [
        "# Stage 14.5D-R0 Closed-loop A/B Anchor Inspection",
        "",
        "Scope: simulation-only source anchor inspection.",
        "",
        "This step identifies likely source files for the later Stage 14.5D baseline vs MPC-assisted closed-loop A/B implementation.",
        "",
        "It does not run MuJoCo closed-loop A/B, does not add the MPC-assisted switch, does not modify the frozen mixed baseline, and does not use ROS torque publishing.",
        "",
        "## Evidence",
        "",
        f"- Summary JSON: `{OUT_SUMMARY.relative_to(ROOT)}`",
        f"- Candidate file list: `{OUT_CANDIDATES.relative_to(ROOT)}`",
        "",
        "## Result",
        "",
        f"- pass: {summary['pass']}",
        f"- failed_checks: {summary['failed_checks']}",
        "",
        "## Anchor categories",
        "",
    ]

    for key, data in summary["matches"].items():
        doc.append(f"### {key}")
        doc.append("")
        doc.append(f"count: {data['count']}")
        doc.append("")
        for f in data["files"][:60]:
            doc.append(f"- `{f}`")
        if data["count"] > 60:
            doc.append(f"- ... truncated in docs; see `{OUT_CANDIDATES.relative_to(ROOT)}`")
        doc.append("")

    doc += [
        "## Boundary",
        "",
        "This is not MPC-assisted closed-loop locomotion evidence. It is only the source-anchor inspection needed before introducing an explicit simulation-only A/B switch.",
        "",
    ]

    OUT_DOC.write_text("\n".join(doc), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
