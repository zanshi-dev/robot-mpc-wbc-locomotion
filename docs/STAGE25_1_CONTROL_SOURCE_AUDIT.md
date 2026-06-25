# Stage 25.1：control source audit

## 1. 目标

Stage 25.1 审计当前控制链路源码入口，为 Stage 25.2 新增 primary_mpc_wbc 控制模式做准备。

本阶段只做 source audit，不修改控制器，不新增 rollout。

## 2. 结果

Stage 25.1 result: pass

Failure count: 0

Scanned source files: 324

Total audit hits: 28772

Ready for Stage 25.2 source patch planning: True

Existing primary_mpc_wbc mode found in scanned non-Stage25 source: False

## 3. Category summary

| category | hit_count | file_count | top_files |
| --- | --- | --- | --- |
| baseline_torque_generation | 2400 | 260 | scripts/stage14_5d_r9_final_simulation_only_evidence_freeze.py; scripts/stage14_5d_r3_baseline_mode_derived_runner_dry_run.py; scripts/stage14_5d_r5_mpc_candidate_injection_design_inspection.py; scripts/stage14_5d_r8_closed_loop_ab_packaging.py; scripts/stage20_3_reproducibility_analysis.py |
| mpc_wbc_candidate_torque | 3868 | 272 | scripts/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_runner.py; scripts/stage14_5d_r6_derive_mpc_assisted_candidate_runner.py; scripts/stage14_5d_r7_candidate_mode_guarded_dry_run.py; scripts/stage14_5e_r1_candidate_robustness_scale_sweep_runner.py; scripts/stage18_2_velocity_tracking_rollout_runner.py |
| candidate_scale_or_blending | 2833 | 218 | scripts/stage14_5e_r1_candidate_robustness_scale_sweep_runner.py; scripts/stage19_4_sync_and_freeze_scale_sweep_evidence.py; scripts/stage23_2_qvel_injection_trace_runner.py; scripts/stage13_2c_final_2400step_robustness_evidence_freeze.py; scripts/stage20_2_replay_reproducibility_runner.py |
| swing_leg_pd | 1367 | 83 | scripts/stage07_online_stance_pd_wbc_plus_swing_pd_sweep.py; scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py; scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py; scripts/stage13_2a_r2_create_2400step_derived_runner.py; scripts/stage14_5d_r2_closed_loop_ab_runner_skeleton.py |
| safety_filter_or_saturation | 2236 | 192 | scripts/stage10_disabled_controller_uses_safety_utilities.py; scripts/stage10_7_8_safety_utility_freeze_summary.py; scripts/stage10_clamp_watchdog_utility_without_publisher.py; scripts/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_runner.py; scripts/stage18_2_velocity_tracking_rollout_runner.py |
| mujoco_torque_write_or_step | 627 | 113 | scripts/stage15_8_mujoco_torque_smoke_test.py; scripts/stage15_10_compare_mujoco_torque_smoke_policies.py; scripts/stage15_9_mujoco_jtf_candidate_injection.py; scripts/stage15_7_mujoco_candidate_compatibility_audit.py; scripts/stage15_5_model_readiness_audit.py |
| control_mode_or_runner_args | 3463 | 202 | scripts/stage14_5d_r5_mpc_candidate_injection_design_inspection.py; scripts/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_runner.py; scripts/stage14_5d_r6_derive_mpc_assisted_candidate_runner.py; scripts/stage14_5d_r7_candidate_mode_guarded_dry_run.py; scripts/stage14_5d_r8_closed_loop_ab_packaging.py |
| qp_osqp_solve_path | 2119 | 247 | scripts/stage14_5c_mpc_force_reference_offline_qp_check.py; scripts/stage23_2_qvel_injection_trace_runner.py; scripts/stage07_full_wbc_stance_constraint_qp.py; scripts/stage14_4_base_velocity_tracking_mpc_demo.py; ros2_ws/src/robot_mpc_wbc_cpp_controller/test/test_contact_force_qp.cpp |
| contact_gait_state | 2100 | 161 | scripts/stage07_online_full_wbc_scheduler_recommended_run.py; scripts/stage07_online_full_wbc_with_scheduler_proto.py; scripts/stage13_2_2400step_online_full_wbc_scheduler_runner.py; scripts/stage04_gait_swing_foothold_demo.py; scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py |
| state_reading_mapping | 7237 | 297 | scripts/stage10_cpp_state_cache_runtime_validation.py; scripts/stage18_2_velocity_tracking_rollout_runner.py; scripts/stage18_4_sync_and_freeze_velocity_evidence.py; scripts/stage19_2_velocity_scale_sweep_runner.py; scripts/stage21_2_local_perturbation_runner.py |
| pinocchio_kinematics_dynamics | 522 | 52 | scripts/stage15_4_pinocchio_jacobian_candidate_rollout.py; scripts/stage15_6_real_model_jacobian_candidate_rollout.py; scripts/stage15_9_mujoco_jtf_candidate_injection.py; scripts/stage08_runtime_interface_adapter_module_check.py; scripts/stage15_4_validate_pinocchio_jacobian_candidate_rollout.py |
| primary_mpc_wbc_existing_mode | 0 | 0 |  |

