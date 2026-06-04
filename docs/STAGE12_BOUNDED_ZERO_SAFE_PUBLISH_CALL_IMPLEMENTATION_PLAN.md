# Stage 12.11 Bounded Zero/Safe Publish-call Implementation Plan

## 一、结论

Stage 12.11 只制定 bounded zero/safe publish-call implementation plan。

本阶段不修改 C++ source，不加入 publish call，不发布 torque，不改变控制律。

## 二、前置状态

Stage 12.10:

- pass: True
- publish_call_preflight_frozen: True
- current_source_has_create_publisher: True
- current_source_has_publish_call: False
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
- source_unchanged_by_stage1211: True

## 四、Bounded zero/safe publish-call implementation plan

Plan CSV:

    results/logs_sample/stage12_bounded_zero_safe_publish_call_implementation_plan.csv

Future bounded publish protocol:

- one-shot or finite bounded message count only；
- zero or watchdog-safe torque only；
- Float64MultiArray length 12；
- all values finite；
- actuator order FR, FL, RR, RL; each hip, thigh, calf；
- watchdogFallbackZeroTorque before clampTorqueCommand；
- manual flags true, active publisher exists, state_ready, inputs_fresh；
- runtime topic echo must verify message count and payload；
- params must be reverted in fail-closed cleanup；
- no control law, estimator, MPC, or WBC logic changes。

## 五、Safety gate after Stage 12.11

新增：

- G29 bounded zero/safe publish-call implementation plan exists: True

Key gates remain:

- G3 no publish call: True
- G8 manual enable active after revert: False
- G9 active ROS publisher path exists: True
- G28 publish-call preflight freeze passed: True

Therefore:

    torque_enable_ready = False

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.11 没有完成：

- publish call；
- torque command publishing；
- continuous torque streaming；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。
