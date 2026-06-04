# Stage 12.2 Publisher Construction Source Patch Design Only

## 一、结论

Stage 12.2 只设计 future publisher construction source patch。

本阶段不修改 C++ controller 源码，不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、前置状态

Stage 12.1:

- pass: True
- pre_construction_source_runtime_guard_passed: True
- torque_publishers_zero_all_samples: True
- G20 pre-construction source/runtime guard passed: True
- manual_enable_active: False
- active_ros_publisher_path_exists: False
- torque_enable_ready: False

## 三、当前 source guard

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: False
- source_has_publish_call: False
- source_has_torque_topic: False
- dormant_publisher_path_source_skeleton_exists: True
- source_unchanged_by_stage122: True

## 四、Source patch design

Design CSV:

    results/logs_sample/stage12_publisher_construction_source_patch_design.csv

Stage 12.2 只设计未来 source patch：

- future publisher member；
- future /go1/joint_torque_cmd topic；
- future create_publisher call；
- construction stage 与 publish stage 分离；
- construction stage 仍禁止 publish call；
- future runtime recheck；
- fail-closed abort policy。

## 五、Safety gate after Stage 12.2

新增：

- G21 publisher construction source patch design exists: True

仍为 False：

- G8 manual enable flags active at runtime: False
- G9 active ROS publisher path exists: False

Therefore:

    torque_enable_ready = False

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.2 不是 ROS2/C++ realtime controller，不创建 publisher，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
