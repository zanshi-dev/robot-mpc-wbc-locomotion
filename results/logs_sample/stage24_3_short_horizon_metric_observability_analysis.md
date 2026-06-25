# Stage 24.3 short-horizon metric observability analysis

## Overall class

    metric_observability_class: pre_step_only_detection_no_post_step_trace_separation
    metric_audit_result: partial_detection

The short-horizon metric set detects all non-nominal qvel perturbations before or at the mj_forward trace stage, but no perturbation remains separated from nominal in the aligned after_mj_step rows. Therefore, Stage 22 long-horizon summary metrics were insensitive because the perturbation effect did not persist into the rollout-step trace used by downstream summaries.

## Class counts

| class | count |
| --- | --- |
| nominal_reference | 1 |
| pre_step_only_detection | 6 |

## Per-case analysis

| case_id | axis | written_delta | max_abs_pre_step_qvel_axis_diff_vs_nominal | post_step_max_abs_state_delta | early_window_max_abs_state_delta | case_metric_observability_class |
| --- | --- | --- | --- | --- | --- | --- |
| nominal_0p010 | qvel_0 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | nominal_reference |
| vx_plus_0p010 | qvel_0 | 0.050000000000 | 0.050000000000 | 0.000000000000 | 0.050000000000 | pre_step_only_detection |
| vx_minus_0p010 | qvel_0 | -0.050000000000 | 0.050000000000 | 0.000000000000 | 0.050000000000 | pre_step_only_detection |
| vy_plus_0p010 | qvel_1 | 0.030000000000 | 0.030000000000 | 0.000000000000 | 0.030000000000 | pre_step_only_detection |
| vy_minus_0p010 | qvel_1 | -0.030000000000 | 0.030000000000 | 0.000000000000 | 0.030000000000 | pre_step_only_detection |
| yawrate_plus_0p010 | qvel_5 | 0.050000000000 | 0.050000000000 | 0.000000000000 | 0.050000000000 | pre_step_only_detection |
| yawrate_minus_0p010 | qvel_5 | -0.050000000000 | 0.050000000000 | 0.000000000000 | 0.050000000000 | pre_step_only_detection |
