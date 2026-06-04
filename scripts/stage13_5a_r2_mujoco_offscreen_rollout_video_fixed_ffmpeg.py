#!/usr/bin/env /usr/bin/python3
from pathlib import Path
import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import traceback
from datetime import datetime

ROOT = Path.cwd()
OUT = ROOT / "results/logs_sample"
DOCS = ROOT / "docs"
VIDEOS = ROOT / "demo_videos"

OUT.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)
VIDEOS.mkdir(parents=True, exist_ok=True)

RUNNER = ROOT / "scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py"
STAGE134B = OUT / "stage13_4b_report_ready_package_manifest_freeze_summary.json"

VIDEO = VIDEOS / "stage13_5a_r2_mujoco_offscreen_2400step_mixed_baseline_demo_720p.mp4"
SUMMARY = OUT / "stage13_5a_r2_mujoco_offscreen_rollout_video_fixed_ffmpeg_summary.json"
DOC = DOCS / "stage13_5a_r2_mujoco_offscreen_rollout_video_fixed_ffmpeg.md"

DEMO_LOG = OUT / "stage13_5a_r2_video_rollout_mixed_baseline_log.csv"
DEMO_SUMMARY_CSV = OUT / "stage13_5a_r2_video_rollout_mixed_baseline_summary.csv"

def read_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))

def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

class Recorder:
    def __init__(self, args):
        self.args = args
        self.renderer = None
        self.camera = None
        self.proc = None
        self.step_count = 0
        self.frame_count = 0
        self.ffmpeg_stderr = ""

    def start(self, model, mujoco):
        if self.renderer is not None:
            return

        if shutil.which("ffmpeg") is None:
            raise RuntimeError("ffmpeg not found in PATH")

        self.renderer = mujoco.Renderer(
            model,
            height=self.args.render_height,
            width=self.args.render_width,
        )

        self.camera = mujoco.MjvCamera()
        self.camera.type = mujoco.mjtCamera.mjCAMERA_FREE
        self.camera.distance = self.args.camera_distance
        self.camera.azimuth = self.args.camera_azimuth
        self.camera.elevation = self.args.camera_elevation

        vf = (
            f"scale={self.args.output_width}:{self.args.output_height}:"
            "force_original_aspect_ratio=decrease,"
            f"pad={self.args.output_width}:{self.args.output_height}:(ow-iw)/2:(oh-ih)/2,"
            "format=yuv420p"
        )

        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-pix_fmt", "rgb24",
            "-s", f"{self.args.render_width}x{self.args.render_height}",
            "-r", str(self.args.fps),
            "-i", "-",
            "-vf", vf,
            "-an",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "18",
            "-movflags", "+faststart",
            str(VIDEO),
        ]

        self.proc = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

    def after_step(self, model, data, mujoco):
        self.step_count += 1
        if self.step_count % self.args.render_every != 0:
            return

        self.start(model, mujoco)

        if data.qpos.shape[0] >= 3:
            x = float(data.qpos[0])
            y = float(data.qpos[1])
            z = float(data.qpos[2])
        else:
            x, y, z = 0.0, 0.0, 0.30

        self.camera.lookat[0] = x
        self.camera.lookat[1] = y
        self.camera.lookat[2] = max(0.22, z)

        self.renderer.update_scene(data, camera=self.camera)
        frame = self.renderer.render()

        if self.proc is None or self.proc.stdin is None:
            raise RuntimeError("ffmpeg pipe is not open")

        self.proc.stdin.write(frame.tobytes())
        self.frame_count += 1

    def close(self):
        rc = None

        if self.proc is not None:
            try:
                if self.proc.stdin:
                    self.proc.stdin.close()
            except BrokenPipeError:
                pass

            if self.proc.stderr:
                self.ffmpeg_stderr = self.proc.stderr.read().decode("utf-8", errors="replace")

            rc = self.proc.wait()

        if self.renderer is not None:
            self.renderer.close()

        return rc

def parse_summary_csv(path):
    import csv
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[0] if rows else {}

