# Stage 10.5 Torque Publisher Enable Gate Design

## 一、结论

Stage 10.5 只设计 torque publisher enable gate。

本阶段不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

Stage 10.5 后，manual enable flag 设计存在，因此 G4 可设为 True。

但 clamp/watchdog 仍未实现，因此 G5 必须保持 False，torque_enable_ready 必须保持 False。

## 二、未来 enable 参数设计

未来允许创建 torque publisher 之前，必须至少包含两个独立手动参数：

- enable_torque_publisher
- confirm_torque_publisher_enable

默认值必须全部为 false。

只有两个参数都为 true，且所有 safety gate 都通过，才允许进入 publisher creation 路径。

Stage 10.5 不实现这两个参数，只记录设计。

## 三、未来 publisher 设计约束

未来 publisher topic:

    /go1/joint_torque_cmd

消息类型:

    std_msgs/msg/Float64MultiArray

数据长度:

    12

顺序:

    MuJoCo actuator order FR, FL, RR, RL; each leg hip, thigh, calf

## 四、clamp 设计

未来 torque command 在任何 publish 之前必须经过：

- 长度检查：必须为 12；
- finite 检查：拒绝 NaN 和 Inf；
- per-joint absolute torque clamp；
- clamp 后再次 finite 检查；
- clamp 结果写入 debug log；
- clamp 限值必须显式写在文档和 summary 中。

Stage 10.5 不实现 clamp。

## 五、watchdog 设计

未来 watchdog 必须检查：

- joint state freshness；
- base state freshness；
- imu freshness；
- foot contact freshness；
- sim time freshness；
- controller loop freshness。

任一状态超时，内部 command 必须退回 zero torque dry-run vector。

Stage 10.5 不实现 watchdog。

## 六、当前源码安全状态

Source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: False
- source_has_publish_call: False
- source_has_torque_topic: False

## 七、Stage 10.5 后 safety gate

Safety gate CSV:

    results/logs_sample/stage10_torque_publisher_safety_gate_after_stage105.csv

Expected status:

- G0: True
- G1: True
- G2: True
- G3: True
- G4: True
- G5: False
- G6: True
- G7: True

Therefore:

    torque_enable_ready = False

## 八、禁止事项

Stage 10.5 禁止：

- 创建 /go1/joint_torque_cmd publisher；
- 引入 create_publisher；
- 引入 publish call；
- 引用 /go1/joint_torque_cmd 到 controller source；
- 改变控制律；
- 声称 ROS2/C++ realtime controller completed。

## 九、输出

- Design CSV: results/logs_sample/stage10_torque_publisher_enable_gate_design.csv
- Safety gate CSV: results/logs_sample/stage10_torque_publisher_safety_gate_after_stage105.csv
- Summary: results/logs_sample/stage10_torque_publisher_enable_gate_design_summary.csv
- Log: results/logs_sample/stage10_torque_publisher_enable_gate_design_log.csv

## 十、边界

当前 baseline 仍是 mixed online control baseline。

Stage 10.5 不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
