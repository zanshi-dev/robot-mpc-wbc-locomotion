# Stage 7：Online Full WBC Scheduler Stability Sweep

## 状态

通过。

## 目标

对 online full WBC with scheduler proto 做参数稳定性 sweep，寻找 roll 更小的在线 scheduler 配置。

目标优先级：

1. QP failure = 0
2. torque saturation = 0
3. pass = True
4. max_abs_roll 尽量小
5. 优先尝试 max_abs_roll < 0.12

## 输入脚本

scripts/stage07_online_full_wbc_with_scheduler_proto.py

## 输出文件

results/logs_sample/stage07_online_full_wbc_scheduler_stability_sweep.csv

## Sweep 参数

period_steps:

400, 600

ramp_alpha:

0.10, 0.15, 0.20

base_qdd_z_ref:

0.03, 0.05

total cases = 12

## 总体结果

num_cases = 12

pass_cases = 11

strict_roll_cases = 0

strict_roll 目标：

max_abs_roll < 0.12

本轮没有配置严格达到 max_abs_roll < 0.12。

## 推荐配置

period_steps = 400

half_period_steps = 200

ramp_alpha = 0.15

base_qdd_z_ref = 0.03

total_steps = 1200

trot_FR_RL_steps = 600

trot_FL_RR_steps = 600

transition_count = 5

## 推荐配置结果

initial_z = 0.284805846483

final_z = 0.305351175409

min_z = 0.284525843843

max_z = 0.325211798729

delta_z = 0.020545328926

final_roll = 0.035555928490

final_pitch = 0.020598258923

max_abs_roll = 0.120328259514

roll_margin_to_0p20 = 0.079671740486

roll_margin_to_0p12 = -0.000328259514

max_abs_pitch = 0.083327623789

pitch_margin_to_0p20 = 0.116672376211

z_margin_to_0p22 = 0.064525843843

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

strict_roll_pass = False

recommended = True

## 失败配置

period_steps = 400

ramp_alpha = 0.20

base_qdd_z_ref = 0.03

失败原因：

max_abs_roll = 0.209898482299 > 0.20

pass = False

## 结论

online full WBC scheduler stability sweep 通过。

当前推荐配置：

period_steps = 400

ramp_alpha = 0.15

base_qdd_z_ref = 0.03

该配置满足：

1. QP failure = 0
2. torque saturation = 0
3. max_abs_roll = 0.120328259514
4. max_abs_pitch = 0.083327623789
5. min_z = 0.284525843843
6. max_tau_total_abs = 11.423881519983

该配置未严格达到 max_abs_roll < 0.12，但只超出 0.000328259514，可作为当前推荐在线 scheduler 配置。

## 当前边界

该结果仍不是完整动态 trot locomotion。

当前仍没有：

1. 在线 swing trajectory
2. base velocity tracking
3. forward velocity command
4. touchdown/liftoff 状态机
5. contact feedback
6. Jdot_v 非零项
7. ROS2/C++ 实时实现

## 下一步

建议用推荐配置重新生成一个 confirmed online full WBC scheduler run。

建议脚本：

scripts/stage07_online_full_wbc_scheduler_recommended_run.py

配置：

period_steps = 400

half_period_steps = 200

ramp_alpha = 0.15

base_qdd_z_ref = 0.03

目标：

1. 固化当前推荐配置
2. 输出独立 log/summary
3. 作为后续 online swing trajectory 接入前的默认 baseline

输出：

results/logs_sample/stage07_online_full_wbc_scheduler_recommended_run_log.csv

results/logs_sample/stage07_online_full_wbc_scheduler_recommended_run_summary.csv
