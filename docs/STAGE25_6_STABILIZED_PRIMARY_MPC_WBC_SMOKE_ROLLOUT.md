# Stage 25.6：stabilized_primary_mpc_wbc smoke rollout

## 1. 目标

Stage 25.6 运行 simulation-only `stabilized_primary_mpc_wbc` smoke rollout，验证 Stage 25.5 新增的稳定化 primary 模式是否能进入 MuJoCo torque loop。

本阶段不做真实机器人实验，不做硬件 torque enablement。

## 2. 结果

Stage 25.6 result: pass

Failure count: 0

stabilized_primary_mpc_wbc_executed: True

rollout_evidence_generated: True

runner_returncode: 0

runner_process_returned_stability_failure: False

smoke_stability_pass: True

runner_log_row_count: 2400

runner_summary_csv:

    results/logs_sample/stage25_5_stabilized_primary_mpc_wbc_rollout_nominal_stab0p05_stabilized_primary_mpc_wbc_summary.csv

runner_log_csv:

    results/logs_sample/stage25_5_stabilized_primary_mpc_wbc_rollout_nominal_stab0p05_stabilized_primary_mpc_wbc_log.csv

## 3. 关键 summary

{
  "stage": "25.5",
  "source_stage": "14.5D-R6",
  "velocity_metric_source": "finite_difference_from_qpos0",
  "target_vx": "0.200000000000",
  "initial_x": "0.000000000000",
  "final_x": "0.625069330445",
  "forward_displacement": "0.625069330445",
  "initial_y": "0.000000000000",
  "final_y": "0.298273472418",
  "lateral_displacement": "0.298273472418",
  "mean_vx": "0.130229659623",
  "mean_abs_velocity_error": "0.085217190847",
  "max_abs_velocity_error": "0.304323637613",
  "control_mode": "stabilized_primary_mpc_wbc",
  "simulation_only_project": "True",
  "hardware_deployment_completed": "False",
  "torque_enable_ready": "False",
  "torque_publisher_enabled": "False",
  "control_law_changed": "True",
  "mixed_baseline_modified": "False",
  "mpc_assisted_candidate_switch_present": "True",
  "mpc_assisted_candidate_executed": "False",
  "primary_mpc_wbc_mode_present": "True",
  "primary_mpc_wbc_executed": "False",
  "primary_mpc_wbc_simulation_only": "False",
  "stabilized_primary_mpc_wbc_mode_present": "True",
  "stabilized_primary_mpc_wbc_executed": "True",
  "stabilized_primary_mpc_wbc_simulation_only": "True",
  "stabilized_primary_scale": "0.05",
  "stabilized_primary_ramp_steps": "600",
  "stabilized_posture_residual_scale": "1.0",
  "stabilized_wbc_residual_scale": "1.0",
  "mpc_assisted_candidate_scale": "0.0",
  "scale_tag": "stab0p05",
  "perturbation_id": "nominal",
  "perturbation_type": "none",
  "perturb_vx": "0.0",
  "perturb_vy": "0.0",
  "perturb_yawrate": "0.0",
  "run_id": "stage25_6_stabilized_primary_mpc_wbc_smoke",
  "mpc_assisted_candidate_scale_max": "0.25",
  "candidate_csv": "results/logs_sample/stage14_5b_offline_mpc_force_to_torque_candidates.csv",
  "candidate_step_policy": "repeat",
  "candidate_row_count": "100",
  "candidate_available_in_run": "True",
  "real_robot_torque_commanded": "False",
  "ros_publisher_used": "False",
  "wbc_script": "scripts/stage13_2_2400step_online_full_wbc_scheduler_runner.py",
  "swing_target_csv": "results/logs_sample/stage13_2_2400step_swing_trajectory_tracking_check.csv",
  "total_steps": "2400",
  "transition_count": "11",
  "trot_FR_RL_steps": "1200",
  "trot_FL_RR_steps": "1200",
  "stance_kp": "60.0",
  "stance_kd": "2.0",
  "swing_kp": "80.0",
  "swing_kd": "2.0",
  "stance_wbc_scale": "0.2",
  "swing_pd_scale": "1.0",
  "swing_target_scale": "0.35",
  "torque_limit": "23.7",
  "initial_z": "0.284805846483",
  "final_z": "0.285182202791",
  "min_z": "0.275183959092",
  "max_z": "0.288863887724",
  "delta_z": "0.000376356308",
  "final_roll": "0.025116828244",
  "final_pitch": "0.016016866659",
  "max_abs_roll": "0.088212790238",
  "roll_margin_to_0p20": "0.111787209762",
  "max_abs_pitch": "0.050696666834",
  "pitch_margin_to_0p20": "0.149303333166",
  "z_margin_to_0p22": "0.055183959092",
  "max_joint_error": "0.071567343785",
  "max_swing_joint_error": "0.053867059918",
  "max_stance_joint_error": "0.071567343785",
  "max_tau_stance_pd_abs": "11.191082223535",
  "max_tau_stance_wbc_abs": "2.147236588743",
  "max_tau_swing_pd_abs": "10.890608907787",
  "max_tau_baseline_raw_abs": "10.890608907787",
  "max_tau_candidate_abs": "19.442509447300",
  "max_tau_candidate_scaled_abs": "0.000000000000",
  "max_tau_primary_mpc_wbc_raw_abs": "19.442509447300",
  "max_tau_stabilized_primary_mpc_wbc_raw_abs": "10.890608907787",
  "max_tau_total_raw_abs": "10.890608907787",
  "max_tau_total_abs": "10.890608907787",
  "max_cmd_step_jump_norm": "25.812044862343",
  "max_cmd_step_jump_abs": "11.462315551593",
  "max_dyn_res_norm": "8.134821720445e-08",
  "max_stance_acc_res_norm": "3.463315236026e-09",
  "max_swing_acc_error_norm": "4.095316941863e-01",
  "qp_fail_steps": "0",
  "saturation_steps": "0",
  "pass": "True",
  "pass_margin": "True"
}

## 4. 当前支持的表述

Stage 25.6 支持：

    stabilized_primary_mpc_wbc 模式已被实际执行；
    stabilized primary torque 已进入 simulation-only MuJoCo torque loop；
    ramp / scale / posture residual / WBC residual 已作为稳定化机制参与控制；
    swing leg PD 和 torque safety filter 仍在链路中；
    已生成 smoke rollout log / summary 证据。

如果 smoke_stability_pass=True，可以进一步声明：

    stabilized_primary_mpc_wbc 在当前固定仿真设置下通过 smoke stability boundary。

如果 smoke_stability_pass=False，只能声明：

    stabilized_primary_mpc_wbc 已执行，但当前默认稳定化参数仍未通过 smoke stability boundary。

## 5. 当前不支持的表述

Stage 25.6 不支持：

  * 不支持真实机器人闭环；
  * 不支持 hardware torque enablement；
  * 不支持复杂地形或外力冲击鲁棒性；
  * 不支持工程级 MPC-WBC 控制器完全成熟。
