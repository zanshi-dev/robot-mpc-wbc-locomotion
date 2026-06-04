# Stage 13.2A 2400-Step Simulation-Only Preflight and Derived Runner Creation

- pass: `False`
- fail_reasons: `['could not locate direct 1200-step assignment to patch', 'derived runner does not contain 2400 after patch']`
- simulation_only_project: `True`
- hardware_deployment_scope: `out_of_scope_by_user_constraint`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- baseline_type: `mixed_online_control_baseline`
- source_stage7_runner: `/home/zanshi/robot-mpc-wbc-locomotion/scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py`
- derived_2400_runner: `/home/zanshi/robot-mpc-wbc-locomotion/scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py`
- original_runner_unchanged: `True`
- derived_runner_exists: `False`
- stage13_1b_pass: `True`
- stage13_1b_total_steps: `1200`

## Patch replacements
- total_steps_assignment: `0`
- num_steps_assignment: `0`
- n_steps_assignment: `0`
- steps_assignment: `0`
- N_STEPS_assignment: `0`

## Python compile

- returncode: `None`

Recommended next stage: `Stage 13.2A-R inspect 2400-step runner derivation failure`