# Stage 7：Base Wrench WBC/QP 短时支撑测试

## 状态

通过。

## 测试目标

验证 Stage 7 base wrench tracking WBC/QP 输出的 actuator torque 是否可以接入 MuJoCo 短时支撑测试。

测试形式：

tau_total = tau_pd + tau_wbc_base_wrench

其中 tau_wbc_base_wrench 来自：

results/logs_sample/stage07_wbc_base_wrench_qp.csv

## 输入文件

results/logs_sample/stage07_wbc_base_wrench_qp.csv

## 输出文件

results/logs_sample/stage07_wbc_base_wrench_support_test_log.csv

results/logs_sample/stage07_wbc_base_wrench_support_test_summary.csv

results/logs_sample/stage07_wbc_base_wrench_support_test_margin_check.csv

## 控制参数

kp = 80.0

kd = 2.0

torque_limit = 23.7

sim_steps = 1000

## 支撑测试结果

initial_z = 0.284805846483

final_z = 0.296097865333

min_z = 0.284697187237

max_z = 0.306443647985

delta_z = 0.011292018850

max_abs_roll = 0.142713128163

max_abs_pitch = 0.027806141378

max_tau_pd_abs = 14.174824804721

max_tau_wbc_abs = 5.309219364818

max_tau_total_abs = 8.865605439903

saturation_steps = 0

pass = True

## Margin 检查结果

max_abs_roll = 0.142713128163

roll_margin_to_0p15 = 0.007286871837

max_abs_pitch = 0.027806141378

pitch_margin_to_0p15 = 0.122193858622

min_z = 0.284697187237

z_margin_to_0p22 = 0.064697187237

final_z = 0.296097865333

final_roll = -0.012013715200

final_pitch = -0.018424145765

pass_margin = True

## 结论

Stage 7 base wrench tracking WBC/QP 输出的 torque 可以接入 MuJoCo actuator torque，并通过 1000 steps 短时支撑测试。

无 torque saturation。

最大总 torque 为 8.865605439903 Nm，小于 torque limit 23.7 Nm。

max_abs_roll = 0.142713128163，距离阈值 0.15 的 margin 为 0.007286871837。虽然通过，但 roll margin 较小，后续完整 WBC 接入时需要重点监控 roll 稳定性。

## 下一步

进入 Stage 7 下一小步：加入 posture regularization 的 WBC/QP 离线原型。

建议目标：

1. 保留 base wrench tracking
2. 保留 force reference tracking
3. 保留 torque reference tracking
4. 增加左右 hip torque 对称 regularization
5. 观察是否降低 roll 相关 torque 偏置

输出文件：

results/logs_sample/stage07_wbc_posture_regularized_qp.csv
