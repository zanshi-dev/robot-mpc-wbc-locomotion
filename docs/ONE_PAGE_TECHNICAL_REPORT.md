# 一页技术报告：robot-mpc-wbc-locomotion

## 项目目标

本项目面向 Go1 风格四足机器人，在 MuJoCo 仿真中构建 locomotion 控制链路，并逐步连接 Pinocchio 模型、gait scheduler、swing trajectory、contact force QP、WBC QP、torque mapping、PD tracking 和 ROS2/C++ safety dry-run 路径。项目当前定位是 simulation-only，不声明硬件部署或真实机器人执行器控制完成。

## 控制框架

系统从 MuJoCo 读取 base state、joint state 和 foot contact，然后通过 MuJoCo-Pinocchio mapping 保证状态、足端 frame 和 actuator order 一致。gait scheduler 决定当前 contact mode，contact planner 将腿分成 stance 和 swing。stance legs 进入 contact force QP 或 WBC QP，swing legs 进入 memory-based swing trajectory generator。WBC/QP 输出的支撑信息经过 torque mapping 变成 12 维 actuator torque，最终由 torque mixer 合成 stance PD、scaled WBC feedforward 和 swing PD tracking。ROS2/C++ 侧只做 safety-gated zero-safe dry-run evidence，不作为硬件控制器声明。

## 关键算法

项目的关键算法包括 MuJoCo 与 Pinocchio 状态映射、standing PD baseline、trot gait scheduler、memory-based swing trajectory、contact force QP、centroidal z MPC prototype、J transpose f force-to-torque mapping、full floating-base WBC QP prototype，以及最终 mixed torque mixer。WBC/QP 的核心变量是 qdd、contact force 和 tau，目标项包括 base task、swing foot task 和 regularization，约束包括动力学方程、接触约束、摩擦锥和 torque limit。

## 失败路径

项目没有把所有可运行脚本都包装成成功结果。direct full WBC torque 与 swing PD torque 直接相加失败，stance-only WBC + swing-only PD 也失败，说明 full WBC 在当前阶段不能直接替代反馈稳定控制。最终选择 mixed baseline，是因为 stance posture PD 提供稳定基础，WBC feedforward 提供动力学补偿，swing PD tracking 负责摆腿目标跟踪。

## 最终 baseline

最终 baseline 为 mixed_online_control_baseline。它不是 pure full WBC locomotion，也不是 hardware realtime controller。其控制结构是 stance posture PD + scaled stance WBC feedforward + memory-based swing target PD。该 baseline 通过 1200-step rerun 和 2400-step robustness regression。

## 关键指标

1200-step mixed baseline rerun 中，total_steps 为 1200，transition_count 为 5，QP fail 为 0，saturation 为 0，min_z 为 0.278419161322，max_abs_roll 为 0.056707402709，max_abs_pitch 为 0.048329482530，max_joint_error 为 0.077233662573，max_tau_total_abs 为 9.659563043535，pass 为 True。

2400-step mixed baseline robustness regression 中，total_steps 为 2400，transition_count 为 11，QP fail 为 0，saturation 为 0，min_z 为 0.274552192756，max_abs_roll 为 0.056707402709，max_abs_pitch 为 0.048329482530，max_joint_error 为 0.077233662573，max_tau_total_abs 为 9.659563043535，pass 为 True。

## 演示视频

演示视频通过 MuJoCo offscreen rendering + policy rollout + raw RGB pipe to ffmpeg 生成，不是 GUI 录屏。视频分辨率为 1280x720，30 fps，时长 20 秒，600 帧，对应 2400 个 MuJoCo step，rollout pass 为 True。

## simulation-only 边界

项目不声明 hardware deployment completed，不声明 actuator enablement completed，不声明 real robot torque execution completed，不声明 torque_enable_ready=True，也不声明 realtime hardware controller 已完成。当前证据只支持 simulation-only locomotion baseline、ROS2/C++ zero-safe dry-run publisher evidence、报告级结果包和离屏渲染 demo video。

## 后续计划

后续最有价值的工作不是继续堆 Stage，而是补充干净可测试的 C++ 算法模块，例如 gait scheduler、swing trajectory generator、torque safety filter 和 controller interface unit tests。算法侧可以继续推进 swing target 纳入 WBC QP、base velocity tracking、contact feedback、EKF 和更完整的 centroidal MPC，但仍应先在 simulation-only 中验证。
