# Stage 7 Final Update After Mode Sequence Test

## 状态

Stage 7 当前阶段性完成。

当前已完成从 contact force 到 actuator torque、WBC/QP、contact schedule、contact mode transition、swing trajectory、swing tracking 到多模式 swing tracking sequence 的完整前置验证链路。

当前仍不能宣称完成完整动态 trot locomotion。

## 已完成主线

1. QP contact force 到 actuator torque 映射
2. actuator torque 符号验证
3. torque support test
4. minimal WBC torque QP
5. base wrench tracking WBC/QP
6. WBC variant comparison
7. contact schedule-aware WBC/QP
8. contact schedule support test
9. contact mode transition jump check
10. torque ramp check
11. contact mode sequence ramp test
12. swing foot tracking QP
13. swing trajectory multi-knot QP
14. swing joint target sequence
15. single-mode conservative swing tracking
16. both-mode conservative swing tracking
17. conservative swing tracking mode sequence test

## 当前默认接口

leg order：

FR, FL, RR, RL

joint order：

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

默认文件：

results/logs_sample/stage07_contact_schedule_wbc_qp.csv

mode scale：

all_stance = 1.0

trot_FR_RL = 0.6

trot_FL_RR = 1.0

transition ramp：

ramp_steps = 5

## Contact Mode Sequence Ramp Test

sequence：

all_stance -> trot_FR_RL -> all_stance -> trot_FL_RR -> all_stance

结果：

total_steps = 1500

max_abs_roll = 0.096498358293

max_abs_pitch = 0.058977498277

max_tau_total_abs = 10.974863827195

max_cmd_step_jump_norm = 2.292707929380

max_cmd_step_jump_abs = 1.071268207495

saturation_steps = 0

pass = True

pass_margin = True

## Swing Trajectory 默认配置

默认文件：

results/logs_sample/stage07_swing_trajectory_qp_k9.csv

参数：

KNOTS = 9

TOTAL_DX = 0.03

CLEARANCE = 0.06

MAX_DQ = 0.12

W_SWING = 100.0

W_STANCE = 10.0

W_REG = 1e-4

结果：

trot_FR_RL pass = True

trot_FL_RR pass = True

mode_max_swing_error = 0.003524538255

mode_swing_relative_error_total = 0.096119524946

## Swing Tracking 默认保守配置

target_scale = 0.25

wbc_scale = 0.0

kp = 60.0

kd = 2.0

num_knots = 9

knot_hold_steps = 80

torque_limit = 23.7

## Single-Mode Swing Tracking 结果

### trot_FR_RL

final_z = 0.276571118100

min_z = 0.270531877762

max_abs_roll = 0.054958576417

max_abs_pitch = 0.036789337006

max_tau_total_abs = 8.320611628149

saturation_steps = 0

max_joint_error = 0.046307819443

pass = True

pass_margin = True

### trot_FL_RR

final_z = 0.281309818973

min_z = 0.271648210780

max_abs_roll = 0.071393714280

max_abs_pitch = 0.056675910934

max_tau_total_abs = 8.876493092716

saturation_steps = 0

max_joint_error = 0.043984959161

pass = True

pass_margin = True

## Multi-Mode Swing Tracking Sequence 结果

sequence：

trot_FR_RL -> trot_FL_RR -> trot_FR_RL

配置：

target_scale = 0.25

wbc_scale = 0.0

num_segments = 3

num_knots_per_segment = 9

knot_hold_steps = 80

total_steps = 2160

kp = 60.0

kd = 2.0

结果：

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

pass = True

pass_margin = True

## 已知失败配置

### Full target swing tracking

target_scale = 1.0

wbc_scale = 0.0

kp = 80.0

kd = 2.0

失败项：

max_abs_roll = 0.238817947944

max_abs_pitch = 0.152858965725

max_joint_error = 0.088734377819

pass = False

### Swing tracking with WBC feedforward

target_scale = 1.0

wbc_scale = 0.6

kp = 80.0

kd = 2.0

失败项：

max_abs_roll = 0.334634959885

max_abs_pitch = 0.193199850224

pass = False

## 当前结论

Stage 7 已完成以下前置验证：

1. contact schedule WBC/QP 可解
2. contact schedule WBC/QP 可支撑
3. contact mode 直接切换存在 torque jump
4. ramp_steps = 5 可压低 torque step jump
5. contact mode sequence ramp test 通过
6. swing trajectory QP 在 KNOTS = 9 下通过
7. swing joint target sequence 通过
8. conservative swing tracking 单模式通过
9. conservative swing tracking 多模式 sequence 通过

当前可认为 Stage 7 已完成保守动态切换前置验证。

## 当前边界

当前不是完整动态 trot locomotion。

尚未完成：

1. 真实 gait phase scheduler
2. swing tracking 与 WBC feedforward 同时稳定工作
3. base velocity tracking
4. full floating-base WBC dynamics
5. qdd / contact force / torque 联合优化
6. stance foot acceleration constraint
7. MuJoCo 中连续步态前进
8. ROS2 节点化
9. C++17 工程化迁移

## 下一阶段建议

建议继续 Stage 7，不进入 Stage 8 EKF。

优先级建议：

### 路线 A：继续控制算法

实现 full floating-base WBC dynamics 原型。

建议脚本：

scripts/stage07_full_wbc_dynamics_qp.py

目标：

1. 优化变量包含 qdd、contact force、tau
2. 加入 floating-base dynamics equality
3. 加入 stance foot acceleration constraint
4. 加入 torque limit
5. 加入 friction cone
6. 输出离线 QP 结果和残差

### 路线 B：工程化整理

整理 Python 原型到 C++/ROS2 的迁移清单。

建议文档：

docs/STAGE07_TO_CPP_ROS2_MIGRATION_PLAN.md

目标：

1. 明确核心模块
2. 明确输入输出接口
3. 明确数据结构
4. 明确 ROS2 topic/service 参数
5. 明确后续 C++ 单元测试清单

## 推荐下一步

优先选择路线 A：

scripts/stage07_full_wbc_dynamics_qp.py

原因：

当前 WBC 仍停留在 wrench/torque/kinematic tracking 原型层，尚未进入完整 floating-base dynamics WBC。
