# Stage 21.2：局部扰动 rollout 证据

## 1. 目标

Stage 21.2 基于 Stage 20.2 replay runner 派生 local perturbation runner，并运行以下组合：

  * perturbation cases: nominal / x_plus / x_minus / y_plus / y_minus / yaw_plus / yaw_minus
  * scale anchors: 0.000 / 0.010 / 0.020

共 21 组 simulation-only rollout。

## 2. 结果

Stage 21.2 result: pass

Failure count: 0

Target vx: 0.2 m/s

Case count: 21

Stability pass count: 21

## 3. Local perturbation 表

| perturbation_id | scale | mean_vx | mean_abs_velocity_error | forward_displacement | min_z | max_abs_roll | max_abs_pitch | qp_fail_steps | saturation_steps | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nominal | 0.000 | 0.131362 | 0.078494 | 0.630505 | 0.274552 | 0.056707 | 0.048329 | 0 | 0 | True |
| nominal | 0.010 | 0.171348 | 0.065265 | 0.822437 | 0.274952 | 0.073652 | 0.084148 | 0 | 0 | True |
| nominal | 0.020 | 0.066640 | 0.147469 | 0.319838 | 0.273040 | 0.090250 | 0.064959 | 0 | 0 | True |
| x_plus | 0.000 | 0.131362 | 0.078494 | 0.630505 | 0.274552 | 0.056707 | 0.048329 | 0 | 0 | True |
| x_plus | 0.010 | 0.171348 | 0.065265 | 0.822437 | 0.274952 | 0.073652 | 0.084148 | 0 | 0 | True |
| x_plus | 0.020 | 0.066640 | 0.147469 | 0.319838 | 0.273040 | 0.090250 | 0.064959 | 0 | 0 | True |
| x_minus | 0.000 | 0.131362 | 0.078494 | 0.630505 | 0.274552 | 0.056707 | 0.048329 | 0 | 0 | True |
| x_minus | 0.010 | 0.171348 | 0.065265 | 0.822437 | 0.274952 | 0.073652 | 0.084148 | 0 | 0 | True |
| x_minus | 0.020 | 0.066640 | 0.147469 | 0.319838 | 0.273040 | 0.090250 | 0.064959 | 0 | 0 | True |
| y_plus | 0.000 | 0.131362 | 0.078494 | 0.630505 | 0.274552 | 0.056707 | 0.048329 | 0 | 0 | True |
| y_plus | 0.010 | 0.171348 | 0.065265 | 0.822437 | 0.274952 | 0.073652 | 0.084148 | 0 | 0 | True |
| y_plus | 0.020 | 0.066640 | 0.147469 | 0.319838 | 0.273040 | 0.090250 | 0.064959 | 0 | 0 | True |
| y_minus | 0.000 | 0.131362 | 0.078494 | 0.630505 | 0.274552 | 0.056707 | 0.048329 | 0 | 0 | True |
| y_minus | 0.010 | 0.171348 | 0.065265 | 0.822437 | 0.274952 | 0.073652 | 0.084148 | 0 | 0 | True |
| y_minus | 0.020 | 0.066640 | 0.147469 | 0.319838 | 0.273040 | 0.090250 | 0.064959 | 0 | 0 | True |
| yaw_plus | 0.000 | 0.131362 | 0.078494 | 0.630505 | 0.274552 | 0.056707 | 0.048329 | 0 | 0 | True |
| yaw_plus | 0.010 | 0.171348 | 0.065265 | 0.822437 | 0.274952 | 0.073652 | 0.084148 | 0 | 0 | True |
| yaw_plus | 0.020 | 0.066640 | 0.147469 | 0.319838 | 0.273040 | 0.090250 | 0.064959 | 0 | 0 | True |
| yaw_minus | 0.000 | 0.131362 | 0.078494 | 0.630505 | 0.274552 | 0.056707 | 0.048329 | 0 | 0 | True |
| yaw_minus | 0.010 | 0.171348 | 0.065265 | 0.822437 | 0.274952 | 0.073652 | 0.084148 | 0 | 0 | True |
| yaw_minus | 0.020 | 0.066640 | 0.147469 | 0.319838 | 0.273040 | 0.090250 | 0.064959 | 0 | 0 | True |

## 4. 生成文件

    scripts/stage21_2_local_perturbation_runner.py
    scripts/stage21_2_run_local_perturbation_rollouts.py
    scripts/stage21_2_validate_local_perturbation_rollouts.py
    results/logs_sample/stage21_2_local_perturbation_execution.csv
    results/logs_sample/stage21_2_local_perturbation_execution_summary.json
    results/logs_sample/stage21_2_local_perturbation_validation.csv
    results/logs_sample/stage21_2_local_perturbation_table.csv
    results/logs_sample/stage21_2_local_perturbation_table.md
    results/logs_sample/stage21_2_local_perturbation_summary.json

## 5. 结论边界

Stage 21.2 只生成 simulation-only local perturbation rollout 数据。是否确认 scale=0.010 的推荐关系在局部扰动下仍然成立，需要在 Stage 21.3 中基于速度误差、前向位移和稳定性边界进一步分析。
