# Stage 21.1：局部扰动注入预检查

## 1. 目标

Stage 21.1 检查 Stage 20.2 replay runner 是否可派生为 Stage 21 local perturbation robustness audit runner。

本阶段不运行新仿真，只检查扰动注入点、输出命名需求和 Stage 21.2 的 rollout 输出计划。

## 2. 结果

Stage 21.1 result: pass

Failure count: 0

## 3. 关键发现

  * Stage 20.2 runner 已经记录 `target_vx`、`base_vx_fd`、`mean_vx`、`mean_abs_velocity_error`、`forward_displacement` 和稳定性边界指标。
  * Stage 21.2 应派生 perturbation-specific runner，避免复用 Stage 20 输出命名空间。
  * Stage 21.2 的输出文件名应同时包含 `perturbation_id` 和 `scale_tag`。
  * 初始状态扰动应在 rollout 开始前注入，并记录到 summary 和 per-step log 中。

## 4. Stage 21.2 输出计划

| perturbation_id | perturb_x | perturb_y | perturb_yaw | scale | control_mode | log_csv | summary_csv |
|---|---:|---:|---:|---:|---|---|---|
| nominal | 0.000000 | 0.000000 | 0.000000 | 0.000 | baseline | `results/logs_sample/stage21_2_local_perturb_nominal_0p000_baseline_log.csv` | `results/logs_sample/stage21_2_local_perturb_nominal_0p000_baseline_summary.csv` |
| nominal | 0.000000 | 0.000000 | 0.000000 | 0.010 | mpc_assisted_candidate | `results/logs_sample/stage21_2_local_perturb_nominal_0p010_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage21_2_local_perturb_nominal_0p010_mpc_assisted_candidate_summary.csv` |
| nominal | 0.000000 | 0.000000 | 0.000000 | 0.020 | mpc_assisted_candidate | `results/logs_sample/stage21_2_local_perturb_nominal_0p020_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage21_2_local_perturb_nominal_0p020_mpc_assisted_candidate_summary.csv` |
| x_plus | 0.020000 | 0.000000 | 0.000000 | 0.000 | baseline | `results/logs_sample/stage21_2_local_perturb_x_plus_0p000_baseline_log.csv` | `results/logs_sample/stage21_2_local_perturb_x_plus_0p000_baseline_summary.csv` |
| x_plus | 0.020000 | 0.000000 | 0.000000 | 0.010 | mpc_assisted_candidate | `results/logs_sample/stage21_2_local_perturb_x_plus_0p010_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage21_2_local_perturb_x_plus_0p010_mpc_assisted_candidate_summary.csv` |
| x_plus | 0.020000 | 0.000000 | 0.000000 | 0.020 | mpc_assisted_candidate | `results/logs_sample/stage21_2_local_perturb_x_plus_0p020_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage21_2_local_perturb_x_plus_0p020_mpc_assisted_candidate_summary.csv` |
| x_minus | -0.020000 | 0.000000 | 0.000000 | 0.000 | baseline | `results/logs_sample/stage21_2_local_perturb_x_minus_0p000_baseline_log.csv` | `results/logs_sample/stage21_2_local_perturb_x_minus_0p000_baseline_summary.csv` |
| x_minus | -0.020000 | 0.000000 | 0.000000 | 0.010 | mpc_assisted_candidate | `results/logs_sample/stage21_2_local_perturb_x_minus_0p010_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage21_2_local_perturb_x_minus_0p010_mpc_assisted_candidate_summary.csv` |
| x_minus | -0.020000 | 0.000000 | 0.000000 | 0.020 | mpc_assisted_candidate | `results/logs_sample/stage21_2_local_perturb_x_minus_0p020_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage21_2_local_perturb_x_minus_0p020_mpc_assisted_candidate_summary.csv` |
| y_plus | 0.000000 | 0.020000 | 0.000000 | 0.000 | baseline | `results/logs_sample/stage21_2_local_perturb_y_plus_0p000_baseline_log.csv` | `results/logs_sample/stage21_2_local_perturb_y_plus_0p000_baseline_summary.csv` |
| y_plus | 0.000000 | 0.020000 | 0.000000 | 0.010 | mpc_assisted_candidate | `results/logs_sample/stage21_2_local_perturb_y_plus_0p010_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage21_2_local_perturb_y_plus_0p010_mpc_assisted_candidate_summary.csv` |
| y_plus | 0.000000 | 0.020000 | 0.000000 | 0.020 | mpc_assisted_candidate | `results/logs_sample/stage21_2_local_perturb_y_plus_0p020_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage21_2_local_perturb_y_plus_0p020_mpc_assisted_candidate_summary.csv` |
| y_minus | 0.000000 | -0.020000 | 0.000000 | 0.000 | baseline | `results/logs_sample/stage21_2_local_perturb_y_minus_0p000_baseline_log.csv` | `results/logs_sample/stage21_2_local_perturb_y_minus_0p000_baseline_summary.csv` |
| y_minus | 0.000000 | -0.020000 | 0.000000 | 0.010 | mpc_assisted_candidate | `results/logs_sample/stage21_2_local_perturb_y_minus_0p010_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage21_2_local_perturb_y_minus_0p010_mpc_assisted_candidate_summary.csv` |
| y_minus | 0.000000 | -0.020000 | 0.000000 | 0.020 | mpc_assisted_candidate | `results/logs_sample/stage21_2_local_perturb_y_minus_0p020_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage21_2_local_perturb_y_minus_0p020_mpc_assisted_candidate_summary.csv` |
| yaw_plus | 0.000000 | 0.000000 | 0.030000 | 0.000 | baseline | `results/logs_sample/stage21_2_local_perturb_yaw_plus_0p000_baseline_log.csv` | `results/logs_sample/stage21_2_local_perturb_yaw_plus_0p000_baseline_summary.csv` |
| yaw_plus | 0.000000 | 0.000000 | 0.030000 | 0.010 | mpc_assisted_candidate | `results/logs_sample/stage21_2_local_perturb_yaw_plus_0p010_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage21_2_local_perturb_yaw_plus_0p010_mpc_assisted_candidate_summary.csv` |
| yaw_plus | 0.000000 | 0.000000 | 0.030000 | 0.020 | mpc_assisted_candidate | `results/logs_sample/stage21_2_local_perturb_yaw_plus_0p020_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage21_2_local_perturb_yaw_plus_0p020_mpc_assisted_candidate_summary.csv` |
| yaw_minus | 0.000000 | 0.000000 | -0.030000 | 0.000 | baseline | `results/logs_sample/stage21_2_local_perturb_yaw_minus_0p000_baseline_log.csv` | `results/logs_sample/stage21_2_local_perturb_yaw_minus_0p000_baseline_summary.csv` |
| yaw_minus | 0.000000 | 0.000000 | -0.030000 | 0.010 | mpc_assisted_candidate | `results/logs_sample/stage21_2_local_perturb_yaw_minus_0p010_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage21_2_local_perturb_yaw_minus_0p010_mpc_assisted_candidate_summary.csv` |
| yaw_minus | 0.000000 | 0.000000 | -0.030000 | 0.020 | mpc_assisted_candidate | `results/logs_sample/stage21_2_local_perturb_yaw_minus_0p020_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage21_2_local_perturb_yaw_minus_0p020_mpc_assisted_candidate_summary.csv` |

## 5. 结论边界

Stage 21.1 只是预检查，不生成新 local perturbation rollout，不声明 scale=0.010 可直接用于真实机器人，也不声明完整 MPC-WBC 速度控制器完成。
