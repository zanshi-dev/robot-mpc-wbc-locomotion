# Stage 20.2：推荐 scale replay 可复现性 rollout

## 1. 目标

Stage 20.2 基于 Stage 19.2 的 scale-tagged velocity sweep runner，派生 replay-specific runner，并重复运行三个锚点：

  * baseline: scale=0.000
  * recommended candidate: scale=0.010
  * regression anchor: scale=0.020

每个锚点重复运行 3 次，生成 replay rollout evidence。

## 2. 结果

Stage 20.2 result: pass

Failure count: 0

Target vx: 0.2 m/s

Case count: 9

Stability pass count: 9

## 3. Replay 表

| run_id | scale | mean_vx | mean_abs_velocity_error | forward_displacement | min_z | max_abs_roll | max_abs_pitch | qp_fail_steps | saturation_steps | pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| run_00 | 0.000 | 0.131362 | 0.078494 | 0.630505 | 0.274552 | 0.056707 | 0.048329 | 0 | 0 | True |
| run_00 | 0.010 | 0.171348 | 0.065265 | 0.822437 | 0.274952 | 0.073652 | 0.084148 | 0 | 0 | True |
| run_00 | 0.020 | 0.066640 | 0.147469 | 0.319838 | 0.273040 | 0.090250 | 0.064959 | 0 | 0 | True |
| run_01 | 0.000 | 0.131362 | 0.078494 | 0.630505 | 0.274552 | 0.056707 | 0.048329 | 0 | 0 | True |
| run_01 | 0.010 | 0.171348 | 0.065265 | 0.822437 | 0.274952 | 0.073652 | 0.084148 | 0 | 0 | True |
| run_01 | 0.020 | 0.066640 | 0.147469 | 0.319838 | 0.273040 | 0.090250 | 0.064959 | 0 | 0 | True |
| run_02 | 0.000 | 0.131362 | 0.078494 | 0.630505 | 0.274552 | 0.056707 | 0.048329 | 0 | 0 | True |
| run_02 | 0.010 | 0.171348 | 0.065265 | 0.822437 | 0.274952 | 0.073652 | 0.084148 | 0 | 0 | True |
| run_02 | 0.020 | 0.066640 | 0.147469 | 0.319838 | 0.273040 | 0.090250 | 0.064959 | 0 | 0 | True |

## 4. 生成文件

    scripts/stage20_2_replay_reproducibility_runner.py
    scripts/stage20_2_run_replay_reproducibility.py
    scripts/stage20_2_validate_replay_reproducibility.py
    results/logs_sample/stage20_2_replay_reproducibility_execution.csv
    results/logs_sample/stage20_2_replay_reproducibility_execution_summary.json
    results/logs_sample/stage20_2_replay_reproducibility_validation.csv
    results/logs_sample/stage20_2_replay_reproducibility_table.csv
    results/logs_sample/stage20_2_replay_reproducibility_table.md
    results/logs_sample/stage20_2_replay_reproducibility_summary.json

## 5. 结论边界

Stage 20.2 只生成 simulation-only replay rollout 数据。是否确认 scale=0.010 的推荐关系可复现，需要在 Stage 20.3 中基于重复运行的均值、标准差、range 和相对排序进一步分析。
