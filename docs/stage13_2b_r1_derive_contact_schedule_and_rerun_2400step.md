# Stage 13.2B-R1 Derive Contact Schedule and Rerun 2400-Step Robustness Regression

- pass: `True`
- fail_reasons: `[]`
- simulation_only_project: `True`
- hardware_deployment_scope: `out_of_scope_by_user_constraint`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- baseline_type: `mixed_online_control_baseline`
- source_contact_rows: `3`
- derived_contact_rows: `2400`
- derived_contact_line_count: `2401`
- wbc_returncode: `0`
- wbc_timeout: `False`
- mixed_returncode: `0`
- mixed_timeout: `False`
- runner_changed: `False`
- wbc_runner_changed: `False`
- derived_swing_changed: `False`
- source_contact_changed: `False`

## Key checks
- total_steps_eq_2400: pass=`True`, actual=`2400`
- transition_count_eq_11: pass=`True`, actual=`11`
- trot_FR_RL_steps_eq_1200: pass=`True`, actual=`1200`
- trot_FL_RR_steps_eq_1200: pass=`True`, actual=`1200`
- pass_eq_True: pass=`True`, actual=`True`
- pass_margin_eq_True: pass=`True`, actual=`True`
- qp_fail_steps_eq_0: pass=`True`, actual=`0`
- saturation_steps_eq_0: pass=`True`, actual=`0`
- min_z_>=_0.22: pass=`True`, actual=`0.274552192756`
- max_abs_roll_<=_0.08: pass=`True`, actual=`0.056707402709`
- max_abs_pitch_<=_0.08: pass=`True`, actual=`0.04832948253`
- max_joint_error_<=_0.12: pass=`True`, actual=`0.077233662573`
- max_tau_total_abs_<=_23.7: pass=`True`, actual=`9.659563043535`

## Evidence files
- wbc_stdout: `/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_2b_r1_wbc_rerun_stdout.log`
- mixed_stdout: `/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_2b_r1_mixed_rerun_stdout.log`
- derived_contact: `/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_2b_r1_2400step_contact_schedule_wbc_qp.csv`
- wbc_summary: `/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_2b_r1_2400step_wbc_summary.csv`
- wbc_log: `/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_2b_r1_2400step_wbc_log.csv`
- mixed_summary: `/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_2b_r1_2400step_mixed_summary.csv`
- mixed_log: `/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_2b_r1_2400step_mixed_log.csv`

Recommended next stage: `Stage 13.2C final 2400-step robustness evidence freeze`