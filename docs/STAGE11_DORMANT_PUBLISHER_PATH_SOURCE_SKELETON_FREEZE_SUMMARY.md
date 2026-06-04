# Stage 11.6 Dormant Publisher-path Source Skeleton Freeze Summary

## 一、冻结结论

Stage 11.5 dormant publisher-path source skeleton 已冻结。

该 baseline 包含：

- Stage 11.3 publisher-path planning freeze；
- Stage 11.4 disabled publisher-path skeleton preflight；
- Stage 11.5 dormant publisher-path source skeleton；
- disabled controller 中的 dormant skeleton marker；
- construct forbidden marker；
- publish forbidden marker；
- 12-length dormant payload helper。

该 baseline 不创建 ROS torque publisher，不调用 publish，不引用 /go1/joint_torque_cmd，不发布 torque，不改变控制律。

## 二、Stage 11.3–11.5 汇总

| 阶段 | 测试名 | scope | pass | torque_publisher_enabled | control_law_changed |
|---|---|---|---:|---:|---:|
| Stage 11.3 | stage11_0_2_publisher_path_planning_freeze_summary | publisher_path_planning_freeze_summary_only | True | False | False |
| Stage 11.4 | disabled_publisher_path_skeleton_preflight | disabled_publisher_path_skeleton_preflight_only | True | False | False |
| Stage 11.5 | dormant_publisher_path_source_skeleton | dormant_publisher_path_source_skeleton_without_ros_publisher_construction | True | False | False |

## 三、源码安全状态

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: False
- source_has_publish_call: False
- source_has_torque_topic: False
- source_has_dormant_skeleton_marker: True
- source_has_construct_forbidden_marker: True
- source_has_publish_forbidden_marker: True
- source_has_payload_length_12: True
- source_has_dormant_payload_helper: True

## 四、Safety gate after Stage 11.5

- G8 manual enable flags active at runtime: False
- G9 active ROS publisher path exists: False
- G15 disabled publisher-path skeleton preflight passed: True
- G16 dormant publisher-path source skeleton exists: True

Therefore:

    torque_enable_ready = False

G8 与 G9 仍为 False，因此不能发布 torque。

## 五、冻结 hash

Hash CSV:

    results/logs_sample/stage11_dormant_publisher_path_source_skeleton_freeze_hashes.csv

## 六、明确边界

当前 baseline 仍是 mixed online control baseline。

Stage 11.6 没有完成：

- ROS torque publisher construction；
- /go1/joint_torque_cmd publisher；
- publish call；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。

## 七、结论

Stage 11.5 可作为 dormant publisher-path source skeleton frozen baseline。

后续如果继续，下一阶段只能做 runtime guard hardening；不得直接引入 create_publisher 或 publish call。
