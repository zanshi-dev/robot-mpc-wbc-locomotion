# Stage 12.9 Publish-call Design Only

## 一、结论

Stage 12.9 只设计 future publish-call implementation protocol。

本阶段不修改 C++ source，不加入 publish call，不发布 torque，不改变控制律。

## 二、前置状态

Stage 12.8:

- pass: True
- manual_enable_no_publish_frozen: True
- current_source_has_create_publisher: True
- current_source_has_publish_call: False
- active_ros_publisher_path_exists: True
- no_message_observed_during_activation: True
- torque_enable_ready: False

## 三、当前 source guard

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: True
- source_has_publish_call: False
- source_references_torque_topic: True
- source_has_active_publisher_member: True
- source_unchanged_by_stage129: True

## 四、Publish-call design

Design CSV:

    results/logs_sample/stage12_publish_call_design.csv

Future publish-call protocol:

- publish call site: active_torque_cmd_publisher_->publish(safe_torque_msg)
- preconditions: manual flags true, active publisher exists, state_ready, inputs_fresh
- payload: Float64MultiArray length 12, all finite, Go1 actuator order FR, FL, RR, RL
- safety chain: watchdogFallbackZeroTorque before clampTorqueCommand
- first publish policy: zero/safe bounded dry-run only
- no control law change
- runtime observation and fail-closed revert required

## 五、Safety gate after Stage 12.9

新增：

- G27 publish-call design exists: True

Key gates remain:

- G3 no publish call: True
- G8 manual enable active after revert: False
- G9 active ROS publisher path exists: True
- G26 manual-enable no-publish freeze passed: True

Therefore:

    torque_enable_ready = False

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.9 没有完成：

- publish call；
- torque command publishing；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。
