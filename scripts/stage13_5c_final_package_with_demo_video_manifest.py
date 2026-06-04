#!/usr/bin/env /usr/bin/python3
from pathlib import Path
import hashlib
import json
from datetime import datetime

ROOT = Path.cwd()
OUT = ROOT / "results/logs_sample"
DOCS = ROOT / "docs"
PROJECT_STATUS = ROOT / "PROJECT_STATUS.md"

STAGE134B_SUMMARY = OUT / "stage13_4b_report_ready_package_manifest_freeze_summary.json"
STAGE134B_MANIFEST = OUT / "stage13_4b_report_ready_package_manifest.json"
STAGE135B_SUMMARY = OUT / "stage13_5b_demo_video_evidence_freeze_summary.json"

SUMMARY = OUT / "stage13_5c_final_package_with_demo_video_manifest_summary.json"
FINAL_MANIFEST_JSON = OUT / "stage13_5c_final_package_with_demo_video_manifest.json"
FINAL_MANIFEST_MD = DOCS / "FINAL_PACKAGE_WITH_DEMO_VIDEO_MANIFEST.md"
DOC = DOCS / "stage13_5c_final_package_with_demo_video_manifest.md"

def read_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))

def sha256_file(path):
    p = Path(path)
    if not p.exists() or not p.is_file():
        return None
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def file_status(path):
    p = Path(path)
    return {
        "path": str(p),
        "exists": p.exists(),
        "size": p.stat().st_size if p.exists() else None,
        "sha256": sha256_file(p),
    }

fail_reasons = []

s134b = read_json(STAGE134B_SUMMARY)
m134b = read_json(STAGE134B_MANIFEST)
s135b = read_json(STAGE135B_SUMMARY)

if s134b is None or s134b.get("pass") is not True:
    fail_reasons.append("Stage 13.4B summary missing or failed")
if not isinstance(m134b, dict):
    fail_reasons.append("Stage 13.4B manifest missing or invalid")
if s135b is None or s135b.get("pass") is not True:
    fail_reasons.append("Stage 13.5B summary missing or failed")

video_path = None if s135b is None else s135b.get("video_path")
video_sha = None if s135b is None else s135b.get("video_sha256")

extra_files = {
    "stage13_5b_summary": STAGE135B_SUMMARY,
    "stage13_5b_doc": DOCS / "stage13_5b_demo_video_evidence_freeze.md",
    "demo_video_manifest": DOCS / "DEMO_VIDEO_MANIFEST.md",
}

if video_path:
    extra_files["demo_video_mp4"] = Path(video_path)
else:
    fail_reasons.append("Stage 13.5B video_path missing")

base_manifest = m134b if isinstance(m134b, dict) else {}
extra_manifest = {k: file_status(v) for k, v in extra_files.items()}
final_manifest = dict(base_manifest)
final_manifest.update(extra_manifest)

missing = [k for k, st in final_manifest.items() if not st.get("exists")]
empty = [k for k, st in final_manifest.items() if st.get("exists") and (st.get("size") is None or st.get("size") <= 0)]

if missing:
    fail_reasons.append(f"missing final package files: {missing}")
if empty:
    fail_reasons.append(f"empty final package files: {empty}")

checks = {
    "simulation_only_project": s135b is not None and s135b.get("simulation_only_project") is True,
    "hardware_deployment_completed_false": s135b is not None and s135b.get("hardware_deployment_completed") is False,
    "torque_enable_ready_false": s135b is not None and s135b.get("torque_enable_ready") is False,
    "torque_publisher_enabled_false": s135b is not None and s135b.get("torque_publisher_enabled") is False,
    "control_law_changed_false": s135b is not None and s135b.get("control_law_changed") is False,
    "baseline_type_mixed": s135b is not None and s135b.get("baseline_type") == "mixed_online_control_baseline",
    "demo_method_offscreen_rgb_ffmpeg": s135b is not None and "MuJoCo offscreen rendering" in s135b.get("method", "") and "raw RGB pipe to ffmpeg" in s135b.get("method", ""),
    "demo_video_sha_matches": (
        video_path is not None
        and Path(video_path).exists()
        and sha256_file(Path(video_path)) == video_sha
    ),
    "demo_rollout_steps_2400": s135b is not None and s135b.get("rollout_summary", {}).get("total_steps") == "2400",
    "demo_rollout_pass_true": s135b is not None and s135b.get("rollout_summary", {}).get("pass") == "True",
}

for k, ok in checks.items():
    if ok is not True:
        fail_reasons.append(f"check failed: {k}")

