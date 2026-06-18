# Stage 15.8 Bounded MuJoCo Torque-Path Smoke Test

## 1. Goal

Stage 15.8 is the first Stage 15 step that intentionally sends a small actuator command through MuJoCo and calls `mj_step`.

The goal is narrow:

```text
Stage 15.7 joint/actuator map
-> small deterministic torque-candidate waveform
-> alpha scaling
-> conservative command clipping
-> MuJoCo actuator command path
-> short-horizon mj_step smoke test
```

This is not a locomotion controller validation.

## 2. Boundary

This stage does not claim:

- stable locomotion
- MPC-WBC closed-loop performance
- hardware deployment
- `torque_enable_ready=True`
- ROS torque publisher readiness

It does not modify the frozen mixed baseline.

## 3. Safety Limits

The script uses:

```text
alpha = 0.0 / 0.001 / 0.002 / 0.005
steps_per_alpha = 200
audit_ctrl_limit = 0.25
```

Every actuator command is clipped by the conservative audit limit and by MuJoCo actuator `ctrlrange` when available.

## 4. Files

```text
scripts/stage15_8_mujoco_torque_smoke_test.py
scripts/stage15_8_validate_mujoco_torque_smoke_test.py
scripts/stage15_8_validate_mujoco_torque_smoke_test.sh
results/logs_sample/stage15_8_mujoco_torque_smoke_test.csv
results/logs_sample/stage15_8_mujoco_torque_smoke_test_summary.json
results/logs_sample/stage15_8_mujoco_torque_smoke_test_validation.csv
results/logs_sample/stage15_8_mujoco_torque_smoke_test_validation_summary.json
results/logs_sample/stage15_8_mujoco_torque_smoke_test.log
```

## 5. Run

```bash
bash scripts/stage15_8_validate_mujoco_torque_smoke_test.sh
```

Expected marker:

```text
stage15_8_result: pass
```

## 6. Validation Checks

The validator checks:

- MuJoCo model loads
- at least 12 actuators map to the Stage 15.7 candidate joint order
- `mj_step` is called
- positive alpha runs send nonzero bounded actuator commands
- no NaN or Inf appears in `qpos` or `qvel`
- no actuator command exceeds the audit limit
- no command saturation occurs
- stable locomotion is not claimed
- ROS torque publisher is not used
- frozen mixed baseline remains unchanged

## 7. Next Stage

Stage 15.9 should stop using the deterministic smoke waveform and instead inject a bounded version of the Stage 15.6 `J^T f` torque candidate into MuJoCo for a short-horizon dry-run.
