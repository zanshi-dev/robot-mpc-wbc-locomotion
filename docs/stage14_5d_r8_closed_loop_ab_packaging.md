# Stage 14.5D-R8 Closed-loop A/B Packaging

Scope: simulation-only A/B evidence packaging from existing runs.

This step compares the existing R3 baseline-mode closed-loop run and R7 MPC-assisted candidate-mode closed-loop run. It does not rerun MuJoCo.

## Evidence

- Summary JSON: `results/logs_sample/stage14_5d_r8_closed_loop_ab_comparison_summary.json`
- Comparison table CSV: `results/logs_sample/stage14_5d_r8_closed_loop_ab_comparison_table.csv`
- Baseline summary CSV: `results/logs_sample/stage14_5d_r2_closed_loop_ab_baseline_skeleton_summary.csv`
- Candidate summary CSV: `results/logs_sample/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_summary.csv`

## Result

- pass: True
- failed_checks: []
- baseline_log_rows: 2400
- candidate_log_rows: 2400
- candidate_scale: 0.05
- candidate_max_tau_candidate_scaled_abs: 0.972125472365

## Key comparison

- min_z: baseline=0.274552192756, candidate=0.276975761939, delta=0.002423569182999963
- max_abs_roll: baseline=0.056707402709, candidate=0.102952660101, delta=0.046245257392
- max_abs_pitch: baseline=0.04832948253, candidate=0.053162351948, delta=0.004832869417999999
- max_tau_total_abs: baseline=9.659563043535, candidate=10.019186119959, delta=0.3596230764240005
- qp_fail_steps: baseline=0, candidate=0, delta=0
- saturation_steps: baseline=0, candidate=0, delta=0

## Boundary

- mujoco_closed_loop_ab_packaged_from_existing_runs: True
- mujoco_closed_loop_ab_rerun_executed: False
- real_robot_torque_commanded: False
- ros_publisher_used: False

This is simulation-only A/B packaging evidence, not hardware-readiness evidence.
