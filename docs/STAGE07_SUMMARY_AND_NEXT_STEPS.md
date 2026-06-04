# Stage 7 总结与后续边界

## 状态

Stage 7 当前第一轮 WBC/QP 原型验证完成。

注意：当前不是完整动态 WBC。当前完成的是 standing pose 下的 torque-level / base-wrench-level WBC/QP 原型，以及 MuJoCo 短时支撑验证。

## 已完成内容

1. minimal WBC torque QP
2. minimal WBC torque QP 支撑测试
3. base wrench tracking WBC/QP
4. base wrench tracking WBC/QP 支撑测试
5. posture regularized WBC/QP 实验 variant
6. posture regularized WBC/QP 支撑测试
7. WBC variant comparison
8. 默认 WBC baseline 选择

## 默认 WBC baseline

当前默认选择：

results/logs_sample/stage07_wbc_base_wrench_qp.csv

原因：

1. QP pass = True
2. support pass = True
3. margin pass = True
4. saturation_steps = 0
5. 相比 posture_regularized_qp，roll margin 更大
6. 相比 posture_regularized_qp，max_tau_total_abs 更低

## 当前默认结果

base_wrench_qp：

tau_max_abs = 5.309219364818

max_tau_total_abs = 8.865605439903

max_abs_roll = 0.142713128163

roll_margin_to_0p15 = 0.007286871837

max_abs_pitch = 0.027806141378

pitch_margin_to_0p15 = 0.122193858622

min_z = 0.284697187237

z_margin_to_0p22 = 0.064697187237

saturation_steps = 0

accepted_baseline = True

## 不采用的 variant

posture_regularized_qp 暂不作为默认控制输入。

原因：

margin_pass = False

roll_margin_to_0p15 = 0.002761702665

max_abs_roll = 0.147238297335

max_tau_total_abs = 9.208799641206

reject_reason = margin_check_failed

## 已确认接口约定

腿顺序：

FR, FL, RR, RL

每条腿关节顺序：

hip, thigh, calf

torque 输出顺序：

FR_hip, FR_thigh, FR_calf,
FL_hip, FL_thigh, FL_calf,
RR_hip, RR_thigh, RR_calf,
RL_hip, RL_thigh, RL_calf

force 到 torque 符号约定：

tau = -J^T f

torque limit：

23.7 Nm

standing pose：

每条腿 [0.0, 0.9, -1.8]

默认 PD baseline：

kp = 80.0
kd = 2.0

## 当前 Stage 7 结论

当前项目已经具备：

1. Stage 5 contact force 到 Stage 6 actuator torque 的映射
2. Stage 7 WBC/QP 对 contact force、base wrench、torque limit 的离线优化
3. Stage 7 WBC/QP torque 接入 MuJoCo 的短时支撑测试
4. WBC variant 对比和默认 baseline 选择

## 当前不足

当前尚未完成完整 WBC。

未完成内容包括：

1. floating base dynamics equality constraint
2. qdd / contact force / torque 联合优化
3. swing foot tracking task
4. stance foot acceleration constraint
5. base pose tracking task
6. contact schedule-aware WBC
7. 动态 trot 闭环接入
8. ROS2 节点化

## 下一步建议

继续 Stage 7，不进入 Stage 8 EKF。

下一小步建议实现：

scripts/stage07_contact_schedule_wbc_qp.py

目标：

将当前 base_wrench_qp 扩展为 contact schedule-aware WBC/QP。

第一版只做离线 QP，不接 MuJoCo。

支持三种 contact mode：

1. all_stance
2. trot_FR_RL
3. trot_FL_RR

要求：

1. inactive legs force = 0
2. active legs 满足 fz 和 friction constraints
3. tau = -J^T f
4. tau 满足 torque limit
5. 保存结果到 results/logs_sample/stage07_contact_schedule_wbc_qp.csv

通过标准：

1. OSQP status = solved
2. 三种 contact mode 均 pass
3. inactive force norm 接近 0
4. tau_max_abs <= 23.7
5. active legs fz >= 1.0
