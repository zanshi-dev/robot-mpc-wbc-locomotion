# Stage 14.4A Base Velocity Tracking MPC

## Scope

This stage adds a standalone simplified 3D base velocity tracking receding-horizon MPC demo.

It is simulation-only.
It does not publish ROS torque commands.
It does not connect to MuJoCo torque execution.
It does not modify the frozen mixed baseline.
It does not modify disabled_controller_node.cpp.
It does not claim hardware deployment, actuator enablement, or real robot torque execution.

## State, input, and dynamics

State:

x = [px, py, pz, vx, vy, vz]

Input:

u = [f1x, f1y, f1z, f2x, f2y, f2z, f3x, f3y, f3z, f4x, f4y, f4z]

Discrete centroidal point-mass dynamics:

p_next = p + dt * v

v_next = v + dt * (sum_i f_i / m + g)

Only the first force vector u0 from the horizon is applied. At the next rollout step, the solver rebuilds and resolves the QP from the new current state. This is the receding-horizon part.

## Constraints

Swing foot force is constrained to zero.

Each stance foot satisfies:

fz_min <= fz <= fz_max

|fx| <= mu * fz

|fy| <= mu * fz

The total vertical force is constrained by total_fz_max.

## Objective

The QP tracks:

vx toward vx_ref

vy toward 0

z toward z_ref

vz toward 0

The objective also includes contact-force regularization and adjacent-control smoothing.

## Artifacts

Script:

scripts/stage14_4_base_velocity_tracking_mpc_demo.py

Rollout CSV:

results/logs_sample/stage14_4_base_velocity_tracking_mpc_rollout.csv

Summary JSON:

results/logs_sample/stage14_4_base_velocity_tracking_mpc_summary.json

## Acceptance

The summary JSON must contain pass=true.

Required safety flags:

simulation_only_project=true

hardware_deployment_completed=false

torque_enable_ready=false

torque_publisher_enabled=false

control_law_changed=false
