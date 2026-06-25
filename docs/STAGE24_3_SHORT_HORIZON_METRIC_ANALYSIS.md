# Stage 24.3：short-horizon metric observability analysis

## 1. 目标

Stage 24.3 分析 Stage 24.2 计算出的短时 perturbation-sensitive metrics，判断这些指标如何解释 Stage 22 长期 summary 指标不敏感问题。

本阶段不新增 rollout，不新增控制器，不重新声明 observable perturbation robustness。

## 2. 结果

Stage 24.3 result: pass

Failure count: 0

Metric observability class: `pre_step_only_detection_no_post_step_trace_separation`

Metric audit result: `partial_detection`

## 3. 关键结论

Stage 24.3 shows that short-horizon perturbation-sensitive metrics detect the injected qvel perturbations only in the pre-step / mj_forward trace segment. The aligned after_mj_step rows are not separated from nominal. This refines the Stage 23 root cause: Stage 22 summary metrics were insensitive because the perturbation signature was visible at injection time but did not persist into the rollout-step trace.

Stage 24 supports adding explicit injection-stage or pre-step trace metrics for future perturbation audits. It does not support observable robustness or a scale=0.010 recommendation upgrade.

## 4. 与 Stage 22 / Stage 23 的关系

Stage 22 结果：

    observable_perturbation_pass=False
    perturbation_metric_variability_detected=False
    recommendation_observable_robust=False

Stage 23 根因：

    overall_root_cause=C_summary_metrics_insensitive_to_short_horizon_trace_change
    root_cause_confidence=high

Stage 24.2 指标：

    any_pre_step_trace_separation_detected=True
    all_pre_step_trace_separation_detected=True
    any_post_step_trace_separation_detected=False
    any_early_window_trace_separation_detected=True
    all_early_window_trace_separation_detected=True

## 5. 数值摘要

    max_pre_step_qvel_axis_diff_vs_nominal=0.050000000000
    max_post_step_state_delta=0.000000000000
    max_early_window_state_delta=0.050000000000
    mean_early_window_state_delta=0.001604938272

## 6. 类别计数

| class | count |
| --- | --- |
| nominal_reference | 1 |
| pre_step_only_detection | 6 |

## 7. 逐 case 分析

| case_id | axis | written_delta | max_abs_pre_step_qvel_axis_diff_vs_nominal | post_step_max_abs_state_delta | early_window_max_abs_state_delta | case_metric_observability_class |
| --- | --- | --- | --- | --- | --- | --- |
| nominal_0p010 | qvel_0 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | nominal_reference |
| vx_plus_0p010 | qvel_0 | 0.050000000000 | 0.050000000000 | 0.000000000000 | 0.050000000000 | pre_step_only_detection |
| vx_minus_0p010 | qvel_0 | -0.050000000000 | 0.050000000000 | 0.000000000000 | 0.050000000000 | pre_step_only_detection |
| vy_plus_0p010 | qvel_1 | 0.030000000000 | 0.030000000000 | 0.000000000000 | 0.030000000000 | pre_step_only_detection |
| vy_minus_0p010 | qvel_1 | -0.030000000000 | 0.030000000000 | 0.000000000000 | 0.030000000000 | pre_step_only_detection |
| yawrate_plus_0p010 | qvel_5 | 0.050000000000 | 0.050000000000 | 0.000000000000 | 0.050000000000 | pre_step_only_detection |
| yawrate_minus_0p010 | qvel_5 | -0.050000000000 | 0.050000000000 | 0.000000000000 | 0.050000000000 | pre_step_only_detection |

## 8. 当前支持的表述

Stage 24.3 支持：

    Stage 24 基于 Stage 23 trace 数据构造并分析了短时 perturbation-sensitive metrics。
    当前结果表明，qvel 扰动可在 injection / mj_forward 阶段被短时指标检测到；
    但在 aligned after_mj_step rows 中没有相对 nominal 的持续 trace separation。
    因此，Stage 22 的长期 summary 指标没有变化是合理的。

## 9. 当前不支持的表述

Stage 24.3 不支持：

  * 不支持 scale=0.010 已通过 observable perturbation robustness 验证；
  * 不支持 scale=0.010 升级为 observable-perturbation-tested recommended candidate scale；
  * 不支持完整 MPC-WBC 速度控制器已经完成；
  * 不支持 scale=0.010 可以直接用于真实机器人；
  * 不支持真实机器人 torque 执行或硬件 torque enablement 已完成；
  * 不支持复杂地形或外力冲击鲁棒性已完成。
