# Stage 10.3 Zero Torque Dry-run Internal Command Validation

## 目标

验证 disabled-by-default C++ controller skeleton 的内部 zero torque dry-run command 对象。

本阶段不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 新增 C++ 文件

- ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp
- ros2_ws/src/robot_mpc_wbc_cpp_controller/src/zero_torque_dry_run_contract_check.cpp

## 验证内容

- zero torque vector 长度为 12；
- 所有元素 finite；
- 所有元素等于 0；
- max abs 为 0；
- L1 norm 为 0；
- disabled controller 源码使用 zero torque factory；
- disabled controller 源码无 create_publisher；
- disabled controller 源码无 publish call；
- disabled controller 源码不引用 /go1/joint_torque_cmd；
- runtime 下 /go1/joint_torque_cmd publisher count 为 0。

## 结果

- pass: True
- zero_torque_size: 12
- zero_torque_all_finite: True
- zero_torque_all_zero: True
- zero_torque_max_abs: 0
- zero_torque_l1: 0
- torque_topic_publishers_zero: True

## 输出

- Log: results/logs_sample/stage10_zero_torque_dry_run_internal_validation_log.csv
- Vector CSV: results/logs_sample/stage10_zero_torque_dry_run_vector.csv
- Summary: results/logs_sample/stage10_zero_torque_dry_run_internal_validation_summary.csv
- Docs: docs/STAGE10_ZERO_TORQUE_DRY_RUN_INTERNAL_VALIDATION.md

## 边界

当前 baseline 仍是 mixed online control baseline。

本阶段不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
