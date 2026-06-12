# Stage 14.5E-R3 Final Robustness Evidence Freeze

Scope: final freeze of Stage 14.5E robustness evidence.

This step freezes the E-R0/E-R1/E-R2 robustness evidence chain. It does not run MuJoCo and does not modify any runner.

## Result

- pass: True
- failed_checks: []
- validated_candidate_scale_max_simulation_only: 0.1
- planned_scales: [0.0, 0.02, 0.05, 0.1]
- scale_zero_policy: baseline_reference_existing_r3_r2_evidence_no_candidate_runner_zero_scale
- all_scale_entries_pass: True
- all_entries_pass_limits: True

## Frozen metrics

- min_z_min_over_entries: 0.273040429683
- max_abs_roll_max_over_entries: 0.102952660101
- max_abs_pitch_max_over_entries: 0.077452968358
- max_tau_total_abs_max_over_entries: 10.59512016256
- max_tau_candidate_scaled_abs_max_over_candidate_runs: 1.94425094473
- total_qp_fail_steps: 0
- total_saturation_steps: 0

## Stage pass map

- stage14_5d_r9: True
- stage14_5e_r0: True
- stage14_5e_r1: True
- stage14_5e_r2: True

## Boundary

- analysis_freeze_only: True
- mujoco_rollout_executed_in_r3: False
- mujoco_closed_loop_ab_executed_in_r3: False
- real_robot_torque_commanded: False
- ros_publisher_used: False
- torque_enable_ready: False

This is simulation-only robustness evidence. It is not hardware-readiness evidence.

## Evidence manifest

- `results/logs_sample/stage14_5e_r3_final_robustness_evidence_manifest.json`
- `results/logs_sample/stage14_5e_r3_final_robustness_evidence_freeze_summary.json`
