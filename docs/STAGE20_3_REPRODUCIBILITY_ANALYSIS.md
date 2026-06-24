# Stage 20.3：推荐 scale 可复现性分析

## 1. 目标

Stage 20.3 对 Stage 20.2 的 replay rollout 结果进行可复现性分析。

分析对象包括：

  * baseline: scale=0.000
  * recommended candidate: scale=0.010
  * regression anchor: scale=0.020

分析重点不是扩大泛化结论，而是验证 Stage 19 中 `scale=0.010` 的推荐关系是否能在固定仿真设置下稳定复现。

## 2. 结果

Stage 20.3 result: pass

Failure count: 0

Reproducibility pass: True

Recommendation stable: True

## 3. 关键结论

Stage 20.3 replay reproducibility audit 通过。在当前固定 simulation-only 设置下，baseline、scale=0.010 和 scale=0.020 的三次 replay 结果完全一致；scale=0.010 在每次 replay 中均保持低于 baseline 和 scale=0.020 的 mean_abs_velocity_error，且 forward_displacement 均高于 baseline 和 scale=0.020。因此，Stage 19 的 scale=0.010 推荐关系在 Stage 20 replay audit 中稳定复现。

## 4. 每个 scale 的可复现性统计

| scale | role | run_count | all_pass | mean_vx_mean | mean_vx_range | mean_abs_velocity_error_mean | mean_abs_velocity_error_range | forward_displacement_mean | forward_displacement_range |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | baseline_reference | 3 | True | 0.131362000000 | 0.000000000000 | 0.078494000000 | 0.000000000000 | 0.630505000000 | 0.000000000000 |
| 0.010 | recommended_candidate | 3 | True | 0.171348000000 | 0.000000000000 | 0.065265000000 | 0.000000000000 | 0.822437000000 | 0.000000000000 |
| 0.020 | regression_anchor | 3 | True | 0.066640000000 | 0.000000000000 | 0.147469000000 | 0.000000000000 | 0.319838000000 | 0.000000000000 |

## 5. 推荐关系逐 run 检查

| run_id | recommended_minus_baseline_error | recommended_minus_0p020_error | regression_0p020_minus_baseline_error | recommended_minus_baseline_displacement | recommended_minus_0p020_displacement |
| --- | --- | --- | --- | --- | --- |
| run_00 | -0.013229 | -0.082204 | 0.068975 | 0.191932 | 0.502599 |
| run_01 | -0.013229 | -0.082204 | 0.068975 | 0.191932 | 0.502599 |
| run_02 | -0.013229 | -0.082204 | 0.068975 | 0.191932 | 0.502599 |

## 6. 当前支持的结论

当前证据支持：

    scale=0.010 可作为当前固定 simulation-only 设置下的 recommended candidate scale。

原因：

  * 三次 replay 中，scale=0.010 均通过稳定性边界；
  * 三次 replay 中，scale=0.010 的 mean_abs_velocity_error 均低于 baseline；
  * 三次 replay 中，scale=0.010 的 mean_abs_velocity_error 均低于 scale=0.020；
  * 三次 replay 中，scale=0.010 的 forward_displacement 均高于 baseline 和 scale=0.020；
  * 三个锚点的 replay 指标在重复运行中完全一致。

## 7. 当前不支持的结论

当前证据不支持：

  * 完整 MPC-WBC 速度控制器已经完成；
  * scale=0.010 可以直接用于真实机器人；
  * scale=0.010 对所有速度、地形和扰动都最优；
  * MPC/WBC candidate 已全面优于 baseline；
  * 已完成真实机器人 torque 执行；
  * 已完成硬件 torque enablement。

## 8. 推荐表述

> Stage 20 对 Stage 19 推荐的 scale=0.010 进行了 simulation-only replay reproducibility audit。在当前固定仿真设置下，baseline、scale=0.010 和 scale=0.020 的重复运行结果完全一致；scale=0.010 相对 baseline 和 scale=0.020 的速度误差优势关系稳定复现。因此，scale=0.010 可作为当前仿真证据下的 recommended candidate scale。
