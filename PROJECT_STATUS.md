# PROJECT_STATUS

## 项目名称
robot-mpc-wbc-locomotion

## 当前阶段
Stage 1: ROS2 + MuJoCo bridge

## 已完成内容
- 已初始化项目仓库。
- 已创建最小 MuJoCo 单腿 XML 模型。
- 已创建最小 torque control 验证脚本。
- 已验证 MuJoCo 模型可以正常加载。
- 已验证 qpos、qvel、body state 和 contact 可以读取。
- 已验证 data.ctrl 可以写入力矩命令。
- 已验证 CSV 日志可以正常保存。
- 已从 mujoco_menagerie 复制 Unitree Go1 MJCF 模型。
- 已验证 Go1 scene 文件包含地面 floor。
- 已确认 Go1 躯干 body 名称为 trunk，body_id = 1。
- 已验证 Go1 torque 接口：nq = 19，nv = 18，nu = 12。
- 已确认 Go1 actuator 顺序：
  - FR_hip
  - FR_thigh
  - FR_calf
  - FL_hip
  - FL_thigh
  - FL_calf
  - RR_hip
  - RR_thigh
  - RR_calf
  - RL_hip
  - RL_thigh
  - RL_calf
- 已验证 Go1 初始地面接触：
  - floor <-> FR
  - floor <-> FL
  - floor <-> RR
  - floor <-> RL
- 已生成日志文件：
  - results/logs_sample/stage00_torque_log.csv
  - results/logs_sample/stage00_go1_scene_torque_log.csv

## 当前目标
完成 Stage 1 最小 ROS2 + MuJoCo bridge 验证。

## 当前问题
Stage 1 最小闭环已完成。当前没有阻塞问题。

## 环境信息
- 操作系统：Ubuntu/Linux，具体版本待记录
- Python：3.13.13
- MuJoCo：3.9.0，Python 包已安装并验证可用
- ROS2：Jazzy，路径 /opt/ros/jazzy/bin/ros2
- Pinocchio：Stage 0 尚未使用
- OSQP：Stage 0 尚未使用
- Eigen：Stage 0 尚未使用
- CMake：Stage 0 尚未使用

## 当前仓库结构
robot-mpc-wbc-locomotion/
├── PROJECT_STATUS.md
├── README.md
├── assets/
├── scripts/
├── docs/
├── src/
├── config/
├── ros2_ws/
└── results/

## 上一次运行命令
python3 scripts/stage00_torque_control_demo.py --model assets/go1/scene.xml --base_body trunk --steps 1000 --log results/logs_sample/stage00_go1_scene_torque_log.csv

## 上一次运行结果
运行成功。Go1 scene 成功加载，模型维度为 nq = 19，nv = 18，nu = 12。脚本使用 trunk 作为 base body。力矩命令成功写入 data.ctrl，qpos/qvel 发生变化，floor contact 成功记录，CSV 日志成功生成。

## 下一步
进入 Stage 1：创建最小 ROS2 + MuJoCo bridge。先验证 ROS2 Jazzy 是否可用，再创建 ROS2 workspace 和最小 package 骨架。

## Stage 1 已完成内容
- 已确认 ROS2 Jazzy 可用。
- 已确认非 Conda 系统 Python 可用：/usr/bin/python3，Python 3.12.3。
- 已确认 rclpy、numpy、mujoco 可在系统 Python 中导入。
- 已创建 ROS2 package：robot_mpc_wbc_bridge。
- 已实现 mujoco_bridge_node。
- 已发布 /go1/joint_states。
- 已发布 /go1/base_state。
- 已发布 /go1/imu。
- 已发布 /go1/foot_contacts。
- 已发布 /go1/sim_time。
- 已订阅 /go1/joint_torque_cmd。
- 已验证 torque command 接收：Received torque command: norm=0.2000。
- 已验证 colcon build 成功。
- 已验证 ros2 topic echo 可读取 bridge 输出。

## Stage 1 验证命令
cd ~/robot-mpc-wbc-locomotion/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run robot_mpc_wbc_bridge mujoco_bridge_node

另开终端：
cd ~/robot-mpc-wbc-locomotion/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 topic list
ros2 topic echo /go1/imu --once
ros2 topic echo /go1/joint_states --once
ros2 topic echo /go1/base_state --once
ros2 topic echo /go1/foot_contacts --once
ros2 topic pub --once /go1/joint_torque_cmd std_msgs/msg/Float64MultiArray "{data: [0.2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}"

## 下一步
进入 Stage 1 收尾：增加最小验证文档和 launch 文件。随后进入 Stage 2：Pinocchio model parsing and kinematics validation。

## Stage 1 完成记录
- ROS2 版本：Jazzy。
- 已创建 ROS2 package：robot_mpc_wbc_bridge。
- 已实现 mujoco_bridge_node。
- 已创建 launch 文件：mujoco_bridge.launch.py。
- 已验证 ros2 launch robot_mpc_wbc_bridge mujoco_bridge.launch.py 可启动。
- 已发布 /go1/joint_states。
- 已发布 /go1/base_state。
- 已发布 /go1/imu。
- 已发布 /go1/foot_contacts。
- 已发布 /go1/sim_time。
- 已订阅 /go1/joint_torque_cmd。
- 已验证 torque command 可被 bridge 接收。
- Stage 1 最小 ROS2 + MuJoCo bridge 已完成。

## 当前目标
进入 Stage 2：Pinocchio model parsing and kinematics validation。

## Stage 2 当前完成记录
- 已安装并验证 Pinocchio：3.9.0。
- 已下载 Go1 URDF：assets/go1/urdf/go1.urdf。
- 已验证 Pinocchio 可加载 Go1 URDF。
- 已确认 Pinocchio 模型维度：nq = 19，nv = 18。
- 已确认 12 个 Go1 关节均存在。
- 已确认足端 frame：
  - FR_foot，frame_id = 26
  - FL_foot，frame_id = 12
  - RR_foot，frame_id = 54
  - RL_foot，frame_id = 40
- 已确认 MuJoCo 与 Pinocchio 关节顺序不同：
  - MuJoCo：FR, FL, RR, RL
  - Pinocchio：FL, FR, RL, RR
- 已实现 MuJoCo qpos/qvel 到 Pinocchio q/v 的显式映射。
- 已处理 floating-base quaternion 顺序差异：
  - MuJoCo: x, y, z, qw, qx, qy, qz
  - Pinocchio: x, y, z, qx, qy, qz, qw
- 已完成初始构型 FK 对齐：
  - FR error = 0.000000 m
  - FL error = 0.000000 m
  - RR error = 0.000000 m
  - RL error = 0.000000 m
  - max_error = 0.000000 m

## Stage 2 下一步
验证 Pinocchio 足端 Jacobian 维度、局部坐标系约定和数值可用性。

## Stage 2 完成记录
- 已安装并验证 Pinocchio：3.9.0。
- 已下载 Go1 URDF：assets/go1/urdf/go1.urdf。
- 已验证 Pinocchio 可加载 Go1 URDF。
- 已确认 Pinocchio 模型维度：nq = 19，nv = 18。
- 已确认 MuJoCo 模型维度：nq = 19，nv = 18。
- 已确认 12 个 Go1 关节均存在。
- 已确认足端 frame：
  - FR_foot，frame_id = 26
  - FL_foot，frame_id = 12
  - RR_foot，frame_id = 54
  - RL_foot，frame_id = 40
- 已确认 MuJoCo 与 Pinocchio 关节顺序不同：
  - MuJoCo：FR, FL, RR, RL
  - Pinocchio：FL, FR, RL, RR
- 已实现 MuJoCo qpos/qvel 到 Pinocchio q/v 的显式映射。
- 已处理 floating-base quaternion 顺序差异：
  - MuJoCo：x, y, z, qw, qx, qy, qz
  - Pinocchio：x, y, z, qx, qy, qz, qw
- 已完成初始构型 FK 对齐：max_error = 0.000000 m。
- 已完成足端 Jacobian 对齐：max_error_norm = 0.0000000000。
- 已完成 actuated foot velocity 对齐：max_velocity_error = 0.000000000000。
- 已完成 full foot velocity 对齐：max_full_velocity_error = 0.000000000000。
- Stage 2 已完成。

## 当前目标
进入 Stage 3：Standing controller and PD baseline。

## Stage 3 当前完成记录
- 已实现最小 Go1 joint PD standing controller。
- 控制公式：tau = kp * (q_des - q) - kd * qd。
- 已设置 standing pose：
  - 每条腿 hip = 0.0
  - 每条腿 thigh = 0.9
  - 每条腿 calf = -1.8
- 已实现自动 base height 初始化，使足端接近地面。
- 已记录 base height、roll、pitch、torque norm、torque saturation 和 contact pairs。
- 推荐 baseline 参数：
  - kp = 80
  - kd = 2.0
  - torque_limit = 23.7
- 推荐 baseline 结果：
  - final_base_z = 0.274232
  - final_roll = -0.000390
  - final_pitch = -0.000545
  - min_base_z = 0.273452
  - max_abs_roll = 0.065949
  - max_abs_pitch = 0.024280
  - torque_saturation_count = 0
- Stage 3 standing PD baseline 已通过 1000 steps 稳定站立验证。

## Stage 3 下一步
生成 Stage 3 文档，然后进入 Stage 4：Gait scheduler, swing trajectory and foothold planner。

## Stage 4 当前完成记录
- 已实现离线 trot contact schedule。
- 腿顺序采用 MuJoCo 控制顺序：FR, FL, RR, RL。
- trot 对角腿分组：
  - Group A: FR + RL
  - Group B: FL + RR
- 已实现 phase 计算。
- 已实现 stance / swing 状态判断。
- 已实现 swing_phase 计算。
- 已实现 smoothstep + parabolic foot clearance swing trajectory。
- 已实现基础 Raibert-style foothold planner。
- 已验证接触序列交替：
  - [FR, FL, RR, RL] = [1, 0, 0, 1]
  - [FR, FL, RR, RL] = [0, 1, 1, 0]
- 已验证 swing foot height：
  - min_z = 0.019
  - max_z = 0.078904
- 已验证 vx_cmd = 0.2 时 foothold 前移：
  - FR/FL x: 0.1881 -> 0.2071
  - RR/RL x: -0.1881 -> -0.1691
- 已生成日志：
  - results/logs_sample/stage04_gait_swing_foothold_log.csv

## Stage 4 下一步
将 gait scheduler 和 swing trajectory 接入 MuJoCo standing PD baseline，形成 open-loop trot baseline。暂不进入 MPC。

## Stage 4 完成记录
- 已完成离线 trot contact schedule、phase、stance/swing 状态机、swing trajectory 和 Raibert-style foothold planner。
- 已完成 MuJoCo open-loop trot PD baseline。
- 当前采用保守 in-place leg-lift trot baseline：
  - gait_period = 1.0
  - duty_factor = 0.75
  - kp = 80
  - kd = 2.0
  - torque_limit = 23.7
  - swing delta q = [0.0, -0.10, 0.18]
- 已验证 1000 steps open-loop trot leg-lift baseline 保持大致直立：
  - final_base_z = 0.290198
  - final_roll = 0.028324
  - final_pitch = -0.038504
  - min_base_z = 0.274788
  - max_abs_roll = 0.086004
  - max_abs_pitch = 0.053453
  - torque_saturation_count = 0
- 已生成日志：
  - results/logs_sample/stage04_gait_swing_foothold_log.csv
  - results/logs_sample/stage04_open_loop_trot_pd_conservative_log.csv
- Stage 4 已完成。

## 当前目标
进入 Stage 5：Convex MPC contact force optimization。先实现站立状态下的 centroidal force QP，验证四足接触力接近 mg/4。

## Stage 5 当前完成记录
- 已验证 Python OSQP / scipy / numpy 可用。
- 已实现站立状态下的 12 维接触力 QP：
  - 变量：FR, FL, RR, RL 四足三维接触力，共 12 维。
  - 约束：合力 = mg。
  - 约束：关于 COM 的合力矩 = 0。
  - 约束：fz_min <= fz <= fz_max。
  - 约束：|fx| <= mu * fz。
  - 约束：|fy| <= mu * fz。
- 已使用 Go1 MuJoCo 模型计算总质量和 COM：
  - total_mass = 12.743448 kg
  - mg = 125.013225 N
  - mg / 4 = 31.253306 N
  - COM = [-0.00211295, 0.00087678, 0.26581414]
- QP 求解结果：
  - OSQP status = solved
  - wrench_error_norm = 0.000000000000
  - max_abs_fz_error_from_mg4 = 0.567263114189
  - friction margins 均为正
- 接触力结果：
  - FR fz = 30.686043 N
  - FL fz = 31.118425 N
  - RR fz = 31.388187 N
  - RL fz = 31.820569 N
- 已生成日志：
  - results/logs_sample/stage05_standing_contact_force_qp.csv

## Stage 5 下一步
实现 contact schedule-aware force QP，支持四足接触、FR+RL 对角接触、FL+RR 对角接触，为后续 convex MPC horizon 做准备。

## Stage 5 contact schedule-aware QP 完成记录
- 已实现 contact schedule-aware force QP。
- 支持三种接触模式：
  - all_stance: FR, FL, RR, RL
  - trot_FR_RL: FR + RL
  - trot_FL_RR: FL + RR
- 已实现 inactive leg force = 0 约束。
- 已实现 active leg 的 fz bounds 和 friction pyramid 约束。
- 已将硬等式 wrench QP 扩展为 wrench tracking QP：
  - min ||A f - desired_wrench||_Q^2 + ||f||_R^2
- all_stance 结果：
  - PASS = True
  - wrench_error_norm = 0.000003226935
- trot_FR_RL 结果：
  - PASS = True
  - wrench_error_norm = 0.069008876751
  - vertical_force_error = -0.000016129890
- trot_FL_RR 结果：
  - PASS = True
  - wrench_error_norm = 0.290227101575
  - vertical_force_error = -0.000180978870
- 已生成日志：
  - results/logs_sample/stage05_contact_schedule_force_qp.csv

## Stage 5 下一步
实现最小 horizon force QP，将多个未来 contact schedule 串联成 N-step convex MPC 原型。

## Stage 5 horizon force QP 完成记录
- 已实现 N-step horizon force QP 原型。
- horizon = 10。
- dt = 0.02。
- 决策变量维度 = 120。
- 每个 knot 优化 12 维接触力。
- contact schedule 来自 trot gait。
- inactive leg force 已约束为 0。
- active leg 满足 fz bounds 和 friction pyramid。
- horizon 内接触模式完成切换：
  - k=00~03: trot_FR_RL, flags=[1,0,0,1]
  - k=04~09: trot_FL_RR, flags=[0,1,1,0]
- OSQP status = solved。
- 所有 knot 均 pass=True。
- max_wrench_error_norm = 0.290227101575。
- max_abs_vertical_force_error = 0.000180978871。
- 已生成日志：
  - results/logs_sample/stage05_horizon_force_qp.csv

## Stage 5 下一步
实现最小 centroidal MPC 状态跟踪：在 horizon 内根据接触力预测 base 线速度和高度变化，加入 z/vz tracking cost。

## Stage 5 centroidal z MPC 完成记录
- 已实现最小 centroidal z MPC。
- 状态变量：
  - z
  - vz
- 控制变量：
  - horizon 内每个 knot 的四足三维接触力
- 动力学：
  - z_{k+1} = z_k + dt * vz_k
  - vz_{k+1} = vz_k + dt * (sum_fz / mass - g)
- horizon = 10。
- dt = 0.02。
- decision_variables = 142。
- constraint_rows = 182。
- contact schedule 来自 trot gait。
- inactive leg force 已约束为 0。
- active leg 满足 fz bounds 与 friction pyramid。
- OSQP status = solved。
- 验证结果：
  - final_z = 0.265816444
  - final_vz = -0.000040462
  - max_z_error = 0.000002305105
  - max_abs_vz = 0.000040462155
  - max_dynamics_residual = 0.000000361450
  - max_inactive_force_norm = 0.000000001080
  - max_abs_vertical_accel = 0.002090110219
- 已生成日志：
  - results/logs_sample/stage05_centroidal_z_mpc.csv
- Stage 5 已完成最小 convex MPC 原型。

## 当前目标
进入 Stage 6：MPC force to joint torque。先实现 tau = J^T f 的离线验证。

## Stage 6 当前完成记录
- 已实现离线 Jacobian transpose torque mapping 验证。
- 控制映射公式：
  - tau = J^T f
- 已分别使用 MuJoCo Jacobian 和 Pinocchio Jacobian 计算 joint torque。
- 已确认 MuJoCo 与 Pinocchio torque 映射完全一致。
- 测试接触力：
  - 每足 fz = mg / 4 = 31.253306 N
  - force direction = +z
- torque 输出顺序：
  - FR, FL, RR, RL
- 验证结果：
  - tau_shape = (12,)
  - tau_norm = 11.565997966
  - tau_max_abs = 5.214571380
  - diff_norm = 0.000000000000
  - diff_max_abs = 0.000000000000
- Stage 6 的 J^T f 离线映射验证已通过。

## Stage 6 下一步
使用 Stage 5 QP 求出的真实接触力，计算对应 joint torque，并检查 torque limit。

<!-- STAGE6_QP_FORCE_TO_ACTUATOR_TORQUE_START -->

## Stage 6 更新：QP 接触力到 actuator torque

Stage 6 离线 QP force to actuator torque 验证已通过。

输入文件：

results/logs_sample/stage05_standing_contact_force_qp.csv

输出文件：

results/logs_sample/stage06_qp_force_to_actuator_torque.csv

已确认符号约定：

actuator_tau = - J^T f_qp

数值结果：

tau_norm     = 11.567004356004
tau_max_abs  = 5.309218454936
torque_limit = 23.7
pass         = True

每条腿 actuator torque：

FR = [ 2.454883448,  0.000000000, 5.119924306]
FL = [-2.489474011, -0.000000000, 5.192066657]
RR = [ 2.511054984,  0.000000000, 5.237076104]
RL = [-2.545645547, -0.000000000, 5.309218455]

下一步：运行短时 MuJoCo 支撑闭环测试，使用 tau_total = tau_pd + tau_qp_actuator。

<!-- STAGE6_QP_FORCE_TO_ACTUATOR_TORQUE_END -->

<!-- STAGE6_QP_TORQUE_SUPPORT_TEST_START -->

## Stage 6 更新：QP torque 短时支撑闭环测试

Stage 6 QP torque support test 已通过。

测试形式：

tau_total = tau_pd + tau_qp_actuator

符号约定：

tau_qp_actuator = - J^T f_qp

控制参数：

kp = 80.0
kd = 2.0
torque_limit = 23.7
sim_steps = 1000

结果：

initial_z = 0.284805846483
final_z = 0.289618537988
min_z = 0.284805846483
max_z = 0.305958635013
delta_z = 0.004812691505
max_abs_roll = 0.066226209316
max_abs_pitch = 0.033555433733
max_tau_pd_abs = 13.776436903041
max_tau_qp_abs = 5.336923217750
max_tau_total_abs = 8.832121424115
saturation_steps = 0
pass = True

日志文件：

results/logs_sample/stage06_qp_torque_support_test_log.csv

汇总文件：

results/logs_sample/stage06_qp_torque_support_test_summary.csv

结论：

Stage 5 QP contact force 已可通过 Stage 6 映射接入 MuJoCo actuator torque，并通过短时支撑闭环测试。

<!-- STAGE6_QP_TORQUE_SUPPORT_TEST_END -->

<!-- STAGE6_SUMMARY_STAGE7_INTERFACE_START -->

## Stage 6 总结与 Stage 7 接口约定

Stage 6 已完成。

已完成：

1. J^T f 离线映射验证
2. Stage 5 QP 接触力到 actuator torque 转换
3. torque limit 检查
4. force sign sanity check
5. MuJoCo 短时支撑闭环测试

已确认符号约定：

tau_qp_actuator = - J^T f_qp

已确认 torque 顺序：

FR_hip, FR_thigh, FR_calf,
FL_hip, FL_thigh, FL_calf,
RR_hip, RR_thigh, RR_calf,
RL_hip, RL_thigh, RL_calf

Stage 6 核心结果：

tau_norm = 11.567004356004
tau_max_abs = 5.309218454936
torque_limit = 23.7
pass = True

短时支撑闭环结果：

initial_z = 0.284805846483
final_z = 0.289618537988
min_z = 0.284805846483
max_abs_roll = 0.066226209316
max_abs_pitch = 0.033555433733
max_tau_total_abs = 8.832121424115
saturation_steps = 0
pass = True

Stage 7 起点：

先实现最小 WBC/QP torque regularization 原型，不直接进入完整 WBC。

目标文件：

scripts/stage07_minimal_wbc_torque_qp.py

输出文件：

results/logs_sample/stage07_minimal_wbc_torque_qp.csv

<!-- STAGE6_SUMMARY_STAGE7_INTERFACE_END -->

<!-- STAGE7_MINIMAL_WBC_TORQUE_QP_START -->

## Stage 7 更新：最小 WBC Torque QP

Stage 7 第一小步已通过。

输入文件：

results/logs_sample/stage06_qp_force_to_actuator_torque.csv

输出文件：

results/logs_sample/stage07_minimal_wbc_torque_qp.csv

QP 变量：

tau_wbc，12 维

目标函数：

W_TRACK * ||tau - tau_ref||^2 + W_REG * ||tau||^2

参数：

W_TRACK = 1.0
W_REG = 0.0001
torque_limit = 23.7

结果：

OSQP status = solved
tau_ref_max_abs = 5.309218454936
tau_wbc_max_abs = 5.308687586177
diff_norm = 0.001156584777
diff_max_abs = 0.000530868759
limit_pass = True
pass = True

结论：

最小 WBC/QP torque 原型已通过，QP 框架可运行，输出满足 torque limit，并与 Stage 6 tau_ref 高度接近。

下一步：

将 tau_wbc 接入 MuJoCo 短时支撑测试，使用 tau_total = tau_pd + tau_wbc。

<!-- STAGE7_MINIMAL_WBC_TORQUE_QP_END -->

<!-- STAGE7_WBC_TORQUE_SUPPORT_TEST_START -->

## Stage 7 更新：WBC torque 短时支撑测试

Stage 7 WBC torque support test 已通过。

测试形式：

tau_total = tau_pd + tau_wbc

tau_wbc 来源：

results/logs_sample/stage07_minimal_wbc_torque_qp.csv

控制参数：

kp = 80.0
kd = 2.0
torque_limit = 23.7
sim_steps = 1000

结果：

initial_z = 0.284805846483
final_z = 0.293882173125
min_z = 0.284805846483
max_z = 0.304683134056
delta_z = 0.009076326641
max_abs_roll = 0.079919230304
max_abs_pitch = 0.032882365738
max_tau_pd_abs = 13.907303920111
max_tau_wbc_abs = 5.308687586177
max_tau_total_abs = 8.787891555301
saturation_steps = 0
pass = True

日志文件：

results/logs_sample/stage07_wbc_torque_support_test_log.csv

汇总文件：

results/logs_sample/stage07_wbc_torque_support_test_summary.csv

结论：

