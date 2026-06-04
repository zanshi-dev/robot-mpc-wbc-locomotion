# Stage 12.7 Manual Enable Runtime Activation Without Publish

## 一、结论

Stage 12.7 执行 runtime-only manual enable activation test，但不实现 publish call。

本阶段行为：

- runtime 设置 enable_torque_publisher=true；
- runtime 设置 confirm_torque_publisher_enable=true；
- 确认 active ROS publisher path 仍存在；
- 确认 C++ source 未改变；
- 确认 source 仍无 publish call；
- 用 ros2 topic echo --once 超时验证没有 torque message；
- 测试结束后 fail-closed revert 两个参数为 false。

## 二、Source guard

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: True
- source_has_publish_call: False
- source_references_torque_topic: True
- source_unchanged_by_stage127: True

## 三、Runtime manual activation

Parameter observation CSV:

    results/logs_sample/stage12_manual_enable_runtime_activation_param_observations.csv

Topic observation CSV:

    results/logs_sample/stage12_manual_enable_runtime_activation_topic_observations.csv

Results:

- initial_enable_param_false: True
- initial_confirm_param_false: True
- activated_enable_param_true: True
- activated_confirm_param_true: True
- reverted_enable_param_false: True
- reverted_confirm_param_false: True
- torque_publishers_positive_all_samples: True
- no_message_observed_during_activation: True

## 四、Safety gate after Stage 12.7

新增：

- G25 manual enable runtime activation without publish passed: True

Runtime during test:

- manual_enable_active_during_test: True
- active_ros_publisher_path_exists: True

After test:

- manual_enable_reverted_false: True
- torque_enable_ready: False
- torque_publisher_enabled: False
- torque_command_published_by_stage127: False

## 五、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.7 没有完成：

- publish call；
- torque command publishing；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。
