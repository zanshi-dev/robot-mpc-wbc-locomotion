# Stage 15.3：Contact-Force-to-Torque Candidate Rollout

## 1. 目标

本阶段把接触力候选进一步推进到“力矩候选统计链路”。

链路为：

```text
接触模式
-> 期望机身线加速度
-> 接触力投影求解
-> 名义 J^T f 映射
-> 关节力矩候选
-> alpha 缩放
-> 安全指标统计
```

本阶段仍然不是 MuJoCo 闭环控制，不修改 frozen mixed baseline，不接 ROS torque publisher，也不声明真实机器人可执行。

## 2. 为什么不用真实 Pinocchio Jacobian

当前阶段使用 deterministic nominal force-to-torque candidate map，只用于验证接口和安全统计链路。

原因：

1. Stage 15.2 刚完成 C++ 接触力 demo；
2. 下一步需要先验证候选力矩缩放、限幅和日志结构；
3. 直接接 Pinocchio Jacobian 和 MuJoCo 闭环会同时引入多个变量，不利于定位错误。

因此，本阶段明确记录：

```text
pinocchio_jacobian_used: false
mujoco_torque_used: false
ros_publisher_used: false
frozen_mixed_baseline_modified: false
```

## 3. 新增文件

```text
scripts/stage15_3_contact_force_candidate_rollout.py
scripts/stage15_3_validate_contact_force_candidate_rollout.py
scripts/stage15_3_validate_contact_force_candidate_rollout.sh
docs/STAGE15_3_CONTACT_FORCE_CANDIDATE_ROLLOUT.md
```

运行后生成：

```text
results/logs_sample/stage15_3_contact_force_candidate_rollout.csv
results/logs_sample/stage15_3_contact_force_candidate_rollout_summary.json
results/logs_sample/stage15_3_contact_force_candidate_rollout_validation.csv
results/logs_sample/stage15_3_contact_force_candidate_rollout_validation_summary.json
results/logs_sample/stage15_3_contact_force_candidate_rollout.log
```

## 4. 验证指标

每个 rollout step 记录：

- contact mode
- base simplified state: `px, pz, vx, vz`
- desired acceleration: `desired_ax, desired_az`
- contact forces for four feet
- net contact force
- swing force norm
- stance normal force range
- friction violation
- normal force violation
- 12D torque candidate
- alpha-scaled torque metrics

验证条件：

```text
total_steps == 2400
swing leg force == 0
friction violation == 0
normal force violation == 0
final vx error <= 0.03 m/s
final z error <= 0.02 m
alpha 0.10 scaled torque within limit
alpha 0.20 scaled torque within limit
```

## 5. 运行方式

```bash
bash scripts/stage15_3_validate_contact_force_candidate_rollout.sh
```

通过标志：

```text
stage15_3_result: pass
```

## 6. 当前边界

本阶段只支持以下结论：

```text
接触力候选可以生成满足约束的四足接触力；
接触力候选可以映射为 12 维关节力矩候选；
alpha = 0.00 / 0.02 / 0.05 / 0.10 / 0.20 的缩放统计可验证；
候选链路没有修改 frozen mixed baseline；
候选链路没有发布 ROS torque；
候选链路没有执行 MuJoCo torque。
```

本阶段不支持以下结论：

```text
真实机器人部署完成；
真实机器人关节力矩执行完成；
Pinocchio Jacobian 已接入；
MuJoCo torque 闭环已接入；
MPC/WBC 已替代 mixed baseline。
```

## 7. 后续方向

Stage 15.4 建议接入 Pinocchio 或已有 MuJoCo-Pinocchio 映射，替换当前 nominal candidate map：

```text
contact force candidate
-> Pinocchio foot Jacobian
-> J^T f torque candidate
-> alpha sweep
-> frozen mixed baseline AB test
```

Stage 15.5 再考虑 MuJoCo torque rollout。
