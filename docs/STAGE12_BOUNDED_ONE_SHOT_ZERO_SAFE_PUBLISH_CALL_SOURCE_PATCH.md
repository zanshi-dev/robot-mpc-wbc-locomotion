# Stage 12.14 Bounded One-shot Zero/Safe Publish-call Source Patch

## 一、结论

Stage 12.14 实现 bounded one-shot zero/safe publish-call source patch。

本阶段允许 exactly one bounded publish call：

- source publish call count: 1
- first_echo_message_received: False
- first_echo_payload_length: 0
- first_echo_payload_all_finite: True
- first_echo_payload_all_zero: False
- second_echo_timeout_no_extra_message: True
- continuous_torque_streaming_enabled: False

## 二、Source patch

Before source backup:

    results/logs_sample/stage12_disabled_controller_node_before_stage1214.cpp

After source snapshot:

    results/logs_sample/stage12_disabled_controller_node_after_stage1214.cpp

Hash before:

    a8c10fcbb6c260c199865ce62601df242706619c9f46db04c75c484911ff8a76

Hash after:

    b3950287e9ed36c88e2b299376d21a9504265eebb99a33a992f5c0079c9b9e03

Source checks:

- post_source_has_create_publisher: True
- post_publish_call_count: 1
- post_source_has_stage1214_marker: True
- post_source_has_bounded_publish_helper: True
- post_source_forbids_continuous_publish: True

## 三、Runtime evidence

Echo 1 stdout:

    results/logs_sample/stage12_bounded_one_shot_zero_safe_publish_call_echo1_stdout.txt

Echo 2 stdout:

    results/logs_sample/stage12_bounded_one_shot_zero_safe_publish_call_echo2_stdout.txt

Param observations:

    results/logs_sample/stage12_bounded_one_shot_zero_safe_publish_call_param_observations.csv

Topic observations:

    results/logs_sample/stage12_bounded_one_shot_zero_safe_publish_call_topic_observations.csv

Runtime checks:

- manual_enable_active_during_test: True
- manual_enable_reverted_false: True
- active_ros_publisher_path_exists: True
- bounded_zero_safe_torque_message_published: False
- controller_alive_after_publish: True

## 四、Safety gate after Stage 12.14

Updated:

- G3 no publish call: False by design
- G8 manual enable active after revert: False
- G9 active ROS publisher path exists: True
- G32 bounded one-shot zero/safe publish-call implementation passed: False

Therefore:

    torque_enable_ready = False

## 五、边界

当前 baseline 仍是 mixed online control baseline。

Stage 12.14 完成的是 bounded one-shot zero/safe publish-call test，不是连续 torque streaming。

Stage 12.14 没有完成：

- continuous torque publishing；
- torque streaming controller；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。
