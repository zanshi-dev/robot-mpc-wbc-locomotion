# Stage 9.5 C++ Mirror Contract Report

## 一、结论

Stage 9.0–9.4 已完成 ROS2/C++ interface mirror 的第一轮闭环。

当前成果是 interface mirror，不是实时控制器。

本阶段没有改变控制律，没有发布 torque command，没有完成 pure full WBC locomotion。

## 二、当前 C++ mirror package

Package:

    ros2_ws/src/robot_mpc_wbc_cpp_interface

Node:

    go1_interface_mirror_node

Launch:

    ros2_ws/src/robot_mpc_wbc_cpp_interface/launch/interface_mirror.launch.py

## 三、推荐运行方式

先 source 环境：

    source /opt/ros/jazzy/setup.bash
    source ros2_ws/install/setup.bash

运行 MuJoCo bridge：

    ros2 run robot_mpc_wbc_bridge mujoco_bridge_node

另一个终端运行 C++ mirror：

    ros2 run robot_mpc_wbc_cpp_interface go1_interface_mirror_node

或：

    ros2 launch robot_mpc_wbc_cpp_interface interface_mirror.launch.py

## 四、Stage 9.0–9.4 汇总

| 阶段 | 测试名 | scope | pass | control_law_changed |
|---|---|---|---:|---:|
| Stage 9.0 | ros2_cpp_interface_contract_inventory | interface_inventory_only | True | False |
| Stage 9.1 | ros2_topic_schema_snapshot | topic_schema_snapshot_only | True | False |
| Stage 9.2 | python_baseline_ros2_field_mapping | field_mapping_table_only | True | False |
| Stage 9.3 | ros2_cpp_interface_mirror_skeleton_check | cpp_interface_mirror_skeleton_only | True | False |
| Stage 9.4 | ros2_runtime_mirror_smoke_test | runtime_mirror_smoke_test_only | True | False |

## 五、已确认 topic contract

Stage 9.0–9.4 已确认：

- /go1/joint_states
- /go1/base_state
- /go1/imu
- /go1/foot_contacts
- /go1/sim_time
- /go1/joint_torque_cmd

关键 runtime smoke test 结果：

- topic_present_count: 6
- topic_type_match_count: 6
- published_topic_echo_success_count: 5
- torque_cmd_publisher_count: 0
- torque_cmd_subscription_count: 2

## 六、关键安全边界

C++ mirror node 当前只订阅 topic。

它不创建 /go1/joint_torque_cmd publisher。

它不调用 publish。

它不运行 MPC、WBC、EKF 或任何 torque controller。

## 七、当前 baseline 边界

当前 baseline 仍是 mixed online control baseline。

它不是 pure full WBC locomotion。

Stage 9.5 不代表以下事项完成：

- ROS2/C++ real-time controller
- EKF
- full 3D centroidal MPC
- base velocity tracking
- hardware deployment

## 八、输出文件

- Log: results/logs_sample/stage09_cpp_mirror_contract_report_log.csv
- Summary: results/logs_sample/stage09_cpp_mirror_contract_report_summary.csv
- Docs: docs/STAGE09_CPP_MIRROR_CONTRACT_REPORT.md

## 九、结论

Stage 9.0–9.5 可作为 ROS2/C++ interface mirror baseline。

下一步若继续推进，应进入 Stage 9.6 C++ mirror runtime contract guard，而不是直接写控制器。
