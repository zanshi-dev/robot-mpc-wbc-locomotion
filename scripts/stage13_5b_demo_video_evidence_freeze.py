#!/usr/bin/env /usr/bin/python3
from pathlib import Path
import hashlib
import json
import subprocess
from datetime import datetime

ROOT = Path.cwd()
OUT = ROOT / "results/logs_sample"
DOCS = ROOT / "docs"
PROJECT_STATUS = ROOT / "PROJECT_STATUS.md"

SUMMARY_IN = OUT / "stage13_5a_r2_mujoco_offscreen_rollout_video_fixed_ffmpeg_summary.json"
VIDEO = ROOT / "demo_videos/stage13_5a_r2_mujoco_offscreen_2400step_mixed_baseline_demo_720p.mp4"

SUMMARY = OUT / "stage13_5b_demo_video_evidence_freeze_summary.json"
DOC = DOCS / "stage13_5b_demo_video_evidence_freeze.md"
VIDEO_MANIFEST = DOCS / "DEMO_VIDEO_MANIFEST.md"

def read_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))

def sha256_file(path):
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def ffprobe_video(path):
    if not path.exists():
        return None
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,duration,nb_frames,codec_name,pix_fmt",
        "-of", "json",
        str(path),
    ]
    p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        return {
            "returncode": p.returncode,
            "stderr": p.stderr,
            "json": None,
        }
    return {
        "returncode": 0,
        "stderr": p.stderr,
        "json": json.loads(p.stdout),
    }

fail_reasons = []

s = read_json(SUMMARY_IN)
if s is None:
    fail_reasons.append("missing Stage 13.5A-R2 summary")
elif s.get("pass") is not True:
    fail_reasons.append("Stage 13.5A-R2 did not pass")

if not VIDEO.exists():
    fail_reasons.append("missing demo video")
elif VIDEO.stat().st_size <= 0:
    fail_reasons.append("demo video is empty")

probe = ffprobe_video(VIDEO)
if probe is None:
    fail_reasons.append("ffprobe skipped because video is missing")
elif probe.get("returncode") != 0:
    fail_reasons.append("ffprobe failed")

stream = {}
if probe and probe.get("json"):
    streams = probe["json"].get("streams", [])
    stream = streams[0] if streams else {}

video_checks = {
    "video_exists": VIDEO.exists(),
    "video_size_gt_0": VIDEO.exists() and VIDEO.stat().st_size > 0,
    "width_1280": stream.get("width") == 1280,
    "height_720": stream.get("height") == 720,
    "fps_30": stream.get("r_frame_rate") == "30/1",
    "nb_frames_600": str(stream.get("nb_frames")) == "600",
}

source_checks = {
    "stage13_5a_r2_pass": s is not None and s.get("pass") is True,
    "method_offscreen_rgb_ffmpeg": s is not None and "MuJoCo offscreen rendering" in s.get("method", "") and "raw RGB pipe to ffmpeg" in s.get("method", ""),
    "mj_steps_seen_2400": s is not None and s.get("mj_steps_seen") == 2400,
    "frames_rendered_600": s is not None and s.get("frames_rendered") == 600,
    "ffmpeg_returncode_0": s is not None and s.get("ffmpeg_returncode") == 0,
    "rollout_total_steps_2400": s is not None and s.get("rollout_summary", {}).get("total_steps") == "2400",
    "rollout_pass_true": s is not None and s.get("rollout_summary", {}).get("pass") == "True",
    "simulation_only_project": s is not None and s.get("simulation_only_project") is True,
    "hardware_deployment_completed_false": s is not None and s.get("hardware_deployment_completed") is False,
    "torque_enable_ready_false": s is not None and s.get("torque_enable_ready") is False,
    "torque_publisher_enabled_false": s is not None and s.get("torque_publisher_enabled") is False,
    "control_law_changed_false": s is not None and s.get("control_law_changed") is False,
}

for k, ok in {**video_checks, **source_checks}.items():
    if ok is not True:
        fail_reasons.append(f"check failed: {k}")

