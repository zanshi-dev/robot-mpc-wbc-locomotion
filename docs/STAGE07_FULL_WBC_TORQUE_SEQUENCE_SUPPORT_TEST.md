# Stage 7：Full WBC Torque Sequence Support Test

## 状态

通过。

## 目标

验证 full WBC swing acceleration task QP 输出的 torque，在 MuJoCo 中通过 ramp 后是否可以完成短时 torque sequence support test。

该测试是 full WBC torque closed-loop 前置验证，但仍不是完整动态 trot locomotion。

## 输入文件

results/logs_sample/stage07_full_wbc_torque_reconstruction_check.csv

## 输出文件

results/logs_sample/stage07_full_wbc_torque_sequence_support_test_log.csv

results/logs_sample/stage07_full_wbc_torque_sequence_support_test_summary.csv

## Mode Sequence

trot_FR_RL -> trot_FL_RR -> trot_FR_RL

## 配置

segment_steps = 300

num_segments = 3

total_steps = 900

ramp_steps = 5

kp = 80.0

kd = 2.0

torque_limit = 23.7

## 结果

initial_z = 0.284805846483

final_z = 0.302695944706

min_z = 0.284782520542

max_z = 0.315369147929

delta_z = 0.017890098222

final_roll = 0.090847703976

final_pitch = -0.056119160829

max_abs_roll = 0.097459520644

roll_margin_to_0p15 = 0.052540479356

max_abs_pitch = 0.064290563391

pitch_margin_to_0p15 = 0.085709436609

z_margin_to_0p22 = 0.064782520542

max_tau_pd_abs = 19.599741458584

max_tau_wbc_cmd_abs = 10.545880364253

max_tau_total_abs = 11.531362579026

max_cmd_step_jump_norm = 4.746000978862

max_cmd_step_jump_abs = 2.164602488251

saturation_steps = 0

pass = True

pass_margin = True

## 结论

full WBC torque sequence support test 通过。

该结果说明 full WBC 离线 QP 输出的 torque，在 ramp_steps = 5 平滑后，可以在 MuJoCo 中完成短时多模式 torque sequence 支撑测试。

当前 full WBC 已完成：

1. 离线 dynamics QP 验证
2. stance constraint 验证
3. base vertical acceleration task 验证
4. swing acceleration task 验证
5. torque reconstruction check
6. torque ramp check
7. MuJoCo torque sequence support test

## 当前边界

该测试仍不是完整动态 trot locomotion。

当前仍没有：

1. 实时 gait phase scheduler
2. qdd / tau 每步在线重求解
3. swing trajectory 与 full WBC 每步耦合
4. base velocity tracking
5. 连续前进速度
6. Jdot_v 非零项
7. ROS2/C++ 实时实现

## 下一步

建议生成 Stage 7 full WBC 最终更新总结。

建议文档：

docs/STAGE07_FULL_WBC_FINAL_UPDATE.md

随后可进入两条路线之一：

1. 继续 Stage 7：实现在线 MuJoCo full WBC step loop 原型
2. 工程化准备：整理 Python -> C++/ROS2 迁移清单
