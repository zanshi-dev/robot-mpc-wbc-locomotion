# Stage 12.18 Continuous Torque Streaming Source Patch Design Only

## 一、结论

Stage 12.18 only designs the future continuous torque streaming source patch.

本阶段不修改 C++ source，不新增 publish call，不创建 continuous streaming timer，不发布连续 torque。

Current source state:

- source_unchanged_by_stage1218: True
- publish_call_count: 1
- source_has_no_continuous_streaming_flags: True
- source_has_no_continuous_streaming_timer: True

## 二、Future patch design

Design CSV:

    results/logs_sample/stage12_continuous_torque_streaming_source_patch_design.csv

Future patch constraints:

- add two continuous streaming params, default false;
- require four-flag gate before streaming;
- add cancellable continuous_torque_streaming_timer_;
- initial rate <= 10 Hz;
- initial duration <= 3 seconds or <= 30 ticks;
- reuse existing single safe publish call path; source publish call count should remain 1;
- payload length 12, finite, zero/safe dry-run first;
- watchdog and clamp every tick;
- cancel timer after tick limit, flag revert, stale watchdog, invalid payload, or shutdown;
- collect runtime evidence: bounded message count and no messages after stop;
- no hardware deployment;
- no control law, estimator, MPC, WBC, or gait changes.

## 三、Safety gate after Stage 12.18

新增：

- G38 continuous torque streaming source patch design exists: True

Key gates:

- G37 continuous torque streaming preflight freeze passed: True
- G36 continuous torque streaming design exists: True
- G9 active ROS publisher path exists: True

Therefore:

    torque_enable_ready = False

## 四、边界

当前 baseline 仍是 mixed_online_control_baseline。

Stage 12.18 没有完成：

- continuous torque streaming；
- torque streaming controller；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。
