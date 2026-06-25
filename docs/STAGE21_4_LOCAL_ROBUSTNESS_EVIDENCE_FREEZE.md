# Stage 21.4：局部扰动鲁棒性证据冻结

## 1. 目标

Stage 21.4 将 Stage 21.0–21.3 的 recommended scale local robustness audit 证据同步到入口文档，并生成冻结证据包。

本阶段不新增控制器，只做证据归档、入口文档同步和结论边界冻结。

## 2. 冻结阶段结果

| 阶段 | 结果 |
|---|---|
| 21.0 | pass |
| 21.1 | pass |
| 21.2 | pass |
| 21.3 | pass |

## 3. 关键结论

Stage 21.3 local robustness analysis 通过。在当前 7 个小范围初始状态扰动工况下，scale=0.010 均通过稳定性边界；scale=0.010 在所有扰动工况中均保持低于 baseline 和 scale=0.020 的 mean_abs_velocity_error，且 forward_displacement 均高于 baseline 和 scale=0.020。因此，scale=0.010 可从 fixed-setting recommended candidate scale 扩展为当前仿真证据下的 local-perturbation-tested recommended candidate scale。

## 4. 扰动敏感性边界

    perturbation_metric_variability_detected: False

当前小范围初始位姿扰动下，记录的 summary 指标未出现可观测变化；因此该结果应解释为当前 runner 与扰动设置下的 local perturbation audit，而不是广义扰动鲁棒性结论。

这意味着 Stage 21 可以作为当前 runner 与当前扰动设置下的 local perturbation audit evidence，但不能扩展为广义扰动鲁棒性、复杂地形鲁棒性或外力冲击鲁棒性结论。

## 5. 当前证据支持

Stage 21 证据支持以下表述：

    Stage 21 对 Stage 20 推荐的 scale=0.010 进行了 simulation-only local perturbation robustness audit。
    在当前小范围初始状态扰动设置下，scale=0.010 均通过稳定性边界；
    scale=0.010 在所有扰动工况中保持低于 baseline 和 scale=0.020 的速度误差。
    因此，scale=0.010 可作为当前仿真证据下的 local-perturbation-tested recommended candidate scale。

## 6. 当前证据不支持

Stage 21.4 不支持以下表述：

  * 已完成完整 MPC-WBC 速度控制器；
  * scale=0.010 可以直接用于真实机器人；
  * scale=0.010 对所有速度、地形、扰动和外力冲击都最优；
  * MPC/WBC candidate 已全面优于 baseline；
  * 已完成真实机器人 torque 执行；
  * 已完成硬件 torque enablement；
  * 已完成复杂地形鲁棒性验证；
  * 已完成外力冲击鲁棒性验证。

## 7. 生成证据文件

    results/logs_sample/stage21_4_local_robustness_evidence_freeze_validation.csv
    results/logs_sample/stage21_4_local_robustness_evidence_hashes.csv
    results/logs_sample/stage21_4_local_robustness_evidence_manifest.json
    results/logs_sample/stage21_4_local_robustness_evidence_freeze_summary.json
    docs/STAGE21_4_LOCAL_ROBUSTNESS_EVIDENCE_FREEZE.md

## 8. 冻结结果

    stage21_4_result: pass
    failure_count: 0
    artifact_count: 72
    recommended_scale: 0.010
    local_robustness_pass: True
    recommendation_robust: True
    perturbation_metric_variability_detected: False
