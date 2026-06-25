# Stage 24.2：short-horizon perturbation-sensitive metrics

## 1. 目标

Stage 24.2 基于 Stage 23.2 的 qvel injection trace 数据，计算短时扰动敏感指标。

本阶段不新增 rollout，不新增控制器，只计算 metrics。

## 2. 结果

Stage 24.2 result: pass

Failure count: 0

Case count: 7

Non-nominal case count: 6

any_pre_step_trace_separation_detected: True

all_pre_step_trace_separation_detected: True

any_post_step_trace_separation_detected: False

any_early_window_trace_separation_detected: True

all_early_window_trace_separation_detected: True

max_early_window_max_abs_state_delta: 0.050000000000

mean_early_window_mean_abs_state_delta: 0.001604938272

## 3. Stage 23 根因背景

    overall_root_cause=C_summary_metrics_insensitive_to_short_horizon_trace_change
    root_cause_confidence=high

Stage 23 已确认 qvel 扰动写入、mj_forward 后保持，并在短时 trace 中产生状态差异。Stage 24.2 的作用是把这种短时差异量化为 metrics。

## 4. Per-case metrics

| case_id | axis | written_delta | after_forward_delta | max_abs_pre_step_qvel_axis_diff_vs_nominal | max_abs_qvel_axis_diff_vs_nominal | max_abs_qpos_axis_diff_vs_nominal | post_step_max_abs_state_delta | early_window_max_abs_state_delta | pre_step_trace_separation_detected | post_step_trace_separation_detected | early_window_trace_separation_detected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nominal_0p010 | qvel_0 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | False | False | False |
| vx_plus_0p010 | qvel_0 | 0.050000000000 | 0.050000000000 | 0.050000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.050000000000 | True | False | True |
| vx_minus_0p010 | qvel_0 | -0.050000000000 | -0.050000000000 | 0.050000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.050000000000 | True | False | True |
| vy_plus_0p010 | qvel_1 | 0.030000000000 | 0.030000000000 | 0.030000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.030000000000 | True | False | True |
| vy_minus_0p010 | qvel_1 | -0.030000000000 | -0.030000000000 | 0.030000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.030000000000 | True | False | True |
| yawrate_plus_0p010 | qvel_5 | 0.050000000000 | 0.050000000000 | 0.050000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.050000000000 | True | False | True |
| yawrate_minus_0p010 | qvel_5 | -0.050000000000 | -0.050000000000 | 0.050000000000 | 0.000000000000 | 0.000000000000 | 0.000000000000 | 0.050000000000 | True | False | True |

## 5. Aggregate metrics

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

## 6. 当前支持的表述

Stage 24.2 支持：

    基于 Stage 23 trace 数据，已计算短时 perturbation-sensitive metrics。
    这些 metrics 可用于分析 Stage 22 长期 summary 指标为什么没有捕捉短时 qvel 初始扰动。

## 7. 当前不支持的表述

Stage 24.2 不支持：

  * 不支持 scale=0.010 已通过 observable perturbation robustness 验证；
  * 不支持 scale=0.010 升级为 observable-perturbation-tested recommended candidate scale；
  * 不支持完整 MPC-WBC 速度控制器已经完成；
  * 不支持 scale=0.010 可以直接用于真实机器人；
  * 不支持真实机器人 torque 执行或硬件 torque enablement 已完成；
  * 不支持复杂地形或外力冲击鲁棒性已完成。
