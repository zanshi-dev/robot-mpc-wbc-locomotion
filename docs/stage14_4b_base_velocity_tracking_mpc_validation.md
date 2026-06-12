# Stage 14.4B：基座速度跟踪 MPC rollout 验证

## 1. 阶段范围

Stage 14.4B 对 Stage 14.4A 的 standalone simplified 3D base velocity tracking MPC rollout 进行独立验证。

本阶段不修改 MPC 公式，不修改 MPC 控制律，不连接 MuJoCo torque execution，不发布 ROS 力矩命令，不修改 frozen mixed baseline，不修改 disabled_controller_node.cpp。

项目仍然保持 simulation-only。

## 2. 输入文件

Stage 14.4A summary：

results/logs_sample/stage14_4_base_velocity_tracking_mpc_summary.json

Stage 14.4A rollout CSV：

results/logs_sample/stage14_4_base_velocity_tracking_mpc_rollout.csv

Stage 14.4A 源码：

scripts/stage14_4_base_velocity_tracking_mpc_demo.py

## 3. 验证内容

验证脚本检查以下内容：

- Stage 14.4A summary 的 pass 必须为 true
- safety flags 必须保持 simulation-only 边界
- rollout CSV 必须包含必要字段
- 所有 rollout step 的 OSQP status 必须为 solved 或 solved inaccurate
- 所有状态和力数值必须为 finite
- swing force norm 必须接近 0
- stance vertical force 必须保持在配置上下界内
- friction pyramid violation 必须接近 0
- total vertical force upper violation 必须接近 0
- vx tracking 必须相对初始状态改善
- final vx、vy 和 z error 必须在阈值内
- 源码必须体现 receding-horizon 模式：循环读取当前状态、重解 QP、只应用 u0、推进简化质心动力学、更新上一帧力用于平滑项

## 4. 输出文件

逐步验证 CSV：

results/logs_sample/stage14_4b_base_velocity_tracking_mpc_validation.csv

验证 summary JSON：

results/logs_sample/stage14_4b_base_velocity_tracking_mpc_validation_summary.json

## 5. 边界说明

Stage 14.4B 只提供简化基座速度跟踪 MPC demo 的验证证据。

它不是 WBC 集成，不是 MuJoCo torque 控制，不是 ROS torque publisher 验证，不是硬件部署，也不是真实机器人力矩执行证据。


## Stage 14.4 中文边界说明

Stage 14.4 是 standalone simplified 3D base velocity tracking receding-horizon MPC demo，当前只属于规划层算法示例。

该 MPC 不接 ROS torque publisher，不接 MuJoCo torque，不直接输出 joint torque，不改变 mixed baseline 控制律。当前结果仍然是 simulation-only 的算法与日志证据，不是硬件部署证据，也不是真实机器人力矩执行证据。

本阶段可以说明 MPC 在简化质心动力学 rollout 中完成了状态、接触力、约束指标、求解状态和 summary JSON 的可复核记录。不能说明 MPC 已经接入真实 locomotion controller，也不能说明 MPC 与 WBC 已形成闭环集成。
