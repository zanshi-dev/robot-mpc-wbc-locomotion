# Stage 10.4 Python Frozen Baseline A/B Regression

## 目标

在任何 torque publisher 设计之前，重新回归 Stage 8 frozen Python baseline 与 Stage 8 adapter-backed A/B baseline。

本阶段不创建 /go1/joint_torque_cmd publisher，不调用 publish，不发布 torque，不改变控制律。

## 回归内容

- Stage 10.3 zero torque dry-run internal validation 已通过；
- C++ disabled controller 源码仍无 create_publisher；
- C++ disabled controller 源码仍无 publish call；
- C++ disabled controller 源码仍不引用 /go1/joint_torque_cmd；
- Stage 8 freeze integrity check 重新运行并通过；
- Stage 8 adapter-backed Stage 7 baseline A/B test 重新运行并通过。

## 结果

- pass: True
- stage8_freeze_pass_after_rerun: True
- stage83_ab_pass_after_rerun: True
- stage83_original_pass_after_rerun: True
- stage83_adapter_pass_after_rerun: True
- stage83_original_pass_margin_after_rerun: True
- stage83_adapter_pass_margin_after_rerun: True
- torque_enable_ready: False

## Safety gate 更新

Stage 10.4 后：

- G6 zero torque dry-run regression completed: True
- G7 Python frozen baseline A/B regression still passes: True

但 G4 与 G5 仍未完成，所以 torque_enable_ready 必须保持 False。

## 输出

- Log: results/logs_sample/stage10_python_frozen_baseline_ab_regression_log.csv
- Safety gate: results/logs_sample/stage10_torque_publisher_safety_gate_after_stage104.csv
- Summary: results/logs_sample/stage10_python_frozen_baseline_ab_regression_summary.csv
- Docs: docs/STAGE10_PYTHON_FROZEN_BASELINE_AB_REGRESSION.md

## 边界

当前 baseline 仍是 mixed online control baseline。

本阶段不是 ROS2/C++ realtime controller，不发布 torque，不完成 pure WBC locomotion，不完成 EKF。
