# Report-Ready Claims and Limitations

## Claims allowed by current evidence
- The project is simulation-only.
- The frozen baseline is mixed_online_control_baseline, not a hardware realtime controller.
- The 1200-step mixed baseline rerun passed.
- The 2400-step simulation-only mixed baseline robustness regression passed.
- ROS2/C++ torque streaming evidence is bounded zero/safe dry-run only.

## Claims not supported by current evidence
- Hardware deployment completed.
- Actuator enablement completed.
- Real robot torque execution completed.
- torque_enable_ready=True.
- A realtime hardware controller was completed.

## Recommended wording

Use: `simulation-only mixed online control baseline with safety-gated ROS2/C++ dry-run evidence`.

Avoid: `hardware-ready torque controller`, `actuator-enabled controller`, or `real robot deployment`.