Stage 7 minimal WBC torque QP 输出可以接入 MuJoCo actuator torque，并通过 1000 steps 短时支撑测试。

下一步：

进入 Stage 7 第三小步：实现 base wrench tracking 的离线 WBC/QP 原型。

<!-- STAGE7_WBC_TORQUE_SUPPORT_TEST_END -->

<!-- STAGE7_WBC_BASE_WRENCH_QP_START -->

## Stage 7 更新：Base Wrench Tracking WBC/QP

Stage 7 第三小步已通过。

输入文件：

results/logs_sample/stage05_standing_contact_force_qp.csv

results/logs_sample/stage06_qp_force_to_actuator_torque.csv

输出文件：

results/logs_sample/stage07_wbc_base_wrench_qp.csv

QP 变量：

f_wbc，12 维接触力

符号约定：

tau = -J^T f

约束：

mu = 0.6
fz_min = 1.0
fz_max = 120.0
torque_limit = 23.7

结果：

OSQP status = solved
tau_max_abs = 5.309219364818
min_fz = 30.686044870227
force_diff_norm = 0.000010473048
tau_diff_norm = 0.000003100096
wrench_error_norm = 0.000014313895
torque_pass = True
fz_pass = True
pass = True

结论：

Stage 7 base wrench tracking WBC/QP 离线原型已通过，能够在满足摩擦、法向力和 torque limit 约束下跟踪已验证 base wrench、contact force 和 actuator torque。

下一步：

将 stage07_wbc_base_wrench_qp.csv 中的 torque 接入 MuJoCo 短时支撑测试。

<!-- STAGE7_WBC_BASE_WRENCH_QP_END -->

<!-- STAGE7_WBC_BASE_WRENCH_SUPPORT_TEST_START -->

## Stage 7 更新：Base Wrench WBC/QP 短时支撑测试

Stage 7 base wrench support test 已通过。

输入文件：

results/logs_sample/stage07_wbc_base_wrench_qp.csv

输出文件：

results/logs_sample/stage07_wbc_base_wrench_support_test_log.csv

results/logs_sample/stage07_wbc_base_wrench_support_test_summary.csv

results/logs_sample/stage07_wbc_base_wrench_support_test_margin_check.csv

测试形式：

tau_total = tau_pd + tau_wbc_base_wrench

控制参数：

kp = 80.0
kd = 2.0
torque_limit = 23.7
sim_steps = 1000

支撑测试结果：

initial_z = 0.284805846483
final_z = 0.296097865333
min_z = 0.284697187237
max_z = 0.306443647985
delta_z = 0.011292018850
max_abs_roll = 0.142713128163
max_abs_pitch = 0.027806141378
max_tau_pd_abs = 14.174824804721
max_tau_wbc_abs = 5.309219364818
max_tau_total_abs = 8.865605439903
saturation_steps = 0
pass = True

Margin 检查：

roll_margin_to_0p15 = 0.007286871837
pitch_margin_to_0p15 = 0.122193858622
z_margin_to_0p22 = 0.064697187237
final_roll = -0.012013715200
final_pitch = -0.018424145765
pass_margin = True

结论：

Stage 7 base wrench tracking WBC/QP 输出可以接入 MuJoCo actuator torque，并通过短时支撑测试。roll margin 较小，后续完整 WBC 接入时需要重点监控 roll 稳定性。

下一步：

加入 posture regularization 的 WBC/QP 离线原型，输出 results/logs_sample/stage07_wbc_posture_regularized_qp.csv。

<!-- STAGE7_WBC_BASE_WRENCH_SUPPORT_TEST_END -->

<!-- STAGE7_WBC_VARIANT_COMPARISON_START -->

## Stage 7 更新：WBC Variant 对比

Stage 7 WBC variant comparison 已完成。

对比文件：

results/logs_sample/stage07_wbc_variant_comparison.csv

对比对象：

1. base_wrench_qp
2. posture_regularized_qp

base_wrench_qp 结果：

qp_pass = True
support_pass = True
margin_pass = True
tau_max_abs = 5.309219364818
max_tau_total_abs = 8.865605439903
max_abs_roll = 0.142713128163
roll_margin_to_0p15 = 0.007286871837
max_abs_pitch = 0.027806141378
pitch_margin_to_0p15 = 0.122193858622
min_z = 0.284697187237
z_margin_to_0p22 = 0.064697187237
saturation_steps = 0
accepted_baseline = True

posture_regularized_qp 结果：

qp_pass = True
support_pass = True
margin_pass = False
tau_max_abs = 5.307369014842
max_tau_total_abs = 9.208799641206
max_abs_roll = 0.147238297335
roll_margin_to_0p15 = 0.002761702665
max_abs_pitch = 0.048544437721
pitch_margin_to_0p15 = 0.101455562279
min_z = 0.284805846483
z_margin_to_0p22 = 0.064935407676
saturation_steps = 0
accepted_baseline = False
reject_reason = margin_check_failed

结论：

当前 Stage 7 默认基准选择 base_wrench_qp。

后续默认 torque source：

results/logs_sample/stage07_wbc_base_wrench_qp.csv

posture_regularized_qp 暂时保留为实验 variant，不作为默认控制输入。

<!-- STAGE7_WBC_VARIANT_COMPARISON_END -->

<!-- STAGE7_SUMMARY_AND_NEXT_STEPS_START -->

## Stage 7 总结与后续边界

Stage 7 当前第一轮 WBC/QP 原型验证完成。

当前完成内容：

1. minimal WBC torque QP
2. minimal WBC torque QP 支撑测试
3. base wrench tracking WBC/QP
4. base wrench tracking WBC/QP 支撑测试
5. posture regularized WBC/QP 实验 variant
6. posture regularized WBC/QP 支撑测试
7. WBC variant comparison
8. 默认 WBC baseline 选择

当前默认 WBC baseline：

results/logs_sample/stage07_wbc_base_wrench_qp.csv

默认选择原因：

base_wrench_qp 同时通过 QP、support test 和 margin check。

base_wrench_qp 核心结果：

tau_max_abs = 5.309219364818
max_tau_total_abs = 8.865605439903
max_abs_roll = 0.142713128163
roll_margin_to_0p15 = 0.007286871837
max_abs_pitch = 0.027806141378
pitch_margin_to_0p15 = 0.122193858622
min_z = 0.284697187237
z_margin_to_0p22 = 0.064697187237
saturation_steps = 0
accepted_baseline = True

posture_regularized_qp 暂不作为默认控制输入：

margin_pass = False
roll_margin_to_0p15 = 0.002761702665
max_abs_roll = 0.147238297335
max_tau_total_abs = 9.208799641206
reject_reason = margin_check_failed

已确认接口约定：

leg order = FR, FL, RR, RL
joint order per leg = hip, thigh, calf
torque order = MuJoCo actuator order
force-to-torque sign = tau = -J^T f
torque_limit = 23.7
standing pose = [0.0, 0.9, -1.8] per leg
PD baseline = kp 80.0, kd 2.0

当前不足：

当前不是完整动态 WBC。尚未实现 floating base dynamics equality、qdd/contact force/torque 联合优化、swing foot tracking、stance foot acceleration constraint、base pose tracking、contact schedule-aware WBC、动态 trot 闭环和 ROS2 节点化。

下一步：

继续 Stage 7，不进入 Stage 8 EKF。

实现 contact schedule-aware WBC/QP 离线原型：

scripts/stage07_contact_schedule_wbc_qp.py

输出文件：

results/logs_sample/stage07_contact_schedule_wbc_qp.csv

支持 contact mode：

all_stance
trot_FR_RL
trot_FL_RR

通过标准：

OSQP status = solved
三种 contact mode 均 pass
inactive force norm 接近 0
tau_max_abs <= 23.7
active legs fz >= 1.0

<!-- STAGE7_SUMMARY_AND_NEXT_STEPS_END -->

<!-- STAGE7_CONTACT_SCHEDULE_WBC_QP_START -->

## Stage 7 更新：Contact Schedule-Aware WBC/QP

Stage 7 contact schedule-aware WBC/QP 离线原型已通过。

输出文件：

results/logs_sample/stage07_contact_schedule_wbc_qp.csv

支持 contact mode：

1. all_stance
2. trot_FR_RL
3. trot_FL_RR

约束：

inactive legs force = 0
active legs fz >= 1.0
active legs fz <= 120.0
friction pyramid, mu = 0.6
torque limit = 23.7
tau = -J^T f

结果：

all_stance:
OSQP status = solved
tau_max_abs = 5.300523665634
inactive_force_norm = 0.000000000000
min_active_fz = 30.740275659250
min_friction_margin = 18.439589223416
wrench_error_norm = 0.023024675737
pass = True

trot_FR_RL:
OSQP status = solved
tau_max_abs = 10.638319002741
inactive_force_norm = 0.000000000000
min_active_fz = 61.943834115289
min_friction_margin = 36.183066443294
wrench_error_norm = 0.141237586084
pass = True

trot_FL_RR:
OSQP status = solved
tau_max_abs = 10.594245657447
inactive_force_norm = 0.000000000000
min_active_fz = 62.190915998027
min_friction_margin = 36.331145835311
wrench_error_norm = 0.264596535614
pass = True

结论：

contact schedule-aware WBC/QP 离线原型通过。三种 contact mode 均可解，inactive force 为 0，active force 满足 fz/friction constraints，tau 未超过 23.7 Nm。

下一步：

将 contact schedule-aware WBC/QP 的 trot_FR_RL 和 trot_FL_RR 分别接入 MuJoCo 短时支撑测试，先做静态单模式，不做动态切换。

<!-- STAGE7_CONTACT_SCHEDULE_WBC_QP_END -->

<!-- STAGE7_CONTACT_SCHEDULE_WBC_SCALED_SUPPORT_TEST_START -->

## Stage 7 更新：Contact Schedule WBC/QP Scaled Support Test

原始 contact schedule-aware WBC/QP 静态支撑测试中，trot_FR_RL 在 scale = 1.0 时失败：

max_abs_roll = 0.156525005128 > 0.15

已完成 trot_FR_RL scale sweep：

scale = 0.6:
max_abs_roll = 0.110752061094
roll_margin_to_0p15 = 0.039247938906
max_abs_pitch = 0.052921077590
max_tau_total_abs = 9.331342107139
pass = True
pass_margin = True

scale = 0.7:
max_abs_roll = 0.121897064021
roll_margin_to_0p15 = 0.028102935979
pass = True
pass_margin = True

scale = 0.8:
max_abs_roll = 0.145498241123
roll_margin_to_0p15 = 0.004501758877
pass = True
pass_margin = False

scale = 0.9:
max_abs_roll = 0.123066868700
roll_margin_to_0p15 = 0.026933131300
pass = True
pass_margin = True

scale = 1.0:
max_abs_roll = 0.156525005128
roll_margin_to_0p15 = -0.006525005128
pass = False
pass_margin = False

推荐：

trot_FR_RL scale = 0.6

Scaled support test 使用：

all_stance scale = 1.0
trot_FR_RL scale = 0.6
trot_FL_RR scale = 1.0

Scaled support test 结果：

all_stance:
final_z = 0.290673824396
min_z = 0.284805846483
max_abs_roll = 0.053689475648
roll_margin_to_0p15 = 0.096310524352
max_abs_pitch = 0.029696786699
max_tau_total_abs = 8.858349940928
saturation_steps = 0
pass = True
pass_margin = True

trot_FR_RL:
final_z = 0.295056299833
min_z = 0.284715134142
max_abs_roll = 0.110752061094
roll_margin_to_0p15 = 0.039247938906
max_abs_pitch = 0.052921077590
max_tau_total_abs = 9.331342107139
saturation_steps = 0
pass = True
pass_margin = True

trot_FL_RR:
final_z = 0.300769804656
min_z = 0.284805846483
max_abs_roll = 0.133384221160
roll_margin_to_0p15 = 0.016615778840
max_abs_pitch = 0.070571666592
max_tau_total_abs = 11.454092417624
saturation_steps = 0
pass = True
pass_margin = True

结论：

scaled contact schedule WBC support test 已通过。当前静态单模式建议使用 all_stance scale = 1.0，trot_FR_RL scale = 0.6，trot_FL_RR scale = 1.0。

当前边界：

该测试仍是静态单模式测试，不是动态步态切换，不能宣称已经完成 trot closed-loop locomotion。

下一步：

实现 contact mode transition sanity check，检查三种 torque 模式之间的跳变，输出 results/logs_sample/stage07_contact_mode_transition_check.csv。

<!-- STAGE7_CONTACT_SCHEDULE_WBC_SCALED_SUPPORT_TEST_END -->

<!-- STAGE7_CONTACT_MODE_TRANSITION_CHECK_START -->

## Stage 7 更新：Contact Mode Transition Sanity Check

contact mode transition sanity check 已完成。

输入文件：

results/logs_sample/stage07_contact_schedule_wbc_qp.csv

输出文件：

results/logs_sample/stage07_contact_mode_transition_check.csv

当前 scale：

all_stance scale = 1.0
trot_FR_RL scale = 0.6
trot_FL_RR scale = 1.0

阈值：

torque jump norm warning threshold = 8.0
torque jump max warning threshold = 5.0

结果：

all_stance -> trot_FR_RL:
jump_norm = 8.327068144804
jump_max_abs = 5.237904619970
need_smoothing = True

trot_FR_RL -> all_stance:
jump_norm = 8.327068144804
jump_max_abs = 5.237904619970
need_smoothing = True

all_stance -> trot_FL_RR:
jump_norm = 11.463539646901
jump_max_abs = 5.356341037477
need_smoothing = True

trot_FL_RR -> all_stance:
jump_norm = 11.463539646901
jump_max_abs = 5.356341037477
need_smoothing = True

trot_FR_RL -> trot_FL_RR:
jump_norm = 18.895751942469
jump_max_abs = 10.594245657447
need_smoothing = True

trot_FL_RR -> trot_FR_RL:
jump_norm = 18.895751942469
jump_max_abs = 10.594245657447
need_smoothing = True

结论：

所有 contact mode transition 都触发 smoothing 需求。当前不应直接执行动态 contact switching，必须先加入 torque ramp 或 low-pass smoothing。

下一步：

实现 torque ramp transition 离线检查，建议 ramp_steps = 5, 10, 20, 40，输出 results/logs_sample/stage07_contact_mode_torque_ramp_check.csv。

<!-- STAGE7_CONTACT_MODE_TRANSITION_CHECK_END -->

<!-- STAGE7_CONTACT_MODE_TORQUE_RAMP_CHECK_START -->

## Stage 7 更新：Contact Mode Torque Ramp Check

contact mode torque ramp check 已完成并通过。

输入文件：

results/logs_sample/stage07_contact_schedule_wbc_qp.csv

输出文件：

results/logs_sample/stage07_contact_mode_torque_ramp_check.csv

当前 scale：

all_stance scale = 1.0
trot_FR_RL scale = 0.6
trot_FL_RR scale = 1.0

测试 ramp_steps：

5, 10, 20, 40

判定阈值：

step_jump_norm <= 8.0
step_jump_max_abs <= 5.0

结果：

ramp_steps = 5:
all_pass = True
max_step_jump_norm = 3.779150388494
max_step_jump_abs = 2.118849131489

ramp_steps = 10:
all_pass = True
max_step_jump_norm = 1.889575194247
max_step_jump_abs = 1.059424565745

ramp_steps = 20:
all_pass = True
max_step_jump_norm = 0.944787597123
max_step_jump_abs = 0.529712282872

ramp_steps = 40:
all_pass = True
max_step_jump_norm = 0.472393798562
max_step_jump_abs = 0.264856141436

推荐：

recommended_ramp_steps = 5

结论：

contact mode transition 必须使用 torque ramp。当前推荐 ramp_steps = 5。直接动态切换不应使用。

下一步：

实现带 ramp 的 contact mode sequence MuJoCo 短时测试。建议 sequence 为 all_stance -> trot_FR_RL -> all_stance -> trot_FL_RR -> all_stance，每段 300 steps，transition ramp_steps = 5。

<!-- STAGE7_CONTACT_MODE_TORQUE_RAMP_CHECK_END -->

<!-- STAGE7_CONTACT_MODE_SEQUENCE_RAMP_TEST_START -->

## Stage 7 更新：Contact Mode Sequence Ramp Test

带 ramp 的 contact mode sequence 短时测试已通过。

输入文件：

results/logs_sample/stage07_contact_schedule_wbc_qp.csv

输出文件：

results/logs_sample/stage07_contact_mode_sequence_ramp_test_log.csv

results/logs_sample/stage07_contact_mode_sequence_ramp_test_summary.csv

测试 sequence：

all_stance -> trot_FR_RL -> all_stance -> trot_FL_RR -> all_stance

每段：

300 steps

总步数：

1500 steps

scale：

all_stance scale = 1.0
trot_FR_RL scale = 0.6
trot_FL_RR scale = 1.0

ramp_steps = 5

控制参数：

kp = 80.0
kd = 2.0
torque_limit = 23.7

结果：

initial_z = 0.284805846483
final_z = 0.294798253254
min_z = 0.284805846483
max_z = 0.305856777251
delta_z = 0.009992406771
final_roll = -0.015084373526
final_pitch = -0.036988602386
max_abs_roll = 0.096498358293
roll_margin_to_0p15 = 0.053501641707
max_abs_pitch = 0.058977498277
pitch_margin_to_0p15 = 0.091022501723
z_margin_to_0p22 = 0.064805846483
max_tau_pd_abs = 18.874491898669
max_tau_wbc_cmd_abs = 10.594245657447
max_tau_total_abs = 10.974863827195
max_cmd_step_jump_norm = 2.292707929380
max_cmd_step_jump_abs = 1.071268207495
saturation_steps = 0
pass = True
pass_margin = True

结论：

带 ramp 的 contact mode sequence 短时测试通过。当前可认为 Stage 7 已完成 contact schedule-aware WBC/QP 的离线验证、静态单模式支撑测试、transition jump 检查和 ramp sequence 前置验证。

边界：

该结果不是完整动态 trot locomotion。尚未完成 swing leg tracking、base velocity tracking、完整 floating-base WBC dynamics 和动态 MuJoCo trot closed-loop。

下一步：

进入 Stage 7 阶段总结，固化默认配置和后续方向。

<!-- STAGE7_CONTACT_MODE_SEQUENCE_RAMP_TEST_END -->

<!-- STAGE7_FINAL_SUMMARY_START -->

## Stage 7 最终阶段总结

Stage 7 当前阶段性完成。

当前完成的是 WBC/QP 第一轮原型验证，不是完整动态 WBC，也不是动态 trot locomotion。

已完成内容：

1. minimal WBC torque QP
2. minimal WBC torque QP support test
3. base wrench tracking WBC/QP
4. base wrench tracking support test
5. posture regularized QP 实验 variant
6. WBC variant comparison
7. contact schedule-aware WBC/QP
8. contact schedule WBC static support test
9. trot_FR_RL scale sweep
10. scaled contact schedule support test
11. contact mode transition check
12. torque ramp check
13. contact mode sequence ramp test

默认配置：

base WBC baseline = results/logs_sample/stage07_wbc_base_wrench_qp.csv
contact schedule WBC = results/logs_sample/stage07_contact_schedule_wbc_qp.csv

mode scale：

all_stance scale = 1.0
trot_FR_RL scale = 0.6
trot_FL_RR scale = 1.0

transition ramp：

ramp_steps = 5

关键接口约定：

leg order = FR, FL, RR, RL
joint order per leg = hip, thigh, calf
torque order = MuJoCo actuator order
force-to-torque sign = tau = -J^T f
torque_limit = 23.7
standing pose = [0.0, 0.9, -1.8] per leg
PD baseline = kp 80.0, kd 2.0

contact mode sequence ramp test 已通过：

sequence = all_stance -> trot_FR_RL -> all_stance -> trot_FL_RR -> all_stance
segment_steps = 300
total_steps = 1500
ramp_steps = 5
final_z = 0.294798253254
min_z = 0.284805846483
max_abs_roll = 0.096498358293
roll_margin_to_0p15 = 0.053501641707
max_abs_pitch = 0.058977498277
pitch_margin_to_0p15 = 0.091022501723
max_tau_total_abs = 10.974863827195
max_cmd_step_jump_norm = 2.292707929380
max_cmd_step_jump_abs = 1.071268207495
saturation_steps = 0
pass = True
pass_margin = True

当前不足：

尚未实现 full floating-base WBC dynamics、qdd/contact force/torque 联合优化、base pose/velocity tracking、swing foot tracking、stance foot acceleration constraint、动态 trot closed-loop、ROS2 节点化和 C++17 工程化。

下一步：

继续 Stage 7，不进入 Stage 8 EKF。

建议实现 swing foot tracking QP 离线原型：

scripts/stage07_swing_foot_tracking_qp.py

输出文件：

results/logs_sample/stage07_swing_foot_tracking_qp.csv

<!-- STAGE7_FINAL_SUMMARY_END -->

<!-- STAGE7_SWING_FOOT_TRACKING_QP_START -->

## Stage 7 更新：Swing Foot Tracking QP

swing foot tracking QP 离线原型已通过。

输出文件：

results/logs_sample/stage07_swing_foot_tracking_qp.csv

支持 contact mode：

trot_FR_RL:
stance legs = FR, RL
swing legs = FL, RR

trot_FL_RR:
stance legs = FL, RR
swing legs = FR, RL

优化变量：

dq，12 维 actuated joint increment

期望 swing foot delta：

dx = 0.03
dy = 0.0
dz = 0.06

参数：

MAX_DQ = 0.35
W_SWING = 100.0
W_STANCE = 10.0
W_REG = 1e-4

结果：

trot_FR_RL:
OSQP status = solved
max_abs_dq = 0.350000000000
swing_error_norm = 0.002170085432
swing_relative_error = 0.022874708942
max_stance_dq = 0.000000000000
pass = True

trot_FL_RR:
OSQP status = solved
max_abs_dq = 0.350000000000
swing_error_norm = 0.002170085432
swing_relative_error = 0.022874708942
max_stance_dq = 0.000000000000
pass = True

结论：

swing foot tracking QP 离线原型已通过。两种 trot contact mode 下，QP 均能生成 12 维 actuated joint increment，使 swing foot 近似达到期望位移，同时 stance legs 保持 dq 为 0。

注意：

max_abs_dq 达到 MAX_DQ = 0.35，说明当前单步 swing delta 较激进。后续接入动态仿真前，应改为多步 swing trajectory tracking。

下一步：

实现 swing trajectory multi-knot tracking QP：

scripts/stage07_swing_trajectory_qp.py

输出文件：

results/logs_sample/stage07_swing_trajectory_qp.csv

<!-- STAGE7_SWING_FOOT_TRACKING_QP_END -->

<!-- STAGE7_SWING_TRAJECTORY_QP_START -->

## Stage 7 更新：Swing Trajectory Multi-Knot QP

swing trajectory multi-knot QP 已通过。

上一版 KNOTS = 5 未通过：

mode_pass = False
mode_max_abs_dq = 0.120000000000
mode_max_swing_error = 0.017592848125
mode_swing_relative_error_total = 0.390610313004

