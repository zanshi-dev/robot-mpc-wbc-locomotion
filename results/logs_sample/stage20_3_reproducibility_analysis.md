# Stage 20.3 reproducibility analysis

## Per-scale reproducibility statistics

| scale | role | run_count | all_pass | mean_vx_mean | mean_vx_range | mean_abs_velocity_error_mean | mean_abs_velocity_error_range | forward_displacement_mean | forward_displacement_range |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | baseline_reference | 3 | True | 0.131362000000 | 0.000000000000 | 0.078494000000 | 0.000000000000 | 0.630505000000 | 0.000000000000 |
| 0.010 | recommended_candidate | 3 | True | 0.171348000000 | 0.000000000000 | 0.065265000000 | 0.000000000000 | 0.822437000000 | 0.000000000000 |
| 0.020 | regression_anchor | 3 | True | 0.066640000000 | 0.000000000000 | 0.147469000000 | 0.000000000000 | 0.319838000000 | 0.000000000000 |

## Pairwise recommendation checks

| run_id | recommended_minus_baseline_error | recommended_minus_0p020_error | regression_0p020_minus_baseline_error | recommended_minus_baseline_displacement | recommended_minus_0p020_displacement |
| --- | --- | --- | --- | --- | --- |
| run_00 | -0.013229 | -0.082204 | 0.068975 | 0.191932 | 0.502599 |
| run_01 | -0.013229 | -0.082204 | 0.068975 | 0.191932 | 0.502599 |
| run_02 | -0.013229 | -0.082204 | 0.068975 | 0.191932 | 0.502599 |
