# robot-mpc-wbc-locomotion

这是一个 Go1 风格四足机器人运动控制项目。项目当前只面向仿真验证，重点是把四足机器人运动控制中容易出错的部分逐步拆开、验证清楚，再组合成一条稳定、可复现的控制链路。

项目最初以 `mixed_online_control_baseline` 作为稳定基线：站立腿姿态 PD 提供基础稳定性，缩放后的 WBC 前馈提供动力学补偿，摆动腿 PD 负责轨迹跟踪。在此基础上，项目进一步加入了 MPC 接触力规划，并完成了 MPC 与 WBC/QP 候选链路的仿真验证。

当前 MPC 升级的定位是：MPC 负责生成接触力参考或接触力候选，WBC/QP 或 `J^T f` 映射层再把接触力候选转换为关节力矩候选。所有结果仍然限定在 MuJoCo 和离线仿真证据范围内。

本仓库不声明真实机器人部署完成，不声明 torque-enable ready，也不发布真实机器人关节力矩命令。

## 1. 项目目标

本项目围绕四足机器人运动控制搭建完整控制架构：

- MuJoCo 仿真环境
- Pinocchio 运动学与动力学模型
- MuJoCo 与 Pinocchio 状态映射
- 步态调度器
- 接触规划器
- 摆腿轨迹生成器
- MPC 接触力规划
- 接触力 QP / WBC QP
- 接触力到关节力矩候选的映射
- 站立腿姿态 PD 与摆动腿 PD 跟踪
- 力矩安全限幅
- ROS2/C++ 零输出干运行证据
- MuJoCo 离屏渲染演示视频

项目采用阶段化路线，不直接跳到真实硬件控制器。四足机器人系统高度耦合，状态映射、接触模式、接触力方向、雅可比矩阵、QP 约束、控制增益和力矩发布路径中任一环节出错，都可能表现为机器人倒下或力矩异常。因此项目先把每个模块拆开验证，再组合成可回归的仿真基线。

## 2. 控制架构

系统闭环可以概括为：

    MuJoCo 仿真状态
    -> 状态读取与 MuJoCo-Pinocchio 映射
    -> 步态调度
    -> 接触规划
    -> MPC 接触力参考规划
    -> 站立腿 / 摆动腿分流
    -> 接触力 QP / WBC QP
    -> 摆腿轨迹生成
    -> 接触力到关节力矩候选映射
    -> 力矩混合
    -> 站立腿姿态 PD + 缩放后的 WBC 前馈 + 摆动腿 PD
    -> 力矩安全限幅
    -> MuJoCo 仿真步进

更详细的架构说明见：

- `docs/CONTROL_ARCHITECTURE_OVERVIEW.md`
- `docs/interview/INTERVIEW_3MIN_SYSTEM_EXPLANATION.md`

## 3. WBC/QP 设计

项目中的浮动基 WBC/QP 原型主要使用三类变量：

- `qdd`：广义加速度
- `contact force`：足端接触力
- `tau`：12 维关节力矩候选

目标项包括：

- 机身任务
- 摆动足任务
- 正则化项

约束包括：

- 浮动基动力学约束
- 站立接触约束
- 非接触腿接触力约束
- 摩擦锥 / 摩擦金字塔约束
- 关节力矩上限

项目没有把 full WBC 直接包装成最终控制器。实验中，直接叠加 full WBC 力矩与摆腿 PD 力矩会导致姿态和关节误差变差；只使用 stance-only WBC 加 swing-only PD 也不能完全替代姿态反馈。因此最终采用混合结构：站立腿姿态 PD 提供基础稳定性，缩放后的 WBC 前馈提供动力学补偿，摆动腿 PD 负责轨迹跟踪。

详细解释见：

- `docs/WBC_QP_EXPLAINED.md`

## 4. Baseline 与 MPC 升级

最终稳定基线：

    mixed_online_control_baseline

