# Stage 22.1：qvel 可观测扰动注入预检查

## 1. 目标

Stage 22.1 检查 Stage 20.2 replay runner 是否可派生为 Stage 22 observable perturbation robustness audit runner。

本阶段不运行新仿真，只检查 qvel 初始速度扰动注入点、输出命名需求和 Stage 22.2 的 rollout 输出计划。

## 2. 结果

Stage 22.1 result: pass

Failure count: 0

## 3. 关键发现

  * Stage 20.2 runner 已经记录 `target_vx`、`base_vx_fd`、`mean_vx`、`mean_abs_velocity_error`、`forward_displacement` 和稳定性边界指标。
  * Stage 22.2 应派生 observable-perturbation-specific runner，避免复用 Stage 20 或 Stage 21 输出命名空间。
  * Stage 22.2 的输出文件名应同时包含 `perturbation_id` 和 `scale_tag`。
  * 初始速度扰动应在 `mujoco.MjData(model)` 创建后、rollout 开始前注入。
  * Stage 22.2 派生 runner 应新增 `mujoco.mj_forward(model, data)`，用于 qvel 修改后的状态同步。
  * Stage 22.3 必须检查 `perturbation_metric_variability_detected`，否则不能声明 observable perturbation robustness。

## 4. qvel 注入计划

    data.qvel[0] += perturb_vx
    data.qvel[1] += perturb_vy
    data.qvel[5] += perturb_yawrate

边界说明：

    这些 qvel index 只作为 MuJoCo free-joint simulation-only 初始速度扰动 anchor。
    不对应真实机器人速度扰动接口。
    不对应硬件扰动测试。

## 5. Stage 22.2 输出计划

