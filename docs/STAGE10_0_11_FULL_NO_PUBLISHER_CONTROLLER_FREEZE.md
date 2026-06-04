# Stage 10.0–10.11 Full No-publisher Controller Baseline Freeze

## 一、冻结结论

Stage 10.0–10.11 已形成 full no-publisher controller baseline。

该 baseline 包含：

- controller implementation plan；
- disabled-by-default C++ controller skeleton；
- state cache runtime validation；
- zero torque dry-run command；
- Python frozen baseline A/B regression；
- torque publisher enable gate design；
- clamp/watchdog utilities；
- disabled controller 内部接入 safety utilities；
- manual enable parameters，默认 false；
- manual-enable parameter guard freeze。

该 baseline 不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、Stage 10.0–10.11 汇总

| 阶段 | 测试名 | scope | pass | torque_publisher_enabled | control_law_changed |
|---|---|---|---:|---:|---:|
| Stage 10.0 | controller_implementation_plan_and_safety_gate | controller_planning_and_safety_gate_only | True | False | False |
| Stage 10.1 | disabled_cpp_controller_skeleton_check | disabled_cpp_controller_skeleton_only | True | False | False |
| Stage 10.2 | cpp_state_cache_runtime_validation | cpp_state_cache_runtime_validation_only | True | False | False |
| Stage 10.3 | zero_torque_dry_run_internal_validation | zero_torque_dry_run_internal_validation_only | True | False | False |
| Stage 10.4 | python_frozen_baseline_ab_regression | python_frozen_baseline_ab_regression_only | True | False | False |
| Stage 10.5 | torque_publisher_enable_gate_design | torque_publisher_enable_gate_design_only | True | False | False |
| Stage 10.6 | stage10_0_5_controller_planning_freeze_summary | controller_planning_freeze_summary_only | True | False | False |
| Stage 10.7 | clamp_watchdog_utility_without_publisher | clamp_watchdog_utility_without_publisher_only | True | False | False |
| Stage 10.8 | disabled_controller_uses_safety_utilities | disabled_controller_uses_safety_utilities_without_publisher_only | True | False | False |
| Stage 10.9 | stage10_7_8_safety_utility_freeze_summary | safety_utility_freeze_summary_only | True | False | False |
| Stage 10.10 | manual_enable_params_disabled_without_publisher | manual_enable_params_disabled_without_publisher_only | True | False | False |
| Stage 10.11 | manual_enable_param_guard_freeze_summary | manual_enable_param_guard_freeze_summary_only | True | False | False |

## 三、最终源码安全状态

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: False
- source_has_publish_call: False
- source_has_torque_topic: False
- source_declares_enable_param_default_false: True
- source_declares_confirm_param_default_false: True
- source_reads_enable_param: True
- source_reads_confirm_param: True
- source_uses_safety_utilities: True

## 四、最终 safety gate

- G0 Stage 8 frozen Python baseline valid: True
- G1 Stage 9 interface mirror frozen: True
- G2 C++ controller source has no torque publisher: True
- G3 C++ controller source has no publish call: True
- G4 Explicit manual enable flag design exists: True
- G5 Torque clamp and watchdog utility implemented: True
- G6 Zero torque dry-run regression completed: True
- G7 Python frozen baseline A/B regression still passes: True
- G8 Manual enable flags active at runtime: False
- G9 Publisher path exists: False
- G10 Disabled controller uses clamp/watchdog internally: True
- G11 Manual enable parameters exist and default false: True

Therefore:

    torque_enable_ready = False

G8 与 G9 仍为 False，因此不能发布 torque。

## 五、冻结 hash

Hash CSV:

    results/logs_sample/stage10_0_11_full_no_publisher_controller_freeze_hashes.csv

## 六、明确边界

当前 baseline 仍是 mixed online control baseline。

Stage 10.0–10.11 没有完成：

- ROS2/C++ realtime controller；
- torque publisher；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- base velocity tracking；
- hardware deployment。

## 七、结论

Stage 10.0–10.11 可作为 full no-publisher controller frozen baseline。

如后续继续，下一阶段应单独设计 publisher path skeleton，并默认 disabled；不得直接启用 torque publish。
