#!/usr/bin/env python3
"""Generate Stage 15 summary report from local validation artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

STAGE_META = {
    "15.1": {
        "title": "ROS2/C++ control algorithm engineering tests",
        "claim": "C++ gait scheduler, swing trajectory and torque safety filter are built and tested through ROS2/CMake/GTest.",
        "boundary": "No torque publishing or hardware execution.",
    },
    "15.2": {
        "title": "C++ contact force QP demo",
        "claim": "A C++ contact-force constraint demo validates stance/swing force allocation, normal force and friction constraints.",
        "boundary": "No OSQP C++ dependency and no closed-loop robot torque execution.",
    },
    "15.3": {
        "title": "contact force to nominal torque candidate rollout",
        "claim": "Contact force candidates are mapped to 12D torque-candidate statistics through a nominal mapping and alpha sweep.",
        "boundary": "No real Pinocchio Jacobian, no MuJoCo torque and no ROS torque publisher.",
    },
    "15.4": {
        "title": "Pinocchio Jacobian candidate rollout",
        "claim": "Pinocchio foot Jacobian based J^T f candidate rollout is available in an offline dry-run path.",
        "boundary": "Synthetic/audit kinematic model may be used; no MuJoCo torque execution.",
    },
    "15.5": {
        "title": "model readiness audit",
        "claim": "MJCF/URDF/Xacro resources are audited for controlled joints, foot frames and mapping readiness.",
        "boundary": "Audit only; no Jacobian execution or torque execution.",
    },
    "15.6": {
        "title": "real-model Jacobian candidate rollout",
        "claim": "Stage 15.5 model metadata or loadable URDF is connected to Pinocchio J^T f candidate generation.",
        "boundary": "If MJCF fallback is used, real geometry is not claimed; no MuJoCo torque execution.",
    },
    "15.7": {
        "title": "MuJoCo candidate compatibility audit",
        "claim": "MuJoCo model, joint names, actuators and candidate order are checked through kinematic mj_forward.",
        "boundary": "No mj_step and no nonzero data.ctrl.",
    },
    "15.8": {
        "title": "bounded MuJoCo torque smoke test",
        "claim": "A low-amplitude actuator command path is tested with mj_step under strict clipping.",
        "boundary": "Smoke test only; not stable locomotion and not MPC-WBC closed-loop validation.",
    },
    "15.9": {
        "title": "MuJoCo J^T f candidate injection",
        "claim": "The Stage 15.6 J^T f candidate is injected into MuJoCo with low alpha for short-horizon safety testing.",
        "boundary": "Short-horizon only; no stable locomotion claim and no hardware claim.",
    },
    "15.10": {
        "title": "MuJoCo torque-smoke policy comparison",
        "claim": "Zero ctrl, deterministic smoke waveform and J^T f candidate are compared under identical short-horizon safety metrics.",
        "boundary": "Safety/compatibility comparison only; not a walking-performance benchmark.",
    },
}

KNOWN_VALIDATION_SUMMARIES = {
    "15.5": "stage15_5_model_readiness_audit_validation_summary.json",
    "15.6": "stage15_6_real_model_jacobian_candidate_rollout_validation_summary.json",
    "15.7": "stage15_7_mujoco_candidate_compatibility_audit_validation_summary.json",
    "15.8": "stage15_8_mujoco_torque_smoke_test_validation_summary.json",
    "15.9": "stage15_9_mujoco_jtf_candidate_injection_validation_summary.json",
    "15.10": "stage15_10_mujoco_torque_smoke_policy_comparison_validation_summary.json",
}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except TypeError:
        return path.read_text(encoding="utf-8")


def find_pass_marker(log_dir: Path, stage: str) -> Dict[str, Any]:
    marker = f"stage{stage.replace('.', '_')}_result: pass"
    alt_marker = f"stage{stage.replace('.', '_')}_result:pass"
    prefix = f"stage{stage.replace('.', '_')}"
    matches = []
    for path in sorted(log_dir.glob(f"{prefix}*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".log", ".txt", ".json", ".csv"}:
            continue
        text = read_text(path)
        lower = text.lower().replace(" ", "")
        if marker in text.lower() or alt_marker in lower:
            matches.append(str(path.name))
    return {"pass_marker_found": bool(matches), "pass_marker_files": matches}


def load_validation_summary(log_dir: Path, stage: str) -> Dict[str, Any]:
    filename = KNOWN_VALIDATION_SUMMARIES.get(stage)
    if not filename:
        return {"validation_summary_found": False, "validation_pass": None, "summary_file": ""}
    path = log_dir / filename
    if not path.exists():
        return {"validation_summary_found": False, "validation_pass": None, "summary_file": filename}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"validation_summary_found": True, "validation_pass": False, "summary_file": filename, "error": str(exc)}
    return {
        "validation_summary_found": True,
        "validation_pass": bool(data.get("validation_pass", False)),
        "summary_file": filename,
        "summary_excerpt": {k: data.get(k) for k in ("stage", "mjcf_model_path", "selected_model_path", "mapped_actuator_count", "model_source", "real_geometry_loaded") if k in data},
    }


def collect_stage_status(log_dir: Path) -> List[Dict[str, Any]]:
    rows = []
    for stage, meta in STAGE_META.items():
        marker = find_pass_marker(log_dir, stage)
        validation = load_validation_summary(log_dir, stage)
        completed = bool(marker["pass_marker_found"] or validation.get("validation_pass") is True)
        rows.append(
            {
                "stage": stage,
                "title": meta["title"],
                "completed": completed,
                "claim": meta["claim"],
                "boundary": meta["boundary"],
                "pass_marker_found": marker["pass_marker_found"],
                "pass_marker_files": marker["pass_marker_files"],
                "validation_summary_found": validation.get("validation_summary_found", False),
                "validation_pass": validation.get("validation_pass"),
                "validation_summary_file": validation.get("summary_file", ""),
                "validation_summary_excerpt": validation.get("summary_excerpt", {}),
            }
        )
    return rows


def write_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "stage", "title", "completed", "claim", "boundary", "pass_marker_found",
                "pass_marker_files", "validation_summary_found", "validation_pass", "validation_summary_file",
            ],
        )
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["pass_marker_files"] = ";".join(row.get("pass_marker_files", []))
            out.pop("validation_summary_excerpt", None)
            writer.writerow(out)


def write_markdown(report: Dict[str, Any], path: Path) -> None:
    rows = report["stages"]
    completed_count = sum(1 for row in rows if row["completed"])
    lines: List[str] = []
    lines.append("# Stage 15 Upgrade Summary")
    lines.append("")
    lines.append("## 1. Status")
    lines.append("")
    lines.append(f"Completed stages: `{completed_count}/10`")
    lines.append("")
    lines.append("| Stage | Status | Main Evidence | Boundary |")
    lines.append("|---|---|---|---|")
    for row in rows:
        status = "pass" if row["completed"] else "missing"
        lines.append(f"| {row['stage']} | {status} | {row['claim']} | {row['boundary']} |")
    lines.append("")
    lines.append("## 2. What can be claimed")
    lines.append("")
    lines.append("The project can now claim the following simulation and engineering evidence:")
    lines.append("")
    for item in report["claimable_items"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## 3. What cannot be claimed")
    lines.append("")
    for item in report["non_claimable_items"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## 4. Interview phrasing")
    lines.append("")
    lines.append("> I upgraded the project in Stage 15 by closing several engineering evidence loops. First, I moved the ROS2/C++ control modules into CMake/GTest. Then I added a C++ contact-force QP demo and built a Python dry-run path from contact force to torque candidates. After that I connected the candidate chain to Pinocchio Jacobians, audited the real model resources, checked MuJoCo joint/actuator compatibility, and finally ran bounded MuJoCo torque-path smoke tests. These results are still simulation-only and short-horizon; I do not claim stable robot walking, real hardware deployment, or torque-enable readiness.")
    lines.append("")
    lines.append("## 5. Recommended next step")
    lines.append("")
    lines.append("Stage 16 should either connect the existing frozen mixed baseline to the Stage 15 candidate path with strict alpha gating, or update the README and one-page technical report so the public project description matches the new evidence.")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_report(repo_root: Path) -> Dict[str, Any]:
    log_dir = repo_root / "results/logs_sample"
    stages = collect_stage_status(log_dir)
    report = {
        "stage": "15.11",
        "name": "stage15_summary_report",
        "completed_stage_count": sum(1 for row in stages if row["completed"]),
        "total_stage_count": len(stages),
        "all_stage15_1_to_15_10_completed": all(row["completed"] for row in stages),
        "stages": stages,
        "claimable_items": [
            "ROS2/C++ control algorithm modules are buildable and testable through colcon/GTest.",
            "A C++ contact-force QP demo validates contact-mode and friction/normal-force constraints.",
            "Contact-force to torque-candidate dry-runs exist with alpha sweep evidence.",
            "Pinocchio Jacobian based J^T f candidate generation has an offline validation path.",
            "Model readiness and MuJoCo joint/actuator compatibility are audited with archived reports.",
            "Bounded MuJoCo actuator-command smoke tests and policy comparisons have been run in short horizon.",
        ],
        "non_claimable_items": [
            "Stable locomotion from the new J^T f candidate path.",
            "Full MPC-WBC closed-loop locomotion controller.",
            "Real robot deployment.",
            "ROS torque publisher readiness for hardware.",
            "torque_enable_ready=True.",
            "Realtime hardware controller completion.",
        ],
        "boundary": {
            "simulation_only": True,
            "hardware_deployment_claimed": False,
            "torque_enable_ready_claimed": False,
            "stable_locomotion_from_stage15_claimed": False,
            "full_mpc_wbc_closed_loop_claimed": False,
        },
    }
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-csv", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    log_dir = repo_root / "results/logs_sample"
    output_json = args.output_json or log_dir / "stage15_11_stage15_summary_report.json"
    output_csv = args.output_csv or log_dir / "stage15_11_stage15_summary_report.csv"
    output_md = args.output_md or repo_root / "docs/STAGE15_UPGRADE_SUMMARY.md"

    report = build_report(repo_root)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(report["stages"], output_csv)
    write_markdown(report, output_md)

    print("stage15_11_report_completed: true")
    print(f"completed_stage_count: {report['completed_stage_count']} / {report['total_stage_count']}")
    print(f"all_stage15_1_to_15_10_completed: {report['all_stage15_1_to_15_10_completed']}")
    print(f"output_json: {output_json}")
    print(f"output_csv: {output_csv}")
    print(f"output_md: {output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
