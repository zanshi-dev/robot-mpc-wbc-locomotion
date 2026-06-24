# Stage 20.4：推荐 scale 可复现性证据冻结

## 1. 目标

Stage 20.4 将 Stage 20.0–20.3 的 recommended scale reproducibility audit 证据同步到入口文档，并生成冻结证据包。

本阶段不新增控制器，只做证据归档、入口文档同步和结论边界冻结。

## 2. 冻结阶段结果

| 阶段 | 结果 |
|---|---|
| 20.0 | pass |
| 20.1 | pass |
| 20.2 | pass |
| 20.3 | pass |

## 3. 关键结论

Stage 20.3 replay reproducibility audit 通过。在当前固定 simulation-only 设置下，baseline、scale=0.010 和 scale=0.020 的三次 replay 结果完全一致；scale=0.010 在每次 replay 中均保持低于 baseline 和 scale=0.020 的 mean_abs_velocity_error，且 forward_displacement 均高于 baseline 和 scale=0.020。因此，Stage 19 的 scale=0.010 推荐关系在 Stage 20 replay audit 中稳定复现。

## 4. 当前证据支持

Stage 20 证据支持以下表述：

    Stage 20 对 Stage 19 推荐的 scale=0.010 进行了 simulation-only replay reproducibility audit。
    在当前固定仿真设置下，baseline、scale=0.010 和 scale=0.020 的三次 replay 结果完全一致；
    scale=0.010 相对 baseline 和 scale=0.020 的速度误差优势关系稳定复现。
    因此，scale=0.010 可作为当前仿真证据下的 recommended candidate scale。

## 5. 当前证据不支持

Stage 20.4 不支持以下表述：

  * 已完成完整 MPC-WBC 速度控制器；
  * scale=0.010 可以直接用于真实机器人；
  * scale=0.010 对所有速度、地形和扰动都最优；
  * MPC/WBC candidate 已全面优于 baseline；
  * 已完成真实机器人 torque 执行；
  * 已完成硬件 torque enablement；
  * 已完成多 target_vx 或复杂地形泛化验证。

## 6. 生成证据文件

    results/logs_sample/stage20_4_reproducibility_evidence_freeze_validation.csv
    results/logs_sample/stage20_4_reproducibility_evidence_hashes.csv
    results/logs_sample/stage20_4_reproducibility_evidence_manifest.json
    results/logs_sample/stage20_4_reproducibility_evidence_freeze_summary.json
    docs/STAGE20_4_REPRODUCIBILITY_EVIDENCE_FREEZE.md

## 7. 冻结结果

    stage20_4_result: pass
    failure_count: 0
    artifact_count: 48
    recommended_scale: 0.010
    reproducibility_pass: True
    recommendation_stable: True
