# Stage 13.0 Simulation-Only Locomotion Preflight Inventory

- pass: `True`
- fail_reasons: `[]`
- simulation_only_project: `True`
- hardware_deployment_scope: `out_of_scope_by_user_constraint`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- baseline_type: `mixed_online_control_baseline`

## Required files
- stage12_22_summary: exists=`True`, path=`/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage12_22_simulation_only_scope_freeze_summary.json`
- simulation_scope_doc: exists=`True`, path=`/home/zanshi/robot-mpc-wbc-locomotion/docs/SIMULATION_ONLY_SCOPE.md`
- project_status: exists=`True`, path=`/home/zanshi/robot-mpc-wbc-locomotion/PROJECT_STATUS.md`
- stage07_recommended_script: exists=`True`, path=`/home/zanshi/robot-mpc-wbc-locomotion/scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py`
- go1_mujoco_scene: exists=`True`, path=`/home/zanshi/robot-mpc-wbc-locomotion/assets/go1/scene.xml`
- go1_urdf: exists=`True`, path=`/home/zanshi/robot-mpc-wbc-locomotion/assets/go1/urdf/go1.urdf`

## Dependency checks
- numpy: returncode=`0`, output=`1.26.4`
- mujoco: returncode=`0`, output=`3.9.0`
- pinocchio: returncode=`0`, output=`3.9.0`
- scipy: returncode=`0`, output=`1.11.4`
- osqp: returncode=`0`, output=`1.1.1`

Recommended next stage: `Stage 13.1 compare existing Stage 7 baseline summary and optionally rerun 1200-step regression`