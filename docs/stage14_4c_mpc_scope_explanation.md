# Stage 14.4C：MPC 范围与边界说明

## 1. 阶段结论

Stage 14.4 是一个独立的、简化的 3D base velocity tracking receding-horizon MPC demo。

本阶段的核心价值是补齐项目中的“标准意义上的 MPC”证据链：在每一个 rollout step，算法读取当前简化 base 状态和接触时序，重新构造并求解有限时域 QP，只取预测时域第一帧接触力 u0 作为当前步输入，然后用简化质心动力学推进状态。下一步再基于新的当前状态重新求解。

因此，Stage 14.4 体现的是 receding-horizon 优化流程，而不是一次性 open-loop force sequence 回放。

Stage 14.4 不是 WBC，不直接输出 joint torque，不接 ROS torque publisher，不接 MuJoCo torque，不改变 mixed baseline 控制律。

## 2. Stage 14.4A 的定位

Stage 14.4A 完成了 standalone Python MPC solver 和简化 rollout demo。

状态定义为：

x = [px, py, pz, vx, vy, vz]

输入定义为四足三维接触力：

u = [FR_fx, FR_fy, FR_fz, FL_fx, FL_fy, FL_fz, RR_fx, RR_fy, RR_fz, RL_fx, RL_fy, RL_fz]

简化离散动力学为：

p_next = p + dt * v

v_next = v + dt * (sum_i f_i / m + g)

QP 目标包括速度跟踪、高度保持、垂向速度抑制、接触力正则化和控制输入平滑。约束包括摆动腿力为零、支撑腿竖直力上下界、摩擦金字塔约束和总竖直力上界。

Stage 14.4A 的结果显示：summary 中 pass 为 true，100 个 rollout step 的 OSQP 状态均为 solved，最终 vx 收敛到 vx_ref 附近，vy 保持为零，z 接近 z_ref，摩擦约束违规为零，摆动腿力范数接近零。

这些结果只能说明简化动力学下的 MPC demo 通过回归，不能说明它已经接入真实 locomotion controller。

## 3. Stage 14.4B 的定位

Stage 14.4B 没有修改 MPC 控制律，而是增加独立验证脚本，对 Stage 14.4A 的日志和源码模式进行复核。

验证内容包括：

- Stage 14.4A summary 必须为 pass=true
- rollout CSV 行数必须符合配置
- CSV 必须包含状态、接触模式、u0、合力、约束指标、求解状态和求解时间
- 每一行求解状态必须为 solved 或 solved inaccurate
- 所有状态和力必须是有限数值
- 摆动腿力必须接近零
- 支撑腿 fz 必须满足上下界
- 摩擦金字塔违规必须接近零
- vx tracking error 必须下降
- vy 和 z 必须保持在阈值内
- 源码必须体现 receding-horizon：当前状态重解、只应用 u0、推进状态、下一步再重解

Stage 14.4B 的结果显示 pass=true，说明 Stage 14.4A 的证据链可独立复核。

## 4. 与 Stage 5 z-MPC prototype 的关系

Stage 5 的 z-MPC prototype 是早期最小原型，主要用于验证垂直方向或高度相关的简化质心优化思想。它不是完整的 base velocity tracking MPC，也不足以说明项目已经具备标准意义上的三维速度跟踪接触力规划能力。

Stage 14.4 与 Stage 5 的关键差异如下：

| 对比项 | Stage 5 z-MPC prototype | Stage 14.4 base velocity tracking MPC |
|---|---|---|
| 状态重点 | 主要关注 z 方向 | 同时包含位置和三维速度 |
| 输入形式 | 原型级简化输入 | 四足三维接触力，共 12 维 |
| 目标函数 | 高度或垂向动力学原型 | vx 跟踪、vy 抑制、z 保持、vz 抑制 |
| 接触约束 | 原型级 | 摆动腿力为零、支撑腿 fz 上下界、摩擦金字塔 |
| 时域方式 | 早期 MPC 原型 | 明确每步重解，只应用 u0 |
| 项目作用 | 验证概念 | 补齐标准 MPC 证据 |

因此，Stage 14.4 不是重复 Stage 5，而是把项目中的 MPC 证据从最小高度方向原型推进到三维 base velocity tracking contact-force MPC demo。

## 5. 与 Stage 7 WBC feedforward 的关系

Stage 7 已经完成 WBC/QP 原型和 mixed online control baseline 的探索。历史尝试中，direct full WBC torque + swing PD 和 stance-only WBC + swing-only PD 都没有成为最终稳定方案。项目最终保留的是 frozen mixed baseline：

- stance posture PD
- scaled stance WBC feedforward
- memory-based swing target PD

当前 frozen mixed baseline 是项目中最可靠、最可解释的在线仿真 baseline，但它不是 pure full WBC locomotion。

