# Stage 12.15 Bounded One-shot Publish-call Freeze and Regression Check

## 一、结论

Stage 12.15 freezes the bounded one-shot zero/safe publish-call state and runs regression checks.

Current source state:

- publish_call_count: 1
- source_has_delayed_one_shot_timer: True
- source_has_zero_safe_message_helper: True
- source_unchanged_by_stage1215: True

Default-disabled regression:

- default_echo_returncode: 124
- default_disabled_no_message_observed: True

Manual-enabled bounded publish regression:

- enabled_echo1_returncode: 0
- enabled_first_message_received: True
- enabled_payload_length: 12
- enabled_payload_all_finite: True
- enabled_payload_all_zero: True
- enabled_echo2_returncode: 124
- enabled_second_echo_timeout_no_extra_message: True

Safety boundary:

- bounded_zero_safe_torque_message_published_by_stage1215: True
- continuous_torque_streaming_enabled: False
- torque_enable_ready: False
- torque_publisher_enabled: False
- control_law_changed: False

## 二、Artifacts

- Log: `results/logs_sample/stage12_bounded_one_shot_publish_call_freeze_regression_log.csv`
- Summary: `results/logs_sample/stage12_bounded_one_shot_publish_call_freeze_regression_summary.csv`
- Hashes: `results/logs_sample/stage12_bounded_one_shot_publish_call_freeze_regression_hashes.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1215.csv`
- Default echo stdout: `results/logs_sample/stage12_bounded_one_shot_publish_call_freeze_default_echo_stdout.txt`
- Enabled echo stdout: `results/logs_sample/stage12_bounded_one_shot_publish_call_freeze_enabled_echo1_stdout.txt`

## 三、Scope boundary

Current baseline remains `mixed_online_control_baseline`.

Stage 12.15 does not complete:

- continuous torque streaming;
- torque streaming controller;
- ROS2/C++ realtime controller;
- pure full WBC locomotion;
- EKF;
- full 3D centroidal MPC;
- hardware deployment.
