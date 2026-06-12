# robot-mpc-wbc-locomotion

Go1 风格四足机器人 locomotion 控制项目。当前项目定位为 **simulation-only**，重点是构建一条可解释、可回归、可演示的控制链路，而不是声明真实硬件部署完成。

项目最终 baseline 是 `mixed_online_control_baseline`。它不是 pure full WBC locomotion controller，也不是 realtime hardware controller；它是一个在 MuJoCo 中验证通过、结构清楚、能解释失败路径的 mixed control baseline。

<!-- STAGE14_5_STATUS_START -->

## 当前状态：Stage 14.5 MPC/WBC simulation-only milestone

当前仓库已完成 **Stage 14.5 simulation-only MPC/WBC candidate evidence packaging and robustness indexing**，并已冻结最终证据链。

最新完成节点：

- `Stage 14.5A-C`: MPC/WBC integration preflight、offline MPC force-to-torque candidate、offline force-reference QP check
- `Stage 14.5D-R0..R9`: closed-loop baseline/candidate simulation-only evidence packaging
- `Stage 14.5E-R0..R3`: candidate robustness envelope evidence through scale `0.10`
- `Stage 14.5F-R0..R2`: release evidence index、milestone release-note draft、final simulation-only milestone freeze

最终安全结论：

> Stage 14.5 completed simulation-only MPC/WBC candidate evidence packaging and robustness indexing up to candidate scale 0.10.

边界声明：

- 本项目当前仍是 **simulation-only**
- `hardware_deployment_completed: false`
- `torque_enable_ready: false`
- `torque_publisher_enabled: false`
- `real_robot_torque_commanded: false`
- `ros_publisher_used: false`
- MPC 输出的是 contact-force reference / candidate evidence；joint torque candidate 由 WBC/QP 或 `J^T f` 映射层生成
- 不声明真实机器人部署完成，不声明 torque-enable ready，不声明 MPC 直接输出 joint torque

### Stage 14.5 关键冻结指标

Baseline 2400-step simulation evidence:

- total_steps: `2400`
- pass: `true`
- min_z: `0.274552192756`
- max_abs_roll: `0.056707402709`
- max_abs_pitch: `0.048329482530`
- max_tau_total_abs: `9.659563043535`
- qp_fail_steps: `0`
- saturation_steps: `0`

MPC-assisted candidate 2400-step simulation evidence at scale `0.05`:

- total_steps: `2400`
- pass: `true`
- min_z: `0.276975761939`
- max_abs_roll: `0.102952660101`
- max_abs_pitch: `0.053162351948`
- max_tau_total_abs: `10.019186119959`
- max_tau_candidate_scaled_abs: `0.972125472365`
- qp_fail_steps: `0`
- saturation_steps: `0`

Robustness envelope:

- planned scales: `0.00 / 0.02 / 0.05 / 0.10`
- positive candidate scales executed: `0.02 / 0.05 / 0.10`
- validated_candidate_scale_max_simulation_only: `0.10`
- min_z_min_over_entries: `0.273040429683`
- max_abs_roll_max_over_entries: `0.102952660101`
- max_abs_pitch_max_over_entries: `0.077452968358`
- max_tau_total_abs_max_over_entries: `10.59512016256`
- max_tau_candidate_scaled_abs_max_over_candidate_runs: `1.94425094473`
- total_qp_fail_steps: `0`
- total_saturation_steps: `0`

### Final freeze artifacts

- `docs/stage14_5f_r2_final_simulation_only_milestone_freeze.md`
- `results/logs_sample/stage14_5f_r2_final_simulation_only_milestone_freeze_summary.json`
- `results/logs_sample/stage14_5f_r2_final_simulation_only_milestone_manifest.json`
- `docs/stage14_5f_r1_simulation_only_milestone_release_note_draft.md`
- `results/logs_sample/stage14_5f_r0_release_evidence_index.csv`

<!-- STAGE14_5_STATUS_END -->



## 1. 项目目标

本项目的目标是围绕四足机器人 locomotion 搭建完整控制架构：

- MuJoCo 仿真环境
- Pinocchio 运动学与动力学模型
- MuJoCo-Pinocchio 状态映射
- gait scheduler
- contact planner
- swing trajectory generator
- contact force QP / WBC QP
- torque mapping
- stance PD + swing PD tracking
- torque safety gate
- ROS2/C++ zero-safe dry-run evidence
- MuJoCo offscreen demo video

