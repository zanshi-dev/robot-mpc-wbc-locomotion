# Stage 21.3 local robustness analysis

## Per-perturbation pairwise checks

| perturbation_id | recommended_minus_baseline_error | recommended_minus_0p020_error | regression_0p020_minus_baseline_error | recommended_minus_baseline_displacement | recommended_minus_0p020_displacement | recommended_pass |
| --- | --- | --- | --- | --- | --- | --- |
| nominal | -0.013229 | -0.082204 | 0.068975 | 0.191932 | 0.502599 | True |
| x_plus | -0.013229 | -0.082204 | 0.068975 | 0.191932 | 0.502599 | True |
| x_minus | -0.013229 | -0.082204 | 0.068975 | 0.191932 | 0.502599 | True |
| y_plus | -0.013229 | -0.082204 | 0.068975 | 0.191932 | 0.502599 | True |
| y_minus | -0.013229 | -0.082204 | 0.068975 | 0.191932 | 0.502599 | True |
| yaw_plus | -0.013229 | -0.082204 | 0.068975 | 0.191932 | 0.502599 | True |
| yaw_minus | -0.013229 | -0.082204 | 0.068975 | 0.191932 | 0.502599 | True |

## Per-scale perturbation statistics

| scale | role | perturbation_count | all_pass | mean_vx_mean | mean_vx_range | mean_abs_velocity_error_mean | mean_abs_velocity_error_range | forward_displacement_mean | forward_displacement_range |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | baseline_reference | 7 | True | 0.131362000000 | 0.000000000000 | 0.078494000000 | 0.000000000000 | 0.630505000000 | 0.000000000000 |
| 0.010 | recommended_candidate | 7 | True | 0.171348000000 | 0.000000000000 | 0.065265000000 | 0.000000000000 | 0.822437000000 | 0.000000000000 |
| 0.020 | regression_anchor | 7 | True | 0.066640000000 | 0.000000000000 | 0.147469000000 | 0.000000000000 | 0.319838000000 | 0.000000000000 |

## Perturbation sensitivity note

当前小范围初始位姿扰动下，记录的 summary 指标未出现可观测变化；因此该结果应解释为当前 runner 与扰动设置下的 local perturbation audit，而不是广义扰动鲁棒性结论。
