# Stage 8.0–8.7 Runtime Interface Hardening 中文汇总

## 一、Stage 8 当前结论

Stage 8.0–8.7 已完成 runtime interface hardening 的第一轮闭环。

当前推荐运行入口：

    /usr/bin/python3 scripts/stage08_adapter_backed_stage07_recommended_test.py

该入口会先执行 runtime adapter preflight，再运行 Stage 7 recommended mixed online control baseline。

当前控制器仍是 mixed online control baseline，不是 pure full WBC locomotion。

控制结构：

1. stance legs 使用 posture PD；
2. stance legs 叠加 scaled stance WBC feedforward；
3. swing legs 使用 online swing target PD；
4. WBC torque 不直接作用 swing legs；
5. swing PD 不直接作用 stance legs。

## 二、Stage 8.0–8.7 阶段记录

| 阶段 | 名称 | 主要目标 | 结果 |
|---|---|---|---|
| Stage 8.0 | runtime interface contract check | 验证 MuJoCo / Pinocchio 维度、关节顺序、quaternion、qpos/qvel/torque round-trip | 通过 |
| Stage 8.1 | runtime adapter module check | 将映射逻辑抽成 scripts/common/go1_runtime_interface.py | 通过 |
| Stage 8.2 | zero-control regression guard | 在不改控制律前提下重跑 Stage 7 baseline，确认 adapter 不破坏结果 | 通过 |
| Stage 8.3 | adapter-backed Stage 7 A/B test | 比较原 Stage 7 入口与 adapter-backed 入口 | 通过 |
| Stage 8.4 | runtime mapping duplication audit | 扫描仓库内重复映射代码 | 通过 |
| Stage 8.5 | audit triage | 区分 active dependency path 与 legacy scripts | 通过 |
| Stage 8.6 | active-path leg order refactor | 清除 active path 中 high-severity hard-coded leg order | 通过 |
| Stage 8.7 | recommended runtime-safe entrypoint promotion | 固化 Stage 8 推荐 runtime-safe 入口 | 通过 |

## 三、核心输出文件

### Stage 8.0

- Script: scripts/stage08_runtime_interface_contract_check.py
- Log: results/logs_sample/stage08_runtime_interface_contract_check_log.csv
- Summary: results/logs_sample/stage08_runtime_interface_contract_check_summary.csv
- Docs: docs/STAGE08_RUNTIME_INTERFACE_CONTRACT_CHECK.md

### Stage 8.1

- Module: scripts/common/go1_runtime_interface.py
- Script: scripts/stage08_runtime_interface_adapter_module_check.py
- Log: results/logs_sample/stage08_runtime_interface_adapter_module_check_log.csv
- Summary: results/logs_sample/stage08_runtime_interface_adapter_module_check_summary.csv
- Docs: docs/STAGE08_RUNTIME_INTERFACE_ADAPTER_MODULE_CHECK.md

### Stage 8.2

- Script: scripts/stage08_adapter_zero_control_regression_guard.py
- Log: results/logs_sample/stage08_adapter_zero_control_regression_guard_log.csv
- Summary: results/logs_sample/stage08_adapter_zero_control_regression_guard_summary.csv
- Docs: docs/STAGE08_ADAPTER_ZERO_CONTROL_REGRESSION_GUARD.md

### Stage 8.3

- Script: scripts/stage08_adapter_backed_stage07_baseline_ab_test.py
- Adapter-backed entrypoint: scripts/stage08_adapter_backed_stage07_recommended_test.py
- Log: results/logs_sample/stage08_adapter_backed_stage07_baseline_ab_test_log.csv
- Summary: results/logs_sample/stage08_adapter_backed_stage07_baseline_ab_test_summary.csv
- Docs: docs/STAGE08_ADAPTER_BACKED_STAGE07_BASELINE_AB_TEST.md

### Stage 8.4

- Script: scripts/stage08_runtime_mapping_duplication_audit.py
- Log: results/logs_sample/stage08_runtime_mapping_duplication_audit_log.csv
- Summary: results/logs_sample/stage08_runtime_mapping_duplication_audit_summary.csv
- Docs: docs/STAGE08_RUNTIME_MAPPING_DUPLICATION_AUDIT.md

### Stage 8.5

