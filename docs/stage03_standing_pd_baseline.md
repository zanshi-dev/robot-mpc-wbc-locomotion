# Stage 3: Standing Controller and PD Baseline

## 目标

实现 Go1 在 MuJoCo 中的最小 joint PD 站立 baseline，验证力矩控制、standing pose、torque limit 和日志记录。

## 控制公式

tau = kp * (q_des - q) - kd * qd

其中：

- q 为 12 维关节角；
- qd 为 12 维关节速度；
- tau 为 12 维关节力矩；
- tau 会被裁剪到 torque_limit 范围内。

## MuJoCo 关节顺序

- FR_hip
- FR_thigh
- FR_calf
- FL_hip
- FL_thigh
- FL_calf
- RR_hip
- RR_thigh
- RR_calf
- RL_hip
- RL_thigh
- RL_calf

## Standing Pose

每条腿使用：

- hip = 0.0
- thigh = 0.9
- calf = -1.8

完整 q_des：

[0.0, 0.9, -1.8,
 0.0, 0.9, -1.8,
 0.0, 0.9, -1.8,
 0.0, 0.9, -1.8]

## 推荐参数

- kp = 80
- kd = 2.0
- torque_limit = 23.7

## 验证结果

1000 steps standing PD 结果：

- final_base_z = 0.274232
- final_roll = -0.000390
- final_pitch = -0.000545
- min_base_z = 0.273452
- max_abs_roll = 0.065949
- max_abs_pitch = 0.024280
- torque_saturation_count = 0

结论：Go1 可在 MuJoCo 中使用 joint PD baseline 保持 1000 steps 稳定站立。

## 运行命令

python3 scripts/stage03_standing_pd_demo.py --model assets/go1/scene.xml --steps 1000 --kp 80 --kd 2.0 --torque_limit 23.7 --log results/logs_sample/stage03_standing_pd_kp80_kd2.csv

## 日志文件

results/logs_sample/stage03_standing_pd_kp80_kd2.csv

## 注意

Stage 3 只验证站立控制，不包含 gait scheduler、swing trajectory、MPC、WBC 或 EKF。