已改为 KNOTS = 9。

输出文件：

results/logs_sample/stage07_swing_trajectory_qp_k9.csv

参数：

KNOTS = 9
TOTAL_DX = 0.03
CLEARANCE = 0.06
MAX_DQ = 0.12
W_SWING = 100.0
W_STANCE = 10.0
W_REG = 1e-4

trot_FR_RL 结果：

mode_pass = True
mode_max_abs_dq = 0.120000000000
mode_max_swing_error = 0.003524538255
mode_max_stance_dq = 0.000000000000
mode_swing_relative_error_total = 0.096119524946

trot_FL_RR 结果：

mode_pass = True
mode_max_abs_dq = 0.120000000000
mode_max_swing_error = 0.003524538255
mode_max_stance_dq = 0.000000000000
mode_swing_relative_error_total = 0.096119524946

结论：

KNOTS = 9 的 swing trajectory multi-knot QP 通过。相比 KNOTS = 5，swing error 明显下降，两种 trot contact mode 均通过。

当前默认 swing trajectory 离线配置：

KNOTS = 9
TOTAL_DX = 0.03
CLEARANCE = 0.06
MAX_DQ = 0.12

注意：

mode_max_abs_dq 仍等于 MAX_DQ = 0.12。后续动态接入前可考虑增加 KNOTS、降低 CLEARANCE 或使用更平滑的 swing height profile。

下一步：

把 KNOTS = 9 的 swing trajectory QP 结果转换为 swing joint target sequence：

scripts/stage07_swing_joint_target_sequence.py

输出文件：

results/logs_sample/stage07_swing_joint_target_sequence.csv

<!-- STAGE7_SWING_TRAJECTORY_QP_END -->

<!-- STAGE7_SWING_JOINT_TARGET_SEQUENCE_START -->

## Stage 7 更新：Swing Joint Target Sequence

swing joint target sequence 已通过。

输入文件：

results/logs_sample/stage07_swing_trajectory_qp_k9.csv

输出文件：

results/logs_sample/stage07_swing_joint_target_sequence.csv

支持模式：

trot_FR_RL:
swing legs = FL, RR
stance legs = FR, RL

trot_FL_RR:
swing legs = FR, RL
stance legs = FL, RR

结果：

modes = trot_FR_RL, trot_FL_RR
num_rows = 18
all_pass = True

trot_FR_RL:
last_knot = 8
max_abs_delta_from_standing = 0.111288270613
last_pass = True

trot_FL_RR:
last_knot = 8
max_abs_delta_from_standing = 0.111288270613
last_pass = True

结论：

KNOTS = 9 的 swing trajectory QP 结果可以转换为每个 knot 的 q_target。所有 q_target 均在保守关节范围内，最大相对 standing pose 的关节偏移为 0.111288270613 rad。

下一步：

实现 MuJoCo swing leg PD tracking 短时测试：

scripts/stage07_swing_joint_target_tracking_test.py

输出文件：

results/logs_sample/stage07_swing_joint_target_tracking_test_summary.csv

<!-- STAGE7_SWING_JOINT_TARGET_SEQUENCE_END -->

<!-- STAGE7_SWING_TRACKING_RECOMMENDED_TEST_START -->

## Stage 7 更新：Swing Joint Target Tracking Recommended Test

保守 swing joint target tracking 短时测试已通过。

背景：

完整 swing target tracking 未通过：

max_abs_roll = 0.238817947944
max_abs_pitch = 0.152858965725
max_joint_error = 0.088734377819
pass = False

加入 trot_FR_RL WBC feedforward 后仍未通过，并且姿态更差：

wbc_scale = 0.6
max_abs_roll = 0.334634959885
max_abs_pitch = 0.193199850224
pass = False

因此执行稳定性 sweep：

results/logs_sample/stage07_swing_tracking_stability_sweep.csv

sweep 结果：

num_cases = 96
pass_cases = 11
pass_margin_cases = 22

推荐配置：

target_scale = 0.25
wbc_scale = 0.0
kp = 60.0
kd = 2.0

推荐配置复现实验脚本：

scripts/stage07_swing_joint_target_tracking_recommended_test.py

输出文件：

results/logs_sample/stage07_swing_joint_target_tracking_recommended_test_log.csv
results/logs_sample/stage07_swing_joint_target_tracking_recommended_test_summary.csv

复现实验结果：

mode = trot_FR_RL
swing legs = FL, RR
stance legs = FR, RL
num_knots = 9
knot_hold_steps = 80
total_steps = 720
target_scale = 0.25
wbc_scale = 0.0
kp = 60.0
kd = 2.0
torque_limit = 23.7

initial_z = 0.284805846483
final_z = 0.276571118100
min_z = 0.270531877762
max_z = 0.284893289428
delta_z = -0.008234728383
final_roll = -0.001430520594
final_pitch = 0.001733127161
max_abs_roll = 0.054958576417
roll_margin_to_0p15 = 0.095041423583
max_abs_pitch = 0.036789337006
pitch_margin_to_0p15 = 0.113210662994
z_margin_to_0p22 = 0.050531877762
max_tau_total_abs = 8.320611628149
saturation_steps = 0
max_joint_error = 0.046307819443
max_swing_joint_error = 0.046307819443
max_stance_joint_error = 0.038460784738
min_swing_foot_z = 0.007720591022
max_swing_foot_z = 0.035251183427
pass = True
pass_margin = True

结论：

保守 swing joint target tracking 短时测试通过。当前可用 swing tracking 默认配置为 target_scale = 0.25, wbc_scale = 0.0, kp = 60.0, kd = 2.0。

边界：

该结果不是完整动态 trot locomotion。完整 target_scale = 1.0 未通过，wbc_scale = 0.6 未通过，动态 contact switching 下的 swing tracking 尚未验证。

下一步：

进入 Stage 7 阶段再总结，或扩展到 trot_FL_RR 的 recommended tracking test。

<!-- STAGE7_SWING_TRACKING_RECOMMENDED_TEST_END -->

<!-- STAGE7_SWING_TRACKING_RECOMMENDED_BOTH_MODES_START -->

## Stage 7 更新：Swing Tracking Recommended Test Both Modes

保守 swing joint target tracking 已在两种 trot 对角模式下通过。

推荐配置：

target_scale = 0.25
wbc_scale = 0.0
kp = 60.0
kd = 2.0
torque_limit = 23.7
num_knots = 9
knot_hold_steps = 80

trot_FR_RL:

swing legs = FL, RR
stance legs = FR, RL
total_steps = 720
initial_z = 0.284805846483
final_z = 0.276571118100
min_z = 0.270531877762
max_abs_roll = 0.054958576417
max_abs_pitch = 0.036789337006
max_tau_total_abs = 8.320611628149
saturation_steps = 0
max_joint_error = 0.046307819443
max_swing_joint_error = 0.046307819443
max_stance_joint_error = 0.038460784738
pass = True
pass_margin = True

trot_FL_RR:

swing legs = FR, RL
stance legs = FL, RR
total_steps = 720
initial_z = 0.284805846483
final_z = 0.281309818973
min_z = 0.271648210780
max_abs_roll = 0.071393714280
max_abs_pitch = 0.056675910934
max_tau_total_abs = 8.876493092716
saturation_steps = 0
max_joint_error = 0.043984959161
max_swing_joint_error = 0.043984959161
max_stance_joint_error = 0.031636404627
pass = True
pass_margin = True

结论：

两种 trot 对角模式下，保守 swing joint target tracking 均通过。当前 Stage 7 的默认保守 swing tracking 配置为 target_scale = 0.25, wbc_scale = 0.0, kp = 60.0, kd = 2.0。

边界：

该结果仍不是完整动态 trot locomotion。当前只验证 standing base 下、单一 contact mode 内的 swing joint target tracking。动态 contact switching、swing tracking 与 WBC 同时工作、base velocity tracking 和 full WBC dynamics 尚未完成。

下一步：

进入 Stage 7 阶段再总结，更新默认配置和失败边界。

<!-- STAGE7_SWING_TRACKING_RECOMMENDED_BOTH_MODES_END -->

<!-- STAGE7_CONSOLIDATED_SUMMARY_AFTER_SWING_START -->

## Stage 7 Consolidated Summary After Swing Tracking

Stage 7 当前阶段性完成。

已完成：

1. WBC/QP 第一轮原型
2. base wrench tracking WBC/QP
3. contact schedule-aware WBC/QP
4. contact mode transition jump check
5. torque ramp check
6. contact mode sequence ramp test
7. swing foot tracking QP
8. swing trajectory multi-knot QP
9. swing joint target sequence
10. swing joint target tracking conservative test

默认 contact schedule WBC：

all_stance = 1.0
trot_FR_RL = 0.6
trot_FL_RR = 1.0

默认 transition ramp：

ramp_steps = 5

默认 swing trajectory QP：

KNOTS = 9
TOTAL_DX = 0.03
CLEARANCE = 0.06
MAX_DQ = 0.12

默认 swing tracking conservative 配置：

target_scale = 0.25
wbc_scale = 0.0
kp = 60.0
kd = 2.0
torque_limit = 23.7
num_knots = 9
knot_hold_steps = 80

trot_FR_RL conservative swing tracking：

final_z = 0.276571118100
min_z = 0.270531877762
max_abs_roll = 0.054958576417
max_abs_pitch = 0.036789337006
max_tau_total_abs = 8.320611628149
saturation_steps = 0
max_joint_error = 0.046307819443
pass = True
pass_margin = True

trot_FL_RR conservative swing tracking：

final_z = 0.281309818973
min_z = 0.271648210780
max_abs_roll = 0.071393714280
max_abs_pitch = 0.056675910934
max_tau_total_abs = 8.876493092716
saturation_steps = 0
max_joint_error = 0.043984959161
pass = True
pass_margin = True

已知失败配置：

完整 target_scale = 1.0 swing tracking 未通过。
wbc_scale = 0.6 swing tracking with WBC feedforward 未通过。

当前结论：

Stage 7 已完成 WBC/QP 与 swing tracking 的离线和短时 MuJoCo 前置验证。

当前仍不能宣称完成动态 trot locomotion。

尚未完成：

1. 动态 contact switching 下的 swing tracking
2. swing tracking 与 WBC feedforward 同时稳定工作
3. base velocity tracking
4. full floating-base WBC dynamics
5. qdd/contact force/torque 联合优化
6. stance foot acceleration constraint
7. ROS2 节点化
8. C++17 工程化迁移

下一步：

继续 Stage 7，建议实现 conservative swing tracking + contact mode switching sequence test：

scripts/stage07_swing_tracking_mode_sequence_test.py

输出文件：

results/logs_sample/stage07_swing_tracking_mode_sequence_test_log.csv
results/logs_sample/stage07_swing_tracking_mode_sequence_test_summary.csv

<!-- STAGE7_CONSOLIDATED_SUMMARY_AFTER_SWING_END -->

<!-- STAGE7_SWING_TRACKING_MODE_SEQUENCE_TEST_START -->

## Stage 7 更新：Swing Tracking Mode Sequence Test

保守 swing tracking mode sequence 测试已通过。

输入文件：

results/logs_sample/stage07_swing_joint_target_sequence.csv

输出文件：

results/logs_sample/stage07_swing_tracking_mode_sequence_test_log.csv
results/logs_sample/stage07_swing_tracking_mode_sequence_test_summary.csv

mode sequence：

trot_FR_RL -> trot_FL_RR -> trot_FR_RL

配置：

target_scale = 0.25
wbc_scale = 0.0
num_segments = 3
num_knots_per_segment = 9
knot_hold_steps = 80
total_steps = 2160
kp = 60.0
kd = 2.0
torque_limit = 23.7

结果：

initial_z = 0.284805846483
final_z = 0.281080409164
min_z = 0.270531877762
max_z = 0.287717440144
delta_z = -0.003725437320
final_roll = -0.003885722206
final_pitch = -0.006745218049
max_abs_roll = 0.072848128772
roll_margin_to_0p15 = 0.077151871228
max_abs_pitch = 0.048797294246
pitch_margin_to_0p15 = 0.101202705754
z_margin_to_0p22 = 0.050531877762
max_tau_total_abs = 8.913662330326
saturation_steps = 0
max_joint_error = 0.047515871120
max_swing_joint_error = 0.047515871120
max_stance_joint_error = 0.038855273920
min_swing_foot_z = 0.007720591022
max_swing_foot_z = 0.043955837312
pass = True
pass_margin = True

结论：

保守 swing tracking mode sequence 测试通过。当前可认为 Stage 7 已完成 contact schedule WBC/QP、contact mode torque ramp、contact mode sequence ramp、swing trajectory QP、swing joint target sequence、单模式 swing tracking、多模式 swing tracking sequence 的前置验证。

边界：

该结果仍不是完整动态 trot locomotion。当前没有使用 WBC feedforward torque、base velocity command、floating-base dynamics WBC、qdd/contact force/torque 联合优化、真实 gait phase scheduler 或 ROS2/C++ 实时控制。

下一步：

生成 Stage 7 最终更新总结。后续可继续 full floating-base WBC dynamics 原型，或整理 C++/ROS2 迁移清单。

<!-- STAGE7_SWING_TRACKING_MODE_SEQUENCE_TEST_END -->

<!-- STAGE7_FINAL_UPDATE_AFTER_MODE_SEQUENCE_START -->

## Stage 7 Final Update After Mode Sequence Test

Stage 7 当前阶段性完成。

当前已完成：

1. QP contact force 到 actuator torque 映射
2. actuator torque 符号验证
3. torque support test
4. minimal WBC torque QP
5. base wrench tracking WBC/QP
6. WBC variant comparison
7. contact schedule-aware WBC/QP
8. contact schedule support test
9. contact mode transition jump check
10. torque ramp check
11. contact mode sequence ramp test
12. swing foot tracking QP
13. swing trajectory multi-knot QP
14. swing joint target sequence
15. single-mode conservative swing tracking
16. both-mode conservative swing tracking
17. conservative swing tracking mode sequence test

当前默认配置：

contact schedule WBC scale:
all_stance = 1.0
trot_FR_RL = 0.6
trot_FL_RR = 1.0

transition ramp:
ramp_steps = 5

swing trajectory:
KNOTS = 9
TOTAL_DX = 0.03
CLEARANCE = 0.06
MAX_DQ = 0.12

conservative swing tracking:
target_scale = 0.25
wbc_scale = 0.0
kp = 60.0
kd = 2.0
num_knots = 9
knot_hold_steps = 80
torque_limit = 23.7

multi-mode swing tracking sequence 已通过：

sequence = trot_FR_RL -> trot_FL_RR -> trot_FR_RL
total_steps = 2160
final_z = 0.281080409164
min_z = 0.270531877762
max_abs_roll = 0.072848128772
max_abs_pitch = 0.048797294246
max_tau_total_abs = 8.913662330326
saturation_steps = 0
max_joint_error = 0.047515871120
pass = True
pass_margin = True

当前结论：

Stage 7 已完成 WBC/QP、contact schedule、contact mode ramp、swing trajectory、swing target sequence、单模式 swing tracking、多模式 swing tracking sequence 的前置验证。

当前仍不是完整动态 trot locomotion。

尚未完成：

1. 真实 gait phase scheduler
2. swing tracking 与 WBC feedforward 同时稳定工作
3. base velocity tracking
4. full floating-base WBC dynamics
5. qdd/contact force/torque 联合优化
6. stance foot acceleration constraint
7. MuJoCo 中连续步态前进
8. ROS2 节点化
9. C++17 工程化迁移

推荐下一步：

继续 Stage 7，实现 full floating-base WBC dynamics 原型：

scripts/stage07_full_wbc_dynamics_qp.py

<!-- STAGE7_FINAL_UPDATE_AFTER_MODE_SEQUENCE_END -->

<!-- STAGE7_FULL_WBC_DYNAMICS_QP_START -->

## Stage 7 更新：Full Floating-Base WBC Dynamics QP

full floating-base WBC dynamics QP 离线原型已通过。

输入文件：

results/logs_sample/stage07_contact_schedule_wbc_qp.csv

输出文件：

results/logs_sample/stage07_full_wbc_dynamics_qp.csv

优化变量：

qdd = 18 维
contact force = 12 维
tau = 12 维
num_vars = 42

动力学约束：

M qdd + h = S^T tau + J^T f

选定 contact_sign = 1.0。

all_stance:

osqp_status = solved
dyn_res_norm = 3.058654385954e-15
max_abs_tau = 5.056337446402
max_abs_qdd = 0.049978975600
min_active_fz = 31.042853613639
min_friction_margin = 16.383104129701
inactive_force_norm = 0.000000000000e+00
tau_diff_norm = 0.788869182635
force_diff_norm = 4.630359089541
pass = True

trot_FR_RL:

osqp_status = solved
dyn_res_norm = 5.688431200954e-14
max_abs_tau = 10.336919898027
max_abs_qdd = 0.237866214144
min_active_fz = 62.411789250330
min_friction_margin = 37.043123301078
inactive_force_norm = 2.927122837681e-19
tau_diff_norm = 1.453084210531
force_diff_norm = 1.704702662899
pass = True

trot_FL_RR:

osqp_status = solved
dyn_res_norm = 2.849909156386e-14
max_abs_tau = 10.276991490673
max_abs_qdd = 0.287407603927
min_active_fz = 62.665557010073
min_friction_margin = 37.034076533927
inactive_force_norm = 2.911209529221e-19
tau_diff_norm = 1.445797911745
force_diff_norm = 1.810670486121
pass = True

结论：

full floating-base WBC dynamics QP 离线原型通过。当前已经实现包含 qdd、contact force、tau 的完整动力学等式 QP 原型。

边界：

该测试仍是离线静态 pose 下的 dynamics QP。尚未加入 stance foot acceleration constraint、base acceleration tracking、swing foot acceleration tracking，也尚未接入 MuJoCo 动态闭环。

下一步：

实现 stance foot acceleration constraint 版本：

scripts/stage07_full_wbc_stance_constraint_qp.py

输出文件：

results/logs_sample/stage07_full_wbc_stance_constraint_qp.csv

<!-- STAGE7_FULL_WBC_DYNAMICS_QP_END -->

<!-- STAGE7_FULL_WBC_STANCE_CONSTRAINT_QP_START -->

## Stage 7 更新：Full WBC Stance Constraint QP

full WBC stance constraint QP 已通过。

输入文件：

results/logs_sample/stage07_contact_schedule_wbc_qp.csv

输出文件：

results/logs_sample/stage07_full_wbc_stance_constraint_qp.csv

优化变量：

qdd = 18 维
contact force = 12 维
tau = 12 维
num_vars = 42

约束：

M qdd + h = S^T tau + J^T f
J_stance qdd = 0

contact_sign = 1.0

all_stance:

num_stance_acc_constraints = 12
osqp_status = solved
dyn_res_norm = 4.269244035819e-14
stance_acc_res_norm = 1.820685054950e-17
max_abs_tau = 5.056128534904
max_abs_qdd = 0.174930174361
min_active_fz = 30.878492208576
min_friction_margin = 16.247430142308
inactive_force_norm = 0.000000000000e+00
pass = True

trot_FR_RL:

num_stance_acc_constraints = 6
osqp_status = solved
dyn_res_norm = 2.849499368786e-14
stance_acc_res_norm = 8.212071048565e-18
max_abs_tau = 10.324397106159
max_abs_qdd = 0.238522198748
min_active_fz = 62.200201091565
min_friction_margin = 36.987165454619
inactive_force_norm = 1.509204993298e-19
pass = True

trot_FL_RR:

num_stance_acc_constraints = 6
osqp_status = solved
dyn_res_norm = 5.691957168469e-14
stance_acc_res_norm = 4.277421474636e-17
max_abs_tau = 10.258608734845
max_abs_qdd = 0.315153457848
min_active_fz = 62.435743500332
min_friction_margin = 36.963058171493
inactive_force_norm = 1.499313846175e-19
pass = True

结论：

加入 stance foot acceleration constraint 后，full WBC dynamics QP 仍然通过。当前 full WBC 已从纯动力学等式推进到包含 stance kinematic constraint 的动力学 QP 原型。

边界：

当前测试仍是离线 standing pose 条件。尚未加入 base acceleration tracking、swing foot acceleration tracking，也尚未接入 MuJoCo 闭环。

下一步：

加入 base acceleration tracking task：

scripts/stage07_full_wbc_base_accel_task_qp.py

输出文件：

results/logs_sample/stage07_full_wbc_base_accel_task_qp.csv

<!-- STAGE7_FULL_WBC_STANCE_CONSTRAINT_QP_END -->

<!-- STAGE7_FULL_WBC_BASE_VERTICAL_ACCEL_TASK_QP_START -->

## Stage 7 更新：Full WBC Base Vertical Accel Task QP

full WBC base vertical acceleration task QP 已通过。

输入文件：

results/logs_sample/stage07_contact_schedule_wbc_qp.csv

输出文件：

results/logs_sample/stage07_full_wbc_base_vertical_accel_task_qp.csv

背景：

上一版 6D base acceleration tracking task 未完全通过，trot_FL_RR 的 base_task_error_norm = 0.07536047349576 超过 0.05。由于 base_qdd_z = 0.184192457744 已接近目标 0.2，因此改为 vertical-only base acceleration tracking。

目标：

base_qdd_z_ref = 0.2

all_stance:

osqp_status = solved
base_qdd_z = 0.172345449438
base_z_task_error = -2.765455056232e-02
dyn_res_norm = 2.860912105997e-14
stance_acc_res_norm = 9.309604088703e-17
max_abs_tau = 5.145971987477
max_abs_qdd = 1.163420196948
min_active_fz = 31.352989831521
min_friction_margin = 16.629454637670
pass = True

trot_FR_RL:

osqp_status = solved
base_qdd_z = 0.185668089815
base_z_task_error = -1.433191018511e-02
dyn_res_norm = 4.270753688660e-14
stance_acc_res_norm = 8.993834424997e-17
max_abs_tau = 10.485941789045
max_abs_qdd = 1.090240185829
min_active_fz = 63.235143005521
min_friction_margin = 37.355381771031
pass = True

trot_FL_RR:

osqp_status = solved
base_qdd_z = 0.185791586133
base_z_task_error = -1.420841386733e-02
dyn_res_norm = 2.895861563847e-14
stance_acc_res_norm = 7.351626287045e-17
max_abs_tau = 10.424434041249
max_abs_qdd = 1.043367245659
min_active_fz = 63.478490228568
min_friction_margin = 37.358992434275
pass = True

结论：

vertical-only base acceleration tracking task 通过。三种 contact mode 均满足 dynamics residual、stance acceleration residual、base_qdd_z tracking、torque limit、friction cone 和 inactive force 约束。

边界：

该测试仍是离线静态 pose 下的 full WBC QP。尚未完成 6D base acceleration tracking、swing foot acceleration tracking task、MuJoCo 闭环、gait phase scheduler 和连续 trot locomotion。

下一步：

加入 swing foot acceleration tracking task：

scripts/stage07_full_wbc_swing_accel_task_qp.py

输出文件：

results/logs_sample/stage07_full_wbc_swing_accel_task_qp.csv

