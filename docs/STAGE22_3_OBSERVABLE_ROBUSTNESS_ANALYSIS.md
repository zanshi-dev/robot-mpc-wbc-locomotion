# Stage 22.3：可观测扰动鲁棒性分析

## 1. 目标

Stage 22.3 分析 Stage 22.2 生成的 21 组 qvel 初始速度扰动 rollout，判断：

  * qvel 初始速度扰动是否造成 summary 指标的可观测变化；
  * `scale=0.010` 是否仍然通过稳定性边界；
  * `scale=0.010` 是否仍然低于 baseline 和 `scale=0.020` 的速度误差；
  * 当前推荐是否可以升级为 observable-perturbation-tested recommended candidate scale。

## 2. 结果

Stage 22.3 result: pass

Failure count: 0

Observable perturbation pass: False

Perturbation metric variability detected: False

Recommendation relation stable: True

Recommendation observable robust: False

## 3. 关键结论

Stage 22.3 analysis 通过，但 observable perturbation robustness 不成立。当前 qvel 初始速度扰动没有使 summary 指标产生可观测变化；因此 Stage 22 不能声明完成 observable perturbation robustness audit，只能记录为 qvel perturbation injection attempt。

当前证据不支持将 scale=0.010 升级为 observable-perturbation-tested recommended candidate scale；仍只能沿用 Stage 21 的 local-perturbation-tested recommended candidate scale 表述。

## 4. 推荐关系逐扰动检查

| perturbation_id | recommended_minus_baseline_error | recommended_minus_0p020_error | recommended_minus_baseline_displacement | recommended_minus_0p020_displacement | recommended_pass |
| --- | --- | --- | --- | --- | --- |
| nominal | -0.013229 | -0.082204 | 0.191932 | 0.502599 | True |
| vx_plus | -0.013229 | -0.082204 | 0.191932 | 0.502599 | True |
| vx_minus | -0.013229 | -0.082204 | 0.191932 | 0.502599 | True |
| vy_plus | -0.013229 | -0.082204 | 0.191932 | 0.502599 | True |
| vy_minus | -0.013229 | -0.082204 | 0.191932 | 0.502599 | True |
| yawrate_plus | -0.013229 | -0.082204 | 0.191932 | 0.502599 | True |
| yawrate_minus | -0.013229 | -0.082204 | 0.191932 | 0.502599 | True |

## 5. 每个 scale 的扰动统计

| scale | role | perturbation_count | all_pass | mean_vx_mean | mean_vx_range | mean_abs_velocity_error_mean | mean_abs_velocity_error_range | forward_displacement_mean | forward_displacement_range |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | baseline_reference | 7 | True | 0.131362000000 | 0.000000000000 | 0.078494000000 | 0.000000000000 | 0.630505000000 | 0.000000000000 |
| 0.010 | recommended_candidate | 7 | True | 0.171348000000 | 0.000000000000 | 0.065265000000 | 0.000000000000 | 0.822437000000 | 0.000000000000 |
| 0.020 | regression_anchor | 7 | True | 0.066640000000 | 0.000000000000 | 0.147469000000 | 0.000000000000 | 0.319838000000 | 0.000000000000 |

## 6. 可观测扰动指标变化检查

| scale_tag | metric | range | std | observable_variability |
| --- | --- | --- | --- | --- |
| 0p000 | mean_vx | 0.000000000000 | 0.000000000000 | False |
| 0p000 | mean_abs_velocity_error | 0.000000000000 | 0.000000000000 | False |
| 0p000 | max_abs_velocity_error | 0.000000000000 | 0.000000000000 | False |
| 0p000 | forward_displacement | 0.000000000000 | 0.000000000000 | False |
| 0p000 | min_z | 0.000000000000 | 0.000000000000 | False |
| 0p000 | max_abs_roll | 0.000000000000 | 0.000000000000 | False |
| 0p000 | max_abs_pitch | 0.000000000000 | 0.000000000000 | False |
| 0p000 | max_tau_total_abs | 0.000000000000 | 0.000000000000 | False |
| 0p000 | max_tau_candidate_scaled_abs | 0.000000000000 | 0.000000000000 | False |
| 0p010 | mean_vx | 0.000000000000 | 0.000000000000 | False |
| 0p010 | mean_abs_velocity_error | 0.000000000000 | 0.000000000000 | False |
| 0p010 | max_abs_velocity_error | 0.000000000000 | 0.000000000000 | False |
| 0p010 | forward_displacement | 0.000000000000 | 0.000000000000 | False |
| 0p010 | min_z | 0.000000000000 | 0.000000000000 | False |
| 0p010 | max_abs_roll | 0.000000000000 | 0.000000000000 | False |
| 0p010 | max_abs_pitch | 0.000000000000 | 0.000000000000 | False |
| 0p010 | max_tau_total_abs | 0.000000000000 | 0.000000000000 | False |
| 0p010 | max_tau_candidate_scaled_abs | 0.000000000000 | 0.000000000000 | False |
| 0p020 | mean_vx | 0.000000000000 | 0.000000000000 | False |
| 0p020 | mean_abs_velocity_error | 0.000000000000 | 0.000000000000 | False |
| 0p020 | max_abs_velocity_error | 0.000000000000 | 0.000000000000 | False |
| 0p020 | forward_displacement | 0.000000000000 | 0.000000000000 | False |
| 0p020 | min_z | 0.000000000000 | 0.000000000000 | False |
| 0p020 | max_abs_roll | 0.000000000000 | 0.000000000000 | False |
| 0p020 | max_abs_pitch | 0.000000000000 | 0.000000000000 | False |
| 0p020 | max_tau_total_abs | 0.000000000000 | 0.000000000000 | False |
| 0p020 | max_tau_candidate_scaled_abs | 0.000000000000 | 0.000000000000 | False |

## 7. 当前支持的结论

如果 `perturbation_metric_variability_detected=False`，当前证据只支持：

    Stage 22 完成了 qvel 初始速度扰动注入尝试；
    21 组 rollout 均通过稳定性边界；
    scale=0.010 的推荐关系在当前记录指标中未被破坏；
    但由于 summary 指标没有出现可观测变化，不能声明 observable perturbation robustness。

如果 `perturbation_metric_variability_detected=True` 且 `recommendation_observable_robust=True`，才支持：

    scale=0.010 可作为当前 simulation-only 证据下的 observable-perturbation-tested recommended candidate scale。

## 8. 当前不支持的结论

当前证据不支持：

  * 完整 MPC-WBC 速度控制器已经完成；
  * `scale=0.010` 可以直接用于真实机器人；
  * `scale=0.010` 对所有速度、地形、扰动和外力冲击都最优；
  * MPC/WBC candidate 已全面优于 baseline；
  * 已完成真实机器人 torque 执行；
  * 已完成硬件 torque enablement；
  * 已完成复杂地形或外力冲击鲁棒性验证。
