# Stage 12.16 Continuous Torque Streaming Design Only

## 一、结论

Stage 12.16 只设计 future continuous torque streaming protocol。

本阶段不修改 C++ source，不新增 publish call，不启动连续 torque streaming。

Current source state:

- publish_call_count: 1
- source_has_delayed_one_shot_timer: True
- source_has_zero_safe_message_helper: True
- source_unchanged_by_stage1216: True

## 二、前置状态

Stage 12.15:

- pass: True
- bounded_one_shot_publish_call_freeze_regression_passed: True
- default_disabled_regression_passed: True
- enabled_bounded_publish_regression_passed: True
- previous_no_continuous_streaming: True

## 三、Continuous streaming design

Design CSV:

    results/logs_sample/stage12_continuous_torque_streaming_design.csv

Future protocol:

- separate two-flag confirmation for continuous streaming;
- initial dry-run rate <= 10 Hz;
- initial dry-run duration <= 3 seconds;
- payload length 12, finite, zero/safe first;
- watchdog and clamp on every cycle;
- timer must stop after duration and after flag revert;
- no messages after stop;
- no hardware deployment;
- no control law, estimator, MPC, WBC, or gait changes.

## 四、Safety gate after Stage 12.16

新增：

- G36 continuous torque streaming design exists: True

Key gates:

- G3 no publish call: False
- G8 manual enable active after revert: False
- G9 active ROS publisher path exists: True
- G35 bounded one-shot freeze and regression passed: True

Therefore:

    torque_enable_ready = False

## 五、边界

当前 baseline 仍是 mixed_online_control_baseline。

Stage 12.16 没有完成：

- continuous torque streaming；
- torque streaming controller；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。
