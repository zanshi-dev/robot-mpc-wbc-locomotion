# Stage 14.5F-R2 Final Simulation-Only Milestone Freeze

Scope: final freeze of Stage 14.5 simulation-only MPC/WBC candidate evidence.

This step freezes the Stage 14.5A-F-R1 evidence chain. It does not run MuJoCo, does not modify any runner, and does not claim hardware readiness.

## Result

- pass: True
- failed_checks: []
- stage14_5_final_simulation_only_milestone_freeze: True
- validated_candidate_scale_max_simulation_only: 0.1

## Evidence index counts

- summary_count: 17
- doc_count: 17
- key_csv_count: 10
- indexed_artifact_count: 47

## Baseline evidence

- control_mode: baseline
- total_steps: 2400
- pass: True
- min_z: 0.274552192756
- max_abs_roll: 0.056707402709
- max_abs_pitch: 0.04832948253
- max_tau_total_abs: 9.659563043535
- qp_fail_steps: 0
- saturation_steps: 0

## MPC-assisted candidate evidence

- control_mode: mpc_assisted_candidate
- total_steps: 2400
- candidate_scale: 0.05
- candidate_row_count: 100
- pass: True
- min_z: 0.276975761939
- max_abs_roll: 0.102952660101
- max_abs_pitch: 0.053162351948
- max_tau_total_abs: 10.019186119959
- max_tau_candidate_abs: 19.4425094473
- max_tau_candidate_scaled_abs: 0.972125472365
- qp_fail_steps: 0
- saturation_steps: 0

## Robustness envelope evidence

- planned_scales: [0.0, 0.02, 0.05, 0.1]
- scale_zero_policy: baseline_reference_existing_r3_r2_evidence_no_candidate_runner_zero_scale
- validated_candidate_scale_max_simulation_only: 0.1
- scale_count: 4
- candidate_run_count: 3
- baseline_reference_count: 1
- min_z_min_over_entries: 0.273040429683
- max_abs_roll_max_over_entries: 0.102952660101
- max_abs_pitch_max_over_entries: 0.077452968358
- max_tau_total_abs_max_over_entries: 10.59512016256
- max_tau_candidate_scaled_abs_max_over_candidate_runs: 1.94425094473
- total_qp_fail_steps: 0
- total_saturation_steps: 0

## Boundary

- simulation_only_project: true
- hardware_deployment_completed: false
- torque_enable_ready: false
- torque_publisher_enabled: false
- real_robot_torque_commanded: false
- ros_publisher_used: false
- final_milestone_freeze_only: true
- mujoco_rollout_executed_in_f2: false
- mujoco_sim_data_ctrl_used_in_f2: false
- mujoco_closed_loop_ab_executed_in_f2: false
- runner_modified_in_f2: false

## Safe final conclusion

Stage 14.5 completed simulation-only MPC/WBC candidate evidence packaging and robustness indexing up to candidate scale 0.10.

Do not rewrite this as hardware readiness, torque-enable readiness, real robot torque execution, or direct MPC joint-torque output.

## Frozen artifacts

- final summary: `results/logs_sample/stage14_5f_r2_final_simulation_only_milestone_freeze_summary.json`
- final manifest: `results/logs_sample/stage14_5f_r2_final_simulation_only_milestone_manifest.json`
- final doc: `docs/stage14_5f_r2_final_simulation_only_milestone_freeze.md`