控制结构：

    站立腿姿态 PD
    + 缩放后的站立腿 WBC 前馈
    + 基于记忆目标的摆动腿 PD

该基线的特点是：

- 站立腿保留姿态 PD，保证基础稳定
- WBC 力矩只以较小比例作用于站立腿，作为前馈补偿
- 摆动腿使用基于记忆的摆腿目标和 PD 跟踪
- 站立腿力矩与摆动腿力矩不错误混合
- 通过 1200-step 和 2400-step 仿真回归

在这个基线之外，项目加入了 MPC 接触力规划。MPC 不直接输出关节力矩，而是生成接触力参考或接触力候选；随后由 WBC/QP 或 `J^T f` 映射层生成关节力矩候选。

MPC 辅助候选链路只用于仿真验证，不修改冻结版 mixed baseline，不接 ROS 力矩发布器，也不发送真实机器人力矩命令。

## 5. 关键结果

1200-step mixed baseline 回归：

- total_steps: 1200
- transition_count: 5
- qp_fail_steps: 0
- saturation_steps: 0
- min_z: 0.278419161322
- max_abs_roll: 0.056707402709
- max_abs_pitch: 0.048329482530
- max_joint_error: 0.077233662573
- max_tau_total_abs: 9.659563043535
- pass: true

2400-step mixed baseline 鲁棒性回归：

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
- pass: true


MPC 辅助候选链路 2400-step 仿真：

- candidate_scale: 0.05
- total_steps: 2400
- qp_fail_steps: 0
- saturation_steps: 0
- min_z: 0.276975761939
- max_abs_roll: 0.102952660101
- max_abs_pitch: 0.053162351948
- max_tau_total_abs: 10.019186119959
- max_tau_candidate_scaled_abs: 0.972125472365
- pass: true

MPC 辅助候选链路鲁棒性包络：

- 已验证候选比例: 0.00 / 0.02 / 0.05 / 0.10
- 正比例候选仿真: 0.02 / 0.05 / 0.10
- validated_candidate_scale_max_simulation_only: 0.10
- min_z_min_over_entries: 0.273040429683
- max_abs_roll_max_over_entries: 0.102952660101
- max_abs_pitch_max_over_entries: 0.077452968358
- max_tau_total_abs_max_over_entries: 10.59512016256
- max_tau_candidate_scaled_abs_max_over_candidate_runs: 1.94425094473
- total_qp_fail_steps: 0
- total_saturation_steps: 0

报告级结果见：

- `docs/ONE_PAGE_TECHNICAL_REPORT.md`
- `docs/REPORT_READY_RESULTS.md`
- `docs/FINAL_PACKAGE_WITH_DEMO_VIDEO_MANIFEST.md`

## 6. Demo video

演示视频不是 GUI 录屏，而是通过以下方式生成：

    MuJoCo 离屏渲染
    + 控制策略 rollout
    + 原始 RGB 管线写入 ffmpeg

视频文件：

    demo_videos/stage13_5a_r2_mujoco_offscreen_2400step_mixed_baseline_demo_720p.mp4

视频证据：

- resolution: 1280x720
- fps: 30
- duration: 20.000000 s
- frames: 600
- rollout_total_steps: 2400
- rollout_pass: true
- sha256: c9fb4241bd9a64f805f2e66ccf487fd683dfaadb1d23d17e8fa46a51073114d1

视频证据清单：

- `docs/DEMO_VIDEO_MANIFEST.md`

重新生成视频：

    /usr/bin/python3 scripts/stage13_5a_r2_mujoco_offscreen_rollout_video_fixed_ffmpeg.py

冻结视频证据：

    /usr/bin/python3 scripts/stage13_5b_demo_video_evidence_freeze.py

## 7. C++ control algorithm modules

项目补充了干净、可编译、可测试的 C++ 控制算法模块：

- 步态调度器
- 摆腿轨迹生成器
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

- MPC 直接输出关节力矩

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
- MuJoCo 离屏渲染演示视频

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

