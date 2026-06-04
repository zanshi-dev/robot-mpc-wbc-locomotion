# Stage 10.7–10.8 Safety Utility Freeze Summary

## 一、冻结结论

Stage 10.7–10.8 已形成 safety-utility frozen baseline。

该 baseline 包含：

- torque clamp utility；
- watchdog freshness utility；
- zero torque fallback；
- disabled controller 内部接入 clamp/watchdog utilities；
- runtime 验证 torque publisher count 仍为 0。

该 baseline 不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 二、Stage 10.7–10.8 汇总

| 阶段 | 测试名 | scope | pass | torque_publisher_enabled | control_law_changed |
|---|---|---|---:|---:|---:|
| Stage 10.7 | clamp_watchdog_utility_without_publisher | clamp_watchdog_utility_without_publisher_only | True | False | False |
| Stage 10.8 | disabled_controller_uses_safety_utilities | disabled_controller_uses_safety_utilities_without_publisher_only | True | False | False |

## 三、源码安全状态

Controller source:

    ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp

Checks:

- source_has_create_publisher: False
- source_has_publish_call: False
- source_has_torque_topic: False
- source_includes_safety_header: True
- source_uses_clamp_torque_command: True
- source_uses_watchdog_fresh_check: True
- source_uses_watchdog_fallback_zero: True

## 四、Safety gate after Stage 10.8

- G0 Stage 8 frozen Python baseline valid: True
- G1 Stage 9 interface mirror frozen: True
- G2 C++ controller source has no torque publisher: True
- G3 C++ controller source has no publish call: True
- G4 Explicit manual enable flag design exists: True
- G5 Torque clamp and watchdog utility implemented: True
- G6 Zero torque dry-run regression completed: True
- G7 Python frozen baseline A/B regression still passes: True
- G8 Manual enable flags active at runtime: False
- G9 Publisher path exists: False
- G10 Disabled controller uses clamp/watchdog internally: True

Therefore:

    torque_enable_ready = False

G8 与 G9 仍为 False，因此不能启用 torque publisher。

## 五、冻结 hash

Hash CSV:

    results/logs_sample/stage10_7_8_safety_utility_freeze_hashes.csv

## 六、边界

当前 baseline 仍是 mixed online control baseline。

Stage 10.7–10.8 没有完成：

- ROS2/C++ realtime controller；
- torque publisher；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。

## 七、结论

Stage 10.7–10.8 可作为 safety-utility frozen baseline。

后续如果继续，应先实现 manual enable parameters disabled-by-default，仍不创建 publisher。
