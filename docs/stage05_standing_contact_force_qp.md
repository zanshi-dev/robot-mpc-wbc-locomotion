# Stage 5: Standing Contact Force QP

## 目标

实现站立状态下的最小接触力 QP，验证 OSQP、摩擦锥约束、法向力约束和期望质心 wrench 跟踪。

本文件记录 Stage 5 的第一步：静态 standing contact force optimization。

## 变量

优化变量为四个足端的三维接触力：

f = [FR_fx, FR_fy, FR_fz,
     FL_fx, FL_fy, FL_fz,
     RR_fx, RR_fy, RR_fz,
     RL_fx, RL_fy, RL_fz]

共 12 维。

## 约束

### 合力约束

sum f_i = [0, 0, mg]

### 合力矩约束

sum r_i x f_i = [0, 0, 0]

其中 r_i 为足端位置相对于 COM 的向量。

### 法向力约束

fz_min <= fz <= fz_max

当前参数：

- fz_min = 1.0 N
- fz_max = 200.0 N

### 摩擦约束

使用线性近似摩擦锥：

- |fx| <= mu * fz
- |fy| <= mu * fz

当前参数：

- mu = 0.6

## 模型参数

从 MuJoCo Go1 模型读取：

- total_mass = 12.743448 kg
- gravity = 9.81 m/s^2
- mg = 125.013225 N
- mg / 4 = 31.253306 N
- COM = [-0.00211295, 0.00087678, 0.26581414]

## 求解结果

OSQP status:

solved

接触力：

- FR: fz = 30.686043 N
- FL: fz = 31.118425 N
- RR: fz = 31.388187 N
- RL: fz = 31.820569 N

验证指标：

- wrench_error_norm = 0.000000000000
- max_abs_fz_error_from_mg4 = 0.567263114189
- friction margins 均为正

## 结论

站立接触力 QP 求解成功。四足法向力接近 mg / 4，并满足零合力矩和摩擦约束。

fz 未完全等于 mg / 4 是合理结果，因为 COM 略偏离几何中心，QP 需要通过四足法向力小幅重分配来满足零合力矩。

## 运行命令

python3 scripts/stage05_standing_contact_force_qp.py --model assets/go1/scene.xml --mu 0.6 --fz_min 1.0 --fz_max 200.0

## 日志文件

results/logs_sample/stage05_standing_contact_force_qp.csv

## 下一步

实现 contact schedule-aware force QP，支持：

- all stance: FR, FL, RR, RL
- trot diagonal stance: FR + RL
- trot diagonal stance: FL + RR

该步骤用于连接 Stage 4 gait scheduler 和 Stage 5 force optimization。

## Contact Schedule-aware Force QP

在 standing contact force QP 基础上，加入 contact schedule。

支持三种接触模式：

- all_stance: [FR, FL, RR, RL] = [1, 1, 1, 1]
- trot_FR_RL: [FR, FL, RR, RL] = [1, 0, 0, 1]
- trot_FL_RR: [FR, FL, RR, RL] = [0, 1, 1, 0]

### inactive leg 约束

当某条腿 inactive 时：

fx = 0
fy = 0
fz = 0

### active leg 约束

当某条腿 active 时：

- fz_min <= fz <= fz_max
- |fx| <= mu * fz
- |fy| <= mu * fz

### QP 形式

为兼容两足对角支撑，contact schedule-aware QP 使用 wrench tracking cost，而不是硬等式 wrench 约束：

min ||A f - desired_wrench||_Q^2 + ||f||_R^2

其中：

- A 为 contact force 到 centroidal wrench 的映射矩阵
- f 为所有足端接触力
- desired_wrench = [0, 0, mg, 0, 0, 0]
- Q 为 wrench tracking 权重
- R 为 force regularization

### 验证结果

all_stance:

- PASS = True
- wrench_error_norm = 0.000003226935

trot_FR_RL:

- PASS = True
- wrench_error_norm = 0.069008876751
- vertical_force_error = -0.000016129890