result = {
    "stage": "13.5C",
    "name": "final_package_with_demo_video_manifest",
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "pass": len(fail_reasons) == 0,
    "fail_reasons": fail_reasons,
    "simulation_only_project": True,
    "hardware_deployment_scope": "out_of_scope_by_user_constraint",
    "hardware_deployment_completed": False,
    "torque_enable_ready": False,
    "torque_publisher_enabled": False,
    "control_law_changed": False,
    "baseline_type": "mixed_online_control_baseline",
    "base_report_package_file_count": len(base_manifest),
    "extra_demo_file_count": len(extra_manifest),
    "final_package_file_count": len(final_manifest),
    "checks": checks,
    "final_manifest_json": str(FINAL_MANIFEST_JSON),
    "final_manifest_md": str(FINAL_MANIFEST_MD),
    "final_manifest": final_manifest,
    "final_statement": "Final package frozen with report-ready results and MuJoCo offscreen demo video. No GUI screen recording, hardware deployment, actuator enablement, or real robot torque execution is claimed.",
    "next_stage": "Stop, or Stage 14 simulation-only improvement planning",
}

FINAL_MANIFEST_JSON.write_text(json.dumps(final_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
SUMMARY.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

md_lines = [
    "# Final Package with Demo Video Manifest",
    "",
    f"- frozen_at: `{result['timestamp']}`",
    f"- pass: `{result['pass']}`",
    f"- simulation_only_project: `{result['simulation_only_project']}`",
    f"- baseline_type: `{result['baseline_type']}`",
    f"- base_report_package_file_count: `{result['base_report_package_file_count']}`",
    f"- extra_demo_file_count: `{result['extra_demo_file_count']}`",
    f"- final_package_file_count: `{result['final_package_file_count']}`",
    f"- hardware_deployment_completed: `{result['hardware_deployment_completed']}`",
    f"- torque_enable_ready: `{result['torque_enable_ready']}`",
    f"- torque_publisher_enabled: `{result['torque_publisher_enabled']}`",
    f"- control_law_changed: `{result['control_law_changed']}`",
    "",
    "## Files",
    "",
]

for name, st in final_manifest.items():
    md_lines.append(
        f"- {name}: exists=`{st.get('exists')}`, size=`{st.get('size')}`, "
        f"sha256=`{st.get('sha256')}`, path=`{st.get('path')}`"
    )

md_lines += [
    "",
    "## Final statement",
    "",
    result["final_statement"],
]

FINAL_MANIFEST_MD.write_text("\n".join(md_lines), encoding="utf-8")

doc_lines = [
    "# Stage 13.5C Final Package with Demo Video Manifest",
    "",
    f"- pass: `{result['pass']}`",
    f"- fail_reasons: `{result['fail_reasons']}`",
    f"- simulation_only_project: `{result['simulation_only_project']}`",
    f"- hardware_deployment_scope: `{result['hardware_deployment_scope']}`",
    f"- hardware_deployment_completed: `{result['hardware_deployment_completed']}`",
    f"- torque_enable_ready: `{result['torque_enable_ready']}`",
    f"- torque_publisher_enabled: `{result['torque_publisher_enabled']}`",
    f"- control_law_changed: `{result['control_law_changed']}`",
    f"- baseline_type: `{result['baseline_type']}`",
    f"- base_report_package_file_count: `{result['base_report_package_file_count']}`",
    f"- extra_demo_file_count: `{result['extra_demo_file_count']}`",
    f"- final_package_file_count: `{result['final_package_file_count']}`",
    f"- final_manifest_json: `{result['final_manifest_json']}`",
    f"- final_manifest_md: `{result['final_manifest_md']}`",
    "",
    f"Next stage: `{result['next_stage']}`",
]

DOC.write_text("\n".join(doc_lines), encoding="utf-8")

if result["pass"]:
    block = f"""

## Stage 13.5C Final Package with Demo Video Manifest

- timestamp: `{result['timestamp']}`
- pass: `True`
- simulation_only_project: `True`
- baseline_type: `mixed_online_control_baseline`
- final_package_file_count: `{result['final_package_file_count']}`
- final_manifest_json: `{FINAL_MANIFEST_JSON}`
- final_manifest_md: `{FINAL_MANIFEST_MD}`
- demo_video: `{video_path}`
- demo_video_sha256: `{video_sha}`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- next_stage: `{result['next_stage']}`
"""
    old = PROJECT_STATUS.read_text(encoding="utf-8", errors="replace") if PROJECT_STATUS.exists() else ""
    if "## Stage 13.5C Final Package with Demo Video Manifest" not in old:
        PROJECT_STATUS.write_text(old.rstrip() + block + "\n", encoding="utf-8")

print(json.dumps(result, indent=2, ensure_ascii=False))
