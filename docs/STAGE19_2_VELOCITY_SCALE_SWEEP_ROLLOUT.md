# Stage 19.2：速度感知 candidate scale sweep rollout

## 1. 目标

Stage 19.2 基于 Stage 18.2 的 velocity tracking runner，派生带 scale tag 的 rollout runner，并运行不同 MPC/WBC candidate scale 的速度感知 sweep。

本阶段用于生成数据，不直接声明 candidate 改善速度跟踪。

## 2. 结果

Stage 19.2 result: pass

Failure count: 0

Target vx: 0.2 m/s

Case count: 5

Stability pass count: 5

## 3. Sweep 表

| scale | mean_vx | mean_abs_velocity_error | forward_displacement | min_z | max_abs_roll | max_abs_pitch | qp_fail_steps | saturation_steps | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.000 | 0.131362 | 0.078494 | 0.630505 | 0.274552 | 0.056707 | 0.048329 | 0 | 0 | True |
| 0.005 | 0.172518 | 0.085663 | 0.828054 | 0.273834 | 0.109772 | 0.064034 | 0 | 0 | True |
| 0.010 | 0.171348 | 0.065265 | 0.822437 | 0.274952 | 0.073652 | 0.084148 | 0 | 0 | True |
| 0.020 | 0.066640 | 0.147469 | 0.319838 | 0.273040 | 0.090250 | 0.064959 | 0 | 0 | True |
| 0.050 | 0.144905 | 0.089988 | 0.695506 | 0.276976 | 0.102953 | 0.053162 | 0 | 0 | True |

## 4. 生成文件

    scripts/stage19_2_velocity_scale_sweep_runner.py
    scripts/stage19_2_run_velocity_scale_sweep.py
    scripts/stage19_2_validate_velocity_scale_sweep.py
    results/logs_sample/stage19_2_velocity_scale_sweep_execution.csv
    results/logs_sample/stage19_2_velocity_scale_sweep_execution_summary.json
    results/logs_sample/stage19_2_velocity_scale_sweep_table.csv
    results/logs_sample/stage19_2_velocity_scale_sweep_table.md
    results/logs_sample/stage19_2_velocity_scale_sweep_validation.csv
    results/logs_sample/stage19_2_velocity_scale_sweep_summary.json

## 5. 结论边界

Stage 19.2 只生成 simulation-only velocity-aware scale sweep 数据。是否存在推荐 scale 区间，需要在 Stage 19.3 中基于速度误差、前向位移和稳定性边界进一步分析。
