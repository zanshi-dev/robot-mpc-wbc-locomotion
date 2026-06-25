# Stage 24.2 short-horizon perturbation-sensitive metrics

## Per-case metrics

| case_id | axis | written_delta | after_forward_delta | max_abs_pre_step_qvel_axis_diff_vs_nominal | max_abs_qvel_axis_diff_vs_nominal | max_abs_qpos_axis_diff_vs_nominal | post_step_max_abs_state_delta | early_window_max_abs_state_delta | pre_step_trace_separation_detected | post_step_trace_separation_detected | early_window_trace_separation_detected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nominal_0p010 | qvel_0 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | False | False | False |
| vx_plus_0p010 | qvel_0 | 0.050000000000 | 0.050000000000 | 0.050000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.050000000000 | True | False | True |
| vx_minus_0p010 | qvel_0 | -0.050000000000 | -0.050000000000 | 0.050000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.050000000000 | True | False | True |
| vy_plus_0p010 | qvel_1 | 0.030000000000 | 0.030000000000 | 0.030000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.030000000000 | True | False | True |
| vy_minus_0p010 | qvel_1 | -0.030000000000 | -0.030000000000 | 0.030000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.030000000000 | True | False | True |
| yawrate_plus_0p010 | qvel_5 | 0.050000000000 | 0.050000000000 | 0.050000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.050000000000 | True | False | True |
| yawrate_minus_0p010 | qvel_5 | -0.050000000000 | -0.050000000000 | 0.050000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.050000000000 | True | False | True |

## Aggregate metrics

| metric | value | interpretation |
| --- | --- | --- |
| non_nominal_case_count | 6 | number of perturbation cases compared with nominal |
| any_pre_step_trace_separation_detected | True | whether any perturbation is visible before/at mj_forward trace |
| all_pre_step_trace_separation_detected | True | whether all non-nominal perturbations are visible before/at mj_forward trace |
| any_post_step_trace_separation_detected | False | whether any perturbation remains separated from nominal during after_mj_step rows |
| any_early_window_trace_separation_detected | True | whether short-horizon metric set can detect perturbation effect |
| all_early_window_trace_separation_detected | True | whether all perturbation cases are detected by short-horizon metric set |
| max_early_window_max_abs_state_delta | 0.050000000000 | largest detected short-horizon state separation |
| mean_early_window_mean_abs_state_delta | 0.001604938272 | average detected short-horizon state separation |