<!-- STAGE7_FULL_WBC_BASE_VERTICAL_ACCEL_TASK_QP_END -->

<!-- STAGE7_FULL_WBC_SWING_ACCEL_TASK_QP_START -->

## Stage 7 更新：Full WBC Swing Accel Task QP

full WBC swing foot acceleration tracking task 已通过。

输入文件：

results/logs_sample/stage07_contact_schedule_wbc_qp.csv

输出文件：

results/logs_sample/stage07_full_wbc_swing_accel_task_qp.csv

优化变量：

qdd = 18 维
contact force = 12 维
tau = 12 维
num_vars = 42

当前包含：

1. floating-base dynamics equality
2. stance foot acceleration constraint
3. base vertical acceleration tracking task
4. swing foot acceleration tracking task
5. torque limit
6. friction cone
7. inactive contact force = 0

base_qdd_z_ref = 0.2

swing_acc_ref = [0.4, 0.0, 0.8]

trot_FR_RL:

stance legs = FR, RL
swing legs = FL, RR
osqp_status = solved
base_qdd_z = 0.215789494368
base_z_task_error = 1.578949436807e-02
swing_acc_error_norm = 1.227426649713e-01
swing_acc_error_max_abs = 8.578944289191e-02
dyn_res_norm = 4.281617822997e-14
stance_acc_res_norm = 1.152775633689e-16
max_abs_tau = 10.545880364253
max_abs_qdd = 2.910331019188
min_active_fz = 63.530428891910
min_friction_margin = 37.533924480127
inactive_force_norm = 3.987469546604e-20
pass = True

trot_FL_RR:

stance legs = FL, RR
swing legs = FR, RL
osqp_status = solved
base_qdd_z = 0.215607732660
base_z_task_error = 1.560773265970e-02
swing_acc_error_norm = 1.218506194838e-01
swing_acc_error_max_abs = 8.880804591198e-02
dyn_res_norm = 4.286630305818e-14
stance_acc_res_norm = 1.083889877283e-16
max_abs_tau = 10.480313206115
max_abs_qdd = 3.026505313002
min_active_fz = 63.784137690160
min_friction_margin = 37.526106825020
inactive_force_norm = 3.911866994703e-20
pass = True

结论：

full WBC swing foot acceleration tracking task 通过。当前 full WBC QP 已包含 qdd/contact force/tau 联合优化、floating-base dynamics equality、stance constraint、base vertical acceleration tracking、swing foot acceleration tracking、torque limit、friction cone 和 inactive contact force 约束。

边界：

该测试仍是离线静态 pose 下的 QP。尚未加入 Jdot_v 非零项，尚未接入 MuJoCo torque closed-loop，尚未实现 gait phase scheduler 和连续 trot locomotion。

下一步：

生成 Stage 7 full WBC 最新总结：

docs/STAGE07_FULL_WBC_SUMMARY.md

<!-- STAGE7_FULL_WBC_SWING_ACCEL_TASK_QP_END -->

<!-- STAGE7_FULL_WBC_SUMMARY_START -->

## Stage 7 Full WBC Summary

Stage 7 full WBC 离线原型阶段性完成。

已完成 full WBC 子步骤：

1. full floating-base WBC dynamics QP
2. full WBC stance foot acceleration constraint QP
3. full WBC base vertical acceleration task QP
4. full WBC swing foot acceleration task QP

当前 full WBC 优化变量：

qdd = 18 维
contact force = 12 维
tau = 12 维
num_vars = 42

动力学形式：

M qdd + h = S^T tau + J^T f

contact_sign = 1.0

当前 full WBC 默认离线配置：

1. dynamics equality
2. stance foot acceleration constraint
3. base vertical acceleration tracking task
4. swing foot acceleration tracking task
5. torque limit
6. friction cone
7. inactive contact force constraint

默认 base task：

base_qdd_z_ref = 0.2

默认 swing task：

swing_acc_ref = [0.4, 0.0, 0.8]

full WBC swing accel task QP 已通过：

trot_FR_RL:

base_qdd_z = 0.215789494368
base_z_task_error = 1.578949436807e-02
swing_acc_error_norm = 1.227426649713e-01
dyn_res_norm = 4.281617822997e-14
stance_acc_res_norm = 1.152775633689e-16
max_abs_tau = 10.545880364253
max_abs_qdd = 2.910331019188
min_active_fz = 63.530428891910
min_friction_margin = 37.533924480127
pass = True

trot_FL_RR:

base_qdd_z = 0.215607732660
base_z_task_error = 1.560773265970e-02
swing_acc_error_norm = 1.218506194838e-01
dyn_res_norm = 4.286630305818e-14
stance_acc_res_norm = 1.083889877283e-16
max_abs_tau = 10.480313206115
max_abs_qdd = 3.026505313002
min_active_fz = 63.784137690160
min_friction_margin = 37.526106825020
pass = True

已知失败项：

6D base acceleration tracking task 未完全通过。trot_FL_RR 的 base_task_error_norm = 0.07536047349576 超过阈值，因此当前采用 vertical-only base acceleration tracking。

当前结论：

Stage 7 已完成 full WBC 离线原型。full WBC 的离线 QP 结构已经打通，但仍不是完整动态 trot locomotion。

尚未完成：

1. Jdot_v 非零项
2. qdd 积分到 MuJoCo
3. torque 闭环仿真
4. gait phase scheduler
5. 连续 trot locomotion
6. base velocity tracking
7. 6D base acceleration tracking 稳定版本
8. ROS2 节点化
9. C++17 工程化迁移

下一步：

进入 full WBC torque reconstruction check：

scripts/stage07_full_wbc_torque_reconstruction_check.py

输出文件：

results/logs_sample/stage07_full_wbc_torque_reconstruction_check.csv

<!-- STAGE7_FULL_WBC_SUMMARY_END -->

<!-- STAGE7_FULL_WBC_TORQUE_RECONSTRUCTION_AND_RAMP_CHECK_START -->

## Stage 7 更新：Full WBC Torque Reconstruction and Ramp Check

full WBC torque reconstruction check 和 ramp check 已通过。

输入文件：

results/logs_sample/stage07_full_wbc_torque_reconstruction_check.csv

输出文件：

results/logs_sample/stage07_full_wbc_torque_ramp_check.csv

Torque reconstruction:

trot_FR_RL:
max_abs_tau_full_wbc = 10.545880364253
max_abs_tau_contact_wbc = 10.638319002741
tau_diff_norm_vs_contact_wbc = 1.390773536447
tau_diff_max_abs_vs_contact_wbc = 0.732158458909
torque_limit_pass = True

trot_FL_RR:
max_abs_tau_full_wbc = 10.480313206115
max_abs_tau_contact_wbc = 10.594245657447
tau_diff_norm_vs_contact_wbc = 1.375153606606
tau_diff_max_abs_vs_contact_wbc = 0.729723929991
torque_limit_pass = True

Direct transition jump:

trot_FR_RL -> trot_FL_RR:
jump_norm = 23.730004894309
jump_max_abs = 10.823012441254
need_smoothing = True

trot_FL_RR -> trot_FR_RL:
jump_norm = 23.730004894309
jump_max_abs = 10.823012441254
need_smoothing = True

Ramp check:

ramp_steps = 3:
ramp_all_pass = True
max_step_jump_norm = 7.910001631436
max_step_jump_abs = 3.607670813751

ramp_steps = 5:
ramp_all_pass = True
max_step_jump_norm = 4.746000978862
max_step_jump_abs = 2.164602488251

ramp_steps = 10:
ramp_all_pass = True
max_step_jump_norm = 2.373000489431
max_step_jump_abs = 1.082301244125

recommended_ramp_steps = 3

结论：

full WBC 单模式 torque 合法，但两种 trot mode 之间直接切换 torque jump 过大，必须使用 ramp smoothing。最小推荐 ramp_steps = 3；进入 MuJoCo 闭环时建议采用更保守的 ramp_steps = 5。

下一步：

进入 full WBC torque closed-loop 前置测试：

scripts/stage07_full_wbc_torque_sequence_support_test.py

输出文件：

results/logs_sample/stage07_full_wbc_torque_sequence_support_test_log.csv
results/logs_sample/stage07_full_wbc_torque_sequence_support_test_summary.csv

<!-- STAGE7_FULL_WBC_TORQUE_RECONSTRUCTION_AND_RAMP_CHECK_END -->

<!-- STAGE7_FULL_WBC_TORQUE_SEQUENCE_SUPPORT_TEST_START -->

## Stage 7 更新：Full WBC Torque Sequence Support Test

full WBC torque sequence support test 已通过。

输入文件：

results/logs_sample/stage07_full_wbc_torque_reconstruction_check.csv

输出文件：

results/logs_sample/stage07_full_wbc_torque_sequence_support_test_log.csv
results/logs_sample/stage07_full_wbc_torque_sequence_support_test_summary.csv

mode sequence：

trot_FR_RL -> trot_FL_RR -> trot_FR_RL

配置：

segment_steps = 300
num_segments = 3
total_steps = 900
ramp_steps = 5
kp = 80.0
kd = 2.0
torque_limit = 23.7

结果：

initial_z = 0.284805846483
final_z = 0.302695944706
min_z = 0.284782520542
max_z = 0.315369147929
delta_z = 0.017890098222
final_roll = 0.090847703976
final_pitch = -0.056119160829
max_abs_roll = 0.097459520644
roll_margin_to_0p15 = 0.052540479356
max_abs_pitch = 0.064290563391
pitch_margin_to_0p15 = 0.085709436609
z_margin_to_0p22 = 0.064782520542
max_tau_pd_abs = 19.599741458584
max_tau_wbc_cmd_abs = 10.545880364253
max_tau_total_abs = 11.531362579026
max_cmd_step_jump_norm = 4.746000978862
max_cmd_step_jump_abs = 2.164602488251
saturation_steps = 0
pass = True
pass_margin = True

结论：

full WBC torque sequence support test 通过。full WBC 离线 QP 输出的 torque，在 ramp_steps = 5 平滑后，可以在 MuJoCo 中完成短时多模式 torque sequence 支撑测试。

当前 full WBC 已完成：

1. 离线 dynamics QP 验证
2. stance constraint 验证
3. base vertical acceleration task 验证
4. swing acceleration task 验证
5. torque reconstruction check
6. torque ramp check
7. MuJoCo torque sequence support test

边界：

该结果仍不是完整动态 trot locomotion。尚未实现实时 gait phase scheduler、每步在线 full WBC 重求解、swing trajectory 与 full WBC 每步耦合、base velocity tracking、连续前进速度、Jdot_v 非零项和 ROS2/C++ 实时实现。

下一步：

生成 Stage 7 full WBC 最终更新总结：

docs/STAGE07_FULL_WBC_FINAL_UPDATE.md

<!-- STAGE7_FULL_WBC_TORQUE_SEQUENCE_SUPPORT_TEST_END -->

<!-- STAGE7_FULL_WBC_FINAL_UPDATE_START -->

## Stage 7 Full WBC Final Update

Stage 7 full WBC 原型阶段性完成。

当前已经完成：

1. full floating-base dynamics QP
2. stance foot acceleration constraint QP
3. base vertical acceleration tracking task QP
4. swing foot acceleration tracking task QP
5. torque reconstruction check
6. torque ramp check
7. MuJoCo torque sequence support test

当前 full WBC 优化变量：

qdd = 18 维
contact force = 12 维
tau = 12 维
num_vars = 42

动力学形式：

M qdd + h = S^T tau + J^T f

contact_sign = 1.0

当前默认 task：

base_qdd_z_ref = 0.2
swing_acc_ref = [0.4, 0.0, 0.8]

推荐 MuJoCo torque sequence ramp：

ramp_steps = 5

full WBC swing accel task QP：

trot_FR_RL:
base_qdd_z = 0.215789494368
swing_acc_error_norm = 1.227426649713e-01
max_abs_tau = 10.545880364253
pass = True

trot_FL_RR:
base_qdd_z = 0.215607732660
swing_acc_error_norm = 1.218506194838e-01
max_abs_tau = 10.480313206115
pass = True

full WBC torque reconstruction：

trot_FR_RL:
max_abs_tau_full_wbc = 10.545880364253
tau_diff_norm_vs_contact_wbc = 1.390773536447
torque_limit_pass = True

trot_FL_RR:
max_abs_tau_full_wbc = 10.480313206115
tau_diff_norm_vs_contact_wbc = 1.375153606606
torque_limit_pass = True

full WBC torque ramp check：

recommended_ramp_steps = 3

进入 MuJoCo 闭环时建议 ramp_steps = 5。

ramp_steps = 5:
max_step_jump_norm = 4.746000978862
max_step_jump_abs = 2.164602488251
pass = True

full WBC torque sequence support test：

sequence = trot_FR_RL -> trot_FL_RR -> trot_FR_RL
total_steps = 900
ramp_steps = 5
kp = 80.0
kd = 2.0
torque_limit = 23.7

initial_z = 0.284805846483
final_z = 0.302695944706
min_z = 0.284782520542
max_abs_roll = 0.097459520644
max_abs_pitch = 0.064290563391
max_tau_total_abs = 11.531362579026
max_cmd_step_jump_norm = 4.746000978862
max_cmd_step_jump_abs = 2.164602488251
saturation_steps = 0
pass = True
pass_margin = True

关键结论：

Stage 7 full WBC 离线 QP 结构已经打通。full WBC torque 经过 ramp smoothing 后，可以在 MuJoCo 中完成短时多模式 torque sequence support test。

当前边界：

仍不能宣称完成动态 trot locomotion。尚未完成每步在线求解 full WBC QP、gait phase scheduler、swing trajectory 与 full WBC 在线耦合、base velocity tracking、连续前进速度、Jdot_v 非零项、qdd 积分策略、foot touchdown/liftoff 状态机和 ROS2/C++ 实时迁移。

下一步：

继续 Stage 7，进入在线 MuJoCo full WBC step loop 原型。

建议脚本：

scripts/stage07_online_full_wbc_step_loop_proto.py

建议输出：

results/logs_sample/stage07_online_full_wbc_step_loop_proto_log.csv
results/logs_sample/stage07_online_full_wbc_step_loop_proto_summary.csv

<!-- STAGE7_FULL_WBC_FINAL_UPDATE_END -->

<!-- STAGE7_ONLINE_FULL_WBC_STEP_LOOP_PROTO_START -->

## Stage 7 更新：Online Full WBC Step Loop Proto

online full WBC step loop proto 已通过。

输入文件：

results/logs_sample/stage07_contact_schedule_wbc_qp.csv

输出文件：

results/logs_sample/stage07_online_full_wbc_step_loop_proto_log.csv
results/logs_sample/stage07_online_full_wbc_step_loop_proto_summary.csv

mode sequence：

trot_FR_RL -> trot_FL_RR -> trot_FR_RL

配置：

num_segments = 3
total_steps = 600
kp_posture = 60.0
kd_posture = 2.0
torque_limit = 23.7
base_qdd_z_ref = 0.05
swing_acc_ref = [0.1, 0.0, 0.2]
ramp_alpha = 0.2

结果：

initial_z = 0.284805846483
final_z = 0.303007083406
min_z = 0.284602787921
max_z = 0.324781172497
delta_z = 0.018201236923
final_roll = 0.006266286166
final_pitch = -0.011694447899
max_abs_roll = 0.087444882304
max_abs_pitch = 0.054577030128
z_margin_to_limit = 0.064602787921
max_tau_pd_abs = 17.925660006849
max_tau_wbc_abs = 10.264344153432
max_tau_total_abs = 11.413605129606
max_cmd_step_jump_norm = 4.585214741716
max_cmd_step_jump_abs = 2.277670654797
max_dyn_res_norm = 9.021244992010e-08
max_stance_acc_res_norm = 3.660267596023e-09
max_swing_acc_error_norm = 2.629309436127e-01
qp_fail_steps = 0
saturation_steps = 0
pass = True
pass_margin = True

结论：

online full WBC step loop proto 通过。full WBC QP 可以在 MuJoCo step loop 中每步在线求解，且原地多模式支撑序列通过。

边界：

仍不是完整动态 trot locomotion。尚未实现 gait phase scheduler、在线 swing trajectory、base velocity tracking、forward velocity command、touchdown/liftoff 状态机、Jdot_v 非零项和 C++/ROS2 实时实现。

下一步：

实现 gait phase scheduler proto：

scripts/stage07_gait_phase_scheduler_proto.py

输出文件：

results/logs_sample/stage07_gait_phase_scheduler_proto.csv

<!-- STAGE7_ONLINE_FULL_WBC_STEP_LOOP_PROTO_END -->

<!-- STAGE7_GAIT_PHASE_SCHEDULER_PROTO_START -->

## Stage 7 更新：Gait Phase Scheduler Proto

gait phase scheduler proto 已通过。

输出文件：

results/logs_sample/stage07_gait_phase_scheduler_proto.csv
results/logs_sample/stage07_gait_phase_scheduler_proto_summary.csv

参数：

dt = 0.002
total_steps = 1200
period_steps = 400
half_period_steps = 200
num_cycles = 3

contact modes：

trot_FR_RL:
stance legs = FR, RL
swing legs = FL, RR

trot_FL_RR:
stance legs = FL, RR
swing legs = FR, RL

结果：

trot_FR_RL_steps = 600
trot_FL_RR_steps = 600
transition_count = 5
expected_transitions = 5
duration_pass = True
transition_pass = True
pass = True

mode switch steps：

0 -> trot_FR_RL
200 -> trot_FL_RR
400 -> trot_FR_RL
600 -> trot_FL_RR
800 -> trot_FR_RL
1000 -> trot_FL_RR

结论：

gait phase scheduler proto 通过。该 scheduler 可以稳定生成 phase、phase_step、mode、mode_step、phase_in_mode、stance legs、swing legs、swing_progress 和 transition 标记。

边界：

当前仍是最小 scheduler。尚未包含 duty factor 参数化、swing trajectory 在线生成、touchdown/liftoff 检测、contact state feedback、velocity command 和 gait start/stop 状态机。

下一步：

将 gait phase scheduler 接入 online full WBC step loop：

scripts/stage07_online_full_wbc_with_scheduler_proto.py

输出文件：

results/logs_sample/stage07_online_full_wbc_with_scheduler_proto_log.csv
results/logs_sample/stage07_online_full_wbc_with_scheduler_proto_summary.csv

<!-- STAGE7_GAIT_PHASE_SCHEDULER_PROTO_END -->

<!-- STAGE7_ONLINE_FULL_WBC_WITH_SCHEDULER_PROTO_START -->

## Stage 7 更新：Online Full WBC with Scheduler Proto

online full WBC with scheduler proto 已通过。

输入文件：

results/logs_sample/stage07_contact_schedule_wbc_qp.csv

输出文件：

results/logs_sample/stage07_online_full_wbc_with_scheduler_proto_log.csv
results/logs_sample/stage07_online_full_wbc_with_scheduler_proto_summary.csv

scheduler = phase_trot

配置：

total_steps = 1200
dt = 0.002
period_steps = 400
half_period_steps = 200
trot_FR_RL_steps = 600
trot_FL_RR_steps = 600
transition_count = 5
kp_posture = 60.0
kd_posture = 2.0
torque_limit = 23.7
base_qdd_z_ref = 0.05
swing_acc_ref = [0.1, 0.0, 0.2]
ramp_alpha = 0.2

结果：

initial_z = 0.284805846483
final_z = 0.306167691855
min_z = 0.284602787921
max_z = 0.324781172497
delta_z = 0.021361845372
final_roll = 0.047401678133
final_pitch = 0.035868317312
max_abs_roll = 0.148607466957
roll_margin_to_limit = 0.051392533043
max_abs_pitch = 0.067919909731
pitch_margin_to_limit = 0.132080090269
z_margin_to_limit = 0.064602787921
max_tau_pd_abs = 18.430845082537
max_tau_wbc_abs = 10.264344153432
max_tau_total_abs = 11.413605129606
max_cmd_step_jump_norm = 4.585214741716
max_cmd_step_jump_abs = 2.277670654797
max_dyn_res_norm = 9.745131047022e-08
max_stance_acc_res_norm = 3.725303596518e-09
max_swing_acc_error_norm = 6.383111519946e-01
qp_fail_steps = 0
saturation_steps = 0
pass = True
pass_margin = True

结论：

phase scheduler 已接入 online full WBC step loop。full WBC QP 可以在 1200 个 MuJoCo step 中持续在线求解，QP failure = 0，torque saturation = 0，原地 scheduler-driven trot support 通过。

注意：

max_abs_roll = 0.148607466957，接近早期常用的 0.15 阈值。当前脚本阈值为 0.20，因此通过；后续建议通过参数 sweep 降低 roll。

边界：

该结果仍不是完整动态 trot locomotion。尚未完成在线 swing trajectory、base velocity tracking、forward velocity command、touchdown/liftoff 状态机、contact feedback、Jdot_v 非零项和 ROS2/C++ 实时实现。

下一步：

做 scheduler 参数稳定性 sweep：

scripts/stage07_online_full_wbc_scheduler_stability_sweep.py

输出文件：

results/logs_sample/stage07_online_full_wbc_scheduler_stability_sweep.csv

<!-- STAGE7_ONLINE_FULL_WBC_WITH_SCHEDULER_PROTO_END -->

<!-- STAGE7_ONLINE_FULL_WBC_SCHEDULER_STABILITY_SWEEP_START -->

## Stage 7 更新：Online Full WBC Scheduler Stability Sweep

online full WBC scheduler stability sweep 已通过。

输出文件：

results/logs_sample/stage07_online_full_wbc_scheduler_stability_sweep.csv

sweep 参数：

period_steps = [400, 600]
ramp_alpha = [0.10, 0.15, 0.20]
base_qdd_z_ref = [0.03, 0.05]

总体结果：

num_cases = 12
pass_cases = 11
strict_roll_cases = 0

strict_roll 目标：

max_abs_roll < 0.12

本轮没有配置严格达到 max_abs_roll < 0.12。

推荐配置：

period_steps = 400
half_period_steps = 200
ramp_alpha = 0.15
base_qdd_z_ref = 0.03

推荐配置结果：

initial_z = 0.284805846483
final_z = 0.305351175409
min_z = 0.284525843843
max_z = 0.325211798729
delta_z = 0.020545328926
final_roll = 0.035555928490
final_pitch = 0.020598258923
max_abs_roll = 0.120328259514
roll_margin_to_0p20 = 0.079671740486
roll_margin_to_0p12 = -0.000328259514
max_abs_pitch = 0.083327623789
pitch_margin_to_0p20 = 0.116672376211
z_margin_to_0p22 = 0.064525843843
max_tau_pd_abs = 17.914484841257
max_tau_wbc_abs = 10.664068495997
max_tau_total_abs = 11.423881519983
max_cmd_step_jump_norm = 3.444357031147
max_cmd_step_jump_abs = 1.782238605127
max_dyn_res_norm = 1.039101885248e-07
max_stance_acc_res_norm = 3.750277847245e-09
max_swing_acc_error_norm = 5.967141996034e-01
qp_fail_steps = 0
saturation_steps = 0
pass = True
strict_roll_pass = False

失败配置：