result = {
    "stage": "13.5B",
    "name": "demo_video_evidence_freeze",
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
    "method": "MuJoCo offscreen rendering + policy rollout + raw RGB pipe to ffmpeg",
    "video_path": str(VIDEO),
    "video_size_bytes": VIDEO.stat().st_size if VIDEO.exists() else None,
    "video_sha256": sha256_file(VIDEO),
    "ffprobe": probe,
    "video_checks": video_checks,
    "source_checks": source_checks,
    "rollout_summary": {} if s is None else s.get("rollout_summary", {}),
    "final_statement": "Demo video frozen as simulation-only offscreen MuJoCo rollout evidence. No GUI screen recording, hardware deployment, actuator enablement, or real robot torque execution is claimed.",
    "next_stage": "Stop at report-ready package and demo video, or Stage 14 simulation-only improvement planning",
}

SUMMARY.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

doc_lines = [
    "# Stage 13.5B Demo Video Evidence Freeze",
    "",
    f"- pass: `{result['pass']}`",
    f"- fail_reasons: `{result['fail_reasons']}`",
    f"- method: `{result['method']}`",
    f"- video_path: `{result['video_path']}`",
    f"- video_size_bytes: `{result['video_size_bytes']}`",
    f"- video_sha256: `{result['video_sha256']}`",
    f"- simulation_only_project: `{result['simulation_only_project']}`",
    f"- hardware_deployment_completed: `{result['hardware_deployment_completed']}`",
    f"- torque_enable_ready: `{result['torque_enable_ready']}`",
    f"- torque_publisher_enabled: `{result['torque_publisher_enabled']}`",
    f"- control_law_changed: `{result['control_law_changed']}`",
    "",
    "## FFprobe",
    "",
    f"- width: `{stream.get('width')}`",
    f"- height: `{stream.get('height')}`",
    f"- r_frame_rate: `{stream.get('r_frame_rate')}`",
    f"- duration: `{stream.get('duration')}`",
    f"- nb_frames: `{stream.get('nb_frames')}`",
    f"- codec_name: `{stream.get('codec_name')}`",
    f"- pix_fmt: `{stream.get('pix_fmt')}`",
    "",
    "## Rollout",
    "",
    f"- total_steps: `{result['rollout_summary'].get('total_steps')}`",
    f"- transition_count: `{result['rollout_summary'].get('transition_count')}`",
    f"- min_z: `{result['rollout_summary'].get('min_z')}`",
    f"- max_abs_roll: `{result['rollout_summary'].get('max_abs_roll')}`",
    f"- max_abs_pitch: `{result['rollout_summary'].get('max_abs_pitch')}`",
    f"- max_joint_error: `{result['rollout_summary'].get('max_joint_error')}`",
    f"- max_tau_total_abs: `{result['rollout_summary'].get('max_tau_total_abs')}`",
    f"- qp_fail_steps: `{result['rollout_summary'].get('qp_fail_steps')}`",
    f"- saturation_steps: `{result['rollout_summary'].get('saturation_steps')}`",
    f"- pass: `{result['rollout_summary'].get('pass')}`",
    "",
    "## Final statement",
    "",
    result["final_statement"],
    "",
    f"Next stage: `{result['next_stage']}`",
]

DOC.write_text("\n".join(doc_lines), encoding="utf-8")
VIDEO_MANIFEST.write_text("\n".join(doc_lines), encoding="utf-8")

if result["pass"]:
    block = f"""

## Stage 13.5B Demo Video Evidence Freeze

- timestamp: `{result['timestamp']}`
- pass: `True`
- method: `MuJoCo offscreen rendering + policy rollout + raw RGB pipe to ffmpeg`
- video_path: `{VIDEO}`
- video_size_bytes: `{result['video_size_bytes']}`
- video_sha256: `{result['video_sha256']}`
- width: `{stream.get('width')}`
- height: `{stream.get('height')}`
- fps: `{stream.get('r_frame_rate')}`
- duration: `{stream.get('duration')}`
- nb_frames: `{stream.get('nb_frames')}`
- rollout_total_steps: `{result['rollout_summary'].get('total_steps')}`
- rollout_pass: `{result['rollout_summary'].get('pass')}`
- simulation_only_project: `True`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- next_stage: `{result['next_stage']}`
"""
    old = PROJECT_STATUS.read_text(encoding="utf-8", errors="replace") if PROJECT_STATUS.exists() else ""
    if "## Stage 13.5B Demo Video Evidence Freeze" not in old:
        PROJECT_STATUS.write_text(old.rstrip() + block + "\n", encoding="utf-8")

print(json.dumps(result, indent=2, ensure_ascii=False))
