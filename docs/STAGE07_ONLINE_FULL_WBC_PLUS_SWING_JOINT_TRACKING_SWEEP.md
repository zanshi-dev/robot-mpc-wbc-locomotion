# Stage 7：Online Full WBC Plus Swing Joint Tracking Sweep

## 状态

sweep 已完成。

结论：直接叠加 full WBC torque 与 swing joint PD torque 的方案当前不通过。

## 背景

上一版 combined online test 使用：

wbc_torque_scale = 1.0

swing_pd_torque_scale = 0.5

target_scale = 0.6

结果失败：

max_abs_roll = 0.370811239659

max_joint_error = 0.269034444734

pass = False

失败原因不是 torque saturation，而是 full WBC torque 与 swing joint PD target 之间存在冲突，导致姿态和 joint error 失控。

## Sweep 脚本

scripts/stage07_online_full_wbc_plus_swing_joint_tracking_sweep.py

## 输出文件

results/logs_sample/stage07_online_full_wbc_plus_swing_joint_tracking_sweep.csv

## Sweep 参数

WBC_TORQUE_SCALE_LIST = [0.0, 0.25, 0.50, 0.75]

SWING_PD_TORQUE_SCALE_LIST = [0.25, 0.50, 0.75]

TARGET_SCALE_LIST = [0.45, 0.60]

total cases = 24

## 总体结果

num_cases = 24

pass_cases = 4

pass_margin_cases = 4

## 推荐项

wbc_torque_scale = 0.0

swing_pd_torque_scale = 0.75

target_scale = 0.45

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

roll_margin_to_0p20 = 0.118949020419

max_abs_pitch = 0.038526145564

pitch_margin_to_0p20 = 0.161473854436

z_margin_to_0p22 = 0.053560102250

max_joint_error = 0.056916933566

max_swing_joint_error = 0.056916933566

max_stance_joint_error = 0.040626466563

max_tau_wbc_abs = 0.000000000000

max_tau_swing_pd_abs = 6.927913461938

max_tau_total_raw_abs = 6.927913461938

max_tau_total_abs = 6.927913461938

max_cmd_step_jump_norm = 19.218700982481

max_cmd_step_jump_abs = 8.105769115036

max_dyn_res_norm = 8.317511092371e-08

max_stance_acc_res_norm = 3.277658348817e-09

max_swing_acc_error_norm = 4.473491801157e-01

qp_fail_steps = 0

saturation_steps = 0

pass = True

pass_margin = True

recommended = True

## 关键发现

所有通过项的 wbc_torque_scale 都是 0.0。

也就是说，本轮通过结果实际是 swing joint PD-only，而不是 full WBC + swing joint tracking 的成功耦合。

wbc_torque_scale >= 0.25 时均未通过。

典型失败：

wbc_torque_scale = 0.25, swing_pd_torque_scale = 0.75, target_scale = 0.45

max_joint_error = 0.086846043753

pass = False

wbc_torque_scale = 0.50, swing_pd_torque_scale = 0.75, target_scale = 0.45

max_joint_error = 0.101080010489

pass = False

wbc_torque_scale = 0.75, swing_pd_torque_scale = 0.25, target_scale = 0.45

max_abs_roll = 3.138252100892

pass = False

## 结论

直接线性叠加 full WBC torque 与 swing joint PD torque 的方案当前被拒绝。

当前可保留两个已通过 baseline：

1. online full WBC scheduler recommended run
2. online swing joint tracking recommended test

但二者不能直接以 torque sum 方式合并。

## 原因判断

full WBC QP 当前已经包含 swing acceleration task，同时 swing joint PD 又试图跟踪 joint target。

二者在 torque 层直接叠加时会出现目标冲突：

1. full WBC torque 改变 base / stance / swing 的整体动力学响应
2. swing PD torque 强制跟踪 IK joint target
3. 当前没有任务层优先级或 nullspace 投影
4. 当前也没有 stance-only / swing-only torque 分配
5. 因此直接 torque sum 会放大 joint error 和 roll

## 当前推荐处理

不要继续使用 direct full WBC torque + swing joint PD torque sum 作为默认方案。

下一步建议改为：

stance-only WBC torque + swing joint PD torque

即：

1. stance legs 使用 WBC torque
2. swing legs 使用 swing joint PD torque
3. 不让 WBC torque 直接控制 swing legs
4. 不让 swing PD 直接控制 stance legs
5. 仍保留 torque limit 和 low-pass smoothing

## 下一步建议

建议脚本：

scripts/stage07_online_stance_wbc_plus_swing_pd_proto.py

目标：

1. 读取 scheduler mode
2. 每步在线求解 full WBC QP
3. WBC torque 只作用于 stance legs
4. swing joint PD torque 只作用于 swing legs
5. 使用 target_scale = 0.45
6. 使用 swing_pd_torque_scale = 0.75
7. sweep stance_wbc_scale
8. 检查 base_z、roll、pitch、joint error、torque saturation

建议输出：

results/logs_sample/stage07_online_stance_wbc_plus_swing_pd_proto_log.csv

results/logs_sample/stage07_online_stance_wbc_plus_swing_pd_proto_summary.csv
