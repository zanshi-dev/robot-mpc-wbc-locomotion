# Stage 23.1：qvel injection trace preflight

## 1. 目标

Stage 23.1 检查 Stage 22.2 runner 是否具备派生 qvel injection trace diagnostic 的基础条件。

本阶段不运行新仿真，只做：

  * 检查 Stage 22.4 negative evidence 是否已冻结；
  * 检查 Stage 22.2 runner 中 qvel 注入、mj_forward、mj_step 和 summary 指标相关代码；
  * 输出 Stage 23.2 trace diagnostic 的 case 计划；
  * 记录潜在状态覆盖点和 trace 需求。

## 2. 结果

Stage 23.1 result: pass

Failure count: 0

## 3. Stage 22 negative evidence 背景

    observable_perturbation_pass=False
    perturbation_metric_variability_detected=False
    recommendation_relation_stable=True
    recommendation_observable_robust=False

## 4. 诊断标志

| flag | value |
|---|---:|
| contains_mj_resetData | False |
| contains_data_qvel_zero_assignment | False |
| contains_data_qpos_zero_assignment | False |
| contains_new_MjData | True |
| contains_state_reset_word | False |
| contains_qvel_trace_fields | False |

## 5. Stage 23.2 trace 计划

| trace_case_id | perturbation_id | perturb_vx | perturb_vy | perturb_yawrate | scale | trace_csv |
|---|---|---:|---:|---:|---:|---|
| nominal_0p010 | nominal | 0.000000 | 0.000000 | 0.000000 | 0.010 | `results/logs_sample/stage23_2_qvel_injection_trace_nominal_0p010.csv` |
| vx_plus_0p010 | vx_plus | 0.050000 | 0.000000 | 0.000000 | 0.010 | `results/logs_sample/stage23_2_qvel_injection_trace_vx_plus_0p010.csv` |
| vx_minus_0p010 | vx_minus | -0.050000 | 0.000000 | 0.000000 | 0.010 | `results/logs_sample/stage23_2_qvel_injection_trace_vx_minus_0p010.csv` |
| vy_plus_0p010 | vy_plus | 0.000000 | 0.030000 | 0.000000 | 0.010 | `results/logs_sample/stage23_2_qvel_injection_trace_vy_plus_0p010.csv` |
| vy_minus_0p010 | vy_minus | 0.000000 | -0.030000 | 0.000000 | 0.010 | `results/logs_sample/stage23_2_qvel_injection_trace_vy_minus_0p010.csv` |
| yawrate_plus_0p010 | yawrate_plus | 0.000000 | 0.000000 | 0.050000 | 0.010 | `results/logs_sample/stage23_2_qvel_injection_trace_yawrate_plus_0p010.csv` |
| yawrate_minus_0p010 | yawrate_minus | 0.000000 | 0.000000 | -0.050000 | 0.010 | `results/logs_sample/stage23_2_qvel_injection_trace_yawrate_minus_0p010.csv` |

## 6. Stage 23.2 必须记录的字段

Stage 23.2 应至少记录：

    qvel_before_injection
    qvel_after_injection
    qvel_after_mj_forward
    qvel_after_first_step
    qpos_before_injection
    qpos_after_first_step
    base_x
    base_y
    base_vx_fd
    base_vy_fd
    qvel_0
    qvel_1
    qvel_5
    qpos_0
    qpos_1
    qpos_2

## 7. 结论边界

Stage 23.1 只是 preflight，不新增 rollout，不声明 observable perturbation robustness，不声明完整 MPC-WBC 速度控制器完成，不涉及真实机器人和硬件 torque enablement。
