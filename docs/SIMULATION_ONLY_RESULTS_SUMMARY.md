# Simulation-Only Results Summary

## Scope

- Project scope: simulation-only.
- Hardware deployment: out of scope.
- Real actuator enablement: out of scope.
- Real robot torque execution: out of scope.

## Frozen milestones

- Stage 12.22: simulation-only scope freeze passed.
- Stage 13.1B: 1200-step mixed baseline rerun passed.
- Stage 13.2B-R1: 2400-step WBC and mixed baseline robustness regression passed.
- Stage 13.2C: final 2400-step robustness evidence freeze.

## 2400-step mixed baseline metrics

- total_steps: `2400`
- transition_count: `11`
- min_z: `0.274552192756`
- max_abs_roll: `0.056707402709`
- max_abs_pitch: `0.04832948253`
- max_joint_error: `0.077233662573`
- max_tau_total_abs: `9.659563043535`
- qp_fail_steps: `0`
- saturation_steps: `0`
- pass: `True`

## Safety statement

No hardware deployment, actuator enablement, or real robot torque execution is claimed.