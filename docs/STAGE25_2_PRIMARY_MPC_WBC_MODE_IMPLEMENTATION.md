# Stage 25.2：primary_mpc_wbc mode implementation

## 1. 目标

Stage 25.2 基于 Stage 25.1 的 source audit 结果，从 `scripts/stage23_2_qvel_injection_trace_runner.py` 派生新的 runner：

    scripts/stage25_2_primary_mpc_wbc_runner.py

并新增 simulation-only 控制模式：

    primary_mpc_wbc

本阶段只实现控制模式，不做 smoke rollout。smoke rollout 将在 Stage 25.3 进行。

## 2. 结果

Stage 25.2 result: pass

Failure count: 0

Target runner:

    scripts/stage25_2_primary_mpc_wbc_runner.py

## 3. 新增控制模式

新增：

    CONTROL_MODE_PRIMARY_MPC_WBC = "primary_mpc_wbc"

新增显式开关：

    --allow-primary-mpc-wbc

## 4. Torque composition

原有 candidate injection 结构保持为：

    tau_total_raw = tau_baseline_raw + tau_candidate_scaled

新增 primary_mpc_wbc 分支：

    tau_primary_mpc_wbc_raw = stance_mask * tau_candidate + tau_swing_pd

    if args.control_mode == CONTROL_MODE_PRIMARY_MPC_WBC:
        tau_total_raw = tau_primary_mpc_wbc_raw
    else:
        tau_total_raw = tau_baseline_raw + tau_candidate_scaled

所有模式仍共同经过 safety filter：

    tau_total = np.clip(tau_total_raw, -TORQUE_LIMIT, TORQUE_LIMIT)

最终仍写入 MuJoCo：

    data.ctrl[:] = tau_total
    mujoco.mj_step(model, data)

## 5. 当前支持的表述

Stage 25.2 支持：

    已新增 simulation-only primary_mpc_wbc runner；
    primary_mpc_wbc 模式将 MPC/WBC candidate torque 作为 stance primary torque；
    swing leg PD 保留；
    torque safety filter 保留；
    baseline 和 mpc_assisted_candidate 模式保留。

## 6. 当前不支持的表述

Stage 25.2 不支持：

  * 不支持 primary_mpc_wbc 已经完成 rollout 验证；
  * 不支持 MPC-WBC 主控闭环已经稳定运行；
  * 不支持真实机器人闭环；
  * 不支持 hardware torque enablement；
  * 不支持 observable perturbation robustness；
  * 不支持复杂地形或外力冲击鲁棒性。

## 7. Patch notes

[
  {
    "patch": "add_primary_control_mode_constant",
    "status": "APPLIED",
    "detail": "CONTROL_MODE_PRIMARY_MPC_WBC"
  },
  {
    "patch": "extend_control_mode_choices",
    "status": "APPLIED",
    "detail": "--control-mode argparse choices include primary_mpc_wbc"
  },
  {
    "patch": "add_allow_primary_flag",
    "status": "APPLIED",
    "detail": "--allow-primary-mpc-wbc"
  },
  {
    "patch": "replace_mode_validation_and_candidate_loading",
    "status": "APPLIED",
    "detail": "load candidate rows for primary_mpc_wbc"
  },
  {
    "patch": "candidate_fetch_for_primary",
    "status": "APPLIED",
    "detail": "candidate_row_for_step branch"
  },
  {
    "patch": "add_max_tau_primary_metric",
    "status": "APPLIED",
    "detail": "max_tau_primary_mpc_wbc_raw_abs"
  },
  {
    "patch": "replace_torque_composition",
    "status": "APPLIED",
    "detail": "primary branch before safety clip"
  },
  {
    "patch": "add_tau_primary_abs_per_step",
    "status": "APPLIED",
    "detail": "tau_primary_mpc_wbc_raw_abs"
  },
  {
    "patch": "update_max_tau_primary_metric",
    "status": "APPLIED",
    "detail": "max_tau_primary_mpc_wbc_raw_abs update"
  },
  {
    "patch": "add_log_tau_primary_column",
    "status": "APPLIED",
    "detail": "log column"
  },
  {
    "patch": "add_primary_summary_flags",
    "status": "APPLIED",
    "detail": "primary_mpc_wbc summary flags"
  },
  {
    "patch": "candidate_available_for_primary",
    "status": "APPLIED",
    "detail": "candidate_available_in_run"
  },
  {
    "patch": "add_summary_primary_tau_metric",
    "status": "APPLIED",
    "detail": "summary metric"
  }
]
