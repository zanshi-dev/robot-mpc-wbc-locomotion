# Stage 25.4：primary_mpc_wbc smoke failure diagnosis

## 1. 目标

Stage 25.4 对 Stage 25.3 的 primary_mpc_wbc smoke rollout 负向结果进行诊断。

本阶段不新增控制器，不新增 rollout，只分析已有 Stage 25.3 log / summary。

## 2. 结果

Stage 25.4 result: pass

Failure count: 0

failure_class:

    posture_limit_violation_with_torque_saturation_no_qp_failure

## 3. 关键诊断指标

| 指标 | 数值 |
|---|---:|
| primary_mpc_wbc_executed | True |
| smoke_stability_pass | False |
| first_roll_exceed_step | 140 |
| first_pitch_exceed_step | 575 |
| first_z_exceed_step | None |
| first_saturation_step | 200 |
| max_abs_roll | 0.488712369676 |
| max_abs_pitch | 0.356235143697 |
| min_z | 0.238243397800 |
| qp_fail_steps | 0 |
| saturation_steps | 555 |
| max_tau_candidate_abs | 19.442509447300 |
| max_tau_primary_mpc_wbc_raw_abs | 75.856574627963 |
| max_tau_total_abs | 23.700000000000 |

## 4. 诊断结论

Stage 25.3 的 primary_mpc_wbc 模式确实进入了 simulation-only MuJoCo torque loop，但未通过稳定性边界。

当前 failure class 为：

    posture_limit_violation_with_torque_saturation_no_qp_failure

这说明主要问题不是 QP/WBC 求解失败，而是直接 primary torque 组合后出现姿态超限和 torque saturation。

## 5. 下一阶段建议

Stage 25.5 应实现 stabilized primary_mpc_wbc variant，候选修正包括：

  * primary torque ramp；
  * primary torque scale；
  * stance posture residual；
  * saturation-aware fallback；
  * 更保守的 swing PD 或 swing target scale。

## 6. 当前支持的表述

Stage 25.4 支持：

    primary_mpc_wbc 已实际执行；
    直接主控模式当前不稳定；
    失败主要表现为 posture limit violation + torque saturation；
    当前不是 QP failure 主导；
    下一步需要稳定化 primary controller，而不是继续声明稳定闭环成功。

## 7. 当前不支持的表述

Stage 25.4 不支持：

  * 不支持 primary_mpc_wbc 已稳定闭环运行；
  * 不支持真实机器人闭环；
  * 不支持 hardware torque enablement；
  * 不支持复杂地形或外力冲击鲁棒性。