trot_FL_RR:

- PASS = True
- wrench_error_norm = 0.290227101575
- vertical_force_error = -0.000180978870

### 结论

contact schedule-aware force QP 已通过。inactive legs 的接触力被约束为 0，active legs 满足法向力和摩擦约束。对角两足模式的 wrench residual 是可接受的，因为该 QP 是 tracking formulation，并且 COM 不一定精确落在支撑线对应的静态平衡条件上。

### 运行命令

python3 scripts/stage05_contact_schedule_force_qp.py --model assets/go1/scene.xml --mu 0.6 --fz_min 1.0 --fz_max 200.0

### 日志文件

results/logs_sample/stage05_contact_schedule_force_qp.csv

## N-step Horizon Force QP

在 contact schedule-aware single-step QP 基础上，已扩展为 N-step horizon force QP。

### 参数

- horizon = 10
- dt = 0.02
- decision variables = 120
- 每个 knot 优化 12 维接触力
- contact schedule 来自 trot gait
- desired_wrench = [0, 0, mg, 0, 0, 0]

### 接触模式

horizon 内接触模式：

- k=00~03: trot_FR_RL, flags=[1,0,0,1]
- k=04~09: trot_FL_RR, flags=[0,1,1,0]

### 约束

每个 knot 均包含：

- inactive leg force = 0
- active leg fz_min <= fz <= fz_max
- active leg |fx| <= mu * fz
- active leg |fy| <= mu * fz

### 验证结果

- OSQP status = solved
- decision_variables = 120
- constraint_rows = 160
- max_wrench_error_norm = 0.290227101575
- max_abs_vertical_force_error = 0.000180978871
- 所有 knot 均 pass=True

### 日志文件

results/logs_sample/stage05_horizon_force_qp.csv

### 结论

N-step horizon force QP 已通过。该结果证明 contact schedule、inactive force constraints、friction constraints 和 horizon QP 拼接逻辑正确。

当前仍属于 force-level horizon optimizer，还不是完整 centroidal dynamics MPC。下一步需要加入 base z/vz dynamics tracking。

## Centroidal Z MPC

在 horizon force QP 基础上，加入竖直方向质心动力学，形成最小 convex MPC 原型。

### 状态变量

- z
- vz

### 控制变量

每个 knot 的四足三维接触力：

- FR_fx, FR_fy, FR_fz
- FL_fx, FL_fy, FL_fz
- RR_fx, RR_fy, RR_fz
- RL_fx, RL_fy, RL_fz

### 动力学

z_{k+1} = z_k + dt * vz_k

vz_{k+1} = vz_k + dt * (sum_fz / mass - g)

### 目标

- z 跟踪 z_ref
- vz 跟踪 0
- 接触力正则化

### 约束

- 初始状态固定为当前 z0, vz0
- 每个 knot 满足 centroidal z dynamics
- inactive leg force = 0
- active leg fz_min <= fz <= fz_max
- active leg |fx| <= mu * fz
- active leg |fy| <= mu * fz

### 参数

- horizon = 10
- dt = 0.02
- decision_variables = 142
- constraint_rows = 182
- gait_period = 0.4
- duty_factor = 0.5
- mu = 0.6
- fz_min = 1.0
- fz_max = 200.0

### 验证结果

- OSQP status = solved
- final_z = 0.265816444
- final_vz = -0.000040462
- max_z_error = 0.000002305105
- max_abs_vz = 0.000040462155
- max_dynamics_residual = 0.000000361450
- max_inactive_force_norm = 0.000000001080
- max_abs_vertical_accel = 0.002090110219

### 日志文件

results/logs_sample/stage05_centroidal_z_mpc.csv

### 结论

最小 centroidal z MPC 已通过。该版本已经具备 horizon 状态跟踪、接触时序约束、inactive force 约束、法向力约束和摩擦约束。

当前 Stage 5 已完成最小 convex MPC 原型。下一阶段进入 MPC force 到 joint torque 的转换。