- Script: scripts/stage08_runtime_mapping_audit_triage.py
- Log: results/logs_sample/stage08_runtime_mapping_audit_triage_log.csv
- Summary: results/logs_sample/stage08_runtime_mapping_audit_triage_summary.csv
- Docs: docs/STAGE08_RUNTIME_MAPPING_AUDIT_TRIAGE.md

### Stage 8.6

- Script: scripts/stage08_active_leg_order_refactor_and_regression.py
- Log: results/logs_sample/stage08_active_leg_order_refactor_and_regression_log.csv
- Summary: results/logs_sample/stage08_active_leg_order_refactor_and_regression_summary.csv
- Docs: docs/STAGE08_ACTIVE_LEG_ORDER_REFACTOR_AND_REGRESSION.md

### Stage 8.7

- Recommended entrypoint: scripts/stage08_adapter_backed_stage07_recommended_test.py
- Summary: results/logs_sample/stage08_recommended_runtime_safe_entrypoint_promotion_summary.csv
- Stdout: results/logs_sample/stage08_recommended_runtime_safe_entrypoint_stdout.txt
- Stderr: results/logs_sample/stage08_recommended_runtime_safe_entrypoint_stderr.txt
- Docs: docs/STAGE08_RECOMMENDED_RUNTIME_SAFE_ENTRYPOINT.md

## 四、关键数值结论

Stage 8.0 / 8.1 adapter round-trip：

- qpos_roundtrip_max_abs = 0.0
- qvel_roundtrip_max_abs = 0.0
- torque_roundtrip_max_abs = 0.0

Stage 8.3 A/B regression：

- original_pass = True
- adapter_pass = True
- original_pass_margin = True
- adapter_pass_margin = True
- original_max_tau_total_abs = adapter_max_tau_total_abs
- original_min_z = adapter_min_z
- original_max_abs_roll = adapter_max_abs_roll
- original_max_abs_pitch = adapter_max_abs_pitch
- original_qp_fail_steps = adapter_qp_fail_steps
- original_saturation_steps = adapter_saturation_steps

Stage 8.6 refactor 后：

- active_high_severity_findings_after_refactor = 0
- rerun_stage83_ab_pass = True
- num_failed_checks = 0

Stage 8.7 推荐入口：

- recommended_entrypoint_returncode = 0
- adapter_preflight_stdout_pass = True
- pass = True

## 五、当前 runtime adapter 合同

统一模块：

    scripts/common/go1_runtime_interface.py

核心合同：

- MuJoCo qpos/qvel/actuator leg order: FR, FL, RR, RL
- Pinocchio actuated joint order: FL, FR, RL, RR
- MuJoCo free joint quaternion: x, y, z, qw, qx, qy, qz
- Pinocchio free-flyer quaternion: x, y, z, qx, qy, qz, qw
- qpos / qvel / torque 映射必须通过 adapter 或与 adapter 对齐
- 后续不应在 active controller path 中继续散落 hard-coded reorder 逻辑

## 六、明确边界

Stage 8.0–8.7 没有完成以下内容：

1. pure full WBC locomotion；
2. WBC QP 内部直接接入 online swing target task；
3. swing target 到 acceleration reference 的在线转换；
4. touchdown / liftoff contact feedback；
5. base velocity tracking；
6. forward velocity command；
7. 完整 3D centroidal MPC；
8. EKF 状态估计；
9. ROS2/C++ real-time controller；
10. OSQP warm-start 与实时周期约束；
11. 硬件部署或真实机器人验证。

## 七、后续建议

下一阶段建议进入 Stage 8.8+ 后续路线之一：

1. runtime adapter API cleanup；
2. 将 adapter-backed entrypoint 纳入推荐 README / PROJECT_STATUS；
3. 继续重构 active low/medium findings，但只在确认不是 false positive 后执行；
4. 开始 ROS2/C++ 迁移前，先生成 Python baseline freeze；
5. 若进入 ROS2/C++，先做接口 mirror，不改控制律。

## 八、最终表述

正确表述：

Stage 8.0–8.7 已完成 Python runtime interface hardening，并固化了 runtime-safe 推荐入口。当前 baseline 仍是通过 MuJoCo closed-loop test 的 mixed online control baseline，其中 WBC 作为 stance legs feedforward，stance 稳定性主要由 posture PD 保证，swing motion 由 online swing target PD 保证。

错误表述：

Stage 8 已完成 pure WBC locomotion。

