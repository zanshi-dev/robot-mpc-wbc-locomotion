# Stage 7：Online Full WBC with Scheduler Proto

## 状态

通过。

## 目标

将 gait phase scheduler 接入 online full WBC step loop，替代固定 mode sequence。

该版本每个 MuJoCo 仿真步：

1. 使用 phase scheduler 生成 trot contact mode
2. 读取当前 q、qd
3. 在线求解 full WBC QP
4. 使用 low-pass smoothing 平滑 WBC torque
5. 叠加 posture PD torque
6. 发送 torque 到 MuJoCo
7. 记录 base_z、roll、pitch、QP residual、torque、mode、phase 和 saturation

该测试仍是原地支撑验证，不包含前进速度。

## 输入文件

results/logs_sample/stage07_contact_schedule_wbc_qp.csv

## 输出文件

results/logs_sample/stage07_online_full_wbc_with_scheduler_proto_log.csv

results/logs_sample/stage07_online_full_wbc_with_scheduler_proto_summary.csv

## Scheduler

scheduler = phase_trot

dt = 0.002

total_steps = 1200

period_steps = 400

half_period_steps = 200

trot_FR_RL_steps = 600

trot_FL_RR_steps = 600

transition_count = 5

## WBC / Control 配置

kp_posture = 60.0

kd_posture = 2.0

torque_limit = 23.7

base_qdd_z_ref = 0.05

swing_acc_ref = [0.1, 0.0, 0.2]

ramp_alpha = 0.2

## 结果

initial_z = 0.284805846483

final_z = 0.306167691855

min_z = 0.284602787921

max_z = 0.324781172497

delta_z = 0.021361845372

final_roll = 0.047401678133

final_pitch = 0.035868317312

max_abs_roll = 0.148607466957

roll_margin_to_limit = 0.051392533043

max_abs_pitch = 0.067919909731

pitch_margin_to_limit = 0.132080090269

z_margin_to_limit = 0.064602787921

max_tau_pd_abs = 18.430845082537

max_tau_wbc_abs = 10.264344153432

max_tau_total_abs = 11.413605129606

max_cmd_step_jump_norm = 4.585214741716

max_cmd_step_jump_abs = 2.277670654797

max_dyn_res_norm = 9.745131047022e-08

max_stance_acc_res_norm = 3.725303596518e-09

max_swing_acc_error_norm = 6.383111519946e-01

qp_fail_steps = 0

saturation_steps = 0

pass = True

pass_margin = True

## 结论

online full WBC with scheduler proto 通过。

该结果说明：

1. phase scheduler 可以驱动 online full WBC step loop
2. full WBC QP 可以在 1200 个 MuJoCo step 中持续在线求解
3. QP failure = 0
4. torque saturation = 0
5. dynamics residual 和 stance acceleration residual 保持较小
6. 原地 scheduler-driven trot support 通过

## 注意事项

max_abs_roll = 0.148607466957，接近早期常用的 0.15 阈值。

当前脚本阈值为 0.20，因此该测试通过；但如果后续重新采用 0.15 作为严格姿态阈值，需要进一步降低 roll。

## 当前边界

该结果仍不是完整动态 trot locomotion。

尚未完成：

1. 在线 swing trajectory
2. swing trajectory 与 full WBC task 耦合
3. base velocity tracking
4. forward velocity command
5. touchdown / liftoff 状态机
6. contact feedback
7. Jdot_v 非零项
8. ROS2/C++ 实时实现

## 下一步

建议做 scheduler 参数稳定性 sweep。

建议脚本：

scripts/stage07_online_full_wbc_scheduler_stability_sweep.py

目标：

1. sweep period_steps
2. sweep ramp_alpha
3. sweep base_qdd_z_ref
4. 找到 roll 更小的默认在线 scheduler 配置
5. 优先让 max_abs_roll < 0.12

输出：

results/logs_sample/stage07_online_full_wbc_scheduler_stability_sweep.csv
