# Stage 7：Full Floating-Base WBC Dynamics QP

## 状态

通过。

## 目标

实现 full floating-base WBC dynamics QP 离线原型。

该版本验证：

1. floating-base dynamics equality
2. qdd / contact force / tau 联合优化
3. torque limit
4. friction cone
5. inactive contact force = 0
6. dynamics residual

该测试不接 MuJoCo 闭环，不代表完整动态 trot locomotion。

## 输入文件

results/logs_sample/stage07_contact_schedule_wbc_qp.csv

## 输出文件

results/logs_sample/stage07_full_wbc_dynamics_qp.csv

## 优化变量

qdd：18 维

contact force：12 维

tau：12 维

总变量数：

42

## 动力学约束

形式：

M qdd + h = S^T tau + J^T f

实际求解中选定：

contact_sign = 1.0

即接触力进入广义力项为：

J^T f

## 通用参数

mu = 0.6

torque_limit = 23.7

FZ_MAX = 300.0

QDD_LIMIT = 200.0

## all_stance 结果

active legs = FR, FL, RR, RL

contact_sign = 1.0

OSQP status = solved

dyn_res_norm = 3.058654385954e-15

max_abs_tau = 5.056337446402

max_abs_qdd = 0.049978975600

qdd_norm = 0.103580173491

min_active_fz = 31.042853613639

min_friction_margin = 16.383104129701

inactive_force_norm = 0.000000000000e+00

tau_diff_norm = 0.788869182635

force_diff_norm = 4.630359089541

pass = True

## trot_FR_RL 结果

active legs = FR, RL

inactive legs = FL, RR

contact_sign = 1.0

OSQP status = solved

dyn_res_norm = 5.688431200954e-14

max_abs_tau = 10.336919898027

max_abs_qdd = 0.237866214144

qdd_norm = 0.358853665751

min_active_fz = 62.411789250330

min_friction_margin = 37.043123301078

inactive_force_norm = 2.927122837681e-19

tau_diff_norm = 1.453084210531

force_diff_norm = 1.704702662899

pass = True

## trot_FL_RR 结果

active legs = FL, RR

inactive legs = FR, RL

contact_sign = 1.0

OSQP status = solved

dyn_res_norm = 2.849909156386e-14

max_abs_tau = 10.276991490673

max_abs_qdd = 0.287407603927

qdd_norm = 0.374421940160

min_active_fz = 62.665557010073

min_friction_margin = 37.034076533927

inactive_force_norm = 2.911209529221e-19

tau_diff_norm = 1.445797911745

force_diff_norm = 1.810670486121

pass = True

## 结论

full floating-base WBC dynamics QP 离线原型通过。

当前已经从原先的 wrench / torque / kinematic tracking 原型，推进到包含 qdd、contact force、tau 的完整动力学等式 QP 原型。

三种 contact mode 均满足：

1. OSQP solved
2. dynamics residual 接近 0
3. torque 未超过 23.7 Nm
4. active fz 为正
5. friction margin 为正
6. inactive contact force 接近 0

## 当前边界

该测试仍是离线静态 pose 下的 dynamics QP。

尚未完成：

1. stance foot acceleration constraint
2. base acceleration tracking task
3. swing foot acceleration tracking task
4. qdd 积分到 MuJoCo 动态闭环
5. gait phase scheduler
6. 连续 trot locomotion
7. ROS2/C++ 实时实现

## 下一步

建议继续 Stage 7：

实现 stance foot acceleration constraint 版本。

建议脚本：

scripts/stage07_full_wbc_stance_constraint_qp.py

目标：

1. 在 full WBC dynamics QP 中加入 stance foot acceleration 约束
2. 约束形式：J_stance qdd + Jdot_v = 0
3. 离线检查 dynamics residual 和 stance acceleration residual
4. 输出 results/logs_sample/stage07_full_wbc_stance_constraint_qp.csv
