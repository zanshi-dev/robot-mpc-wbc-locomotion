# Stage 20.1：推荐 scale replay 可复现性预检查

## 1. 目标

Stage 20.1 检查 Stage 19.2 的 scale-tagged velocity sweep runner 是否可作为 Stage 20 replay reproducibility audit 的派生源。

本阶段不运行新仿真，只检查 runner 能力、输出命名需求和 Stage 20.2 的 replay 输出计划。

## 2. 结果

Stage 20.1 result: pass

Failure count: 0

## 3. 关键发现

  * Stage 19.2 runner 已经记录 `target_vx`、`base_vx_fd`、`mean_vx`、`mean_abs_velocity_error`、`forward_displacement` 和稳定性边界指标。
  * Stage 19.2 runner 的输出文件属于 Stage 19 命名空间，不应直接用于 Stage 20 证据。
  * Stage 20.2 应派生 replay-specific runner，在输出文件名中同时包含 `run_id` 和 `scale_tag`。
  * Stage 20.2 只 replay 三个锚点：baseline 0.000、recommended scale 0.010、regression anchor 0.020。

## 4. Stage 20.2 输出计划

| run_id | scale | scale_tag | control_mode | log_csv | summary_csv |
|---|---:|---|---|---|---|
| run_00 | 0.000 | 0p000 | baseline | `results/logs_sample/stage20_2_replay_run_00_0p000_baseline_log.csv` | `results/logs_sample/stage20_2_replay_run_00_0p000_baseline_summary.csv` |
| run_00 | 0.010 | 0p010 | mpc_assisted_candidate | `results/logs_sample/stage20_2_replay_run_00_0p010_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage20_2_replay_run_00_0p010_mpc_assisted_candidate_summary.csv` |
| run_00 | 0.020 | 0p020 | mpc_assisted_candidate | `results/logs_sample/stage20_2_replay_run_00_0p020_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage20_2_replay_run_00_0p020_mpc_assisted_candidate_summary.csv` |
| run_01 | 0.000 | 0p000 | baseline | `results/logs_sample/stage20_2_replay_run_01_0p000_baseline_log.csv` | `results/logs_sample/stage20_2_replay_run_01_0p000_baseline_summary.csv` |
| run_01 | 0.010 | 0p010 | mpc_assisted_candidate | `results/logs_sample/stage20_2_replay_run_01_0p010_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage20_2_replay_run_01_0p010_mpc_assisted_candidate_summary.csv` |
| run_01 | 0.020 | 0p020 | mpc_assisted_candidate | `results/logs_sample/stage20_2_replay_run_01_0p020_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage20_2_replay_run_01_0p020_mpc_assisted_candidate_summary.csv` |
| run_02 | 0.000 | 0p000 | baseline | `results/logs_sample/stage20_2_replay_run_02_0p000_baseline_log.csv` | `results/logs_sample/stage20_2_replay_run_02_0p000_baseline_summary.csv` |
| run_02 | 0.010 | 0p010 | mpc_assisted_candidate | `results/logs_sample/stage20_2_replay_run_02_0p010_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage20_2_replay_run_02_0p010_mpc_assisted_candidate_summary.csv` |
| run_02 | 0.020 | 0p020 | mpc_assisted_candidate | `results/logs_sample/stage20_2_replay_run_02_0p020_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage20_2_replay_run_02_0p020_mpc_assisted_candidate_summary.csv` |

## 5. 结论边界

Stage 20.1 只是预检查，不生成新 replay rollout，不声明 scale=0.010 可直接用于真实机器人，也不声明完整 MPC-WBC 速度控制器完成。
