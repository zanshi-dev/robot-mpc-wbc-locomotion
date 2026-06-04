# 控制架构总览

本文用于把 robot-mpc-wbc-locomotion 项目讲成一个清楚的机器人控制系统，而不是一组阶段脚本。当前项目边界是 simulation-only。最终可运行 baseline 是 mixed_online_control_baseline，不是硬件实时控制器，也不是 pure full WBC locomotion controller。

## 一句话概括

本项目构建了一条 Go1 风格四足机器人仿真 locomotion 控制链路：从 MuJoCo 读取机器人状态，经过状态映射、gait scheduler、contact planner、swing trajectory、contact force QP、WBC QP、torque mapping、PD tracking 和 torque safety gate，最终在 torque-level 闭环中完成 1200-step 与 2400-step 仿真回归，并通过 ROS2/C++ safety dry-run 路径验证 torque publisher 的安全边界。

## 系统闭环

系统闭环可以按下面顺序理解。

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

第一步，MuJoCo 提供仿真状态，包括 floating base 位姿、关节位置、关节速度、足端接触和仿真时间。项目没有直接把这些数组交给控制器使用，而是先建立 MuJoCo 与 Pinocchio 之间的状态映射，显式处理 joint order、actuator order、foot frame 和 quaternion 顺序差异。这样做的原因是四足机器人控制中最容易出错的不是某一个算法公式，而是状态数组错位、足端 frame 错位或关节力矩顺序错位。

第二步，状态读取结果进入 gait scheduler。scheduler 根据当前 step 和 gait period 输出当前 contact mode。项目中的保守 trot 使用 FR+RL 与 FL+RR 两组对角腿交替，并保留 duty factor 和 contact overlap 以提高早期稳定性。gait scheduler 的作用是把连续时间中的运动意图离散成每条腿当前是 stance 还是 swing。

第三步，contact planner 根据 scheduler 的输出决定哪些腿作为支撑腿，哪些腿作为摆动腿。支撑腿进入 contact force QP 或 WBC QP，摆动腿进入 swing trajectory generator。contact planner 的意义是把足端接触模式作为优化约束和 torque mixer 的输入，而不是让所有腿始终使用同一种控制策略。

第四步，swing trajectory generator 为摆动腿生成连续的足端或关节空间目标。项目最终采用 memory-based swing target generator，保存每条腿的上一帧 target、lift-off 位置和 touch-down 目标，避免 mode switch 时 target 突跳。这样做的原因是摆腿目标如果只由当前 mode 直接决定，会在 contact 切换瞬间产生不连续，进而导致 joint error 和 torque jump。

第五步，contact force QP 或 WBC QP 计算支撑相关的动力学量。早期 contact force QP 用来求解满足重力支撑、摩擦约束和接触模式的足端力。后续 WBC QP 进一步把 qdd、contact force 和 tau 放入统一优化问题，用动力学方程、接触约束和任务项组织控制目标。该模块的作用是给 stance legs 提供有物理意义的 feedforward 支撑信息。

第六步，torque mapping 将足端力或 WBC 输出转成 MuJoCo actuator order 下的 12 维 joint torque。项目显式验证了 MuJoCo mj_jacGeom 与 Pinocchio getFrameJacobian 的 J transpose f 映射一致，并确认实际支撑方向使用正确的 force sign。该步骤的意义是把模型侧计算结果安全地落到仿真执行器顺序上。

第七步，PD tracking 和 torque mixer 将 stance 与 swing 分开处理。最终 baseline 没有直接使用 full WBC torque 控制所有腿，而是采用 stance posture PD + scaled stance WBC feedforward + swing target PD。这个 mixed baseline 是当前最稳定、最可解释的折中：stance PD 负责基础姿态稳定，WBC feedforward 提供支撑方向的动力学补偿，swing PD 负责跟踪在线摆腿目标。

第八步，torque safety gate 和 ROS2/C++ dry-run 路径提供工程安全边界。C++ 侧没有直接变成硬件控制器，而是分阶段完成 disabled controller、publisher construction、manual enable、bounded one-shot zero-safe publish、bounded continuous zero-safe dry-run 和证据冻结。这样做的原因是 torque publisher 一旦接入硬件会具有风险，因此必须先证明默认禁用、手动确认、payload 长度、finite 检查、停止条件和 hash 证据都可控。

## 当前最终 baseline

当前最终 baseline 是 mixed_online_control_baseline。它不是“完整 WBC 控制器已经完成”的证明，而是一个工程上合理、仿真中稳定、能解释失败路径的中间结果。

它的核心是：stance legs 保留 posture PD 作为主稳定来源；WBC torque 只以较小比例作用于 stance legs，作为 feedforward；swing legs 由 memory-based swing target 和 swing PD 跟踪；两类腿不直接混合不对应的 torque。该策略通过了 1200-step rerun 和 2400-step robustness regression。

## 为什么不直接使用 pure full WBC

项目尝试过 direct full WBC torque 与 swing PD torque 直接叠加，也尝试过 stance-only WBC + swing-only PD。结果说明直接 torque sum 会导致 roll、pitch 或 joint error 变大，stance-only WBC feedforward 也无法替代 posture feedback。根本原因是初期 full WBC 同时承担 base stabilization、contact switching、swing tracking 和 torque generation，任务耦合过强；一旦 contact mode 切换、swing target 不连续或支撑裕度不足，闭环稳定性会明显下降。

因此 mixed baseline 不是退步，而是当前阶段的合理控制架构选择。它把最可靠的反馈稳定机制保留下来，同时把 WBC 作为可解释、可逐步增强的动力学 feedforward 模块。
