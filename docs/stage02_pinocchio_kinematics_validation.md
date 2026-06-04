# Stage 2: Pinocchio Model Parsing and Kinematics Validation

## 目标

验证 Go1 URDF 能被 Pinocchio 正确解析，并与 MuJoCo MJCF 在关节顺序、floating-base quaternion、足端位置、Jacobian 和速度上对齐。

## 模型文件

- MuJoCo MJCF: assets/go1/scene.xml
- Pinocchio URDF: assets/go1/urdf/go1.urdf

## 模型维度

- MuJoCo: nq = 19, nv = 18
- Pinocchio: nq = 19, nv = 18

## 足端 frame

- FR_foot: frame_id = 26
- FL_foot: frame_id = 12
- RR_foot: frame_id = 54
- RL_foot: frame_id = 40

## 关节顺序

MuJoCo actuated joint order:

- FR_hip_joint
- FR_thigh_joint
- FR_calf_joint
- FL_hip_joint
- FL_thigh_joint
- FL_calf_joint
- RR_hip_joint
- RR_thigh_joint
- RR_calf_joint
- RL_hip_joint
- RL_thigh_joint
- RL_calf_joint

Pinocchio actuated joint order:

- FL_hip_joint
- FL_thigh_joint
- FL_calf_joint
- FR_hip_joint
- FR_thigh_joint
- FR_calf_joint
- RL_hip_joint
- RL_thigh_joint
- RL_calf_joint
- RR_hip_joint
- RR_thigh_joint
- RR_calf_joint

## qpos/qvel 映射

Pinocchio q[7:19] 使用以下顺序：

- MuJoCo FL qpos[10:13]
- MuJoCo FR qpos[7:10]
- MuJoCo RL qpos[16:19]
- MuJoCo RR qpos[13:16]

Pinocchio v[6:18] 使用以下顺序：

- MuJoCo FL qvel[9:12]
- MuJoCo FR qvel[6:9]
- MuJoCo RL qvel[15:18]
- MuJoCo RR qvel[12:15]

## quaternion 映射

MuJoCo free joint qpos:

- x, y, z, qw, qx, qy, qz

Pinocchio free-flyer q:

- x, y, z, qx, qy, qz, qw

## 验证结果

- FK position max_error = 0.000000 m
- Jacobian max_error_norm = 0.0000000000
- actuated foot velocity max_velocity_error = 0.000000000000
- full foot velocity max_full_velocity_error = 0.000000000000

## 结论

Pinocchio 与 MuJoCo 的 Go1 运动学已对齐。该映射可用于后续 Jacobian transpose force control、swing foot task-space control、WBC/QP 和 EKF stance foot velocity constraint。
