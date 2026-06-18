# Stage 15.9 MuJoCo J^T f Candidate Injection

## 1. Goal

Stage 15.9 replaces the deterministic Stage 15.8 smoke waveform with the actual Stage 15.6 `J^T f` torque candidate.

The chain is:

```text
Stage 15.5 model readiness report
-> Stage 15.6 Pinocchio foot Jacobian and contact force candidate
-> J^T f torque candidate
-> Stage 15.7 MuJoCo actuator mapping
-> low-alpha MuJoCo actuator command injection
-> short-horizon mj_step smoke test
```

## 2. Boundary

This stage is still not a stable locomotion claim.

It does not claim:

- stable walking
- MPC-WBC closed-loop control
- hardware deployment
- ROS torque publisher readiness
- `torque_enable_ready=True`

It does not modify the frozen mixed baseline.

## 3. Difference from Stage 15.8

Stage 15.8 used a deterministic hand-written torque-like waveform only to test the actuator command path.

Stage 15.9 uses the Stage 15.6 `J^T f` candidate:

```text
contact force -> Pinocchio foot Jacobian -> J^T f -> 12D candidate torque -> MuJoCo actuator command
```

The alpha values are automatically bounded from the Stage 15.6 max candidate torque and a conservative target command limit.

## 4. Safety Limits

```text
steps_per_alpha = 200
audit_ctrl_limit = 0.25
target_max_ctrl = 0.18
```

## 5. Files

```text
scripts/stage15_9_mujoco_jtf_candidate_injection.py
scripts/stage15_9_validate_mujoco_jtf_candidate_injection.py
scripts/stage15_9_validate_mujoco_jtf_candidate_injection.sh
results/logs_sample/stage15_9_mujoco_jtf_candidate_injection.csv
results/logs_sample/stage15_9_mujoco_jtf_candidate_injection_summary.json
results/logs_sample/stage15_9_mujoco_jtf_candidate_injection_validation.csv
results/logs_sample/stage15_9_mujoco_jtf_candidate_injection_validation_summary.json
results/logs_sample/stage15_9_mujoco_jtf_candidate_injection.log
```

## 6. Run

```bash
bash scripts/stage15_9_validate_mujoco_jtf_candidate_injection.sh
```

Expected marker:

```text
stage15_9_result: pass
```

## 7. Next Stage

Stage 15.10 should add a controlled comparison between:

```text
zero ctrl
Stage 15.8 deterministic smoke waveform
Stage 15.9 J^T f candidate injection
```

The comparison should remain short-horizon and should report only safety and compatibility metrics unless a real stabilizing baseline is explicitly connected.
