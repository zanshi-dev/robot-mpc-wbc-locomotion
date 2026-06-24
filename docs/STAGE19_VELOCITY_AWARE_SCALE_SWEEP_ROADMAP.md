# Stage 19：速度感知的 candidate scale sweep 路线图

## 1. 背景

Stage 17 已完成 simulation-only conservative closed-loop rollout evidence，证明低尺度 MPC/WBC candidate injection 没有破坏高度、姿态、QP failure 和 torque saturation 边界。

Stage 18 补齐了速度跟踪证据，新增 base_x、base_vx_fd、target_vx、mean_vx、mean_abs_velocity_error 和 forward_displacement 等指标。

Stage 18 的关键结论是：

    在 target_vx=0.2 m/s 测试中，baseline 与 scale=0.02 的低尺度 MPC/WBC candidate injection 均通过稳定性和安全边界；
    但 baseline 的速度跟踪优于 candidate。
    因此不能声明 candidate 改善速度跟踪。

## 2. Stage 19 目标

Stage 19 的目标不是直接改控制器，而是进一步回答：

    不同 MPC/WBC candidate scale 对速度跟踪和稳定性边界的影响是什么？
    scale=0.02 的速度退化是否随 scale 增大而加重？
    是否存在更小的 candidate scale，在稳定性通过的同时，对速度跟踪影响较小？

## 3. 推荐 scale 设置

Stage 19 初始 scale sweep 使用：

    baseline: 0.00
    candidate: 0.005
    candidate: 0.010
    candidate: 0.020
    candidate: 0.050

其中：

    scale=0.00 作为 baseline reference；
    scale=0.02 对应 Stage 18.2 已验证的 candidate case；
    scale=0.005 和 0.010 用于观察更低注入强度；
    scale=0.050 用于观察速度退化是否进一步加重。

## 4. 需要记录的指标

每个 scale 至少记录：

    target_vx
    mean_vx
    mean_abs_velocity_error
    max_abs_velocity_error
    forward_displacement
    min_z
    max_abs_roll
    max_abs_pitch
    qp_fail_steps
    saturation_steps
    max_tau_total_abs
    max_tau_candidate_scaled_abs
    pass

## 5. 判断逻辑

Stage 19 不追求证明 candidate 更优，而是做工程审计：

    若所有 scale 均稳定，但 velocity error 随 scale 增大而增大，则说明当前 candidate 注入对速度跟踪有负面影响；
    若较小 scale 的 velocity error 接近 baseline，则可作为后续更保守 candidate 注入范围；
    若某些 scale 破坏稳定性或触发 saturation，则应作为不推荐范围。

## 6. Stage 19 不声明

Stage 19 不声明：

  * 已完成完整 MPC-WBC 速度控制器；
  * candidate 已改善速度跟踪；
  * MPC/WBC 全面优于 baseline；
  * 已完成真实机器人 torque 执行；
  * 已完成硬件 torque enablement。

## 7. Stage 19 可以支持的表述

完成后可支持类似表述：

    Stage 19 对 MPC/WBC candidate 注入强度进行了速度感知的 scale sweep。
    结果用于判断 candidate scale 对 mean_vx、velocity error、forward displacement 和稳定性边界的影响。
    当前证据仍限定在 simulation-only rollout，不对应真实机器人部署。

## 8. 分阶段任务

### Stage 19.0

新增路线图和验证脚本。

### Stage 19.1

检查 Stage 18.2 velocity tracking runner 是否可复用，并确认 scale sweep 输出文件命名不会覆盖。

### Stage 19.2

运行 scale sweep，生成每个 scale 的 log 和 summary。

### Stage 19.3

生成速度-稳定性综合分析表，明确推荐与不推荐 scale 区间。

### Stage 19.4

同步 README、PROJECT_STATUS、ARTIFACT_INDEX，并冻结 Stage 19 证据。
