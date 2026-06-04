# Stage 8.4 Runtime Mapping Duplication Audit

## Target

Scan Python scripts for duplicated MuJoCo/Pinocchio runtime mapping logic before refactoring controller scripts.

## Boundary

This stage is audit-only.

It does not modify controller logic, control gains, gait scheduler, WBC/QP, swing target tracking, or ROS2/C++ code.

## Inputs

- Adapter module: `scripts/common/go1_runtime_interface.py`
- Previous A/B regression: `results/logs_sample/stage08_adapter_backed_stage07_baseline_ab_test_summary.csv`

## Outputs

- Audit log: `results/logs_sample/stage08_runtime_mapping_duplication_audit_log.csv`
- Audit summary: `results/logs_sample/stage08_runtime_mapping_duplication_audit_summary.csv`

## Result

- pass: `True`
- stage83_pass: `True`
- files_with_findings: `68`
- total_findings: `244`
- high_severity_findings: `85`
- medium_severity_findings: `55`
- low_severity_findings: `104`

## Files with most findings

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

Findings are not failures.

They are candidate locations for Stage 8.5 refactoring into `scripts/common/go1_runtime_interface.py`.

A Stage 8.5 refactor should be done one script at a time and followed by an A/B regression test.
