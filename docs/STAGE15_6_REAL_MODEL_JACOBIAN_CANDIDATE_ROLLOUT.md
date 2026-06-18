# Stage 15.6 Real-Model Pinocchio Jacobian Candidate Rollout

## 1. Goal

Stage 15.6 consumes the Stage 15.5 model readiness audit and runs a dry-run contact-force-to-torque-candidate rollout through Pinocchio Jacobians.

The intended chain is:

```text
Stage 15.5 selected model candidate
-> Pinocchio model loading or audit-model construction from real joint/frame names
-> foot Jacobian computation
-> J^T f torque candidate
-> alpha sweep validation
```

## 2. Boundary

This stage remains offline and simulation-only.

It does not:

- run MuJoCo torque control
- publish ROS torque commands
- modify the frozen mixed baseline
- claim hardware deployment
- claim `torque_enable_ready=True`

## 3. Model Loading Policy

If the selected Stage 15.5 model is a directly loadable URDF, the script loads it with Pinocchio and sets:

```text
real_geometry_loaded: true
model_source: urdf_pinocchio
```

If the selected model is MJCF/Xacro or cannot be loaded as URDF, the script builds a Pinocchio audit model using the real joint and foot frame names discovered in Stage 15.5. In that fallback mode it sets:

```text
real_model_candidate_used: true
selected_model_metadata_used: true
real_geometry_loaded: false
model_source: audit_pinocchio_model_from_stage15_5_names
```

This avoids overstating the result while still moving beyond the Stage 15.4 fully synthetic naming setup.

## 4. Files

```text
scripts/stage15_6_real_model_jacobian_candidate_rollout.py
scripts/stage15_6_validate_real_model_jacobian_candidate_rollout.py
scripts/stage15_6_validate_real_model_jacobian_candidate_rollout.sh
results/logs_sample/stage15_6_real_model_jacobian_candidate_rollout.csv
results/logs_sample/stage15_6_real_model_jacobian_candidate_rollout_summary.json
results/logs_sample/stage15_6_real_model_jacobian_candidate_rollout_validation.csv
results/logs_sample/stage15_6_real_model_jacobian_candidate_rollout_validation_summary.json
results/logs_sample/stage15_6_real_model_jacobian_candidate_rollout.log
```

## 5. Run

```bash
bash scripts/stage15_6_validate_real_model_jacobian_candidate_rollout.sh
```

Expected marker:

```text
stage15_6_result: pass
```

## 6. Validation Checks

The validator checks:

- Pinocchio import succeeds
- a Pinocchio model is created or loaded
- Stage 15.5 selected model is used
- at least 12 controlled joints are mapped
- at least 4 foot frames are mapped
- Jacobian norm is positive
- torque candidate values are finite
- alpha 0.10 and 0.20 do not exceed the audit torque limit
- no MuJoCo torque is used
- no ROS torque publisher is used
- frozen mixed baseline remains unchanged

## 7. Next Stage

Stage 15.7 should connect the real-model Jacobian candidate map to a MuJoCo offline rollout audit, still without publishing ROS torque or claiming hardware readiness.
