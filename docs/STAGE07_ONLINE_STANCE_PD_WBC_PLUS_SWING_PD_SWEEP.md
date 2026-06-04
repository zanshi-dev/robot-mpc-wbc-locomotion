# Stage 7：Online Stance PD/WBC Plus Swing PD Sweep

## 状态

通过。

## 目标

验证更合理的分腿控制结构：

1. stance legs：standing posture PD + optional stance WBC feedforward
2. swing legs：swing target PD
3. WBC torque 只作为 stance legs feedforward，不直接作用 swing legs
4. swing target PD 只作用 swing legs

该测试用于替代失败的：

1. direct full WBC torque + swing PD torque sum
2. stance-only WBC + swing-only PD

## 背景

上一轮 stance-only WBC + swing-only PD sweep 全部失败。

主要原因：

stance legs 缺少姿态/关节保持 PD，导致 stance legs 支撑不足，出现翻倒、torque saturation 和大姿态角。

因此本轮加入 stance posture PD。

## 脚本

scripts/stage07_online_stance_pd_wbc_plus_swing_pd_sweep.py

## 输出文件

results/logs_sample/stage07_online_stance_pd_wbc_plus_swing_pd_sweep.csv

## Sweep 参数

STANCE_KP = 60.0

STANCE_KD = 2.0

SWING_KP = 80.0

SWING_KD = 2.0

STANCE_WBC_SCALE_LIST = [0.0, 0.10, 0.20, 0.30]

SWING_TARGET_SCALE_LIST = [0.35, 0.45, 0.60]

SWING_PD_SCALE_LIST = [0.50, 0.75, 1.00]

## 总体结果

num_cases = 36

pass_cases = 27

pass_margin_cases = 27

stance_wbc_pass_cases = 19

## 脚本自动推荐项

脚本自动推荐项为：

stance_wbc_scale = 0.0

swing_pd_scale = 1.0

swing_target_scale = 0.35

该项通过，但属于 PD-only，不包含 stance WBC feedforward。

因此它不作为最终 combined baseline。

## 采用的非零 WBC 推荐项

当前采用以下非零 WBC 配置作为 combined baseline：

stance_wbc_scale = 0.2

swing_pd_scale = 1.0

swing_target_scale = 0.35

## 非零 WBC 推荐项结果

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

online stance PD/WBC plus swing PD sweep 通过。

直接 torque sum 失败后，当前可用的 combined control baseline 是：

stance legs = standing posture PD + scaled stance WBC feedforward

swing legs = scaled swing target PD

采用配置：

stance_wbc_scale = 0.2

swing_pd_scale = 1.0

swing_target_scale = 0.35

该配置满足：

1. max_swing_joint_error < 0.08
2. max_abs_roll < 0.20
3. max_abs_pitch < 0.20
4. min_z > 0.22
5. qp_fail_steps = 0
6. saturation_steps = 0
7. pass_margin = True

## 当前边界

该方案仍不是最终 WBC locomotion。

当前 WBC 只是 stance legs feedforward，不是严格的 task-priority WBC。

尚未完成：

1. WBC QP 内部直接加入 online swing target task
2. swing target 到 acceleration task 的实时转换
3. touchdown/liftoff contact feedback
4. base velocity tracking
5. forward velocity command
6. ROS2/C++ 实时实现

## 下一步

生成 recommended run：

scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py

推荐配置：

stance_wbc_scale = 0.2

swing_pd_scale = 1.0

swing_target_scale = 0.35

输出：

results/logs_sample/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test_log.csv

results/logs_sample/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test_summary.csv
