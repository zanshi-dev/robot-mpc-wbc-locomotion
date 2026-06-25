# Stage 24.4：short-horizon metric evidence freeze

## 1. 目标

Stage 24.4 冻结 Stage 24.0–24.3 的短时扰动敏感指标审计证据。

本阶段不新增控制器，不新增 rollout，不新增真实机器人实验，只同步入口文档、生成 manifest，并冻结结论边界。

## 2. 阶段结果

| 阶段 | 结果 |
|---|---|
| 24.0 | pass |
| 24.1 | pass |
| 24.2 | pass |
| 24.3 | pass |

## 3. 核心结论

    metric_observability_class: pre_step_only_detection_no_post_step_trace_separation
    metric_audit_result: partial_detection

    any_pre_step_trace_separation_detected: True
    all_pre_step_trace_separation_detected: True
    any_post_step_trace_separation_detected: False
    any_early_window_trace_separation_detected: True
    all_early_window_trace_separation_detected: True

    max_pre_step_qvel_axis_diff_vs_nominal: 0.050000000000
    max_post_step_state_delta: 0.000000000000
    max_early_window_state_delta: 0.050000000000
    mean_early_window_state_delta: 0.001604938272

Stage 24.3 shows that short-horizon perturbation-sensitive metrics detect the injected qvel perturbations only in the pre-step / mj_forward trace segment. The aligned after_mj_step rows are not separated from nominal. This refines the Stage 23 root cause: Stage 22 summary metrics were insensitive because the perturbation signature was visible at injection time but did not persist into the rollout-step trace.

Stage 24 supports adding explicit injection-stage or pre-step trace metrics for future perturbation audits. It does not support observable robustness or a scale=0.010 recommendation upgrade.

## 4. 当前证据支持

Stage 24 支持：

  * 构造并分析短时 perturbation-sensitive metrics；
  * qvel 扰动在 injection / mj_forward 阶段可被短时指标检测到；
  * aligned after_mj_step rows 中没有相对 nominal 的持续 trace separation；
  * Stage 22 的长期 summary 指标没有变化是合理的；
  * 后续扰动审计应加入 injection-stage 或 pre-step trace metrics。

## 5. 当前证据不支持

Stage 24 不支持：

  * 不支持 `scale=0.010` 已通过 observable perturbation robustness 验证；
  * 不支持 `scale=0.010` 升级为 observable-perturbation-tested recommended candidate scale；
  * 不支持完整 MPC-WBC 速度控制器已经完成；
  * 不支持 `scale=0.010` 可以直接用于真实机器人；
  * 不支持真实机器人 torque 执行或硬件 torque enablement 已完成；
  * 不支持复杂地形或外力冲击鲁棒性已完成。

## 6. 冻结结果

    stage24_4_result: pass
    failure_count: 0
