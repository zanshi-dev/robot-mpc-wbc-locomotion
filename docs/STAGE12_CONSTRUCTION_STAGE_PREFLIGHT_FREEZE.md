# Stage 12.3 Construction-stage Preflight Freeze

## 一、冻结结论

Stage 12.0–12.2 已形成 construction-stage preflight frozen baseline。

该 baseline 包含：

- active publisher construction planning；
- pre-construction source/runtime guard；
- publisher construction source patch design；
- source unchanged check；
- no create_publisher；
- no publish call；
- no /go1/joint_torque_cmd reference in controller source；
- active publisher path remains absent。

Stage 12.3 不修改 C++ controller 源码，不创建 publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、Stage 12.0–12.2 汇总

| 阶段 | 测试名 | scope | pass | torque_publisher_enabled | control_law_changed |
|---|---|---|---:|---:|---:|
| Stage 12.0 | active_publisher_construction_planning_only | active_publisher_construction_planning_only | True | False | False |
| Stage 12.1 | pre_construction_source_runtime_guard | pre_construction_source_runtime_guard_only | True | False | False |
| Stage 12.2 | publisher_construction_source_patch_design_only | publisher_construction_source_patch_design_only | True | False | False |

## 三、Source guard

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: False
- source_has_publish_call: False
- source_has_torque_topic: False
- dormant_publisher_path_source_skeleton_exists: True

## 四、Safety gate after Stage 12.2

- G8 manual enable flags active at runtime: False
- G9 active ROS publisher path exists: False
- G19 active publisher construction planning exists: True
- G20 pre-construction source and runtime guard passed: True
- G21 publisher construction source patch design exists: True

Therefore:

    torque_enable_ready = False

G8 与 G9 仍为 False，因此不能发布 torque。

## 五、冻结 hash

Hash CSV:

    results/logs_sample/stage12_construction_stage_preflight_freeze_hashes.csv

## 六、明确边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.3 没有完成：

- ROS torque publisher construction；
- /go1/joint_torque_cmd active publisher；
- publish call；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。

## 七、结论

Stage 12.0–12.3 可作为 construction-stage preflight frozen baseline。

后续如果继续，下一阶段才可考虑 publisher construction source patch implementation，但仍不得调用 publish。
