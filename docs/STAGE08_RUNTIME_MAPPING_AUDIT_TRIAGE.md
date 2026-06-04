# Stage 8.5 Runtime Mapping Audit Triage

## Target

Classify Stage 8.4 runtime mapping findings into:

1. active dependency path findings
2. legacy or non-active script findings

This prevents historical validation scripts from being treated as current controller-chain risk.

## Boundary

This stage is audit-only.

No controller logic, gains, gait scheduler, WBC/QP logic, swing tracking, or ROS2/C++ code is modified.

## Entrypoints

- `scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py`
- `scripts/stage08_adapter_backed_stage07_recommended_test.py`

## Active dependency closure

- `scripts/common/go1_runtime_interface.py`
- `scripts/stage07_online_full_wbc_scheduler_recommended_run.py`
- `scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py`
- `scripts/stage08_adapter_backed_stage07_recommended_test.py`

## Result

- pass: `True`
- audit_pass: `True`
- total_findings: `244`
- active_dependency_findings: `3`
- legacy_or_nonactive_findings: `241`
- active_high_severity_findings: `0`
- active_medium_severity_findings: `2`
- active_low_severity_findings: `1`

## Active files with findings

- `scripts/stage08_adapter_backed_stage07_recommended_test.py`: 2 findings
- `scripts/stage07_online_full_wbc_scheduler_recommended_run.py`: 1 findings

## Legacy or non-active files with most findings

- `scripts/stage08_runtime_interface_contract_check.py`: 43 findings
- `scripts/stage06_jacobian_transpose_torque.py`: 26 findings
- `scripts/stage08_runtime_interface_adapter_module_check.py`: 17 findings
- `scripts/stage02_compare_mujoco_pinocchio_fk.py`: 8 findings
- `scripts/stage02_compare_foot_velocity.py`: 7 findings
- `scripts/stage02_compare_full_foot_velocity.py`: 7 findings
- `scripts/stage02_compare_mujoco_pinocchio_jacobian.py`: 7 findings
- `scripts/stage02_check_pinocchio_jacobian.py`: 6 findings
- `scripts/stage02_validate_pinocchio_fk.py`: 6 findings
- `scripts/stage08_adapter_backed_stage07_baseline_ab_test.py`: 4 findings
- `scripts/stage03_standing_pd_demo.py`: 3 findings
- `scripts/stage04_open_loop_trot_pd_demo.py`: 3 findings
- `scripts/stage05_contact_schedule_force_qp.py`: 3 findings
- `scripts/stage05_horizon_force_qp.py`: 3 findings
- `scripts/stage05_standing_contact_force_qp.py`: 3 findings
- `scripts/stage07_full_wbc_base_accel_task_qp.py`: 3 findings
- `scripts/stage07_full_wbc_base_vertical_accel_task_qp.py`: 3 findings
- `scripts/stage07_full_wbc_dynamics_qp.py`: 3 findings
- `scripts/stage07_full_wbc_stance_constraint_qp.py`: 3 findings
- `scripts/stage00_torque_control_demo.py`: 2 findings

## Interpretation

If `active_high_severity_findings > 0`, Stage 8.6 should refactor only the active-path file with the highest high-severity count and then run A/B regression.

If `active_high_severity_findings = 0`, Stage 8.6 should not refactor legacy Stage 0/2 validation scripts. Instead, it should promote the adapter-backed entrypoint as the recommended Stage 8 runtime-safe baseline.
