# Stage 23.3：扰动可观测性根因分析

## 1. 目标

Stage 23.3 基于 Stage 23.2 的 qvel injection trace diagnostic，解释 Stage 22 中 qvel 初始速度扰动没有造成 summary 指标变化的原因。

本阶段不新增控制器，不新增真实机器人实验，不重新声明 observable perturbation robustness。

## 2. 结果

Stage 23.3 result: pass

Failure count: 0

Overall root cause: `C_summary_metrics_insensitive_to_short_horizon_trace_change`

Root-cause confidence: `high`

## 3. 关键结论

Stage 23.3 root-cause analysis indicates that the Stage 22 qvel perturbations were injected and visible in short-horizon trace data, but the Stage 22 rollout summary metrics did not vary. The root cause is therefore summary-metric insensitivity to short-horizon initial qvel perturbations.

Stage 23 supports explaining Stage 22 negative evidence as a metric/observability limitation, not as a successful observable robustness validation.

## 4. Stage 22 negative evidence 背景

    observable_perturbation_pass=False
    perturbation_metric_variability_detected=False
    recommendation_relation_stable=True
    recommendation_observable_robust=False

## 5. Stage 23.2 trace flags

    all_nonzero_perturbations_written=True
    all_after_forward_preserved=True
    any_first_step_state_changed=True

## 6. 根因类别计数

| root_cause_class | count |
| --- | --- |
| C_summary_metrics_insensitive_to_short_horizon_trace_change | 6 |
| nominal_reference | 1 |

## 7. 逐 case 根因分析

| trace_case_id | axis | expected_delta | written_delta | after_forward_delta | first_step_qvel_delta | qpos_delta_first_step | injection_written | after_forward_preserved | first_step_state_changed | root_cause_class |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nominal_0p010 | qvel_0 | 0.000000000000 | 0.000000000000 | 0.000000000000 | -0.016621033634 | -0.000033242067 | True | True | True | nominal_reference |
| vx_plus_0p010 | qvel_0 | 0.050000000000 | 0.050000000000 | 0.050000000000 | -0.016621033634 | -0.000033242067 | True | True | True | C_summary_metrics_insensitive_to_short_horizon_trace_change |
| vx_minus_0p010 | qvel_0 | -0.050000000000 | -0.050000000000 | -0.050000000000 | -0.016621033634 | -0.000033242067 | True | True | True | C_summary_metrics_insensitive_to_short_horizon_trace_change |
| vy_plus_0p010 | qvel_1 | 0.030000000000 | 0.030000000000 | 0.030000000000 | 0.000213879716 | 0.000000427759 | True | True | True | C_summary_metrics_insensitive_to_short_horizon_trace_change |
| vy_minus_0p010 | qvel_1 | -0.030000000000 | -0.030000000000 | -0.030000000000 | 0.000213879716 | 0.000000427759 | True | True | True | C_summary_metrics_insensitive_to_short_horizon_trace_change |
| yawrate_plus_0p010 | qvel_5 | 0.050000000000 | 0.050000000000 | 0.050000000000 | -0.031726322323 | -0.000000022225 | True | True | True | C_summary_metrics_insensitive_to_short_horizon_trace_change |
| yawrate_minus_0p010 | qvel_5 | -0.050000000000 | -0.050000000000 | -0.050000000000 | -0.031726322323 | -0.000000022225 | True | True | True | C_summary_metrics_insensitive_to_short_horizon_trace_change |

## 8. 当前支持的表述

Stage 23 支持：

    Stage 23 对 Stage 22 的 qvel perturbation negative evidence 进行了 root-cause audit。
    当前结果解释了 Stage 22 为什么没有形成 observable perturbation robustness evidence。

## 9. 当前不支持的表述

Stage 23 不支持：

  * 不支持 `scale=0.010` 已通过 observable perturbation robustness 验证；
  * 不支持 `scale=0.010` 升级为 observable-perturbation-tested recommended candidate scale；
  * 不支持完整 MPC-WBC 速度控制器已经完成；
  * 不支持 `scale=0.010` 可以直接用于真实机器人；
  * 不支持真实机器人 torque 执行或硬件 torque enablement 已完成；
  * 不支持复杂地形或外力冲击鲁棒性已完成。