## 4. Candidate patch files

| path | hit_count | category_count | likely_role | categories |
| --- | --- | --- | --- | --- |
| scripts/stage23_2_qvel_injection_trace_runner.py | 515 | 10 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; contact_gait_state; control_mode_or_runner_args; mpc_wbc_candidate_torque; mujoco_torque_write_or_step; qp_osqp_solve_path; safety_filter_or_saturation; state_reading_mapping; swing_leg_pd |
| scripts/stage21_2_local_perturbation_runner.py | 481 | 10 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; contact_gait_state; control_mode_or_runner_args; mpc_wbc_candidate_torque; mujoco_torque_write_or_step; qp_osqp_solve_path; safety_filter_or_saturation; state_reading_mapping; swing_leg_pd |
| scripts/stage22_2_observable_perturbation_runner.py | 475 | 10 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; contact_gait_state; control_mode_or_runner_args; mpc_wbc_candidate_torque; mujoco_torque_write_or_step; qp_osqp_solve_path; safety_filter_or_saturation; state_reading_mapping; swing_leg_pd |
| scripts/stage19_2_velocity_scale_sweep_runner.py | 474 | 10 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; contact_gait_state; control_mode_or_runner_args; mpc_wbc_candidate_torque; mujoco_torque_write_or_step; qp_osqp_solve_path; safety_filter_or_saturation; state_reading_mapping; swing_leg_pd |
| scripts/stage20_2_replay_reproducibility_runner.py | 473 | 10 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; contact_gait_state; control_mode_or_runner_args; mpc_wbc_candidate_torque; mujoco_torque_write_or_step; qp_osqp_solve_path; safety_filter_or_saturation; state_reading_mapping; swing_leg_pd |
| scripts/stage18_2_velocity_tracking_rollout_runner.py | 465 | 10 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; contact_gait_state; control_mode_or_runner_args; mpc_wbc_candidate_torque; mujoco_torque_write_or_step; qp_osqp_solve_path; safety_filter_or_saturation; state_reading_mapping; swing_leg_pd |
| scripts/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_runner.py | 423 | 10 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; contact_gait_state; control_mode_or_runner_args; mpc_wbc_candidate_torque; mujoco_torque_write_or_step; qp_osqp_solve_path; safety_filter_or_saturation; state_reading_mapping; swing_leg_pd |
| scripts/stage14_5e_r1_candidate_robustness_scale_sweep_runner.py | 370 | 7 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; control_mode_or_runner_args; mpc_wbc_candidate_torque; qp_osqp_solve_path; safety_filter_or_saturation; state_reading_mapping |
| scripts/stage14_5d_r2_closed_loop_ab_runner_skeleton.py | 312 | 10 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; contact_gait_state; control_mode_or_runner_args; mpc_wbc_candidate_torque; mujoco_torque_write_or_step; qp_osqp_solve_path; safety_filter_or_saturation; state_reading_mapping; swing_leg_pd |
| scripts/stage14_5d_r5_mpc_candidate_injection_design_inspection.py | 303 | 10 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; contact_gait_state; control_mode_or_runner_args; mpc_wbc_candidate_torque; mujoco_torque_write_or_step; qp_osqp_solve_path; safety_filter_or_saturation; state_reading_mapping; swing_leg_pd |
| scripts/stage14_5d_r9_final_simulation_only_evidence_freeze.py | 303 | 7 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; control_mode_or_runner_args; mpc_wbc_candidate_torque; qp_osqp_solve_path; safety_filter_or_saturation; state_reading_mapping |
| scripts/stage14_5d_r6_derive_mpc_assisted_candidate_runner.py | 290 | 9 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; contact_gait_state; control_mode_or_runner_args; mpc_wbc_candidate_torque; mujoco_torque_write_or_step; safety_filter_or_saturation; state_reading_mapping; swing_leg_pd |
| scripts/stage14_5e_r2_candidate_robustness_sweep_analysis_packaging.py | 272 | 7 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; control_mode_or_runner_args; mpc_wbc_candidate_torque; qp_osqp_solve_path; safety_filter_or_saturation; state_reading_mapping |
| scripts/stage14_5d_r8_closed_loop_ab_packaging.py | 268 | 9 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; contact_gait_state; control_mode_or_runner_args; mpc_wbc_candidate_torque; qp_osqp_solve_path; safety_filter_or_saturation; state_reading_mapping; swing_leg_pd |
| scripts/stage07_online_stance_pd_wbc_plus_swing_pd_sweep.py | 249 | 9 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; contact_gait_state; mpc_wbc_candidate_torque; mujoco_torque_write_or_step; qp_osqp_solve_path; safety_filter_or_saturation; state_reading_mapping; swing_leg_pd |
| scripts/stage19_4_sync_and_freeze_scale_sweep_evidence.py | 245 | 7 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; control_mode_or_runner_args; mpc_wbc_candidate_torque; qp_osqp_solve_path; safety_filter_or_saturation; state_reading_mapping |
| scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py | 239 | 10 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; contact_gait_state; control_mode_or_runner_args; mpc_wbc_candidate_torque; mujoco_torque_write_or_step; qp_osqp_solve_path; safety_filter_or_saturation; state_reading_mapping; swing_leg_pd |
| scripts/stage15_4_pinocchio_jacobian_candidate_rollout.py | 239 | 10 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; contact_gait_state; control_mode_or_runner_args; mpc_wbc_candidate_torque; pinocchio_kinematics_dynamics; qp_osqp_solve_path; safety_filter_or_saturation; state_reading_mapping; swing_leg_pd |
| scripts/stage13_2_2400step_online_full_wbc_scheduler_runner.py | 238 | 10 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; contact_gait_state; mpc_wbc_candidate_torque; mujoco_torque_write_or_step; pinocchio_kinematics_dynamics; qp_osqp_solve_path; safety_filter_or_saturation; state_reading_mapping; swing_leg_pd |
| scripts/stage07_online_full_wbc_scheduler_recommended_run.py | 235 | 10 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; contact_gait_state; mpc_wbc_candidate_torque; mujoco_torque_write_or_step; pinocchio_kinematics_dynamics; qp_osqp_solve_path; safety_filter_or_saturation; state_reading_mapping; swing_leg_pd |
| scripts/stage07_online_full_wbc_with_scheduler_proto.py | 235 | 10 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; contact_gait_state; mpc_wbc_candidate_torque; mujoco_torque_write_or_step; pinocchio_kinematics_dynamics; qp_osqp_solve_path; safety_filter_or_saturation; state_reading_mapping; swing_leg_pd |
| scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py | 233 | 9 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; contact_gait_state; mpc_wbc_candidate_torque; mujoco_torque_write_or_step; qp_osqp_solve_path; safety_filter_or_saturation; state_reading_mapping; swing_leg_pd |
| scripts/stage14_5d_r7_candidate_mode_guarded_dry_run.py | 228 | 7 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; control_mode_or_runner_args; mpc_wbc_candidate_torque; qp_osqp_solve_path; safety_filter_or_saturation; state_reading_mapping |
| scripts/stage07_online_stance_wbc_plus_swing_pd_sweep.py | 226 | 9 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; contact_gait_state; mpc_wbc_candidate_torque; mujoco_torque_write_or_step; qp_osqp_solve_path; safety_filter_or_saturation; state_reading_mapping; swing_leg_pd |
| scripts/stage14_5b_offline_mpc_force_to_torque_candidate_check.py | 222 | 9 | candidate_controller_patch_point | baseline_torque_generation; candidate_scale_or_blending; contact_gait_state; control_mode_or_runner_args; mpc_wbc_candidate_torque; pinocchio_kinematics_dynamics; qp_osqp_solve_path; safety_filter_or_saturation; state_reading_mapping |

