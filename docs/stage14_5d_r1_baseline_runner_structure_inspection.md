# Stage 14.5D-R1 Baseline Runner Structure Inspection

Scope: simulation-only source structure inspection.

This step inspects the exact baseline runner source structure before deriving a Stage 14.5D closed-loop A/B script.

It does not run MuJoCo, does not modify the frozen mixed baseline, does not add an MPC-assisted switch, and does not use ROS torque publishing.

## Evidence

- Summary JSON: `results/logs_sample/stage14_5d_r1_baseline_runner_structure_inspection_summary.json`
- Snippets: `results/logs_sample/stage14_5d_r1_baseline_runner_structure_snippets.txt`

## Result

- pass: True
- failed_checks: []
- baseline_runner: `scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py`
- line_count: 358

## Pattern hit counts

- main_or_entry: 2
- mujoco_model_data: 4
- simulation_loop: 4
- torque_write: 46
- baseline_control_terms: 100
- metrics_summary: 40
- file_outputs: 16

## Functions

- `load_wbc` lines 41-45
- `read_swing_targets` lines 48-71
- `leg_indices` lines 74-79
- `main` lines 82-354

## Boundary

This is source-structure evidence only. It is not MPC-assisted closed-loop locomotion evidence.
