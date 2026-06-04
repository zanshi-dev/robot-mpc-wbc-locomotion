# Stage 7：Swing Tracking Mode Sequence Test

## 状态

通过。

## 目标

验证保守 swing joint target tracking 配置在多个 trot contact mode 顺序切换下是否稳定。

该测试是动态 contact switching 前置验证，但仍不是完整动态 trot locomotion。

## 输入文件

results/logs_sample/stage07_swing_joint_target_sequence.csv

## 输出文件

results/logs_sample/stage07_swing_tracking_mode_sequence_test_log.csv

results/logs_sample/stage07_swing_tracking_mode_sequence_test_summary.csv

## Mode Sequence

trot_FR_RL -> trot_FL_RR -> trot_FR_RL

## 配置

target_scale = 0.25

wbc_scale = 0.0

num_segments = 3

num_knots_per_segment = 9

knot_hold_steps = 80

total_steps = 2160

kp = 60.0

kd = 2.0

torque_limit = 23.7

## 结果

initial_z = 0.284805846483

final_z = 0.281080409164

min_z = 0.270531877762

max_z = 0.287717440144

delta_z = -0.003725437320

final_roll = -0.003885722206

final_pitch = -0.006745218049

max_abs_roll = 0.072848128772

roll_margin_to_0p15 = 0.077151871228

max_abs_pitch = 0.048797294246

pitch_margin_to_0p15 = 0.101202705754

z_margin_to_0p22 = 0.050531877762

max_tau_total_abs = 8.913662330326

saturation_steps = 0

max_joint_error = 0.047515871120

max_swing_joint_error = 0.047515871120

max_stance_joint_error = 0.038855273920

min_swing_foot_z = 0.007720591022

max_swing_foot_z = 0.043955837312

pass = True

pass_margin = True

## 结论

保守 swing tracking mode sequence 测试通过。

当前可认为 Stage 7 已完成以下前置验证：

1. contact schedule WBC/QP
2. contact mode torque ramp
3. contact mode sequence ramp
4. swing trajectory QP
5. swing joint target sequence
6. 单模式 swing tracking
7. 多模式 swing tracking sequence

## 当前默认 swing sequence 配置

target_scale = 0.25

wbc_scale = 0.0

kp = 60.0

kd = 2.0

num_knots_per_segment = 9

knot_hold_steps = 80

## 边界

该结果仍不是完整动态 trot locomotion。

当前测试没有：

1. 使用 WBC feedforward torque
2. 使用 base velocity command
3. 使用 floating-base dynamics WBC
4. 使用 qdd / contact force / torque 联合优化
5. 使用真实 gait phase scheduler
6. 做 ROS2/C++ 实时控制

## 下一步

建议生成 Stage 7 最终更新总结。

后续路线可二选一：

1. 继续 Stage 7：实现 full floating-base WBC dynamics 原型
2. 进入工程化准备：把当前 Python 原型接口整理为 C++/ROS2 迁移清单
