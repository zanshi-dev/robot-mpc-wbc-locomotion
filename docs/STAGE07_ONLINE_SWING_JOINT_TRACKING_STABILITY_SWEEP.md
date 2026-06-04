# Stage 7：Online Swing Joint Tracking Stability Sweep

## 状态

通过。

## 目标

对 online swing joint target tracking support test 做 KP / KD / target_scale sweep，寻找满足 joint error、姿态、高度和 torque limit 的稳定配置。

## 背景

原始 online swing joint target tracking support test 使用：

kp = 60.0

kd = 2.0

target_scale = 1.0

结果：

max_joint_error = 0.099326587385

pass = False

失败原因：

max_joint_error > 0.08

姿态、高度和 torque saturation 均不是失败主因。

## 输入脚本

scripts/stage07_online_swing_joint_target_tracking_support_test.py

## 输出文件

results/logs_sample/stage07_online_swing_joint_tracking_stability_sweep.csv

## Sweep 参数

KP_LIST = [60.0, 80.0, 100.0]

KD_LIST = [2.0, 4.0, 6.0]

TARGET_SCALE_LIST = [0.60, 0.75, 0.90, 1.00]

total cases = 36

## 总体结果

num_cases = 36

pass_cases = 6

pass_margin_cases = 6

## 推荐配置

kp = 80.0

kd = 2.0

target_scale = 0.6

## 推荐配置结果

total_steps = 1200

initial_z = 0.284805846483

final_z = 0.282769844842

min_z = 0.270657074947

max_z = 0.285595003453

delta_z = -0.002036001641

final_roll = -0.006184160640

final_pitch = -0.008386076938

max_abs_roll = 0.063224324564

roll_margin_to_0p20 = 0.136775675436

max_abs_pitch = 0.055307047284

pitch_margin_to_0p20 = 0.144692952716

z_margin_to_0p22 = 0.050657074947

max_joint_error = 0.059643533460

max_swing_joint_error = 0.059643533460

max_stance_joint_error = 0.035331528104

max_tau_raw_abs = 9.930087778241

max_tau_total_abs = 9.930087778241

saturation_steps = 0

pass = True

pass_margin = True

recommended = True

## 其他可通过配置

以下配置也通过：

1. kp = 60.0, kd = 2.0, target_scale = 0.6
2. kp = 100.0, kd = 2.0, target_scale = 0.6
3. kp = 100.0, kd = 2.0, target_scale = 0.75
4. kp = 100.0, kd = 2.0, target_scale = 0.9
5. kp = 100.0, kd = 2.0, target_scale = 1.0

KD = 4.0 和 KD = 6.0 的配置未成为推荐项；KD = 6.0 多数出现 torque saturation。

## 结论

online swing joint tracking stability sweep 通过。

当前推荐 online swing joint tracking baseline：

kp = 80.0

kd = 2.0

target_scale = 0.6

该配置满足：

1. max_joint_error < 0.08
2. min_z > 0.22
3. max_abs_roll < 0.20
4. max_abs_pitch < 0.20
5. saturation_steps = 0
6. pass_margin = True

## 当前边界

该测试只验证 joint target tracking，不叠加 full WBC torque。

尚未完成：

1. online swing target 与 full WBC 同时闭环
2. swing target 到 full WBC acceleration task 的转换
3. touchdown/liftoff contact feedback
4. base velocity tracking
5. forward velocity command
6. ROS2/C++ 实时实现

## 下一步

建议生成 recommended online swing joint target tracking support test。

建议脚本：

scripts/stage07_online_swing_joint_tracking_recommended_test.py

配置：

kp = 80.0

kd = 2.0

target_scale = 0.6

输出：

results/logs_sample/stage07_online_swing_joint_tracking_recommended_test_log.csv

results/logs_sample/stage07_online_swing_joint_tracking_recommended_test_summary.csv
