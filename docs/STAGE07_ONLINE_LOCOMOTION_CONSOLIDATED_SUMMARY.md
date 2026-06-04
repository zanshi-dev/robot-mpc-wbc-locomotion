# Stage 7：Online Locomotion Consolidated Summary

## 状态

Stage 7 online locomotion 主线已完成阶段性闭环。

当前可用 baseline：

stance PD + scaled stance WBC feedforward + swing target PD

该 baseline 已通过 1200-step scheduler-driven trot MuJoCo closed-loop test。

## 当前最终推荐 baseline

脚本：

scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py

输出：

results/logs_sample/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test_log.csv

results/logs_sample/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test_summary.csv

控制结构：

1. stance legs：standing posture PD
2. stance legs：叠加 0.2 * stance WBC feedforward
3. swing legs：online swing target PD
4. WBC torque 不直接作用 swing legs
5. swing PD 不直接作用 stance legs

配置：

STANCE_KP = 60.0

STANCE_KD = 2.0

SWING_KP = 80.0

SWING_KD = 2.0

stance_wbc_scale = 0.2

swing_pd_scale = 1.0

swing_target_scale = 0.35

torque_limit = 23.7

结果：

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

max_abs_pitch = 0.048329482530

z_margin_to_0p22 = 0.058419161322

max_joint_error = 0.077233662573

max_swing_joint_error = 0.042163850217

max_stance_joint_error = 0.077233662573

max_tau_stance_pd_abs = 11.083222358114

max_tau_stance_wbc_abs = 2.125887056052

max_tau_swing_pd_abs = 9.659563043535

max_tau_total_abs = 9.659563043535

qp_fail_steps = 0

saturation_steps = 0

pass = True

pass_margin = True

## Online gait scheduler

脚本：

scripts/stage07_gait_phase_scheduler_proto.py

结果：

dt = 0.002

total_steps = 1200

period_steps = 400

half_period_steps = 200

num_cycles = 3

trot_FR_RL steps = 600

trot_FL_RR steps = 600

transition_count = 5

pass = True

结论：

phase-based trot scheduler 已可稳定生成 FR/RL 与 FL/RR 两个对角支撑模式。

## Online full WBC scheduler baseline

脚本：

scripts/stage07_online_full_wbc_scheduler_recommended_run.py

配置：

period_steps = 400

ramp_alpha = 0.15

base_qdd_z_ref = 0.03

swing_acc_ref = [0.1, 0.0, 0.2]

kp = 60

kd = 2

结果：

total_steps = 1200

final_z = 0.305351175409

min_z = 0.284525843843

max_abs_roll = 0.120328259514

max_abs_pitch = 0.083327623789

max_tau_total_abs = 11.423881519983

qp_fail = 0

saturation = 0

pass = True

pass_margin = True

结论：

online full WBC scheduler proto 可独立稳定运行，但它本身尚未形成完整 swing target tracking locomotion。

## Online swing trajectory memory proto

脚本：

scripts/stage07_online_swing_trajectory_memory_proto.py

输出：

results/logs_sample/stage07_online_swing_trajectory_memory_proto.csv

结果：

transition_count = 5

swing_start_count = 12

expected_swing_start_count = 12

min_target_z = 0.020000000000

max_target_z = 0.045000000000

max_step_delta_norm = 0.000392684534

max_step_delta_z = 0.000392682933

每条腿 swing_samples = 600

每条腿 stance_samples = 600

pass = True

结论：

memory-based online swing target generator 已解决 mode switch target jump 问题。

## Online swing trajectory tracking check

脚本：

scripts/stage07_online_swing_trajectory_tracking_check.py

输入：

results/logs_sample/stage07_online_swing_trajectory_memory_proto.csv

输出：

results/logs_sample/stage07_online_swing_trajectory_tracking_check.csv

结果：

total_steps = 1200

max_foot_error_norm = 0.000900142979

max_swing_foot_error_norm = 0.000373110134

max_stance_foot_error_norm = 0.000900142979

max_abs_dq_step = 0.003211667495

max_q_delta_from_standing = 0.183211559405

qp_fail_steps = 0

pass = True

结论：

memory swing trajectory 可以通过小步 IK/QP 转换为连续 joint target。

## Online swing joint tracking recommended test

脚本：

