# Stage 23：扰动可观测性根因审计路线图

## 1. 背景

Stage 22 完成了 qvel initial perturbation attempt，结果为：

    observable_perturbation_pass=False
    perturbation_metric_variability_detected=False
    recommendation_relation_stable=True
    recommendation_observable_robust=False

这说明：

  * 21 组 qvel 初始速度扰动 rollout 均通过稳定性边界；
  * scale=0.010 的推荐关系在当前记录指标中未被破坏；
  * 但是 qvel 初始速度扰动没有造成 summary 指标可观测变化；
  * 因此 Stage 22 不能支持 observable perturbation robustness 结论。

Stage 23 的目标不是继续证明 scale=0.010 更鲁棒，而是解释 Stage 22 为什么没有产生可观测扰动效果。

## 2. Stage 23 核心问题

Stage 23 要回答：

    qvel 扰动是否真的写入了 MuJoCo data.qvel？
    写入后 mujoco.mj_forward 是否保持了扰动状态？
    rollout 第 0 步、第 1 步、前若干步中，qvel/qpos/base_vx_fd 是否发生变化？
    扰动是否被后续 reset、状态映射、控制器初始化或仿真循环覆盖？
    当前 summary 指标不变，是因为扰动没有注入，还是因为评估指标/控制链路对该扰动不敏感？

## 3. Stage 23 不做的事情

Stage 23 不做：

  * 不新增控制器；
  * 不修改 torque 执行链路；
  * 不重新声明 observable perturbation robustness；
  * 不做真实机器人部署；
  * 不做硬件 torque enablement；
  * 不做复杂地形；
  * 不做外力冲击；
  * 不做多 target_vx 泛化测试；
  * 不声明 scale=0.010 对所有速度、地形、扰动和外力冲击都最优。

## 4. Stage 23 审计对象

Stage 23 主要审计以下文件和数据流：

    scripts/stage22_2_observable_perturbation_runner.py
    scripts/stage22_2_run_observable_perturbation_rollouts.py
    results/logs_sample/stage22_2_observable_perturbation_table.csv
    results/logs_sample/stage22_3_observable_perturbation_variability.csv
    results/logs_sample/stage22_3_observable_robustness_summary.json

重点关注：

    data.qvel 写入点
    mujoco.mj_forward 调用点
    mujoco.mj_step 前后的状态变化
    qpos[0]、qpos[1]、qvel[0]、qvel[1]、qvel[5]
    base_x、base_y、base_vx_fd、base_vy_fd
    perturb_vx、perturb_vy、perturb_yawrate
    第 0 步和前 10 步状态

## 5. Stage 23 推荐诊断实验

Stage 23.2 不需要重复完整 21 组大规模 rollout，可以先做 trace diagnostic：

    nominal
    vx_plus
    vx_minus
    yawrate_plus
    yawrate_minus

每个 case 可以先固定：

    scale=0.010
    control_mode=mpc_assisted_candidate
    target_vx=0.2

如果需要对比，也可加入：

    baseline scale=0.000
    regression anchor scale=0.020

Stage 23.2 的关键不是最终速度误差，而是 trace：

    qvel_before_injection
    qvel_after_injection
    qvel_after_mj_forward
    qvel_after_first_step
    qpos_before_injection
    qpos_after_first_step
    base_x_trace
    base_y_trace
    base_vx_fd_trace
    base_vy_fd_trace

## 6. Stage 23 判断逻辑

Stage 23 可能出现三种结果：

### 情况 A：qvel 扰动没有实际写入

如果 qvel_before 与 qvel_after 完全一致，说明 Stage 22.2 的注入代码没有真实生效。  
结论应写为：

    Stage 22 negative evidence 主要来自扰动注入未生效。

### 情况 B：qvel 扰动写入了，但第一步前后被覆盖或快速消失

如果 qvel_after_injection 有变化，但 qvel_after_first_step 或 base_vx_fd 没有变化，说明扰动可能被 reset、控制循环、状态映射或仿真步进逻辑覆盖/吸收。  
结论应写为：

    Stage 22 negative evidence 来自当前 runner 对初始 qvel 扰动不敏感或扰动被后续流程覆盖。

### 情况 C：qvel 扰动写入且短时 trace 有变化，但 summary 指标不变

如果前若干步 qvel/qpos/base_vx_fd 有变化，但 mean_vx、mean_abs_velocity_error、forward_displacement 不变，说明扰动影响过短或被长时间 summary 平均掩盖。  
结论应写为：

    Stage 22 negative evidence 来自当前 summary 指标对短时初始速度扰动不敏感。

## 7. Stage 23 输出文件

Stage 23 计划生成：

    docs/STAGE23_PERTURBATION_OBSERVABILITY_ROOT_CAUSE_ROADMAP.md
    scripts/stage23_0_validate_perturbation_observability_roadmap.py
    results/logs_sample/stage23_0_perturbation_observability_roadmap_validation.csv
    results/logs_sample/stage23_0_perturbation_observability_roadmap_summary.json

后续阶段生成：

    docs/STAGE23_1_QVEL_INJECTION_TRACE_PREFLIGHT.md
    docs/STAGE23_2_QVEL_INJECTION_TRACE_DIAGNOSTIC.md
    docs/STAGE23_3_PERTURBATION_OBSERVABILITY_ROOT_CAUSE_ANALYSIS.md
    docs/STAGE23_4_PERTURBATION_OBSERVABILITY_EVIDENCE_FREEZE.md

## 8. Stage 23 可以支持的表述

Stage 23 通过后，最多支持：

    Stage 23 对 Stage 22 的 qvel perturbation negative evidence 进行了 root-cause audit。
    该阶段解释了为什么 qvel 初始扰动没有造成 summary 指标变化。

## 9. Stage 23 不支持的表述

Stage 23 不支持：

  * scale=0.010 已通过 observable perturbation robustness 验证；
  * scale=0.010 已可直接用于真实机器人；
  * 完整 MPC-WBC 速度控制器已经完成；
  * 真实机器人 torque 执行已经完成；
  * 硬件 torque enablement 已经完成；
  * 复杂地形或外力冲击鲁棒性已经完成。

## 10. Stage 23.4 证据冻结说明

Stage 23.4 将同步 README、PROJECT_STATUS、ARTIFACT_INDEX，并冻结 Stage 23 的扰动可观测性根因审计证据。

Stage 23.4 只做证据归档和结论边界冻结，不新增控制器、不新增真实机器人实验、不重新声明 observable perturbation robustness。
