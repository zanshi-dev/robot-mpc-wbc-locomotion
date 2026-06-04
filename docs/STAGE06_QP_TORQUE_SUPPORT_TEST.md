# Stage 6：QP 力矩短时支撑闭环测试

## 状态

通过。

## 测试目标

验证 Stage 5 QP 接触力经过 Stage 6 映射后，是否可以作为 actuator torque 接入 MuJoCo 短时闭环支撑测试。

使用形式：

tau_total = tau_pd + tau_qp_actuator

其中：

tau_qp_actuator = - J^T f_qp

所有 actuator torque 裁剪到：

[-23.7, 23.7]

## 输入文件

results/logs_sample/stage05_standing_contact_force_qp.csv

## 输出文件

results/logs_sample/stage06_qp_torque_support_test_log.csv

results/logs_sample/stage06_qp_torque_support_test_summary.csv

## 控制参数

kp = 80.0

kd = 2.0

torque_limit = 23.7

sim_steps = 1000

## 验证结果

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

## 结论

QP actuator torque 接入 MuJoCo 后，机器人在 1000 steps 内保持支撑稳定。

无 torque saturation。

最大总 torque 为 8.832121424115 Nm，小于 torque limit 23.7 Nm。

Stage 6 已完成从 Stage 5 QP contact force 到 MuJoCo actuator torque 的离线验证和短时闭环支撑验证。

## 下一步

进入 Stage 6 最后一小步：整理 Stage 6 总结文档，并明确进入 Stage 7 WBC/QP 前的接口约定。
