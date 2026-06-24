# Stage 19.3：速度-稳定性综合分析

## 1. 目标

Stage 19.3 对 Stage 19.2 的 velocity-aware candidate scale sweep 结果进行综合分析。

分析目标不是证明 MPC/WBC candidate 全面优于 baseline，而是判断不同 candidate scale 对速度跟踪和稳定性边界的影响。

## 2. 结果

Stage 19.3 result: pass

Failure count: 0

## 3. 关键结论

当前 sweep 中所有 scale 均通过稳定性和安全边界；速度误差随 scale 变化呈非单调特征。在已测试 candidate scale 中，scale=0.010 的 mean_abs_velocity_error 最低，相对 baseline 的 delta_error=-0.013229，可作为当前更合理的低尺度 candidate 注入候选。scale=0.020 出现明显速度退化，不建议作为速度跟踪默认注入强度。

## 4. 速度-稳定性分析表

| scale | mean_vx | mean_abs_velocity_error | forward_displacement | delta_error_vs_baseline | pass | recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 0.131362 | 0.078494 | 0.630505 | 0.000000 | True | baseline_reference |
| 0.005 | 0.172518 | 0.085663 | 0.828054 | 0.007169 | True | stable_but_not_best |
| 0.010 | 0.171348 | 0.065265 | 0.822437 | -0.013229 | True | recommended_candidate |
| 0.020 | 0.066640 | 0.147469 | 0.319838 | 0.068975 | True | not_recommended_velocity_regression |
| 0.050 | 0.144905 | 0.089988 | 0.695506 | 0.011494 | True | stable_but_not_best |

## 5. 速度误差排序

| rank | scale | mean_abs_velocity_error | mean_vx | forward_displacement | recommendation |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.010 | 0.065265 | 0.171348 | 0.822437 | recommended_candidate |
| 2 | 0.000 | 0.078494 | 0.131362 | 0.630505 | baseline_reference |
| 3 | 0.005 | 0.085663 | 0.172518 | 0.828054 | stable_but_not_best |
| 4 | 0.050 | 0.089988 | 0.144905 | 0.695506 | stable_but_not_best |
| 5 | 0.020 | 0.147469 | 0.066640 | 0.319838 | not_recommended_velocity_regression |

## 6. 当前推荐

当前可推荐的候选注入强度：

    scale=0.010

推荐理由：

    在当前 target_vx=0.2 m/s 的 simulation-only sweep 中，scale=0.010 通过稳定性边界，且 mean_abs_velocity_error=0.065265，优于 baseline 的速度误差。

## 7. 当前不推荐

当前不推荐将 scale=0.020 作为速度跟踪默认注入强度。

原因：

    scale=0.020 虽然通过稳定性边界，但 mean_abs_velocity_error 明显高于 baseline 和 scale=0.010，对前向速度跟踪不利。

## 8. 结论边界

Stage 19.3 仍然只支持 simulation-only 证据结论。

不能声明：

  * 已完成完整 MPC-WBC 速度控制器；
  * MPC/WBC candidate 已全面优于 baseline；
  * 已完成真实机器人 torque 执行；
  * 已完成硬件 torque enablement。

更准确的表述是：

> Stage 19 通过速度感知 scale sweep 发现 candidate scale 对速度跟踪影响并非单调。在当前 target_vx=0.2 m/s 仿真测试中，scale=0.010 是更合理的低尺度 candidate 注入候选，而 scale=0.020 不适合作为速度跟踪默认注入强度。
