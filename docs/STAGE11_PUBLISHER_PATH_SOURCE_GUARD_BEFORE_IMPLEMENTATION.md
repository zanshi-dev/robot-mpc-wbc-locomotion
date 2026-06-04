# Stage 11.1 Publisher-path Source Guard Before Implementation

## 一、结论

Stage 11.1 是 publisher-path implementation 前的 source/runtime guard。

本阶段不修改 C++ controller 源码，不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、前置状态

Stage 11.0:

- pass: True
- publisher_path_plan_exists: True
- publisher_path_implemented: False
- torque_enable_ready: False

## 三、源码 guard

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: False
- source_has_publish_call: False
- source_has_torque_topic: False
- source_declares_enable_param_default_false: True
- source_declares_confirm_param_default_false: True
- source_uses_safety_utilities: True

## 四、Runtime guard

Runtime checks:

- disabled_controller_alive_after_startup: True
- enable_param_default_false: True
- confirm_param_default_false: True
- torque_topic_publishers_zero: True
- torque_topic_subscribers_positive: True

## 五、Safety gate after Stage 11.1

新增：

- G13 publisher-path source guard passed before implementation: True

仍为 False：

- G8 manual enable flags active at runtime: False
- G9 publisher path exists: False

Therefore:

    torque_enable_ready = False

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 11.1 不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
