# Stage 17.2: Conservative Rollout Metrics Table

## 1. 目标

Stage 17.2 将 Stage 14.5e 的 candidate robustness scale sweep 结果整理为可读指标表，用于 README、项目答辩和技术说明。

本阶段不新增控制器，不重新声明闭环性能，只做已有 simulation-only 证据的结构化整理。

## 2. 数据来源

```text
results/logs_sample/stage14_5e_r1_candidate_robustness_scale_sweep_table.csv
results/logs_sample/stage17_1_conservative_closed_loop_rollout_summary.json
```

## 3. 指标表

| scale | control_mode | pass | total_steps | min_z | z_margin_to_0p22 | max_abs_roll | roll_margin_to_0p20 | max_abs_pitch | pitch_margin_to_0p20 | max_tau_total_abs | max_tau_candidate_scaled_abs | qp_fail_steps | saturation_steps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.00 | baseline | True | 2400 | 0.274552 | 0.054552 | 0.056707 | 0.143293 | 0.048329 | 0.151671 | 9.659563 | 0.000000 | 0 | 0 |
| 0.02 | mpc_assisted_candidate | True | 2400 | 0.273040 | 0.053040 | 0.090250 | 0.109750 | 0.064959 | 0.135041 | 9.911886 | 0.388850 | 0 | 0 |
| 0.05 | mpc_assisted_candidate | True | 2400 | 0.276976 | 0.056976 | 0.102953 | 0.097047 | 0.053162 | 0.146838 | 10.019186 | 0.972125 | 0 | 0 |
| 0.10 | mpc_assisted_candidate | True | 2400 | 0.274332 | 0.054332 | 0.075194 | 0.124806 | 0.077453 | 0.122547 | 10.595120 | 1.944251 | 0 | 0 |

## 4. 结论边界

可以声明：

- 已整理 `scale=0.00 / 0.02 / 0.05 / 0.10` 的 conservative candidate rollout 指标；
- 已记录高度、姿态、力矩、QP failure、saturation 等安全边界；
- `scale=0.02` 可作为 Stage 17.1 的 conservative candidate injection 代表工况；
- 该证据属于 simulation-only closed-loop rollout evidence。

不能声明：

- 已完成真实机器人控制；
- 已完成硬件 torque enablement；
- 已完成速度跟踪性能评估；
- 已证明 MPC/WBC 全面优于 baseline；
- 已完成高性能 MPC-WBC locomotion controller。

## 5. 技术表述

推荐表述：

> 我没有直接宣称 MPC/WBC 已经全面替代 baseline，而是先做 conservative candidate injection sweep。结果表明，在 simulation-only 环境下，低尺度 candidate 注入没有破坏高度、姿态、QP 求解和力矩饱和边界；其中 scale=0.02 作为最保守工况被封装为 Stage 17.1 evidence。

