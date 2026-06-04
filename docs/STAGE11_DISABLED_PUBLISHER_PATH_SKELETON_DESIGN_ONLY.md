# Stage 11.2 Disabled Publisher-path Skeleton Design Only

## 一、结论

Stage 11.2 只设计 disabled publisher-path skeleton。

本阶段不修改 C++ controller 源码，不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、前置状态

Stage 11.1:

- pass: True
- publisher_path_source_guard_passed: True
- publisher_path_implemented: False
- manual_enable_active: False
- torque_enable_ready: False

## 三、当前源码状态

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: False
- source_has_publish_call: False
- source_has_torque_topic: False
- source_declares_enable_param_default_false: True
- source_declares_confirm_param_default_false: True
- source_uses_safety_utilities: True

## 四、设计内容

Design CSV:

    results/logs_sample/stage11_disabled_publisher_path_skeleton_design.csv

设计但不实现：

- future publisher handle: torque_cmd_publisher_
- future topic: /go1/joint_torque_cmd
- future message type: std_msgs/msg/Float64MultiArray
- future construct gate: publisher_construct_allowed
- future publish gate: publish_allowed
- future payload: safe_torque_command_msg
- future runtime guard: publisher_count_guard

## 五、Safety gate after Stage 11.2

新增：

- G14 disabled publisher-path skeleton design exists: True

仍为 False：

- G8 manual enable flags active at runtime: False
- G9 publisher path exists: False

Therefore:

    torque_enable_ready = False

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 11.2 不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
