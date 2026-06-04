# Stage 8.2 Adapter Zero-Control Regression Guard

## Target

Before modifying the Stage 7 mixed baseline controller, this check verifies that:

1. The Stage 8.1 runtime adapter still satisfies qpos/qvel/torque round-trip contracts.
2. The existing Stage 7 recommended mixed baseline still passes without changing control logic.

## Control boundary

No controller parameter is changed in this stage.

Stage 7 baseline remains:

- stance PD
- scaled stance WBC feedforward
- swing target PD

This is still a mixed online control baseline, not pure full WBC locomotion.

## Outputs

- Log CSV: `results/logs_sample/stage08_adapter_zero_control_regression_guard_log.csv`
- Summary CSV: `results/logs_sample/stage08_adapter_zero_control_regression_guard_summary.csv`
- Stage 7 stdout: `results/logs_sample/stage08_adapter_zero_control_regression_guard_stage07_stdout.txt`
- Stage 7 stderr: `results/logs_sample/stage08_adapter_zero_control_regression_guard_stage07_stderr.txt`

## Result

- pass: `True`
- adapter_qpos_roundtrip_max_abs: `0.0`
- adapter_qvel_roundtrip_max_abs: `0.0`
- adapter_torque_roundtrip_max_abs: `0.0`
- stage07_pass: `True`
- stage07_pass_margin: `True`
- stage07_qp_fail_steps: `0.0`
- stage07_saturation_steps: `0.0`

## Interpretation

Passing this stage means the reusable adapter is available and the previous Stage 7 recommended baseline remains intact before any refactor.

The next step can safely refactor duplicated state/torque mapping code to use `scripts/common/go1_runtime_interface.py`.