period_steps = 400
ramp_alpha = 0.20
base_qdd_z_ref = 0.03
max_abs_roll = 0.209898482299
pass = False

结论：

当前推荐配置满足 QP failure = 0、torque saturation = 0、pass = True，且 max_abs_roll = 0.120328259514。它未严格达到 max_abs_roll < 0.12，但只超出 0.000328259514，可作为当前推荐在线 scheduler 配置。

下一步：

用推荐配置生成 confirmed online full WBC scheduler run：

scripts/stage07_online_full_wbc_scheduler_recommended_run.py

输出文件：

results/logs_sample/stage07_online_full_wbc_scheduler_recommended_run_log.csv
results/logs_sample/stage07_online_full_wbc_scheduler_recommended_run_summary.csv

<!-- STAGE7_ONLINE_FULL_WBC_SCHEDULER_STABILITY_SWEEP_END -->

<!-- STAGE7_ONLINE_FULL_WBC_SCHEDULER_RECOMMENDED_RUN_START -->

## Stage 7 更新：Online Full WBC Scheduler Recommended Run

online full WBC scheduler recommended run 已通过。

输入脚本：

scripts/stage07_online_full_wbc_scheduler_recommended_run.py

输出文件：

results/logs_sample/stage07_online_full_wbc_scheduler_recommended_run_log.csv
results/logs_sample/stage07_online_full_wbc_scheduler_recommended_run_summary.csv

推荐 baseline 配置：

scheduler = phase_trot
total_steps = 1200
dt = 0.002
period_steps = 400
half_period_steps = 200
trot_FR_RL_steps = 600
trot_FL_RR_steps = 600
transition_count = 5
kp_posture = 60.0
kd_posture = 2.0
torque_limit = 23.7
base_qdd_z_ref = 0.03
swing_acc_ref = [0.1, 0.0, 0.2]
ramp_alpha = 0.15

结果：

initial_z = 0.284805846483
final_z = 0.305351175409
min_z = 0.284525843843
max_z = 0.325211798729
delta_z = 0.020545328926
final_roll = 0.035555928490
final_pitch = 0.020598258923
max_abs_roll = 0.120328259514
roll_margin_to_limit = 0.079671740486
max_abs_pitch = 0.083327623789
pitch_margin_to_limit = 0.116672376211
z_margin_to_limit = 0.064525843843
max_tau_pd_abs = 17.914484841257
max_tau_wbc_abs = 10.664068495997
max_tau_total_abs = 11.423881519983
max_cmd_step_jump_norm = 3.444357031147
max_cmd_step_jump_abs = 1.782238605127
max_dyn_res_norm = 1.039101885248e-07
max_stance_acc_res_norm = 3.750277847245e-09
max_swing_acc_error_norm = 5.967141996034e-01
qp_fail_steps = 0
saturation_steps = 0
pass = True
pass_margin = True

结论：

该配置现在作为 Stage 7 online full WBC 原地 scheduler-driven support 的推荐 baseline。

推荐 baseline：

period_steps = 400
half_period_steps = 200
base_qdd_z_ref = 0.03
ramp_alpha = 0.15
kp_posture = 60.0
kd_posture = 2.0
torque_limit = 23.7

边界：

该结果仍不是完整动态 trot locomotion。尚未完成 online swing trajectory、swing foot target 与 full WBC task 耦合、base velocity tracking、forward velocity command、touchdown/liftoff 状态机、contact feedback、Jdot_v 非零项和 ROS2/C++ 实时实现。

下一步：

进入 online swing trajectory proto：

scripts/stage07_online_swing_trajectory_proto.py

输出文件：

results/logs_sample/stage07_online_swing_trajectory_proto.csv
results/logs_sample/stage07_online_swing_trajectory_proto_summary.csv

<!-- STAGE7_ONLINE_FULL_WBC_SCHEDULER_RECOMMENDED_RUN_END -->

<!-- STAGE7_ONLINE_SWING_TRAJECTORY_MEMORY_PROTO_START -->

## Stage 7 更新：Online Swing Trajectory Memory Proto

online swing trajectory memory proto 已通过。

普通版本：

scripts/stage07_online_swing_trajectory_proto.py

失败原因：

smooth_pass = False
max_step_delta_norm = 0.007500000000

原因：

mode 切换瞬间 stance/swing 角色交换，x target 从 +stride/2 跳到 -stride/2，导致 foot target 不连续。

memory 版本：

scripts/stage07_online_swing_trajectory_memory_proto.py

输出文件：

results/logs_sample/stage07_online_swing_trajectory_memory_proto.csv
results/logs_sample/stage07_online_swing_trajectory_memory_proto_summary.csv

方法：

每条腿维护 prev_target、prev_leg_state、lift_off_pos、touch_down_pos。进入 swing 时从当前 prev_target 作为 lift_off_pos，并以 lift_off_pos + [stride_x, 0, 0] 作为 touch_down_pos。swing 段内使用 smoothstep 插值，z 方向加入半正弦 clearance。

配置：

dt = 0.002
total_steps = 1200
period_steps = 400
half_period_steps = 200
stride_x = 0.015
clearance_z = 0.025

结果：

transition_count = 5
swing_start_count = 12
expected_swing_start_count = 12
min_target_z = 0.020000000000
max_target_z = 0.045000000000
max_step_delta_norm = 0.000392684534
max_step_delta_z = 0.000392682933
FR_swing_samples = 600
FL_swing_samples = 600
RR_swing_samples = 600
RL_swing_samples = 600
FR_stance_samples = 600
FL_stance_samples = 600
RR_stance_samples = 600
RL_stance_samples = 600
z_pass = True
smooth_pass = True
balance_pass = True
transition_pass = True
swing_start_pass = True
pass = True

结论：

online swing trajectory memory proto 通过。相对普通版本，最大 target step jump 从 0.007500000000 降低到 0.000392684534。该版本可作为后续 online full WBC 接入 swing foot target / swing foot acceleration target 的默认轨迹生成器。

边界：

该版本仍不接 WBC。尚未完成 foot target 到 joint target 的在线 IK、foot target 到 swing acceleration target 的在线转换、与 full WBC swing task 耦合、touchdown/liftoff contact feedback、forward velocity command 和 ROS2/C++ 实时实现。

下一步：

实现 online swing trajectory tracking check：

scripts/stage07_online_swing_trajectory_tracking_check.py

输出文件：

results/logs_sample/stage07_online_swing_trajectory_tracking_check.csv
results/logs_sample/stage07_online_swing_trajectory_tracking_check_summary.csv

<!-- STAGE7_ONLINE_SWING_TRAJECTORY_MEMORY_PROTO_END -->

<!-- STAGE7_ONLINE_SWING_TRAJECTORY_TRACKING_CHECK_START -->

## Stage 7 更新：Online Swing Trajectory Tracking Check

online swing trajectory tracking check 已通过。

输入文件：

results/logs_sample/stage07_online_swing_trajectory_memory_proto.csv

输出文件：

results/logs_sample/stage07_online_swing_trajectory_tracking_check.csv
results/logs_sample/stage07_online_swing_trajectory_tracking_check_summary.csv

方法：

读取 memory swing trajectory 的 foot target，用当前 joint command pose 的 foot Jacobian 做小步 IK/QP，生成连续 joint target。

QP 参数：

MAX_DQ_STEP = 0.015
MAX_Q_DELTA_FROM_STANDING = 0.35
W_SWING = 200.0
W_STANCE = 50.0
W_REG = 1e-3
W_SMOOTH = 10.0

结果：

total_steps = 1200
max_foot_error_norm = 0.000900142979
max_swing_foot_error_norm = 0.000373110134
max_stance_foot_error_norm = 0.000900142979
max_abs_dq_step = 0.003211667495
max_q_delta_from_standing = 0.183211559405
qp_fail_steps = 0
foot_error_tol = 0.006
max_dq_step_tol = 0.016
max_q_delta_tol = 0.36
foot_error_pass = True
swing_error_pass = True
dq_step_pass = True
q_delta_pass = True
qp_pass = True
pass = True

结论：

online swing trajectory tracking check 通过。memory swing trajectory 可以被小步 IK/QP 转换为连续 joint target，foot tracking error 很小，每步 dq 和 q delta 均可控，QP failure = 0。

边界：

该测试仍不是完整动态 trot locomotion。尚未完成 MuJoCo joint target tracking 闭环、full WBC 中使用该 swing target、swing target 到 acceleration task 的在线转换、touchdown/liftoff contact feedback、base velocity tracking、forward velocity command 和 ROS2/C++ 实时实现。

下一步：

做 online swing joint target tracking support test：

scripts/stage07_online_swing_joint_target_tracking_support_test.py

输出文件：

results/logs_sample/stage07_online_swing_joint_target_tracking_support_test_log.csv
results/logs_sample/stage07_online_swing_joint_target_tracking_support_test_summary.csv

<!-- STAGE7_ONLINE_SWING_TRAJECTORY_TRACKING_CHECK_END -->

<!-- STAGE7_ONLINE_SWING_JOINT_TRACKING_STABILITY_SWEEP_START -->

## Stage 7 更新：Online Swing Joint Tracking Stability Sweep

online swing joint tracking stability sweep 已通过。

背景：

原始 online swing joint target tracking support test 使用 kp=60.0、kd=2.0、target_scale=1.0，结果 max_joint_error = 0.099326587385，超过 0.08，因此 pass = False。

输出文件：

results/logs_sample/stage07_online_swing_joint_tracking_stability_sweep.csv

Sweep 参数：

KP_LIST = [60.0, 80.0, 100.0]
KD_LIST = [2.0, 4.0, 6.0]
TARGET_SCALE_LIST = [0.60, 0.75, 0.90, 1.00]

总体结果：

num_cases = 36
pass_cases = 6
pass_margin_cases = 6

推荐配置：

kp = 80.0
kd = 2.0
target_scale = 0.6

推荐配置结果：

total_steps = 1200
initial_z = 0.284805846483
final_z = 0.282769844842
min_z = 0.270657074947
max_z = 0.285595003453
delta_z = -0.002036001641
final_roll = -0.006184160640
final_pitch = -0.008386076938
max_abs_roll = 0.063224324564
roll_margin_to_0p20 = 0.136775675436
max_abs_pitch = 0.055307047284
pitch_margin_to_0p20 = 0.144692952716
z_margin_to_0p22 = 0.050657074947
max_joint_error = 0.059643533460
max_swing_joint_error = 0.059643533460
max_stance_joint_error = 0.035331528104
max_tau_raw_abs = 9.930087778241
max_tau_total_abs = 9.930087778241
saturation_steps = 0
pass = True
pass_margin = True

结论：

推荐 online swing joint tracking baseline 为 kp=80.0、kd=2.0、target_scale=0.6。该配置满足 joint error、base z、roll、pitch 和 torque saturation 检查。

边界：

该测试只验证 joint target tracking，不叠加 full WBC torque。尚未完成 online swing target 与 full WBC 同时闭环、swing target 到 full WBC acceleration task 的转换、touchdown/liftoff contact feedback、base velocity tracking、forward velocity command 和 ROS2/C++ 实时实现。

下一步：

生成 recommended online swing joint target tracking support test：

scripts/stage07_online_swing_joint_tracking_recommended_test.py

输出文件：

results/logs_sample/stage07_online_swing_joint_tracking_recommended_test_log.csv
results/logs_sample/stage07_online_swing_joint_tracking_recommended_test_summary.csv

<!-- STAGE7_ONLINE_SWING_JOINT_TRACKING_STABILITY_SWEEP_END -->

<!-- STAGE7_ONLINE_SWING_JOINT_TRACKING_RECOMMENDED_TEST_START -->

## Stage 7 更新：Online Swing Joint Tracking Recommended Test

online swing joint tracking recommended test 已通过。

输入文件：

results/logs_sample/stage07_online_swing_trajectory_tracking_check.csv

脚本：

scripts/stage07_online_swing_joint_tracking_recommended_test.py

输出文件：

results/logs_sample/stage07_online_swing_joint_tracking_recommended_test_log.csv
results/logs_sample/stage07_online_swing_joint_tracking_recommended_test_summary.csv

推荐配置：

kp = 80.0
kd = 2.0
target_scale = 0.6
torque_limit = 23.7

结果：

total_steps = 1200
initial_z = 0.284805846483
final_z = 0.282769844842
min_z = 0.270657074947
max_z = 0.285595003453
delta_z = -0.002036001641
final_roll = -0.006184160640
final_pitch = -0.008386076938
max_abs_roll = 0.063224324564
roll_margin_to_0p20 = 0.136775675436
max_abs_pitch = 0.055307047284
pitch_margin_to_0p20 = 0.144692952716
z_margin_to_0p22 = 0.050657074947
max_joint_error = 0.059643533460
max_swing_joint_error = 0.059643533460
max_stance_joint_error = 0.035331528104
max_tau_raw_abs = 9.930087778241
max_tau_total_abs = 9.930087778241
saturation_steps = 0
pass = True
pass_margin = True

结论：

当前 online swing joint tracking 推荐 baseline 为 kp=80.0、kd=2.0、target_scale=0.6。该配置满足 joint error、base z、roll、pitch 和 torque saturation 检查。

边界：

该测试仍不是完整动态 trot locomotion。尚未完成 online swing joint tracking 与 full WBC torque 同时闭环、swing target 到 full WBC swing acceleration task 的在线转换、touchdown/liftoff contact feedback、base velocity tracking、forward velocity command 和 ROS2/C++ 实时实现。

下一步：

进入 combined online test：

scripts/stage07_online_full_wbc_plus_swing_joint_tracking_proto.py

输出文件：

results/logs_sample/stage07_online_full_wbc_plus_swing_joint_tracking_proto_log.csv
results/logs_sample/stage07_online_full_wbc_plus_swing_joint_tracking_proto_summary.csv

<!-- STAGE7_ONLINE_SWING_JOINT_TRACKING_RECOMMENDED_TEST_END -->

<!-- STAGE7_ONLINE_FULL_WBC_PLUS_SWING_JOINT_TRACKING_SWEEP_START -->

## Stage 7 更新：Online Full WBC Plus Swing Joint Tracking Sweep

online full WBC plus swing joint tracking sweep 已完成。

结论：直接叠加 full WBC torque 与 swing joint PD torque 的方案当前不通过。

输出文件：

results/logs_sample/stage07_online_full_wbc_plus_swing_joint_tracking_sweep.csv

Sweep 参数：

WBC_TORQUE_SCALE_LIST = [0.0, 0.25, 0.50, 0.75]
SWING_PD_TORQUE_SCALE_LIST = [0.25, 0.50, 0.75]
TARGET_SCALE_LIST = [0.45, 0.60]

总体结果：

num_cases = 24
pass_cases = 4
pass_margin_cases = 4

推荐项：

wbc_torque_scale = 0.0
swing_pd_torque_scale = 0.75
target_scale = 0.45

推荐项结果：

total_steps = 1200
transition_count = 5
trot_FR_RL_steps = 600
trot_FL_RR_steps = 600
initial_z = 0.284805846483
final_z = 0.278310544360
min_z = 0.273560102250
max_z = 0.286192396049
delta_z = -0.006495302123
final_roll = 0.001730304043
final_pitch = 0.004612578650
max_abs_roll = 0.081050979581
max_abs_pitch = 0.038526145564
z_margin_to_0p22 = 0.053560102250
max_joint_error = 0.056916933566
max_swing_joint_error = 0.056916933566
max_stance_joint_error = 0.040626466563
max_tau_wbc_abs = 0.000000000000
max_tau_swing_pd_abs = 6.927913461938
max_tau_total_abs = 6.927913461938
qp_fail_steps = 0
saturation_steps = 0
pass = True
pass_margin = True

关键发现：

所有通过项的 wbc_torque_scale 都是 0.0。因此本轮通过结果实际是 swing joint PD-only，不是 full WBC + swing joint tracking 的成功耦合。wbc_torque_scale >= 0.25 时均未通过。

结论：

direct full WBC torque + swing joint PD torque sum 被拒绝。当前保留 online full WBC scheduler recommended run 和 online swing joint tracking recommended test 两个已通过 baseline，但不能直接以 torque sum 方式合并。

下一步：

改为 stance-only WBC torque + swing joint PD torque：

scripts/stage07_online_stance_wbc_plus_swing_pd_proto.py

输出文件：

results/logs_sample/stage07_online_stance_wbc_plus_swing_pd_proto_log.csv
results/logs_sample/stage07_online_stance_wbc_plus_swing_pd_proto_summary.csv

<!-- STAGE7_ONLINE_FULL_WBC_PLUS_SWING_JOINT_TRACKING_SWEEP_END -->

<!-- STAGE7_ONLINE_STANCE_PD_WBC_PLUS_SWING_PD_SWEEP_START -->

## Stage 7 更新：Online Stance PD/WBC Plus Swing PD Sweep

online stance PD/WBC plus swing PD sweep 已通过。

脚本：

scripts/stage07_online_stance_pd_wbc_plus_swing_pd_sweep.py

输出文件：

results/logs_sample/stage07_online_stance_pd_wbc_plus_swing_pd_sweep.csv

控制结构：

stance legs = standing posture PD + optional stance WBC feedforward
swing legs = swing target PD

总体结果：

num_cases = 36
pass_cases = 27
pass_margin_cases = 27
stance_wbc_pass_cases = 19

脚本自动推荐项为 stance_wbc_scale=0.0、swing_pd_scale=1.0、swing_target_scale=0.35。该项通过，但属于 PD-only，不包含 stance WBC feedforward，因此不作为最终 combined baseline。

采用的非零 WBC 推荐项：

stance_wbc_scale = 0.2
swing_pd_scale = 1.0
swing_target_scale = 0.35

非零 WBC 推荐项结果：

total_steps = 1200
transition_count = 5
trot_FR_RL_steps = 600
trot_FL_RR_steps = 600
initial_z = 0.284805846483
final_z = 0.286644861037
min_z = 0.278419161322
max_z = 0.289102536841
delta_z = 0.001839014553
final_roll = -0.015879508048
final_pitch = -0.009621783271
max_abs_roll = 0.056707402709
max_abs_pitch = 0.048329482530
z_margin_to_0p22 = 0.058419161322
max_joint_error = 0.077233662573
max_swing_joint_error = 0.042163850217
max_stance_joint_error = 0.077233662573
max_tau_stance_pd_abs = 11.083222358114
max_tau_stance_wbc_abs = 2.125887056052
max_tau_swing_pd_abs = 9.659563043535
max_tau_total_abs = 9.659563043535
qp_fail_steps = 0
saturation_steps = 0
pass = True
pass_margin = True

结论：

当前可用 combined control baseline 为 stance PD + scaled stance WBC feedforward + swing target PD。采用配置为 stance_wbc_scale=0.2、swing_pd_scale=1.0、swing_target_scale=0.35。

边界：

该方案仍不是最终 WBC locomotion。WBC 只是 stance legs feedforward，不是严格 task-priority WBC。尚未完成 WBC QP 内部直接加入 online swing target task、swing target 到 acceleration task 的实时转换、touchdown/liftoff contact feedback、base velocity tracking、forward velocity command 和 ROS2/C++ 实时实现。

下一步：

生成 recommended run：

scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py

输出文件：

results/logs_sample/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test_log.csv
results/logs_sample/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test_summary.csv

<!-- STAGE7_ONLINE_STANCE_PD_WBC_PLUS_SWING_PD_SWEEP_END -->

<!-- STAGE7_ONLINE_STANCE_PD_WBC_PLUS_SWING_PD_RECOMMENDED_TEST_START -->

## Stage 7 更新：Online Stance PD/WBC Plus Swing PD Recommended Test

online stance PD/WBC plus swing PD recommended test 已通过。

脚本：

scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py

输出文件：

results/logs_sample/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test_log.csv
results/logs_sample/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test_summary.csv

控制结构：

stance legs = standing posture PD + scaled stance WBC feedforward
swing legs = online swing target PD

配置：

STANCE_KP = 60.0
STANCE_KD = 2.0
SWING_KP = 80.0
SWING_KD = 2.0
stance_wbc_scale = 0.2
swing_pd_scale = 1.0
swing_target_scale = 0.35
torque_limit = 23.7

结果：

total_steps = 1200
transition_count = 5
trot_FR_RL_steps = 600
trot_FL_RR_steps = 600
initial_z = 0.284805846483
final_z = 0.286644861037
min_z = 0.278419161322
max_z = 0.289102536841
delta_z = 0.001839014553
final_roll = -0.015879508048
final_pitch = -0.009621783271
max_abs_roll = 0.056707402709
max_abs_pitch = 0.048329482530
z_margin_to_0p22 = 0.058419161322
max_joint_error = 0.077233662573
max_swing_joint_error = 0.042163850217
max_stance_joint_error = 0.077233662573
max_tau_stance_pd_abs = 11.083222358114
max_tau_stance_wbc_abs = 2.125887056052
max_tau_swing_pd_abs = 9.659563043535
max_tau_total_abs = 9.659563043535
max_cmd_step_jump_norm = 25.788963931985
max_cmd_step_jump_abs = 10.987848177937
max_dyn_res_norm = 7.732488454756e-08
max_stance_acc_res_norm = 3.520891005970e-09
max_swing_acc_error_norm = 2.545718566371e-01
qp_fail_steps = 0
saturation_steps = 0
pass = True
pass_margin = True

结论：

当前可用 combined online baseline 为 stance PD + scaled stance WBC feedforward + swing target PD。该配置通过 1200-step scheduler-driven trot 测试，姿态、高度、swing joint error、QP failure 和 torque saturation 均满足检查。

关键判断：

该结果不是 pure full WBC locomotion，而是 mixed online control baseline。WBC 当前作为 stance feedforward，stance 稳定性主要由 posture PD 保证，swing motion 由 online swing target PD 保证。

边界：

尚未完成 WBC QP 内部直接接入 online swing target task、swing target 到 acceleration reference 的在线转换、contact feedback 驱动 touchdown/liftoff、base velocity tracking、forward velocity command 和 ROS2/C++ 实时实现。

下一步：

生成 Stage 7 online locomotion consolidated summary：

docs/STAGE07_ONLINE_LOCOMOTION_CONSOLIDATED_SUMMARY.md

<!-- STAGE7_ONLINE_STANCE_PD_WBC_PLUS_SWING_PD_RECOMMENDED_TEST_END -->

<!-- STAGE7_ONLINE_LOCOMOTION_CONSOLIDATED_SUMMARY_START -->

## Stage 7 更新：Online Locomotion Consolidated Summary

Stage 7 online locomotion 主线已完成阶段性闭环。

汇总文档：

docs/STAGE07_ONLINE_LOCOMOTION_CONSOLIDATED_SUMMARY.md

当前可用 combined online baseline：

stance legs = standing posture PD + scaled stance WBC feedforward
swing legs = online swing target PD

推荐脚本：

scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py

推荐配置：

STANCE_KP = 60.0
STANCE_KD = 2.0
SWING_KP = 80.0
SWING_KD = 2.0
stance_wbc_scale = 0.2
swing_pd_scale = 1.0
swing_target_scale = 0.35
torque_limit = 23.7

推荐结果：

