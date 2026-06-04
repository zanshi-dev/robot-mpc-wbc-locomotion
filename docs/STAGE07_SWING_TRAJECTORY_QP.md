# Stage 7：Swing Trajectory Multi-Knot QP

## 状态

通过。

## 背景

上一版 KNOTS = 5 未通过。

失败原因：

首尾 knot 的 swing dz 较大，导致 max_abs_dq 达到 MAX_DQ = 0.12，且 swing_error 较大。

KNOTS = 5 结果：

mode_pass = False

mode_max_abs_dq = 0.120000000000

mode_max_swing_error = 0.017592848125

mode_swing_relative_error_total = 0.390610313004

因此改为 KNOTS = 9。

## 输入

Go1 MuJoCo model：

assets/go1/scene.xml

## 输出文件

results/logs_sample/stage07_swing_trajectory_qp_k9.csv

## 支持 contact mode

trot_FR_RL：

stance legs = FR, RL

swing legs = FL, RR

trot_FL_RR：

stance legs = FL, RR

swing legs = FR, RL

## 优化变量

每个 knot 求解 12 维 actuated joint increment：

dq

顺序：

FR_hip, FR_thigh, FR_calf,
FL_hip, FL_thigh, FL_calf,
RR_hip, RR_thigh, RR_calf,
RL_hip, RL_thigh, RL_calf

## 轨迹参数

KNOTS = 9

TOTAL_DX = 0.03

CLEARANCE = 0.06

MAX_DQ = 0.12

## 目标函数

swing legs：

使用 foot Jacobian 近似跟踪每个 knot 的 foot delta。

stance legs：

保持 dq 接近 0。

权重：

W_SWING = 100.0

W_STANCE = 10.0

W_REG = 1e-4

## 结果

### trot_FR_RL

OSQP status = solved for all knots

mode_pass = True

mode_max_abs_dq = 0.120000000000

mode_max_swing_error = 0.003524538255

mode_max_stance_dq = 0.000000000000

mode_swing_relative_error_total = 0.096119524946

### trot_FL_RR

OSQP status = solved for all knots

mode_pass = True

mode_max_abs_dq = 0.120000000000

mode_max_swing_error = 0.003524538255

mode_max_stance_dq = 0.000000000000

mode_swing_relative_error_total = 0.096119524946

## 结论

KNOTS = 9 的 swing trajectory multi-knot QP 通过。

相比 KNOTS = 5：

1. swing relative error 从 0.390610313004 降到 0.096119524946
2. max_swing_error 从 0.017592848125 降到 0.003524538255
3. 两种 trot contact mode 均通过
4. stance legs dq 保持为 0

## 当前默认配置

后续 swing trajectory 离线原型默认使用：

KNOTS = 9

TOTAL_DX = 0.03

CLEARANCE = 0.06

MAX_DQ = 0.12

## 注意

mode_max_abs_dq 仍等于 MAX_DQ = 0.12，说明轨迹首尾 knot 仍触及 dq 限制。

后续若接入 MuJoCo 动态测试，可优先考虑：

1. 增加 KNOTS 到 11 或 13
2. 降低 CLEARANCE 到 0.04
3. 使用更平滑的 swing height profile
4. 将 dq 转换为 desired joint trajectory，而不是直接作为 torque 输入

## 下一步

进入 Stage 7 下一小步：

把 KNOTS = 9 的 swing trajectory QP 结果转换为 swing joint target sequence。

建议文件：

scripts/stage07_swing_joint_target_sequence.py

输出文件：

results/logs_sample/stage07_swing_joint_target_sequence.csv

目标：

1. 从 standing pose 开始累计 dq
2. 输出每个 knot 的 q_target
3. 检查 q_target 是否在合理范围
4. 为后续 MuJoCo swing leg PD tracking 做准备
