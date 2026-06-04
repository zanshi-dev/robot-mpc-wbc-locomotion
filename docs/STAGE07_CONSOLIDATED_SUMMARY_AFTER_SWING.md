# Stage 7 Consolidated Summary After Swing Tracking

## 状态

Stage 7 当前阶段性完成。

当前已完成：

1. WBC/QP 第一轮原型
2. base wrench tracking WBC/QP
3. contact schedule-aware WBC/QP
4. contact mode transition jump check
5. torque ramp check
6. contact mode sequence ramp test
7. swing foot tracking QP
8. swing trajectory multi-knot QP
9. swing joint target sequence
10. swing joint target tracking conservative test

当前仍不是完整动态 trot locomotion。

## 默认接口约定

leg order：

FR, FL, RR, RL

joint order per leg：

hip, thigh, calf

torque order：

MuJoCo actuator order

force-to-torque sign：

tau = -J^T f

standing pose：

每条腿 [0.0, 0.9, -1.8]

torque limit：

23.7 Nm

## Contact Schedule WBC 默认配置

默认 contact schedule WBC 输出：

results/logs_sample/stage07_contact_schedule_wbc_qp.csv

mode scale：

all_stance = 1.0

trot_FR_RL = 0.6

trot_FL_RR = 1.0

transition ramp：

ramp_steps = 5

## Contact Mode Sequence Ramp Test

测试 sequence：

all_stance -> trot_FR_RL -> all_stance -> trot_FL_RR -> all_stance

segment_steps = 300

total_steps = 1500

ramp_steps = 5

结果：

final_z = 0.294798253254

min_z = 0.284805846483

max_abs_roll = 0.096498358293

max_abs_pitch = 0.058977498277

max_tau_total_abs = 10.974863827195

max_cmd_step_jump_norm = 2.292707929380

max_cmd_step_jump_abs = 1.071268207495

saturation_steps = 0

pass = True

pass_margin = True

## Swing Trajectory QP 默认配置

默认输出：

results/logs_sample/stage07_swing_trajectory_qp_k9.csv

默认参数：

KNOTS = 9

TOTAL_DX = 0.03

CLEARANCE = 0.06

MAX_DQ = 0.12

W_SWING = 100.0

W_STANCE = 10.0

W_REG = 1e-4

结果：

trot_FR_RL：

mode_pass = True

mode_max_abs_dq = 0.120000000000

mode_max_swing_error = 0.003524538255

mode_max_stance_dq = 0.000000000000

mode_swing_relative_error_total = 0.096119524946

trot_FL_RR：

mode_pass = True

mode_max_abs_dq = 0.120000000000

mode_max_swing_error = 0.003524538255

mode_max_stance_dq = 0.000000000000

mode_swing_relative_error_total = 0.096119524946

## Swing Joint Target Sequence

默认输出：

results/logs_sample/stage07_swing_joint_target_sequence.csv

结果：

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

## Swing Tracking 默认保守配置

当前默认保守 swing tracking 配置：

target_scale = 0.25

wbc_scale = 0.0

kp = 60.0

kd = 2.0

torque_limit = 23.7

num_knots = 9

knot_hold_steps = 80

### trot_FR_RL 结果

swing legs = FL, RR

stance legs = FR, RL

final_z = 0.276571118100

min_z = 0.270531877762

max_abs_roll = 0.054958576417

max_abs_pitch = 0.036789337006

max_tau_total_abs = 8.320611628149

saturation_steps = 0

max_joint_error = 0.046307819443

pass = True

pass_margin = True

### trot_FL_RR 结果

swing legs = FR, RL

stance legs = FL, RR

final_z = 0.281309818973

min_z = 0.271648210780

max_abs_roll = 0.071393714280

max_abs_pitch = 0.056675910934

max_tau_total_abs = 8.876493092716

saturation_steps = 0

max_joint_error = 0.043984959161

pass = True

pass_margin = True

## 已知失败配置

### 完整 swing target tracking

target_scale = 1.0

wbc_scale = 0.0

kp = 80.0

kd = 2.0

结果：

max_abs_roll = 0.238817947944

max_abs_pitch = 0.152858965725

max_joint_error = 0.088734377819

pass = False

### swing tracking with WBC feedforward

target_scale = 1.0

wbc_scale = 0.6

kp = 80.0

kd = 2.0

结果：

max_abs_roll = 0.334634959885

max_abs_pitch = 0.193199850224

pass = False

## 当前结论

Stage 7 已完成 WBC/QP 与 swing tracking 的离线和短时 MuJoCo 前置验证。

当前可作为默认的稳定配置：

1. contact schedule WBC：all_stance = 1.0, trot_FR_RL = 0.6, trot_FL_RR = 1.0
2. contact mode transition ramp：ramp_steps = 5
3. swing trajectory QP：KNOTS = 9
4. swing tracking：target_scale = 0.25, wbc_scale = 0.0, kp = 60.0, kd = 2.0

## 当前边界

当前不能宣称完成动态 trot locomotion。

尚未完成：

1. 动态 contact switching 下的 swing tracking
2. swing tracking 与 WBC feedforward 同时稳定工作
3. base velocity tracking
4. full floating-base WBC dynamics
5. qdd / contact force / torque 联合优化
6. stance foot acceleration constraint
7. ROS2 节点化
8. C++17 工程化迁移

## 下一步建议

继续 Stage 7。

建议下一小步：

实现 conservative swing tracking + contact mode switching sequence test。

目标：

1. 使用 target_scale = 0.25
2. 使用 wbc_scale = 0.0
3. 使用 kp = 60.0, kd = 2.0
4. sequence：trot_FR_RL -> trot_FL_RR -> trot_FR_RL
5. 每个 mode 内执行 9-knot swing target tracking
6. 检查 base_z、roll、pitch、joint_error、torque saturation

建议脚本：

scripts/stage07_swing_tracking_mode_sequence_test.py

建议输出：

results/logs_sample/stage07_swing_tracking_mode_sequence_test_log.csv

results/logs_sample/stage07_swing_tracking_mode_sequence_test_summary.csv
