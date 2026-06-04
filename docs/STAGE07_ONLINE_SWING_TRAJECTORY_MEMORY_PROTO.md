# Stage 7：Online Swing Trajectory Memory Proto

## 状态

通过。

## 目标

实现 online swing trajectory proto，并修复普通版本在 mode 切换瞬间 foot target 跳变的问题。

该版本只生成 swing foot target，不接 WBC。

## 背景

普通版本：

scripts/stage07_online_swing_trajectory_proto.py

输出：

results/logs_sample/stage07_online_swing_trajectory_proto.csv

结果：

pass = False

失败原因：

smooth_pass = False

max_step_delta_norm = 0.007500000000

原因：

mode 切换瞬间 stance/swing 角色交换，x target 从 +stride/2 跳到 -stride/2，导致 foot target 不连续。

## Memory 版本

脚本：

scripts/stage07_online_swing_trajectory_memory_proto.py

输出：

results/logs_sample/stage07_online_swing_trajectory_memory_proto.csv

results/logs_sample/stage07_online_swing_trajectory_memory_proto_summary.csv

## 核心方法

每条腿维护：

1. prev_target
2. prev_leg_state
3. lift_off_pos
4. touch_down_pos

当 leg 进入 swing：

1. lift_off_pos = prev_target
2. touch_down_pos = lift_off_pos + [stride_x, 0, 0]
3. 当前 swing 段内用 smoothstep 插值
4. z 方向加入半正弦 clearance

轨迹形式：

target = (1 - s) * lift_off_pos + s * touch_down_pos

s = smoothstep(progress)

target_z += clearance_z * sin(pi * progress)

## 配置

dt = 0.002

total_steps = 1200

period_steps = 400

half_period_steps = 200

stride_x = 0.015

clearance_z = 0.025

## 结果

transition_count = 5

swing_start_count = 12

expected_swing_start_count = 12

min_target_z = 0.020000000000

max_target_z = 0.045000000000

max_step_delta_norm = 0.000392684534

max_step_delta_z = 0.000392682933

FR_swing_samples = 600

FL_swing_samples = 600

RR_swing_samples = 600

RL_swing_samples = 600

FR_stance_samples = 600

FL_stance_samples = 600

RR_stance_samples = 600

RL_stance_samples = 600

z_pass = True

smooth_pass = True

balance_pass = True

transition_pass = True

swing_start_pass = True

pass = True

## 结论

online swing trajectory memory proto 通过。

相对普通版本，memory 版本将最大 target step jump 从：

0.007500000000

降低到：

0.000392684534

并满足平滑性检查。

该版本可作为后续 online full WBC 接入 swing foot target / swing foot acceleration target 的默认轨迹生成器。

## 当前边界

该版本仍不接 WBC。

尚未完成：

1. foot target 到 joint target 的在线 IK
2. foot target 到 swing acceleration target 的在线转换
3. 与 full WBC swing task 耦合
4. touchdown/liftoff contact feedback
5. forward velocity command
6. ROS2/C++ 实时实现

## 下一步

建议把 memory swing trajectory 接入在线 tracking 检查，但先不接 full WBC torque。

建议脚本：

scripts/stage07_online_swing_trajectory_tracking_check.py

目标：

1. 读取 memory swing target
2. 用当前站立 pose 的 foot Jacobian 做小步 IK/QP
3. 生成 swing joint target
4. 检查 joint target delta、foot target tracking error、连续性
5. 为后续接入 online full WBC 做准备

输出：

results/logs_sample/stage07_online_swing_trajectory_tracking_check.csv

results/logs_sample/stage07_online_swing_trajectory_tracking_check_summary.csv
