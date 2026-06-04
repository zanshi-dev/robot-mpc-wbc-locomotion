# Stage 6：QP 接触力到关节力矩映射

## 状态

通过。

## 输入文件

results/logs_sample/stage05_standing_contact_force_qp.csv

输入为 Stage 5 standing contact force QP 输出。

接触力顺序：

FR, FL, RR, RL

CSV 列：

leg, fx, fy, fz

## 输出文件

results/logs_sample/stage06_qp_force_to_actuator_torque.csv

## 符号约定

Stage 5 QP 输出的接触力记为 f_qp。

MuJoCo actuator torque 使用：

actuator_tau = - J^T f_qp

符号 sanity check 结果：

plus:
initial_z = 0.28480584648330304
final_z   = 0.27428167433940703
delta_z   = -0.010524172143896005

minus:
initial_z = 0.28480584648330304
final_z   = 0.29351710400099223
delta_z   = 0.008711257517689197

结论：minus 符号更符合支撑方向，因此后续使用 actuator_tau = - J^T f_qp。

## 数值结果

tau_norm     = 11.567004356004
tau_max_abs  = 5.309218454936
torque_limit = 23.700000000000
limit_pass   = True

每条腿 actuator torque：

FR = [ 2.454883448,  0.000000000, 5.119924306]
FL = [-2.489474011, -0.000000000, 5.192066657]
RR = [ 2.511054984,  0.000000000, 5.237076104]
RL = [-2.545645547, -0.000000000, 5.309218455]

## 结论

Stage 5 QP 接触力可以安全映射为 12 维 MuJoCo actuator torque。

最大关节力矩小于 Go1 torque limit：

5.309218454936 < 23.7

Stage 6 离线 QP force to actuator torque 验证完成。

## 下一步

进入 Stage 6 的短时 MuJoCo 支撑闭环测试。

测试形式：

tau_total = tau_pd + tau_qp_actuator

其中：

tau_qp_actuator = - J^T f_qp

所有 actuator torque 需要裁剪到 [-23.7, 23.7]。
