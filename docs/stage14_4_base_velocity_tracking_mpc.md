# Stage 14.4A：基座速度跟踪 MPC

## 1. 阶段范围

本阶段新增一个独立的、简化的三维基座速度跟踪 receding-horizon MPC demo。

本阶段只属于 simulation-only 算法验证，不发布 ROS 力矩命令，不连接 MuJoCo torque execution，不修改 frozen mixed baseline，不修改 disabled_controller_node.cpp，不宣称硬件部署、执行器使能或真实机器人力矩执行。

## 2. 状态、输入与动力学

状态定义为：

x = [px, py, pz, vx, vy, vz]

输入定义为四个足端的三维接触力：

u = [f1x, f1y, f1z, f2x, f2y, f2z, f3x, f3y, f3z, f4x, f4y, f4z]

简化离散质心动力学为：

p_next = p + dt * v

v_next = v + dt * (sum_i f_i / m + g)

每个 rollout step 只应用 horizon 第一帧接触力 u0。下一步重新读取当前状态并重新求解 QP，因此该 demo 体现的是 receding-horizon MPC，而不是一次性 open-loop 轨迹回放。

## 3. 约束

摆动腿接触力被约束为 0。

支撑腿满足：

fz_min <= fz <= fz_max

|fx| <= mu * fz

|fy| <= mu * fz

总竖直力满足：

sum_fz <= total_fz_max

## 4. 目标函数

QP 目标包括：

- 跟踪 vx_ref
- 抑制 vy 漂移
- 保持 z 接近 z_ref
- 抑制 vz
- 正则化接触力
- 平滑相邻控制输入

## 5. 输出文件

脚本：

scripts/stage14_4_base_velocity_tracking_mpc_demo.py

rollout CSV：

results/logs_sample/stage14_4_base_velocity_tracking_mpc_rollout.csv

summary JSON：

results/logs_sample/stage14_4_base_velocity_tracking_mpc_summary.json

## 6. 验收标准

summary JSON 中 pass 必须为 true。

必须保留以下安全边界：

simulation_only_project=true

hardware_deployment_completed=false

torque_enable_ready=false

torque_publisher_enabled=false

control_law_changed=false

## 7. 当前不能宣称的内容

Stage 14.4A 不能被描述为 WBC 集成，不能被描述为 MuJoCo torque closed-loop 控制，不能被描述为 ROS torque publisher 已启用，也不能被描述为硬件控制器完成。

本阶段只证明简化质心动力学下的三维基座速度跟踪 MPC demo 可以独立运行并生成可复核日志。


## Stage 14.4 中文边界说明

Stage 14.4 是 standalone simplified 3D base velocity tracking receding-horizon MPC demo，当前只属于规划层算法示例。

该 MPC 不接 ROS torque publisher，不接 MuJoCo torque，不直接输出 joint torque，不改变 mixed baseline 控制律。当前结果仍然是 simulation-only 的算法与日志证据，不是硬件部署证据，也不是真实机器人力矩执行证据。

本阶段可以说明 MPC 在简化质心动力学 rollout 中完成了状态、接触力、约束指标、求解状态和 summary JSON 的可复核记录。不能说明 MPC 已经接入真实 locomotion controller，也不能说明 MPC 与 WBC 已形成闭环集成。
