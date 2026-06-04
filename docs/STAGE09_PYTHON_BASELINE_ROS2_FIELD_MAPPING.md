# Stage 9.2 Python frozen baseline ↔ ROS2 topic field mapping table

## 目标

建立 Stage 8 frozen Python baseline 与 ROS2 bridge topic 字段之间的映射表。

本阶段只生成接口映射表，不写 controller，不改变控制律。

## 前置条件

- Stage 9.1 pass: `True`
- Stage 8 adapter exists: `True`
- Stage 8 entrypoint exists: `True`
- bridge source exists: `True`

## 字段映射表

| direction | topic | ROS type | field | expected shape / length | type match |
|---|---|---|---|---|---:|
| publish | `/go1/joint_states` | `sensor_msgs/msg/JointState` | `name` | `12` | True |
| publish | `/go1/joint_states` | `sensor_msgs/msg/JointState` | `position` | `12` | True |
| publish | `/go1/joint_states` | `sensor_msgs/msg/JointState` | `velocity` | `12` | True |
| publish | `/go1/joint_states` | `sensor_msgs/msg/JointState` | `effort` | `12` | True |
| publish | `/go1/base_state` | `std_msgs/msg/Float64MultiArray` | `data` | `implementation-defined Float64MultiArray; must be documented before C++ mirror` | True |
| publish | `/go1/imu` | `sensor_msgs/msg/Imu` | `orientation` | `geometry_msgs/Quaternion` | True |
| publish | `/go1/imu` | `sensor_msgs/msg/Imu` | `angular_velocity` | `Vector3` | True |
| publish | `/go1/imu` | `sensor_msgs/msg/Imu` | `linear_acceleration` | `Vector3` | True |
| publish | `/go1/foot_contacts` | `std_msgs/msg/Int32MultiArray` | `data` | `4` | True |
| publish | `/go1/sim_time` | `std_msgs/msg/Float64` | `data` | `1` | True |
| subscribe | `/go1/joint_torque_cmd` | `std_msgs/msg/Float64MultiArray` | `data` | `12` | True |

## 关键合同

### Joint order

MuJoCo actuator / ROS torque command order:

    FR, FL, RR, RL

每条腿顺序：

    hip, thigh, calf

### Floating-base quaternion

MuJoCo free joint qpos:

    x, y, z, qw, qx, qy, qz

Pinocchio free-flyer qpos:

    x, y, z, qx, qy, qz, qw

ROS Quaternion field order:

    x, y, z, w

因此后续 C++ mirror 不能直接把 MuJoCo qpos[3:7] 当成 ROS orientation。

### Torque command

/go1/joint_torque_cmd 使用 Float64MultiArray.data，长度必须为 12，顺序必须是 MuJoCo actuator order。

## 结果

- pass: `True`
- field_mapping_rows: `11`
- all_types_match_stage91_schema: `True`

## 输出

- Log: `results/logs_sample/stage09_python_baseline_ros2_field_mapping_log.csv`
- Field map: `results/logs_sample/stage09_python_baseline_ros2_field_mapping.csv`
- Summary: `results/logs_sample/stage09_python_baseline_ros2_field_mapping_summary.csv`

## 边界

本阶段不改变控制律，不完成 ROS2/C++ real-time controller，不完成 EKF，不完成 pure full WBC locomotion。

当前 baseline 仍是 mixed online control baseline。
