# Stage 22.3 observable robustness analysis

## Per-perturbation recommendation checks

| perturbation_id | recommended_minus_baseline_error | recommended_minus_0p020_error | recommended_minus_baseline_displacement | recommended_minus_0p020_displacement | recommended_pass |
| --- | --- | --- | --- | --- | --- |
| nominal | -0.013229 | -0.082204 | 0.191932 | 0.502599 | True |
| vx_plus | -0.013229 | -0.082204 | 0.191932 | 0.502599 | True |
| vx_minus | -0.013229 | -0.082204 | 0.191932 | 0.502599 | True |
| vy_plus | -0.013229 | -0.082204 | 0.191932 | 0.502599 | True |
| vy_minus | -0.013229 | -0.082204 | 0.191932 | 0.502599 | True |
| yawrate_plus | -0.013229 | -0.082204 | 0.191932 | 0.502599 | True |
| yawrate_minus | -0.013229 | -0.082204 | 0.191932 | 0.502599 | True |

## Per-scale statistics

| scale | role | perturbation_count | all_pass | mean_vx_mean | mean_vx_range | mean_abs_velocity_error_mean | mean_abs_velocity_error_range | forward_displacement_mean | forward_displacement_range |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | baseline_reference | 7 | True | 0.131362000000 | 0.000000000000 | 0.078494000000 | 0.000000000000 | 0.630505000000 | 0.000000000000 |
| 0.010 | recommended_candidate | 7 | True | 0.171348000000 | 0.000000000000 | 0.065265000000 | 0.000000000000 | 0.822437000000 | 0.000000000000 |
| 0.020 | regression_anchor | 7 | True | 0.066640000000 | 0.000000000000 | 0.147469000000 | 0.000000000000 | 0.319838000000 | 0.000000000000 |

## Perturbation metric variability

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