## 5. Stage 25.2 implementation strategy

Stage 25.2 implementation strategy:

1. Select the highest-confidence runner / controller patch point from stage25_1_control_source_audit_candidate_files.csv.
2. Add a new control mode named primary_mpc_wbc.
3. Preserve existing baseline and mpc-assisted candidate injection behavior.
4. Keep three explicit final torque composition branches:
   baseline: tau_total = tau_baseline + tau_swing_pd
   mpc_assisted_candidate: tau_total = tau_baseline + alpha * tau_mpc_wbc_candidate + tau_swing_pd
   primary_mpc_wbc: tau_total = tau_mpc_wbc_candidate_as_primary_stance + tau_swing_pd
5. Keep torque safety filter after all torque composition modes.
6. If QP / WBC solve fails, record the failure and use a safe fallback.
7. Add smoke rollout evidence before baseline comparison.

## 6. 当前支持的表述

Stage 25.1 支持：

    已完成控制源码入口审计；
    已定位 baseline / MPC-WBC candidate / scale blending / swing PD / safety filter / MuJoCo step / runner args 的候选源码位置；
    可以进入 Stage 25.2 新增 simulation-only primary_mpc_wbc 控制模式。

## 7. 当前不支持的表述

Stage 25.1 不支持：

  * 不支持 primary_mpc_wbc 已实现；
  * 不支持 MPC-WBC 已作为主控闭环运行；
  * 不支持真实机器人闭环；
  * 不支持 hardware torque enablement；
  * 不支持 observable perturbation robustness；
  * 不支持复杂地形或外力冲击鲁棒性。