def run_child(args):
    fail_reasons = []
    exception_text = ""
    ffmpeg_returncode = None

    s134b = read_json(STAGE134B)
    if s134b is None:
        fail_reasons.append("missing Stage 13.4B summary")
    elif s134b.get("pass") is not True:
        fail_reasons.append("Stage 13.4B did not pass")

    if not RUNNER.exists():
        fail_reasons.append(f"missing rollout runner: {RUNNER}")

    if VIDEO.exists():
        VIDEO.unlink()

    recorder = Recorder(args)

    try:
        if fail_reasons:
            raise RuntimeError("; ".join(fail_reasons))

        import mujoco

        original_mj_step = mujoco.mj_step

        def wrapped_mj_step(model, data, *a, **kw):
            result = original_mj_step(model, data, *a, **kw)
            recorder.after_step(model, data, mujoco)
            return result

        mujoco.mj_step = wrapped_mj_step

        spec = importlib.util.spec_from_file_location("stage13_5a_r2_runner", RUNNER)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        mod.LOG_CSV = str(DEMO_LOG)
        mod.SUMMARY_CSV = str(DEMO_SUMMARY_CSV)

        mod.main()

    except Exception as e:
        exception_text = traceback.format_exc()
        fail_reasons.append(repr(e))

    finally:
        try:
            ffmpeg_returncode = recorder.close()
        except Exception as e:
            fail_reasons.append(f"recorder close failed: {repr(e)}")

    rollout_summary = parse_summary_csv(DEMO_SUMMARY_CSV)

    if recorder.frame_count <= 0:
        fail_reasons.append("no frames rendered")

    if ffmpeg_returncode != 0:
        fail_reasons.append(f"ffmpeg returned nonzero: {ffmpeg_returncode}")

    if not VIDEO.exists() or VIDEO.stat().st_size <= 0:
        fail_reasons.append("video file missing or empty")

    if rollout_summary.get("total_steps") not in ("2400", 2400):
        fail_reasons.append(f"rollout summary total_steps mismatch: {rollout_summary.get('total_steps')}")

    if rollout_summary.get("pass") not in ("True", True):
        fail_reasons.append(f"rollout summary pass mismatch: {rollout_summary.get('pass')}")

    result = {
        "stage": "13.5A-R2",
        "name": "mujoco_offscreen_rollout_video_fixed_ffmpeg",
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
        "method": "MuJoCo offscreen rendering at 640x480 + policy rollout + raw RGB pipe to ffmpeg + aspect-correct 720p encode",
        "mujoco_gl_backend": os.environ.get("MUJOCO_GL"),
        "runner": str(RUNNER),
        "video_path": str(VIDEO),
        "video_exists": VIDEO.exists(),
        "video_size_bytes": VIDEO.stat().st_size if VIDEO.exists() else None,
        "render_width": args.render_width,
        "render_height": args.render_height,
        "output_width": args.output_width,
        "output_height": args.output_height,
        "fps": args.fps,
        "render_every": args.render_every,
        "mj_steps_seen": recorder.step_count,
        "frames_rendered": recorder.frame_count,
        "expected_frames_about": 2400 // args.render_every,
        "ffmpeg_returncode": ffmpeg_returncode,
        "ffmpeg_stderr_tail": recorder.ffmpeg_stderr[-3000:],
        "demo_rollout_log": str(DEMO_LOG),
        "demo_rollout_summary_csv": str(DEMO_SUMMARY_CSV),
        "rollout_summary": rollout_summary,
        "exception_text": exception_text,
    }

    write_json(SUMMARY, result)

    DOC.write_text(
        "\n".join([
            "# Stage 13.5A-R2 MuJoCo Offscreen Rollout Video",
            "",
            f"- pass: `{result['pass']}`",
            f"- fail_reasons: `{result['fail_reasons']}`",
            f"- method: `{result['method']}`",
            f"- mujoco_gl_backend: `{result['mujoco_gl_backend']}`",
            f"- video_path: `{result['video_path']}`",
            f"- video_size_bytes: `{result['video_size_bytes']}`",
            f"- render_size: `{result['render_width']}x{result['render_height']}`",
            f"- output_size: `{result['output_width']}x{result['output_height']}`",
            f"- fps: `{result['fps']}`",
            f"- render_every: `{result['render_every']}`",
            f"- mj_steps_seen: `{result['mj_steps_seen']}`",
            f"- frames_rendered: `{result['frames_rendered']}`",
            f"- ffmpeg_returncode: `{result['ffmpeg_returncode']}`",
            f"- rollout_total_steps: `{rollout_summary.get('total_steps')}`",
            f"- rollout_pass: `{rollout_summary.get('pass')}`",
            f"- hardware_deployment_completed: `{result['hardware_deployment_completed']}`",
            f"- torque_enable_ready: `{result['torque_enable_ready']}`",
            f"- torque_publisher_enabled: `{result['torque_publisher_enabled']}`",
            f"- control_law_changed: `{result['control_law_changed']}`",
            "",
            "This video was generated without GUI screen recording.",
        ]),
        encoding="utf-8",
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["pass"] else 1

def run_parent(args):
    backends = [x.strip() for x in args.backends.split(",") if x.strip()]
    attempt_logs = []
    fail_reasons = []

    for backend in backends:
        log_path = OUT / f"stage13_5a_r2_backend_{backend}_attempt.log"
        env = os.environ.copy()
        env["MUJOCO_GL"] = backend
        env["STAGE13_5A_R2_CHILD"] = "1"

        cmd = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--child",
            "--render-width", str(args.render_width),
            "--render-height", str(args.render_height),
            "--output-width", str(args.output_width),
            "--output-height", str(args.output_height),
            "--fps", str(args.fps),
            "--render-every", str(args.render_every),
            "--camera-distance", str(args.camera_distance),
            "--camera-azimuth", str(args.camera_azimuth),
            "--camera-elevation", str(args.camera_elevation),
        ]

        p = subprocess.run(
            cmd,
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        log_path.write_text(p.stdout, encoding="utf-8", errors="replace")
        attempt_logs.append(str(log_path))

        if p.returncode == 0:
            print(p.stdout)
            return 0

        fail_reasons.append(f"backend {backend} failed with returncode {p.returncode}")

    result = {
        "stage": "13.5A-R2",
        "name": "mujoco_offscreen_rollout_video_fixed_ffmpeg",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "pass": False,
        "fail_reasons": fail_reasons,
        "attempt_logs": attempt_logs,
        "simulation_only_project": True,
        "hardware_deployment_scope": "out_of_scope_by_user_constraint",
        "hardware_deployment_completed": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "control_law_changed": False,
        "video_path": str(VIDEO),
    }

    write_json(SUMMARY, result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--child", action="store_true")
    ap.add_argument("--backends", default="glfw,egl,osmesa")
    ap.add_argument("--render-width", type=int, default=640)
    ap.add_argument("--render-height", type=int, default=480)
    ap.add_argument("--output-width", type=int, default=1280)
    ap.add_argument("--output-height", type=int, default=720)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--render-every", type=int, default=4)
    ap.add_argument("--camera-distance", type=float, default=2.0)
    ap.add_argument("--camera-azimuth", type=float, default=135.0)
    ap.add_argument("--camera-elevation", type=float, default=-20.0)
    args = ap.parse_args()

    if args.child or os.environ.get("STAGE13_5A_R2_CHILD") == "1":
        return run_child(args)

    return run_parent(args)

if __name__ == "__main__":
    raise SystemExit(main())
