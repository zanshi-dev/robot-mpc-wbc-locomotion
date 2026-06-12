# Stage 14.5 Simulation-Only MPC/WBC Milestone Release Note Draft

Status: draft release note generated from frozen local evidence.

## Scope

Stage 14.5 connects the offline MPC contact-force reference evidence to simulation-only WBC/QP-side candidate evaluation and robustness packaging.

The evidence is simulation-only. It does not claim hardware deployment, torque-enable readiness, ROS torque publishing, or real robot torque execution.

## Completed evidence chain

- Stage 14.5A: MPC/WBC integration preflight inventory.
- Stage 14.5B: offline MPC contact-force to joint-torque candidate evidence through the robot model mapping layer.
- Stage 14.5C: offline MPC force-reference QP check.
- Stage 14.5D: explicit closed-loop baseline/candidate simulation-only evidence packaging.
- Stage 14.5E: candidate robustness envelope evidence through scale 0.10.
- Stage 14.5F-R0: release evidence index preflight.

## Baseline closed-loop evidence

- control_mode: baseline
- total_steps: 2400
- pass: True
- min_z: 0.274552192756
- max_abs_roll: 0.056707402709
- max_abs_pitch: 0.04832948253
- max_tau_total_abs: 9.659563043535
- qp_fail_steps: 0
- saturation_steps: 0

## MPC-assisted candidate closed-loop evidence

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
- all_scale_entries_pass: True
- all_entries_pass_limits: True
- min_z_min_over_entries: 0.273040429683
- max_abs_roll_max_over_entries: 0.102952660101
- max_abs_pitch_max_over_entries: 0.077452968358
- max_tau_total_abs_max_over_entries: 10.59512016256
- max_tau_candidate_scaled_abs_max_over_candidate_runs: 1.94425094473
- total_qp_fail_steps: 0
- total_saturation_steps: 0

## Release evidence index

- summary_count: 17
- doc_count: 17
- key_csv_count: 10
- indexed_artifact_count: 47
- release_evidence_index_csv: results/logs_sample/stage14_5f_r0_release_evidence_index.csv
- release_evidence_manifest_json: results/logs_sample/stage14_5f_r0_release_evidence_manifest.json

## Boundary statements

- simulation_only_project: true
- hardware_deployment_completed: false
- torque_enable_ready: false
- torque_publisher_enabled: false
- real_robot_torque_commanded: false
- ros_publisher_used: false
- mujoco_rollout_executed_in_f1: false
- runner_modified_in_f1: false

## Safe conclusion text

Stage 14.5 completed simulation-only MPC/WBC candidate evidence packaging and robustness indexing up to candidate scale 0.10.

Do not rewrite this as hardware readiness, torque-enable readiness, real robot torque execution, or direct MPC joint-torque output.
