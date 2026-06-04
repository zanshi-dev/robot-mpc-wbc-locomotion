# Stage 7：Swing Foot Tracking QP

## 状态

通过。

## 目标

实现 Stage 7 的 swing foot tracking QP 离线原型。

该版本只做运动学层 foot tracking，不接 MuJoCo 动态闭环，不代表完整 WBC swing task 已完成。

## 输出文件

results/logs_sample/stage07_swing_foot_tracking_qp.csv

## 支持 contact mode

trot_FR_RL：

stance legs = FR, RL

swing legs = FL, RR

trot_FL_RR：

stance legs = FL, RR

swing legs = FR, RL

## 优化变量

dq，12 维 actuated joint increment。

顺序：

FR_hip, FR_thigh, FR_calf,
FL_hip, FL_thigh, FL_calf,
RR_hip, RR_thigh, RR_calf,
RL_hip, RL_thigh, RL_calf

## 目标

swing legs：

使用 foot Jacobian 近似跟踪 foot delta。

期望 swing foot delta：

dx = 0.03

dy = 0.0

dz = 0.06

stance legs：

保持 dq 接近 0。

## 参数

SWING_DX = 0.03

SWING_DZ = 0.06

MAX_DQ = 0.35

W_SWING = 100.0

W_STANCE = 10.0

W_REG = 1e-4

## 结果

### trot_FR_RL

OSQP status = solved

swing legs = FL, RR

stance legs = FR, RL

max_abs_dq = 0.350000000000

swing_error_norm = 0.002170085432

swing_relative_error = 0.022874708942

max_stance_dq = 0.000000000000

pass = True

### trot_FL_RR

OSQP status = solved

swing legs = FR, RL

stance legs = FL, RR

max_abs_dq = 0.350000000000

swing_error_norm = 0.002170085432

swing_relative_error = 0.022874708942

max_stance_dq = 0.000000000000

pass = True

## 结论

swing foot tracking QP 离线原型已通过。

两种 trot contact mode 下，QP 均能生成 12 维 actuated joint increment，使 swing foot 近似达到期望位移，同时 stance legs 保持 dq 为 0。

当前结果说明 swing task 的运动学层 QP 可行。

## 注意

max_abs_dq 达到 MAX_DQ = 0.35，说明当前期望 swing delta 对单步关节增量约束较激进。

后续接入动态仿真前，需要将该结果改为多步 swing trajectory tracking，而不是单步大位移。

## 下一步

进入 Stage 7 下一小步：

实现 swing trajectory multi-knot tracking QP。

建议文件：

scripts/stage07_swing_trajectory_qp.py

目标：

1. 生成 5 个 swing knot
2. 每个 knot 的 dz 使用 parabolic clearance
3. 每个 knot 求解小 dq
4. 检查每步 max_abs_dq 是否明显小于 0.35
5. 输出 results/logs_sample/stage07_swing_trajectory_qp.csv
