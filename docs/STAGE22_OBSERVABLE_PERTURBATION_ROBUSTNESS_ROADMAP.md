# Stage 22：可观测扰动鲁棒性审计路线图

## 1. 背景

Stage 21 完成了 recommended scale local perturbation robustness audit，并得到：

    local_robustness_pass=True
    recommendation_robust=True
    perturbation_metric_variability_detected=False

这说明 scale=0.010 在当前小范围初始位姿扰动设置下保持了推荐关系，但也暴露出一个边界：

    当前扰动设置下，summary 指标未出现可观测变化。

因此 Stage 21 只能作为当前 runner 与扰动设置下的 local perturbation audit evidence，不能扩展为广义扰动鲁棒性、复杂地形鲁棒性或外力冲击鲁棒性结论。

Stage 22 在 Stage 21 的基础上，进一步引入更容易影响 rollout 的初始速度扰动，目标是让扰动对 summary 指标产生可观测变化。

## 2. Stage 22 目标

Stage 22 的目标是回答：

    初始速度扰动是否能被 runner 正确注入？
    初始速度扰动是否能让 summary 指标出现可观测变化？
    在可观测扰动下，scale=0.010 是否仍然稳定？
    在可观测扰动下，scale=0.010 是否仍然低于 baseline 和 scale=0.020 的速度误差？
    当前推荐能否从 local-perturbation-tested 升级为 observable-perturbation-tested recommended candidate scale？

## 3. Stage 22 不做的事情

Stage 22 不做：

  * 不新增控制器；
  * 不修改 torque 执行链路；
  * 不做真实机器人部署；
  * 不做硬件 torque enablement；
  * 不做复杂地形；
  * 不做外力冲击扰动；
  * 不做多 target_vx 泛化声明；
  * 不声明 scale=0.010 对所有速度、地形、扰动和外力冲击都最优。

特别注意：

    Stage 22 的扰动仍然是 simulation-only 初始状态扰动。
    target_vx 仍固定为 0.2 m/s，避免把评价目标误写成多速度命令跟踪能力。
    Stage 22.1 必须先确认 qvel 注入点，再进行 Stage 22.2 rollout。

## 4. 推荐扰动工况

Stage 22 建议使用初始速度扰动：

    nominal: 无扰动
    vx_plus: 初始 base vx +0.05 m/s
    vx_minus: 初始 base vx -0.05 m/s
    vy_plus: 初始 base vy +0.03 m/s
    vy_minus: 初始 base vy -0.03 m/s
    yawrate_plus: 初始 yaw rate +0.05 rad/s
    yawrate_minus: 初始 yaw rate -0.05 rad/s

每个 perturbation case 测试三个 scale：

    baseline: scale=0.000
    recommended candidate: scale=0.010
    regression anchor: scale=0.020

总测试数量：

    7 perturbation cases × 3 scale anchors = 21 rollouts

## 5. 需要记录的指标

每个 rollout 至少记录：

    perturbation_id
    perturbation_type
    perturb_vx
    perturb_vy
    perturb_yawrate
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

Stage 22.3 需要派生：

    perturbation_metric_variability_detected
    observable_perturbation_pass
    recommendation_observable_robust
    per-perturbation ranking
    recommended_vs_baseline_error_delta
    recommended_vs_0p020_error_delta
    recommended_vs_baseline_displacement_delta
    recommended_vs_0p020_displacement_delta

## 6. 判断逻辑

Stage 22 的判断逻辑：

    如果初始速度扰动能让 summary 指标出现可观测变化；
    且 scale=0.010 在所有扰动工况中均通过稳定性边界；
    且 scale=0.010 的 mean_abs_velocity_error 在所有或多数扰动工况中低于 baseline；
    且 scale=0.010 的 mean_abs_velocity_error 在所有或多数扰动工况中低于 scale=0.020；
    则可以记录为 observable-perturbation-tested recommended candidate scale。

更严格的理想结论是：

    perturbation_metric_variability_detected=True
    observable_perturbation_pass=True
    recommendation_observable_robust=True

如果扰动没有造成 summary 指标变化，则 Stage 22 不能声称完成可观测扰动鲁棒性审计。

如果扰动造成指标变化，但 scale=0.010 推荐关系不再稳定，则应记录为推荐关系在可观测扰动下未完全成立。

## 7. Stage 22 不声明

Stage 22 不声明：

  * 完整 MPC-WBC 速度控制器已经完成；
  * scale=0.010 可以直接用于真实机器人；
  * scale=0.010 对所有速度、地形、扰动和外力冲击都最优；
  * MPC/WBC candidate 已全面优于 baseline；
  * 已完成真实机器人 torque 执行；
  * 已完成硬件 torque enablement；
  * 已完成复杂地形或外力冲击鲁棒性验证。

## 8. Stage 22 可以支持的表述

如果 Stage 22.2–22.3 通过，最多支持类似表述：

    Stage 22 对 Stage 20 推荐的 scale=0.010 进行了 simulation-only observable perturbation robustness audit。
    在当前初始速度扰动设置下，扰动对 rollout 指标产生可观测影响；
    scale=0.010 通过稳定性边界，并与 baseline 和 scale=0.020 进行速度误差和前向位移对比。
    该结论仅作为仿真证据下的 observable perturbation evidence。

## 9. 分阶段任务

### Stage 22.0

新增路线图和验证脚本。

### Stage 22.1

检查 Stage 21.2 runner 或 Stage 20.2 runner 是否可派生 qvel perturbation 版本，并确认初始 qvel 注入点。

### Stage 22.2

运行 nominal、vx/vy/yawrate 初始速度扰动下的 baseline / scale=0.010 / scale=0.020 rollout evidence。

### Stage 22.3

分析可观测扰动下的速度误差、前向位移、稳定性边界和扰动指标变化，判断 scale=0.010 推荐关系是否在可观测扰动下稳定。

### Stage 22.4

同步 README、PROJECT_STATUS、ARTIFACT_INDEX，并冻结 Stage 22 证据。
