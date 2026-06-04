# Stage 10.1 Disabled-by-default C++ Controller Skeleton

## 目标

创建 disabled-by-default C++ controller skeleton。

该节点只订阅状态 topic，建立 state cache，并生成内部 zero torque dry-run vector。

本阶段不创建 /go1/joint_torque_cmd publisher，不调用 publish，不改变控制律。

## Package

    ros2_ws/src/robot_mpc_wbc_cpp_controller

## Node

    go1_disabled_controller_node

## 订阅 topic

- /go1/joint_states
- /go1/base_state
- /go1/imu
- /go1/foot_contacts
- /go1/sim_time

## 明确禁止

本阶段源码不得包含：

- /go1/joint_torque_cmd
- create_publisher
- publish call

## 结果

- pass: True
- subscription_found_count: 5
- source_references_torque_cmd_topic: False
- source_has_create_publisher: False
- source_has_publish_call: False
- zero_torque_dry_run_vector_declared: True
- colcon_build_returncode: 0

## 输出

- Log: results/logs_sample/stage10_disabled_cpp_controller_skeleton_check_log.csv
- Summary: results/logs_sample/stage10_disabled_cpp_controller_skeleton_check_summary.csv
- Build stdout: results/logs_sample/stage10_disabled_cpp_controller_skeleton_build_stdout.txt
- Build stderr: results/logs_sample/stage10_disabled_cpp_controller_skeleton_build_stderr.txt

## 边界

当前 baseline 仍是 mixed online control baseline。

本阶段不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
