# Stage 14.4B Base Velocity Tracking MPC Rollout Validation

## Scope

Stage 14.4B independently validates the Stage 14.4A standalone simplified 3D base velocity tracking MPC rollout.

This stage does not change the MPC formulation.
This stage does not connect MPC to MuJoCo torque execution.
This stage does not publish ROS torque commands.
This stage does not modify the frozen mixed baseline.
This stage does not modify disabled_controller_node.cpp.

The project remains simulation-only.

## Inputs

Stage 14.4A summary:

results/logs_sample/stage14_4_base_velocity_tracking_mpc_summary.json

Stage 14.4A rollout CSV:

results/logs_sample/stage14_4_base_velocity_tracking_mpc_rollout.csv

Stage 14.4A source script:

scripts/stage14_4_base_velocity_tracking_mpc_demo.py

## Validation checks

The validator checks:

- Stage 14.4A summary pass is true.
- Safety flags remain simulation-only.
- Required rollout CSV columns are present.
- All rollout rows have solved or solved inaccurate OSQP status.
- All state and force values are finite.
- Swing force norm is close to zero.
- Stance vertical force remains within configured bounds.
- Friction pyramid violation is near zero.
- Total vertical force upper violation is near zero.
- vx tracking improves relative to the initial state.
- final vx, vy, and z errors are within thresholds.
- The source script contains the expected receding-horizon pattern:
  - loop over rollout steps
  - solve from current state
  - apply only u0
  - advance simplified centroidal dynamics
  - update previous force for smoothing

## Outputs

Validation per-step CSV:

results/logs_sample/stage14_4b_base_velocity_tracking_mpc_validation.csv

Validation summary JSON:

results/logs_sample/stage14_4b_base_velocity_tracking_mpc_validation_summary.json

## Boundary

Stage 14.4B is validation evidence for a simplified base velocity tracking MPC demo. It is not WBC integration, not MuJoCo torque control, not ROS torque publishing, and not hardware deployment.
