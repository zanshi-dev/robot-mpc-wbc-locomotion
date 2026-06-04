# Stage 7：Swing Tracking Recommended Test Both Modes

## 状态

通过。

## 目标

验证保守 swing joint target tracking 配置是否同时适用于两种 trot 对角模式：

1. trot_FR_RL
2. trot_FL_RR

## 推荐配置

target_scale = 0.25

wbc_scale = 0.0

kp = 60.0

kd = 2.0

torque_limit = 23.7

num_knots = 9

knot_hold_steps = 80

## trot_FR_RL 结果

swing legs = FL, RR

stance legs = FR, RL

total_steps = 720

initial_z = 0.284805846483

final_z = 0.276571118100

min_z = 0.270531877762

max_abs_roll = 0.054958576417

max_abs_pitch = 0.036789337006

max_tau_total_abs = 8.320611628149

saturation_steps = 0

max_joint_error = 0.046307819443

max_swing_joint_error = 0.046307819443

max_stance_joint_error = 0.038460784738

pass = True

pass_margin = True

## trot_FL_RR 结果

swing legs = FR, RL

stance legs = FL, RR

total_steps = 720

initial_z = 0.284805846483

final_z = 0.281309818973

min_z = 0.271648210780

max_abs_roll = 0.071393714280

max_abs_pitch = 0.056675910934

max_tau_total_abs = 8.876493092716

saturation_steps = 0

max_joint_error = 0.043984959161

max_swing_joint_error = 0.043984959161

max_stance_joint_error = 0.031636404627

pass = True

pass_margin = True

## 结论

两种 trot 对角模式下，保守 swing joint target tracking 均通过。

当前 Stage 7 的默认保守 swing tracking 配置为：

target_scale = 0.25

wbc_scale = 0.0

kp = 60.0

kd = 2.0

该配置可作为后续动态 contact switching + swing tracking 的起点。

## 边界

该结果仍不是完整动态 trot locomotion。

当前验证的是：

standing base 下，单一 contact mode 内的 swing joint target tracking。

尚未验证：

1. 两种 trot mode 之间动态切换
2. swing tracking 与 contact schedule WBC 同时工作
3. base velocity tracking
4. full WBC dynamics
5. ROS2/C++ 实时实现

## 下一步

建议进入 Stage 7 阶段再总结，更新默认配置：

1. contact schedule WBC 默认 scale
2. transition ramp 默认 steps
3. swing trajectory QP 默认 KNOTS
4. swing tracking 默认 target_scale/kp/kd
5. 已失败配置和边界
