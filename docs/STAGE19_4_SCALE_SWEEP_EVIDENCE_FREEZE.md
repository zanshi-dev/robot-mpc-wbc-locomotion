# Stage 19.4：速度感知 scale sweep 证据冻结

## 1. 目标

Stage 19.4 将 Stage 19.0–19.3 的速度感知 scale sweep 证据同步到入口文档，并生成冻结证据包。

本阶段不新增控制器，只做证据归档、入口文档同步和结论边界冻结。

## 2. 冻结阶段结果

| 阶段 | 结果 |
|---|---|
| 19.0 | pass |
| 19.1 | pass |
| 19.2 | pass |
| 19.3 | pass |

## 3. 关键结论

当前 sweep 中所有 scale 均通过稳定性和安全边界；速度误差随 scale 变化呈非单调特征。在已测试 candidate scale 中，scale=0.010 的 mean_abs_velocity_error 最低，相对 baseline 的 delta_error=-0.013229，可作为当前更合理的低尺度 candidate 注入候选。scale=0.020 出现明显速度退化，不建议作为速度跟踪默认注入强度。

## 4. 当前证据支持

Stage 19 证据支持以下表述：

    Stage 19 完成了 simulation-only velocity-aware scale sweep。在当前 target_vx=0.2 m/s 测试中，所有 scale 均通过稳定性和安全边界；candidate scale 对速度跟踪影响呈非单调特征；scale=0.010 是当前更合理的低尺度 candidate 注入候选，scale=0.020 不适合作为速度跟踪默认注入强度。

## 5. 当前证据不支持

Stage 19.4 不支持以下表述：

  * 已完成完整 MPC-WBC 速度控制器；
  * MPC/WBC candidate 已全面优于 baseline；
  * 已完成真实机器人 torque 执行；
  * 已完成硬件 torque enablement；
  * 当前 scale 结论可直接迁移到真实机器人或复杂地形。

## 6. 生成证据文件

    results/logs_sample/stage19_4_scale_sweep_evidence_freeze_validation.csv
    results/logs_sample/stage19_4_scale_sweep_evidence_hashes.csv
    results/logs_sample/stage19_4_scale_sweep_evidence_manifest.json
    results/logs_sample/stage19_4_scale_sweep_evidence_freeze_summary.json
    docs/STAGE19_4_SCALE_SWEEP_EVIDENCE_FREEZE.md

## 7. 冻结结果

    stage19_4_result: pass
    failure_count: 0
    artifact_count: 39
