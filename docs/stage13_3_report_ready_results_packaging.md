# Stage 13.3 Report-Ready Results Packaging

- pass: `True`
- fail_reasons: `[]`
- simulation_only_project: `True`
- hardware_deployment_scope: `out_of_scope_by_user_constraint`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- baseline_type: `mixed_online_control_baseline`

## Packaged metrics

- metrics_table: `/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_3_report_ready_metrics_table.csv`

## Evidence status
- stage12_22_summary: exists=`True`, sha256=`6e355a2e644c90de0596895dfcf43679a4438b469165d4b0c896c329737c4c51`, path=`/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage12_22_simulation_only_scope_freeze_summary.json`
- stage13_1b_summary: exists=`True`, sha256=`18fbb696d4458e7ae8e6f7316a48dbc60c91047a6ade40da6d79c0a7c4a87576`, path=`/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_1b_rerun_1200step_simulation_only_mixed_baseline_summary.json`
- stage13_2c_summary: exists=`True`, sha256=`82b826eb565a33a73fb48f653855f7eaa0f89f5619f5e04998bb4141cdd87dae`, path=`/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_2c_final_2400step_robustness_evidence_freeze_summary.json`
- stage13_3_metrics_csv: exists=`True`, sha256=`c7c7759f37970a39d5b2b9ab2752d44305a2f22d15ec1f3ad7d0f48af780fca3`, path=`/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_3_report_ready_metrics_table.csv`
- simulation_only_scope_doc: exists=`True`, sha256=`4cfdf4ce53c1d29ee96c0a9d26ad01c4b207625bac3447dab8110b4cd6283cbf`, path=`/home/zanshi/robot-mpc-wbc-locomotion/docs/SIMULATION_ONLY_SCOPE.md`
- simulation_only_results_summary: exists=`True`, sha256=`b50510ec0ef0f7b16b9b21cc8d7e67884fa2594d954da58d36201f54b0ee4c6e`, path=`/home/zanshi/robot-mpc-wbc-locomotion/docs/SIMULATION_ONLY_RESULTS_SUMMARY.md`

## Allowed claims
- The project is simulation-only.
- The frozen baseline is mixed_online_control_baseline, not a hardware realtime controller.
- The 1200-step mixed baseline rerun passed.
- The 2400-step simulation-only mixed baseline robustness regression passed.
- ROS2/C++ torque streaming evidence is bounded zero/safe dry-run only.

## Disallowed claims
- Hardware deployment completed.
- Actuator enablement completed.
- Real robot torque execution completed.
- torque_enable_ready=True.
- A realtime hardware controller was completed.

Next stage: `Stage 13.4 optional plots/tables for report, or Stage 14 simulation-only improvement planning`