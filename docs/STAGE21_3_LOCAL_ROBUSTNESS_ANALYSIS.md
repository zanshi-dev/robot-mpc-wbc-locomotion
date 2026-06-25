# Stage 21.3：局部扰动鲁棒性分析

## 1. 目标

Stage 21.3 对 Stage 21.2 的 21 组 local perturbation rollout 进行分析，判断 Stage 20 推荐的 `scale=0.010` 是否在小范围初始状态扰动下仍然稳定。

分析对象：

  * perturbation cases: nominal / x_plus / x_minus / y_plus / y_minus / yaw_plus / yaw_minus
  * scale anchors: 0.000 / 0.010 / 0.020
  * target_vx: 0.2 m/s

## 2. 结果

Stage 21.3 result: pass

Failure count: 0

Local robustness pass: True

Recommendation robust: True

Perturbation metric variability detected: False

## 3. 关键结论

Stage 21.3 local robustness analysis 通过。在当前 7 个小范围初始状态扰动工况下，scale=0.010 均通过稳定性边界；scale=0.010 在所有扰动工况中均保持低于 baseline 和 scale=0.020 的 mean_abs_velocity_error，且 forward_displacement 均高于 baseline 和 scale=0.020。因此，scale=0.010 可从 fixed-setting recommended candidate scale 扩展为当前仿真证据下的 local-perturbation-tested recommended candidate scale。

## 4. 推荐关系逐扰动检查

| perturbation_id | recommended_minus_baseline_error | recommended_minus_0p020_error | regression_0p020_minus_baseline_error | recommended_minus_baseline_displacement | recommended_minus_0p020_displacement | recommended_pass |
| --- | --- | --- | --- | --- | --- | --- |
| nominal | -0.013229 | -0.082204 | 0.068975 | 0.191932 | 0.502599 | True |
| x_plus | -0.013229 | -0.082204 | 0.068975 | 0.191932 | 0.502599 | True |
| x_minus | -0.013229 | -0.082204 | 0.068975 | 0.191932 | 0.502599 | True |
| y_plus | -0.013229 | -0.082204 | 0.068975 | 0.191932 | 0.502599 | True |
| y_minus | -0.013229 | -0.082204 | 0.068975 | 0.191932 | 0.502599 | True |
| yaw_plus | -0.013229 | -0.082204 | 0.068975 | 0.191932 | 0.502599 | True |
| yaw_minus | -0.013229 | -0.082204 | 0.068975 | 0.191932 | 0.502599 | True |

## 5. 每个 scale 的扰动统计

| scale | role | perturbation_count | all_pass | mean_vx_mean | mean_vx_range | mean_abs_velocity_error_mean | mean_abs_velocity_error_range | forward_displacement_mean | forward_displacement_range |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | baseline_reference | 7 | True | 0.131362000000 | 0.000000000000 | 0.078494000000 | 0.000000000000 | 0.630505000000 | 0.000000000000 |
| 0.010 | recommended_candidate | 7 | True | 0.171348000000 | 0.000000000000 | 0.065265000000 | 0.000000000000 | 0.822437000000 | 0.000000000000 |
| 0.020 | regression_anchor | 7 | True | 0.066640000000 | 0.000000000000 | 0.147469000000 | 0.000000000000 | 0.319838000000 | 0.000000000000 |

## 6. 扰动敏感性说明

当前小范围初始位姿扰动下，记录的 summary 指标未出现可观测变化；因此该结果应解释为当前 runner 与扰动设置下的 local perturbation audit，而不是广义扰动鲁棒性结论。

## 7. 当前支持的结论

当前证据支持：

    scale=0.010 可作为当前 simulation-only 证据下的 local-perturbation-tested recommended candidate scale。

原因：

  * 7 个扰动工况中，scale=0.010 均通过稳定性边界；
  * 7 个扰动工况中，scale=0.010 的 mean_abs_velocity_error 均低于 baseline；
  * 7 个扰动工况中，scale=0.010 的 mean_abs_velocity_error 均低于 scale=0.020；
  * 7 个扰动工况中，scale=0.010 的 forward_displacement 均高于 baseline 和 scale=0.020。

## 8. 当前不支持的结论

当前证据不支持：

  * 完整 MPC-WBC 速度控制器已经完成；
  * scale=0.010 可以直接用于真实机器人；
  * scale=0.010 对所有速度、地形、扰动和外力冲击都最优；
  * MPC/WBC candidate 已全面优于 baseline；
  * 已完成真实机器人 torque 执行；
  * 已完成硬件 torque enablement；
  * 已完成复杂地形或外力扰动鲁棒性验证。

## 9. 推荐表述

> Stage 21 对 Stage 20 推荐的 scale=0.010 进行了 simulation-only local perturbation robustness audit。在当前小范围初始状态扰动设置下，scale=0.010 均通过稳定性边界，并在所有扰动工况中保持低于 baseline 和 scale=0.020 的速度误差。因此，scale=0.010 可作为当前仿真证据下的 local-perturbation-tested recommended candidate scale。
