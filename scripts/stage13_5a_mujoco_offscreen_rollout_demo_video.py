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

VIDEO = VIDEOS / "stage13_5a_mujoco_offscreen_2400step_mixed_baseline_demo.mp4"
SUMMARY = OUT / "stage13_5a_mujoco_offscreen_rollout_demo_video_summary.json"
DOC = DOCS / "stage13_5a_mujoco_offscreen_rollout_demo_video.md"

DEMO_LOG = OUT / "stage13_5a_video_rollout_mixed_baseline_log.csv"
DEMO_SUMMARY_CSV = OUT / "stage13_5a_video_rollout_mixed_baseline_summary.csv"

def read_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))

def write_summary(data):
    SUMMARY.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def parent_main(args):
    backends = [x.strip() for x in args.backends.split(",") if x.strip()]
    attempt_logs = []
    fail_reasons = []

    for backend in backends:
        log_path = OUT / f"stage13_5a_backend_{backend}_attempt.log"
        env = os.environ.copy()
        env["MUJOCO_GL"] = backend
        env["STAGE13_5A_CHILD"] = "1"

        cmd = [sys.executable, str(Path(__file__).resolve()), "--child"]
        cmd += [
            "--width", str(args.width),
            "--height", str(args.height),
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

    data = {
        "stage": "13.5A",
        "name": "mujoco_offscreen_rollout_demo_video",
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
    write_summary(data)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 1

class OffscreenFFmpegRecorder:
    def __init__(self, args):
        self.args = args
        self.renderer = None
        self.camera = None
        self.ffmpeg = None
        self.step_count = 0
        self.frame_count = 0
        self.backend = os.environ.get("MUJOCO_GL", "")

    def start(self, model, mujoco):
        if self.renderer is not None:
            return

        if shutil.which("ffmpeg") is None:
            raise RuntimeError("ffmpeg not found in PATH")

        self.renderer = mujoco.Renderer(model, height=self.args.height, width=self.args.width)

        self.camera = mujoco.MjvCamera()
        self.camera.type = mujoco.mjtCamera.mjCAMERA_FREE
        self.camera.distance = self.args.camera_distance
        self.camera.azimuth = self.args.camera_azimuth
        self.camera.elevation = self.args.camera_elevation

        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-pix_fmt", "rgb24",
            "-s", f"{self.args.width}x{self.args.height}",
            "-r", str(self.args.fps),
            "-i", "-",
            "-an",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            str(VIDEO),
        ]

        self.ffmpeg = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def render_after_step(self, model, data, mujoco):
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

        if self.ffmpeg is None or self.ffmpeg.stdin is None:
            raise RuntimeError("ffmpeg pipe is not open")

        self.ffmpeg.stdin.write(frame.tobytes())
        self.frame_count += 1

    def close(self):
        ffmpeg_rc = None
        ffmpeg_stderr = ""

        if self.ffmpeg is not None:
            try:
                if self.ffmpeg.stdin:
                    self.ffmpeg.stdin.close()
            except Exception:
                pass

            out, err = self.ffmpeg.communicate()
            ffmpeg_rc = self.ffmpeg.returncode
            ffmpeg_stderr = err.decode("utf-8", errors="replace") if isinstance(err, bytes) else str(err)

        if self.renderer is not None:
            self.renderer.close()

        return ffmpeg_rc, ffmpeg_stderr

def child_main(args):
    fail_reasons = []
    ffmpeg_rc = None
    ffmpeg_stderr_tail = ""
    exception_text = ""
    frames_rendered = 0
    rollout_exception = None

    s134b = read_json(STAGE134B)
    if s134b is None:
        fail_reasons.append("missing Stage 13.4B summary")
    elif s134b.get("pass") is not True:
        fail_reasons.append("Stage 13.4B did not pass")

    if not RUNNER.exists():
        fail_reasons.append(f"missing rollout runner: {RUNNER}")

    if VIDEO.exists():
        VIDEO.unlink()

    recorder = OffscreenFFmpegRecorder(args)

    try:
        if fail_reasons:
            raise RuntimeError("; ".join(fail_reasons))

        import mujoco

        original_mj_step = mujoco.mj_step

        def wrapped_mj_step(model, data, *a, **kw):
            result = original_mj_step(model, data, *a, **kw)
            recorder.render_after_step(model, data, mujoco)
            return result

        mujoco.mj_step = wrapped_mj_step

        spec = importlib.util.spec_from_file_location("stage13_5a_rollout_runner", RUNNER)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        mod.LOG_CSV = str(DEMO_LOG)
        mod.SUMMARY_CSV = str(DEMO_SUMMARY_CSV)

        mod.main()

    except Exception as e:
        rollout_exception = e
        exception_text = traceback.format_exc()
        fail_reasons.append(repr(e))

    finally:
        try:
            ffmpeg_rc, ffmpeg_stderr = recorder.close()
            ffmpeg_stderr_tail = ffmpeg_stderr[-4000:]
        except Exception as e:
            fail_reasons.append(f"ffmpeg close failed: {repr(e)}")

    frames_rendered = recorder.frame_count

    if ffmpeg_rc not in (0, None):
        fail_reasons.append(f"ffmpeg returned nonzero: {ffmpeg_rc}")

    if frames_rendered <= 0:
        fail_reasons.append("no frames rendered")

    if not VIDEO.exists() or VIDEO.stat().st_size <= 0:
        fail_reasons.append("video file missing or empty")

    data = {
        "stage": "13.5A",
        "name": "mujoco_offscreen_rollout_demo_video",
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
        "mujoco_gl_backend": os.environ.get("MUJOCO_GL"),
        "runner": str(RUNNER),
        "video_path": str(VIDEO),
        "video_exists": VIDEO.exists(),
        "video_size_bytes": VIDEO.stat().st_size if VIDEO.exists() else None,
        "width": args.width,
        "height": args.height,
        "fps": args.fps,
        "render_every": args.render_every,
        "frames_rendered": frames_rendered,
        "ffmpeg_returncode": ffmpeg_rc,
        "ffmpeg_stderr_tail": ffmpeg_stderr_tail,
        "demo_rollout_log": str(DEMO_LOG),
        "demo_rollout_summary_csv": str(DEMO_SUMMARY_CSV),
        "exception_text": exception_text,
    }

    write_summary(data)

    doc_lines = [
        "# Stage 13.5A MuJoCo Offscreen Rollout Demo Video",
        "",
        f"- pass: `{data['pass']}`",
        f"- fail_reasons: `{data['fail_reasons']}`",
        f"- method: `{data['method']}`",
        f"- simulation_only_project: `{data['simulation_only_project']}`",
        f"- hardware_deployment_scope: `{data['hardware_deployment_scope']}`",
        f"- hardware_deployment_completed: `{data['hardware_deployment_completed']}`",
        f"- torque_enable_ready: `{data['torque_enable_ready']}`",
        f"- torque_publisher_enabled: `{data['torque_publisher_enabled']}`",
        f"- control_law_changed: `{data['control_law_changed']}`",
        f"- baseline_type: `{data['baseline_type']}`",
        f"- mujoco_gl_backend: `{data['mujoco_gl_backend']}`",
        f"- video_path: `{data['video_path']}`",
        f"- video_size_bytes: `{data['video_size_bytes']}`",
        f"- width: `{data['width']}`",
        f"- height: `{data['height']}`",
        f"- fps: `{data['fps']}`",
        f"- render_every: `{data['render_every']}`",
        f"- frames_rendered: `{data['frames_rendered']}`",
        f"- ffmpeg_returncode: `{data['ffmpeg_returncode']}`",
        "",
        "This video was generated without GUI screen recording.",
    ]
    DOC.write_text("\n".join(doc_lines), encoding="utf-8")

    print(json.dumps(data, indent=2, ensure_ascii=False))

    return 0 if data["pass"] else 1

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--child", action="store_true")
    ap.add_argument("--backends", default="egl,osmesa,glfw")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--render-every", type=int, default=1)
    ap.add_argument("--camera-distance", type=float, default=2.0)
    ap.add_argument("--camera-azimuth", type=float, default=135.0)
    ap.add_argument("--camera-elevation", type=float, default=-20.0)
    args = ap.parse_args()

    if args.child or os.environ.get("STAGE13_5A_CHILD") == "1":
        return child_main(args)

    return parent_main(args)

if __name__ == "__main__":
    raise SystemExit(main())
