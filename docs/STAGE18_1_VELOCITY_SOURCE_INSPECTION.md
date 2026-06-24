# Stage 18.1: Velocity Source Inspection

## 1. Goal

Stage 18.1 inspects existing rollout runners and evidence CSV files to determine how to add velocity tracking metrics without rewriting the controller.

## 2. Result

Stage 18.1 result: pass

Recommended source runner:

    scripts/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_runner.py

## 3. Findings

Existing Stage 14.5e evidence already records stability and torque-injection fields such as base height, roll, pitch, candidate scale, torque magnitude, QP failure steps, and saturation steps.

However, the existing candidate log does not include base_x, base_vx, mean_vx, or mean_abs_velocity_error. This is the main Stage 18 gap.

## 4. Generated Files

    results/logs_sample/stage18_1_velocity_source_inspection.csv
    results/logs_sample/stage18_1_velocity_existing_csv_headers.csv
    results/logs_sample/stage18_1_velocity_source_anchor_report.txt
    results/logs_sample/stage18_1_velocity_source_inspection_validation.csv
    results/logs_sample/stage18_1_velocity_source_inspection_summary.json
    docs/STAGE18_1_VELOCITY_SOURCE_INSPECTION.md

## 5. Stage 18.2 Recommendation

Derive a new Stage 18.2 runner from the recommended source runner.

The runner should add:

    base_x
    base_y
    base_vx_fd
    base_vx_qvel_if_available
    target_vx
    velocity_error
    mean_vx
    mean_abs_velocity_error
    final_x
    forward_displacement

The finite-difference velocity should be treated as the auditable primary metric if qvel coordinate semantics are uncertain.

## 6. Claim Boundary

Stage 18.1 is source inspection only. It does not implement velocity tracking, does not rerun the controller, and does not claim hardware deployment.
