# Stage 11.0 Publisher-path Skeleton Planning Only

## 一、结论

Stage 11.0 只规划未来 publisher-path skeleton。

本阶段不修改 C++ controller 源码，不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

Stage 10.12 full no-publisher controller baseline 已通过，且 torque_enable_ready 仍为 False。

## 二、前置状态

Stage 10.12:

- pass: True
- full_no_publisher_controller_frozen: True
- torque_enable_ready: False
- torque_publisher_enabled: False
- control_law_changed: False

## 三、当前源码状态

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: False
- source_has_publish_call: False
- source_has_torque_topic: False
- source_declares_enable_param_default_false: True
- source_declares_confirm_param_default_false: True
- source_uses_safety_utilities: True

## 四、Publisher-path skeleton 未来设计

未来 publisher path skeleton 不得直接启用 torque publish。它必须满足：

- publisher topic: /go1/joint_torque_cmd；
- message type: std_msgs/msg/Float64MultiArray；
- payload length: 12；
- actuator order: FR, FL, RR, RL; each leg hip, thigh, calf；
- create_publisher 只能出现在独立 stage 中；
- publish call 只能在更晚 stage 中出现；
- 两个 manual enable 参数必须均为 true；
- state_ready 与 inputs_fresh 必须为 true；
- command 必须通过 watchdog fallback 与 clampTorqueCommand；
- first runtime policy 必须保持 disabled。

Stage 11.0 不实现上述 publisher path，只记录设计。

## 五、Safety gate after Stage 11.0

Safety gate CSV:

    results/logs_sample/stage11_torque_publisher_safety_gate_after_stage110.csv

新增：

- G12 publisher path skeleton plan exists: True

仍为 False：

- G8 manual enable flags active at runtime: False
- G9 publisher path exists: False

Therefore:

    torque_enable_ready = False

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 11.0 不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
