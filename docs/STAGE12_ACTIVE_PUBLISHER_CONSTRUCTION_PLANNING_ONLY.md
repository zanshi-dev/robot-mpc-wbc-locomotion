# Stage 12.0 Active Publisher Construction Planning Only

## 一、结论

Stage 12.0 只规划 future active publisher construction。

本阶段不修改 C++ controller 源码，不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、前置状态

Stage 11.10:

- pass: True
- verified_full_publisher_path_no_active_publisher_frozen: True
- hash_integrity_passed: True
- G8 manual_enable_active: False
- G9 active_ros_publisher_path_exists: False
- G18 full_freeze_integrity_check_passed: True
- torque_enable_ready: False

## 三、当前 source guard

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: False
- source_has_publish_call: False
- source_has_torque_topic: False
- dormant_publisher_path_source_skeleton_exists: True

## 四、Stage 12 active publisher construction plan

Plan CSV:

    results/logs_sample/stage12_active_publisher_construction_plan.csv

Stage 12.0 只记录未来策略：

- publisher topic: /go1/joint_torque_cmd；
- message type: std_msgs/msg/Float64MultiArray；
- payload length: 12；
- actuator order: FR, FL, RR, RL; each hip, thigh, calf；
- publisher construction 与 publish call 必须分离到不同阶段；
- future construction stage 仍不得调用 publish；
- publish stage 前必须再次做 source guard、runtime guard、hash check；
- manual enable、state freshness、watchdog、clamp 全部必须通过；
- 任何 hash mismatch、source guard failure、参数默认值异常、publisher count 异常都必须 abort。

## 五、Safety gate after Stage 12.0

新增：

- G19 active publisher construction planning exists: True

仍为 False：

- G8 manual enable flags active at runtime: False
- G9 active ROS publisher path exists: False

Therefore:

    torque_enable_ready = False

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.0 不是 ROS2/C++ realtime controller，不创建 publisher，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
