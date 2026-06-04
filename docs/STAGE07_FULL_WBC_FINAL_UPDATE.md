# Stage 7 Full WBC Final Update

## 状态

Stage 7 full WBC 原型阶段性完成。

当前已经完成：

1. full floating-base dynamics QP
2. stance foot acceleration constraint QP
3. base vertical acceleration tracking task QP
4. swing foot acceleration tracking task QP
5. torque reconstruction check
6. torque ramp check
7. MuJoCo torque sequence support test

当前仍不是完整动态 trot locomotion。

## 核心接口

leg order：

FR, FL, RR, RL

joint order：

hip, thigh, calf

torque order：

MuJoCo actuator order

contact force order：

FR_fx, FR_fy, FR_fz,
FL_fx, FL_fy, FL_fz,
RR_fx, RR_fy, RR_fz,
RL_fx, RL_fy, RL_fz

动力学形式：

M qdd + h = S^T tau + J^T f

contact_sign = 1.0

## Full WBC 优化变量

qdd = 18 维

contact force = 12 维

tau = 12 维

num_vars = 42

## Full WBC 当前默认配置

约束：

1. floating-base dynamics equality
2. stance foot acceleration constraint
3. torque limit
4. active contact fz >= 0
5. friction cone
6. inactive contact force = 0

soft task：

1. base vertical acceleration tracking
2. swing foot acceleration tracking
3. qdd regularization
4. force reference tracking
5. torque reference tracking

默认参数：

mu = 0.6

torque_limit = 23.7

base_qdd_z_ref = 0.2

swing_acc_ref = [0.4, 0.0, 0.8]

推荐 ramp_steps = 5

## 已完成文件

### Full WBC Dynamics QP

脚本：

scripts/stage07_full_wbc_dynamics_qp.py

输出：

results/logs_sample/stage07_full_wbc_dynamics_qp.csv

结论：

all_stance、trot_FR_RL、trot_FL_RR 均通过。

### Full WBC Stance Constraint QP

脚本：

scripts/stage07_full_wbc_stance_constraint_qp.py

输出：

results/logs_sample/stage07_full_wbc_stance_constraint_qp.csv

结论：

加入 J_stance qdd = 0 后，三种 contact mode 均通过。

### Full WBC Base Vertical Accel Task QP

脚本：

scripts/stage07_full_wbc_base_vertical_accel_task_qp.py

输出：

results/logs_sample/stage07_full_wbc_base_vertical_accel_task_qp.csv

结论：

vertical-only base acceleration tracking task 通过。

### Full WBC Swing Accel Task QP

脚本：

scripts/stage07_full_wbc_swing_accel_task_qp.py

输出：

results/logs_sample/stage07_full_wbc_swing_accel_task_qp.csv

结论：

两种 trot contact mode 均通过。

trot_FR_RL：

base_qdd_z = 0.215789494368

swing_acc_error_norm = 1.227426649713e-01

max_abs_tau = 10.545880364253

pass = True

trot_FL_RR：

base_qdd_z = 0.215607732660

swing_acc_error_norm = 1.218506194838e-01

max_abs_tau = 10.480313206115

pass = True

### Torque Reconstruction Check

脚本：

scripts/stage07_full_wbc_torque_reconstruction_check.py

输出：

results/logs_sample/stage07_full_wbc_torque_reconstruction_check.csv

结论：

full WBC 单模式 torque 合法。

trot_FR_RL：

max_abs_tau_full_wbc = 10.545880364253

tau_diff_norm_vs_contact_wbc = 1.390773536447

torque_limit_pass = True

trot_FL_RR：

max_abs_tau_full_wbc = 10.480313206115

tau_diff_norm_vs_contact_wbc = 1.375153606606

torque_limit_pass = True

直接 mode 切换 torque jump 过大，需要 smoothing。

### Torque Ramp Check

脚本：

scripts/stage07_full_wbc_torque_ramp_check.py

输出：

results/logs_sample/stage07_full_wbc_torque_ramp_check.csv

结果：

recommended_ramp_steps = 3

但进入 MuJoCo 闭环时建议使用更保守的：

ramp_steps = 5

ramp_steps = 5：

max_step_jump_norm = 4.746000978862

max_step_jump_abs = 2.164602488251

pass = True

### Torque Sequence Support Test

脚本：

scripts/stage07_full_wbc_torque_sequence_support_test.py

输出：

results/logs_sample/stage07_full_wbc_torque_sequence_support_test_log.csv

results/logs_sample/stage07_full_wbc_torque_sequence_support_test_summary.csv

sequence：

trot_FR_RL -> trot_FL_RR -> trot_FR_RL

配置：

segment_steps = 300

num_segments = 3

total_steps = 900

ramp_steps = 5

kp = 80.0

kd = 2.0

torque_limit = 23.7

结果：

initial_z = 0.284805846483

final_z = 0.302695944706

min_z = 0.284782520542

max_z = 0.315369147929

delta_z = 0.017890098222

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

## 关键结论

Stage 7 full WBC 离线 QP 结构已经打通。

full WBC torque 经过 ramp smoothing 后，已经可以在 MuJoCo 中完成短时多模式 torque sequence support test。

这说明当前 WBC 的 torque 输出方向、符号、约束、力矩范围、mode 切换平滑策略均通过前置验证。

## 已知失败项

6D base acceleration tracking task 未完全通过。

失败模式：

trot_FL_RR

失败指标：

base_task_error_norm = 0.07536047349576

当前处理：

采用 vertical-only base acceleration tracking。

## 当前边界

当前仍不能宣称完成动态 trot locomotion。

尚未完成：

1. 每个仿真步在线求解 full WBC QP
2. gait phase scheduler
3. swing trajectory 与 full WBC 在线耦合
4. base velocity tracking
5. 连续前进速度
6. Jdot_v 非零项
7. qdd 积分策略
8. foot touchdown / liftoff 状态机
9. ROS2/C++ 实时迁移
10. 硬件接口与安全保护

## 下一步路线

建议继续 Stage 7，进入在线 MuJoCo full WBC step loop 原型。

建议脚本：

scripts/stage07_online_full_wbc_step_loop_proto.py

目标：

1. 每个仿真步读取 q、qd
2. 根据简化 gait phase 选择 contact mode
3. 每步在线求解 full WBC QP
4. 使用 ramp / low-pass 平滑 tau
5. 发送 torque 到 MuJoCo
6. 记录 base_z、roll、pitch、tau、mode、QP status
7. 先做原地 trot support，不引入前进速度

建议输出：

results/logs_sample/stage07_online_full_wbc_step_loop_proto_log.csv

results/logs_sample/stage07_online_full_wbc_step_loop_proto_summary.csv