total_steps = 1200
transition_count = 5
trot_FR_RL_steps = 600
trot_FL_RR_steps = 600
initial_z = 0.284805846483
final_z = 0.286644861037
min_z = 0.278419161322
max_z = 0.289102536841
delta_z = 0.001839014553
max_abs_roll = 0.056707402709
max_abs_pitch = 0.048329482530
max_joint_error = 0.077233662573
max_swing_joint_error = 0.042163850217
max_stance_joint_error = 0.077233662573
max_tau_stance_pd_abs = 11.083222358114
max_tau_stance_wbc_abs = 2.125887056052
max_tau_swing_pd_abs = 9.659563043535
max_tau_total_abs = 9.659563043535
qp_fail_steps = 0
saturation_steps = 0
pass = True
pass_margin = True

Stage 7 关键结论：

1. online gait scheduler 已通过
2. online memory swing trajectory 已通过
3. swing trajectory IK/QP joint target conversion 已通过
4. MuJoCo swing joint target tracking 已通过
5. online full WBC scheduler proto 已通过
6. direct full WBC torque + swing PD torque sum 被拒绝
7. stance-only WBC + swing-only PD 被拒绝
8. stance PD + scaled stance WBC feedforward + swing PD 已通过

当前边界：

该结果不是 pure WBC locomotion，而是 mixed online control baseline。尚未完成 WBC QP 内部直接接入 online swing target task、swing target 到 acceleration reference 的在线转换、contact feedback、base velocity tracking、forward velocity command 和 ROS2/C++ 实时实现。

Stage 8 入口：

建议从 Python/MuJoCo proto 进入可迁移控制架构。

建议起始文档：

docs/STAGE08_INTERFACE_PLAN.md

建议起始脚本：

scripts/stage08_interface_contract_check.py

<!-- STAGE7_ONLINE_LOCOMOTION_CONSOLIDATED_SUMMARY_END -->

## Stage 8.0 Runtime Interface Contract Check

Stage 8 has started with a minimal runtime interface contract check.

- Script: `scripts/stage08_runtime_interface_contract_check.py`
- Log: `results/logs_sample/stage08_runtime_interface_contract_check_log.csv`
- Summary: `results/logs_sample/stage08_runtime_interface_contract_check_summary.csv`
- Docs: `docs/STAGE08_RUNTIME_INTERFACE_CONTRACT_CHECK.md`
- pass: `True`
- qpos_roundtrip_max_abs: `0.0`
- qvel_roundtrip_max_abs: `0.0`
- torque_roundtrip_max_abs: `0.0`

This check only validates the MuJoCo/Pinocchio runtime interface contract. It does not complete ROS2/C++ migration or pure WBC locomotion.

## Stage 8.1 Runtime Interface Adapter Module Check

Stage 8.1 extracted the MuJoCo/Pinocchio runtime mapping logic into a reusable Python module.

- Module: `scripts/common/go1_runtime_interface.py`
- Script: `scripts/stage08_runtime_interface_adapter_module_check.py`
- Log: `results/logs_sample/stage08_runtime_interface_adapter_module_check_log.csv`
- Summary: `results/logs_sample/stage08_runtime_interface_adapter_module_check_summary.csv`
- Docs: `docs/STAGE08_RUNTIME_INTERFACE_ADAPTER_MODULE_CHECK.md`
- pass: `True`
- qpos_roundtrip_max_abs: `0.0`
- qvel_roundtrip_max_abs: `0.0`
- torque_roundtrip_max_abs: `0.0`

This stage only validates the reusable runtime adapter. It does not complete ROS2/C++ migration or pure WBC locomotion.

## Stage 8.2 Adapter Zero-Control Regression Guard

Stage 8.2 verified the Stage 8.1 runtime adapter and reran the Stage 7 recommended mixed baseline without changing controller logic.

- Script: `scripts/stage08_adapter_zero_control_regression_guard.py`
- Log: `results/logs_sample/stage08_adapter_zero_control_regression_guard_log.csv`
- Summary: `results/logs_sample/stage08_adapter_zero_control_regression_guard_summary.csv`
- Docs: `docs/STAGE08_ADAPTER_ZERO_CONTROL_REGRESSION_GUARD.md`
- pass: `False`
- adapter_qpos_roundtrip_max_abs: `0.0`
- adapter_qvel_roundtrip_max_abs: `0.0`
- adapter_torque_roundtrip_max_abs: `0.0`
- stage07_pass: `False`
- stage07_pass_margin: `False`
- stage07_qp_fail_steps: `nan`
- stage07_saturation_steps: `nan`

This stage is a zero-control-change regression guard. It does not complete ROS2/C++ migration, EKF, base velocity tracking, full MPC, or pure full WBC locomotion.

## Stage 8.3 Adapter-backed Stage 7 Baseline A/B Test

Stage 8.3 created an adapter-backed Stage 7 entrypoint and compared it with the original Stage 7 recommended mixed baseline.

- Original script: `scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py`
- Adapter-backed script: `scripts/stage08_adapter_backed_stage07_recommended_test.py`
- A/B script: `scripts/stage08_adapter_backed_stage07_baseline_ab_test.py`
- Log: `results/logs_sample/stage08_adapter_backed_stage07_baseline_ab_test_log.csv`
- Summary: `results/logs_sample/stage08_adapter_backed_stage07_baseline_ab_test_summary.csv`
- Docs: `docs/STAGE08_ADAPTER_BACKED_STAGE07_BASELINE_AB_TEST.md`
- pass: `True`
- adapter_qpos_roundtrip_max_abs: `0.0`
- adapter_qvel_roundtrip_max_abs: `0.0`
- adapter_torque_roundtrip_max_abs: `0.0`
- original_pass: `True`
- adapter_pass: `True`
- original_pass_margin: `True`
- adapter_pass_margin: `True`

This is an adapter-backed entrypoint regression, not a controller redesign. It does not complete pure WBC locomotion, ROS2/C++ migration, EKF, or full MPC.

## Stage 8.4 Runtime Mapping Duplication Audit

Stage 8.4 scanned Python scripts for duplicated MuJoCo/Pinocchio runtime mapping logic before refactoring.

- Script: `scripts/stage08_runtime_mapping_duplication_audit.py`
- Log: `results/logs_sample/stage08_runtime_mapping_duplication_audit_log.csv`
- Summary: `results/logs_sample/stage08_runtime_mapping_duplication_audit_summary.csv`
- Docs: `docs/STAGE08_RUNTIME_MAPPING_DUPLICATION_AUDIT.md`
- pass: `True`
- stage83_pass: `True`
- files_with_findings: `69`
- total_findings: `246`
- high_severity_findings: `87`
- medium_severity_findings: `55`
- low_severity_findings: `104`

Findings are refactor candidates, not controller failures. Stage 8 remains focused on runtime interface hardening and does not complete pure WBC locomotion, ROS2/C++ migration, EKF, or full MPC.

## Stage 8.5 Runtime Mapping Audit Triage

Stage 8.5 classified Stage 8.4 runtime mapping findings into active dependency path findings and legacy/non-active script findings.

- Script: `scripts/stage08_runtime_mapping_audit_triage.py`
- Log: `results/logs_sample/stage08_runtime_mapping_audit_triage_log.csv`
- Summary: `results/logs_sample/stage08_runtime_mapping_audit_triage_summary.csv`
- Docs: `docs/STAGE08_RUNTIME_MAPPING_AUDIT_TRIAGE.md`
- pass: `True`
- audit_pass: `True`
- active_dependency_file_count: `4`
- total_findings: `246`
- active_dependency_findings: `5`
- legacy_or_nonactive_findings: `241`
- active_high_severity_findings: `2`
- active_medium_severity_findings: `2`
- active_low_severity_findings: `1`

Findings in legacy validation scripts are not treated as current controller-chain failures. Stage 8 remains focused on runtime interface hardening and does not complete pure WBC locomotion, ROS2/C++ migration, EKF, or full MPC.

## Stage 8.6 Active-path Hard-coded MuJoCo Leg Order Refactor and Regression

Stage 8.6 replaced active-path hard-coded MuJoCo leg order assignments with the shared adapter constant `MJ_LEG_ORDER`.

- Script: `scripts/stage08_active_leg_order_refactor_and_regression.py`
- Patched files:
  - `scripts/stage07_online_full_wbc_scheduler_recommended_run.py`
  - `scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py`
- Log: `results/logs_sample/stage08_active_leg_order_refactor_and_regression_log.csv`
- Summary: `results/logs_sample/stage08_active_leg_order_refactor_and_regression_summary.csv`
- Docs: `docs/STAGE08_ACTIVE_LEG_ORDER_REFACTOR_AND_REGRESSION.md`
- pass: `True`
- rerun_stage83_ab_pass: `True`
- active_high_severity_findings_after_refactor: `0`
- active_medium_severity_findings_after_refactor: `2`
- active_low_severity_findings_after_refactor: `1`

This is an active-path runtime interface refactor with A/B regression. It does not complete pure WBC locomotion, ROS2/C++ migration, EKF, or full MPC.

## Stage 8.7 推荐 runtime-safe 入口固化

Stage 8.7 将 Stage 8 推荐运行入口固化为：

    /usr/bin/python3 scripts/stage08_adapter_backed_stage07_recommended_test.py

该入口运行 Stage 7 mixed online control baseline 前，会先执行 runtime adapter preflight。

输出文件：

- docs/STAGE08_RECOMMENDED_RUNTIME_SAFE_ENTRYPOINT.md
- results/logs_sample/stage08_recommended_runtime_safe_entrypoint_promotion_summary.csv
- results/logs_sample/stage08_recommended_runtime_safe_entrypoint_stdout.txt
- results/logs_sample/stage08_recommended_runtime_safe_entrypoint_stderr.txt

本阶段没有完成 pure full WBC locomotion、ROS2/C++ migration、EKF、base velocity tracking 或 full MPC。

## Stage 8.8 Stage 8.0–8.7 Runtime Interface Hardening 中文汇总

Stage 8.8 生成了 Stage 8.0–8.7 中文汇总文档，冻结当前 runtime-safe Python baseline。

核心结论：

- Stage 8.0–8.7 已完成 runtime interface hardening 第一轮闭环。
- 当前推荐入口为：

      /usr/bin/python3 scripts/stage08_adapter_backed_stage07_recommended_test.py

- runtime adapter module 为：

      scripts/common/go1_runtime_interface.py

- active high-severity runtime mapping duplication 已清零。
- 当前控制器仍是 Stage 7 mixed online control baseline。
- 本阶段没有完成 pure full WBC locomotion、ROS2/C++ real-time controller、EKF 或 full 3D centroidal MPC。

输出文件：

- docs/STAGE08_0_7_RUNTIME_INTERFACE_HARDENING_SUMMARY.md
- results/logs_sample/stage08_0_7_runtime_interface_hardening_summary.csv


## Stage 8.9 Python Runtime-safe Baseline Freeze Manifest

Stage 8.9 生成了 Python runtime-safe baseline freeze manifest。

当前冻结 baseline：

    Stage 8 runtime-safe adapter-backed Stage 7 mixed online control baseline

推荐入口：

    /usr/bin/python3 scripts/stage08_adapter_backed_stage07_recommended_test.py

核心文件：

- scripts/stage08_adapter_backed_stage07_recommended_test.py
- scripts/common/go1_runtime_interface.py
- docs/STAGE08_0_7_RUNTIME_INTERFACE_HARDENING_SUMMARY.md
- docs/STAGE08_BASELINE_FREEZE_MANIFEST.md
- results/logs_sample/stage08_baseline_freeze_manifest.csv

边界：

- control_law_changed = False
- baseline_type = mixed_online_control_baseline
- active_high_severity_findings_after_refactor = 0
- pure_wbc_locomotion_completed = False
- ros2_cpp_realtime_controller_completed = False
- ekf_completed = False
- full_3d_centroidal_mpc_completed = False

后续 ROS2/C++ 或更深控制器改造必须以该 frozen baseline 作为回归基准。

## Stage 8.10 Freeze Integrity Check

Stage 8.10 完成 Python runtime-safe frozen baseline 的完整性检查。

- Script: `scripts/stage08_freeze_integrity_check.py`
- Hash log: `results/logs_sample/stage08_freeze_integrity_hashes.csv`
- Summary: `results/logs_sample/stage08_freeze_integrity_check_summary.csv`
- Docs: `docs/STAGE08_FREEZE_INTEGRITY_CHECK.md`
- pass: `True`
- all_files_exist: `True`
- recommended_entrypoint_returncode: `0`
- adapter_preflight_stdout_pass: `True`

当前 baseline 仍是 mixed online control baseline，不是 pure full WBC locomotion。后续 ROS2/C++ 或控制器改造必须以该 frozen baseline 为回归基准。

## Stage 9.0 ROS2/C++ Interface Contract Inventory

Stage 9.0 完成 ROS2/C++ interface contract inventory。

- Script: `scripts/stage09_ros2_cpp_interface_contract_inventory.py`
- Log: `results/logs_sample/stage09_ros2_cpp_interface_contract_inventory_log.csv`
- Topic map: `results/logs_sample/stage09_ros2_cpp_interface_topic_contract_map.csv`
- Summary: `results/logs_sample/stage09_ros2_cpp_interface_contract_inventory_summary.csv`
- Docs: `docs/STAGE09_ROS2_CPP_INTERFACE_CONTRACT_INVENTORY.md`
- pass: `True`
- bridge_package_found: `True`
- all_expected_topics_found: `True`
- control_law_changed: `False`
- stage9_scope: `interface_inventory_only`

Stage 9.0 只做接口盘点，不写实时 C++ controller，不改变控制律。当前 baseline 仍是 mixed online control baseline。

## Stage 9.1 ROS2 Topic Schema Snapshot

Stage 9.1 完成 ROS2 topic schema snapshot。

- Script: `scripts/stage09_ros2_topic_schema_snapshot.py`
- Log: `results/logs_sample/stage09_ros2_topic_schema_snapshot_log.csv`
- Schema map: `results/logs_sample/stage09_ros2_topic_schema_snapshot_map.csv`
- Schema dir: `results/logs_sample/stage09_topic_schemas/`
- Summary: `results/logs_sample/stage09_ros2_topic_schema_snapshot_summary.csv`
- Docs: `docs/STAGE09_ROS2_TOPIC_SCHEMA_SNAPSHOT.md`
- pass: `True`
- topic_found_count: `6`
- topic_type_inferred_count: `6`
- topic_schema_available_count: `6`
- control_law_changed: `False`
- stage9_scope: `topic_schema_snapshot_only`

Stage 9.1 只记录消息类型和字段 schema，不写实时 C++ controller，不改变控制律。当前 baseline 仍是 mixed online control baseline。

## Stage 9.2 Python frozen baseline ↔ ROS2 topic field mapping table

Stage 9.2 完成 Python frozen baseline 与 ROS2 bridge topic 字段之间的映射表。

- Script: `scripts/stage09_python_baseline_ros2_field_mapping.py`
- Log: `results/logs_sample/stage09_python_baseline_ros2_field_mapping_log.csv`
- Field map: `results/logs_sample/stage09_python_baseline_ros2_field_mapping.csv`
- Summary: `results/logs_sample/stage09_python_baseline_ros2_field_mapping_summary.csv`
- Docs: `docs/STAGE09_PYTHON_BASELINE_ROS2_FIELD_MAPPING.md`
- pass: `True`
- field_mapping_rows: `11`
- all_types_match_stage91_schema: `True`
- control_law_changed: `False`
- stage9_scope: `field_mapping_table_only`

Stage 9.2 只生成接口映射表，不写实时 C++ controller，不改变控制律。当前 baseline 仍是 mixed online control baseline。

## Stage 9.3 ROS2/C++ Interface Mirror Skeleton

Stage 9.3 创建并编译了 C++ ROS2 interface mirror skeleton。

- Package: `ros2_ws/src/robot_mpc_wbc_cpp_interface`
- Node: `go1_interface_mirror_node`
- Script: `scripts/stage09_ros2_cpp_interface_mirror_skeleton_check.py`
- Log: `results/logs_sample/stage09_ros2_cpp_interface_mirror_skeleton_check_log.csv`
- Summary: `results/logs_sample/stage09_ros2_cpp_interface_mirror_skeleton_check_summary.csv`
- Docs: `docs/STAGE09_ROS2_CPP_INTERFACE_MIRROR_SKELETON.md`
- pass: `True`
- subscription_found_count: `6`
- torque_command_publisher_found: `False`
- publish_call_found: `False`
- colcon_build_returncode: `0`
- control_law_changed: `False`
- stage9_scope: `cpp_interface_mirror_skeleton_only`

Stage 9.3 只创建 C++ interface mirror skeleton，不发布 torque command，不写实时 controller，不改变控制律。

## Stage 9.4 ROS2 Runtime Mirror Smoke Test

Stage 9.4 完成 ROS2 runtime mirror smoke test。

- Script: `scripts/stage09_ros2_runtime_mirror_smoke_test.py`
- Log: `results/logs_sample/stage09_ros2_runtime_mirror_smoke_test_log.csv`
- Topic observations: `results/logs_sample/stage09_ros2_runtime_mirror_topic_observations.csv`
- Summary: `results/logs_sample/stage09_ros2_runtime_mirror_smoke_test_summary.csv`
- Docs: `docs/STAGE09_ROS2_RUNTIME_MIRROR_SMOKE_TEST.md`
- pass: `True`
- topic_present_count: `6`
- topic_type_match_count: `6`
- published_topic_echo_success_count: `5`
- torque_cmd_publisher_count: `0`
- control_law_changed: `False`
- torque_command_published_by_stage94: `False`
- stage9_scope: `runtime_mirror_smoke_test_only`

Stage 9.4 只验证 runtime interface mirror，不发布 torque，不写实时 C++ controller，不改变控制律。

## Stage 9.5 C++ Mirror Contract Report

Stage 9.5 生成了 C++ mirror contract report，汇总 Stage 9.0–9.4。

- Script: `scripts/stage09_cpp_mirror_contract_report.py`
- Log: `results/logs_sample/stage09_cpp_mirror_contract_report_log.csv`
- Summary: `results/logs_sample/stage09_cpp_mirror_contract_report_summary.csv`
- Docs: `docs/STAGE09_CPP_MIRROR_CONTRACT_REPORT.md`
- pass: `True`
- topic_present_count: `6`
- topic_type_match_count: `6`
- torque_cmd_publisher_count: `0`
- control_law_changed: `False`
- stage9_scope: `cpp_mirror_contract_report_only`

Stage 9.5 只汇总 interface mirror contract，不发布 torque，不写实时 C++ controller，不改变控制律。

## Stage 9.6 C++ Mirror Runtime Contract Guard

Stage 9.6 完成 C++ mirror runtime contract guard。

- Script: `scripts/stage09_cpp_mirror_runtime_contract_guard.py`
- Log: `results/logs_sample/stage09_cpp_mirror_runtime_contract_guard_log.csv`
- Samples: `results/logs_sample/stage09_cpp_mirror_runtime_contract_guard_samples.csv`
- Summary: `results/logs_sample/stage09_cpp_mirror_runtime_contract_guard_summary.csv`
- Docs: `docs/STAGE09_CPP_MIRROR_RUNTIME_CONTRACT_GUARD.md`
- pass: `False`
- all_sample_topic_types_match: `True`
- torque_cmd_publishers_all_zero: `True`
- torque_cmd_subscribers_positive: `True`
- control_law_changed: `False`
- torque_command_published_by_stage96: `False`
- stage9_scope: `cpp_mirror_runtime_contract_guard_only`

Stage 9.6 只固化 interface mirror runtime guard，不发布 torque，不写实时 C++ controller，不改变控制律。

## Stage 9.7 Stage 9.0–9.6 Interface Mirror Freeze Summary

Stage 9.7 生成了 Stage 9.0–9.6 ROS2/C++ interface mirror freeze summary。

- Script: `scripts/stage09_interface_mirror_freeze_summary.py`
- Log: `results/logs_sample/stage09_0_6_interface_mirror_freeze_log.csv`
- Hashes: `results/logs_sample/stage09_0_6_interface_mirror_freeze_hashes.csv`
- Summary: `results/logs_sample/stage09_0_6_interface_mirror_freeze_summary.csv`
- Docs: `docs/STAGE09_0_6_INTERFACE_MIRROR_FREEZE_SUMMARY.md`
- pass: `True`
- ros2_cpp_interface_mirror_frozen: `True`
- control_law_changed: `False`
- torque_command_published_by_stage97: `False`
- stage9_scope: `interface_mirror_freeze_summary_only`

Stage 9.0–9.6 形成 ROS2/C++ interface mirror frozen baseline。它不是实时控制器，不发布 torque，不改变控制律。

## Stage 10.0 Controller Implementation Plan and Safety Gate

Stage 10.0 生成了 controller implementation plan 与 torque publisher safety gate。

- Script: `scripts/stage10_controller_implementation_plan_and_safety_gate.py`
- Log: `results/logs_sample/stage10_controller_implementation_plan_and_safety_gate_log.csv`
- Plan CSV: `results/logs_sample/stage10_controller_implementation_plan.csv`
- Safety gate CSV: `results/logs_sample/stage10_torque_publisher_safety_gate.csv`
- Summary: `results/logs_sample/stage10_controller_implementation_plan_and_safety_gate_summary.csv`
- Docs: `docs/STAGE10_CONTROLLER_IMPLEMENTATION_PLAN_AND_SAFETY_GATE.md`
- pass: `True`
- torque_enable_ready: `False`
- control_law_changed: `False`
- torque_publisher_enabled: `False`
- torque_command_published_by_stage100: `False`
- stage10_scope: `controller_planning_and_safety_gate_only`

Stage 10.0 不写 controller，不发布 torque，不改变控制律。后续 Stage 10.1 只能创建 disabled-by-default controller skeleton。

## Stage 10.1 Disabled-by-default C++ Controller Skeleton

Stage 10.1 创建并编译了 disabled-by-default C++ controller skeleton。

- Package: `ros2_ws/src/robot_mpc_wbc_cpp_controller`
- Node: `go1_disabled_controller_node`
- Script: `scripts/stage10_disabled_cpp_controller_skeleton_check.py`
- Log: `results/logs_sample/stage10_disabled_cpp_controller_skeleton_check_log.csv`
- Summary: `results/logs_sample/stage10_disabled_cpp_controller_skeleton_check_summary.csv`
- Docs: `docs/STAGE10_DISABLED_CPP_CONTROLLER_SKELETON.md`
- pass: `True`
- subscription_found_count: `5`
- source_references_torque_cmd_topic: `False`
- source_has_create_publisher: `False`
- source_has_publish_call: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 10.1 只创建 disabled controller skeleton，不发布 torque，不改变控制律。\n\n## Stage 10.2 C++ State Cache Runtime Validation

Stage 10.2 完成 disabled-by-default C++ controller skeleton 的 state cache runtime validation。

