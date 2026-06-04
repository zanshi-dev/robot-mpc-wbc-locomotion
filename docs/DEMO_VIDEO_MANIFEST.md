# Stage 13.5B Demo Video Evidence Freeze

- pass: `True`
- fail_reasons: `[]`
- method: `MuJoCo offscreen rendering + policy rollout + raw RGB pipe to ffmpeg`
- video_path: `/home/zanshi/robot-mpc-wbc-locomotion/demo_videos/stage13_5a_r2_mujoco_offscreen_2400step_mixed_baseline_demo_720p.mp4`
- video_size_bytes: `2606663`
- video_sha256: `c9fb4241bd9a64f805f2e66ccf487fd683dfaadb1d23d17e8fa46a51073114d1`
- simulation_only_project: `True`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

## FFprobe

- width: `1280`
- height: `720`
- r_frame_rate: `30/1`
- duration: `20.000000`
- nb_frames: `600`
- codec_name: `h264`
- pix_fmt: `yuv420p`

## Rollout

- total_steps: `2400`
- transition_count: `11`
- min_z: `0.274552192756`
- max_abs_roll: `0.056707402709`
- max_abs_pitch: `0.048329482530`
- max_joint_error: `0.077233662573`
- max_tau_total_abs: `9.659563043535`
- qp_fail_steps: `0`
- saturation_steps: `0`
- pass: `True`

## Final statement

Demo video frozen as simulation-only offscreen MuJoCo rollout evidence. No GUI screen recording, hardware deployment, actuator enablement, or real robot torque execution is claimed.

Next stage: `Stop at report-ready package and demo video, or Stage 14 simulation-only improvement planning`