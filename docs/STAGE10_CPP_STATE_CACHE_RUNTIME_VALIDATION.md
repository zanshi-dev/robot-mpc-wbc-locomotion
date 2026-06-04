# Stage 10.2 C++ State Cache Runtime Validation

## 目标

验证 disabled-by-default C++ controller skeleton 的 state cache 输入链路。

本阶段只验证状态订阅与缓存逻辑，不创建 torque publisher，不调用 publish，不改变控制律。

## 验证内容

- Stage 10.1 已通过；
- C++ source 无 create_publisher；
- C++ source 无 publish call；
- C++ source 不引用 /go1/joint_torque_cmd；
- C++ source 包含 state cache 写入逻辑；
- bridge 与 disabled controller 可同时启动；
- 5 个状态 topic 存在、类型匹配、有 publisher/subscriber，并可 echo 到非空样本；
- /go1/joint_torque_cmd publisher count 为 0。

## 结果

- pass: True
- state_topic_present_count: 5
- state_topic_type_match_count: 5
- state_topic_pubsub_ok_count: 5
- state_topic_echo_ok_count: 5
- torque_topic_publishers_zero: True

## 输出

- Log: results/logs_sample/stage10_cpp_state_cache_runtime_validation_log.csv
- Topic observations: results/logs_sample/stage10_cpp_state_cache_runtime_validation_topic_observations.csv
- Summary: results/logs_sample/stage10_cpp_state_cache_runtime_validation_summary.csv
- Build stdout/stderr: results/logs_sample/stage10_cpp_state_cache_runtime_validation_build_stdout.txt / stderr.txt
- Controller stdout/stderr: results/logs_sample/stage10_cpp_state_cache_runtime_validation_controller_stdout.txt / stderr.txt

## 边界

当前 baseline 仍是 mixed online control baseline。

本阶段不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
