# Stage 14.5E-R2 Candidate Robustness Sweep Analysis Packaging

Scope: analysis-only packaging of E-R1 robustness sweep results.

This step analyzes the existing E-R1 sweep table. It does not rerun MuJoCo and does not modify any runner.

## Result

- pass: True
- failed_checks: []
- validated_candidate_scale_max_simulation_only: 0.1
- all_entries_pass_limits: True
- min_z_min_over_entries: 0.273040429683
- max_abs_roll_max_over_entries: 0.102952660101
- max_abs_pitch_max_over_entries: 0.077452968358
- max_tau_total_abs_max_over_entries: 10.59512016256
- max_tau_candidate_scaled_abs_max_over_candidate_runs: 1.94425094473
- total_qp_fail_steps: 0
- total_saturation_steps: 0

## Per-scale analysis

### scale=0.00
- evidence_source: baseline_reference
- limits_pass: True
- min_z: 0.274552192756
- max_abs_roll: 0.056707402709
- max_abs_pitch: 0.04832948253
- max_tau_total_abs: 9.659563043535
- max_tau_candidate_scaled_abs: 0.0
- qp_fail_steps: 0
- saturation_steps: 0

### scale=0.02
- evidence_source: candidate_run
- limits_pass: True
- min_z: 0.273040429683
- max_abs_roll: 0.090249676148
- max_abs_pitch: 0.064958727791
- max_tau_total_abs: 9.91188550792
- max_tau_candidate_scaled_abs: 0.388850188946
- qp_fail_steps: 0
- saturation_steps: 0

### scale=0.05
- evidence_source: candidate_run
- limits_pass: True
- min_z: 0.276975761939
- max_abs_roll: 0.102952660101
- max_abs_pitch: 0.053162351948
- max_tau_total_abs: 10.019186119959
- max_tau_candidate_scaled_abs: 0.972125472365
- qp_fail_steps: 0
- saturation_steps: 0

### scale=0.10
- evidence_source: candidate_run
- limits_pass: True
- min_z: 0.274332281656
- max_abs_roll: 0.075194323645
- max_abs_pitch: 0.077452968358
- max_tau_total_abs: 10.59512016256
- max_tau_candidate_scaled_abs: 1.94425094473
- qp_fail_steps: 0
- saturation_steps: 0

## Boundary

- analysis_only_packaging: True
- mujoco_rollout_executed_in_r2: False
- mujoco_closed_loop_ab_executed_in_r2: False
- real_robot_torque_commanded: False
- ros_publisher_used: False
- torque_enable_ready: False

This is simulation-only analysis evidence. It is not hardware-readiness evidence.

## Evidence

- summary: `results/logs_sample/stage14_5e_r2_candidate_robustness_sweep_analysis_summary.json`
- analysis table: `results/logs_sample/stage14_5e_r2_candidate_robustness_sweep_analysis_table.csv`
- source sweep table: `results/logs_sample/stage14_5e_r1_candidate_robustness_scale_sweep_table.csv`
