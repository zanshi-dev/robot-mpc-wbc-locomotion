# Stage 7：Online Swing Joint Tracking Recommended Test

## 状态

通过。

## 目标

使用 stability sweep 推荐配置，重新运行 online swing joint target tracking support test，固化为当前默认 baseline。

该测试只验证 online swing joint target tracking，不叠加 full WBC torque。

## 输入文件

results/logs_sample/stage07_online_swing_trajectory_tracking_check.csv

## 脚本

scripts/stage07_online_swing_joint_tracking_recommended_test.py

## 输出文件

results/logs_sample/stage07_online_swing_joint_tracking_recommended_test_log.csv

results/logs_sample/stage07_online_swing_joint_tracking_recommended_test_summary.csv

## 推荐配置

kp = 80.0

kd = 2.0

target_scale = 0.6

torque_limit = 23.7

## 结果

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

## 结论

online swing joint tracking recommended test 通过。

当前 online swing joint tracking 推荐 baseline：

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

该测试仍不是完整动态 trot locomotion。

尚未完成：

1. online swing joint tracking 与 full WBC torque 同时闭环
2. swing target 到 full WBC swing acceleration task 的在线转换
3. touchdown/liftoff contact feedback
4. base velocity tracking
5. forward velocity command
6. ROS2/C++ 实时实现

## 下一步

建议进入 combined online test：

scripts/stage07_online_full_wbc_plus_swing_joint_tracking_proto.py

目标：

1. 使用 online full WBC scheduler recommended baseline
2. 使用 online swing joint tracking recommended baseline
3. full WBC torque + scaled swing joint PD torque 同时作用
4. 检查 base_z、roll、pitch、joint error、torque saturation
5. 先保持原地 trot，不加入 forward velocity

建议输出：

results/logs_sample/stage07_online_full_wbc_plus_swing_joint_tracking_proto_log.csv

results/logs_sample/stage07_online_full_wbc_plus_swing_joint_tracking_proto_summary.csv
