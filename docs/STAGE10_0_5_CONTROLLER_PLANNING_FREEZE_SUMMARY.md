# Stage 10.0–10.5 Controller Planning Freeze Summary

## 一、冻结结论

Stage 10.0–10.5 已形成 controller-planning baseline。

该 baseline 只包含：

- controller implementation plan；
- disabled-by-default C++ controller skeleton；
- state cache runtime validation；
- zero torque dry-run internal command validation；
- Python frozen baseline A/B regression；
- torque publisher enable gate design。

该 baseline 不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、Stage 10.0–10.5 汇总

| 阶段 | 测试名 | scope | pass | torque_publisher_enabled | control_law_changed |
|---|---|---|---:|---:|---:|
| Stage 10.0 | controller_implementation_plan_and_safety_gate | controller_planning_and_safety_gate_only | True | False | False |
| Stage 10.1 | disabled_cpp_controller_skeleton_check | disabled_cpp_controller_skeleton_only | True | False | False |
| Stage 10.2 | cpp_state_cache_runtime_validation | cpp_state_cache_runtime_validation_only | True | False | False |
| Stage 10.3 | zero_torque_dry_run_internal_validation | zero_torque_dry_run_internal_validation_only | True | False | False |
| Stage 10.4 | python_frozen_baseline_ab_regression | python_frozen_baseline_ab_regression_only | True | False | False |
| Stage 10.5 | torque_publisher_enable_gate_design | torque_publisher_enable_gate_design_only | True | False | False |

## 三、源码安全状态

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: False
- source_has_publish_call: False
- source_has_torque_topic: False
- zero_header_declares_12: True

## 四、Stage 10.5 safety gate 状态

- G0 Stage 8 frozen Python baseline valid: True
- G1 Stage 9 interface mirror frozen: True
- G2 C++ source has no torque publisher: True
- G3 C++ source has no publish call: True
- G4 Explicit manual enable flag design exists: True
- G5 Torque command clamp and watchdog implemented: False
- G6 Zero torque dry-run regression completed: True
- G7 Python frozen baseline A/B regression still passes: True

Therefore:

    torque_enable_ready = False

G5 仍为 False，因此不能启用 torque publisher。

## 五、冻结 hash

Hash CSV:

    results/logs_sample/stage10_0_5_controller_planning_freeze_hashes.csv

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 10.0–10.5 没有完成：

- ROS2/C++ realtime controller；
- torque publisher；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。

## 七、结论

Stage 10.0–10.5 可作为 controller-planning frozen baseline。

后续如果继续，应优先进入 clamp/watchdog utility implementation without publisher，而不是直接创建 torque publisher。
