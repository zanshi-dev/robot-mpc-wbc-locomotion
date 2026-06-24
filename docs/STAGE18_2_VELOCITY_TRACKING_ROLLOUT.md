# Stage 18.2: Velocity Tracking Rollout

## 1. Goal

Stage 18.2 derives a velocity-tracking evidence runner from the Stage 14.5d MPC-assisted candidate runner.

The derived runner adds per-step velocity evidence:

    base_x
    base_y
    base_vx_fd
    base_vy_fd
    base_vx_qvel
    target_vx
    velocity_error

It also adds summary metrics:

    mean_vx
    mean_abs_velocity_error
    max_abs_velocity_error
    final_x
    forward_displacement

## 2. Result

Stage 18.2 result: pass

Failure count: 0

## 3. Comparison Table

See:

    results/logs_sample/stage18_2_velocity_tracking_rollout_comparison.csv

## 4. Claim Boundary

Stage 18.2 provides simulation-only velocity evidence. It does not claim hardware torque execution, real robot deployment, or comprehensive MPC/WBC superiority over the baseline.
