# 3 分钟项目讲法

这个项目是一个 Go1 风格四足机器人的 simulation-only locomotion 控制项目。我没有直接从完整动态行走控制器开始做，而是先把四足控制链路拆成可验证的模块：MuJoCo 仿真、Pinocchio 模型映射、gait scheduler、swing trajectory、contact force QP、WBC QP、torque mapping、PD tracking 和 ROS2/C++ safety dry-run。

系统闭环是这样的：MuJoCo 提供 base state、joint state 和 contact state；我先做 MuJoCo 和 Pinocchio 的状态映射，解决 actuator order、foot frame 和 quaternion order 不一致的问题。然后 gait scheduler 输出当前接触模式，contact planner 把腿分成 stance legs 和 swing legs。stance legs 进入 contact force QP 或 WBC QP，swing legs 进入 memory-based swing trajectory。WBC 或 force QP 的结果通过 J transpose f 和 torque mapping 变成 12 维 actuator torque，最后进入 torque mixer。

WBC QP 这一块，我的 full WBC 原型使用 qdd、contact force 和 tau 作为决策变量。目标项包括 base task、swing foot task 和 regularization，约束包括 floating-base dynamics、接触约束、摩擦锥和 torque limit。这个设计可以解释动力学，但是我没有把它直接包装成最终成功的 full WBC controller，因为实验中 direct full WBC torque 加 swing PD 会导致 roll 和 joint error 变大，stance-only WBC 加 swing-only PD 也无法稳定。原因是当前阶段 contact switching、swing tracking、base stabilization 和 torque generation 耦合太强，而项目还没有接入 EKF、touchdown feedback 和完整 base velocity tracking。

所以最终我选择 mixed_online_control_baseline。它的结构是 stance posture PD 保证基础稳定，scaled WBC feedforward 只作用于 stance legs，swing legs 使用 memory-based swing target 和 swing PD tracking。这个 baseline 通过了 1200-step rerun 和 2400-step robustness regression。2400-step 中 QP fail 为 0，saturation 为 0，min_z 大约 0.2746，最大 roll 大约 0.0567，最大 pitch 大约 0.0483，最大 joint error 大约 0.0772，最大 torque 大约 9.66，低于 23.7 的 torque limit。

C++/ROS2 侧我没有直接宣称硬件控制器完成，而是做了 safety-gated dry-run。包括 publisher construction、manual enable、bounded one-shot zero-safe publish、bounded continuous zero-safe dry-run 和证据冻结。这样做是因为 torque publisher 一旦接入真实硬件就有风险，必须先证明默认禁用、手动确认、payload 长度、finite 检查和停止条件都可控。

最终项目还生成了 MuJoCo offscreen rendering 演示视频，不是 GUI 录屏，而是 policy rollout 每步渲染 RGB frame，然后 pipe 到 ffmpeg 编码。整个项目的当前边界是 simulation-only，不声明硬件部署、执行器使能或真实机器人 torque execution。后续如果继续，我会优先补干净的 C++ gait scheduler、swing trajectory generator、torque safety filter 和单元测试，而不是贸然迁移整个控制器。
