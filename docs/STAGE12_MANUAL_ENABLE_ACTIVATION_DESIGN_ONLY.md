# Stage 12.6 Manual Enable Activation Design Only

## 一、结论

Stage 12.6 只设计 future manual enable activation protocol。

本阶段不设置 runtime params 为 true，不修改 C++ source，不添加 publish call，不发布 torque，不改变控制律。

## 二、前置状态

Stage 12.5:

- pass: True
- publisher_construction_no_publish_integrity_passed: True
- current_source_has_create_publisher: True
- current_source_has_publish_call: False
- active_ros_publisher_path_exists: True
- manual_enable_active: False
- torque_enable_ready: False

## 三、当前 source guard

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: True
- source_has_publish_call: False
- source_references_torque_topic: True
- source_has_active_publisher_member: True
- source_unchanged_by_stage126: True

## 四、Manual enable activation design

Design CSV:

    results/logs_sample/stage12_manual_enable_activation_design.csv

Future activation protocol:

- set enable_torque_publisher true；
- set confirm_torque_publisher_enable true；
- no C++ source change；
- no publish call；
- runtime observations required；
- fail-closed revert procedure required；
- abort on source hash change, publish call, param failure, unexpected topic count, or controller exit。

## 五、Safety gate after Stage 12.6

新增：

- G24 manual enable activation design exists: True

仍为 False：

- G8 manual enable flags active at runtime: False

保持 True：

- G9 active ROS publisher path exists: True

Therefore:

    torque_enable_ready = False

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.6 没有完成：

- manual enable activation；
- publish call；
- torque command publishing；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。
