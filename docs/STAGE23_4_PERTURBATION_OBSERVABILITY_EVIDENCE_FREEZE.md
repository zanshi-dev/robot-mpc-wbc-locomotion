# Stage 23.4：perturbation observability evidence freeze

## 1. 目标

Stage 23.4 冻结 Stage 23.0–23.3 的扰动可观测性根因审计证据。

本阶段不新增控制器，不新增 rollout，不新增真实机器人实验，只同步入口文档、生成 manifest，并冻结结论边界。

## 2. 阶段结果

| 阶段 | 结果 |
|---|---|
| 23.0 | pass |
| 23.1 | pass |
| 23.2 | pass |
| 23.3 | pass |

## 3. 核心结论

    overall_root_cause: C_summary_metrics_insensitive_to_short_horizon_trace_change
    root_cause_confidence: high

    all_nonzero_perturbations_written: True
    all_after_forward_preserved: True
    any_first_step_state_changed: True

Stage 23.3 root-cause analysis indicates that the Stage 22 qvel perturbations were injected and visible in short-horizon trace data, but the Stage 22 rollout summary metrics did not vary. The root cause is therefore summary-metric insensitivity to short-horizon initial qvel perturbations.

Stage 23 supports explaining Stage 22 negative evidence as a metric/observability limitation, not as a successful observable robustness validation.

## 4. 当前证据支持

Stage 23 支持：

  * 对 Stage 22 qvel perturbation negative evidence 进行了 root-cause audit；
  * qvel 扰动确实写入 MuJoCo `data.qvel`；
  * qvel 扰动在 `mujoco.mj_forward` 后保持；
  * qvel 扰动能在短时 trace 中产生状态差异；
  * Stage 22 summary 指标未变化的根因是 summary 指标对短时初始 qvel 扰动不敏感。

## 5. 当前证据不支持

Stage 23 不支持：

  * 不支持 `scale=0.010` 已通过 observable perturbation robustness 验证；
  * 不支持 `scale=0.010` 升级为 observable-perturbation-tested recommended candidate scale；
  * 不支持完整 MPC-WBC 速度控制器已经完成；
  * 不支持 `scale=0.010` 可以直接用于真实机器人；
  * 不支持真实机器人 torque 执行或硬件 torque enablement 已完成；
  * 不支持复杂地形或外力冲击鲁棒性已完成。

## 6. 冻结结果

    stage23_4_result: pass
    failure_count: 0
    artifact_count: 57
