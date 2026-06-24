# Stage 19.3 velocity-stability tradeoff analysis

## Analysis table

| scale | mean_vx | mean_abs_velocity_error | forward_displacement | delta_error_vs_baseline | pass | recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 0.131362 | 0.078494 | 0.630505 | 0.000000 | True | baseline_reference |
| 0.005 | 0.172518 | 0.085663 | 0.828054 | 0.007169 | True | stable_but_not_best |
| 0.010 | 0.171348 | 0.065265 | 0.822437 | -0.013229 | True | recommended_candidate |
| 0.020 | 0.066640 | 0.147469 | 0.319838 | 0.068975 | True | not_recommended_velocity_regression |
| 0.050 | 0.144905 | 0.089988 | 0.695506 | 0.011494 | True | stable_but_not_best |

## Ranking by velocity error

| rank | scale | mean_abs_velocity_error | mean_vx | forward_displacement | recommendation |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.010 | 0.065265 | 0.171348 | 0.822437 | recommended_candidate |
| 2 | 0.000 | 0.078494 | 0.131362 | 0.630505 | baseline_reference |
| 3 | 0.005 | 0.085663 | 0.172518 | 0.828054 | stable_but_not_best |
| 4 | 0.050 | 0.089988 | 0.144905 | 0.695506 | stable_but_not_best |
| 5 | 0.020 | 0.147469 | 0.066640 | 0.319838 | not_recommended_velocity_regression |
