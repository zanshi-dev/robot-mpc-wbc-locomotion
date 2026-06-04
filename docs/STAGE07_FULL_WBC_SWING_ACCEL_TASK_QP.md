# Stage 7：Full WBC Swing Accel Task QP

## 状态

通过。

## 目标

在 full WBC dynamics QP 中加入 swing foot acceleration tracking soft task。

该版本包含：

1. floating-base dynamics equality
2. stance foot acceleration constraint
3. base vertical acceleration tracking task
4. swing foot acceleration tracking task
5. torque limit
6. friction cone
7. inactive contact force = 0

该测试仍是离线静态 pose 下的 QP，不接 MuJoCo 闭环。

## 输入文件

results/logs_sample/stage07_contact_schedule_wbc_qp.csv

## 输出文件

results/logs_sample/stage07_full_wbc_swing_accel_task_qp.csv

## 优化变量

qdd = 18 维

contact force = 12 维

tau = 12 维

num_vars = 42

## 约束

动力学约束：

M qdd + h = S^T tau + J^T f

stance foot acceleration constraint：

J_stance qdd = 0

contact constraints：

1. active contact fz >= 0
2. friction cone
3. inactive contact force = 0

torque limit：

|tau| <= 23.7

## Base Vertical Task

base_qdd_z_ref = 0.2

## Swing Acceleration Task

swing_acc_ref = [0.4, 0.0, 0.8]

任务形式：

J_swing qdd ≈ swing_acc_ref

当前 standing pose 且 qvel = 0，因此暂不加入 Jdot_v 项。

## trot_FR_RL 结果

stance legs = FR, RL

swing legs = FL, RR

osqp_status = solved

base_qdd_z = 0.215789494368

base_z_task_error = 1.578949436807e-02

swing_acc_error_norm = 1.227426649713e-01

swing_acc_error_max_abs = 8.578944289191e-02

dyn_res_norm = 4.281617822997e-14

stance_acc_res_norm = 1.152775633689e-16

max_abs_tau = 10.545880364253

max_abs_qdd = 2.910331019188

min_active_fz = 63.530428891910

min_friction_margin = 37.533924480127

inactive_force_norm = 3.987469546604e-20

pass = True

## trot_FL_RR 结果

stance legs = FL, RR

swing legs = FR, RL

osqp_status = solved

base_qdd_z = 0.215607732660

base_z_task_error = 1.560773265970e-02

swing_acc_error_norm = 1.218506194838e-01

swing_acc_error_max_abs = 8.880804591198e-02

dyn_res_norm = 4.286630305818e-14

stance_acc_res_norm = 1.083889877283e-16

max_abs_tau = 10.480313206115

max_abs_qdd = 3.026505313002

min_active_fz = 63.784137690160

min_friction_margin = 37.526106825020

inactive_force_norm = 3.911866994703e-20

pass = True

## 结论

full WBC swing foot acceleration tracking task 通过。

当前 full WBC QP 已包含：

1. qdd / contact force / tau 联合优化
2. floating-base dynamics equality
3. stance foot acceleration constraint
4. base vertical acceleration tracking
5. swing foot acceleration tracking
6. torque limit
7. friction cone
8. inactive contact force 约束

两种 trot contact mode 均通过。

## 当前边界

该测试仍是离线静态 pose 下的 QP。

尚未完成：

1. Jdot_v 非零项
2. qdd 积分到 MuJoCo
3. torque 闭环仿真
4. gait phase scheduler
5. 连续 trot locomotion
6. ROS2/C++ 实时实现

## 下一步

建议生成 Stage 7 full WBC 最新总结。

建议文档：

docs/STAGE07_FULL_WBC_SUMMARY.md

内容：

1. full WBC dynamics QP
2. stance constraint QP
3. base vertical acceleration task QP
4. swing acceleration task QP
5. 当前默认 full WBC 离线配置
6. 下一步 MuJoCo torque closed-loop 接入路线
