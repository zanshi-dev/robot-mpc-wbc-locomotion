# Stage 4: Gait Scheduler, Swing Trajectory and Foothold Planner

## 目标

实现并验证 trot contact schedule、phase 计算、stance/swing 状态机、swing trajectory 和基础 Raibert-style foothold planner。

本阶段暂不引入 MPC、WBC 或 EKF。

## 腿顺序

使用 MuJoCo 控制顺序：

- FR
- FL
- RR
- RL

## Trot Contact Schedule

对角腿分组：

- Group A: FR + RL
- Group B: FL + RR

相位偏移：

- FR: 0.0
- RL: 0.0
- FL: 0.5
- RR: 0.5

接触判断：

- phase < duty_factor: stance
- phase >= duty_factor: swing

在 duty_factor = 0.5 时，接触序列为：

- [FR, FL, RR, RL] = [1, 0, 0, 1]
- [FR, FL, RR, RL] = [0, 1, 1, 0]

## Swing Trajectory

使用 smoothstep 插值和平抛式足端抬高：

- 平面位置：p = (1 - alpha) * p_start + alpha * p_end
- alpha = smoothstep(s)
- z 方向抬脚：z += swing_height * 4 * s * (1 - s)

参数：

- swing_height = 0.06 m
- nominal foot z = 0.019 m

验证结果：

- min_z = 0.019
- max_z = 0.078904

## Foothold Planner

使用基础 Raibert-style heuristic：

p_des = p_nominal + v_cmd * T_stance / 2 + kv * (v_body - v_cmd)

当前参数：

- gait_period = 0.5 s
- duty_factor = 0.5
- stance_duration = 0.25 s
- vx_cmd = 0.2 m/s
- vx_body = 0.0 m/s
- kv = 0.03

验证结果：

- FR/FL nominal x = 0.1881 -> foothold x = 0.2071
- RR/RL nominal x = -0.1881 -> foothold x = -0.1691

## 日志文件

results/logs_sample/stage04_gait_swing_foothold_log.csv

## 运行命令

python3 scripts/stage04_gait_swing_foothold_demo.py --duration 2.0 --dt 0.01 --gait_period 0.5 --duty_factor 0.5 --swing_height 0.06 --vx_cmd 0.2 --vy_cmd 0.0 --vx_body 0.0 --vy_body 0.0 --kv 0.03

## 当前结论

Stage 4 离线 gait/swing/foothold 验证通过。下一步将 gait scheduler 和 swing trajectory 接入 MuJoCo standing PD baseline，形成 open-loop trot baseline。

## Open-loop Trot PD Baseline

在 Stage 3 standing PD baseline 基础上，加入保守 open-loop trot leg-lift：

- standing pose: [0.0, 0.9, -1.8] × 4
- swing delta q: [0.0, -0.10, 0.18]
- gait_period: 1.0 s
- duty_factor: 0.75
- kp: 80
- kd: 2.0
- torque_limit: 23.7

由于 duty_factor = 0.75，两组对角腿存在 double-support overlap，因此 contact_cmd 会出现 [1, 1, 1, 1]，这是预期行为。

### 验证结果

1000 steps 结果：

- final_base_z = 0.290198
- final_roll = 0.028324
- final_pitch = -0.038504
- min_base_z = 0.274788
- max_abs_roll = 0.086004
- max_abs_pitch = 0.053453
- torque_saturation_count = 0

结论：Stage 4 open-loop trot leg-lift baseline 通过。该 baseline 只验证 gait schedule 与周期性抬腿，不代表完整稳定行走控制。后续速度跟踪和抗扰能力由 MPC/WBC 完成。

### 运行命令

python3 scripts/stage04_open_loop_trot_pd_demo.py --steps 1000 --kp 80 --kd 2.0 --gait_period 1.0 --duty_factor 0.75 --torque_limit 23.7 --log results/logs_sample/stage04_open_loop_trot_pd_conservative_log.csv
