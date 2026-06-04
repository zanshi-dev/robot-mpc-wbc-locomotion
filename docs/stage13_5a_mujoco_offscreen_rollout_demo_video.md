# Stage 13.5A MuJoCo Offscreen Rollout Demo Video

- pass: `False`
- fail_reasons: `['ValueError(\'Image width 1280 > framebuffer width 640. Either reduce the image\\nwidth or specify a larger offscreen framebuffer in the model XML using the\\nclause:\\n<visual>\\n  <global offwidth="my_width"/>\\n</visual>\')', 'no frames rendered', 'video file missing or empty']`
- method: `MuJoCo offscreen rendering + policy rollout + raw RGB pipe to ffmpeg`
- simulation_only_project: `True`
- hardware_deployment_scope: `out_of_scope_by_user_constraint`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- baseline_type: `mixed_online_control_baseline`
- mujoco_gl_backend: `glfw`
- video_path: `/home/zanshi/robot-mpc-wbc-locomotion/demo_videos/stage13_5a_mujoco_offscreen_2400step_mixed_baseline_demo.mp4`
- video_size_bytes: `None`
- width: `1280`
- height: `720`
- fps: `60`
- render_every: `1`
- frames_rendered: `0`
- ffmpeg_returncode: `None`

This video was generated without GUI screen recording.