# Stage 22.4：observable qvel perturbation evidence freeze

## 1. 目标

Stage 22.4 冻结 Stage 22.0–22.3 的 qvel observable perturbation attempt 证据。

本阶段不新增控制器，不新增 rollout，只同步入口文档、生成 manifest，并冻结结论边界。

## 2. 阶段结果

| 阶段 | 结果 |
|---|---|
| 22.0 | pass |
| 22.1 | pass |
| 22.2 | pass |
| 22.3 | pass |

## 3. 核心结论

    observable_perturbation_pass: False
    perturbation_metric_variability_detected: False
    recommendation_relation_stable: True
    recommendation_observable_robust: False

Stage 22.3 analysis 通过，但 observable perturbation robustness 不成立。当前 qvel 初始速度扰动没有使 summary 指标产生可观测变化；因此 Stage 22 不能声明完成 observable perturbation robustness audit，只能记录为 qvel perturbation injection attempt。

当前证据不支持将 scale=0.010 升级为 observable-perturbation-tested recommended candidate scale；仍只能沿用 Stage 21 的 local-perturbation-tested recommended candidate scale 表述。

## 4. 当前证据支持

Stage 22 支持：

  * 完成 simulation-only qvel initial perturbation injection attempt；
  * 21 组 rollout 均通过稳定性边界；
  * `scale=0.010` 的推荐关系在当前记录指标中未被破坏；
  * 记录了 qvel 扰动未造成 summary 指标可观测变化这一 negative evidence。

## 5. 当前证据不支持

Stage 22 不支持：

  * 不支持 `scale=0.010` 升级为 observable-perturbation-tested recommended candidate scale；
  * 不支持 observable perturbation robustness claim；
  * 不支持完整 MPC-WBC 速度控制器已经完成；
  * 不支持 `scale=0.010` 可以直接用于真实机器人；
  * 不支持真实机器人 torque 执行或硬件 torque enablement 已完成；
  * 不支持复杂地形或外力冲击鲁棒性已完成。

## 6. 冻结结果

    stage22_4_result: pass
    failure_count: 0
    artifact_count: 73
