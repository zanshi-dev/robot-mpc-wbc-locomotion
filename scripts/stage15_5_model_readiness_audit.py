#!/usr/bin/env python3
"""Stage 15.5 model readiness audit.

This script scans the repository for MJCF / URDF / Xacro robot model files and
produces a readiness report for the next step: replacing the synthetic
Pinocchio Jacobian candidate map with a real model based Jacobian map.

It does not publish torque, does not run MuJoCo, and does not modify the frozen
mixed baseline.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

MODEL_SUFFIXES = {".xml", ".mjcf", ".urdf", ".xacro"}
PRUNED_DIRS = {
    ".git",
    ".stage15_1_backup",
    ".stage15_2_backup",
    ".stage15_3_backup",
    ".stage15_4_backup",
    ".stage15_5_backup",
    "build",
    "install",
    "log",
    "__pycache__",
    ".pytest_cache",
    ".colcon",
}
MODEL_TEXT_MARKERS = (
    "<mujoco",
    "<robot",
    "<worldbody",
    "<compiler",
    "<actuator",
    "<transmission",
)
NON_MODEL_NAMES = {
    "package.xml",
    "manifest.xml",
}
LEG_ALIASES = {
    "FR": ("fr", "front_right", "front-right", "front right", "right_front", "right-front", "right front", "rf"),
    "FL": ("fl", "front_left", "front-left", "front left", "left_front", "left-front", "left front", "lf"),
    "RR": ("rr", "rear_right", "rear-right", "rear right", "right_rear", "right-rear", "right rear", "hr", "hind_right", "hind-right"),
    "RL": ("rl", "rear_left", "rear-left", "rear left", "left_rear", "left-rear", "left rear", "hl", "hind_left", "hind-left"),
}
JOINT_ALIASES = {
    "hip": ("hip", "abad", "abduction", "adduction", "haa"),
    "thigh": ("thigh", "upper", "hip_pitch", "hfe", "shoulder"),
    "calf": ("calf", "lower", "knee", "shank", "kfe"),
}
FOOT_MARKERS = ("foot", "toe", "ankle", "ee", "end_effector", "end-effector")
ROOT_JOINT_MARKERS = ("root", "floating", "free", "base", "world")


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _read_text(path: Path, limit: int = 2_000_000) -> str:
    data = path.read_bytes()[:limit]
    return data.decode("utf-8", errors="ignore")


def _looks_like_robot_model(path: Path, text: str) -> bool:
    if path.name in NON_MODEL_NAMES:
        return False
    low = text.lower()
    if not any(marker in low for marker in MODEL_TEXT_MARKERS):
        return False
    if "<package" in low and "<robot" not in low and "<mujoco" not in low:
        return False
    return True


def discover_model_files(repo_root: Path) -> List[Path]:
    files: List[Path] = []
    for base, dirs, filenames in os_walk_pruned(repo_root):
        for name in filenames:
            path = base / name
            if path.suffix.lower() not in MODEL_SUFFIXES:
                continue
            try:
                text = _read_text(path)
            except OSError:
                continue
            if _looks_like_robot_model(path, text):
                files.append(path)
    return sorted(files, key=lambda p: str(p))


def os_walk_pruned(root: Path) -> Iterable[Tuple[Path, List[str], List[str]]]:
    import os

    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        dirs[:] = [d for d in dirs if d not in PRUNED_DIRS and not d.startswith(".stage")]
        yield current_path, dirs, files


@dataclass
class ModelCandidate:
    path: str
    suffix: str
    model_type: str
    parse_status: str
    parse_error: str
    joint_names: List[str]
    actuator_joint_names: List[str]
    controlled_joint_names: List[str]
    body_names: List[str]
    site_names: List[str]
    link_names: List[str]
    foot_frame_candidates: List[str]
    inferred_joint_order: Dict[str, Dict[str, Optional[str]]]
    inferred_foot_frames: Dict[str, Optional[str]]
    score: float

    @property
    def controlled_joint_count(self) -> int:
        return len(self.controlled_joint_names)

    @property
    def foot_candidate_count(self) -> int:
        return len(self.foot_frame_candidates)


def _parse_xml(path: Path) -> Tuple[Optional[ET.Element], str, str]:
    try:
        root = ET.parse(path).getroot()
        return root, "parsed", ""
    except Exception as exc:  # Xacro or partial XML may fail.
        return None, "text_fallback", f"{type(exc).__name__}: {exc}"


def _collect_named(root: ET.Element, tag: str) -> List[str]:
    out = []
    for elem in root.iter():
        if _strip_ns(elem.tag) == tag:
            name = elem.attrib.get("name")
            if name:
                out.append(name)
    return out


def _joint_type(elem: ET.Element) -> str:
    return elem.attrib.get("type", "").lower()


def _is_root_joint(name: str, joint_type: str) -> bool:
    n = _norm(name)
    if joint_type in {"free", "floating", "planar"}:
        return True
    return any(marker in n for marker in ROOT_JOINT_MARKERS) and not any(
        leg in n for aliases in LEG_ALIASES.values() for leg in aliases
    )


def _infer_leg(name: str) -> Optional[str]:
    raw = name.lower()
    normalized = _norm(name)
    tokens = set(normalized.split("_"))
    for leg, aliases in LEG_ALIASES.items():
        for alias in aliases:
            a_norm = _norm(alias)
            if a_norm in normalized or alias in raw:
                return leg
            if len(a_norm) == 2 and a_norm in tokens:
                return leg
    return None


def _infer_joint_kind(name: str) -> Optional[str]:
    normalized = _norm(name)
    for kind, aliases in JOINT_ALIASES.items():
        for alias in aliases:
            if _norm(alias) in normalized:
                return kind
    return None


def infer_joint_order(joint_names: Sequence[str]) -> Dict[str, Dict[str, Optional[str]]]:
    mapping: Dict[str, Dict[str, Optional[str]]] = {
        leg: {"hip": None, "thigh": None, "calf": None} for leg in ("FR", "FL", "RR", "RL")
    }
    for name in joint_names:
        leg = _infer_leg(name)
        kind = _infer_joint_kind(name)
        if leg and kind and mapping[leg][kind] is None:
            mapping[leg][kind] = name
    return mapping


def _is_foot_name(name: str) -> bool:
    n = _norm(name)
    return any(marker in n for marker in FOOT_MARKERS)


def infer_foot_frames(frame_names: Sequence[str]) -> Dict[str, Optional[str]]:
    mapping: Dict[str, Optional[str]] = {leg: None for leg in ("FR", "FL", "RR", "RL")}
    foot_like = [name for name in frame_names if _is_foot_name(name)]
    search_space = foot_like if foot_like else list(frame_names)
    for name in search_space:
        leg = _infer_leg(name)
        if leg and mapping[leg] is None:
            mapping[leg] = name
    return mapping


def _score_candidate(
    path: Path,
    model_type: str,
    controlled_joints: Sequence[str],
    foot_candidates: Sequence[str],
    joint_order: Dict[str, Dict[str, Optional[str]]],
    foot_frames: Dict[str, Optional[str]],
) -> float:
    score = 0.0
    p = str(path).lower()
    if model_type == "mujoco_mjcf":
        score += 10.0
    if model_type == "urdf":
        score += 9.0
    if path.suffix.lower() == ".xacro":
        score += 5.0
    if "go1" in p or "unitree" in p:
        score += 10.0
    if "asset" in p or "model" in p or "urdf" in p or "mjcf" in p:
        score += 3.0
    score += min(len(controlled_joints), 12) * 2.0
    score -= abs(len(controlled_joints) - 12) * 0.5 if controlled_joints else 0.0
    score += min(len(foot_candidates), 4) * 2.0
    mapped_joints = sum(1 for leg in joint_order.values() for value in leg.values() if value)
    score += mapped_joints * 1.5
    mapped_feet = sum(1 for value in foot_frames.values() if value)
    score += mapped_feet * 2.0
    return score


def parse_model_candidate(path: Path, repo_root: Path) -> ModelCandidate:
    root, parse_status, parse_error = _parse_xml(path)
    text = _read_text(path)
    joint_names: List[str] = []
    actuator_joint_names: List[str] = []
    controlled_joint_names: List[str] = []
    body_names: List[str] = []
    site_names: List[str] = []
    link_names: List[str] = []
    model_type = "unknown_xml"

    if root is not None:
        root_tag = _strip_ns(root.tag).lower()
        if root_tag == "mujoco" or "<mujoco" in text.lower():
            model_type = "mujoco_mjcf"
            body_names = _collect_named(root, "body")
            site_names = _collect_named(root, "site")
            for elem in root.iter():
                if _strip_ns(elem.tag) == "joint":
                    name = elem.attrib.get("name")
                    if not name:
                        continue
                    joint_names.append(name)
                    jt = _joint_type(elem)
                    if jt in {"", "hinge"} and not _is_root_joint(name, jt):
                        controlled_joint_names.append(name)
                if _strip_ns(elem.tag) in {"motor", "position", "velocity", "general"}:
                    jname = elem.attrib.get("joint")
                    if jname:
                        actuator_joint_names.append(jname)
            if actuator_joint_names:
                controlled_joint_names = [j for j in actuator_joint_names if not _is_root_joint(j, "")]
        elif root_tag == "robot" or "<robot" in text.lower():
            model_type = "urdf"
            link_names = _collect_named(root, "link")
            for elem in root.iter():
                if _strip_ns(elem.tag) != "joint":
                    continue
                name = elem.attrib.get("name")
                if not name:
                    continue
                joint_names.append(name)
                jt = _joint_type(elem)
                if jt not in {"fixed", "floating", "planar"} and not _is_root_joint(name, jt):
                    controlled_joint_names.append(name)
        else:
            model_type = root_tag or "unknown_xml"
    else:
        # Text fallback is intentionally conservative. It helps with xacro files.
        if "<mujoco" in text.lower():
            model_type = "mujoco_mjcf_text_fallback"
        elif "<robot" in text.lower():
            model_type = "urdf_xacro_text_fallback"
        names = re.findall(r"<joint[^>]*\bname=[\"']([^\"']+)[\"']", text)
        joint_names = names
        controlled_joint_names = [j for j in names if not _is_root_joint(j, "")]
        link_names = re.findall(r"<link[^>]*\bname=[\"']([^\"']+)[\"']", text)
        body_names = re.findall(r"<body[^>]*\bname=[\"']([^\"']+)[\"']", text)
        site_names = re.findall(r"<site[^>]*\bname=[\"']([^\"']+)[\"']", text)
        actuator_joint_names = re.findall(r"<(?:motor|position|velocity|general)[^>]*\bjoint=[\"']([^\"']+)[\"']", text)
        if actuator_joint_names:
            controlled_joint_names = actuator_joint_names

    # Preserve order while removing duplicates.
    def dedup(values: Sequence[str]) -> List[str]:
        seen = set()
        out = []
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            out.append(value)
        return out

    joint_names = dedup(joint_names)
    actuator_joint_names = dedup(actuator_joint_names)
    controlled_joint_names = dedup(controlled_joint_names)
    body_names = dedup(body_names)
    site_names = dedup(site_names)
    link_names = dedup(link_names)

    frame_names = site_names + body_names + link_names
    foot_candidates = dedup([name for name in frame_names if _is_foot_name(name)])
    inferred_joint_order = infer_joint_order(controlled_joint_names or joint_names)
    inferred_foot_frames = infer_foot_frames(frame_names)
    score = _score_candidate(path, model_type, controlled_joint_names, foot_candidates, inferred_joint_order, inferred_foot_frames)

    return ModelCandidate(
        path=_safe_rel(path, repo_root),
        suffix=path.suffix.lower(),
        model_type=model_type,
        parse_status=parse_status,
        parse_error=parse_error,
        joint_names=joint_names,
        actuator_joint_names=actuator_joint_names,
        controlled_joint_names=controlled_joint_names,
        body_names=body_names,
        site_names=site_names,
        link_names=link_names,
        foot_frame_candidates=foot_candidates,
        inferred_joint_order=inferred_joint_order,
        inferred_foot_frames=inferred_foot_frames,
        score=score,
    )


def _mapping_count_joint(mapping: Dict[str, Dict[str, Optional[str]]]) -> int:
    return sum(1 for leg in mapping.values() for value in leg.values() if value)


def _mapping_count_feet(mapping: Dict[str, Optional[str]]) -> int:
    return sum(1 for value in mapping.values() if value)


def build_report(repo_root: Path) -> Dict[str, Any]:
    model_paths = discover_model_files(repo_root)
    candidates = [parse_model_candidate(path, repo_root) for path in model_paths]
    candidates.sort(key=lambda c: c.score, reverse=True)
    best = candidates[0] if candidates else None

    readiness = {
        "has_model_candidate": best is not None,
        "has_12_controlled_joints": bool(best and len(best.controlled_joint_names) >= 12),
        "has_4_foot_frame_candidates": bool(best and len(best.foot_frame_candidates) >= 4),
        "has_full_inferred_joint_order": bool(best and _mapping_count_joint(best.inferred_joint_order) == 12),
        "has_full_inferred_foot_mapping": bool(best and _mapping_count_feet(best.inferred_foot_frames) == 4),
        "ready_for_real_model_jacobian_stage": False,
    }
    readiness["ready_for_real_model_jacobian_stage"] = bool(
        readiness["has_model_candidate"]
        and readiness["has_12_controlled_joints"]
        and readiness["has_4_foot_frame_candidates"]
    )

    boundary = {
        "mujoco_torque_used": False,
        "ros_publisher_used": False,
        "frozen_mixed_baseline_modified": False,
        "torque_enable_ready_claimed": False,
        "hardware_deployment_claimed": False,
        "pinocchio_jacobian_executed": False,
        "audit_only": True,
    }

    report: Dict[str, Any] = {
        "stage": "15.5",
        "name": "model_readiness_audit",
        "audit_completed": True,
        "repo_root": str(repo_root),
        "model_file_count": len(candidates),
        "candidate_models": [asdict(c) for c in candidates],
        "selected_model": asdict(best) if best else None,
        "readiness": readiness,
        "boundary": boundary,
        "notes": [
            "This stage audits model resources only.",
            "It does not execute MuJoCo torque or ROS torque publishing.",
            "The next stage should replace the Stage 15.4 synthetic Jacobian map with the selected real model if readiness is sufficient.",
        ],
    }
    return report


def write_inventory_csv(report: Dict[str, Any], path: Path) -> None:
    rows = []
    for candidate in report["candidate_models"]:
        rows.append(
            {
                "path": candidate["path"],
                "model_type": candidate["model_type"],
                "parse_status": candidate["parse_status"],
                "score": f"{candidate['score']:.3f}",
                "joint_count": len(candidate["joint_names"]),
                "actuator_joint_count": len(candidate["actuator_joint_names"]),
                "controlled_joint_count": len(candidate["controlled_joint_names"]),
                "foot_candidate_count": len(candidate["foot_frame_candidates"]),
                "mapped_joint_count": _mapping_count_joint(candidate["inferred_joint_order"]),
                "mapped_foot_count": _mapping_count_feet(candidate["inferred_foot_frames"]),
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "path",
                "model_type",
                "parse_status",
                "score",
                "joint_count",
                "actuator_joint_count",
                "controlled_joint_count",
                "foot_candidate_count",
                "mapped_joint_count",
                "mapped_foot_count",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-csv", type=Path, default=None)
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    report = build_report(repo_root)

    output_json = args.output_json or repo_root / "results/logs_sample/stage15_5_model_readiness_audit.json"
    output_csv = args.output_csv or repo_root / "results/logs_sample/stage15_5_model_readiness_audit_inventory.csv"
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_inventory_csv(report, output_csv)

    selected = report.get("selected_model") or {}
    print("stage15_5_audit_completed: true")
    print(f"model_file_count: {report['model_file_count']}")
    print(f"selected_model: {selected.get('path', '')}")
    print(f"ready_for_real_model_jacobian_stage: {report['readiness']['ready_for_real_model_jacobian_stage']}")
    print(f"audit_json: {output_json}")
    print(f"inventory_csv: {output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
