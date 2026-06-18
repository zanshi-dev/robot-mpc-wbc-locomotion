# Stage 15.7 MuJoCo Candidate Compatibility Audit

## 1. Goal

Stage 15.7 connects the Stage 15.6 Jacobian torque candidate metadata to a MuJoCo model in an offline compatibility audit.

The chain is:

```text
Stage 15.5 model readiness report
+ Stage 15.6 real-model Jacobian candidate summary
-> MuJoCo MJCF model loading
-> joint name mapping
-> actuator mapping
-> kinematic mj_forward audit
-> candidate torque scale compatibility check
```

## 2. Boundary

This stage does not execute torque in MuJoCo.

It does not:

- call `mj_step`
- apply nonzero `data.ctrl`
- publish ROS torque commands
- modify the frozen mixed baseline
- claim hardware deployment
- claim `torque_enable_ready=True`

It only calls `mj_forward` after setting a kinematic joint pose for compatibility checks.

## 3. Files

```text
scripts/stage15_7_mujoco_candidate_compatibility_audit.py
scripts/stage15_7_validate_mujoco_candidate_compatibility_audit.py
scripts/stage15_7_validate_mujoco_candidate_compatibility_audit.sh
results/logs_sample/stage15_7_mujoco_candidate_compatibility_audit.csv
results/logs_sample/stage15_7_mujoco_candidate_compatibility_audit_summary.json
results/logs_sample/stage15_7_mujoco_candidate_compatibility_audit_validation.csv
results/logs_sample/stage15_7_mujoco_candidate_compatibility_audit_validation_summary.json
results/logs_sample/stage15_7_mujoco_candidate_compatibility_audit.log
```

## 4. Run

```bash
bash scripts/stage15_7_validate_mujoco_candidate_compatibility_audit.sh
```

Expected marker:

```text
stage15_7_result: pass
```

## 5. Validation Checks

The validator checks:

- MuJoCo Python import succeeds
- MJCF model loads
- at least 12 Stage 15.6 candidate joints map to MuJoCo joints
- at least one actuator maps to candidate joints
- 2400 kinematic `mj_forward` calls complete
- `mj_step` is not called
- `data.ctrl` remains zero
- `qpos` and `qvel` remain finite
- Stage 15.6 alpha 0.10 and 0.20 candidate torques remain within the audit torque limit
- no ROS torque publisher is used
- frozen mixed baseline remains unchanged

## 6. Next Stage

Stage 15.8 can introduce a strictly bounded MuJoCo torque-in-the-loop experiment with very small `alpha`, or it can first add an offline joint-order bridge table if Stage 15.7 reveals mapping ambiguity.
