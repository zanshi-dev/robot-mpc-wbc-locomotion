# Stage 15 Upgrade Summary

## 1. Status

Completed stages: `10/10`

| Stage | Status | Main Evidence | Boundary |
|---|---|---|---|
| 15.1 | pass | C++ gait scheduler, swing trajectory and torque safety filter are built and tested through ROS2/CMake/GTest. | No torque publishing or hardware execution. |
| 15.2 | pass | A C++ contact-force constraint demo validates stance/swing force allocation, normal force and friction constraints. | No OSQP C++ dependency and no closed-loop robot torque execution. |
| 15.3 | pass | Contact force candidates are mapped to 12D torque-candidate statistics through a nominal mapping and alpha sweep. | No real Pinocchio Jacobian, no MuJoCo torque and no ROS torque publisher. |
| 15.4 | pass | Pinocchio foot Jacobian based J^T f candidate rollout is available in an offline dry-run path. | Synthetic/audit kinematic model may be used; no MuJoCo torque execution. |
| 15.5 | pass | MJCF/URDF/Xacro resources are audited for controlled joints, foot frames and mapping readiness. | Audit only; no Jacobian execution or torque execution. |
| 15.6 | pass | Stage 15.5 model metadata or loadable URDF is connected to Pinocchio J^T f candidate generation. | If MJCF fallback is used, real geometry is not claimed; no MuJoCo torque execution. |
| 15.7 | pass | MuJoCo model, joint names, actuators and candidate order are checked through kinematic mj_forward. | No mj_step and no nonzero data.ctrl. |
| 15.8 | pass | A low-amplitude actuator command path is tested with mj_step under strict clipping. | Smoke test only; not stable locomotion and not MPC-WBC closed-loop validation. |
| 15.9 | pass | The Stage 15.6 J^T f candidate is injected into MuJoCo with low alpha for short-horizon safety testing. | Short-horizon only; no stable locomotion claim and no hardware claim. |
| 15.10 | pass | Zero ctrl, deterministic smoke waveform and J^T f candidate are compared under identical short-horizon safety metrics. | Safety/compatibility comparison only; not a walking-performance benchmark. |

## 2. What can be claimed

The project can now claim the following simulation and engineering evidence:

- ROS2/C++ control algorithm modules are buildable and testable through colcon/GTest.
- A C++ contact-force QP demo validates contact-mode and friction/normal-force constraints.
- Contact-force to torque-candidate dry-runs exist with alpha sweep evidence.
- Pinocchio Jacobian based J^T f candidate generation has an offline validation path.
- Model readiness and MuJoCo joint/actuator compatibility are audited with archived reports.
- Bounded MuJoCo actuator-command smoke tests and policy comparisons have been run in short horizon.

## 3. What cannot be claimed

- Stable locomotion from the new J^T f candidate path.
- Full MPC-WBC closed-loop locomotion controller.
- Real robot deployment.
- ROS torque publisher readiness for hardware.
- torque_enable_ready=True.
- Realtime hardware controller completion.

## 4. Interview phrasing

> I upgraded the project in Stage 15 by closing several engineering evidence loops. First, I moved the ROS2/C++ control modules into CMake/GTest. Then I added a C++ contact-force QP demo and built a Python dry-run path from contact force to torque candidates. After that I connected the candidate chain to Pinocchio Jacobians, audited the real model resources, checked MuJoCo joint/actuator compatibility, and finally ran bounded MuJoCo torque-path smoke tests. These results are still simulation-only and short-horizon; I do not claim stable robot walking, real hardware deployment, or torque-enable readiness.

## 5. Recommended next step

Stage 16 should either connect the existing frozen mixed baseline to the Stage 15 candidate path with strict alpha gating, or update the README and one-page technical report so the public project description matches the new evidence.
