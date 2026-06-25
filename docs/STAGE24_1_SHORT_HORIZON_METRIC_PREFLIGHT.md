# Stage 24.1：short-horizon metric design preflight

## 1. 目标

Stage 24.1 检查 Stage 23.2 的 qvel injection trace 数据是否足够支持 Stage 24.2 计算短时扰动敏感指标。

本阶段不新增 rollout，不新增控制器，只做数据字段检查和指标设计。

## 2. 结果

Stage 24.1 result: pass

Failure count: 0

Trace case count: 7

Metric design count: 15

All trace inputs ready for Stage 24.2: True

## 3. Stage 23 根因背景

    overall_root_cause=C_summary_metrics_insensitive_to_short_horizon_trace_change
    root_cause_confidence=high
    stage23_2_all_nonzero_perturbations_written=True
    stage23_2_all_after_forward_preserved=True
    stage23_2_any_first_step_state_changed=True

## 4. Trace 输入计划

| case_id | axis | qpos_axis | trace_csv | ready_for_stage24_2 |
|---|---|---|---|---|
| nominal_0p010 | qvel_0 | qpos_0 | `results/logs_sample/stage23_2_qvel_injection_trace_nominal_0p010.csv` | True |
| vx_plus_0p010 | qvel_0 | qpos_0 | `results/logs_sample/stage23_2_qvel_injection_trace_vx_plus_0p010.csv` | True |
| vx_minus_0p010 | qvel_0 | qpos_0 | `results/logs_sample/stage23_2_qvel_injection_trace_vx_minus_0p010.csv` | True |
| vy_plus_0p010 | qvel_1 | qpos_1 | `results/logs_sample/stage23_2_qvel_injection_trace_vy_plus_0p010.csv` | True |
| vy_minus_0p010 | qvel_1 | qpos_1 | `results/logs_sample/stage23_2_qvel_injection_trace_vy_minus_0p010.csv` | True |
| yawrate_plus_0p010 | qvel_5 | qpos_3 | `results/logs_sample/stage23_2_qvel_injection_trace_yawrate_plus_0p010.csv` | True |
| yawrate_minus_0p010 | qvel_5 | qpos_3 | `results/logs_sample/stage23_2_qvel_injection_trace_yawrate_minus_0p010.csv` | True |

## 5. 指标设计

| metric_name | metric_group | expected_use |
|---|---|---|
| injection_written | injection_preservation | confirm perturbation injection validity |
| after_forward_preserved | injection_preservation | confirm simulation-state synchronization did not erase injection |
| written_delta | injection_preservation | quantify qvel injection magnitude |
| after_forward_delta | injection_preservation | quantify preserved qvel delta |
| first_step_qvel_delta | first_step_response | measure immediate qvel response |
| qpos_delta_first_step | first_step_response | measure immediate position response |
| max_abs_qvel_axis_diff_vs_nominal | trace_separation_vs_nominal | detect perturbation-sensitive qvel trace separation |
| mean_abs_qvel_axis_diff_vs_nominal | trace_separation_vs_nominal | detect average qvel trace separation |
| max_abs_qpos_axis_diff_vs_nominal | trace_separation_vs_nominal | detect perturbation-sensitive qpos trace separation |
| mean_abs_qpos_axis_diff_vs_nominal | trace_separation_vs_nominal | detect average qpos trace separation |
| max_abs_base_vx_fd_diff_vs_nominal | trace_separation_vs_nominal | detect finite-difference velocity separation |
| max_abs_base_vy_fd_diff_vs_nominal | trace_separation_vs_nominal | detect lateral finite-difference velocity separation |
| early_window_max_abs_state_delta | early_window_state_delta | single scalar for short-horizon perturbation observability |
| early_window_mean_abs_state_delta | early_window_state_delta | average scalar for short-horizon perturbation observability |
| early_window_trace_separation_detected | early_window_state_delta | decide whether short-horizon metrics detect perturbation |

## 6. Stage 24.2 计算要求

Stage 24.2 应：

  * 读取 nominal trace 和 6 个 perturbation trace；
  * 按 `trace_step_index` 对齐 `after_mj_step` 行；
  * 计算 qvel/qpos/base finite-difference velocity 相对 nominal 的短时差异；
  * 输出 per-case metric table；
  * 输出 aggregate metric summary；
  * 判断 `early_window_trace_separation_detected` 是否为 True。

## 7. 结论边界

Stage 24.1 只是 metric design preflight，不声明 observable perturbation robustness，不声明完整 MPC-WBC 速度控制器完成，不涉及真实机器人和硬件 torque enablement。
