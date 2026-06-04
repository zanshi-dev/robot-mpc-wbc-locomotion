# Stage 12.10 Publish-call Preflight Freeze

## 一、冻结结论

Stage 12.10 冻结 publish-call preflight baseline。

当前状态：

- active ROS publisher path exists: True
- current_source_has_create_publisher: True
- current_source_has_publish_call: False
- manual_enable_active: False
- torque_enable_ready: False
- torque_command_published_by_stage1210: False

本阶段不修改 C++ source，不加入 publish call，不发布 torque，不改变控制律。

## 二、Stage 12.4–12.9 汇总

| 阶段 | 测试名 | scope | pass | torque_publisher_enabled | control_law_changed |
|---|---|---|---:|---:|---:|
| Stage 12.4 | publisher_construction_source_patch_without_publish | publisher_construction_source_patch_without_publish_call | True | False | False |
| Stage 12.5 | publisher_construction_no_publish_freeze | publisher_construction_no_publish_freeze_only | True | False | False |
| Stage 12.6 | manual_enable_activation_design_only | manual_enable_activation_design_only | True | False | False |
| Stage 12.7 | manual_enable_runtime_activation_without_publish | manual_enable_runtime_activation_without_publish_call | True | False | False |
| Stage 12.8 | manual_enable_no_publish_freeze | manual_enable_no_publish_freeze_only | True | False | False |
| Stage 12.9 | publish_call_design_only | publish_call_design_only | True | False | False |

## 三、Source integrity

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- current_source_has_create_publisher: True
- current_source_has_publish_call: False
- current_source_references_torque_topic: True
- current_source_has_active_publisher_member: True
- current_source_has_stage124_marker: True

## 四、Publish-call design integrity

Design CSV:

    results/logs_sample/stage12_publish_call_design.csv

Checks:

- publish_design_all_items_not_implemented: True
- publish_design_has_publish_call_site: True
- publish_design_has_preconditions: True
- publish_design_has_payload_contract: True
- publish_design_has_safety_filter: True
- publish_design_has_first_publish_policy: True
- publish_design_has_abort_conditions: True

## 五、Safety gate after Stage 12.10

新增：

- G28 publish-call preflight freeze passed: True

Key gates:

- G3 no publish call: True
- G8 manual enable active after revert: False
- G9 active ROS publisher path exists: True
- G27 publish-call design exists: True

Therefore:

    torque_enable_ready = False

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.10 没有完成：

- publish call；
- torque command publishing；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。
