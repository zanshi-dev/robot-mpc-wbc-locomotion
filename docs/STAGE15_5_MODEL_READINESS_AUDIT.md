# Stage 15.5 Model Readiness Audit

## 1. Goal

Stage 15.5 audits the repository model resources before replacing the Stage 15.4 synthetic Pinocchio Jacobian map with a real model based Jacobian map.

The audit scans MJCF, URDF and Xacro files, selects the most relevant robot model candidate, and checks whether the model exposes enough information for the next stage:

- 12 controlled leg joints
- four foot body/site/link/frame candidates
- inferred leg joint order candidates
- inferred foot frame candidates
- clear simulation-only safety boundaries

## 2. Scope

This stage is an audit-only step.

It does not:

- run MuJoCo torque control
- publish ROS torque commands
- modify the frozen mixed baseline
- claim hardware deployment
- claim `torque_enable_ready=True`
- execute a real-model Pinocchio Jacobian rollout

## 3. Files

```text
scripts/stage15_5_model_readiness_audit.py
scripts/stage15_5_validate_model_readiness_audit.py
scripts/stage15_5_validate_model_readiness_audit.sh
results/logs_sample/stage15_5_model_readiness_audit.json
results/logs_sample/stage15_5_model_readiness_audit_inventory.csv
results/logs_sample/stage15_5_model_readiness_audit_validation_summary.json
results/logs_sample/stage15_5_model_readiness_audit_validation.csv
results/logs_sample/stage15_5_model_readiness_audit.log
```

## 4. Run

```bash
bash scripts/stage15_5_validate_model_readiness_audit.sh
```

Expected terminal marker:

```text
stage15_5_result: pass
```

## 5. Interpretation

The generated JSON report contains:

```text
selected_model
readiness.has_12_controlled_joints
readiness.has_4_foot_frame_candidates
readiness.has_full_inferred_joint_order
readiness.has_full_inferred_foot_mapping
readiness.ready_for_real_model_jacobian_stage
```

Passing Stage 15.5 means the repository contains a model candidate that is sufficiently structured for the next stage. It does not mean the real-model Jacobian chain has already been executed.

## 6. Next Stage

Stage 15.6 should use the selected real model candidate to compute foot Jacobians and replace the synthetic kinematic audit model used in Stage 15.4.
