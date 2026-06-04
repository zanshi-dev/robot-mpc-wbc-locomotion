# Stage 11.0–11.8 Full Publisher-path No-active-publisher Freeze

## 一、冻结结论

Stage 11.0–11.8 已形成 full publisher-path no-active-publisher frozen baseline。

该 baseline 包含：

- publisher-path skeleton planning；
- source guard before implementation；
- disabled publisher-path skeleton design；
- publisher-path planning freeze；
- disabled skeleton preflight；
- dormant publisher-path source skeleton；
- dormant source skeleton freeze；
- runtime guard hardening；
- dormant publisher skeleton runtime freeze。

该 baseline 没有创建 ROS torque publisher，没有调用 publish，没有引用 /go1/joint_torque_cmd，没有发布 torque，没有改变控制律。

## 二、Stage 11.0–11.8 汇总

| 阶段 | 测试名 | scope | pass | torque_publisher_enabled | control_law_changed |
|---|---|---|---:|---:|---:|
| Stage 11.0 | publisher_path_skeleton_planning_only | publisher_path_skeleton_planning_only | True | False | False |
| Stage 11.1 | publisher_path_source_guard_before_implementation | publisher_path_source_guard_before_implementation_only | True | False | False |
| Stage 11.2 | disabled_publisher_path_skeleton_design_only | disabled_publisher_path_skeleton_design_only | True | False | False |
| Stage 11.3 | stage11_0_2_publisher_path_planning_freeze_summary | publisher_path_planning_freeze_summary_only | True | False | False |
| Stage 11.4 | disabled_publisher_path_skeleton_preflight | disabled_publisher_path_skeleton_preflight_only | True | False | False |
| Stage 11.5 | dormant_publisher_path_source_skeleton | dormant_publisher_path_source_skeleton_without_ros_publisher_construction | True | False | False |
| Stage 11.6 | dormant_publisher_path_source_skeleton_freeze_summary | dormant_publisher_path_source_skeleton_freeze_summary_only | True | False | False |
| Stage 11.7 | runtime_guard_hardening_for_dormant_publisher_skeleton | runtime_guard_hardening_for_dormant_publisher_skeleton_only | True | False | False |
| Stage 11.8 | stage11_5_7_dormant_publisher_runtime_freeze_summary | dormant_publisher_skeleton_runtime_freeze_summary_only | True | False | False |

## 三、最终源码安全状态

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: False
- source_has_publish_call: False
- source_has_torque_topic: False
- source_has_dormant_skeleton_marker: True
- source_has_construct_forbidden_marker: True
- source_has_publish_forbidden_marker: True
- source_has_payload_length_12: True
- source_has_dormant_payload_helper: True

## 四、最终 runtime guard

Observation CSV:

    results/logs_sample/stage11_runtime_guard_hardening_topic_observations.csv

Results:

- runtime_observation_row_count: 6
- runtime_observation_publishers_zero_all_rows: True
- runtime_observation_subscribers_positive_all_rows: True

## 五、最终 safety gate

- G8 manual enable flags active at runtime: False
- G9 active ROS publisher path exists: False
- G16 dormant publisher-path source skeleton exists: True
- G17 runtime guard hardened for dormant publisher skeleton: True

Therefore:

    torque_enable_ready = False

G8 与 G9 仍为 False，因此不能发布 torque。

## 六、冻结 hash

Hash CSV:

    results/logs_sample/stage11_0_8_full_publisher_path_no_active_publisher_freeze_hashes.csv

## 七、明确边界

当前 baseline 仍是 mixed online control baseline。

Stage 11.0–11.8 没有完成：

- ROS torque publisher construction；
- /go1/joint_torque_cmd active publisher；
- publish call；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。

## 八、结论

Stage 11.0–11.8 可作为 full publisher-path no-active-publisher frozen baseline。

后续若继续，应先做 full freeze integrity check，不应直接引入 active publisher。
