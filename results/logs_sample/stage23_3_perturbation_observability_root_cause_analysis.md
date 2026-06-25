# Stage 23.3 perturbation observability root-cause analysis

## Overall root cause

    overall_root_cause: C_summary_metrics_insensitive_to_short_horizon_trace_change
    root_cause_confidence: high

Nonzero qvel perturbations were written, preserved after mj_forward, and produced short-horizon state differences. However, Stage 22 summary metrics remained identical across perturbation cases. Thus the Stage 22 negative evidence is best explained by summary-metric insensitivity to short-horizon initial qvel changes.

## Classification counts

| root_cause_class | count |
| --- | --- |
| C_summary_metrics_insensitive_to_short_horizon_trace_change | 6 |
| nominal_reference | 1 |

## Per-case classification

| trace_case_id | axis | expected_delta | written_delta | after_forward_delta | first_step_qvel_delta | qpos_delta_first_step | injection_written | after_forward_preserved | first_step_state_changed | root_cause_class |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nominal_0p010 | qvel_0 | 0.000000000000 | 0.000000000000 | 0.000000000000 | -0.016621033634 | -0.000033242067 | True | True | True | nominal_reference |
| vx_plus_0p010 | qvel_0 | 0.050000000000 | 0.050000000000 | 0.050000000000 | -0.016621033634 | -0.000033242067 | True | True | True | C_summary_metrics_insensitive_to_short_horizon_trace_change |
| vx_minus_0p010 | qvel_0 | -0.050000000000 | -0.050000000000 | -0.050000000000 | -0.016621033634 | -0.000033242067 | True | True | True | C_summary_metrics_insensitive_to_short_horizon_trace_change |
| vy_plus_0p010 | qvel_1 | 0.030000000000 | 0.030000000000 | 0.030000000000 | 0.000213879716 | 0.000000427759 | True | True | True | C_summary_metrics_insensitive_to_short_horizon_trace_change |
| vy_minus_0p010 | qvel_1 | -0.030000000000 | -0.030000000000 | -0.030000000000 | 0.000213879716 | 0.000000427759 | True | True | True | C_summary_metrics_insensitive_to_short_horizon_trace_change |
| yawrate_plus_0p010 | qvel_5 | 0.050000000000 | 0.050000000000 | 0.050000000000 | -0.031726322323 | -0.000000022225 | True | True | True | C_summary_metrics_insensitive_to_short_horizon_trace_change |
| yawrate_minus_0p010 | qvel_5 | -0.050000000000 | -0.050000000000 | -0.050000000000 | -0.031726322323 | -0.000000022225 | True | True | True | C_summary_metrics_insensitive_to_short_horizon_trace_change |
