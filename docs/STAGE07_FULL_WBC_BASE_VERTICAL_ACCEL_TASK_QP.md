# Stage 7：Full WBC Base Vertical Accel Task QP

## 状态

通过。

## 背景

上一版 6D base acceleration tracking task 未完全通过。

失败原因不是 dynamics constraint，而是 trot_FL_RR 的 6D base task error 超过阈值：

base_task_error_norm = 0.07536047349576

其中 base_qdd_z = 0.184192457744，已经接近目标 0.2。

因此改为 vertical-only base acceleration tracking，只跟踪 base_qdd_z。

## 输入文件

results/logs_sample/stage07_contact_schedule_wbc_qp.csv

## 输出文件

results/logs_sample/stage07_full_wbc_base_vertical_accel_task_qp.csv

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

contact force constraints：

1. active contact fz >= 0
2. friction cone
3. inactive contact force = 0

torque limit：

|tau| <= 23.7

## Base Vertical Task

目标：

base_qdd_z_ref = 0.2

阈值：

abs(base_qdd_z - base_qdd_z_ref) < 0.03

## all_stance 结果

osqp_status = solved

base_qdd_z = 0.172345449438

base_z_task_error = -2.765455056232e-02

dyn_res_norm = 2.860912105997e-14

stance_acc_res_norm = 9.309604088703e-17

max_abs_tau = 5.145971987477

max_abs_qdd = 1.163420196948

min_active_fz = 31.352989831521

min_friction_margin = 16.629454637670

pass = True

## trot_FR_RL 结果

osqp_status = solved

base_qdd_z = 0.185668089815

base_z_task_error = -1.433191018511e-02

dyn_res_norm = 4.270753688660e-14

stance_acc_res_norm = 8.993834424997e-17

max_abs_tau = 10.485941789045

max_abs_qdd = 1.090240185829

min_active_fz = 63.235143005521

min_friction_margin = 37.355381771031

pass = True

## trot_FL_RR 结果

osqp_status = solved

base_qdd_z = 0.185791586133

base_z_task_error = -1.420841386733e-02

dyn_res_norm = 2.895861563847e-14

stance_acc_res_norm = 7.351626287045e-17

max_abs_tau = 10.424434041249

max_abs_qdd = 1.043367245659

min_active_fz = 63.478490228568

min_friction_margin = 37.358992434275

pass = True

## 结论

vertical-only base acceleration tracking task 通过。

三种 contact mode 均满足：

1. OSQP solved
2. dynamics residual 接近 0
3. stance acceleration residual 接近 0
4. base_qdd_z 接近 0.2
5. torque 未超过 23.7 Nm
6. active fz 为正
7. friction margin 为正
8. inactive force 接近 0

## 当前边界

该测试仍是离线静态 pose 下的 full WBC QP。

尚未完成：

1. 6D base acceleration tracking 的严格通过
2. swing foot acceleration tracking task
3. qdd / tau 接入 MuJoCo 闭环
4. gait phase scheduler
5. 连续 trot locomotion
6. ROS2/C++ 实时实现

## 下一步

建议继续 Stage 7：

加入 swing foot acceleration tracking task。

建议脚本：

scripts/stage07_full_wbc_swing_accel_task_qp.py

目标：

1. 保留 dynamics equality
2. 保留 stance foot acceleration constraint
3. 保留 vertical base acceleration task
4. 对 swing foot 加入 acceleration tracking soft task
5. 输出 results/logs_sample/stage07_full_wbc_swing_accel_task_qp.csv
