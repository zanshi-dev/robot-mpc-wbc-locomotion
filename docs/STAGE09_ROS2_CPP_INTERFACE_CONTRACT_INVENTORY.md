# Stage 9.0 ROS2/C++ Interface Contract Inventory

## 目标

Stage 9 从 ROS2/C++ interface mirror 开始，不直接写实时控制器，不改变控制律。

本阶段只盘点当前 ROS2 workspace、bridge package、topic contract，以及 Stage 8 frozen Python baseline 与 ROS2 topic 的对应关系。

## Stage 8 frozen baseline

推荐入口：

    /usr/bin/python3 scripts/stage08_adapter_backed_stage07_recommended_test.py

Runtime adapter:

    scripts/common/go1_runtime_interface.py

Stage 8 freeze pass: `True`

Control law changed: `False`

## ROS2 workspace

- ros2_ws_exists: `True`
- ros2_src_exists: `True`
- ros2_command_available: `True`
- colcon_command_available: `True`

## ROS2 packages

| package | path | setup.py | CMakeLists.txt | launch_files | python_files | cpp_files |
|---|---|---:|---:|---:|---:|---:|
| robot_mpc_wbc_bridge | ros2_ws/src/robot_mpc_wbc_bridge | True | False | 1 | 7 | 0 |

## Expected bridge topic contract

| direction | topic | found_in_source | hit_count | Python baseline signal |
|---|---|---:|---:|---|
| publish | `/go1/joint_states` | True | 1 | joint_states |
| publish | `/go1/base_state` | True | 1 | base_state |
| publish | `/go1/imu` | True | 1 | imu |
| publish | `/go1/foot_contacts` | True | 1 | foot_contacts |
| publish | `/go1/sim_time` | True | 1 | sim_time |
| subscribe | `/go1/joint_torque_cmd` | True | 1 | joint_torque_cmd |

## 结果

- pass: `True`
- bridge_package_found: `True`
- all_expected_topics_found: `True`
- publish_topic_found_count: `5`
- subscribe_topic_found_count: `1`

## 输出

- Log: `results/logs_sample/stage09_ros2_cpp_interface_contract_inventory_log.csv`
- Topic map: `results/logs_sample/stage09_ros2_cpp_interface_topic_contract_map.csv`
- Summary: `results/logs_sample/stage09_ros2_cpp_interface_contract_inventory_summary.csv`

## 边界

本阶段不改变控制律，不完成 ROS2/C++ real-time controller，不完成 EKF，不完成 pure full WBC locomotion。

当前 baseline 仍是 mixed online control baseline。
