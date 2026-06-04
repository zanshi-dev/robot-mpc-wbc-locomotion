# Stage 10.10 Manual Enable Parameters Disabled Without Publisher

## 一、目标

给 disabled controller 增加 manual enable parameters，并确认默认值为 false。

本阶段不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、新增参数

Node:

    go1_disabled_controller_node

Parameters:

    enable_torque_publisher = false
    confirm_torque_publisher_enable = false

两个参数都必须默认为 false。

Stage 10.10 不会把参数设为 true。

## 三、源码安全状态

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: False
- source_has_publish_call: False
- source_has_torque_topic: False
- manual_enable_params_declared: True
- manual_enable_params_default_false: True

## 四、Runtime 检查

- enable_param_listed: True
- confirm_param_listed: True
- enable_param_default_false: True
- confirm_param_default_false: True
- torque_topic_publishers_zero: True

## 五、Safety gate

Stage 10.10 后新增：

- G11 manual enable parameters exist and default false: True

但以下仍为 False：

- G8 manual enable flags active at runtime: False
- G9 publisher path exists: False

Therefore:

    torque_enable_ready = False

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 10.10 不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
