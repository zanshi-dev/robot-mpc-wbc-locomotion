# Stage 13.2B 2400-Step Simulation-Only Robustness Regression

- pass: `False`
- fail_reasons: `['2400-step runner returned nonzero: 1', '2400-step run did not produce mixed baseline summary CSV', '2400-step run did not produce mixed baseline log CSV', '2400-step run did not produce WBC summary CSV', '2400-step run did not produce WBC log CSV']`
- simulation_only_project: `True`
- hardware_deployment_scope: `out_of_scope_by_user_constraint`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- baseline_type: `mixed_online_control_baseline`
- rerun_returncode: `1`
- rerun_timeout: `False`
- runner_changed: `False`
- swing_csv_changed: `False`

## Key checks

## Evidence files
- stdout: `/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_2b_run_2400step_stdout.log`
- mixed_summary: `/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_2b_2400step_mixed_baseline_summary.csv`
- mixed_log: `/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_2b_2400step_mixed_baseline_log.csv`
- wbc_summary: `/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_2b_2400step_wbc_summary.csv`
- wbc_log: `/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_2b_2400step_wbc_log.csv`

Recommended next stage: `Stage 13.2B-R inspect 2400-step robustness regression failure`