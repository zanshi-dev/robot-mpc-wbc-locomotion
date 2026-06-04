# Stage 13.2C Final 2400-Step Robustness Evidence Freeze

- pass: `True`
- fail_reasons: `[]`
- simulation_only_project: `True`
- hardware_deployment_scope: `out_of_scope_by_user_constraint`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- baseline_type: `mixed_online_control_baseline`

## Mixed 2400-step results

- total_steps: `2400`
- transition_count: `11`
- trot_FR_RL_steps: `1200`
- trot_FL_RR_steps: `1200`
- min_z: `0.274552192756`
- final_z: `0.286030728906`
- max_abs_roll: `0.056707402709`
- max_abs_pitch: `0.04832948253`
- max_joint_error: `0.077233662573`
- max_tau_total_abs: `9.659563043535`
- qp_fail_steps: `0`
- saturation_steps: `0`
- pass: `True`
- pass_margin: `True`

## WBC 2400-step results

- total_steps: `2400`
- transition_count: `11`
- min_z: `0.284525843843`
- final_z: `0.304968764218`
- max_abs_roll: `0.163118252883`
- max_abs_pitch: `0.106881861177`
- max_tau_total_abs: `11.520998707973`
- qp_fail_steps: `0`
- saturation_steps: `0`
- pass: `True`
- pass_margin: `True`

## Evidence files
- wbc_stdout: exists=`True`, sha256=`1069455f824823210b5a4bac5507e6264b4dded43cf7653eaecfb1efd221e245`, path=`/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_2b_r1_wbc_rerun_stdout.log`
- mixed_stdout: exists=`True`, sha256=`fa88e40767f2abab255f2032bb226e2338f75ac258b94b6615ba5db473f42d94`, path=`/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_2b_r1_mixed_rerun_stdout.log`
- derived_contact: exists=`True`, sha256=`2d612dad6063a333982128e6ce2b535060cc7cdc1b67a131e9fa9435ef268eaa`, path=`/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_2b_r1_2400step_contact_schedule_wbc_qp.csv`
- wbc_summary: exists=`True`, sha256=`e7ec4f1742ba8538b6096c14222e80c7214ec25768e8a36ae152ae66e40bb5a0`, path=`/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_2b_r1_2400step_wbc_summary.csv`
- wbc_log: exists=`True`, sha256=`89aae719df7c06a98b53cc70938cc4ed7b5123b9d295eb879f970393e4bdf37e`, path=`/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_2b_r1_2400step_wbc_log.csv`
- mixed_summary: exists=`True`, sha256=`ad177850ad605fb220e4e1f55cce5c07b544d94424eab8bcc1d64a6b42c0d514`, path=`/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_2b_r1_2400step_mixed_summary.csv`
- mixed_log: exists=`True`, sha256=`772bc8db15c9a0f165ae4e690e1ffc2cf783bb8c914297551142ef119677e818`, path=`/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_2b_r1_2400step_mixed_log.csv`
- backup_dir: exists=`True`, sha256=`None`, path=`/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_2b_r1_backup`

## Final statement

2400-step simulation-only robustness regression passed for the mixed online control baseline; no hardware deployment or actuator enablement is claimed.

Next stage: `Stage 13.3 documentation consolidation and report-ready results packaging`