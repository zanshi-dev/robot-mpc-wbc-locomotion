# Stage 19.1：速度感知 scale sweep 预检查

## 1. 目标

Stage 19.1 检查 Stage 18.2 的 velocity tracking runner 是否可以作为 Stage 19 scale sweep 的派生源。

本阶段不运行新仿真，只检查 runner 能力、输出命名风险和 Stage 19.2 的输出计划。

## 2. 结果

Stage 19.1 result: pass

Failure count: 0

## 3. 关键发现

  * Stage 18.2 runner 已经记录 `target_vx`、`base_vx_fd`、`mean_vx`、`mean_abs_velocity_error` 和 `forward_displacement`。
  * Stage 18.2 runner 当前输出文件名只按 `control_mode` 区分。
  * 如果直接循环多个 candidate scale，会覆盖同一个 `mpc_assisted_candidate` 输出文件。
  * Stage 19.2 应派生 scale-tagged runner，使每个 scale 独立输出 log 和 summary。

## 4. Stage 19.2 输出计划

| scale | scale_tag | control_mode | log_csv | summary_csv |
|---:|---|---|---|---|
| 0.000 | 0p000 | baseline | `results/logs_sample/stage19_2_velocity_scale_0p000_baseline_log.csv` | `results/logs_sample/stage19_2_velocity_scale_0p000_baseline_summary.csv` |
| 0.005 | 0p005 | mpc_assisted_candidate | `results/logs_sample/stage19_2_velocity_scale_0p005_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage19_2_velocity_scale_0p005_mpc_assisted_candidate_summary.csv` |
| 0.010 | 0p010 | mpc_assisted_candidate | `results/logs_sample/stage19_2_velocity_scale_0p010_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage19_2_velocity_scale_0p010_mpc_assisted_candidate_summary.csv` |
| 0.020 | 0p020 | mpc_assisted_candidate | `results/logs_sample/stage19_2_velocity_scale_0p020_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage19_2_velocity_scale_0p020_mpc_assisted_candidate_summary.csv` |
| 0.050 | 0p050 | mpc_assisted_candidate | `results/logs_sample/stage19_2_velocity_scale_0p050_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage19_2_velocity_scale_0p050_mpc_assisted_candidate_summary.csv` |

## 5. 结论边界

Stage 19.1 只是预检查，不生成新 rollout，不声明 candidate 改善速度跟踪，也不声明完整 MPC-WBC 速度控制器完成。