scripts/stage07_online_swing_joint_tracking_recommended_test.py

配置：

kp = 80.0

kd = 2.0

target_scale = 0.6

结果：

total_steps = 1200

final_z = 0.282769844842

min_z = 0.270657074947

max_abs_roll = 0.063224324564

max_abs_pitch = 0.055307047284

max_joint_error = 0.059643533460

max_swing_joint_error = 0.059643533460

max_stance_joint_error = 0.035331528104

max_tau_total_abs = 9.930087778241

saturation_steps = 0

pass = True

pass_margin = True

结论：

online swing joint target 可被 MuJoCo PD 闭环稳定跟踪。

## 失败分支 1：direct full WBC torque + swing PD torque sum

脚本：

scripts/stage07_online_full_wbc_plus_swing_joint_tracking_proto.py

初始配置：

wbc_torque_scale = 1.0

swing_pd_torque_scale = 0.5

target_scale = 0.6

结果：

max_abs_roll = 0.370811239659

max_abs_pitch = 0.199495920616

max_joint_error = 0.269034444734

pass = False

结论：

直接线性叠加 full WBC torque 与 swing joint PD torque 会造成任务冲突，不作为当前方案。

## 失败分支 2：full WBC plus swing PD torque scale sweep

脚本：

scripts/stage07_online_full_wbc_plus_swing_joint_tracking_sweep.py

结果：

num_cases = 24

pass_cases = 4

pass_margin_cases = 4

关键发现：

所有通过项的 wbc_torque_scale 都是 0.0。

结论：

通过项实际是 swing PD-only，不是 full WBC + swing tracking 成功耦合。direct torque sum 被拒绝。

## 失败分支 3：stance-only WBC + swing-only PD

脚本：

scripts/stage07_online_stance_wbc_plus_swing_pd_sweep.py

结果：

num_cases = 45

pass_cases = 0

pass_margin_cases = 0

stance_wbc_pass_cases = 0

典型现象：

max_abs_roll 接近 3.14

max_tau_total_abs = 23.7

存在大量 saturation

结论：

stance legs 缺少 posture PD 时，stance-only WBC feedforward 无法单独稳定闭环。

## 成功分支：stance PD/WBC plus swing PD

脚本：

scripts/stage07_online_stance_pd_wbc_plus_swing_pd_sweep.py

结果：

num_cases = 36

pass_cases = 27

pass_margin_cases = 27

stance_wbc_pass_cases = 19

采用的非零 WBC baseline：

stance_wbc_scale = 0.2

swing_pd_scale = 1.0

swing_target_scale = 0.35

结论：

加入 stance posture PD 后，stance WBC feedforward 可稳定叠加，形成当前可用 mixed control baseline。

## 当前 Stage 7 结论

Stage 7 已完成以下闭环：

1. online gait scheduler
2. online memory swing trajectory
3. swing trajectory IK/QP joint target conversion
4. MuJoCo swing joint target tracking
5. online full WBC QP proto
6. scheduler-driven online full WBC proto
7. mixed stance PD/WBC + swing PD closed-loop proto

当前可用方案不是 pure WBC locomotion，而是 mixed online control baseline。

当前最可靠 baseline：

stance legs = posture PD + scaled stance WBC feedforward

swing legs = online swing target PD

## 当前边界

尚未完成：

1. WBC QP 内部直接接入 online swing target task
2. swing target 到 acceleration reference 的在线转换
3. touchdown/liftoff contact feedback
4. base velocity tracking
5. forward velocity command
6. C++/ROS2 real-time controller
7. Pinocchio/MuJoCo state interface 对齐
8. OSQP warm-start 与实时周期约束

## Stage 8 入口建议

Stage 8 建议目标：

从 Python/MuJoCo proto 进入可迁移控制架构。

优先任务：

1. 定义 C++ controller module interface
2. 固化 gait scheduler interface
3. 固化 swing trajectory generator interface
4. 固化 stance/swing torque mixer interface
5. 固化 WBC QP input/output interface
6. 做 Python-to-C++ numeric parity tests
7. 再进入 ROS2 Jazzy node integration

建议 Stage 8 起始脚本：

scripts/stage08_interface_contract_check.py

建议 Stage 8 起始文档：

docs/STAGE08_INTERFACE_PLAN.md
