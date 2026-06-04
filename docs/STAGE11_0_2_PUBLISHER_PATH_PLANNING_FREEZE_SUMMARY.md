# Stage 11.0–11.2 Publisher-path Planning Freeze Summary

## 一、冻结结论

Stage 11.0–11.2 已形成 publisher-path planning frozen baseline。

该 baseline 只包含：

- publisher-path skeleton planning；
- implementation 前 source/runtime guard；
- disabled publisher-path skeleton design。

该 baseline 不修改 C++ controller 源码，不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、Stage 11.0–11.2 汇总

| 阶段 | 测试名 | scope | pass | torque_publisher_enabled | control_law_changed |
|---|---|---|---:|---:|---:|
| Stage 11.0 | publisher_path_skeleton_planning_only | publisher_path_skeleton_planning_only | True | False | False |
| Stage 11.1 | publisher_path_source_guard_before_implementation | publisher_path_source_guard_before_implementation_only | True | False | False |
| Stage 11.2 | disabled_publisher_path_skeleton_design_only | disabled_publisher_path_skeleton_design_only | True | False | False |

## 三、最终源码安全状态

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: False
- source_has_publish_call: False
- source_has_torque_topic: False
- source_declares_enable_param_default_false: True
- source_declares_confirm_param_default_false: True
- source_uses_safety_utilities: True

## 四、最终 safety gate

- G8 manual enable flags active at runtime: False
- G9 publisher path exists: False
- G12 publisher path skeleton plan exists: True
- G13 publisher-path source guard passed before implementation: True
- G14 disabled publisher-path skeleton design exists: True

Therefore:

    torque_enable_ready = False

G8 与 G9 仍为 False，因此不能发布 torque。

## 五、冻结 hash

Hash CSV:

    results/logs_sample/stage11_0_2_publisher_path_planning_freeze_hashes.csv

## 六、明确边界

当前 baseline 仍是 mixed online control baseline。

Stage 11.0–11.2 没有完成：

- /go1/joint_torque_cmd publisher；
- publish call；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。

## 七、结论

Stage 11.0–11.2 可作为 publisher-path planning frozen baseline。

后续如果继续，下一阶段才可考虑 disabled publisher skeleton implementation，但仍不得调用 publish。
