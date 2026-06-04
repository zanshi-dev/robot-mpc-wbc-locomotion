# Stage 13.1A Existing Stage 7 Mixed Baseline Summary Verification

- pass: `True`
- fail_reasons: `[]`
- simulation_only_project: `True`
- hardware_deployment_scope: `out_of_scope_by_user_constraint`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- baseline_type: `mixed_online_control_baseline`

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

Recommended next stage: `Stage 13.1B rerun 1200-step simulation-only mixed baseline regression`