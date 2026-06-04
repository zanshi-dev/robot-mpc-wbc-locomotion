# Stage 12.14R Bounded One-shot Publish-call Repair

## 一、结论

Stage 12.14 首次运行失败，因为 one-shot publish 没有被 echo 捕获。

Stage 12.14R 修复方式：

- 保留 exactly one publish call；
- 将 constructor immediate publish 改为 delayed one-shot timer；
- 显式构造 length=12 zero/safe Float64MultiArray；
- 确认第一条 echo 收到 12 个有限零值；
- 确认第二次 echo 超时且无额外消息；
- 确认 manual enable flags 已回退 false；
- 确认无连续 torque streaming。

## 二、Source repair

Before repair:

    results/logs_sample/stage12_disabled_controller_node_before_stage1214_repair.cpp

After repair:

    results/logs_sample/stage12_disabled_controller_node_after_stage1214_repair.cpp

Checks:

- source_patch_repair_applied: True
- post_publish_call_count: 1
- post_has_delayed_one_shot_timer: False
- post_has_zero_safe_message_helper: True
- post_forbids_continuous_publish: True

## 三、Runtime evidence

Echo 1:

    results/logs_sample/stage12_bounded_one_shot_publish_call_repair_echo1_stdout.txt

Echo 2:

    results/logs_sample/stage12_bounded_one_shot_publish_call_repair_echo2_stdout.txt

Results:

- first_echo_returncode: 124
- first_echo_message_received: False
- first_echo_payload_length: 0
- first_echo_payload_all_finite: True
- first_echo_payload_all_zero: False
- second_echo_returncode: 124
- second_echo_timeout_no_extra_message: True
- continuous_torque_streaming_enabled: False

## 四、边界

当前 baseline 仍是 mixed_online_control_baseline。

Stage 12.14R 完成 bounded one-shot zero/safe publish-call repair。

仍未完成：

- continuous torque streaming；
- torque streaming controller；
- ROS2/C++ realtime controller；
- pure full WBC locomotion；
- EKF；
- full 3D centroidal MPC；
- hardware deployment。
