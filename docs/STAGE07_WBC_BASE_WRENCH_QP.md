# Stage 7：Base Wrench Tracking WBC/QP

## 状态

通过。

## 目标

实现 Stage 7 第三小步：离线 base wrench tracking WBC/QP 原型。

该版本以接触力 f 为优化变量，通过接触力生成 base wrench，并通过已确认的符号约定映射为 actuator torque。

## 输入文件

Stage 5 QP 接触力：

results/logs_sample/stage05_standing_contact_force_qp.csv

Stage 6 actuator torque 参考：

results/logs_sample/stage06_qp_force_to_actuator_torque.csv

## 输出文件

results/logs_sample/stage07_wbc_base_wrench_qp.csv

## 优化变量

f_wbc，12 维：

FR_fx, FR_fy, FR_fz,
FL_fx, FL_fy, FL_fz,
RR_fx, RR_fy, RR_fz,
RL_fx, RL_fy, RL_fz

## 目标函数

同时跟踪：

1. base wrench
2. Stage 5 force reference
3. Stage 6 torque reference
4. force regularization

权重：

W_WRENCH = 10.0
W_FORCE_REF = 1.0
W_TAU_REF = 1.0
W_REG = 1e-6

## 约束

摩擦系数：

mu = 0.6

法向力约束：

1.0 <= fz <= 120.0

力矩约束：

-23.7 <= tau <= 23.7

符号约定：

tau = -J^T f

## 验证结果

OSQP status = solved

tau_max_abs = 5.309219364818

min_fz = 30.686044870227

force_diff_norm = 0.000010473048

tau_diff_norm = 0.000003100096

wrench_error_norm = 0.000014313895

torque_pass = True

fz_pass = True

pass = True

## 结论

Stage 7 base wrench tracking WBC/QP 离线原型通过。

QP 能在满足摩擦、法向力和 torque limit 的条件下，保持接触力、base wrench 和 actuator torque 与已验证参考值高度一致。

当前结果仍是离线 WBC/QP 原型，不代表完整动态 WBC 已完成。

## 下一步

进入 Stage 7 第四小步：

将 stage07_wbc_base_wrench_qp.csv 中的 torque 接入 MuJoCo 短时支撑测试。

测试形式：

tau_total = tau_pd + tau_wbc_base_wrench

通过标准：

1. sim_steps = 1000
2. min_z > 0.22
3. max_abs_roll < 0.15
4. max_abs_pitch < 0.15
5. saturation_steps = 0
6. pass = True
