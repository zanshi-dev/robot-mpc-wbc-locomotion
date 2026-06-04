# Stage 12.8 Manual-enable No-publish Freeze

## 一、冻结结论

Stage 12.8 冻结 Stage 12.7 manual enable runtime activation without publish 的结果。

当前状态：

- active ROS publisher path exists: True
- manual_enable_active_during_test: True
- manual_enable_reverted_false: True
- source_has_publish_call: False
- no_message_observed_during_activation: True
- torque_command_published_by_stage128: False

本阶段不修改 C++ source，不加入 publish call，不发布 torque，不改变控制律。

## 二、Stage 12.4–12.7 汇总

| 阶段 | 测试名 | scope | pass | torque_publisher_enabled | control_law_changed |
|---|---|---|---:|---:|---:|
| Stage 12.4 | publisher_construction_source_patch_without_publish | publisher_construction_source_patch_without_publish_call | True | False | False |
| Stage 12.5 | publisher_construction_no_publish_freeze | publisher_construction_no_publish_freeze_only | True | False | False |
| Stage 12.6 | manual_enable_activation_design_only | manual_enable_activation_design_only | True | False | False |
| Stage 12.7 | manual_enable_runtime_activation_without_publish | manual_enable_runtime_activation_without_publish_call | True | False | False |

## 三、Source integrity

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- current_source_has_create_publisher: True
- current_source_has_publish_call: False
- current_source_references_torque_topic: True
- current_source_has_active_publisher_member: True
- current_source_has_stage124_marker: True

## 四、Runtime activation evidence

Parameter observations:

    results/logs_sample/stage12_manual_enable_runtime_activation_param_observations.csv

Topic observations:

    results/logs_sample/stage12_manual_enable_runtime_activation_topic_observations.csv

Evidence:

- initial_enable_false_observed: True
- initial_confirm_false_observed: True
- activated_enable_true_observed: True
- activated_confirm_true_observed: True
- reverted_enable_false_observed: True
- reverted_confirm_false_observed: True
- topic_observation_publishers_positive_all_rows: True
- topic_echo_stdout_empty: True

## 五、Safety gate after Stage 12.8

新增：

- G26 manual-enable no-publish freeze passed: True

Key gates:

- G3 no publish call: True
- G8 manual enable active at runtime after revert: False
- G9 active ROS publisher path exists: True
- G25 manual enable runtime activation without publish passed: True

Therefore:

    torque_enable_ready = False

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.8 没有完成：

- publish call；
- torque command publishing；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。
