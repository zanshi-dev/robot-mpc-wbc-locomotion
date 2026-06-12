# Stage 14.5E-R0 Candidate Robustness Envelope Preflight

Scope: simulation-only robustness sweep preflight.

This step freezes the candidate robustness envelope plan. It does not run MuJoCo and does not modify any runner.

## Result

- pass: True
- failed_checks: []

## Planned scale envelope

- scale=0.00
- scale=0.02
- scale=0.05
- scale=0.10

## Acceptance criteria for future sweep

- total_steps = 2400
- qp_fail_steps = 0
- saturation_steps = 0
- min_z > 0.22
- max_abs_roll < 0.20
- max_abs_pitch < 0.20
- max_tau_total_abs <= 23.7
- real_robot_torque_commanded = False
- ros_publisher_used = False

## Boundary

- mujoco_closed_loop_sweep_executed_in_r0: False
- mujoco_sim_data_ctrl_used_in_r0: False
- real_robot_torque_commanded: False
- ros_publisher_used: False
- torque_enable_ready: False

This is a planning/preflight artifact only. It is not hardware-readiness evidence.

## Evidence

- summary: `results/logs_sample/stage14_5e_r0_candidate_robustness_envelope_preflight_summary.json`
- scale plan: `results/logs_sample/stage14_5e_r0_candidate_robustness_scale_plan.csv`