项目采用阶段化路线，不直接跳到完整硬件控制器。原因是四足机器人系统高度耦合，状态映射、接触模式、force sign、Jacobian、QP 约束、控制增益和 torque publisher 任一环节错误，都可能表现为机器人倒下或力矩异常。因此项目先把每个模块拆开验证，再组合成可回归 baseline。

## 2. 控制架构

系统闭环可以概括为：

    MuJoCo 仿真状态
    -> 状态读取与 MuJoCo-Pinocchio 映射
    -> Gait Scheduler
    -> Contact Planner
    -> Stance Legs / Swing Legs 分流
    -> Contact Force QP / WBC QP
    -> Memory-based Swing Trajectory
    -> Torque Mapping
    -> Torque Mixer
    -> Stance PD + scaled WBC feedforward + Swing PD
    -> Torque Safety Filter / Clamp
    -> MuJoCo Step
    -> ROS2/C++ zero-safe dry-run evidence

更详细的架构说明见：

- `docs/CONTROL_ARCHITECTURE_OVERVIEW.md`
- `docs/interview/INTERVIEW_3MIN_SYSTEM_EXPLANATION.md`

## 3. WBC/QP 设计

项目中的 full floating-base WBC QP 原型使用三类核心决策变量：

- `qdd`：广义加速度
- `contact force`：足端接触力
- `tau`：12 维关节力矩

目标项包括：

- base task
- swing foot task
- regularization

约束包括：

- floating-base dynamics
- stance contact constraint
- inactive leg force constraint
- friction cone / friction pyramid
- torque limit

项目没有把 full WBC 直接包装成最终成功控制器。实验中，direct full WBC torque 与 swing PD torque 直接相加会导致姿态和 joint error 变差；stance-only WBC + swing-only PD 也无法替代姿态反馈稳定。因此最终采用 mixed baseline：stance posture PD 提供基本稳定性，scaled WBC feedforward 提供动力学补偿，swing PD tracking 负责摆腿目标。

详细解释见：

- `docs/WBC_QP_EXPLAINED.md`

## 4. 最终 baseline

最终 baseline：

    mixed_online_control_baseline

控制结构：

    stance posture PD
    + scaled stance WBC feedforward
    + memory-based swing target PD

该 baseline 的特点是：

- stance legs 保留 posture PD，保证基础稳定
- WBC torque 只以较小比例作用于 stance legs，作为 feedforward
- swing legs 使用 memory-based swing target 和 swing PD tracking
- stance torque 与 swing torque 不直接混合错误腿状态
- 通过 1200-step 和 2400-step simulation regression

## 5. 关键结果

1200-step mixed baseline rerun：

- total_steps: 1200
- transition_count: 5
- qp_fail_steps: 0
- saturation_steps: 0
- min_z: 0.278419161322
- max_abs_roll: 0.056707402709
- max_abs_pitch: 0.048329482530
- max_joint_error: 0.077233662573
- max_tau_total_abs: 9.659563043535
- pass: True

2400-step mixed baseline robustness regression：

- total_steps: 2400
- transition_count: 11
- trot_FR_RL_steps: 1200
- trot_FL_RR_steps: 1200
- qp_fail_steps: 0
- saturation_steps: 0
- min_z: 0.274552192756
- max_abs_roll: 0.056707402709
- max_abs_pitch: 0.048329482530
- max_joint_error: 0.077233662573
- max_tau_total_abs: 9.659563043535
- pass: True

报告级结果见：

- `docs/ONE_PAGE_TECHNICAL_REPORT.md`
- `docs/REPORT_READY_RESULTS.md`
- `docs/FINAL_PACKAGE_WITH_DEMO_VIDEO_MANIFEST.md`

## 6. Demo video

演示视频不是 GUI 录屏，而是通过以下方式生成：

    MuJoCo offscreen rendering
    + policy rollout
    + raw RGB pipe to ffmpeg

视频文件：

    demo_videos/stage13_5a_r2_mujoco_offscreen_2400step_mixed_baseline_demo_720p.mp4

视频证据：

- resolution: 1280x720
- fps: 30
- duration: 20.000000 s
- frames: 600
- rollout_total_steps: 2400
- rollout_pass: True
- sha256: c9fb4241bd9a64f805f2e66ccf487fd683dfaadb1d23d17e8fa46a51073114d1

视频 manifest：

- `docs/DEMO_VIDEO_MANIFEST.md`

重新生成视频：

    /usr/bin/python3 scripts/stage13_5a_r2_mujoco_offscreen_rollout_video_fixed_ffmpeg.py

冻结视频证据：

    /usr/bin/python3 scripts/stage13_5b_demo_video_evidence_freeze.py

