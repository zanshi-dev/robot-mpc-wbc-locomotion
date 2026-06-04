# Stage 9.3 ROS2/C++ Interface Mirror Skeleton

## 目标

创建一个 C++ ROS2 interface mirror skeleton，用于镜像 Stage 9.2 已记录的 ROS2 topic schema。

本阶段只创建空壳接口节点，不写控制器，不发布 torque command，不改变控制律。

## Package

    ros2_ws/src/robot_mpc_wbc_cpp_interface

## Node

    go1_interface_mirror_node

## 订阅 topic

- /go1/joint_states
- /go1/base_state
- /go1/imu
- /go1/foot_contacts
- /go1/sim_time
- /go1/joint_torque_cmd

## 安全边界

该节点不创建 /go1/joint_torque_cmd publisher。

该节点不调用 publish。

该节点不实现 WBC、MPC、EKF 或 torque controller。

## 编译结果

- colcon_build_returncode: 0
- pass: True

## 输出

- Log: results/logs_sample/stage09_ros2_cpp_interface_mirror_skeleton_check_log.csv
- Summary: results/logs_sample/stage09_ros2_cpp_interface_mirror_skeleton_check_summary.csv
- Build stdout: results/logs_sample/stage09_ros2_cpp_interface_mirror_skeleton_build_stdout.txt
- Build stderr: results/logs_sample/stage09_ros2_cpp_interface_mirror_skeleton_build_stderr.txt

## 运行方式

先 source ROS2 与 workspace：

    source /opt/ros/jazzy/setup.bash
    source ros2_ws/install/setup.bash

运行节点：

    ros2 run robot_mpc_wbc_cpp_interface go1_interface_mirror_node

或使用 launch：

    ros2 launch robot_mpc_wbc_cpp_interface interface_mirror.launch.py

## 边界

当前 baseline 仍是 mixed online control baseline。

本阶段不完成 ROS2/C++ real-time controller，不完成 pure WBC locomotion，不完成 EKF，不完成 full 3D centroidal MPC。
