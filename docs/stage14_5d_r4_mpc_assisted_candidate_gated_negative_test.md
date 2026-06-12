# Stage 14.5D-R4 MPC-assisted Candidate Gated Negative Test

Scope: simulation-only negative gate validation.

This step verifies that `mpc_assisted_candidate` is safely rejected before implementation.

It does not run MuJoCo rollout, does not execute A/B comparison, does not inject MPC-assisted torque candidates, and does not use ROS torque publishing.

## Evidence

- Summary JSON: `results/logs_sample/stage14_5d_r4_mpc_assisted_candidate_gated_negative_test_summary.json`
- No-allow stdout: `results/logs_sample/stage14_5d_r4_candidate_no_allow_stdout.txt`
- No-allow stderr: `results/logs_sample/stage14_5d_r4_candidate_no_allow_stderr.txt`
- With-allow stdout: `results/logs_sample/stage14_5d_r4_candidate_with_allow_stdout.txt`
- With-allow stderr: `results/logs_sample/stage14_5d_r4_candidate_with_allow_stderr.txt`

## Result

- pass: True
- failed_checks: []
- candidate_without_allow_returncode: 1
- candidate_with_allow_returncode: 1
- mpc_assisted_candidate_safely_rejected: True

## Boundary

- mujoco_closed_loop_ab_executed: False
- mujoco_sim_data_ctrl_used: False
- mpc_assisted_candidate_executed: False
- real_robot_torque_commanded: False

This is negative gate evidence only, not MPC-assisted closed-loop evidence.
