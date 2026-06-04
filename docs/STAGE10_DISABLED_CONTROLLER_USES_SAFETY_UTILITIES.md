# Stage 10.8 Disabled Controller Uses Safety Utilities

## 一、目标

将 Stage 10.7 的 torque_safety utility 接入 disabled controller 内部路径。

本阶段不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、接入内容

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

已接入：

- torque_safety.hpp
- clampTorqueCommand
- allInputsFresh
- watchdogFallbackZeroTorque
- internal safe_torque_dry_run_ buffer
- input freshness timeout

## 三、运行时边界

Stage 10.8 运行 bridge 和 disabled controller，只验证：

- controller 可启动；
- safety utility contract check 仍通过；
- torque topic publisher count 仍为 0；
- controller source 无 create_publisher；
- controller source 无 publish call；
- controller source 不引用 /go1/joint_torque_cmd。

## 四、结果

- pass: True
- controller_uses_safety_utilities: True
- disabled_controller_alive_after_startup: True
- torque_topic_publishers_zero: True
- torque_enable_ready: False

## 五、Safety gate

Stage 10.8 后：

- G10 disabled controller uses clamp/watchdog internally: True
- G8 manual enable flags active at runtime: False
- G9 publisher path exists: False

因此 torque_enable_ready 仍必须为 False。

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 10.8 不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
