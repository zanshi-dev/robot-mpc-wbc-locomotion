# Stage 7：Contact Schedule-Aware WBC/QP

## 状态

通过。

## 目标

实现 Stage 7 的 contact schedule-aware WBC/QP 离线原型。

该版本在 base wrench tracking WBC/QP 基础上加入 contact mode：

1. all_stance
2. trot_FR_RL
3. trot_FL_RR

## 输入文件

Stage 5 接触力：

results/logs_sample/stage05_standing_contact_force_qp.csv

Stage 6 actuator torque 参考：

results/logs_sample/stage06_qp_force_to_actuator_torque.csv

## 输出文件

results/logs_sample/stage07_contact_schedule_wbc_qp.csv

## 优化变量

f_wbc，12 维接触力：

FR_fx, FR_fy, FR_fz,
FL_fx, FL_fy, FL_fz,
RR_fx, RR_fy, RR_fz,
RL_fx, RL_fy, RL_fz

## 接触模式

all_stance：

FR, FL, RR, RL active

trot_FR_RL：

FR, RL active

FL, RR inactive

trot_FL_RR：

FL, RR active

FR, RL inactive

## 约束

inactive legs force = 0

active legs 满足：

fz >= 1.0

fz <= 120.0

|fx| <= mu * fz

|fy| <= mu * fz

mu = 0.6

torque limit：

-23.7 <= tau <= 23.7

符号约定：

tau = -J^T f

## 结果

### all_stance

OSQP status = solved

tau_max_abs = 5.300523665634

inactive_force_norm = 0.000000000000

min_active_fz = 30.740275659250

min_friction_margin = 18.439589223416

wrench_error_norm = 0.023024675737

pass = True

### trot_FR_RL

OSQP status = solved

tau_max_abs = 10.638319002741

inactive_force_norm = 0.000000000000

min_active_fz = 61.943834115289

min_friction_margin = 36.183066443294

wrench_error_norm = 0.141237586084

pass = True

### trot_FL_RR

OSQP status = solved

tau_max_abs = 10.594245657447

inactive_force_norm = 0.000000000000

min_active_fz = 62.190915998027

min_friction_margin = 36.331145835311

wrench_error_norm = 0.264596535614

pass = True

## 结论

contact schedule-aware WBC/QP 离线原型通过。

三种 contact mode 均满足：

1. OSQP solved
2. inactive force = 0
3. active fz 合法
4. friction constraints 合法
5. tau_max_abs <= 23.7
6. pass = True

对角双足支撑下，tau_max_abs 约为 10.6 Nm，仍低于 Go1 torque limit 23.7 Nm。

## 下一步

进入 Stage 7 下一小步：

将 contact schedule-aware WBC/QP 的两个 trot contact mode 分别接入 MuJoCo 短时支撑测试。

建议先测试静态单模式：

1. trot_FR_RL
2. trot_FL_RR

暂不做动态切换。

输出文件建议：

results/logs_sample/stage07_contact_schedule_wbc_support_test_summary.csv
