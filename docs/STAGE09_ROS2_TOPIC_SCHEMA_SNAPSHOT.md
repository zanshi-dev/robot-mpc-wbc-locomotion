# Stage 9.1 ROS2 Topic Schema Snapshot

## 目标

记录 ROS2 bridge topic 的消息类型和字段 schema。

本阶段只做 topic schema snapshot，不写 controller，不改变控制律。

## 前置条件

- Stage 9.0 pass: `True`
- bridge package found: `True`

## Topic schema map

| direction | topic | ROS type | schema available | field count | baseline signal |
|---|---|---|---:|---:|---|
| publish | `/go1/joint_states` | `sensor_msgs/msg/JointState` | True | 9 | `joint_state_feedback` |
| publish | `/go1/base_state` | `std_msgs/msg/Float64MultiArray` | True | 7 | `floating_base_state` |
| publish | `/go1/imu` | `sensor_msgs/msg/Imu` | True | 21 | `imu_feedback` |
| publish | `/go1/foot_contacts` | `std_msgs/msg/Int32MultiArray` | True | 7 | `contact_state_feedback` |
| publish | `/go1/sim_time` | `std_msgs/msg/Float64` | True | 1 | `simulation_time` |
| subscribe | `/go1/joint_torque_cmd` | `std_msgs/msg/Float64MultiArray` | True | 7 | `joint_torque_command` |

## 结果

- pass: `True`
- expected_topic_count: `6`
- topic_found_count: `6`
- topic_type_inferred_count: `6`
- topic_schema_available_count: `6`
- all_expected_topics_found: `True`
- all_topic_types_inferred: `True`
- all_topic_schemas_available: `True`

## 输出

- Log: `results/logs_sample/stage09_ros2_topic_schema_snapshot_log.csv`
- Schema map: `results/logs_sample/stage09_ros2_topic_schema_snapshot_map.csv`
- Schema dir: `results/logs_sample/stage09_topic_schemas/`
- Summary: `results/logs_sample/stage09_ros2_topic_schema_snapshot_summary.csv`

## 边界

本阶段不改变控制律，不完成 ROS2/C++ real-time controller，不完成 EKF，不完成 pure full WBC locomotion。

当前 baseline 仍是 mixed online control baseline。
