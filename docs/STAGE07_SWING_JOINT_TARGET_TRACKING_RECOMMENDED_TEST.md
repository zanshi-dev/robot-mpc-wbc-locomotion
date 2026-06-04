# Stage 7：Swing Joint Target Tracking Recommended Test

## 状态

通过。

## 背景

完整 swing target tracking 测试未通过：

max_abs_roll = 0.238817947944

max_abs_pitch = 0.152858965725

max_joint_error = 0.088734377819

pass = False

加入 trot_FR_RL WBC feedforward 后仍未通过，并且姿态更差：

wbc_scale = 0.6

max_abs_roll = 0.334634959885

max_abs_pitch = 0.193199850224

pass = False

因此执行稳定性 sweep。

## Sweep 结果

sweep 文件：

results/logs_sample/stage07_swing_tracking_stability_sweep.csv

测试组合数：

96

pass_cases = 11

pass_margin_cases = 22

推荐配置：

target_scale = 0.25

wbc_scale = 0.0

kp = 60.0

kd = 2.0

## 推荐配置复现实验

脚本：

scripts/stage07_swing_joint_target_tracking_recommended_test.py

输入文件：

results/logs_sample/stage07_swing_joint_target_sequence.csv

输出文件：

results/logs_sample/stage07_swing_joint_target_tracking_recommended_test_log.csv

results/logs_sample/stage07_swing_joint_target_tracking_recommended_test_summary.csv

## 测试模式

mode = trot_FR_RL

swing legs = FL, RR

stance legs = FR, RL

num_knots = 9

knot_hold_steps = 80

total_steps = 720

## 控制参数

target_scale = 0.25

wbc_scale = 0.0

kp = 60.0

kd = 2.0

torque_limit = 23.7

## 结果

initial_z = 0.284805846483

final_z = 0.276571118100

min_z = 0.270531877762

max_z = 0.284893289428

delta_z = -0.008234728383

final_roll = -0.001430520594

final_pitch = 0.001733127161

max_abs_roll = 0.054958576417

roll_margin_to_0p15 = 0.095041423583

max_abs_pitch = 0.036789337006

pitch_margin_to_0p15 = 0.113210662994

z_margin_to_0p22 = 0.050531877762

max_tau_total_abs = 8.320611628149

saturation_steps = 0

max_joint_error = 0.046307819443

max_swing_joint_error = 0.046307819443

max_stance_joint_error = 0.038460784738

min_swing_foot_z = 0.007720591022

max_swing_foot_z = 0.035251183427

pass = True

pass_margin = True

## 结论

保守 swing joint target tracking 短时测试通过。

当前可用配置为：

target_scale = 0.25

wbc_scale = 0.0

kp = 60.0

kd = 2.0

该结果说明 swing joint target sequence 可以在 MuJoCo 中被 PD 稳定跟踪，但必须使用缩小后的 swing target。

## 当前边界

该结果不是完整动态 trot locomotion。

当前通过的是：

standing base 下的保守 swing joint target tracking 短时测试。

当前没有通过的是：

1. target_scale = 1.0 的完整 swing target tracking
2. wbc_scale = 0.6 的 swing tracking with WBC
3. 动态 contact switching 下的 swing tracking
4. base velocity tracking
5. full WBC dynamics

## 下一步

建议进入 Stage 7 阶段再总结，固化：

1. contact schedule WBC 默认配置
2. swing trajectory QP 默认配置
3. swing tracking recommended 默认配置
4. 当前失败配置和边界

然后再决定是否继续：

1. 扩展到 trot_FL_RR 的 recommended tracking test
2. 做 target_scale sweep 的更精细版本
3. 开始 full WBC dynamics