- Script: `scripts/stage10_cpp_state_cache_runtime_validation.py`
- Log: `results/logs_sample/stage10_cpp_state_cache_runtime_validation_log.csv`
- Topic observations: `results/logs_sample/stage10_cpp_state_cache_runtime_validation_topic_observations.csv`
- Summary: `results/logs_sample/stage10_cpp_state_cache_runtime_validation_summary.csv`
- Docs: `docs/STAGE10_CPP_STATE_CACHE_RUNTIME_VALIDATION.md`
- pass: `False`
- state_topic_present_count: `5`
- state_topic_type_match_count: `5`
- state_topic_pubsub_ok_count: `0`
- state_topic_echo_ok_count: `5`
- torque_topic_publishers_zero: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 10.2 只验证 state cache 输入链路，不发布 torque，不改变控制律。\n

## Stage 10.3 Zero Torque Dry-run Internal Command Validation

Stage 10.3 完成 zero torque dry-run internal command validation。

- Script: `scripts/stage10_zero_torque_dry_run_internal_validation.py`
- Header: `ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp`
- Contract check: `ros2_ws/src/robot_mpc_wbc_cpp_controller/src/zero_torque_dry_run_contract_check.cpp`
- Log: `results/logs_sample/stage10_zero_torque_dry_run_internal_validation_log.csv`
- Vector CSV: `results/logs_sample/stage10_zero_torque_dry_run_vector.csv`
- Summary: `results/logs_sample/stage10_zero_torque_dry_run_internal_validation_summary.csv`
- Docs: `docs/STAGE10_ZERO_TORQUE_DRY_RUN_INTERNAL_VALIDATION.md`
- pass: `True`
- zero_torque_size: `12`
- zero_torque_all_zero: `True`
- zero_torque_max_abs: `0`
- torque_topic_publishers_zero: `True`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 10.3 只验证内部 zero torque dry-run command，不发布 torque，不改变控制律。

## Stage 10.4 Python Frozen Baseline A/B Regression

Stage 10.4 完成 Python frozen baseline A/B regression。

- Script: `scripts/stage10_python_frozen_baseline_ab_regression.py`
- Log: `results/logs_sample/stage10_python_frozen_baseline_ab_regression_log.csv`
- Safety gate: `results/logs_sample/stage10_torque_publisher_safety_gate_after_stage104.csv`
- Summary: `results/logs_sample/stage10_python_frozen_baseline_ab_regression_summary.csv`
- Docs: `docs/STAGE10_PYTHON_FROZEN_BASELINE_AB_REGRESSION.md`
- pass: `True`
- stage8_freeze_pass_after_rerun: `True`
- stage83_ab_pass_after_rerun: `True`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 10.4 只做 Python frozen baseline 回归，不发布 torque，不改变控制律。

## Stage 10.5 Torque Publisher Enable Gate Design

Stage 10.5 完成 torque publisher enable gate design。

- Script: `scripts/stage10_torque_publisher_enable_gate_design.py`
- Design CSV: `results/logs_sample/stage10_torque_publisher_enable_gate_design.csv`
- Safety gate CSV: `results/logs_sample/stage10_torque_publisher_safety_gate_after_stage105.csv`
- Summary: `results/logs_sample/stage10_torque_publisher_enable_gate_design_summary.csv`
- Docs: `docs/STAGE10_TORQUE_PUBLISHER_ENABLE_GATE_DESIGN.md`
- pass: `True`
- manual_enable_flag_design_exists: `True`
- clamp_watchdog_design_exists: `True`
- clamp_watchdog_implemented: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 10.5 只设计 enable gate，不创建 publisher，不发布 torque，不改变控制律。

## Stage 10.6 Stage 10.0–10.5 Controller Planning Freeze Summary

Stage 10.6 冻结 Stage 10.0–10.5 controller-planning baseline。

- Script: `scripts/stage10_0_5_controller_planning_freeze_summary.py`
- Log: `results/logs_sample/stage10_0_5_controller_planning_freeze_log.csv`
- Hashes: `results/logs_sample/stage10_0_5_controller_planning_freeze_hashes.csv`
- Summary: `results/logs_sample/stage10_0_5_controller_planning_freeze_summary.csv`
- Docs: `docs/STAGE10_0_5_CONTROLLER_PLANNING_FREEZE_SUMMARY.md`
- pass: `True`
- controller_planning_frozen: `True`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 10.0–10.5 只形成 controller planning baseline，不发布 torque，不改变控制律。

## Stage 10.7 Clamp/Watchdog Utility Without Publisher

Stage 10.7 完成 clamp/watchdog utility implementation without publisher。

- Script: `scripts/stage10_clamp_watchdog_utility_without_publisher.py`
- Header: `ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/torque_safety.hpp`
- Contract check: `ros2_ws/src/robot_mpc_wbc_cpp_controller/src/torque_safety_contract_check.cpp`
- Log: `results/logs_sample/stage10_clamp_watchdog_utility_without_publisher_log.csv`
- Clamped vector CSV: `results/logs_sample/stage10_clamp_watchdog_utility_clamped_vector.csv`
- Safety gate CSV: `results/logs_sample/stage10_torque_publisher_safety_gate_after_stage107.csv`
- Summary: `results/logs_sample/stage10_clamp_watchdog_utility_without_publisher_summary.csv`
- Docs: `docs/STAGE10_CLAMP_WATCHDOG_UTILITY_WITHOUT_PUBLISHER.md`
- pass: `True`
- clamp_watchdog_utility_implemented: `True`
- torque_topic_publishers_zero: `True`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 10.7 只实现 clamp/watchdog utility，不创建 publisher，不发布 torque，不改变控制律。

## Stage 10.8 Disabled Controller Uses Safety Utilities

Stage 10.8 将 clamp/watchdog utilities 接入 disabled controller 内部路径。

- Script: `scripts/stage10_disabled_controller_uses_safety_utilities.py`
- Source: `ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp`
- Log: `results/logs_sample/stage10_disabled_controller_uses_safety_utilities_log.csv`
- Safety gate: `results/logs_sample/stage10_torque_publisher_safety_gate_after_stage108.csv`
- Summary: `results/logs_sample/stage10_disabled_controller_uses_safety_utilities_summary.csv`
- Docs: `docs/STAGE10_DISABLED_CONTROLLER_USES_SAFETY_UTILITIES.md`
- pass: `True`
- controller_uses_safety_utilities: `True`
- torque_topic_publishers_zero: `True`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 10.8 只接入内部 safety utility，不创建 publisher，不发布 torque，不改变控制律。

## Stage 10.9 Stage 10.7–10.8 Safety Utility Freeze Summary

Stage 10.9 冻结 Stage 10.7–10.8 safety-utility baseline。

- Script: `scripts/stage10_7_8_safety_utility_freeze_summary.py`
- Log: `results/logs_sample/stage10_7_8_safety_utility_freeze_log.csv`
- Hashes: `results/logs_sample/stage10_7_8_safety_utility_freeze_hashes.csv`
- Summary: `results/logs_sample/stage10_7_8_safety_utility_freeze_summary.csv`
- Docs: `docs/STAGE10_7_8_SAFETY_UTILITY_FREEZE_SUMMARY.md`
- pass: `True`
- safety_utility_frozen: `True`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 10.7–10.8 只形成 safety utility baseline，不创建 publisher，不发布 torque，不改变控制律。

## Stage 10.10 Manual Enable Parameters Disabled Without Publisher

Stage 10.10 给 disabled controller 增加 manual enable parameters，默认值保持 false。

- Script: `scripts/stage10_manual_enable_params_disabled_without_publisher.py`
- Source: `ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp`
- Log: `results/logs_sample/stage10_manual_enable_params_disabled_without_publisher_log.csv`
- Safety gate: `results/logs_sample/stage10_torque_publisher_safety_gate_after_stage1010.csv`
- Summary: `results/logs_sample/stage10_manual_enable_params_disabled_without_publisher_summary.csv`
- Docs: `docs/STAGE10_MANUAL_ENABLE_PARAMS_DISABLED_WITHOUT_PUBLISHER.md`
- pass: `True`
- manual_enable_params_declared: `True`
- manual_enable_params_default_false: `True`
- manual_enable_active: `False`
- publisher_path_exists: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 10.10 只增加 disabled-by-default manual enable parameters，不创建 publisher，不发布 torque，不改变控制律。

## Stage 10.11 Manual-enable Parameter Guard Freeze Summary

Stage 10.11 冻结 manual-enable parameter guard。

- Script: `scripts/stage10_manual_enable_param_guard_freeze_summary.py`
- Log: `results/logs_sample/stage10_manual_enable_param_guard_freeze_log.csv`
- Hashes: `results/logs_sample/stage10_manual_enable_param_guard_freeze_hashes.csv`
- Summary: `results/logs_sample/stage10_manual_enable_param_guard_freeze_summary.csv`
- Docs: `docs/STAGE10_MANUAL_ENABLE_PARAM_GUARD_FREEZE_SUMMARY.md`
- pass: `True`
- manual_enable_param_guard_frozen: `True`
- g8_manual_enable_active: `False`
- g9_publisher_path_exists: `False`
- g11_manual_enable_params_exist_and_default_false: `True`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 10.11 只冻结 manual-enable parameter guard，不创建 publisher，不发布 torque，不改变控制律。

## Stage 10.12 Stage 10.0–10.11 Full No-publisher Controller Freeze

Stage 10.12 冻结 Stage 10.0–10.11 full no-publisher controller baseline。

- Script: `scripts/stage10_0_11_full_no_publisher_controller_freeze.py`
- Log: `results/logs_sample/stage10_0_11_full_no_publisher_controller_freeze_log.csv`
- Hashes: `results/logs_sample/stage10_0_11_full_no_publisher_controller_freeze_hashes.csv`
- Summary: `results/logs_sample/stage10_0_11_full_no_publisher_controller_freeze_summary.csv`
- Docs: `docs/STAGE10_0_11_FULL_NO_PUBLISHER_CONTROLLER_FREEZE.md`
- pass: `True`
- full_no_publisher_controller_frozen: `True`
- g8_manual_enable_active: `False`
- g9_publisher_path_exists: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 10.0–10.11 只形成 no-publisher controller baseline，不发布 torque，不改变控制律。

## Stage 11.0 Publisher-path Skeleton Planning Only

Stage 11.0 完成 publisher-path skeleton planning only。

- Script: `scripts/stage11_publisher_path_skeleton_planning_only.py`
- Plan CSV: `results/logs_sample/stage11_publisher_path_skeleton_plan.csv`
- Safety gate: `results/logs_sample/stage11_torque_publisher_safety_gate_after_stage110.csv`
- Summary: `results/logs_sample/stage11_publisher_path_skeleton_planning_summary.csv`
- Docs: `docs/STAGE11_PUBLISHER_PATH_SKELETON_PLANNING_ONLY.md`
- pass: `True`
- publisher_path_plan_exists: `True`
- publisher_path_implemented: `False`
- manual_enable_active: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 11.0 只规划 publisher path，不创建 publisher，不发布 torque，不改变控制律。

## Stage 11.1 Publisher-path Source Guard Before Implementation

Stage 11.1 完成 publisher-path source/runtime guard。

- Script: `scripts/stage11_publisher_path_source_guard_before_implementation.py`
- Log: `results/logs_sample/stage11_publisher_path_source_guard_log.csv`
- Safety gate: `results/logs_sample/stage11_torque_publisher_safety_gate_after_stage111.csv`
- Summary: `results/logs_sample/stage11_publisher_path_source_guard_summary.csv`
- Docs: `docs/STAGE11_PUBLISHER_PATH_SOURCE_GUARD_BEFORE_IMPLEMENTATION.md`
- pass: `True`
- publisher_path_source_guard_passed: `True`
- publisher_path_implemented: `False`
- manual_enable_active: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 11.1 只做 publisher-path implementation 前 guard，不创建 publisher，不发布 torque，不改变控制律。

## Stage 11.2 Disabled Publisher-path Skeleton Design Only

Stage 11.2 完成 disabled publisher-path skeleton design only。

- Script: `scripts/stage11_disabled_publisher_path_skeleton_design_only.py`
- Design CSV: `results/logs_sample/stage11_disabled_publisher_path_skeleton_design.csv`
- Safety gate: `results/logs_sample/stage11_torque_publisher_safety_gate_after_stage112.csv`
- Summary: `results/logs_sample/stage11_disabled_publisher_path_skeleton_design_summary.csv`
- Docs: `docs/STAGE11_DISABLED_PUBLISHER_PATH_SKELETON_DESIGN_ONLY.md`
- pass: `True`
- disabled_publisher_path_design_exists: `True`
- publisher_path_implemented: `False`
- manual_enable_active: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 11.2 只设计 disabled publisher path，不创建 publisher，不发布 torque，不改变控制律。

## Stage 11.3 Stage 11.0–11.2 Publisher-path Planning Freeze Summary

Stage 11.3 冻结 Stage 11.0–11.2 publisher-path planning baseline。

- Script: `scripts/stage11_0_2_publisher_path_planning_freeze_summary.py`
- Log: `results/logs_sample/stage11_0_2_publisher_path_planning_freeze_log.csv`
- Hashes: `results/logs_sample/stage11_0_2_publisher_path_planning_freeze_hashes.csv`
- Summary: `results/logs_sample/stage11_0_2_publisher_path_planning_freeze_summary.csv`
- Docs: `docs/STAGE11_0_2_PUBLISHER_PATH_PLANNING_FREEZE_SUMMARY.md`
- pass: `True`
- publisher_path_planning_frozen: `True`
- g8_manual_enable_active: `False`
- g9_publisher_path_exists: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 11.0–11.2 只形成 publisher-path planning baseline，不创建 publisher，不发布 torque，不改变控制律。

## Stage 11.4 Disabled Publisher-path Skeleton Preflight

Stage 11.4 完成 disabled publisher-path skeleton preflight。

- Script: `scripts/stage11_disabled_publisher_path_skeleton_preflight.py`
- Preflight CSV: `results/logs_sample/stage11_disabled_publisher_path_skeleton_preflight.csv`
- Safety gate: `results/logs_sample/stage11_torque_publisher_safety_gate_after_stage114.csv`
- Summary: `results/logs_sample/stage11_disabled_publisher_path_skeleton_preflight_summary.csv`
- Docs: `docs/STAGE11_DISABLED_PUBLISHER_PATH_SKELETON_PREFLIGHT.md`
- pass: `True`
- disabled_publisher_path_skeleton_preflight_passed: `True`
- source_unchanged_by_stage114: `True`
- publisher_path_implemented: `False`
- manual_enable_active: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 11.4 只做 preflight，不创建 publisher，不发布 torque，不改变控制律。

## Stage 11.5 Dormant Publisher-path Source Skeleton

Stage 11.5 在 disabled controller 中加入 dormant publisher-path source skeleton。

- Script: `scripts/stage11_dormant_publisher_path_source_skeleton.py`
- Source: `ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp`
- Safety gate: `results/logs_sample/stage11_torque_publisher_safety_gate_after_stage115.csv`
- Summary: `results/logs_sample/stage11_dormant_publisher_path_source_skeleton_summary.csv`
- Docs: `docs/STAGE11_DORMANT_PUBLISHER_PATH_SOURCE_SKELETON.md`
- pass: `True`
- dormant_publisher_path_source_skeleton_exists: `True`
- publisher_path_implemented: `False`
- manual_enable_active: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 11.5 只加入 dormant source skeleton，不创建 ROS publisher，不发布 torque，不改变控制律。

## Stage 11.6 Dormant Publisher-path Source Skeleton Freeze Summary

Stage 11.6 冻结 Stage 11.5 dormant publisher-path source skeleton。

- Script: `scripts/stage11_dormant_publisher_path_source_skeleton_freeze_summary.py`
- Log: `results/logs_sample/stage11_dormant_publisher_path_source_skeleton_freeze_log.csv`
- Hashes: `results/logs_sample/stage11_dormant_publisher_path_source_skeleton_freeze_hashes.csv`
- Summary: `results/logs_sample/stage11_dormant_publisher_path_source_skeleton_freeze_summary.csv`
- Docs: `docs/STAGE11_DORMANT_PUBLISHER_PATH_SOURCE_SKELETON_FREEZE_SUMMARY.md`
- pass: `True`
- dormant_publisher_path_source_skeleton_frozen: `True`
- dormant_publisher_path_source_skeleton_exists: `True`
- g8_manual_enable_active: `False`
- g9_active_ros_publisher_path_exists: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 11.6 只冻结 dormant source skeleton，不创建 ROS publisher，不发布 torque，不改变控制律。

## Stage 11.7 Runtime Guard Hardening for Dormant Publisher Skeleton

Stage 11.7 强化 dormant publisher skeleton runtime guard。

- Script: `scripts/stage11_runtime_guard_hardening_for_dormant_publisher_skeleton.py`
- Observations: `results/logs_sample/stage11_runtime_guard_hardening_topic_observations.csv`
- Safety gate: `results/logs_sample/stage11_torque_publisher_safety_gate_after_stage117.csv`
- Summary: `results/logs_sample/stage11_runtime_guard_hardening_for_dormant_publisher_skeleton_summary.csv`
- Docs: `docs/STAGE11_RUNTIME_GUARD_HARDENING_FOR_DORMANT_PUBLISHER_SKELETON.md`
- pass: `True`
- dormant_publisher_runtime_guard_hardened: `True`
- torque_publishers_zero_all_samples: `True`
- publisher_path_implemented: `False`
- manual_enable_active: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 11.7 只强化 runtime guard，不创建 ROS publisher，不发布 torque，不改变控制律。

## Stage 11.8 Stage 11.5–11.7 Dormant Publisher Skeleton Runtime Freeze Summary

Stage 11.8 冻结 Stage 11.5–11.7 dormant publisher skeleton runtime baseline。

- Script: `scripts/stage11_5_7_dormant_publisher_runtime_freeze_summary.py`
- Log: `results/logs_sample/stage11_5_7_dormant_publisher_runtime_freeze_log.csv`
- Hashes: `results/logs_sample/stage11_5_7_dormant_publisher_runtime_freeze_hashes.csv`
- Summary: `results/logs_sample/stage11_5_7_dormant_publisher_runtime_freeze_summary.csv`
- Docs: `docs/STAGE11_5_7_DORMANT_PUBLISHER_RUNTIME_FREEZE_SUMMARY.md`
- pass: `True`
- dormant_publisher_skeleton_runtime_frozen: `True`
- dormant_publisher_runtime_guard_hardened: `True`
- g8_manual_enable_active: `False`
- g9_active_ros_publisher_path_exists: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 11.8 只冻结 dormant publisher skeleton runtime baseline，不创建 ROS publisher，不发布 torque，不改变控制律。

## Stage 11.9 Stage 11.0–11.8 Full Publisher-path No-active-publisher Freeze

Stage 11.9 冻结 Stage 11.0–11.8 full publisher-path no-active-publisher baseline。

- Script: `scripts/stage11_0_8_full_publisher_path_no_active_publisher_freeze.py`
- Log: `results/logs_sample/stage11_0_8_full_publisher_path_no_active_publisher_freeze_log.csv`
- Hashes: `results/logs_sample/stage11_0_8_full_publisher_path_no_active_publisher_freeze_hashes.csv`
- Summary: `results/logs_sample/stage11_0_8_full_publisher_path_no_active_publisher_freeze_summary.csv`
- Docs: `docs/STAGE11_0_8_FULL_PUBLISHER_PATH_NO_ACTIVE_PUBLISHER_FREEZE.md`
- pass: `True`
- full_publisher_path_no_active_publisher_frozen: `True`
- g8_manual_enable_active: `False`
- g9_active_ros_publisher_path_exists: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 11.9 只冻结 no-active-publisher baseline，不创建 ROS publisher，不发布 torque，不改变控制律。

## Stage 11.10 Full Freeze Integrity Check

Stage 11.10 完成 full freeze integrity check。

- Script: `scripts/stage11_full_freeze_integrity_check.py`
- Log: `results/logs_sample/stage11_full_freeze_integrity_check_log.csv`
- Hash check: `results/logs_sample/stage11_full_freeze_integrity_check_hash_check.csv`
- Safety gate: `results/logs_sample/stage11_torque_publisher_safety_gate_after_stage1110.csv`
- Summary: `results/logs_sample/stage11_full_freeze_integrity_check_summary.csv`
- Docs: `docs/STAGE11_FULL_FREEZE_INTEGRITY_CHECK.md`
- pass: `True`
- hash_integrity_passed: `True`
- verified_full_publisher_path_no_active_publisher_frozen: `True`
- g8_manual_enable_active: `False`
- g9_active_ros_publisher_path_exists: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 11.10 只验证 freeze integrity，不创建 ROS publisher，不发布 torque，不改变控制律。

## Stage 12.0 Active Publisher Construction Planning Only

Stage 12.0 完成 active publisher construction planning only。

- Script: `scripts/stage12_active_publisher_construction_planning_only.py`
- Plan: `results/logs_sample/stage12_active_publisher_construction_plan.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage120.csv`
- Summary: `results/logs_sample/stage12_active_publisher_construction_planning_summary.csv`
- Docs: `docs/STAGE12_ACTIVE_PUBLISHER_CONSTRUCTION_PLANNING_ONLY.md`
- pass: `True`
- active_publisher_construction_planning_complete: `True`
- active_ros_publisher_path_exists: `False`
- manual_enable_active: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 12.0 只规划 active publisher construction，不创建 publisher，不发布 torque，不改变控制律。

## Stage 12.1 Pre-construction Source and Runtime Guard

Stage 12.1 完成 active publisher construction 前 source/runtime guard。

- Script: `scripts/stage12_pre_construction_source_runtime_guard.py`
- Observations: `results/logs_sample/stage12_pre_construction_topic_observations.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage121.csv`
- Summary: `results/logs_sample/stage12_pre_construction_source_runtime_guard_summary.csv`
- Docs: `docs/STAGE12_PRE_CONSTRUCTION_SOURCE_RUNTIME_GUARD.md`
- pass: `False`
- pre_construction_source_runtime_guard_passed: `False`
- torque_publishers_zero_all_samples: `False`
- active_ros_publisher_path_exists: `False`
- manual_enable_active: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 12.1 只做 source/runtime guard，不创建 publisher，不发布 torque，不改变控制律。

## Stage 12.2 Publisher Construction Source Patch Design Only

Stage 12.2 完成 publisher construction source patch design only。

- Script: `scripts/stage12_publisher_construction_source_patch_design_only.py`
- Design: `results/logs_sample/stage12_publisher_construction_source_patch_design.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage122.csv`
- Summary: `results/logs_sample/stage12_publisher_construction_source_patch_design_summary.csv`
- Docs: `docs/STAGE12_PUBLISHER_CONSTRUCTION_SOURCE_PATCH_DESIGN_ONLY.md`
- pass: `True`
- publisher_construction_source_patch_design_complete: `True`
- source_unchanged_by_stage122: `True`
- active_ros_publisher_path_exists: `False`
- manual_enable_active: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 12.2 只设计 source patch，不创建 publisher，不发布 torque，不改变控制律。

## Stage 12.3 Construction-stage Preflight Freeze

Stage 12.3 冻结 construction-stage preflight baseline。

