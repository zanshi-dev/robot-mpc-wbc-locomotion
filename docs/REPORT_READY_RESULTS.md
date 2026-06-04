# Report-Ready Results

## Scope

This project is explicitly simulation-only. Hardware deployment, actuator enablement, and real robot torque execution are out of scope.

## Baseline

The evaluated baseline is `mixed_online_control_baseline`: stance PD + scaled WBC contribution plus swing PD tracking. It should not be described as a completed full realtime hardware WBC controller.

## Main results

| Experiment | Steps | Transitions | min_z | max_abs_roll | max_abs_pitch | max_joint_error | max_tau_total_abs | QP fails | Saturations | Pass |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| mixed_1200_step | 1200 | 5 | 0.278419161322 | 0.056707402709 | 0.04832948253 | 0.077233662573 | 9.659563043535 | 0 | 0 | True |
| mixed_2400_step | 2400 | 11 | 0.274552192756 | 0.056707402709 | 0.04832948253 | 0.077233662573 | 9.659563043535 | 0 | 0 | True |
| wbc_2400_step | 2400 | 11 | 0.284525843843 | 0.163118252883 | 0.106881861177 |  | 11.520998707973 | 0 | 0 | True |

## Safety statement

No hardware deployment, actuator enablement, or real robot torque execution is claimed.