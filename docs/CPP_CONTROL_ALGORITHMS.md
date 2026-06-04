# C++ 控制算法子模块

本模块用于补强项目的 C++ 算法表达能力。它不是硬件控制器，不发布 torque，不启用执行器，只提供可编译、可测试、输入输出清楚的控制算法组件。

当前包含三个模块。

第一个模块是 gait scheduler。它根据 step 和 half-period 输出 trot_FR_RL 或 trot_FL_RR 接触模式，并返回四条腿的 contact mask。它对应 Python/MuJoCo baseline 中的 gait scheduler，用于说明项目不是只依赖脚本，而是能把核心控制逻辑抽象成 C++ 算法接口。

第二个模块是 swing trajectory generator。它用 smoothstep 插值和正弦 clearance 生成摆动腿轨迹。输入是起点、目标点和 phase，输出是当前 swing foot target。它对应项目中的 memory-based swing trajectory 思路，但这里实现成最小可测试的纯函数式 C++ 模块。

第三个模块是 torque safety filter。它接收 12 维 torque，检查 finite 和 torque limit，并对超限或非有限值进行安全处理。它对应 ROS2/C++ safety gate 的核心思想：任何 torque 输出路径都必须先经过 clamp、finite check 和 limit check。

该 C++ 子模块的价值在于，它比直接迁移完整控制器更清楚、更可测试。面试时可以说明：完整 WBC/MPC 控制器仍在 simulation-only 原型中，但 gait scheduler、swing trajectory 和 torque safety filter 这类确定性模块已经可以独立用 C++ 实现和测试，为后续控制器工程化迁移打基础。
