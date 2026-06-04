# Simulation-Only Project Scope

This project is now explicitly scoped as simulation-only.

## In scope

- Unitree Go1 MuJoCo simulation.
- ROS2 topic dry-run validation.
- C++ controller safety-gated bounded zero/safe torque streaming dry-run.
- Reproducible logs, summaries, docs, and regression evidence.
- Python prototype and ROS2/C++ interface consistency checks.
- Report/paper/defense-ready experiment packaging.

## Out of scope

- Hardware deployment.
- Real actuator enablement.
- Real robot torque execution.
- Claiming `torque_enable_ready=True`.
- Claiming hardware realtime controller completion.

## Current frozen evidence

- Stage 12.21-R3 pass: `True`
- continuous_torque_streaming_completed: `True`
- source_hash: `b2d7371786b58300ca68be5542372d5cf8aa2814678b9f451e09bdb8061aa138`
- publish_call_count: `1`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`