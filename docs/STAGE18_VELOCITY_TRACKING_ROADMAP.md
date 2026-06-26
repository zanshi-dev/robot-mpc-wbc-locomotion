# Stage 18: Velocity Tracking Evidence Roadmap

## 1. Stage 18 目标

Stage 18 的目标是补齐 Stage 17 的主要边界：缺少速度跟踪指标。

Stage 17 已完成：

    simulation-only conservative closed-loop rollout evidence
    low-scale MPC/WBC candidate injection
    height / roll / pitch / QP failure / torque saturation boundary validation

Stage 18 需要新增：

    base_x
    base_y
    base_vx
    target_vx
    mean_vx
    mean_abs_velocity_error
    final_x
    forward_displacement
    velocity_tracking_summary
    baseline vs candidate comparison

## 2. Stage 18 不直接声明的内容

Stage 18 不声明：

- 已完成真实机器人控制；
- 已完成硬件 torque enablement；
- 已完成高性能 MPC-WBC 控制器；
- 已证明 MPC/WBC 全面优于 baseline；
- 已完成复杂地形速度跟踪；
- 已完成多速度命令跟踪。

## 3. Stage 18 可以声明的目标

完成后可以声明：

- 已为 simulation-only closed-loop rollout 增加 velocity tracking evidence；
- 已记录 base position 和 base velocity 相关指标；
- 已完成 baseline 与 low-scale candidate injection 的速度指标对照；
- 已明确速度跟踪的适用边界和失败条件。

## 4. 最小验收指标

Stage 18 最小验收指标：

    target_vx: 0.2 m/s 或 0.3 m/s
    total_steps: 2400 或与 Stage 14.5e 一致
    base_x: 可记录
    base_vx: 可估计或直接读取
    mean_vx: 可统计
    mean_abs_velocity_error: 可统计
    final_x: 可统计
    min_z: 仍高于 0.22
    max_abs_roll: 仍低于 0.20
    max_abs_pitch: 仍低于 0.20
    qp_fail_steps: 0
    saturation_steps: 0

## 5. 推荐实现方式

优先不重写控制器，而是派生现有 runner：

    existing Stage 13 / Stage 14.5d / Stage 14.5e runner
    -> add base_x / base_y / base_vx logging
    -> add target_vx parameter
    -> add velocity summary CSV / JSON

速度估计优先级：

1. 若 MuJoCo qvel 中已有 floating base linear velocity，则直接使用 qvel[0]。
2. 若 qvel 坐标语义不确定，则用 finite difference:
   base_vx = (base_x[t] - base_x[t-1]) / dt
3. 同时记录 raw qpos[0] / qpos[1]，避免指标不可审计。

## 6. 推荐分阶段任务

### Stage 18.0

新增 velocity tracking roadmap 和验证脚本。

### Stage 18.1

检查现有 runner 的 MuJoCo state 读取方式：

    qpos
    qvel
    data.ctrl
    mj_step
    log csv
    summary csv
    target parameters

### Stage 18.2

派生 velocity tracking runner：

    scripts/stage18_2_velocity_tracking_rollout_runner.py

输出：

    results/logs_sample/stage18_2_velocity_tracking_rollout_log.csv
    results/logs_sample/stage18_2_velocity_tracking_rollout_summary.json

### Stage 18.3

生成 baseline vs candidate 速度对照表。

### Stage 18.4

同步 README / PROJECT_STATUS / ARTIFACT_INDEX 并 freeze。

## 7. 结论表述边界

推荐表述：

> Stage 18 主要补齐 Stage 17 缺少速度指标的问题。项目没有直接声明 MPC/WBC 已经成为完整主控制器，而是在 simulation-only conservative rollout 上增加 base_x、base_vx、mean_vx 和 velocity error 指标，用于评估 baseline 与 low-scale candidate injection 对前向速度的影响。

不推荐表述：

> 已完成完整 MPC-WBC 速度跟踪控制器。

> 已完成真实机器人速度控制。

> MPC/WBC 已全面优于 baseline。
