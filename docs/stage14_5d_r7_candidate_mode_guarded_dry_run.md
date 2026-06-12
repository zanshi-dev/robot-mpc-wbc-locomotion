# Stage 14.5D-R7 Candidate-mode Guarded Dry Run

Scope: simulation-only candidate-mode dry run.

This step runs the R6 candidate-capable runner in explicit `mpc_assisted_candidate` mode with a conservative scale of 0.05.

It does not execute A/B comparison, does not send real robot torque, does not use ROS torque publishing, and does not modify the frozen baseline source.

## Evidence

- Summary JSON: `results/logs_sample/stage14_5d_r7_candidate_mode_guarded_dry_run_summary.json`
- stdout: `results/logs_sample/stage14_5d_r7_candidate_mode_guarded_dry_run_stdout.txt`
- stderr: `results/logs_sample/stage14_5d_r7_candidate_mode_guarded_dry_run_stderr.txt`
- Candidate log CSV: `results/logs_sample/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_log.csv`
- Candidate summary CSV: `results/logs_sample/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_summary.csv`

## Result

- pass: True
- failed_checks: []
- run_returncode: 0
- candidate_mode_pass: True
- total_steps: 2400
- log_row_count: 2400
- candidate_scale: 0.05

## Safety boundary

- mujoco_closed_loop_candidate_mode_executed: True
- mujoco_closed_loop_ab_executed: False
- mujoco_sim_data_ctrl_used: True
- real_robot_torque_commanded: False
- ros_publisher_used: False

This is candidate-mode simulation evidence only, not A/B evidence and not hardware-readiness evidence.
