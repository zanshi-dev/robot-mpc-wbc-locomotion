# Stage 8.7 推荐 runtime-safe 入口固化

## 推荐入口

后续 Stage 8 默认运行：

    /usr/bin/python3 scripts/stage08_adapter_backed_stage07_recommended_test.py

## 前置结论

- Stage 8.3 A/B regression 已通过。
- Stage 8.6 active-path leg order refactor 已通过。
- active high-severity runtime mapping duplication 已清零。
- 当前入口仍运行 Stage 7 mixed online control baseline。

## 控制边界

该入口没有改变控制律。

当前控制器仍是：

1. stance legs 使用 posture PD；
2. stance legs 叠加 scaled stance WBC feedforward；
3. swing legs 使用 online swing target PD；
4. WBC torque 不直接作用 swing legs；
5. swing PD 不直接作用 stance legs。

## 非完成项

本阶段不代表以下内容已完成：

- pure full WBC locomotion
- ROS2/C++ real-time controller
- EKF
- base velocity tracking
- full 3D centroidal MPC
- OSQP warm-start / real-time timing guarantee
- 硬件部署

## 输出文件

- results/logs_sample/stage08_recommended_runtime_safe_entrypoint_promotion_summary.csv
- results/logs_sample/stage08_recommended_runtime_safe_entrypoint_stdout.txt
- results/logs_sample/stage08_recommended_runtime_safe_entrypoint_stderr.txt

## 结论

Stage 8.7 固化 runtime-safe 推荐入口。后续 Stage 8 默认基于：

    /usr/bin/python3 scripts/stage08_adapter_backed_stage07_recommended_test.py
