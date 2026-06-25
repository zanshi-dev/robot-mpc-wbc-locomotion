# Stage 22.2：可观测 qvel 扰动 rollout 证据

## 1. 目标

Stage 22.2 基于 Stage 21.2 local perturbation runner 派生 observable qvel perturbation runner，并运行以下组合：

  * perturbation cases: nominal / vx_plus / vx_minus / vy_plus / vy_minus / yawrate_plus / yawrate_minus
  * scale anchors: 0.000 / 0.010 / 0.020

共 21 组 simulation-only rollout。

## 2. 结果

Stage 22.2 result: pass

Failure count: 0

Target vx: 0.2 m/s

Case count: 21

Stability pass count: 21

## 3. Observable perturbation 表

| perturbation_id | scale | mean_vx | mean_abs_velocity_error | forward_displacement | min_z | max_abs_roll | max_abs_pitch | qp_fail_steps | saturation_steps | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nominal | 0.000 | 0.131362 | 0.078494 | 0.630505 | 0.274552 | 0.056707 | 0.048329 | 0 | 0 | True |
| nominal | 0.010 | 0.171348 | 0.065265 | 0.822437 | 0.274952 | 0.073652 | 0.084148 | 0 | 0 | True |
| nominal | 0.020 | 0.066640 | 0.147469 | 0.319838 | 0.273040 | 0.090250 | 0.064959 | 0 | 0 | True |
| vx_plus | 0.000 | 0.131362 | 0.078494 | 0.630505 | 0.274552 | 0.056707 | 0.048329 | 0 | 0 | True |
| vx_plus | 0.010 | 0.171348 | 0.065265 | 0.822437 | 0.274952 | 0.073652 | 0.084148 | 0 | 0 | True |
| vx_plus | 0.020 | 0.066640 | 0.147469 | 0.319838 | 0.273040 | 0.090250 | 0.064959 | 0 | 0 | True |
| vx_minus | 0.000 | 0.131362 | 0.078494 | 0.630505 | 0.274552 | 0.056707 | 0.048329 | 0 | 0 | True |
| vx_minus | 0.010 | 0.171348 | 0.065265 | 0.822437 | 0.274952 | 0.073652 | 0.084148 | 0 | 0 | True |
| vx_minus | 0.020 | 0.066640 | 0.147469 | 0.319838 | 0.273040 | 0.090250 | 0.064959 | 0 | 0 | True |
| vy_plus | 0.000 | 0.131362 | 0.078494 | 0.630505 | 0.274552 | 0.056707 | 0.048329 | 0 | 0 | True |
| vy_plus | 0.010 | 0.171348 | 0.065265 | 0.822437 | 0.274952 | 0.073652 | 0.084148 | 0 | 0 | True |
| vy_plus | 0.020 | 0.066640 | 0.147469 | 0.319838 | 0.273040 | 0.090250 | 0.064959 | 0 | 0 | True |
| vy_minus | 0.000 | 0.131362 | 0.078494 | 0.630505 | 0.274552 | 0.056707 | 0.048329 | 0 | 0 | True |
| vy_minus | 0.010 | 0.171348 | 0.065265 | 0.822437 | 0.274952 | 0.073652 | 0.084148 | 0 | 0 | True |
| vy_minus | 0.020 | 0.066640 | 0.147469 | 0.319838 | 0.273040 | 0.090250 | 0.064959 | 0 | 0 | True |
| yawrate_plus | 0.000 | 0.131362 | 0.078494 | 0.630505 | 0.274552 | 0.056707 | 0.048329 | 0 | 0 | True |
| yawrate_plus | 0.010 | 0.171348 | 0.065265 | 0.822437 | 0.274952 | 0.073652 | 0.084148 | 0 | 0 | True |
| yawrate_plus | 0.020 | 0.066640 | 0.147469 | 0.319838 | 0.273040 | 0.090250 | 0.064959 | 0 | 0 | True |
| yawrate_minus | 0.000 | 0.131362 | 0.078494 | 0.630505 | 0.274552 | 0.056707 | 0.048329 | 0 | 0 | True |
| yawrate_minus | 0.010 | 0.171348 | 0.065265 | 0.822437 | 0.274952 | 0.073652 | 0.084148 | 0 | 0 | True |
| yawrate_minus | 0.020 | 0.066640 | 0.147469 | 0.319838 | 0.273040 | 0.090250 | 0.064959 | 0 | 0 | True |

## 4. 生成文件

    scripts/stage22_2_observable_perturbation_runner.py
    scripts/stage22_2_run_observable_perturbation_rollouts.py
    scripts/stage22_2_validate_observable_perturbation_rollouts.py
    results/logs_sample/stage22_2_observable_perturbation_execution.csv
    results/logs_sample/stage22_2_observable_perturbation_execution_summary.json
    results/logs_sample/stage22_2_observable_perturbation_validation.csv
    results/logs_sample/stage22_2_observable_perturbation_table.csv
    results/logs_sample/stage22_2_observable_perturbation_table.md
    results/logs_sample/stage22_2_observable_perturbation_summary.json

## 5. 结论边界

Stage 22.2 只生成 simulation-only observable qvel perturbation rollout 数据。是否确认扰动对 summary 指标产生可观测变化，以及 scale=0.010 的推荐关系是否在可观测扰动下仍然成立，需要在 Stage 22.3 中进一步分析。
