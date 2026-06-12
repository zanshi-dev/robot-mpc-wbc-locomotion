# Stage 14.5B Offline MPC Contact-Force to Joint Torque Candidate Check

Scope: simulation-only offline mapping check.

This stage reads Stage 14.4 MPC contact-force rollout data and maps contact-force targets through nominal Pinocchio foot Jacobians to produce joint torque candidates for offline analysis.

It does not run MuJoCo closed-loop simulation, does not run WBC/QP, does not use a ROS torque publisher, and does not modify the frozen mixed baseline control law.

## Evidence

- Summary JSON: `results/logs_sample/stage14_5b_offline_mpc_force_to_torque_candidate_summary.json`
- Candidate CSV: `results/logs_sample/stage14_5b_offline_mpc_force_to_torque_candidates.csv`

## Result

- pass: True
- failed_checks: []
- row_count: 100
- candidate_row_count: 100
- max_tau_candidate_abs: 19.44250944732831
- torque_limit_abs: 23.7
- torque_limit_violation_count: 0

## Safety flags

- simulation_only_project: True
- hardware_deployment_completed: False
- torque_enable_ready: False
- torque_publisher_enabled: False
- control_law_changed: False
- mixed_baseline_modified: False
- mujoco_closed_loop_used: False
- mujoco_torque_used: False
- ros_publisher_used: False
- wbc_qp_executed: False

## Boundary

The generated values are offline joint torque candidates, not real robot torque commands and not hardware execution evidence.
