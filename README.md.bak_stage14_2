# robot-mpc-wbc-locomotion

本仓库是一个四足机器人 Go1 风格 locomotion 控制实验项目，当前交付状态为：

- 仿真-only 项目
- MuJoCo + Pinocchio 仿真验证
- mixed online control baseline
- ROS2/C++ 侧仅保留安全门控 dry-run 证据
- 包含可复现实验结果、报告级文档、图表和 MuJoCo 离屏渲染演示视频

## 项目范围

本项目当前明确限定为 **simulation-only**。

已完成内容：

- 1200-step mixed baseline 回归
- 2400-step mixed baseline robustness 回归
- 2400-step MuJoCo 离屏渲染演示视频
- 报告级结果文档和最终 manifest
- ROS2/C++ bounded zero/safe dry-run 证据

未声明内容：

- 未完成硬件部署
- 未完成执行器使能
- 未完成真实机器人力矩执行
- 不声明 `torque_enable_ready=True`
- 不声明已完成 realtime hardware controller

## 当前冻结 baseline

当前冻结 baseline 为：

`mixed_online_control_baseline`

其含义是：

- stance PD
- scaled WBC contribution
- swing PD tracking
- MuJoCo 仿真验证
- 非硬件实时控制器完成声明

## 主要结果

### 1200-step mixed baseline rerun

| 指标 | 数值 |
|---|---:|
| total_steps | 1200 |
| transition_count | 5 |
| qp_fail_steps | 0 |
| saturation_steps | 0 |
| min_z | 0.278419161322 |
| max_abs_roll | 0.056707402709 |
| max_abs_pitch | 0.048329482530 |
| max_joint_error | 0.077233662573 |
| max_tau_total_abs | 9.659563043535 |
| pass | True |

### 2400-step mixed baseline robustness regression

| 指标 | 数值 |
|---|---:|
| total_steps | 2400 |
| transition_count | 11 |
| trot_FR_RL_steps | 1200 |
| trot_FL_RR_steps | 1200 |
| qp_fail_steps | 0 |
| saturation_steps | 0 |
| min_z | 0.274552192756 |
| max_abs_roll | 0.056707402709 |
| max_abs_pitch | 0.048329482530 |
| max_joint_error | 0.077233662573 |
| max_tau_total_abs | 9.659563043535 |
| pass | True |

## 演示视频

演示视频生成方式为：

MuJoCo 离屏渲染 + policy rollout + raw RGB pipe to ffmpeg

该视频不是 GUI 录屏。

视频文件：

`demo_videos/stage13_5a_r2_mujoco_offscreen_2400step_mixed_baseline_demo_720p.mp4`

视频证据：

| 字段 | 数值 |
|---|---|
| 分辨率 | 1280x720 |
| 帧率 | 30 fps |
| 时长 | 20.000000 秒 |
| 帧数 | 600 |
| rollout_total_steps | 2400 |
| rollout_pass | True |
| sha256 | c9fb4241bd9a64f805f2e66ccf487fd683dfaadb1d23d17e8fa46a51073114d1 |

重新生成视频：

    /usr/bin/python3 scripts/stage13_5a_r2_mujoco_offscreen_rollout_video_fixed_ffmpeg.py

冻结视频证据：

    /usr/bin/python3 scripts/stage13_5b_demo_video_evidence_freeze.py

## 报告级文档

关键文档：

- `docs/FINAL_PACKAGE_WITH_DEMO_VIDEO_MANIFEST.md`
- `docs/REPORT_READY_RESULTS.md`
- `docs/REPORT_READY_CLAIMS_AND_LIMITATIONS.md`
- `docs/REPORT_READY_FIGURES.md`
- `docs/REPORT_READY_METRICS_TABLE.md`
- `docs/SIMULATION_ONLY_SCOPE.md`
- `docs/SIMULATION_ONLY_RESULTS_SUMMARY.md`
- `docs/DEMO_VIDEO_MANIFEST.md`

关键机器可读证据：

- `results/logs_sample/stage13_5c_final_package_with_demo_video_manifest_summary.json`
- `results/logs_sample/stage13_5c_final_package_with_demo_video_manifest.json`
- `results/logs_sample/stage13_5b_demo_video_evidence_freeze_summary.json`
- `results/logs_sample/stage13_2c_final_2400step_robustness_evidence_freeze_summary.json`
- `results/logs_sample/stage13_3_report_ready_metrics_table.csv`

## 最终交付状态

当前最终冻结阶段：

`Stage 13.5C Final Package with Demo Video Manifest`

冻结结果：

- pass: True
- final_package_file_count: 20
- simulation_only_project: True
- baseline_type: mixed_online_control_baseline
- hardware_deployment_completed: False
- torque_enable_ready: False
- torque_publisher_enabled: False
- control_law_changed: False

## 安全声明

本仓库不声明硬件部署完成，不声明执行器使能完成，不声明真实机器人力矩执行完成。当前证据仅支持 simulation-only locomotion baseline、报告级结果包和 MuJoCo 离屏渲染演示视频。