| perturbation_id | perturb_vx | perturb_vy | perturb_yawrate | scale | control_mode | log_csv | summary_csv |
|---|---:|---:|---:|---:|---|---|---|
| nominal | 0.000000 | 0.000000 | 0.000000 | 0.000 | baseline | `results/logs_sample/stage22_2_observable_perturb_nominal_0p000_baseline_log.csv` | `results/logs_sample/stage22_2_observable_perturb_nominal_0p000_baseline_summary.csv` |
| nominal | 0.000000 | 0.000000 | 0.000000 | 0.010 | mpc_assisted_candidate | `results/logs_sample/stage22_2_observable_perturb_nominal_0p010_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage22_2_observable_perturb_nominal_0p010_mpc_assisted_candidate_summary.csv` |
| nominal | 0.000000 | 0.000000 | 0.000000 | 0.020 | mpc_assisted_candidate | `results/logs_sample/stage22_2_observable_perturb_nominal_0p020_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage22_2_observable_perturb_nominal_0p020_mpc_assisted_candidate_summary.csv` |
| vx_plus | 0.050000 | 0.000000 | 0.000000 | 0.000 | baseline | `results/logs_sample/stage22_2_observable_perturb_vx_plus_0p000_baseline_log.csv` | `results/logs_sample/stage22_2_observable_perturb_vx_plus_0p000_baseline_summary.csv` |
| vx_plus | 0.050000 | 0.000000 | 0.000000 | 0.010 | mpc_assisted_candidate | `results/logs_sample/stage22_2_observable_perturb_vx_plus_0p010_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage22_2_observable_perturb_vx_plus_0p010_mpc_assisted_candidate_summary.csv` |
| vx_plus | 0.050000 | 0.000000 | 0.000000 | 0.020 | mpc_assisted_candidate | `results/logs_sample/stage22_2_observable_perturb_vx_plus_0p020_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage22_2_observable_perturb_vx_plus_0p020_mpc_assisted_candidate_summary.csv` |
| vx_minus | -0.050000 | 0.000000 | 0.000000 | 0.000 | baseline | `results/logs_sample/stage22_2_observable_perturb_vx_minus_0p000_baseline_log.csv` | `results/logs_sample/stage22_2_observable_perturb_vx_minus_0p000_baseline_summary.csv` |
| vx_minus | -0.050000 | 0.000000 | 0.000000 | 0.010 | mpc_assisted_candidate | `results/logs_sample/stage22_2_observable_perturb_vx_minus_0p010_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage22_2_observable_perturb_vx_minus_0p010_mpc_assisted_candidate_summary.csv` |
| vx_minus | -0.050000 | 0.000000 | 0.000000 | 0.020 | mpc_assisted_candidate | `results/logs_sample/stage22_2_observable_perturb_vx_minus_0p020_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage22_2_observable_perturb_vx_minus_0p020_mpc_assisted_candidate_summary.csv` |
| vy_plus | 0.000000 | 0.030000 | 0.000000 | 0.000 | baseline | `results/logs_sample/stage22_2_observable_perturb_vy_plus_0p000_baseline_log.csv` | `results/logs_sample/stage22_2_observable_perturb_vy_plus_0p000_baseline_summary.csv` |
| vy_plus | 0.000000 | 0.030000 | 0.000000 | 0.010 | mpc_assisted_candidate | `results/logs_sample/stage22_2_observable_perturb_vy_plus_0p010_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage22_2_observable_perturb_vy_plus_0p010_mpc_assisted_candidate_summary.csv` |
| vy_plus | 0.000000 | 0.030000 | 0.000000 | 0.020 | mpc_assisted_candidate | `results/logs_sample/stage22_2_observable_perturb_vy_plus_0p020_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage22_2_observable_perturb_vy_plus_0p020_mpc_assisted_candidate_summary.csv` |
| vy_minus | 0.000000 | -0.030000 | 0.000000 | 0.000 | baseline | `results/logs_sample/stage22_2_observable_perturb_vy_minus_0p000_baseline_log.csv` | `results/logs_sample/stage22_2_observable_perturb_vy_minus_0p000_baseline_summary.csv` |
| vy_minus | 0.000000 | -0.030000 | 0.000000 | 0.010 | mpc_assisted_candidate | `results/logs_sample/stage22_2_observable_perturb_vy_minus_0p010_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage22_2_observable_perturb_vy_minus_0p010_mpc_assisted_candidate_summary.csv` |
| vy_minus | 0.000000 | -0.030000 | 0.000000 | 0.020 | mpc_assisted_candidate | `results/logs_sample/stage22_2_observable_perturb_vy_minus_0p020_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage22_2_observable_perturb_vy_minus_0p020_mpc_assisted_candidate_summary.csv` |
| yawrate_plus | 0.000000 | 0.000000 | 0.050000 | 0.000 | baseline | `results/logs_sample/stage22_2_observable_perturb_yawrate_plus_0p000_baseline_log.csv` | `results/logs_sample/stage22_2_observable_perturb_yawrate_plus_0p000_baseline_summary.csv` |
| yawrate_plus | 0.000000 | 0.000000 | 0.050000 | 0.010 | mpc_assisted_candidate | `results/logs_sample/stage22_2_observable_perturb_yawrate_plus_0p010_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage22_2_observable_perturb_yawrate_plus_0p010_mpc_assisted_candidate_summary.csv` |
| yawrate_plus | 0.000000 | 0.000000 | 0.050000 | 0.020 | mpc_assisted_candidate | `results/logs_sample/stage22_2_observable_perturb_yawrate_plus_0p020_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage22_2_observable_perturb_yawrate_plus_0p020_mpc_assisted_candidate_summary.csv` |
| yawrate_minus | 0.000000 | 0.000000 | -0.050000 | 0.000 | baseline | `results/logs_sample/stage22_2_observable_perturb_yawrate_minus_0p000_baseline_log.csv` | `results/logs_sample/stage22_2_observable_perturb_yawrate_minus_0p000_baseline_summary.csv` |
| yawrate_minus | 0.000000 | 0.000000 | -0.050000 | 0.010 | mpc_assisted_candidate | `results/logs_sample/stage22_2_observable_perturb_yawrate_minus_0p010_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage22_2_observable_perturb_yawrate_minus_0p010_mpc_assisted_candidate_summary.csv` |
| yawrate_minus | 0.000000 | 0.000000 | -0.050000 | 0.020 | mpc_assisted_candidate | `results/logs_sample/stage22_2_observable_perturb_yawrate_minus_0p020_mpc_assisted_candidate_log.csv` | `results/logs_sample/stage22_2_observable_perturb_yawrate_minus_0p020_mpc_assisted_candidate_summary.csv` |

## 6. 结论边界

Stage 22.1 只是预检查，不生成新 observable perturbation rollout，不声明 scale=0.010 可直接用于真实机器人，也不声明完整 MPC-WBC 速度控制器完成。
