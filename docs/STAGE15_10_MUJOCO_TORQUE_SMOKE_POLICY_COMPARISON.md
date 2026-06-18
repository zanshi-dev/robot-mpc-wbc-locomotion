# Stage 15.10 MuJoCo Torque-Smoke Policy Comparison

## 1. Goal

Stage 15.10 compares three short-horizon actuator-command policies under the same MuJoCo setup:

```text
zero_ctrl
Stage 15.8 deterministic waveform
Stage 15.9 J^T f candidate
```

This comparison is for safety and compatibility only. It is not a stable locomotion benchmark.

## 2. Scope

The stage reports:

- finite `qpos` / `qvel`
- max actuator command
- saturation count
- nonzero command count
- min base height
- max velocity magnitude
- contact count proxy
- command L2 proxy

It does not report walking performance or claim controller success.

## 3. Safety Parameters

```text
steps_per_policy = 200
target_max_ctrl = 0.08
audit_ctrl_limit = 0.25
```

Each nonzero policy is scaled to keep actuator commands within the target max command.

## 4. Boundary

This stage does not:

- modify the frozen mixed baseline
- publish ROS torque commands
- claim stable locomotion
- claim real robot deployment
- claim `torque_enable_ready=True`

## 5. Files

```text
scripts/stage15_10_compare_mujoco_torque_smoke_policies.py
scripts/stage15_10_validate_mujoco_torque_smoke_policy_comparison.py
scripts/stage15_10_validate_mujoco_torque_smoke_policy_comparison.sh
results/logs_sample/stage15_10_mujoco_torque_smoke_policy_comparison.csv
results/logs_sample/stage15_10_mujoco_torque_smoke_policy_comparison_summary.json
results/logs_sample/stage15_10_mujoco_torque_smoke_policy_comparison_validation.csv
results/logs_sample/stage15_10_mujoco_torque_smoke_policy_comparison_validation_summary.json
results/logs_sample/stage15_10_mujoco_torque_smoke_policy_comparison.log
```

## 6. Run

```bash
bash scripts/stage15_10_validate_mujoco_torque_smoke_policy_comparison.sh
```

Expected marker:

```text
stage15_10_result: pass
```

## 7. Next Stage

Stage 15.11 should create a report-level summary of Stage 15.1 to Stage 15.10, explaining what is now closed, what remains dry-run only, and what still cannot be claimed.
