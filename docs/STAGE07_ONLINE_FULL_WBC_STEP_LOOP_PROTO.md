# Stage 7：Online Full WBC Step Loop Proto

## 状态

通过。

## 目标

实现在线 MuJoCo full WBC step loop 原型。

该版本每个仿真步：

1. 读取当前 q、qd
2. 根据固定 mode sequence 选择 contact mode
3. 在线求解 full WBC QP
4. 使用 low-pass ramp 平滑 WBC torque
5. 叠加 posture PD torque
6. 发送 torque 到 MuJoCo
7. 记录 base_z、roll、pitch、QP residual、torque 和 saturation

该测试仍是原地支撑验证，不包含前进速度。

## 输入文件

results/logs_sample/stage07_contact_schedule_wbc_qp.csv

## 输出文件

results/logs_sample/stage07_online_full_wbc_step_loop_proto_log.csv

results/logs_sample/stage07_online_full_wbc_step_loop_proto_summary.csv

## Mode Sequence

trot_FR_RL -> trot_FL_RR -> trot_FR_RL

## 配置

num_segments = 3

total_steps = 600

kp_posture = 60.0

kd_posture = 2.0

torque_limit = 23.7

base_qdd_z_ref = 0.05

swing_acc_ref = [0.1, 0.0, 0.2]

ramp_alpha = 0.2

## 结果

initial_z = 0.284805846483

final_z = 0.303007083406

min_z = 0.284602787921

max_z = 0.324781172497

delta_z = 0.018201236923

final_roll = 0.006266286166

final_pitch = -0.011694447899

max_abs_roll = 0.087444882304

roll_margin_to_limit = 0.112555117696

max_abs_pitch = 0.054577030128

pitch_margin_to_limit = 0.145422969872

z_margin_to_limit = 0.064602787921

max_tau_pd_abs = 17.925660006849

max_tau_wbc_abs = 10.264344153432

max_tau_total_abs = 11.413605129606

max_cmd_step_jump_norm = 4.585214741716

max_cmd_step_jump_abs = 2.277670654797

max_dyn_res_norm = 9.021244992010e-08

max_stance_acc_res_norm = 3.660267596023e-09

max_swing_acc_error_norm = 2.629309436127e-01

qp_fail_steps = 0

saturation_steps = 0

pass = True

pass_margin = True

## 结论

online full WBC step loop proto 通过。

该结果说明：

1. full WBC QP 可以在 MuJoCo step loop 中每步在线求解
2. QP 没有失败步
3. dynamics residual 和 stance acceleration residual 保持较小
4. low-pass torque smoothing 后没有 torque saturation
5. 原地多模式支撑序列稳定通过
6. base z、roll、pitch 均保留较大安全裕度

## 当前边界

该结果仍不是完整动态 trot locomotion。

当前仍没有：

1. gait phase scheduler
2. swing trajectory 在线生成
3. swing trajectory 与 full WBC 在线耦合
4. base velocity tracking
5. forward velocity command
6. touchdown / liftoff 状态机
7. Jdot_v 非零项
8. C++/ROS2 实时实现

## 下一步

建议继续 Stage 7：

实现 gait phase scheduler proto。

建议脚本：

scripts/stage07_gait_phase_scheduler_proto.py

目标：

1. 使用周期 phase 生成 trot_FR_RL / trot_FL_RR mode
2. 输出 stance/swing legs
3. 输出 phase、phase_in_mode、mode、swing_progress
4. 检查 mode duration 和切换次数
5. 为 online full WBC step loop 替换固定 mode sequence 做准备

输出文件：

results/logs_sample/stage07_gait_phase_scheduler_proto.csv
