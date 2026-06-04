# Stage 7：Gait Phase Scheduler Proto

## 状态

通过。

## 目标

实现一个最小 gait phase scheduler 原型，为后续 online full WBC step loop 替换固定 mode sequence 做准备。

该版本只生成周期相位和 trot contact mode，不接入 WBC。

## 输出文件

results/logs_sample/stage07_gait_phase_scheduler_proto.csv

results/logs_sample/stage07_gait_phase_scheduler_proto_summary.csv

## 参数

dt = 0.002

total_steps = 1200

period_steps = 400

half_period_steps = 200

num_cycles = 3

## Contact Modes

### trot_FR_RL

stance legs = FR, RL

swing legs = FL, RR

### trot_FL_RR

stance legs = FL, RR

swing legs = FR, RL

## 结果

trot_FR_RL_steps = 600

trot_FL_RR_steps = 600

transition_count = 5

expected_transitions = 5

duration_pass = True

transition_pass = True

pass = True

## Mode Switch Steps

step = 0:

mode = trot_FR_RL

step = 200:

mode = trot_FL_RR

step = 400:

mode = trot_FR_RL

step = 600:

mode = trot_FL_RR

step = 800:

mode = trot_FR_RL

step = 1000:

mode = trot_FL_RR

## 结论

gait phase scheduler proto 通过。

该 scheduler 可以稳定生成：

1. 周期 phase
2. phase_step
3. mode
4. mode_step
5. phase_in_mode
6. stance legs
7. swing legs
8. swing_progress
9. transition 标记

该结果可用于替换 online full WBC step loop proto 中的固定 mode sequence。

## 当前边界

该 scheduler 仍是最小版本。

尚未包含：

1. duty factor 参数化
2. swing trajectory 在线生成
3. touchdown/liftoff 检测
4. contact state feedback
5. velocity command
6. gait start/stop 状态机

## 下一步

建议将 gait phase scheduler 接入 online full WBC step loop。

建议脚本：

scripts/stage07_online_full_wbc_with_scheduler_proto.py

目标：

1. 使用 phase scheduler 生成 contact mode
2. 每步在线求解 full WBC QP
3. 保留 low-pass torque smoothing
4. 保留 posture PD
5. 做 1200 steps 原地 trot support
6. 检查 QP failure、base_z、roll、pitch、torque saturation

输出：

results/logs_sample/stage07_online_full_wbc_with_scheduler_proto_log.csv

results/logs_sample/stage07_online_full_wbc_with_scheduler_proto_summary.csv
