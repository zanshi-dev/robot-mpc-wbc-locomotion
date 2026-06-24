# Stage 21：推荐 candidate scale 局部扰动鲁棒性审计路线图

## 1. 背景

Stage 19 完成了 velocity-aware candidate scale sweep，并发现：

    scale=0.010 是当前更合理的低尺度 candidate 注入候选；
    scale=0.020 不适合作为速度跟踪默认注入强度。

Stage 20 在固定仿真设置下对 scale=0.010 进行了 replay reproducibility audit，并发现：

    baseline、scale=0.010、scale=0.020 的三次 replay 结果完全一致；
    scale=0.010 相对 baseline 和 scale=0.020 的速度误差优势关系稳定复现。

Stage 21 在 Stage 20 的基础上，进一步做小范围初始状态扰动下的 local robustness audit。

## 2. Stage 21 目标

Stage 21 的目标是回答：

    在轻微初始状态扰动下，scale=0.010 是否仍然稳定？
    scale=0.010 相对 baseline 的速度误差优势是否仍然存在？
    scale=0.010 相对 scale=0.020 的优势关系是否仍然存在？
    当前推荐是否可以从 fixed-setting recommendation 升级为 local-perturbation-tested recommendation？

## 3. Stage 21 不做的事情

Stage 21 不做：

  * 不新增控制器；
  * 不修改 torque 执行链路；
  * 不做真实机器人部署；
  * 不做复杂地形；
  * 不做外力冲击扰动；
  * 不做多 target_vx 泛化声明；
  * 不声明 scale=0.010 对所有速度、地形和扰动都最优。

特别注意：

    Stage 21 的扰动只用于仿真审计，不代表真实硬件扰动测试。
    target_vx 仍固定为 0.2 m/s，避免把评价指标误写成多速度命令跟踪能力。

## 4. 推荐扰动工况

Stage 21 初始扰动建议只使用小范围初始位姿扰动：

    nominal: 无扰动
    x_plus: base_x + 0.02 m
    x_minus: base_x - 0.02 m
    y_plus: base_y + 0.02 m
    y_minus: base_y - 0.02 m
    yaw_plus: yaw + 0.03 rad
    yaw_minus: yaw - 0.03 rad

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
    perturb_x
    perturb_y
    perturb_yaw
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

Stage 21.3 需要派生：

    per-perturbation ranking
    recommended_vs_baseline_error_delta
    recommended_vs_0p020_error_delta
    recommended_vs_baseline_displacement_delta
    recommended_vs_0p020_displacement_delta
    local_robustness_pass
    recommendation_robust

## 6. 判断逻辑

Stage 21 的判断逻辑：

    如果 scale=0.010 在所有扰动工况中均通过稳定性边界；
    且 scale=0.010 的 mean_abs_velocity_error 在多数或全部扰动工况中低于 baseline；
    且 scale=0.010 的 mean_abs_velocity_error 在多数或全部扰动工况中低于 scale=0.020；
    则可以记录为 local-perturbation-tested recommended candidate scale。

更严格的理想结论是：

    scale=0.010 在所有 perturbation cases 中均低于 baseline 和 scale=0.020 的速度误差。

如果有个别扰动下关系不成立，则只能写成：

    scale=0.010 在当前局部扰动审计中大体保持稳定，但推荐关系不是全扰动严格成立。

## 7. Stage 21 不声明

Stage 21 不声明：

  * 完整 MPC-WBC 速度控制器已经完成；
  * scale=0.010 可以直接用于真实机器人；
  * scale=0.010 对所有速度、地形和扰动都最优；
  * MPC/WBC candidate 已全面优于 baseline；
  * 已完成真实机器人 torque 执行；
  * 已完成硬件 torque enablement；
  * 已完成复杂地形或外力扰动鲁棒性验证。

## 8. Stage 21 可以支持的表述

如果 Stage 21.2–21.3 通过，最多支持类似表述：

    Stage 21 对 Stage 20 推荐的 scale=0.010 进行了 simulation-only local perturbation robustness audit。
    在当前小范围初始状态扰动设置下，scale=0.010 通过稳定性边界；
    并与 baseline 和 scale=0.020 进行速度误差和前向位移对比。
    该结论仅作为仿真证据下的 local robustness evidence。

## 9. 分阶段任务

### Stage 21.0

新增路线图和验证脚本。

### Stage 21.1

检查 Stage 20.2 replay runner 是否可派生扰动版本，并确认初始 qpos / yaw 注入点。

### Stage 21.2

运行 nominal、x/y/yaw 小扰动下的 baseline / scale=0.010 / scale=0.020 rollout evidence。

### Stage 21.3

分析扰动下的速度误差、前向位移和稳定性边界，判断 scale=0.010 推荐关系是否在局部扰动下稳定。

### Stage 21.4

同步 README、PROJECT_STATUS、ARTIFACT_INDEX，并冻结 Stage 21 证据。