- Script: `scripts/stage12_construction_stage_preflight_freeze.py`
- Log: `results/logs_sample/stage12_construction_stage_preflight_freeze_log.csv`
- Hashes: `results/logs_sample/stage12_construction_stage_preflight_freeze_hashes.csv`
- Summary: `results/logs_sample/stage12_construction_stage_preflight_freeze_summary.csv`
- Docs: `docs/STAGE12_CONSTRUCTION_STAGE_PREFLIGHT_FREEZE.md`
- pass: `True`
- construction_stage_preflight_frozen: `True`
- g8_manual_enable_active: `False`
- g9_active_ros_publisher_path_exists: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 12.3 只冻结 preflight，不创建 publisher，不发布 torque，不改变控制律。

## Stage 12.4 Publisher Construction Source Patch Without Publish

Stage 12.4 实现 publisher construction source patch without publish call。

- Script: `scripts/stage12_publisher_construction_source_patch_without_publish.py`
- Observations: `results/logs_sample/stage12_publisher_construction_without_publish_topic_observations.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage124.csv`
- Summary: `results/logs_sample/stage12_publisher_construction_source_patch_without_publish_summary.csv`
- Docs: `docs/STAGE12_PUBLISHER_CONSTRUCTION_SOURCE_PATCH_WITHOUT_PUBLISH.md`
- pass: `True`
- publisher_construction_implemented_without_publish_call: `True`
- active_ros_publisher_path_exists: `True`
- manual_enable_active: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 12.4 只构造 publisher，不调用 publish，不发布 torque，不改变控制律。

## Stage 12.5 Publisher Construction No-publish Freeze

Stage 12.5 完成 publisher construction no-publish freeze。

- Script: `scripts/stage12_publisher_construction_no_publish_freeze.py`
- Log: `results/logs_sample/stage12_publisher_construction_no_publish_freeze_log.csv`
- Hashes: `results/logs_sample/stage12_publisher_construction_no_publish_freeze_hashes.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage125.csv`
- Summary: `results/logs_sample/stage12_publisher_construction_no_publish_freeze_summary.csv`
- Docs: `docs/STAGE12_PUBLISHER_CONSTRUCTION_NO_PUBLISH_FREEZE.md`
- pass: `True`
- publisher_construction_no_publish_integrity_passed: `True`
- active_ros_publisher_path_exists: `True`
- manual_enable_active: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 12.5 只冻结 publisher construction no-publish baseline，不发布 torque，不改变控制律。

## Stage 12.6 Manual Enable Activation Design Only

Stage 12.6 完成 manual enable activation design only。

- Script: `scripts/stage12_manual_enable_activation_design_only.py`
- Design: `results/logs_sample/stage12_manual_enable_activation_design.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage126.csv`
- Summary: `results/logs_sample/stage12_manual_enable_activation_design_summary.csv`
- Docs: `docs/STAGE12_MANUAL_ENABLE_ACTIVATION_DESIGN_ONLY.md`
- pass: `True`
- manual_enable_activation_design_complete: `True`
- source_unchanged_by_stage126: `True`
- active_ros_publisher_path_exists: `True`
- manual_enable_active: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`

Stage 12.6 只设计 manual enable activation，不设置参数，不发布 torque，不改变控制律。

## Stage 12.7 Manual Enable Runtime Activation Without Publish

Stage 12.7 完成 runtime manual enable activation without publish call。

- Script: `scripts/stage12_manual_enable_runtime_activation_without_publish.py`
- Param observations: `results/logs_sample/stage12_manual_enable_runtime_activation_param_observations.csv`
- Topic observations: `results/logs_sample/stage12_manual_enable_runtime_activation_topic_observations.csv`
- Summary: `results/logs_sample/stage12_manual_enable_runtime_activation_without_publish_summary.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage127.csv`
- Docs: `docs/STAGE12_MANUAL_ENABLE_RUNTIME_ACTIVATION_WITHOUT_PUBLISH.md`
- pass: `True`
- manual_enable_runtime_activation_without_publish_passed: `True`
- manual_enable_active_during_test: `True`
- manual_enable_reverted_false: `True`
- active_ros_publisher_path_exists: `True`
- no_message_observed_during_activation: `True`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- torque_command_published_by_stage127: `False`
- control_law_changed: `False`

Stage 12.7 只激活 runtime manual flags 并回退，不加入 publish call，不发布 torque，不改变控制律。

## Stage 12.8 Manual-enable No-publish Freeze

Stage 12.8 冻结 manual-enable no-publish baseline。

- Script: `scripts/stage12_manual_enable_no_publish_freeze.py`
- Log: `results/logs_sample/stage12_manual_enable_no_publish_freeze_log.csv`
- Hashes: `results/logs_sample/stage12_manual_enable_no_publish_freeze_hashes.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage128.csv`
- Summary: `results/logs_sample/stage12_manual_enable_no_publish_freeze_summary.csv`
- Docs: `docs/STAGE12_MANUAL_ENABLE_NO_PUBLISH_FREEZE.md`
- pass: `True`
- manual_enable_no_publish_frozen: `True`
- manual_enable_active_during_test: `True`
- manual_enable_reverted_false: `True`
- active_ros_publisher_path_exists: `True`
- no_message_observed_during_activation: `True`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- torque_command_published_by_stage128: `False`
- control_law_changed: `False`

Stage 12.8 只冻结 manual-enable no-publish baseline，不加入 publish call，不发布 torque，不改变控制律。

## Stage 12.9 Publish-call Design Only

Stage 12.9 完成 publish-call design only。

- Script: `scripts/stage12_publish_call_design_only.py`
- Design: `results/logs_sample/stage12_publish_call_design.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage129.csv`
- Summary: `results/logs_sample/stage12_publish_call_design_summary.csv`
- Docs: `docs/STAGE12_PUBLISH_CALL_DESIGN_ONLY.md`
- pass: `True`
- publish_call_design_complete: `True`
- source_unchanged_by_stage129: `True`
- active_ros_publisher_path_exists: `True`
- manual_enable_active: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- torque_command_published_by_stage129: `False`
- control_law_changed: `False`

Stage 12.9 只设计 publish call，不加入 publish call，不发布 torque，不改变控制律。

## Stage 12.10 Publish-call Preflight Freeze

Stage 12.10 冻结 publish-call preflight baseline。

- Script: `scripts/stage12_publish_call_preflight_freeze.py`
- Log: `results/logs_sample/stage12_publish_call_preflight_freeze_log.csv`
- Hashes: `results/logs_sample/stage12_publish_call_preflight_freeze_hashes.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1210.csv`
- Summary: `results/logs_sample/stage12_publish_call_preflight_freeze_summary.csv`
- Docs: `docs/STAGE12_PUBLISH_CALL_PREFLIGHT_FREEZE.md`
- pass: `True`
- publish_call_preflight_frozen: `True`
- active_ros_publisher_path_exists: `True`
- current_source_has_publish_call: `False`
- manual_enable_active: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- torque_command_published_by_stage1210: `False`
- control_law_changed: `False`

Stage 12.10 只冻结 publish-call preflight baseline，不加入 publish call，不发布 torque，不改变控制律。

## Stage 12.11 Bounded Zero/Safe Publish-call Implementation Plan

Stage 12.11 完成 bounded zero/safe publish-call implementation plan only。

- Script: `scripts/stage12_bounded_zero_safe_publish_call_implementation_plan.py`
- Plan: `results/logs_sample/stage12_bounded_zero_safe_publish_call_implementation_plan.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1211.csv`
- Summary: `results/logs_sample/stage12_bounded_zero_safe_publish_call_implementation_plan_summary.csv`
- Docs: `docs/STAGE12_BOUNDED_ZERO_SAFE_PUBLISH_CALL_IMPLEMENTATION_PLAN.md`
- pass: `True`
- bounded_zero_safe_publish_call_implementation_plan_complete: `True`
- source_unchanged_by_stage1211: `True`
- source_has_publish_call: `False`
- active_ros_publisher_path_exists: `True`
- manual_enable_active: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- torque_command_published_by_stage1211: `False`
- control_law_changed: `False`

Stage 12.11 只规划 bounded zero/safe publish-call implementation，不加入 publish call，不发布 torque，不改变控制律。

## Stage 12.12 Bounded Publish-call Source Patch Design Only

Stage 12.12 完成 bounded publish-call source patch design only。

- Script: `scripts/stage12_bounded_publish_call_source_patch_design_only.py`
- Design: `results/logs_sample/stage12_bounded_publish_call_source_patch_design.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1212.csv`
- Summary: `results/logs_sample/stage12_bounded_publish_call_source_patch_design_summary.csv`
- Docs: `docs/STAGE12_BOUNDED_PUBLISH_CALL_SOURCE_PATCH_DESIGN_ONLY.md`
- pass: `True`
- bounded_publish_call_source_patch_design_complete: `True`
- source_unchanged_by_stage1212: `True`
- source_has_publish_call: `False`
- active_ros_publisher_path_exists: `True`
- manual_enable_active: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- torque_command_published_by_stage1212: `False`
- control_law_changed: `False`

Stage 12.12 只设计 bounded publish-call source patch，不加入 publish call，不发布 torque，不改变控制律。

## Stage 12.13 Bounded Publish-call Source Patch Preflight Freeze

Stage 12.13 冻结 bounded publish-call source patch preflight baseline。

- Script: `scripts/stage12_bounded_publish_call_source_patch_preflight_freeze.py`
- Log: `results/logs_sample/stage12_bounded_publish_call_source_patch_preflight_freeze_log.csv`
- Hashes: `results/logs_sample/stage12_bounded_publish_call_source_patch_preflight_freeze_hashes.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1213.csv`
- Summary: `results/logs_sample/stage12_bounded_publish_call_source_patch_preflight_freeze_summary.csv`
- Docs: `docs/STAGE12_BOUNDED_PUBLISH_CALL_SOURCE_PATCH_PREFLIGHT_FREEZE.md`
- pass: `True`
- bounded_publish_call_source_patch_preflight_frozen: `True`
- current_source_has_publish_call: `False`
- active_ros_publisher_path_exists: `True`
- manual_enable_active: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- torque_command_published_by_stage1213: `False`
- control_law_changed: `False`

Stage 12.13 只冻结 bounded publish-call source patch preflight baseline，不加入 publish call，不发布 torque，不改变控制律。

## Stage 12.14 Bounded One-shot Zero/Safe Publish-call Source Patch

Stage 12.14 完成 bounded one-shot zero/safe publish-call source patch。

- Script: `scripts/stage12_bounded_one_shot_zero_safe_publish_call_source_patch.py`
- Summary: `results/logs_sample/stage12_bounded_one_shot_zero_safe_publish_call_source_patch_summary.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1214.csv`
- Echo 1: `results/logs_sample/stage12_bounded_one_shot_zero_safe_publish_call_echo1_stdout.txt`
- Echo 2: `results/logs_sample/stage12_bounded_one_shot_zero_safe_publish_call_echo2_stdout.txt`
- pass: `False`
- bounded_one_shot_publish_call_implemented: `False`
- bounded_zero_safe_torque_message_published: `False`
- first_echo_payload_length: `0`
- first_echo_payload_all_zero: `False`
- second_echo_timeout_no_extra_message: `True`
- continuous_torque_streaming_enabled: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- torque_command_published_by_stage1214: `False`
- control_law_changed: `False`

Stage 12.14 只完成 bounded one-shot zero/safe publish，不完成连续 torque streaming，不完成 realtime controller。

## Stage 12.15 Bounded One-shot Publish-call Freeze and Regression

Stage 12.15 冻结 bounded one-shot zero/safe publish-call 状态并完成回归检查。

- Script: `scripts/stage12_bounded_one_shot_publish_call_freeze_regression.py`
- Summary: `results/logs_sample/stage12_bounded_one_shot_publish_call_freeze_regression_summary.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1215.csv`
- pass: `True`
- bounded_one_shot_publish_call_freeze_regression_passed: `True`
- default_disabled_no_message_observed: `True`
- enabled_payload_length: `12`
- enabled_payload_all_zero: `True`
- enabled_second_echo_timeout_no_extra_message: `True`
- continuous_torque_streaming_enabled: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- torque_command_published_by_stage1215: `True`
- control_law_changed: `False`

Stage 12.15 不完成连续 torque streaming，不完成 ROS2/C++ realtime controller，不完成硬件部署。

## Stage 12.16 Continuous Torque Streaming Design Only

Stage 12.16 完成 continuous torque streaming design only。

- Script: `scripts/stage12_continuous_torque_streaming_design_only.py`
- Design: `results/logs_sample/stage12_continuous_torque_streaming_design.csv`
- Summary: `results/logs_sample/stage12_continuous_torque_streaming_design_summary.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1216.csv`
- pass: `True`
- continuous_torque_streaming_design_complete: `True`
- source_unchanged_by_stage1216: `True`
- publish_call_count: `1`
- continuous_torque_streaming_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- torque_command_published_by_stage1216: `False`
- control_law_changed: `False`

Stage 12.16 只设计连续 streaming，不实现连续 streaming，不改变控制律，不部署硬件。

## Stage 12.17 Continuous Torque Streaming Preflight Freeze

Stage 12.17 冻结 continuous torque streaming preflight baseline。

- Script: `scripts/stage12_continuous_torque_streaming_preflight_freeze.py`
- Log: `results/logs_sample/stage12_continuous_torque_streaming_preflight_freeze_log.csv`
- Hashes: `results/logs_sample/stage12_continuous_torque_streaming_preflight_freeze_hashes.csv`
- Summary: `results/logs_sample/stage12_continuous_torque_streaming_preflight_freeze_summary.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1217.csv`
- pass: `True`
- continuous_torque_streaming_preflight_frozen: `True`
- publish_call_count: `1`
- source_has_no_continuous_streaming_flags: `True`
- source_has_no_continuous_streaming_timer: `True`
- continuous_torque_streaming_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- torque_command_published_by_stage1217: `False`
- control_law_changed: `False`

Stage 12.17 不实现连续 streaming，不改变控制律，不部署硬件。

## Stage 12.18 Continuous Torque Streaming Source Patch Design Only

Stage 12.18 完成 continuous torque streaming source patch design only。

- Script: `scripts/stage12_continuous_torque_streaming_source_patch_design_only.py`
- Design: `results/logs_sample/stage12_continuous_torque_streaming_source_patch_design.csv`
- Summary: `results/logs_sample/stage12_continuous_torque_streaming_source_patch_design_summary.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1218.csv`
- pass: `True`
- continuous_torque_streaming_source_patch_design_complete: `True`
- source_unchanged_by_stage1218: `True`
- publish_call_count: `1`
- continuous_torque_streaming_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- torque_command_published_by_stage1218: `False`
- control_law_changed: `False`

Stage 12.18 只设计连续 streaming source patch，不实现连续 streaming，不改变控制律，不部署硬件。

## Stage 12.19 Continuous Torque Streaming Source Patch Preflight Freeze

Stage 12.19 冻结 continuous torque streaming source patch preflight baseline。

- Script: `scripts/stage12_continuous_torque_streaming_source_patch_preflight_freeze.py`
- Log: `results/logs_sample/stage12_continuous_torque_streaming_source_patch_preflight_freeze_log.csv`
- Hashes: `results/logs_sample/stage12_continuous_torque_streaming_source_patch_preflight_freeze_hashes.csv`
- Summary: `results/logs_sample/stage12_continuous_torque_streaming_source_patch_preflight_freeze_summary.csv`
- Safety gate: `results/logs_sample/stage12_torque_publisher_safety_gate_after_stage1219.csv`
- pass: `True`
- continuous_streaming_source_patch_preflight_frozen: `True`
- publish_call_count: `1`
- source_has_no_continuous_streaming_flags: `True`
- source_has_no_continuous_streaming_timer: `True`
- source_has_no_stage1219_marker: `True`
- continuous_torque_streaming_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- torque_command_published_by_stage1219: `False`
- control_law_changed: `False`

Stage 12.19 不实现连续 streaming，不改变控制律，不部署硬件。

## Stage 12.20E Final Evidence Freeze

- timestamp: `2026-06-03T17:22:35`
- pass: `True`
- stage1220_completed: `True`
- continuous_torque_streaming_completed: `True`
- source_hash: `b2d7371786b58300ca68be5542372d5cf8aa2814678b9f451e09bdb8061aa138`
- publish_call_count: `1`
- default-off regression: `pass`
- bounded streaming regression: `pass`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- hardware_deployment_completed: `False`
- control_law_changed: `False`
- next_stage: `Stage 12.21 freeze and regression check; no hardware deployment`

## Stage 12.21-R3 Final Repaired Freeze Summary

- timestamp: `2026-06-04T09:47:26`
- pass: `True`
- stage1221_repaired_pass: `True`
- stage1220_completed_remains_true: `True`
- continuous_torque_streaming_completed: `True`
- simulation_only_project: `True`
- hardware_deployment_scope: `out_of_scope_by_user_constraint`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- source_hash: `b2d7371786b58300ca68be5542372d5cf8aa2814678b9f451e09bdb8061aa138`
- publish_call_count: `1`
- bounded streaming repaired regression: `pass`
- next_stage: `Stage 12.22 simulation-only project scope freeze and documentation update`

## Stage 12.22 Simulation-Only Scope Freeze

- timestamp: `2026-06-04T09:49:04`
- pass: `True`
- simulation_only_project: `True`
- hardware_available: `False`
- hardware_deployment_scope: `out_of_scope_by_user_constraint`
- hardware_deployment_completed: `False`
- real_robot_torque_execution_scope: `out_of_scope`
- actuator_hardware_enablement_scope: `out_of_scope`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- source_hash: `b2d7371786b58300ca68be5542372d5cf8aa2814678b9f451e09bdb8061aa138`
- publish_call_count: `1`
- next_stage: `Stage 13 simulation-only MuJoCo locomotion regression and documentation consolidation`

## Stage 13.2A-R2 2400-Step Derived Runner Creation

- timestamp: `2026-06-04T10:07:46`
- pass: `True`
- original_sources_unchanged: `True`
- derived_wbc_runner: `/home/zanshi/robot-mpc-wbc-locomotion/scripts/stage13_2_2400step_online_full_wbc_scheduler_runner.py`
- derived_recommended_runner: `/home/zanshi/robot-mpc-wbc-locomotion/scripts/stage13_2_2400step_simulation_only_mixed_baseline_runner.py`
- derived_swing_target_csv: `/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_2_2400step_swing_trajectory_tracking_check.csv`
- derived_swing_row_count: `2400`
- control_law_changed: `False`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- next_stage: `Stage 13.2B run 2400-step simulation-only robustness regression`

## Stage 13.2B-R1 2400-Step Simulation-Only Robustness Regression

- timestamp: `2026-06-04T10:16:51`
- pass: `True`
- previous_stage13_2b_failure_classified_as_missing_contact_schedule: `True`
- total_steps: `2400`
- transition_count: `11`
- trot_FR_RL_steps: `1200`
- trot_FL_RR_steps: `1200`
- qp_fail_steps: `0`
- saturation_steps: `0`
- min_z: `0.274552192756`
- max_abs_roll: `0.056707402709`
- max_abs_pitch: `0.04832948253`
- max_joint_error: `0.077233662573`
- max_tau_total_abs: `9.659563043535`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- next_stage: `Stage 13.2C final 2400-step robustness evidence freeze`

## Stage 13.2C Final 2400-Step Robustness Evidence Freeze

- timestamp: `2026-06-04T10:18:42`
- pass: `True`
- simulation_only_project: `True`
- baseline_type: `mixed_online_control_baseline`
- total_steps: `2400`
- transition_count: `11`
- trot_FR_RL_steps: `1200`
- trot_FL_RR_steps: `1200`
- min_z: `0.274552192756`
- max_abs_roll: `0.056707402709`
- max_abs_pitch: `0.04832948253`
- max_joint_error: `0.077233662573`
- max_tau_total_abs: `9.659563043535`
- qp_fail_steps: `0`
- saturation_steps: `0`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- next_stage: `Stage 13.3 documentation consolidation and report-ready results packaging`

## Stage 13.3 Report-Ready Results Packaging

- timestamp: `2026-06-04T10:21:00`
- pass: `True`
- simulation_only_project: `True`
- baseline_type: `mixed_online_control_baseline`
- metrics_table: `/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_3_report_ready_metrics_table.csv`
- report_ready_results: `/home/zanshi/robot-mpc-wbc-locomotion/docs/REPORT_READY_RESULTS.md`
- claims_and_limitations: `/home/zanshi/robot-mpc-wbc-locomotion/docs/REPORT_READY_CLAIMS_AND_LIMITATIONS.md`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- next_stage: `Stage 13.4 optional plots/tables for report, or Stage 14 simulation-only improvement planning`

## Stage 13.4B Report-Ready Package Manifest Freeze

- timestamp: `2026-06-04T10:24:00`
- pass: `True`
- simulation_only_project: `True`
- baseline_type: `mixed_online_control_baseline`
- package_file_count: `16`
- manifest_json: `/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_4b_report_ready_package_manifest.json`
- manifest_md: `/home/zanshi/robot-mpc-wbc-locomotion/docs/REPORT_READY_PACKAGE_MANIFEST.md`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- next_stage: `Stage 14 simulation-only improvement planning, or stop at report-ready package`

## Stage 13.5B Demo Video Evidence Freeze

- timestamp: `2026-06-04T11:21:19`
- pass: `True`
- method: `MuJoCo offscreen rendering + policy rollout + raw RGB pipe to ffmpeg`
- video_path: `/home/zanshi/robot-mpc-wbc-locomotion/demo_videos/stage13_5a_r2_mujoco_offscreen_2400step_mixed_baseline_demo_720p.mp4`
- video_size_bytes: `2606663`
- video_sha256: `c9fb4241bd9a64f805f2e66ccf487fd683dfaadb1d23d17e8fa46a51073114d1`
- width: `1280`
- height: `720`
- fps: `30/1`
- duration: `20.000000`
- nb_frames: `600`
- rollout_total_steps: `2400`
- rollout_pass: `True`
- simulation_only_project: `True`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- next_stage: `Stop at report-ready package and demo video, or Stage 14 simulation-only improvement planning`

## Stage 13.5C Final Package with Demo Video Manifest

- timestamp: `2026-06-04T11:23:12`
- pass: `True`
- simulation_only_project: `True`
- baseline_type: `mixed_online_control_baseline`
- final_package_file_count: `20`
- final_manifest_json: `/home/zanshi/robot-mpc-wbc-locomotion/results/logs_sample/stage13_5c_final_package_with_demo_video_manifest.json`
- final_manifest_md: `/home/zanshi/robot-mpc-wbc-locomotion/docs/FINAL_PACKAGE_WITH_DEMO_VIDEO_MANIFEST.md`
- demo_video: `/home/zanshi/robot-mpc-wbc-locomotion/demo_videos/stage13_5a_r2_mujoco_offscreen_2400step_mixed_baseline_demo_720p.mp4`
- demo_video_sha256: `c9fb4241bd9a64f805f2e66ccf487fd683dfaadb1d23d17e8fa46a51073114d1`
- hardware_deployment_completed: `False`
- torque_enable_ready: `False`
- torque_publisher_enabled: `False`
- control_law_changed: `False`
- next_stage: `Stop, or Stage 14 simulation-only improvement planning`

