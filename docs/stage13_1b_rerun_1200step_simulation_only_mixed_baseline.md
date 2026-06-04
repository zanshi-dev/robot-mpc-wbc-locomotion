# Stage 13.1B Rerun 1200-Step Simulation-Only Mixed Baseline Regression

- pass: `True`
- fail_reasons: `[]`
- simulation_only_project: `True`
- hardware_deployment_scope: `out_of_scope_by_user_constraint`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- baseline_type: `mixed_online_control_baseline`
- rerun_returncode: `0`
- rerun_timeout: `False`
- source_changed: `False`

## Key checks
- total_steps_eq_1200: pass=`True`, actual=`1200`
- transition_count_eq_5: pass=`True`, actual=`5`
- trot_FR_RL_steps_eq_600: pass=`True`, actual=`600`
- trot_FL_RR_steps_eq_600: pass=`True`, actual=`600`
- pass_eq_True: pass=`True`, actual=`True`
- pass_margin_eq_True: pass=`True`, actual=`True`
- qp_fail_steps_eq_0: pass=`True`, actual=`0`
- saturation_steps_eq_0: pass=`True`, actual=`0`
- min_z_>=_0.22: pass=`True`, actual=`0.278419161322`
- max_abs_roll_<=_0.08: pass=`True`, actual=`0.056707402709`
- max_abs_pitch_<=_0.08: pass=`True`, actual=`0.04832948253`
- max_joint_error_<=_0.12: pass=`True`, actual=`0.077233662573`
- max_tau_total_abs_<=_23.7: pass=`True`, actual=`9.659563043535`

## Evidence files

- stdout: `/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_1b_rerun_1200step_stdout.log`
- copied_summary: `/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_1b_stage07_rerun_summary.csv`
- copied_log: `/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_1b_stage07_rerun_log.csv`
- copied_swing_tracking: `/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_1b_stage07_rerun_swing_tracking.csv`
- backup_dir: `/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_1b_backup`

Recommended next stage: `Stage 13.2 2400-step simulation-only robustness regression`