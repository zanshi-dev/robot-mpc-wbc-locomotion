# Stage 14.5D-R3 Baseline-mode Derived Runner Dry Run

Scope: simulation-only baseline-mode run of the derived Stage 14.5D runner skeleton.

This step runs the derived runner in explicit baseline mode. It does not execute A/B comparison, does not execute MPC-assisted candidate mode, does not modify the original baseline runner, and does not use ROS torque publishing.

## Evidence

- Summary JSON: `results/logs_sample/stage14_5d_r3_baseline_mode_derived_runner_dry_run_summary.json`
- Runner stdout: `results/logs_sample/stage14_5d_r3_baseline_mode_derived_runner_stdout.txt`
- Runner stderr: `results/logs_sample/stage14_5d_r3_baseline_mode_derived_runner_stderr.txt`
- Derived baseline log CSV: `results/logs_sample/stage14_5d_r2_closed_loop_ab_baseline_skeleton_log.csv`
- Derived baseline summary CSV: `results/logs_sample/stage14_5d_r2_closed_loop_ab_baseline_skeleton_summary.csv`

## Result

- pass: True
- failed_checks: []
- run_returncode: 0
- baseline_mode_pass: True
- total_steps: 2400
- log_row_count: 2400

## Safety boundary

- simulation_only_project: True
- hardware_deployment_completed: False
- torque_enable_ready: False
- torque_publisher_enabled: False
- real_robot_torque_commanded: False
- ros_publisher_used: False
- mujoco_closed_loop_baseline_mode_executed: True
- mujoco_closed_loop_ab_executed: False
- mujoco_sim_data_ctrl_used: True
- mpc_assisted_candidate_executed: False

This is not MPC-assisted closed-loop evidence and not hardware-readiness evidence.
