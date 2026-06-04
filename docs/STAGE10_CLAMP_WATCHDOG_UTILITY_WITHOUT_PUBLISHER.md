# Stage 10.7 Clamp/Watchdog Utility Without Publisher

## 一、目标

实现 torque clamp 与 watchdog 工具库，并完成 contract check。

本阶段不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、新增文件

- ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp
- ros2_ws/src/robot_mpc_wbc_cpp_controller/src/torque_safety_contract_check.cpp

## 三、已实现 utility

Clamp utility:

- 输入长度固定为 12；
- 非 finite 输入转换为 0；
- 每关节按 max_abs_torque clamp；
- 输出再次检查 finite；
- 记录是否发生 clamp。

Watchdog utility:

- 检查输入 age 是否 finite；
- 检查 age 是否非负；
- 检查 age 是否小于等于 timeout；
- stale 或 NaN 输入会阻断 fresh 状态；
- fallback command 为 zero torque dry-run vector。

## 四、结果

- pass: True
- clamp_watchdog_utility_implemented: True
- clamp_output_all_finite: True
- clamp_expected_values_ok: True
- watchdog_stale_blocks: True
- watchdog_nan_blocks: True
- watchdog_zero_all_zero: True
- torque_topic_publishers_zero: True

## 五、源码安全边界

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- controller_source_has_create_publisher: False
- controller_source_has_publish_call: False
- controller_source_has_torque_topic: False

## 六、Safety gate 更新

Stage 10.7 后：

- G5 torque clamp and watchdog utility implemented: True
- G8 manual enable flags active at runtime: False
- G9 publisher path exists: False

因此：

    torque_enable_ready = False

## 七、边界

当前 baseline 仍是 mixed online control baseline。

Stage 10.7 不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
