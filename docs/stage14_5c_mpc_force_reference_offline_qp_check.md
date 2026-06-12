# Stage 14.5C MPC Force Target as Offline WBC/QP Reference Check

Scope: simulation-only offline reference QP check.

This stage uses the Stage 14.4 MPC contact-force target as an offline QP reference and checks whether the reference can be represented as a bounded contact-force solution under contact, friction, vertical force, total vertical force, and nominal `J^T f` torque bounds.

It does not run MuJoCo closed-loop simulation, does not replace the frozen mixed baseline, does not use a ROS torque publisher, and does not produce real robot torque commands.

## Evidence

- Summary JSON: `results/logs_sample/stage14_5c_mpc_force_reference_offline_qp_summary.json`
- QP CSV: `results/logs_sample/stage14_5c_mpc_force_reference_offline_qp_check.csv`

## Result

- pass: True
- failed_checks: []
- row_count: 100
- qp_row_count: 100
- qp_status_counts: {'solved': 100}
- max_tracking_error_inf: 1.8869763896238494e-09
- max_tau_abs: 19.442509447328305
- torque_bound_abs: 23.7
- torque_violation_count: 0
- max_friction_violation: 0.0
- max_swing_force_norm: 4.605163373947106e-37

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
- wbc_qp_replaces_baseline: False

## Boundary

This is offline WBC/QP-reference compatibility evidence only. It is not MPC-assisted closed-loop locomotion evidence and not hardware-readiness evidence.
