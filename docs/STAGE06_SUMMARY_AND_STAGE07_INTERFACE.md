# Stage 6 总结与 Stage 7 接口约定

## Stage 6 状态

Stage 6 已完成。

已完成内容：

1. J^T f 离线映射验证
2. Stage 5 QP 接触力到 12 维 actuator torque 的转换
3. torque limit 检查
4. force sign sanity check
5. MuJoCo 短时支撑闭环测试
6. Stage 6 结果文档固化

## 已确认输入

Stage 5 接触力文件：

results/logs_sample/stage05_standing_contact_force_qp.csv

接触力顺序：

FR, FL, RR, RL

每条腿接触力格式：

fx, fy, fz

## 已确认输出

Stage 6 actuator torque 文件：

results/logs_sample/stage06_qp_force_to_actuator_torque.csv

输出 torque 顺序：

FR_hip, FR_thigh, FR_calf,
FL_hip, FL_thigh, FL_calf,
RR_hip, RR_thigh, RR_calf,
RL_hip, RL_thigh, RL_calf

该顺序与 MuJoCo actuator order 一致。

## 已确认符号约定

Stage 5 QP force 记为 f_qp。

MuJoCo actuator torque 使用：

actuator_tau = - J^T f_qp

符号检查结论：

plus 符号导致 base_z 下降。

minus 符号导致 base_z 上升并保持支撑。

因此后续统一使用：

tau_qp_actuator = - J^T f_qp

## torque limit 检查结果

tau_norm = 11.567004356004

tau_max_abs = 5.309218454936

torque_limit = 23.7

pass = True

结论：

Stage 5 QP 接触力映射到 actuator torque 后未超过 torque limit。

## 短时 MuJoCo 支撑闭环结果

测试形式：

tau_total = tau_pd + tau_qp_actuator

其中：

tau_qp_actuator = - J^T f_qp

控制参数：

kp = 80.0
kd = 2.0
torque_limit = 23.7
sim_steps = 1000

结果：

initial_z = 0.284805846483
final_z = 0.289618537988
min_z = 0.284805846483
max_z = 0.305958635013
delta_z = 0.004812691505
max_abs_roll = 0.066226209316
max_abs_pitch = 0.033555433733
max_tau_pd_abs = 13.776436903041
max_tau_qp_abs = 5.336923217750
max_tau_total_abs = 8.832121424115
saturation_steps = 0
pass = True

结论：

Stage 5 QP contact force 已可通过 Stage 6 映射接入 MuJoCo actuator torque，并通过短时支撑闭环测试。

## Stage 7 WBC/QP 前置接口约定

Stage 7 不应重新验证 MuJoCo、Pinocchio、Jacobian 顺序或 actuator 顺序。

Stage 7 应直接继承以下约定：

1. 腿顺序使用 FR, FL, RR, RL
2. 每条腿关节顺序使用 hip, thigh, calf
3. torque 输出顺序使用 MuJoCo actuator order
4. foot Jacobian 使用 world-aligned translational Jacobian
5. QP 接触力到 actuator torque 使用 actuator_tau = - J^T f_qp
6. torque limit 使用 23.7 Nm
7. standing pose 使用每条腿 [0.0, 0.9, -1.8]
8. 初始稳定 baseline 使用 kp = 80.0, kd = 2.0

## Stage 7 建议起点

Stage 7 第一小步不要直接做完整 WBC。

建议先实现离线 WBC/QP 最小原型：

目标：

在 standing pose 下，构造一个最小 QP，求解 12 维 actuator torque。

最小变量：

tau, 12 维

最小目标：

1. 跟踪 Stage 6 的 tau_qp_actuator
2. 限制 torque 在 [-23.7, 23.7]
3. 加入 torque regularization

第一版不加入 floating base dynamics，不加入 swing foot tracking，不加入完整接触约束。

第一版通过标准：

1. OSQP status solved
2. tau_wbc 维度为 12
3. tau_wbc_max_abs <= 23.7
4. tau_wbc 与 Stage 6 tau_qp_actuator 接近
5. 保存日志到 results/logs_sample/stage07_minimal_wbc_torque_qp.csv

## 下一步

进入 Stage 7 第一小步：

scripts/stage07_minimal_wbc_torque_qp.py
