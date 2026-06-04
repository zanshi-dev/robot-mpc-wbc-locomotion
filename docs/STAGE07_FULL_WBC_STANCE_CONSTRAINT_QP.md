# Stage 7：Full WBC Stance Constraint QP

## 状态

通过。

## 目标

在 full floating-base WBC dynamics QP 中加入 stance foot acceleration constraint。

该版本验证：

1. floating-base dynamics equality
2. qdd / contact force / tau 联合优化
3. stance foot acceleration constraint
4. torque limit
5. friction cone
6. inactive contact force = 0
7. dynamics residual
8. stance acceleration residual

该测试仍是离线静态 pose 下的 QP，不接 MuJoCo 闭环。

## 输入文件

results/logs_sample/stage07_contact_schedule_wbc_qp.csv

## 输出文件

results/logs_sample/stage07_full_wbc_stance_constraint_qp.csv

## 优化变量

qdd：18 维

contact force：12 维

tau：12 维

总变量数：

42

## 动力学约束

M qdd + h = S^T tau + J^T f

contact_sign = 1.0

## Stance Constraint

约束形式：

J_stance qdd + Jdot_v = 0

当前测试条件：

standing pose

qvel = 0

因此：

Jdot_v = 0

实际约束：

J_stance qdd = 0

## 通用参数

mu = 0.6

torque_limit = 23.7

FZ_MAX = 300.0

QDD_LIMIT = 200.0

## all_stance 结果

active legs = FR, FL, RR, RL

num_stance_acc_constraints = 12

OSQP status = solved

dyn_res_norm = 4.269244035819e-14

stance_acc_res_norm = 1.820685054950e-17

max_abs_tau = 5.056128534904

max_abs_qdd = 0.174930174361

qdd_norm = 0.390166338134

min_active_fz = 30.878492208576

min_friction_margin = 16.247430142308

inactive_force_norm = 0.000000000000e+00

tau_diff_norm = 0.812890587364

force_diff_norm = 4.644238904760

pass = True

## trot_FR_RL 结果

active legs = FR, RL

inactive legs = FL, RR

num_stance_acc_constraints = 6

OSQP status = solved

dyn_res_norm = 2.849499368786e-14

stance_acc_res_norm = 8.212071048565e-18

max_abs_tau = 10.324397106159

max_abs_qdd = 0.238522198748

qdd_norm = 0.515418509308

min_active_fz = 62.200201091565

min_friction_margin = 36.987165454619

inactive_force_norm = 1.509204993298e-19

tau_diff_norm = 1.463971912180

force_diff_norm = 1.670091465071

pass = True

## trot_FL_RR 结果

active legs = FL, RR

inactive legs = FR, RL

num_stance_acc_constraints = 6

OSQP status = solved

dyn_res_norm = 5.691957168469e-14

stance_acc_res_norm = 4.277421474636e-17

max_abs_tau = 10.258608734845

max_abs_qdd = 0.315153457848

qdd_norm = 0.680867656069

min_active_fz = 62.435743500332

min_friction_margin = 36.963058171493

inactive_force_norm = 1.499313846175e-19

tau_diff_norm = 1.457197420730

force_diff_norm = 1.766089650262

pass = True

## 结论

加入 stance foot acceleration constraint 后，full WBC dynamics QP 仍然通过。

三种 contact mode 均满足：

1. OSQP solved
2. dynamics residual 接近 0
3. stance acceleration residual 接近 0
4. torque 未超过 23.7 Nm
5. active fz 为正
6. friction margin 为正
7. inactive contact force 接近 0

这一步说明 full WBC 已从纯动力学等式推进到包含 stance kinematic constraint 的动力学 QP 原型。

## 当前边界

当前测试仍是离线 standing pose 条件。

尚未完成：

1. base acceleration tracking task
2. swing foot acceleration tracking task
3. qdd 积分或 torque 接入 MuJoCo 闭环
4. gait phase scheduler
5. 连续 trot locomotion
6. ROS2/C++ 实时实现

## 下一步

建议继续 Stage 7：

加入 base acceleration tracking task。

建议脚本：

scripts/stage07_full_wbc_base_accel_task_qp.py

目标：

1. 在当前 dynamics + stance constraint 基础上加入 base qdd reference
2. 测试 base vertical acceleration 或 roll/pitch stabilization
3. 检查 dynamics residual、stance residual、torque、friction margin
4. 输出 results/logs_sample/stage07_full_wbc_base_accel_task_qp.csv
