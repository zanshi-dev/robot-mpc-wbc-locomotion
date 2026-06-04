# Stage 9.6 C++ Mirror Runtime Contract Guard

## 目标

将 Stage 9.4 smoke test 固化为可重复运行的 runtime contract guard。

该 guard 多轮采样 ROS2 topic type、publisher count、subscription count，确认 C++ mirror 只做 interface mirror。

## 检查内容

- Stage 9.5 contract report 已通过；
- bridge 与 mirror 节点可启动；
- 6 个 topic 的类型持续匹配；
- 5 个 bridge 发布 topic 均有 publisher 与 subscriber；
- /go1/joint_torque_cmd 的 publisher count 始终为 0；
- /go1/joint_torque_cmd 的 subscriber count 始终大于等于 2；
- C++ mirror stdout 明确声明不发布 torque command。

## 结果

- pass: True
- all_sample_topic_types_match: True
- torque_cmd_publishers_all_zero: True
- torque_cmd_subscribers_positive: True
- published_topics_have_publishers: True
- published_topics_have_subscribers: True

## 输出

- Log: results/logs_sample/stage09_cpp_mirror_runtime_contract_guard_log.csv
- Samples: results/logs_sample/stage09_cpp_mirror_runtime_contract_guard_samples.csv
- Summary: results/logs_sample/stage09_cpp_mirror_runtime_contract_guard_summary.csv
- Bridge stdout/stderr: results/logs_sample/stage09_cpp_mirror_runtime_contract_guard_bridge_stdout.txt / stderr.txt
- Mirror stdout/stderr: results/logs_sample/stage09_cpp_mirror_runtime_contract_guard_mirror_stdout.txt / stderr.txt

## 边界

本阶段不发布 torque command，不写实时 C++ controller，不改变控制律，不完成 EKF，不完成 pure WBC locomotion。

当前 baseline 仍是 mixed online control baseline。
