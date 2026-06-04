# Stage 7：WBC Torque 短时支撑测试

## 状态

通过。

## 测试目标

验证 Stage 7 minimal WBC torque QP 输出的 tau_wbc 是否可以接入 MuJoCo 短时支撑测试。

测试形式：

tau_total = tau_pd + tau_wbc

其中 tau_wbc 来自：

results/logs_sample/stage07_minimal_wbc_torque_qp.csv

## 输入文件

results/logs_sample/stage07_minimal_wbc_torque_qp.csv

## 输出文件

results/logs_sample/stage07_wbc_torque_support_test_log.csv

results/logs_sample/stage07_wbc_torque_support_test_summary.csv

## 控制参数

kp = 80.0

kd = 2.0

torque_limit = 23.7

sim_steps = 1000

## 验证结果

initial_z = 0.284805846483

final_z = 0.293882173125

min_z = 0.284805846483

max_z = 0.304683134056

delta_z = 0.009076326641

max_abs_roll = 0.079919230304

max_abs_pitch = 0.032882365738

max_tau_pd_abs = 13.907303920111

max_tau_wbc_abs = 5.308687586177

max_tau_total_abs = 8.787891555301

saturation_steps = 0

pass = True

## 结论

Stage 7 minimal WBC torque QP 输出可以接入 MuJoCo actuator torque，并通过 1000 steps 短时支撑测试。

无 torque saturation。

最大总 torque 为 8.787891555301 Nm，小于 torque limit 23.7 Nm。

当前结果说明 Stage 7 的最小 torque-level QP 框架可以作为后续完整 WBC/QP 的基础。

## 下一步

进入 Stage 7 第三小步：加入 base wrench tracking 的离线 WBC/QP 原型。

建议变量：

tau，12 维

目标：

1. 跟踪 Stage 6 / Stage 7 已验证 tau_ref
2. 加入 torque regularization
3. 加入近似 base wrench tracking 目标

暂不接入完整 floating-base dynamics。

输出文件：

results/logs_sample/stage07_wbc_base_wrench_qp.csv
