# Stage 25.5：stabilized_primary_mpc_wbc mode implementation

## 1. 目标

Stage 25.5 基于 Stage 25.4 的失败诊断，实现一个 stabilized primary_mpc_wbc variant。

该模式名称为：

    stabilized_primary_mpc_wbc

本阶段只实现 runner，不做 rollout。rollout 将在下一阶段进行。

## 2. 设计动机

Stage 25.4 表明，直接 primary_mpc_wbc 模式失败类型为：

    posture_limit_violation_with_torque_saturation_no_qp_failure

关键问题是：

  * posture limit violation；
  * torque saturation；
  * qp_fail_steps=0；
  * direct primary torque 没有稳定化机制。

因此 Stage 25.5 添加：

  * primary candidate torque scale；
  * primary candidate torque ramp；
  * stance posture residual；
  * online WBC residual；
  * 保留 swing PD；
  * 保留 torque safety filter。

## 3. Torque composition

新增模式：

    stabilized_primary_mpc_wbc

其 torque composition 为：

    stabilized_ramp = min(1.0, (step + 1) / ramp_steps)

    tau_stabilized_primary_candidate =
        stabilized_primary_scale * stabilized_ramp * stance_mask * tau_candidate

    tau_stabilized_primary_mpc_wbc_raw =
        tau_stabilized_primary_candidate
        + stabilized_posture_residual_scale * tau_stance_pd
        + stabilized_wbc_residual_scale * tau_stance_wbc
        + tau_swing_pd

所有模式仍共同经过 safety filter：

    tau_total = np.clip(tau_total_raw, -TORQUE_LIMIT, TORQUE_LIMIT)

## 4. 默认保守参数

    stabilized_primary_scale = 0.05
    stabilized_primary_ramp_steps = 600
    stabilized_posture_residual_scale = 1.0
    stabilized_wbc_residual_scale = 1.0

该默认参数的意图不是证明 full primary torque 已经稳定，而是先得到一个从 baseline residual 到 primary candidate torque 的保守稳定化入口。

## 5. 当前支持的表述

Stage 25.5 支持：

    已实现 stabilized_primary_mpc_wbc runner；
    已加入 ramp / scale / posture residual / WBC residual；
    baseline、mpc_assisted_candidate、primary_mpc_wbc 均保留；
    torque safety filter 保留。

## 6. 当前不支持的表述

Stage 25.5 不支持：

  * 不支持 stabilized_primary_mpc_wbc 已经 rollout 通过；
  * 不支持 full primary_mpc_wbc 已经稳定；
  * 不支持真实机器人闭环；
  * 不支持 hardware torque enablement；
  * 不支持复杂地形或外力冲击鲁棒性。
