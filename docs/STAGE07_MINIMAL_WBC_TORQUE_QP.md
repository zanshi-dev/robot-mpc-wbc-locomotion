# Stage 7：最小 WBC Torque QP

## 状态

通过。

## 目标

实现 Stage 7 的第一小步：最小 WBC/QP torque 原型。

该原型暂不加入 floating base dynamics、swing foot tracking、contact constraint 或完整 WBC 动力学，只验证 WBC/QP 的最小优化框架是否可运行。

## 输入文件

results/logs_sample/stage06_qp_force_to_actuator_torque.csv

输入 torque 为 Stage 6 生成的 actuator torque。

## 输出文件

results/logs_sample/stage07_minimal_wbc_torque_qp.csv

## 变量

QP 决策变量：

tau_wbc，12 维

顺序：

FR_hip, FR_thigh, FR_calf,
FL_hip, FL_thigh, FL_calf,
RR_hip, RR_thigh, RR_calf,
RL_hip, RL_thigh, RL_calf

## 目标函数

最小化：

W_TRACK * ||tau - tau_ref||^2 + W_REG * ||tau||^2

参数：

W_TRACK = 1.0
W_REG = 0.0001

## 约束

torque limit：

-23.7 <= tau_i <= 23.7

## 验证结果

OSQP status = solved

tau_ref_max_abs = 5.309218454936

tau_wbc_max_abs = 5.308687586177

diff_norm = 0.001156584777

diff_max_abs = 0.000530868759

torque_limit = 23.7

limit_pass = True

pass = True

## 结论

最小 WBC/QP torque 原型已通过。

QP 能正常求解，输出 12 维 actuator torque，满足 torque limit，并且与 Stage 6 tau_ref 高度接近。

该结果只证明 Stage 7 的最小 QP 框架可运行，不代表完整 WBC 已完成。

## 下一步

Stage 7 第二小步：把最小 WBC torque QP 接入 MuJoCo 短时支撑测试。

测试形式：

tau_total = tau_pd + tau_wbc

其中 tau_wbc 来自 Stage 7 QP 输出。

通过标准：

1. sim_steps = 1000
2. min_z > 0.22
3. max_abs_roll < 0.15
4. max_abs_pitch < 0.15
5. saturation_steps = 0
6. pass = True
