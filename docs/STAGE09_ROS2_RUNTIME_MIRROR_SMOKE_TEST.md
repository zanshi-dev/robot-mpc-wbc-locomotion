# Stage 9.4 ROS2 Runtime Mirror Smoke Test

## 目标

启动 Python MuJoCo bridge 与 C++ interface mirror node，验证 C++ mirror 能看到 Stage 9.2 已冻结的 ROS2 topic contract。

## 本阶段不做的事

- 不发布 /go1/joint_torque_cmd
- 不运行 C++ controller
- 不实现 WBC / MPC / EKF
- 不改变 Stage 8 frozen Python baseline
- 不声明 pure full WBC locomotion

## 运行对象

Bridge package:

    robot_mpc_wbc_bridge

Bridge executable:

    mujoco_bridge_node

Mirror package:

    robot_mpc_wbc_cpp_interface

Mirror executable:

    go1_interface_mirror_node

## 结果

- pass: True
- stage93_pass: True
- colcon_build_returncode: 0
- topic_present_count: 6
- topic_type_match_count: 6
- published_topic_echo_success_count: 5
- torque_cmd_publisher_count: 0
- torque_cmd_subscription_count: 2

## 输出

- Log: results/logs_sample/stage09_ros2_runtime_mirror_smoke_test_log.csv
- Topic observations: results/logs_sample/stage09_ros2_runtime_mirror_topic_observations.csv
- Summary: results/logs_sample/stage09_ros2_runtime_mirror_smoke_test_summary.csv
- Bridge stdout/stderr: results/logs_sample/stage09_ros2_runtime_mirror_bridge_stdout.txt / stderr.txt
- Mirror stdout/stderr: results/logs_sample/stage09_ros2_runtime_mirror_node_stdout.txt / stderr.txt

## 边界

当前 baseline 仍是 mixed online control baseline。Stage 9.4 只是 runtime mirror smoke test，不是 ROS2/C++ realtime controller。
