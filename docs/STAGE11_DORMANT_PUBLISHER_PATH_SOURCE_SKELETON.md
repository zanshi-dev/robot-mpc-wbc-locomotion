# Stage 11.5 Dormant Publisher-path Source Skeleton

## 一、结论

Stage 11.5 在 disabled controller 中加入 dormant publisher-path source skeleton。

本阶段不创建 ROS publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、前置状态

Stage 11.4:

- pass: True
- disabled_publisher_path_skeleton_preflight_passed: True
- publisher_path_implemented: False
- manual_enable_active: False
- torque_enable_ready: False

## 三、新增 dormant skeleton

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

新增：

- kDormantPublisherPathSkeletonPresent = true
- kDormantPublisherConstructionAllowed = false
- kDormantPublishCallAllowed = false
- kDormantTorquePayloadLength = 12
- makeDormantSafeTorqueCommandMessage()
- dormantPublisherConstructAllowed()
- dormantPublishAllowed()

## 四、禁止项

Checks:

- source_has_create_publisher: False
- source_has_publish_call: False
- source_has_torque_topic: False
- torque_topic_publishers_zero: True
- manual_enable_active: False

## 五、Safety gate after Stage 11.5

新增：

- G16 dormant publisher-path source skeleton exists: True

仍为 False：

- G8 manual enable flags active at runtime: False
- G9 active ROS publisher path exists: False

Therefore:

    torque_enable_ready = False

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 11.5 不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
