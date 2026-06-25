# Stage 25.3：primary_mpc_wbc smoke rollout

## 1. 目标

Stage 25.3 运行 simulation-only `primary_mpc_wbc` smoke rollout，验证 Stage 25.2 新增的控制模式是否能进入 MuJoCo torque loop。

本阶段不做真实机器人实验，不做硬件 torque enablement。

## 2. 结果

Stage 25.3 result: pass

Failure count: 0

primary_mpc_wbc_executed: True

rollout_evidence_generated: True

runner_returncode: 2

runner_process_returned_stability_failure: True

smoke_stability_pass: False

runner_log_row_count: 2400

runner_summary_csv:

    results/logs_sample/stage25_2_primary_mpc_wbc_rollout_nominal_primary_primary_mpc_wbc_summary.csv

runner_log_csv:

    results/logs_sample/stage25_2_primary_mpc_wbc_rollout_nominal_primary_primary_mpc_wbc_log.csv

## 3. 关键 summary

{
  "stage": "25.2",
  "source_stage": "14.5D-R6",
  "velocity_metric_source": "finite_difference_from_qpos0",
  "target_vx": "0.200000000000",
  "initial_x": "0.000000000000",
  "final_x": "-0.106363121452",
  "forward_displacement": "-0.106363121452",
  "initial_y": "0.000000000000",
  "final_y": "-0.848286824952",
  "lateral_displacement": "-0.848286824952",
  "mean_vx": "-0.022147532394",
  "mean_abs_velocity_error": "0.248176580076",
  "max_abs_velocity_error": "0.850819400529",
  "control_mode": "primary_mpc_wbc",
  "simulation_only_project": "True",
  "hardware_deployment_completed": "False",
  "torque_enable_ready": "False",
  "torque_publisher_enabled": "False",
  "control_law_changed": "True",
  "mixed_baseline_modified": "False",
  "mpc_assisted_candidate_switch_present": "True",
  "mpc_assisted_candidate_executed": "False",
  "primary_mpc_wbc_mode_present": "True",
  "primary_mpc_wbc_executed": "True",
  "primary_mpc_wbc_simulation_only": "True",
  "mpc_assisted_candidate_scale": "0.0",
  "scale_tag": "primary",
  "perturbation_id": "nominal",
  "perturbation_type": "none",
  "perturb_vx": "0.0",
  "perturb_vy": "0.0",
  "perturb_yawrate": "0.0",
  "run_id": "stage25_3_primary_mpc_wbc_smoke",
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
  "final_z": "0.271131937121",
  "min_z": "0.238243397800",
  "max_z": "0.307841065959",
  "delta_z": "-0.013673909362",
  "final_roll": "0.332761189180",
  "final_pitch": "-0.136434426712",
  "max_abs_roll": "0.488712369676",
  "roll_margin_to_0p20": "-0.288712369676",
  "max_abs_pitch": "0.356235143697",
  "pitch_margin_to_0p20": "-0.156235143697",
  "z_margin_to_0p22": "0.018243397800",
  "max_joint_error": "0.980273239292",
  "max_swing_joint_error": "0.915656293921",
  "max_stance_joint_error": "0.980273239292",
  "max_tau_stance_pd_abs": "71.264532613097",
  "max_tau_stance_wbc_abs": "4.377325607949",
  "max_tau_swing_pd_abs": "75.856574627963",
  "max_tau_baseline_raw_abs": "75.856574627963",
  "max_tau_candidate_abs": "19.442509447300",
  "max_tau_candidate_scaled_abs": "0.000000000000",
  "max_tau_primary_mpc_wbc_raw_abs": "75.856574627963",
  "max_tau_total_raw_abs": "75.856574627963",
  "max_tau_total_abs": "23.700000000000",
  "max_cmd_step_jump_norm": "75.765840020908",
  "max_cmd_step_jump_abs": "31.410597942610",
  "max_dyn_res_norm": "9.986467556927e-05",
  "max_stance_acc_res_norm": "4.316273593820e-06",
  "max_swing_acc_error_norm": "6.740142379812e+00",
  "qp_fail_steps": "0",
  "saturation_steps": "555",
  "pass": "False",
  "pass_margin": "False"
}

## 4. 当前支持的表述

Stage 25.3 支持：

    primary_mpc_wbc 模式已被实际执行；
    MPC/WBC candidate torque 已作为 primary stance torque 进入 simulation-only MuJoCo torque loop；
    swing leg PD 和 torque safety filter 仍在链路中；
    已生成 smoke rollout log / summary 证据；
    当前 smoke_stability_pass=False，说明 primary_mpc_wbc 直接主控模式尚未稳定。

## 5. 当前不支持的表述

Stage 25.3 不支持：

  * 不支持真实机器人闭环；
  * 不支持 hardware torque enablement；
  * 不支持复杂地形或外力冲击鲁棒性；
  * 如果 smoke_stability_pass=False，则不支持 primary_mpc_wbc 已稳定闭环运行。
