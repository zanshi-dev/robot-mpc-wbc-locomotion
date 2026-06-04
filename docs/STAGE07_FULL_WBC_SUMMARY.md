# Stage 7 Full WBC Summary

## 状态

Stage 7 full WBC 离线原型阶段性完成。

当前已经完成从 contact schedule WBC 到 full floating-base dynamics WBC 的离线验证链路。

当前仍不是完整动态 trot locomotion。

## 已完成 full WBC 子步骤

1. full floating-base WBC dynamics QP
2. full WBC stance foot acceleration constraint QP
3. full WBC base vertical acceleration task QP
4. full WBC swing foot acceleration task QP

## 默认接口

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

force-to-generalized-force sign：

M qdd + h = S^T tau + J^T f

contact_sign = 1.0

## 优化变量

qdd = 18 维

contact force = 12 维

tau = 12 维

num_vars = 42

## 通用约束

### Dynamics equality

M qdd + h = S^T tau + J^T f

### Stance foot acceleration constraint

J_stance qdd = 0

当前 standing pose 且 qvel = 0，因此暂未加入非零 Jdot_v。

### Torque limit

|tau| <= 23.7

### Contact constraints

active contact：

fz >= 0

friction cone：

|fx| <= mu fz

|fy| <= mu fz

inactive contact：

fx = 0

fy = 0

fz = 0

## 通用参数

mu = 0.6

torque_limit = 23.7

FZ_MAX = 300.0

QDD_LIMIT = 200.0

## Full WBC Dynamics QP

输出文件：

results/logs_sample/stage07_full_wbc_dynamics_qp.csv

结果：

all_stance pass = True

trot_FR_RL pass = True

trot_FL_RR pass = True

结论：

包含 qdd、contact force、tau 的 full floating-base dynamics equality QP 可解，且 dynamics residual 接近 0。

## Full WBC Stance Constraint QP

输出文件：

results/logs_sample/stage07_full_wbc_stance_constraint_qp.csv

结果：

all_stance pass = True

trot_FR_RL pass = True

trot_FL_RR pass = True

关键残差：

all_stance stance_acc_res_norm = 1.820685054950e-17

trot_FR_RL stance_acc_res_norm = 8.212071048565e-18

trot_FL_RR stance_acc_res_norm = 4.277421474636e-17

结论：

加入 stance foot acceleration constraint 后，三种 contact mode 均可解。

## Full WBC Base Vertical Accel Task QP

输出文件：

results/logs_sample/stage07_full_wbc_base_vertical_accel_task_qp.csv

目标：

base_qdd_z_ref = 0.2

结果：

all_stance:

base_qdd_z = 0.172345449438

base_z_task_error = -2.765455056232e-02

pass = True

trot_FR_RL:

base_qdd_z = 0.185668089815

base_z_task_error = -1.433191018511e-02

pass = True

trot_FL_RR:

base_qdd_z = 0.185791586133

base_z_task_error = -1.420841386733e-02

pass = True

结论：

vertical-only base acceleration tracking task 通过。

## Full WBC Swing Accel Task QP

输出文件：

results/logs_sample/stage07_full_wbc_swing_accel_task_qp.csv

支持模式：

trot_FR_RL：

stance legs = FR, RL

swing legs = FL, RR

trot_FL_RR：

stance legs = FL, RR

swing legs = FR, RL

base task：

base_qdd_z_ref = 0.2

swing task：

swing_acc_ref = [0.4, 0.0, 0.8]

### trot_FR_RL 结果

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

### trot_FL_RR 结果

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

结论：

full WBC swing acceleration tracking task 通过。

## 当前 full WBC 默认离线配置

推荐当前默认 full WBC 离线配置：

1. dynamics equality
2. stance foot acceleration constraint
3. base vertical acceleration tracking task
4. swing foot acceleration tracking task
5. torque limit
6. friction cone
7. inactive contact force constraint

默认 base task：

base_qdd_z_ref = 0.2

默认 swing task：

swing_acc_ref = [0.4, 0.0, 0.8]

默认 contact modes：

trot_FR_RL

trot_FL_RR

## 已知失败项

6D base acceleration tracking task 未完全通过。

失败模式：

trot_FL_RR

失败指标：

base_task_error_norm = 0.07536047349576

原因：

6D base task 对 x/y/姿态加速度约束过强。base_qdd_z 本身已经接近目标，因此当前采用 vertical-only base acceleration tracking。

## 当前结论

Stage 7 已完成 full WBC 离线原型。

当前 full WBC 已具备：

1. qdd / contact force / tau 联合优化
2. floating-base dynamics equality
3. stance foot acceleration constraint
4. base vertical acceleration tracking
5. swing foot acceleration tracking
6. torque limit
7. friction cone
8. inactive contact force 约束

该结果说明 full WBC 的离线 QP 结构已经打通。

## 当前边界

当前仍不是完整动态 trot locomotion。

尚未完成：

1. Jdot_v 非零项
2. qdd 积分到 MuJoCo
3. torque 闭环仿真
4. gait phase scheduler
5. 连续 trot locomotion
6. base velocity tracking
7. 6D base acceleration tracking 稳定版本
8. ROS2 节点化
9. C++17 工程化迁移

## 下一步建议

下一步建议进入 MuJoCo 闭环前的 torque reconstruction check。

建议脚本：

scripts/stage07_full_wbc_torque_reconstruction_check.py

目标：

1. 读取 full WBC swing accel task QP 的 tau
2. 与 contact schedule WBC tau 做对比
3. 检查 torque limit
4. 检查 mode 间 torque jump
5. 为 MuJoCo torque closed-loop test 做准备

输出文件：

results/logs_sample/stage07_full_wbc_torque_reconstruction_check.csv
