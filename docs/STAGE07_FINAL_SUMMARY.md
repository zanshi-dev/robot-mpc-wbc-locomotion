# Stage 7 最终阶段总结

## 状态

Stage 7 当前阶段性完成。

当前完成的是 WBC/QP 的第一轮原型验证，包括：

1. 最小 torque QP
2. base wrench tracking QP
3. contact schedule-aware QP
4. MuJoCo 短时支撑测试
5. contact mode transition 检查
6. torque ramp 检查
7. 带 ramp 的 contact mode sequence 测试

当前不能宣称完成完整动态 WBC，也不能宣称完成动态 trot locomotion。

## 已完成脚本

scripts/stage07_minimal_wbc_torque_qp.py

scripts/stage07_wbc_torque_support_test.py

scripts/stage07_wbc_base_wrench_qp.py

scripts/stage07_wbc_base_wrench_support_test.py

scripts/stage07_wbc_posture_regularized_qp.py

scripts/stage07_wbc_posture_regularized_support_test.py

scripts/stage07_compare_wbc_variants.py

scripts/stage07_contact_schedule_wbc_qp.py

scripts/stage07_contact_schedule_wbc_support_test.py

scripts/stage07_contact_schedule_wbc_scale_sweep.py

scripts/stage07_contact_schedule_wbc_scaled_support_test.py

scripts/stage07_contact_mode_transition_check.py

scripts/stage07_contact_mode_torque_ramp_check.py

scripts/stage07_contact_mode_sequence_ramp_test.py

## 默认 WBC 配置

当前默认 WBC baseline：

results/logs_sample/stage07_wbc_base_wrench_qp.csv

当前默认 contact schedule WBC：

results/logs_sample/stage07_contact_schedule_wbc_qp.csv

当前默认 contact mode scale：

all_stance scale = 1.0

trot_FR_RL scale = 0.6

trot_FL_RR scale = 1.0

当前默认 transition ramp：

ramp_steps = 5

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

force 到 torque 符号：

tau = -J^T f

torque limit：

23.7 Nm

standing pose：

每条腿 [0.0, 0.9, -1.8]

默认 PD：

kp = 80.0

kd = 2.0

## 关键结果

### base_wrench_qp

tau_max_abs = 5.309219364818

max_tau_total_abs = 8.865605439903

max_abs_roll = 0.142713128163

roll_margin_to_0p15 = 0.007286871837

max_abs_pitch = 0.027806141378

saturation_steps = 0

pass = True

pass_margin = True

### contact schedule WBC scaled support test

all_stance:

max_abs_roll = 0.053689475648

max_abs_pitch = 0.029696786699

max_tau_total_abs = 8.858349940928

pass = True

pass_margin = True

trot_FR_RL，scale = 0.6:

max_abs_roll = 0.110752061094

max_abs_pitch = 0.052921077590

max_tau_total_abs = 9.331342107139

pass = True

pass_margin = True

trot_FL_RR，scale = 1.0:

max_abs_roll = 0.133384221160

max_abs_pitch = 0.070571666592

max_tau_total_abs = 11.454092417624

pass = True

pass_margin = True

### contact mode sequence ramp test

sequence：

all_stance -> trot_FR_RL -> all_stance -> trot_FL_RR -> all_stance

segment_steps = 300

total_steps = 1500

ramp_steps = 5

结果：

final_z = 0.294798253254

min_z = 0.284805846483

max_abs_roll = 0.096498358293

roll_margin_to_0p15 = 0.053501641707

max_abs_pitch = 0.058977498277

pitch_margin_to_0p15 = 0.091022501723

max_tau_total_abs = 10.974863827195

max_cmd_step_jump_norm = 2.292707929380

max_cmd_step_jump_abs = 1.071268207495

saturation_steps = 0

pass = True

pass_margin = True

## 当前不足

Stage 7 尚未完成完整 WBC。

未完成内容：

1. floating base dynamics equality constraint
2. qdd、contact force、torque 联合优化
3. base pose tracking
4. base velocity tracking
5. swing foot tracking
6. stance foot acceleration constraint
7. 实时 gait phase 接入
8. 动态 trot closed-loop locomotion
9. ROS2 节点化
10. C++17 工程化迁移

## 结论

Stage 7 已完成 WBC/QP 的第一轮原型验证。

当前系统已具备：

1. contact force 到 actuator torque 的安全映射
2. base wrench tracking WBC/QP
3. contact schedule-aware WBC/QP
4. 静态单模式支撑测试
5. contact mode transition jump 检查
6. torque ramp 平滑机制
7. 带 ramp 的 contact mode sequence 短时测试

下一步应继续 Stage 7，不进入 Stage 8 EKF。

## 下一步建议

Stage 7 下一阶段建议从 swing leg tracking 开始，而不是直接做完整 floating-base WBC。

建议下一小步：

scripts/stage07_swing_foot_tracking_qp.py

目标：

离线实现 swing foot tracking QP 原型。

第一版只做运动学层任务，不接 MuJoCo 动态闭环。

建议支持：

1. stance legs 使用 contact schedule WBC force
2. swing legs 生成期望 foot position
3. 使用 foot Jacobian 近似求解 swing leg joint velocity 或 torque correction
4. 保存日志到 results/logs_sample/stage07_swing_foot_tracking_qp.csv

完成后再考虑动态 gait phase 接入。
