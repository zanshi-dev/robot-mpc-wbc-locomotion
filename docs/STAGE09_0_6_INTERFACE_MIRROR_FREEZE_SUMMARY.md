# Stage 9.0–9.6 ROS2/C++ Interface Mirror Freeze Summary

## 一、冻结结论

Stage 9.0–9.6 已形成 ROS2/C++ interface mirror baseline。

该 baseline 只完成接口镜像、schema 记录、字段映射、C++ mirror skeleton、runtime smoke test 与 runtime contract guard。

它不是 ROS2/C++ real-time controller。

它不发布 torque command。

它没有改变 Stage 8 frozen Python baseline 的控制律。

## 二、当前 C++ mirror package

Package:

    ros2_ws/src/robot_mpc_wbc_cpp_interface

Node:

    go1_interface_mirror_node

Launch:

    ros2_ws/src/robot_mpc_wbc_cpp_interface/launch/interface_mirror.launch.py

## 三、Stage 9.0–9.6 汇总

| 阶段 | 测试名 | scope | pass | control_law_changed |
|---|---|---|---:|---:|
| Stage 9.0 | ros2_cpp_interface_contract_inventory | interface_inventory_only | True | False |
| Stage 9.1 | ros2_topic_schema_snapshot | topic_schema_snapshot_only | True | False |
| Stage 9.2 | python_baseline_ros2_field_mapping | field_mapping_table_only | True | False |
| Stage 9.3 | ros2_cpp_interface_mirror_skeleton_check | cpp_interface_mirror_skeleton_only | True | False |
| Stage 9.4 | ros2_runtime_mirror_smoke_test | runtime_mirror_smoke_test_only | True | False |
| Stage 9.5 | cpp_mirror_contract_report | cpp_mirror_contract_report_only | True | False |
| Stage 9.6 | cpp_mirror_runtime_contract_guard | cpp_mirror_runtime_contract_guard_only | True | False |

## 四、关键 runtime guard 结果

Stage 9.6 结果：

- sample_row_count: 30
- all_sample_topic_types_match: True
- torque_cmd_publishers_all_zero: True
- torque_cmd_subscribers_positive: True
- source_has_no_create_publisher: True
- source_has_no_publish_call: True

## 五、接口合同

已冻结 topic：

- /go1/joint_states
- /go1/base_state
- /go1/imu
- /go1/foot_contacts
- /go1/sim_time
- /go1/joint_torque_cmd

关键约束：

- /go1/joint_torque_cmd publisher count 必须为 0；
- C++ mirror 只能订阅，不允许发布 torque；
- C++ mirror 不允许调用 publish；
- joint order 继续遵守 MuJoCo actuator order: FR, FL, RR, RL；每条腿 hip, thigh, calf；
- quaternion 顺序继续遵守 Stage 8 runtime adapter contract。

## 六、边界

Stage 9.0–9.6 没有完成：

- ROS2/C++ real-time controller
- pure full WBC locomotion
- EKF
- full 3D centroidal MPC
- base velocity tracking
- hardware deployment

当前 baseline 仍是 mixed online control baseline。

## 七、冻结文件 hash

Hash log:

    results/logs_sample/stage09_0_6_interface_mirror_freeze_hashes.csv

## 八、结论

Stage 9.0–9.6 可作为 ROS2/C++ interface mirror frozen baseline。

后续如果进入控制器实现，必须先以该 baseline 做回归，且第一步应继续保持 torque publisher disabled。
