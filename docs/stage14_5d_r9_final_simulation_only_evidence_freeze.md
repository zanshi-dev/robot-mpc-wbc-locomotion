# Stage 14.5D-R9 Final Simulation-only Evidence Freeze

Scope: final evidence freeze for Stage 14.5D.

This document freezes the simulation-only MPC-to-WBC closed-loop evidence chain. It does not rerun MuJoCo and does not modify any runner.

## Result

- pass: True
- failed_checks: []

## Stage pass map

- stage14_5a: True
- stage14_5b: True
- stage14_5c: True
- stage14_5d_r0: True
- stage14_5d_r1: True
- stage14_5d_r2: True
- stage14_5d_r3: True
- stage14_5d_r4: True
- stage14_5d_r5: True
- stage14_5d_r6: True
- stage14_5d_r7: True
- stage14_5d_r8: True

## Baseline vs candidate evidence

- baseline control mode: baseline
- baseline total steps: 2400
- candidate control mode: mpc_assisted_candidate
- candidate total steps: 2400
- candidate scale: 0.05
- candidate row count: 100
- candidate max scaled torque candidate abs: 0.972125472365

## Key stability metrics

- baseline min_z: 0.274552192756
- candidate min_z: 0.276975761939
- baseline max_abs_roll: 0.056707402709
- candidate max_abs_roll: 0.102952660101
- baseline max_abs_pitch: 0.04832948253
- candidate max_abs_pitch: 0.053162351948
- baseline max_tau_total_abs: 9.659563043535
- candidate max_tau_total_abs: 10.019186119959
- baseline qp_fail_steps: 0
- candidate qp_fail_steps: 0
- baseline saturation_steps: 0
- candidate saturation_steps: 0

## Boundary

- simulation_only_project: True
- hardware_deployment_completed: False
- torque_enable_ready: False
- torque_publisher_enabled: False
- real_robot_torque_commanded: False
- ros_publisher_used: False
- frozen_baseline_source_modified: False
- mujoco_closed_loop_ab_final_evidence_packaged: True
- mujoco_closed_loop_ab_rerun_executed_in_r9: False

This is simulation-only evidence. It is not hardware-readiness evidence and does not claim torque-enable readiness.

## Evidence manifest

- `results/logs_sample/stage14_5d_r9_final_simulation_only_evidence_manifest.json`
- `results/logs_sample/stage14_5d_r9_final_simulation_only_evidence_freeze_summary.json`
- `results/logs_sample/stage14_5d_r8_closed_loop_ab_comparison_table.csv`
