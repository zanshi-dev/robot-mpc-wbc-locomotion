# Stage 24：短时扰动敏感指标审计路线图

## 1. 背景

Stage 22 尝试通过 qvel 初始速度扰动构造 observable perturbation audit，但结果为：

    observable_perturbation_pass=False
    perturbation_metric_variability_detected=False
    recommendation_relation_stable=True
    recommendation_observable_robust=False

Stage 23 对该负向证据进行了 root-cause audit，结论为：

    overall_root_cause=C_summary_metrics_insensitive_to_short_horizon_trace_change
    root_cause_confidence=high
    all_nonzero_perturbations_written=True
    all_after_forward_preserved=True
    any_first_step_state_changed=True

这说明：

  * qvel 扰动确实写入 MuJoCo data.qvel；
  * 扰动在 mujoco.mj_forward 后保持；
  * 扰动能在短时 trace 中产生状态差异；
  * 但 Stage 22 的长期 summary 指标没有变化；
  * 根因是 Stage 22 summary 指标对短时初始 qvel 扰动不敏感。

Stage 24 的目标是基于 Stage 23 的 trace 数据，构造和验证一组更适合短时扰动诊断的 perturbation-sensitive metrics。

## 2. Stage 24 核心问题

Stage 24 要回答：

    哪些短时指标能捕捉 qvel 初始扰动？
    qvel/qpos/base finite-difference velocity 在前若干步是否相对 nominal 出现可量化差异？
    Stage 22 的 mean_vx、mean_abs_velocity_error、forward_displacement 为什么会掩盖短时差异？
    后续如果继续做扰动审计，应该补哪些 summary 指标？

## 3. Stage 24 不做的事情

Stage 24 不做：

  * 不新增控制器；
  * 不修改 torque 执行链路；
  * 不重新声明 observable perturbation robustness；
  * 不做真实机器人部署；
  * 不做硬件 torque enablement；
  * 不做复杂地形；
  * 不做外力冲击；
  * 不声明 scale=0.010 对所有速度、地形、扰动和外力冲击都最优；
  * 不把 Stage 24 解释为真实扰动鲁棒性验证。

## 4. Stage 24 数据来源

Stage 24 主要读取 Stage 23.2 生成的 trace 数据：

    results/logs_sample/stage23_2_qvel_injection_trace_nominal_0p010.csv
    results/logs_sample/stage23_2_qvel_injection_trace_vx_plus_0p010.csv
    results/logs_sample/stage23_2_qvel_injection_trace_vx_minus_0p010.csv
    results/logs_sample/stage23_2_qvel_injection_trace_vy_plus_0p010.csv
    results/logs_sample/stage23_2_qvel_injection_trace_vy_minus_0p010.csv
    results/logs_sample/stage23_2_qvel_injection_trace_yawrate_plus_0p010.csv
    results/logs_sample/stage23_2_qvel_injection_trace_yawrate_minus_0p010.csv

同时读取 Stage 23.3 根因分析结果：

    results/logs_sample/stage23_3_perturbation_observability_root_cause_summary.json
    results/logs_sample/stage23_3_perturbation_observability_root_cause_per_case.csv

## 5. 推荐短时指标

Stage 24 计划计算以下指标：

### 5.1 注入保持类指标

    injection_written
    after_forward_preserved
    written_delta
    after_forward_delta

这些指标说明扰动是否进入 qvel，并在 mj_forward 后保持。

### 5.2 第一步响应类指标

    first_step_qvel_delta
    qpos_delta_first_step
    first_step_base_vx_fd
    first_step_base_vy_fd

这些指标说明扰动是否在第一个 mj_step 后产生短时响应。

### 5.3 相对 nominal 的 trace 分离指标

对每个 perturbation case，与 nominal trace 对齐比较：

    max_abs_qvel_axis_diff_vs_nominal
    mean_abs_qvel_axis_diff_vs_nominal
    max_abs_qpos_axis_diff_vs_nominal
    mean_abs_qpos_axis_diff_vs_nominal
    max_abs_base_vx_fd_diff_vs_nominal
    max_abs_base_vy_fd_diff_vs_nominal

### 5.4 early-window 综合指标

在前 12 个 mj_step 中统计：

    early_window_trace_separation_detected
    early_window_max_abs_state_delta
    early_window_mean_abs_state_delta

## 6. Stage 24 判断逻辑

Stage 24 可能出现两种主要结果：

### 情况 A：短时指标能检测扰动

如果相对 nominal 的 early-window 指标出现非零差异，则结论应写为：

    Stage 24 shows that short-horizon perturbation-sensitive metrics can capture the qvel perturbation effect that Stage 22 long-horizon summary metrics missed.

这支持“指标体系改进”，但不支持“鲁棒性验证成功”。

### 情况 B：短时指标也不能检测扰动

如果短时指标仍无法区分 perturbation 与 nominal，则说明 Stage 23 的 first-step trace 判断还不够充分，可能需要更细粒度 trace 或更直接的 MuJoCo state inspection。

此时不能继续做鲁棒性声明。

## 7. Stage 24 输出文件

Stage 24.0 输出：

    docs/STAGE24_SHORT_HORIZON_PERTURBATION_METRIC_ROADMAP.md
    scripts/stage24_0_validate_short_horizon_metric_roadmap.py
    results/logs_sample/stage24_0_short_horizon_metric_roadmap_validation.csv
    results/logs_sample/stage24_0_short_horizon_metric_roadmap_summary.json

后续阶段计划输出：

    docs/STAGE24_1_SHORT_HORIZON_METRIC_PREFLIGHT.md
    docs/STAGE24_2_SHORT_HORIZON_PERTURBATION_METRICS.md
    docs/STAGE24_3_SHORT_HORIZON_METRIC_ANALYSIS.md
    docs/STAGE24_4_SHORT_HORIZON_METRIC_EVIDENCE_FREEZE.md

## 8. Stage 24 可以支持的表述

Stage 24 通过后，最多支持：

    Stage 24 基于 Stage 23 trace 数据构造了短时 perturbation-sensitive metrics。
    这些指标用于解释和补充 Stage 22 长期 summary 指标对短时 qvel 初始扰动不敏感的问题。

## 9. Stage 24 不支持的表述

Stage 24 不支持：

  * scale=0.010 已通过 observable perturbation robustness 验证；
  * scale=0.010 已升级为 observable-perturbation-tested recommended candidate scale；
  * 完整 MPC-WBC 速度控制器已经完成；
  * scale=0.010 可以直接用于真实机器人；
  * 真实机器人 torque 执行已经完成；
  * 硬件 torque enablement 已经完成；
  * 复杂地形或外力冲击鲁棒性已经完成。

## 10. Stage 24.4 证据冻结说明

Stage 24.4 将同步 README、PROJECT_STATUS、ARTIFACT_INDEX，并冻结 Stage 24 的短时扰动敏感指标审计证据。

Stage 24.4 只做证据归档和结论边界冻结，不新增控制器、不新增真实机器人实验、不重新声明 observable perturbation robustness。
