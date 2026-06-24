# Stage 18.4：速度跟踪证据冻结

## 1. 目标

Stage 18.4 将 Stage 18.0–18.3 的速度跟踪证据同步到入口文档，并生成冻结证据包。

本阶段不新增控制器，只做证据归档、入口文档同步和结论边界冻结。

## 2. 冻结阶段结果

| 阶段 | 结果 |
|---|---|
| 18.0 | pass |
| 18.1 | pass |
| 18.2a | pass |
| 18.2 | pass |
| 18.3 | pass |

## 3. 关键结论

Stage 18.2 的低尺度 MPC/WBC candidate 注入工况保持稳定，但不改善速度跟踪。在 target_vx=0.2 m/s 的当前测试中，baseline 的 mean_vx 更高、mean_abs_velocity_error 更低、forward_displacement 更大。

## 4. 当前证据支持

Stage 18 证据支持以下表述：

    Stage 18 补齐了 simulation-only velocity evidence。在当前 target_vx=0.2 m/s 测试中，baseline 与低尺度 MPC/WBC candidate 注入均通过稳定性和安全边界，但 baseline 速度跟踪优于 candidate。

## 5. 当前证据不支持

Stage 18.4 不支持以下表述：

  * 低尺度 MPC/WBC candidate 改善速度跟踪；
  * 已完成完整 MPC-WBC 速度控制器；
  * 已完成真实机器人 torque 执行；
  * 已完成硬件 torque enablement；
  * MPC/WBC 全面优于 baseline。

## 6. 生成证据文件

    results/logs_sample/stage18_4_velocity_evidence_freeze_validation.csv
    results/logs_sample/stage18_4_velocity_evidence_hashes.csv
    results/logs_sample/stage18_4_velocity_evidence_manifest.json
    results/logs_sample/stage18_4_velocity_evidence_freeze_summary.json
    docs/STAGE18_4_VELOCITY_EVIDENCE_FREEZE.md

## 7. 冻结结果

    stage18_4_result: pass
    failure_count: 0
    artifact_count: 35
