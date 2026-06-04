# Stage 1: ROS2 + MuJoCo Bridge

## 目标
建立最小 ROS2 与 MuJoCo 闭环通信，不引入 MPC、WBC、EKF。

## ROS2 版本
- ROS2：Jazzy
- ROS2 路径：/opt/ros/jazzy/bin/ros2
- 系统 Python：/usr/bin/python3
- Python 版本：3.12.3

## ROS2 Package
ros2_ws/src/robot_mpc_wbc_bridge

## Node
mujoco_bridge_node

## 发布 Topic
- /go1/joint_states：sensor_msgs/msg/JointState，发布 12 个关节位置、速度、力矩。
- /go1/base_state：std_msgs/msg/Float64MultiArray，发布 time、base position、quaternion、linear velocity、angular velocity。
- /go1/imu：sensor_msgs/msg/Imu，发布 orientation、angular velocity、占位 linear acceleration。
- /go1/foot_contacts：std_msgs/msg/Int32MultiArray，发布 FR、FL、RR、RL 接触状态。
- /go1/sim_time：std_msgs/msg/Float64，发布 MuJoCo 仿真时间。

## 订阅 Topic
- /go1/joint_torque_cmd：std_msgs/msg/Float64MultiArray，接收 12 维关节 torque command。

## 已验证结果
- colcon build 成功。
- bridge node 可启动。
- /go1/imu 可 echo。
- /go1/joint_states 可 echo。
- /go1/base_state 可 echo。
- /go1/foot_contacts 可 echo。
- /go1/joint_torque_cmd 可发布。
- bridge 端已打印 Received torque command: norm=0.2000。

## 运行命令
终端 1：cd ~/robot-mpc-wbc-locomotion/ros2_ws；source /opt/ros/jazzy/setup.bash；source install/setup.bash；ros2 run robot_mpc_wbc_bridge mujoco_bridge_node

终端 2：cd ~/robot-mpc-wbc-locomotion/ros2_ws；source /opt/ros/jazzy/setup.bash；source install/setup.bash；ros2 topic list；ros2 topic echo /go1/imu --once；ros2 topic echo /go1/joint_states --once；ros2 topic echo /go1/base_state --once；ros2 topic echo /go1/foot_contacts --once；ros2 topic pub --once /go1/joint_torque_cmd std_msgs/msg/Float64MultiArray "{data: [0.2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}"

## 注意
当前 bridge 不负责稳定控制。机器人倒下后 /go1/foot_contacts 可能变为 [0, 0, 0, 0]，这不是 Stage 1 失败项。稳定站立将在 Stage 3 实现。
