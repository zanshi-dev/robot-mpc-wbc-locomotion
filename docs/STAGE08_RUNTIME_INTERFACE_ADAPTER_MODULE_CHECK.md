# Stage 8.1 Runtime Interface Adapter Module Check

## Target

Extract the MuJoCo/Pinocchio runtime state mapping from the Stage 8.0 one-off contract check into a reusable Python module.

## Module

- `scripts/common/go1_runtime_interface.py`

## Verified contracts

1. MuJoCo model dimensions.
2. Pinocchio model dimensions.
3. MuJoCo actuator order.
4. Pinocchio actuated joint order.
5. Floating-base quaternion order conversion.
6. qpos / qvel / torque round-trip.
7. MuJoCo foot object and Pinocchio foot frame naming.

## Outputs

- Log CSV: `results/logs_sample/stage08_runtime_interface_adapter_module_check_log.csv`
- Summary CSV: `results/logs_sample/stage08_runtime_interface_adapter_module_check_summary.csv`

## Result

- pass: `True`
- qpos_roundtrip_max_abs: `0.0`
- qvel_roundtrip_max_abs: `0.0`
- torque_roundtrip_max_abs: `0.0`

## Boundary

This stage only creates and validates the Python runtime adapter module.

It does not complete ROS2/C++ migration, EKF, base velocity tracking, full MPC, or pure full WBC locomotion.
