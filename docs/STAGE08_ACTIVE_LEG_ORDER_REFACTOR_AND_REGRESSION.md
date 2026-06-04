# Stage 8.6 Active-path Hard-coded MuJoCo Leg Order Refactor and Regression

## Target

Replace active-path hard-coded MuJoCo leg order assignments with the shared runtime adapter constant:

- `MJ_LEG_ORDER`
- source module: `scripts/common/go1_runtime_interface.py`

## Patched files

- `scripts/stage07_online_full_wbc_scheduler_recommended_run.py`
- `scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py`

## Boundary

This stage only replaces duplicated active-path leg-order constants.

It does not change:

- control gains
- gait scheduler
- WBC/QP formulation
- swing target tracking
- torque limits
- ROS2/C++ code
- EKF
- MPC

The controller remains the Stage 7 mixed online control baseline.

## Regression

After patching, Stage 8.3 A/B regression was rerun.

## Result

- pass: `True`
- rerun_stage83_ab_pass: `True`
- rerun_original_pass: `True`
- rerun_adapter_pass: `True`
- rerun_original_pass_margin: `True`
- rerun_adapter_pass_margin: `True`
- active_high_severity_findings_after_refactor: `0`
- active_medium_severity_findings_after_refactor: `2`
- active_low_severity_findings_after_refactor: `1`

## Interpretation

If `active_high_severity_findings_after_refactor = 0`, the highest-risk active-path runtime mapping duplication has been removed.

Remaining active medium findings may be false positives from adapter preflight sample torque variables and should not be treated as controller failures without inspection.
