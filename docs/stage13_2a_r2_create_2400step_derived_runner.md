# Stage 13.2A-R2 Create 2400-Step Derived Runner

- pass: `True`
- fail_reasons: `[]`
- simulation_only_project: `True`
- hardware_deployment_scope: `out_of_scope_by_user_constraint`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- original_sources_unchanged: `True`
- swing_row_count: `1200`
- derived_swing_row_count: `2400`

## Static checks
- derived_wbc_has_TOTAL_STEPS_2400: `True`
- derived_wbc_no_TOTAL_STEPS_1200: `True`
- derived_recommended_points_to_derived_wbc: `True`
- derived_recommended_points_to_derived_swing_csv: `True`
- derived_swing_row_count_2400: `True`

## Compile checks
- derived WBC returncode: `0`
- derived recommended returncode: `0`

## Derived files
- derived_wbc_runner: `/home/zanshi/robot-mpc-wbc-locomotion/scripts/stage13_2_2400step_online_full_wbc_scheduler_runner.py`
- derived_recommended_runner: `/home/zanshi/robot-mpc-wbc-locomotion/scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py`
- derived_swing_target_csv: `/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_2_2400step_swing_trajectory_tracking_check.csv`

Recommended next stage: `Stage 13.2B run 2400-step simulation-only robustness regression`