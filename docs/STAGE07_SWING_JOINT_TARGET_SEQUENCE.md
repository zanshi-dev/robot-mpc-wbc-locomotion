# Stage 7：Swing Joint Target Sequence

## 状态

通过。

## 目标

将 KNOTS = 9 的 swing trajectory QP 输出转换为 swing joint target sequence。

该步骤用于把每个 knot 的 dq 累加为 q_target，为后续 MuJoCo swing leg PD tracking 做准备。

## 输入文件

results/logs_sample/stage07_swing_trajectory_qp_k9.csv

## 输出文件

results/logs_sample/stage07_swing_joint_target_sequence.csv

## 支持 contact mode

trot_FR_RL：

swing legs = FL, RR

stance legs = FR, RL

trot_FL_RR：

swing legs = FR, RL

stance legs = FL, RR

## 初始关节角

每条腿 standing pose：

hip = 0.0

thigh = 0.9

calf = -1.8

## 离线关节范围检查

hip：

[-1.2, 1.2]

thigh：

[-0.8, 2.2]

calf：

[-2.8, -0.4]

## 结果

modes = trot_FR_RL, trot_FL_RR

num_rows = 18

all_pass = True

trot_FR_RL：

last_knot = 8

max_abs_delta_from_standing = 0.111288270613

last_pass = True

trot_FL_RR：

last_knot = 8

max_abs_delta_from_standing = 0.111288270613

last_pass = True

## 结论

swing joint target sequence 转换通过。

KNOTS = 9 的 swing trajectory QP 结果可以转换为每个 knot 的 q_target。

所有 q_target 均在保守关节范围内。

最大相对 standing pose 的关节偏移为 0.111288270613 rad，属于保守范围。

## 当前边界

该结果仍是离线 joint target sequence。

尚未接入 MuJoCo swing leg PD tracking。

尚未验证动态步态切换时 swing foot 是否跟踪该 q_target sequence。

## 下一步

进入 Stage 7 下一小步：

实现 MuJoCo swing leg PD tracking 短时测试。

建议文件：

scripts/stage07_swing_joint_target_tracking_test.py

输入文件：

results/logs_sample/stage07_swing_joint_target_sequence.csv

测试目标：

1. 选择 trot_FR_RL 模式
2. stance legs 保持 standing pose
3. swing legs 按 9 个 knot 的 q_target 执行 PD tracking
4. 每个 knot 保持固定 steps
5. 记录 base_z、roll、pitch、swing joint error、torque saturation
6. 输出 results/logs_sample/stage07_swing_joint_target_tracking_test_summary.csv
