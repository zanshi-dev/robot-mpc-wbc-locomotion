# Stage 20：推荐 candidate scale 可复现性审计路线图

## 1. 背景

Stage 19 已完成 velocity-aware candidate scale sweep。

Stage 19 的关键结论是：

    在 target_vx=0.2 m/s 的 simulation-only sweep 中，
    0.000 / 0.005 / 0.010 / 0.020 / 0.050 五组 scale 均通过稳定性和安全边界。
    candidate scale 对速度跟踪影响呈非单调特征。
    scale=0.010 是当前更合理的低尺度 candidate 注入候选。
    scale=0.020 不适合作为速度跟踪默认注入强度。

Stage 20 在 Stage 19 的基础上，不继续扩大 scale sweep，而是验证推荐结论的可复现性。

## 2. Stage 20 目标

Stage 20 的目标是回答：

    scale=0.010 的推荐结论是否可复现？
    重复运行时 baseline、scale=0.010、scale=0.020 的速度指标是否一致？
    scale=0.010 相对 baseline 和 scale=0.020 的优势关系是否稳定？
    当前推荐是否可以作为 simulation-only candidate scale recommendation 被记录下来？

## 3. Stage 20 不做的事情

Stage 20 不做：

  * 不新增控制器；
  * 不修改 torque 执行链路；
  * 不把 scale=0.010 写成硬件默认值；
  * 不做真实机器人部署；
  * 不做复杂地形泛化；
  * 不做多 target_vx 泛化声明。

特别注意：

    当前 runner 中 target_vx 主要用于速度误差评价。
    在没有确认 target_vx 进入实际速度控制命令之前，不应把改变 target_vx 的测试写成“多速度命令跟踪能力”。

## 4. 推荐 replay 工况

Stage 20 初始 replay 只选择三个锚点：

    baseline: scale=0.000
    recommended candidate: scale=0.010
    regression anchor: scale=0.020

每个工况建议重复运行 3 次：

    run_00
    run_01
    run_02

如果仿真完全确定性，则同一 scale 的三次结果应完全一致或数值差异接近 0。

## 5. 需要记录的指标

每个 replay 至少记录：

    run_id
    scale
    scale_tag
    control_mode
    target_vx
    mean_vx
    mean_abs_velocity_error
    max_abs_velocity_error
    forward_displacement
    min_z
    max_abs_roll
    max_abs_pitch
    qp_fail_steps
    saturation_steps
    max_tau_total_abs
    max_tau_candidate_scaled_abs
    pass

Stage 20.3 需要派生：

    per-scale mean
    per-scale std
    per-scale max-min range
    reproducibility_pass
    recommendation_stable

## 6. 判断逻辑

Stage 20 的判断逻辑：

    如果 scale=0.010 在重复运行中稳定通过安全边界；
    且 mean_abs_velocity_error 持续低于 baseline；
    且 mean_abs_velocity_error 持续低于 scale=0.020；
    则可以记录 scale=0.010 为当前 simulation-only recommended candidate scale。

如果结果不稳定，则只能写：

    Stage 19 的推荐结论未通过 Stage 20 replay reproducibility audit。

## 7. Stage 20 不声明

Stage 20 不声明：

  * 完整 MPC-WBC 速度控制器已经完成；
  * MPC/WBC candidate 已全面优于 baseline；
  * scale=0.010 可以直接用于真实机器人；
  * 已完成真实机器人 torque 执行；
  * 已完成硬件 torque enablement；
  * scale=0.010 对所有速度、地形和扰动都最优。

## 8. Stage 20 可以支持的表述

完成后可支持类似表述：

    Stage 20 对 Stage 19 推荐的 scale=0.010 进行了 simulation-only replay reproducibility audit。
    在当前固定仿真设置下，baseline、scale=0.010 和 scale=0.020 的重复运行结果可复现；
    scale=0.010 相对 baseline 和 scale=0.020 的速度误差优势关系保持稳定。
    该结论仅作为仿真证据下的 candidate scale recommendation。

## 9. 分阶段任务

### Stage 20.0

新增路线图和验证脚本。

### Stage 20.1

检查 Stage 19.2 scale-tagged runner 是否可复用，并规划 replay 输出命名。

### Stage 20.2

重复运行 baseline / scale=0.010 / scale=0.020，生成 replay log、summary 和汇总表。

### Stage 20.3

分析重复运行结果，验证推荐关系是否稳定。

### Stage 20.4

同步 README、PROJECT_STATUS、ARTIFACT_INDEX，并冻结 Stage 20 证据。
