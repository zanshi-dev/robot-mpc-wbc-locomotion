# Stage 14.5E-R1 Candidate Robustness Scale Sweep Runner

Scope: simulation-only candidate robustness scale sweep.

This step records scale=0.00 as existing baseline-reference evidence, and runs positive candidate scales with the R6 candidate-capable runner.

## Result

- pass: True
- failed_checks: []
- planned_scales: [0.0, 0.02, 0.05, 0.1]
- pass_count: 4 / 4
- candidate_run_count: 3
- baseline_reference_count: 1
- min_z_over_entries: 0.273040429683
- max_abs_roll_over_entries: 0.102952660101
- max_abs_pitch_over_entries: 0.077452968358
- max_tau_total_abs_over_entries: 10.59512016256
- max_tau_candidate_scaled_abs_over_candidate_runs: 1.94425094473
- total_qp_fail_steps: 0
- total_saturation_steps: 0

## Per-scale outputs

### scale=0.00
- evidence_source: baseline_reference
- pass: True
- failed_checks: []
- summary_csv: `results/logs_sample/stage14_5e_r1_scale_0p00_baseline_reference_summary.csv`
- log_csv: `results/logs_sample/stage14_5e_r1_scale_0p00_baseline_reference_log.csv`

### scale=0.02
- evidence_source: candidate_run
- pass: True
- failed_checks: []
- summary_csv: `results/logs_sample/stage14_5e_r1_scale_0p02_candidate_summary.csv`
- log_csv: `results/logs_sample/stage14_5e_r1_scale_0p02_candidate_log.csv`

### scale=0.05
- evidence_source: candidate_run
- pass: True
- failed_checks: []
- summary_csv: `results/logs_sample/stage14_5e_r1_scale_0p05_candidate_summary.csv`
- log_csv: `results/logs_sample/stage14_5e_r1_scale_0p05_candidate_log.csv`

### scale=0.10
- evidence_source: candidate_run
- pass: True
- failed_checks: []
- summary_csv: `results/logs_sample/stage14_5e_r1_scale_0p10_candidate_summary.csv`
- log_csv: `results/logs_sample/stage14_5e_r1_scale_0p10_candidate_log.csv`

## Boundary

- simulation_only_project: True
- mujoco_closed_loop_candidate_sweep_executed: True
- mujoco_closed_loop_ab_executed: False
- real_robot_torque_commanded: False
- ros_publisher_used: False
- torque_enable_ready: False

This is simulation-only robustness evidence. It is not hardware-readiness evidence.

## Evidence

- summary: `results/logs_sample/stage14_5e_r1_candidate_robustness_scale_sweep_summary.json`
- sweep table: `results/logs_sample/stage14_5e_r1_candidate_robustness_scale_sweep_table.csv`
