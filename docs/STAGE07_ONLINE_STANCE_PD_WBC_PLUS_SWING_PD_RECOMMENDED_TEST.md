# Stage 7：Online Stance PD/WBC Plus Swing PD Recommended Test

## 状态

通过。

## 目标

固化当前 combined online control baseline：

1. stance legs 使用 standing posture PD
2. stance legs 叠加 scaled WBC feedforward
3. swing legs 使用 online swing target PD
4. WBC torque 不直接作用 swing legs
5. swing PD 不直接作用 stance legs

该方案是 direct torque sum 失败、stance-only WBC + swing-only PD 失败后的当前可用 combined baseline。

## 输入

WBC baseline：

scripts/stage07_online_full_wbc_scheduler_recommended_run.py

Swing target：

results/logs_sample/stage07_online_swing_trajectory_tracking_check.csv

## 脚本

scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py

## 输出文件

results/logs_sample/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test_log.csv

results/logs_sample/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test_summary.csv

## 配置

STANCE_KP = 60.0

STANCE_KD = 2.0

SWING_KP = 80.0

SWING_KD = 2.0

stance_wbc_scale = 0.2

swing_pd_scale = 1.0

swing_target_scale = 0.35

torque_limit = 23.7

## 结果

total_steps = 1200

transition_count = 5

trot_FR_RL_steps = 600

trot_FL_RR_steps = 600

initial_z = 0.284805846483

final_z = 0.286644861037

min_z = 0.278419161322

max_z = 0.289102536841

delta_z = 0.001839014553

final_roll = -0.015879508048

final_pitch = -0.009621783271

max_abs_roll = 0.056707402709

roll_margin_to_0p20 = 0.143292597291

max_abs_pitch = 0.048329482530

pitch_margin_to_0p20 = 0.151670517470

z_margin_to_0p22 = 0.058419161322

max_joint_error = 0.077233662573

max_swing_joint_error = 0.042163850217

max_stance_joint_error = 0.077233662573

max_tau_stance_pd_abs = 11.083222358114

max_tau_stance_wbc_abs = 2.125887056052

max_tau_swing_pd_abs = 9.659563043535

max_tau_total_raw_abs = 9.659563043535

max_tau_total_abs = 9.659563043535

max_cmd_step_jump_norm = 25.788963931985

max_cmd_step_jump_abs = 10.987848177937

max_dyn_res_norm = 7.732488454756e-08

max_stance_acc_res_norm = 3.520891005970e-09

max_swing_acc_error_norm = 2.545718566371e-01

qp_fail_steps = 0

saturation_steps = 0

pass = True

pass_margin = True

## 结论

online stance PD/WBC plus swing PD recommended test 通过。

当前可用 combined online baseline：

stance legs = standing posture PD + 0.2 * stance WBC feedforward

swing legs = swing target PD, swing_target_scale = 0.35

该配置满足：

1. qp_fail_steps = 0
2. saturation_steps = 0
3. min_z > 0.22
4. max_abs_roll < 0.20
5. max_abs_pitch < 0.20
6. max_swing_joint_error < 0.08
7. pass_margin = True

## 关键判断

该结果不是 pure full WBC locomotion。

它是一个可运行的 mixed online control baseline：

1. WBC 目前作为 stance feedforward
2. stance 稳定性主要由 posture PD 保证
3. swing motion 由 online swing target PD 保证
4. online gait scheduler、memory swing trajectory、IK/QP joint target、MuJoCo closed-loop tracking 已经贯通

## 当前边界

尚未完成：

1. WBC QP 内部直接接入 online swing target task
2. swing target 到 acceleration reference 的在线转换
3. contact feedback 驱动 touchdown/liftoff
4. base velocity tracking
5. forward velocity command
6. ROS2/C++ 实时实现

## 下一步

建议生成 Stage 7 online locomotion consolidated summary。

建议文档：

docs/STAGE07_ONLINE_LOCOMOTION_CONSOLIDATED_SUMMARY.md

目标：

1. 汇总 online scheduler
2. 汇总 online swing trajectory
3. 汇总 swing joint tracking
4. 汇总 full WBC online proto
5. 汇总失败的 direct torque sum
6. 汇总当前通过的 mixed baseline
7. 明确 Stage 8 入口
