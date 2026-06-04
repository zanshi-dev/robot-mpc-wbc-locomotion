# Stage 8.3 Adapter-backed Stage 7 Baseline A/B Test

## Target

Create an adapter-backed Stage 7 baseline entrypoint and compare it against the original Stage 7 recommended mixed baseline.

## Scripts

- Original: `scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py`
- Adapter-backed entrypoint: `scripts/stage08_adapter_backed_stage07_recommended_test.py`
- A/B test: `scripts/stage08_adapter_backed_stage07_baseline_ab_test.py`

## Boundary

This stage does not change control parameters or controller structure.

The adapter-backed entrypoint performs a runtime adapter preflight before executing the original Stage 7 recommended baseline.

This is still the Stage 7 mixed online control baseline:

- stance PD
- scaled stance WBC feedforward
- swing target PD

It is not pure full WBC locomotion.

## Outputs

- A/B log: `results/logs_sample/stage08_adapter_backed_stage07_baseline_ab_test_log.csv`
- A/B summary: `results/logs_sample/stage08_adapter_backed_stage07_baseline_ab_test_summary.csv`
- Original summary copy: `results/logs_sample/stage08_ab_original_stage07_summary.csv`
- Adapter-backed summary copy: `results/logs_sample/stage08_ab_adapter_backed_stage07_summary.csv`

## Result

- pass: `True`
- adapter_qpos_roundtrip_max_abs: `0.0`
- adapter_qvel_roundtrip_max_abs: `0.0`
- adapter_torque_roundtrip_max_abs: `0.0`
- original_pass: `True`
- adapter_pass: `True`
- original_pass_margin: `True`
- adapter_pass_margin: `True`

## Interpretation

Passing this stage means the adapter-backed entrypoint does not change the Stage 7 recommended baseline result.

The next stage may refactor duplicated runtime mapping calls to use `scripts/common/go1_runtime_interface.py` directly, if such duplicated calls exist in controller scripts.