Stage 14.4 与 Stage 7 的关键差异如下：

| 对比项 | Stage 7 WBC feedforward / mixed baseline | Stage 14.4 MPC demo |
|---|---|---|
| 层级 | WBC/QP 与 torque-side baseline | 接触力规划层 MPC |
| 输出 | 与 joint torque 或 feedforward torque 相关 | 第一帧接触力 u0 |
| 是否进入在线 baseline | 是，作为 frozen mixed baseline 的历史组成 | 否，仅 standalone demo |
| 是否改变 mixed baseline | 已冻结 | 不改变 |
| 是否接 MuJoCo torque | mixed baseline 历史结果属于仿真控制 | Stage 14.4 不接 torque |
| 主要价值 | 解释并支撑已有仿真 locomotion baseline | 补齐 receding-horizon MPC 证据 |

Stage 14.4 当前没有把 MPC 输出送入 WBC，也没有把接触力映射为关节力矩。因此，它不是 MPC-WBC integrated controller。

## 6. 当前架构中的正确位置

当前项目可以按三层理解：

第一层是已验证仿真 baseline。该层对应 frozen mixed baseline，用于 Stage 13 系列的长步数回归、视频生成和结果打包。

第二层是 WBC/QP 解释层。该层对应 Stage 7 的 WBC/QP 原型和 scaled stance WBC feedforward，用来解释动力学一致性、QP 结构和 torque-side 控制探索。

第三层是 MPC 规划层。该层对应 Stage 14.4 的 base velocity tracking MPC，用来展示接触力层的 receding-horizon 优化能力。

Stage 14.4 当前只属于第三层的 standalone demo。它尚未与第一层 mixed baseline 或第二层 WBC/QP 闭环集成。

## 7. 当前不能宣称的内容

即使 Stage 14.4A 和 Stage 14.4B 都通过，也不能把项目描述为：

- 硬件侧已经准备完成
- 力矩使能流程已经完成
- 存在真实机器人力矩执行证据
- 执行器使能已经完成
- 存在实时硬件控制器完成证据
- full 3D centroidal MPC 已经和 WBC 完整集成
- MPC 已经接入 MuJoCo closed-loop locomotion baseline
- MPC 输出真实 joint torque
- ROS torque publisher 已经启用

这些内容均不属于当前阶段证据。

## 8. 当前可以宣称的内容

可以谨慎表述为：

- 项目新增了 standalone simplified 3D base velocity tracking receding-horizon MPC demo。
- 该 demo 使用 OSQP 求解有限时域 contact-force QP。
- 该 demo 在简化质心动力学 rollout 中通过 100 步回归。
- 该 demo 记录了状态、接触模式、第一帧接触力 u0、合力、约束指标、求解状态和求解时间。
- Stage 14.4B 独立验证了 rollout CSV、summary JSON、receding-horizon 源码模式和安全边界标志。
- 当前证据是 simulation-only 的算法与日志证据，不是硬件控制证据。

## 9. 安全边界标志

simulation_only_project=true

hardware_deployment_completed=false

torque_enable_ready=false

torque_publisher_enabled=false

control_law_changed=false

mixed_baseline_modified=false

mujoco_torque_used=false

ros_publisher_used=false

## 10. 后续阶段建议

Stage 14.4D 可以把 MPC 部分加入 README、ONE_PAGE_TECHNICAL_REPORT 和 CONTROL_ARCHITECTURE_OVERVIEW。

后续如果继续推进算法，可以考虑 Stage 14.5，例如 C++ contact force QP、C++ MPC demo 或更清晰的 MPC/WBC interface mock。

不应在当前阶段直接把 Stage 14.4 MPC 接入真实 torque controller，也不应跳到硬件部署。


## 11. 中文说明补充

本说明文档的核心目的不是扩大项目能力边界，而是收紧表述边界。当前阶段只证明简化质心动力学下的接触力规划问题可以通过有限时域优化反复求解，并且可以在每个控制步只使用第一帧解作为当前输入。该结果属于算法层、日志层和解释层证据，不属于机器人整机闭环控制证据。

在项目叙述中，应把 Stage 14.4 明确放在规划层，而不是执行层。它可以说明项目已经补充了三维基座速度跟踪的 MPC 示例，也可以说明约束、目标函数、滚动时域求解和结果记录已经形成可复核证据。但它不能替代已有 mixed baseline，不能替代 WBC，不能代表真实关节力矩输出，也不能代表任何硬件侧准备状态。

后续文档应继续采用保守表述：先说清楚当前结果的输入、输出、假设、约束和验证方式，再说明它尚未接入哪些模块。凡是涉及硬件、执行器、真实机器人、实时控制器、力矩发布和闭环集成的内容，都必须明确标注为未完成或不在当前范围内。
