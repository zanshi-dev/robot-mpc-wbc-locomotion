# Stage 7：Online Swing Trajectory Tracking Check

## 状态

通过。

## 目标

验证 online swing trajectory memory proto 生成的 foot target 是否可以通过站立 pose 附近的小步 IK/QP 转换为连续 joint target。

该测试暂不接 MuJoCo torque 闭环，也不接 full WBC torque。

## 输入文件

results/logs_sample/stage07_online_swing_trajectory_memory_proto.csv

## 输出文件

results/logs_sample/stage07_online_swing_trajectory_tracking_check.csv

results/logs_sample/stage07_online_swing_trajectory_tracking_check_summary.csv

## 方法

每个 step：

1. 读取 memory swing trajectory 的 foot target
2. 在当前 joint command pose 下计算 foot Jacobian
3. 以 12 维 actuated dq 为优化变量
4. swing leg 高权重跟踪 foot target
5. stance leg 中等权重保持 foot target
6. 加入 dq regularization 和 dq smooth term
7. 限制每步 dq
8. 积分得到 q_cmd
9. 检查 foot tracking error、dq step、q delta

## QP 参数

MAX_DQ_STEP = 0.015

MAX_Q_DELTA_FROM_STANDING = 0.35

W_SWING = 200.0

W_STANCE = 50.0

W_REG = 1e-3

W_SMOOTH = 10.0

## 结果

input_csv = results/logs_sample/stage07_online_swing_trajectory_memory_proto.csv

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

## 结论

online swing trajectory tracking check 通过。

memory swing trajectory 可以被小步 IK/QP 转换为连续 joint target：

1. foot tracking error 很小
2. swing foot error 很小
3. 每步 dq 远低于限制
4. joint target 相对 standing pose 偏移可控
5. QP failure = 0

该结果说明 online swing trajectory 可以进入下一步：接入 MuJoCo joint target tracking 或接入 full WBC swing task。

## 当前边界

该测试仍不是完整动态 trot locomotion。

尚未完成：

1. MuJoCo joint target tracking 闭环
2. full WBC 中使用该 swing target
3. swing target 到 acceleration task 的在线转换
4. touchdown/liftoff contact feedback
5. base velocity tracking
6. forward velocity command
7. ROS2/C++ 实时实现

## 下一步

建议做 online swing joint target tracking support test。

建议脚本：

scripts/stage07_online_swing_joint_target_tracking_support_test.py

目标：

1. 读取 online swing trajectory tracking check 的 q target
2. 使用 scheduler 推荐配置
3. MuJoCo 中用 PD 跟踪 q target
4. 暂不叠加 full WBC torque
5. 检查 base_z、roll、pitch、joint error、torque saturation

输出：

results/logs_sample/stage07_online_swing_joint_target_tracking_support_test_log.csv

results/logs_sample/stage07_online_swing_joint_target_tracking_support_test_summary.csv
