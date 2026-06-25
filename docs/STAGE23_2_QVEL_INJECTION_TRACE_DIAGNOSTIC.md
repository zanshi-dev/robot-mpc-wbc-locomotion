# Stage 23.2：qvel injection trace diagnostic

## 1. 目标

Stage 23.2 记录 qvel 初始速度扰动在 MuJoCo data 中的短时 trace，用于解释 Stage 22 中 summary 指标没有出现可观测变化的原因。

本阶段记录：

  * before_injection；
  * after_injection；
  * after_mj_forward；
  * 前 12 个 mj_step 后的 qpos/qvel/base finite-difference velocity。

## 2. 结果

Stage 23.2 result: pass

Failure count: 0

Trace case count: 7

all_nonzero_perturbations_written: True

all_after_forward_preserved: True

any_first_step_state_changed: True

## 3. Trace diagnostic table

| trace_case_id | axis | expected_delta | written_delta | after_forward_delta | first_step_qvel_delta | qpos_delta_first_step | injection_written | after_forward_preserved | first_step_state_changed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nominal_0p010 | qvel_0 | 0.000000000000 | 0.000000000000 | 0.000000000000 | -0.016621033634 | -0.000033242067 | True | True | True |
| vx_plus_0p010 | qvel_0 | 0.050000000000 | 0.050000000000 | 0.050000000000 | -0.016621033634 | -0.000033242067 | True | True | True |
| vx_minus_0p010 | qvel_0 | -0.050000000000 | -0.050000000000 | -0.050000000000 | -0.016621033634 | -0.000033242067 | True | True | True |
| vy_plus_0p010 | qvel_1 | 0.030000000000 | 0.030000000000 | 0.030000000000 | 0.000213879716 | 0.000000427759 | True | True | True |
| vy_minus_0p010 | qvel_1 | -0.030000000000 | -0.030000000000 | -0.030000000000 | 0.000213879716 | 0.000000427759 | True | True | True |
| yawrate_plus_0p010 | qvel_5 | 0.050000000000 | 0.050000000000 | 0.050000000000 | -0.031726322323 | -0.000000022225 | True | True | True |
| yawrate_minus_0p010 | qvel_5 | -0.050000000000 | -0.050000000000 | -0.050000000000 | -0.031726322323 | -0.000000022225 | True | True | True |

## 4. 初步解释

Stage 23.2 只给出 trace 诊断数据，不直接给最终根因结论。

根因结论将在 Stage 23.3 中基于以下逻辑判断：

  * 如果 `all_nonzero_perturbations_written=False`，说明 qvel 扰动未真实写入；
  * 如果 `all_nonzero_perturbations_written=True` 但 `all_after_forward_preserved=False`，说明扰动在 mj_forward 后未保持；
  * 如果扰动写入并保持，但 `any_first_step_state_changed=False`，说明当前扰动未影响短时仿真状态；
  * 如果短时状态发生变化但 Stage 22 summary 不变，说明当前 summary 指标对短时 qvel 初始扰动不敏感。

## 5. 结论边界

Stage 23.2 不声明 observable perturbation robustness，不声明完整 MPC-WBC 速度控制器完成，不涉及真实机器人和硬件 torque enablement。
