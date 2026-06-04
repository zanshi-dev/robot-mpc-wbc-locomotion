# Stage 11.5–11.7 Dormant Publisher Skeleton Runtime Freeze Summary

## 一、冻结结论

Stage 11.5–11.7 已形成 dormant publisher skeleton runtime frozen baseline。

该 baseline 包含：

- dormant publisher-path source skeleton；
- dormant skeleton freeze；
- runtime guard hardening；
- 6 次 /go1/joint_torque_cmd topic info 采样；
- manual enable 参数默认 false；
- publisher count 全部为 0。

该 baseline 不创建 ROS torque publisher，不调用 publish，不引用 /go1/joint_torque_cmd，不发布 torque，不改变控制律。

## 二、Stage 11.5–11.7 汇总

| 阶段 | 测试名 | scope | pass | torque_publisher_enabled | control_law_changed |
|---|---|---|---:|---:|---:|
| Stage 11.5 | dormant_publisher_path_source_skeleton | dormant_publisher_path_source_skeleton_without_ros_publisher_construction | True | False | False |
| Stage 11.6 | dormant_publisher_path_source_skeleton_freeze_summary | dormant_publisher_path_source_skeleton_freeze_summary_only | True | False | False |
| Stage 11.7 | runtime_guard_hardening_for_dormant_publisher_skeleton | runtime_guard_hardening_for_dormant_publisher_skeleton_only | True | False | False |

## 三、源码安全状态

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: False
- source_has_publish_call: False
- source_has_torque_topic: False
- dormant_publisher_path_source_skeleton_exists: True

## 四、Runtime guard

Observation CSV:

    results/logs_sample/stage11_runtime_guard_hardening_topic_observations.csv

Results:

- runtime_observation_row_count: 6
- runtime_observation_publishers_zero_all_rows: True
- runtime_observation_subscribers_positive_all_rows: True

## 五、Safety gate after Stage 11.7

- G8 manual enable flags active at runtime: False
- G9 active ROS publisher path exists: False
- G16 dormant publisher-path source skeleton exists: True
- G17 runtime guard hardened for dormant publisher skeleton: True

Therefore:

    torque_enable_ready = False

G8 与 G9 仍为 False，因此不能发布 torque。

## 六、冻结 hash

Hash CSV:

    results/logs_sample/stage11_5_7_dormant_publisher_runtime_freeze_hashes.csv

## 七、明确边界

当前 baseline 仍是 mixed online control baseline。

Stage 11.8 没有完成：

- ROS torque publisher construction；
- /go1/joint_torque_cmd publisher；
- publish call；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。

## 八、结论

Stage 11.5–11.7 可作为 dormant publisher skeleton runtime frozen baseline。

后续如果继续，应先冻结 Stage 11.0–11.8 full publisher-path no-active-publisher baseline，不应直接进入 active publisher construction。
