# Stage 12.12 Bounded Publish-call Source Patch Design Only

## 一、结论

Stage 12.12 只设计 bounded publish-call source patch。

本阶段不修改 C++ source，不加入 publish call，不发布 torque，不改变控制律。

## 二、前置状态

Stage 12.11:

- pass: True
- bounded_zero_safe_publish_call_implementation_plan_complete: True
- source_has_create_publisher: True
- source_has_publish_call: False
- active_ros_publisher_path_exists: True
- manual_enable_active: False
- torque_enable_ready: False

## 三、当前 source guard

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: True
- source_has_publish_call: False
- source_references_torque_topic: True
- source_has_active_publisher_member: True
- source_unchanged_by_stage1212: True

## 四、Bounded publish-call source patch design

Design CSV:

    results/logs_sample/stage12_bounded_publish_call_source_patch_design.csv

Future source patch design:

- exactly one bounded publish helper;
- exactly one publish call site inside the allowed helper;
- no timer loop and no continuous streaming;
- message helper produces length-12 Float64MultiArray;
- payload is zero or watchdog-safe torque only;
- safety chain is watchdogFallbackZeroTorque then clampTorqueCommand;
- future source diff is limited to publish-gated output path;
- no estimator, MPC, WBC, gait, or control-law changes;
- future runtime evidence must verify one bounded message, payload length, finite values, and fail-closed revert.

## 五、Safety gate after Stage 12.12

新增：

- G30 bounded publish-call source patch design exists: True

Key gates remain:

- G3 no publish call: True
- G8 manual enable active after revert: False
- G9 active ROS publisher path exists: True
- G29 bounded zero/safe publish-call implementation plan exists: True

Therefore:

    torque_enable_ready = False

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.12 没有完成：

- publish call；
- torque command publishing；
- continuous torque streaming；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。
