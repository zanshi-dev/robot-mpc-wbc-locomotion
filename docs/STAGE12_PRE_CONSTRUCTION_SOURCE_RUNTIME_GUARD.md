# Stage 12.1 Pre-construction Source and Runtime Guard

## 一、结论

Stage 12.1 完成 active publisher construction 前的 source/runtime guard。

本阶段不修改 C++ controller 源码，不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、前置状态

Stage 12.0:

- pass: True
- active_publisher_construction_planning_complete: True
- active_ros_publisher_path_exists: False
- manual_enable_active: False
- torque_enable_ready: False

## 三、Source guard

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: False
- source_has_publish_call: False
- source_has_torque_topic: False
- dormant_publisher_path_source_skeleton_exists: True

## 四、Runtime guard

Runtime samples:

- runtime_expected_sample_count: 6
- runtime_observed_sample_count: 6
- topic_info_all_returncode_zero: True
- torque_publishers_zero_all_samples: True
- torque_subscribers_positive_all_samples: True
- enable_param_default_false: True
- confirm_param_default_false: True

Observation CSV:

    results/logs_sample/stage12_pre_construction_topic_observations.csv

## 五、Safety gate after Stage 12.1

新增：

- G20 pre-construction source and runtime guard passed: True

仍为 False：

- G8 manual enable flags active at runtime: False
- G9 active ROS publisher path exists: False

Therefore:

    torque_enable_ready = False

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.1 不是 ROS2/C++ realtime controller，不创建 publisher，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