## 7. C++ control algorithm modules

项目补充了干净、可编译、可测试的 C++ 控制算法模块：

- gait scheduler
- swing trajectory generator
- torque safety filter

路径：

    ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/control/
    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/control/
    ros2_ws/src/robot_mpc_wbc_cpp_controller/test/test_control_algorithms.cpp

这些模块不发布 torque、不接入硬件，只用于展示控制算法的 C++ 工程化表达。它们比一次性迁移完整控制器更清楚，也更适合作为后续 ROS2/C++ realtime controller 的基础模块。

独立编译测试：

    g++ -std=c++17 -Wall -Wextra -Werror \
      -I ros2_ws/src/robot_mpc_wbc_cpp_controller/include \
      ros2_ws/src/robot_mpc_wbc_cpp_controller/src/control/gait_scheduler.cpp \
      ros2_ws/src/robot_mpc_wbc_cpp_controller/src/control/swing_trajectory.cpp \
      ros2_ws/src/robot_mpc_wbc_cpp_controller/src/control/torque_safety_filter.cpp \
      ros2_ws/src/robot_mpc_wbc_cpp_controller/test/test_control_algorithms.cpp \
      -o /tmp/test_control_algorithms

    /tmp/test_control_algorithms

说明文档：

- `docs/CPP_CONTROL_ALGORITHMS.md`

## 8. simulation-only 边界

当前项目不声明：

- hardware deployment completed
- actuator enablement completed
- real robot torque execution completed
- torque_enable_ready=True
- realtime hardware controller completed

当前证据只支持：

- simulation-only locomotion baseline
- MuJoCo/Pinocchio control prototype
- ROS2/C++ zero-safe dry-run publisher evidence
- report-ready result package
- MuJoCo offscreen demo video

## 9. 推荐阅读顺序

面试或快速审阅时，建议按下面顺序看：

1. `README.md`
2. `docs/ONE_PAGE_TECHNICAL_REPORT.md`
3. `docs/CONTROL_ARCHITECTURE_OVERVIEW.md`
4. `docs/WBC_QP_EXPLAINED.md`
5. `docs/interview/INTERVIEW_3MIN_SYSTEM_EXPLANATION.md`
6. `docs/CPP_CONTROL_ALGORITHMS.md`
7. `docs/FINAL_PACKAGE_WITH_DEMO_VIDEO_MANIFEST.md`

## 10. 后续计划

后续优先方向不是继续堆更多日志，而是继续增强系统可解释性和工程化质量：

- 将 C++ gait scheduler / swing trajectory / torque safety filter 接入 ROS2 package 的 CMake 测试体系
- 补 contact force QP 的 C++ demo
- 把 swing target 更系统地纳入 WBC QP
- 加入 base velocity tracking
- 加入 touchdown/liftoff feedback
- 后续再考虑 EKF 和更完整的 centroidal MPC

所有后续工作仍应先保持 simulation-only。

<!-- STAGE14_4E_MPC_ENTRY_BEGIN -->

## 已补充：MPC 规划层 demo

项目已补充一个仿真内 standalone simplified 3D base velocity tracking receding-horizon MPC demo，用于展示 planning-layer / contact-force MPC 的接触力优化能力。

该模块使用简化质心动力学，状态为 `x = [px, py, pz, vx, vy, vz]`，优化变量为四足三维接触力。每个 rollout step 都会基于当前状态重新求解有限时域 QP，只应用第一帧接触力 `u0`，再推进简化质心状态。

已完成内容：

- standalone Python MPC solver
- 100-step receding-horizon rollout
- rollout CSV 和 summary JSON 记录
- OSQP 求解状态、摆动腿力、支撑腿力、摩擦约束、速度跟踪和高度误差验证
- 与早期 z-MPC prototype、WBC feedforward 的边界关系说明

当前边界：

- MPC 只属于 planning-layer / contact-force MPC demo
- 不是 WBC
- 不直接输出 joint torque
- 不接 ROS torque publisher
- 不接 MuJoCo torque
- 不改变 frozen mixed baseline 控制律
- 项目范围仍保持 simulation-only

相关文件：

- `scripts/stage14_4_base_velocity_tracking_mpc_demo.py`
- `scripts/stage14_4b_validate_base_velocity_mpc_rollout.py`
- `docs/stage14_4_base_velocity_tracking_mpc.md`
- `docs/stage14_4b_base_velocity_tracking_mpc_validation.md`
- `docs/stage14_4c_mpc_scope_explanation.md`

<!-- STAGE14_4E_MPC_ENTRY_END -->

