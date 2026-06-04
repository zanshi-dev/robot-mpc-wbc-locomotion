# Stage 8.0 Runtime Interface Contract Check

## Target

Stage 8 starts with a minimal runtime interface contract check before ROS2/C++ migration.

This test verifies:

1. MuJoCo model dimensions.
2. Pinocchio model dimensions.
3. MuJoCo actuator order.
4. Pinocchio actuated joint order.
5. Floating-base quaternion conversion.
6. qpos / qvel / torque reorder round-trip.
7. MuJoCo foot object and Pinocchio foot frame naming contract.

## Inputs

- MuJoCo model: `assets/go1/scene.xml`
- Pinocchio URDF: `assets/go1/urdf/go1.urdf`

## Outputs

- Log CSV: `results/logs_sample/stage08_runtime_interface_contract_check_log.csv`
- Summary CSV: `results/logs_sample/stage08_runtime_interface_contract_check_summary.csv`

## Result

- pass: `True`
- qpos_roundtrip_max_abs: `0.0`
- qvel_roundtrip_max_abs: `0.0`
- torque_roundtrip_max_abs: `0.0`

## Interpretation

Passing this check means Stage 8 can safely build runtime state adapters on top of the existing Stage 7 mixed baseline.

It does not mean ROS2/C++ real-time control, EKF, MPC velocity tracking, or pure full WBC locomotion is complete.
