# Stage 11.4 Disabled Publisher-path Skeleton Preflight

## 一、结论

Stage 11.4 只做 disabled publisher-path skeleton preflight。

本阶段不修改 C++ controller 源码，不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、前置状态

Stage 11.3:

- pass: True
- publisher_path_planning_frozen: True
- torque_enable_ready: False
- torque_publisher_enabled: False
- control_law_changed: False

## 三、当前源码状态

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: False
- source_has_publish_call: False
- source_has_torque_topic: False
- source_unchanged_by_stage114: True

## 四、Preflight 约束

Stage 11.4 决定：后续 skeleton implementation 仍不得直接创建 ROS publisher。

后续允许的只是 dormant source skeleton，例如：

- inactive helper method；
- nullptr member；
- compile-time placeholder；
- no create_publisher；
- no publish call；
- controller source 仍不直接包含 /go1/joint_torque_cmd；
- runtime publisher count 仍必须为 0。

## 五、Safety gate after Stage 11.4

新增：

- G15 disabled publisher-path skeleton preflight passed: True

仍为 False：

- G8 manual enable flags active at runtime: False
- G9 publisher path exists: False

Therefore:

    torque_enable_ready = False

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 11.4 不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
