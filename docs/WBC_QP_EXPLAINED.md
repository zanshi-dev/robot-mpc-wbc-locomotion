# WBC/QP 可解释性说明

本文说明项目中的 WBC/QP 是什么、优化变量是什么、目标项和约束是什么，以及为什么最终 baseline 没有采用 pure full WBC torque 作为直接控制输出。

## WBC/QP 在项目中的位置

WBC/QP 位于 contact planner 之后、torque mixer 之前。它接收当前机器人状态、接触模式、期望 base task 和 swing foot task，输出可用于 stance 支撑的接触力或关节力矩信息。在最终 mixed baseline 中，WBC 的作用不是完全替代 PD 控制，而是为 stance legs 提供 scaled feedforward。

## 决策变量

项目中的 full floating-base WBC QP 原型包含三类核心决策变量。

第一类是广义加速度 qdd。对于 floating-base Go1 模型，qdd 包含 base 相关自由度和 12 个 actuated joints 的加速度。引入 qdd 的目的是让优化问题能够表达系统动力学，而不只是做静态力分配。

第二类是 contact force。对于当前接触模式中的 stance feet，QP 为每个接触足求解三维接触力。inactive swing legs 的接触力需要为零。contact force 的意义是表达地面对机器人提供的支撑和加速度来源。

第三类是 joint torque tau。它是最终能作用到 MuJoCo actuator 的控制量，也是 WBC 与 torque-level simulation 闭环连接的关键变量。由于机器人有 12 个电机，tau 是 12 维 actuated torque。

因此，这里的 WBC 不是只算足端力，也不是只算关节 PD，而是尝试在同一个优化问题中同时组织 qdd、contact force 和 tau。

## 目标项

WBC/QP 的目标项可以分成几类理解。

base task 用于约束或跟踪机身相关目标。早期项目尝试过更完整的 6D base acceleration task，但在初期原型中该任务过重，容易在 trot contact mode 下造成误差和姿态裕度不足。因此项目退回更保守的 vertical-only base acceleration task，用更小的任务集合先保证仿真闭环稳定。

swing foot task 用于约束摆动腿足端加速度或目标跟踪。它的目的是让 swing leg 不只是被动抬腿，而是尽可能跟踪规划出的 swing trajectory。不过在最终 mixed baseline 中，swing tracking 的主要执行方式仍然是 swing joint target PD，而不是完全由 full WBC 承担。

regularization 用于抑制过大的加速度、接触力或关节力矩，避免优化器在满足任务时产生不必要的激进控制量。对于四足 locomotion，regularization 不是装饰项，而是降低 torque jump 和数值不稳定的重要手段。

## 约束项

WBC/QP 的核心硬约束首先是 floating-base dynamics。该约束可以写成概念形式：M(q) qdd + h(q, dq) = S transpose tau + J transpose f。它保证优化出的加速度、接触力和关节力矩在动力学上自洽。

第二类约束是接触约束。stance feet 应满足接触一致性，例如足端在接触方向不能产生不合理加速度；swing feet 不应拥有接触力。该约束使 contact planner 的输出真正进入 WBC，而不是只作为日志标签。

第三类约束是摩擦锥和接触力边界。接触力的法向力需要在合理范围内，切向力不能超过摩擦限制。这样可以避免 QP 用物理上不可实现的足端力来解决姿态任务。

第四类约束是力矩限制。Go1 仿真中使用 torque limit 23.7，QP 或后处理都必须保证控制量不超过该限制。否则即使数学上任务误差很小，实际 actuator 也无法执行。

## 为什么 full WBC 不稳定

项目中的失败路径很重要。direct full WBC torque 与 swing PD torque 直接叠加后，roll 和 joint error 会明显失控。进一步做 scale sweep 时，所有通过项实质上都把 WBC torque scale 降到了 0，这说明直接叠加并没有让 full WBC 成功参与闭环控制。

另一个失败路径是 stance-only WBC + swing-only PD。该方案试图让 stance legs 只依赖 WBC feedforward，而 swing legs 使用 swing PD。但结果显示缺少 stance posture feedback 时，机器人容易失去基础姿态稳定。

这些失败说明，当前 full WBC 原型的问题不是 QP 完全不能求解，而是能求解不等于能稳定闭环控制。在 contact mode 切换、swing target 变化、base task 与 stance support 耦合时，full WBC 对模型准确性、任务权重、接触反馈和实时性要求更高。当前项目尚未完成 EKF、touchdown/liftoff feedback、base velocity tracking 和 full 3D centroidal MPC，因此 direct full WBC torque 不是最稳妥的最终输出。

## 为什么 mixed baseline 是合理折中

mixed baseline 保留 stance posture PD，是因为 posture PD 已在 MuJoCo 中证明能提供稳定站立基础。它使用 scaled WBC feedforward，是因为 WBC 提供了支撑方向和动力学解释，但当前不适合完全替代反馈稳定器。它使用 swing target PD，是因为 memory-based swing trajectory 已能生成平滑目标，而 joint PD 可以稳定跟踪这些目标。

这种结构的意义是把复杂问题拆开：stance 稳定由可靠反馈承担，WBC 提供可解释的动力学补偿，swing motion 由独立轨迹和 PD tracking 承担，torque mixer 避免不同腿状态下的控制目标互相污染。因此，mixed baseline 是当前项目阶段中最稳、最清楚、最适合继续迭代的架构。
