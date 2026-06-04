# Stage 6: MPC Force to Joint Torque

## 目标

验证从足端接触力到关节力矩的映射：

tau = J^T f

其中：

- J 为足端位置 Jacobian
- f 为世界系足端接触力
- tau 为 12 维关节力矩
- torque 顺序为 MuJoCo actuator order: FR, FL, RR, RL

## 模型

- MuJoCo model: assets/go1/scene.xml
- Pinocchio URDF: assets/go1/urdf/go1.urdf

## 关节顺序

MuJoCo actuated joint order:

- FR
- FL
- RR
- RL

Pinocchio actuated joint order:

- FL
- FR
- RL
- RR

脚本中已将 Pinocchio torque 重排为 MuJoCo actuator order。

## 测试接触力

每个足端施加世界系向上的接触力：

- fz_each = mg / 4 = 31.253306 N

## 验证结果

MuJoCo Jacobian transpose torque:

[-2.5002645, 0.0, -5.21457138,
  2.5002645, 0.0, -5.21457138,
 -2.5002645, 0.0, -5.21457138,
  2.5002645, 0.0, -5.21457138]

Pinocchio Jacobian transpose torque 与 MuJoCo 结果一致。

验证指标：

- tau_shape = (12,)
- tau_norm = 11.565997966
- tau_max_abs = 5.214571380
- diff_norm = 0.000000000000
- diff_max_abs = 0.000000000000

## 结论

MuJoCo 与 Pinocchio 的 J^T f torque mapping 已对齐。该映射可用于后续将 MPC 输出的足端接触力转换为 MuJoCo actuator torque。

## 下一步

使用 Stage 5 QP 输出的接触力，计算对应 joint torque，并检查 torque limit。
