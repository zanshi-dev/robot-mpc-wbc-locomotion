# Stage 15.4：Pinocchio Jacobian Candidate Rollout

## 1. 目标

本阶段把 Stage 15.3 的名义力矩候选映射升级为 Pinocchio Jacobian 候选链路。

链路为：

```text
接触模式
-> 期望机身线加速度
-> 接触力候选
-> Pinocchio FK
-> 足端位置有限差分 Jacobian
-> J^T f 关节力矩候选
-> alpha 缩放统计
-> 安全指标验证
```

## 2. 当前边界

本阶段仍然是 simulation-only / offline audit，不是 MuJoCo torque 闭环。

明确边界：

```text
pinocchio_jacobian_used: true
synthetic_kinematic_model: true
real_go1_urdf_used: false
mujoco_torque_used: false
ros_publisher_used: false
frozen_mixed_baseline_modified: false
```

也就是说，本阶段验证的是 Pinocchio Jacobian 管线，而不是完整 Go1 URDF 模型部署。

## 3. 为什么先用 synthetic kinematic model

直接接入真实 Go1 URDF/MJCF、MuJoCo 当前状态、Pinocchio frame Jacobian 和 frozen mixed baseline，会同时引入多个可能出错的变量：

- 模型文件路径
- joint order
- q/qv 状态映射
- frame name
- world/local frame 约定
- force sign
- torque sign
- baseline 混合比例

本阶段先构建一个 12 DoF Go1-like kinematic audit model，只验证：

```text
Pinocchio model 可构建；
足端位置可通过 FK 得到；
足端 Jacobian 可由有限差分得到；
J^T f 可以生成 12 维关节力矩候选；
alpha 缩放后不超过 torque limit；
候选链路不触碰 ROS torque 和 MuJoCo torque。
```

## 4. 新增文件

```text
scripts/stage15_4_pinocchio_jacobian_candidate_rollout.py
scripts/stage15_4_validate_pinocchio_jacobian_candidate_rollout.py
scripts/stage15_4_validate_pinocchio_jacobian_candidate_rollout.sh
docs/STAGE15_4_PINOCCHIO_JACOBIAN_CANDIDATE_ROLLOUT.md
```

运行后生成：

```text
results/logs_sample/stage15_4_pinocchio_jacobian_candidate_rollout.csv
results/logs_sample/stage15_4_pinocchio_jacobian_candidate_rollout_summary.json
results/logs_sample/stage15_4_pinocchio_jacobian_candidate_rollout_validation.csv
results/logs_sample/stage15_4_pinocchio_jacobian_candidate_rollout_validation_summary.json
results/logs_sample/stage15_4_pinocchio_jacobian_candidate_rollout.log
```

## 5. 验证指标

验证条件：

```text
Pinocchio imported successfully
Pinocchio audit model nq == 12
Pinocchio audit model nv == 12
foot Jacobian norm > 0
total_steps == 2400
swing leg force == 0
friction violation == 0
normal force violation == 0
final vx error <= 0.03 m/s
final z error <= 0.02 m
alpha 0.10 scaled torque within limit
alpha 0.20 scaled torque within limit
```

## 6. 运行方式

```bash
bash scripts/stage15_4_validate_pinocchio_jacobian_candidate_rollout.sh
```

通过标志：

```text
stage15_4_result: pass
```

## 7. 后续方向

Stage 15.5 建议从 synthetic kinematic model 升级到真实 Go1 模型映射审计：

```text
Go1 model path discovery
-> joint order audit
-> foot frame name audit
-> MuJoCo q/dq to Pinocchio q/v mapping
-> Pinocchio analytical frame Jacobian
-> J^T f torque candidate
-> alpha sweep
```

Stage 15.6 再考虑 MuJoCo torque rollout AB test。
