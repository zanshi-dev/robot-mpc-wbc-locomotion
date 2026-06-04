# Stage 7：Contact Mode Sequence Ramp Test

## 状态

通过。

## 目标

验证 contact schedule-aware WBC/QP 在加入 torque ramp 后，是否可以完成短时 contact mode sequence 测试。

该测试仍不是完整动态 trot locomotion，而是接触模式切换前置验证。

## 输入文件

results/logs_sample/stage07_contact_schedule_wbc_qp.csv

## 输出文件

results/logs_sample/stage07_contact_mode_sequence_ramp_test_log.csv

results/logs_sample/stage07_contact_mode_sequence_ramp_test_summary.csv

## Contact Mode Sequence

all_stance -> trot_FR_RL -> all_stance -> trot_FL_RR -> all_stance

每段保持：

300 steps

总步数：

1500 steps

## Torque Scale

all_stance scale = 1.0

trot_FR_RL scale = 0.6

trot_FL_RR scale = 1.0

## Torque Ramp

ramp_steps = 5

控制形式：

tau_cmd = tau_prev + alpha * (tau_target - tau_prev)

其中 alpha 从 1 / ramp_steps 增加到 1。

## 控制参数

kp = 80.0

kd = 2.0

torque_limit = 23.7

## 测试结果

initial_z = 0.284805846483

final_z = 0.294798253254

min_z = 0.284805846483

max_z = 0.305856777251

delta_z = 0.009992406771

final_roll = -0.015084373526

final_pitch = -0.036988602386

max_abs_roll = 0.096498358293

roll_margin_to_0p15 = 0.053501641707

max_abs_pitch = 0.058977498277

pitch_margin_to_0p15 = 0.091022501723

z_margin_to_0p22 = 0.064805846483

max_tau_pd_abs = 18.874491898669

max_tau_wbc_cmd_abs = 10.594245657447

max_tau_total_abs = 10.974863827195

max_cmd_step_jump_norm = 2.292707929380

max_cmd_step_jump_abs = 1.071268207495

saturation_steps = 0

pass = True

pass_margin = True

## 结论

带 ramp 的 contact mode sequence 短时测试通过。

相比直接切换，ramp 后最大单步 torque command jump 已降低到：

max_cmd_step_jump_norm = 2.292707929380

max_cmd_step_jump_abs = 1.071268207495

无 torque saturation。

base 高度、roll、pitch 均在阈值内。

## 当前边界

该测试仍然是 standing pose 下的 contact mode sequence torque 测试。

当前不能宣称已完成动态 trot locomotion。

尚未完成：

1. 实时 gait phase 切换
2. swing leg trajectory tracking
3. base velocity tracking
4. qdd / contact force / torque 联合优化
5. 完整 floating base dynamics WBC
6. 动态 MuJoCo trot closed-loop

## 下一步

进入 Stage 7 阶段总结。

目标：

1. 固化 Stage 7 已完成的所有 WBC/QP 原型
2. 明确当前默认配置
3. 明确 Stage 7 后续应进入 swing leg tracking 或完整 WBC dynamics，而不是 Stage 8 EKF
