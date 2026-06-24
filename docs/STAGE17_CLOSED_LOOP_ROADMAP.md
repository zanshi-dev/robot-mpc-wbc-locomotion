# Stage 17: MPC/WBC Closed-Loop MuJoCo Rollout Roadmap

## 1. Stage 17 目标

Stage 17 的目标是把当前候选力矩链路推进为 simulation-only torque-level closed-loop rollout。

目标链路：

```text
MuJoCo state
-> state mapping
-> gait scheduler
-> contact planner
-> MPC contact force reference
-> WBC / J^T f torque candidate
-> torque safety filter
-> MuJoCo actuator command
-> rollout metrics
```

## 2. 当前基线

当前稳定基线仍然是：

```text
stance posture PD
+ scaled stance WBC feedforward
+ memory-based swing target PD
+ torque safety filter
```

Stage 17 不直接废弃该基线，而是在该基线上逐步注入 MPC/WBC torque candidate。

## 3. Stage 17 不声明的内容

Stage 17.0 阶段不声明：

- 已完成真实机器人部署；
- 已完成 actuator enablement；
- 已完成真实机器人 torque execution；
- 已完成 realtime hardware controller；
- 已完成高性能 MPC-WBC locomotion；
- 已证明 MPC/WBC 全面优于 baseline。

## 4. Stage 17 可以声明的目标

完成后可以声明：

- 已完成 simulation-only torque-level closed-loop rollout 原型；
- 已完成低速 trot 场景下 MPC/WBC 候选力矩注入；
- 已完成 rollout metrics、summary、validation log 归档；
- 已完成与 mixed_online_control_baseline 的初步对照；
- 已明确失败边界和不稳定工况。

## 5. 最小验收指标

Stage 17.1 最小验收指标：

```text
target_vx: 0.2 m/s 或 0.3 m/s
rollout_time: >= 5 s
fall_rate: 0 for smoke rollout
base_height_min: 不低于安全阈值
roll/pitch: 不发散
torque_saturation_ratio: 可统计
mean_abs_velocity_error: 可统计
MPC/WBC candidate alpha: 可配置
summary json: 可生成
validation log: 可归档
```

## 6. 推荐分阶段任务

### Stage 17.0

新增 Stage 17 路线图、验收边界和验证脚本。

### Stage 17.1

新增 conservative closed-loop rollout 脚本。

优先策略：

```text
mixed_online_control_baseline
+ low-alpha MPC/WBC torque candidate
+ torque safety filter
```

### Stage 17.2

新增 rollout metrics：

```text
mean_vx
mean_abs_velocity_error
base_height_min
base_height_mean
roll_rms
pitch_rms
torque_rms
torque_max
torque_saturation_ratio
fall_flag
simulation_time
```

### Stage 17.3

新增 policy comparison：

```text
baseline only
baseline + J^T f low-alpha
baseline + MPC/WBC low-alpha
```

### Stage 17.4

更新 README、PROJECT_STATUS 和 ARTIFACT_INDEX，但只更新到 Stage 17 已完成的实际证据范围。

## 7. 面试表述边界

推荐表述：

> Stage 17 的目标是把原有 MPC/WBC 候选力矩链路推进到 MuJoCo torque-level closed-loop rollout。当前采用 conservative low-alpha injection，不直接替代已有稳定 baseline，而是通过安全限幅和指标记录验证 MPC/WBC 候选力矩对闭环运动的影响。

不推荐表述：

> 已完成真实机器人 MPC-WBC 控制器。

> 已完成高性能闭环稳定奔跑。

> MPC/WBC 已全面优于 baseline。
