# Stage 7：Online Full WBC Scheduler Recommended Run

## 状态

通过。

## 目标

用 scheduler stability sweep 推荐配置生成独立 confirmed run，作为后续 online swing trajectory 接入前的默认 baseline。

## 输入脚本

scripts/stage07_online_full_wbc_scheduler_recommended_run.py

## 输出文件

results/logs_sample/stage07_online_full_wbc_scheduler_recommended_run_log.csv

results/logs_sample/stage07_online_full_wbc_scheduler_recommended_run_summary.csv

## 推荐配置

scheduler = phase_trot

total_steps = 1200

dt = 0.002

period_steps = 400

half_period_steps = 200

trot_FR_RL_steps = 600

trot_FL_RR_steps = 600

transition_count = 5

kp_posture = 60.0

kd_posture = 2.0

torque_limit = 23.7

base_qdd_z_ref = 0.03

swing_acc_ref = [0.1, 0.0, 0.2]

ramp_alpha = 0.15

## 结果

initial_z = 0.284805846483

final_z = 0.305351175409

min_z = 0.284525843843

max_z = 0.325211798729

delta_z = 0.020545328926

final_roll = 0.035555928490

final_pitch = 0.020598258923

max_abs_roll = 0.120328259514

roll_margin_to_limit = 0.079671740486

max_abs_pitch = 0.083327623789

pitch_margin_to_limit = 0.116672376211

z_margin_to_limit = 0.064525843843

max_tau_pd_abs = 17.914484841257

max_tau_wbc_abs = 10.664068495997

max_tau_total_abs = 11.423881519983

max_cmd_step_jump_norm = 3.444357031147

max_cmd_step_jump_abs = 1.782238605127

max_dyn_res_norm = 1.039101885248e-07

max_stance_acc_res_norm = 3.750277847245e-09

max_swing_acc_error_norm = 5.967141996034e-01

qp_fail_steps = 0

saturation_steps = 0

pass = True

pass_margin = True

## 结论

online full WBC scheduler recommended run 通过。

该配置现在作为 Stage 7 online full WBC 原地 scheduler-driven support 的推荐 baseline。

推荐 baseline：

period_steps = 400

half_period_steps = 200

base_qdd_z_ref = 0.03

ramp_alpha = 0.15

kp_posture = 60.0

kd_posture = 2.0

torque_limit = 23.7

该 baseline 满足：

1. QP failure = 0
2. torque saturation = 0
3. max_abs_roll = 0.120328259514
4. max_abs_pitch = 0.083327623789
5. min_z = 0.284525843843
6. max_tau_total_abs = 11.423881519983

## 当前边界

该结果仍不是完整动态 trot locomotion。

尚未完成：

1. online swing trajectory
2. swing foot target 与 full WBC task 耦合
3. base velocity tracking
4. forward velocity command
5. touchdown/liftoff 状态机
6. contact feedback
7. Jdot_v 非零项
8. ROS2/C++ 实时实现

## 下一步

建议进入 online swing trajectory proto。

建议脚本：

scripts/stage07_online_swing_trajectory_proto.py

目标：

1. 基于 scheduler 的 phase_in_mode / swing_progress
2. 为 swing legs 生成 foot position target
3. 使用保守 swing stride 和 clearance
4. 输出 target foot position，不接 WBC
5. 检查轨迹连续性和高度

建议输出：

results/logs_sample/stage07_online_swing_trajectory_proto.csv

results/logs_sample/stage07_online_swing_trajectory_proto_summary.csv
