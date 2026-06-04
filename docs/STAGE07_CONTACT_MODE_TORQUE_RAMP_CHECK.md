# Stage 7：Contact Mode Torque Ramp Check

## 状态

通过。

## 目标

在 contact mode 动态切换前，检查 torque ramp 是否可以降低模式切换时的单步 torque jump。

该检查基于前一步结论：

直接 contact mode switching 会产生过大的 torque jump，必须加入 ramp 或 smoothing。

## 输入文件

results/logs_sample/stage07_contact_schedule_wbc_qp.csv

## 输出文件

results/logs_sample/stage07_contact_mode_torque_ramp_check.csv

## 当前 scale

all_stance scale = 1.0

trot_FR_RL scale = 0.6

trot_FL_RR scale = 1.0

## 测试 ramp_steps

5, 10, 20, 40

## 判定阈值

step_jump_norm <= 8.0

step_jump_max_abs <= 5.0

## 检查结果

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

## 推荐值

recommended_ramp_steps = 5

原因：

1. ramp_steps = 5 已满足所有 transition 的 step jump 阈值
2. ramp_steps = 5 延迟最小
3. 更大的 ramp_steps 更平滑，但会引入更长模式切换滞后

## 最大跳变来源

最大 direct transition：

trot_FR_RL -> trot_FL_RR

direct_jump_norm = 18.895751942469

direct_jump_max_abs = 10.594245657447

使用 ramp_steps = 5 后：

step_jump_norm = 3.779150388494

step_jump_max_abs = 2.118849131489

低于阈值。

## 结论

contact mode transition 必须使用 torque ramp。

当前推荐：

ramp_steps = 5

动态切换时应使用：

tau_cmd[k] = tau_prev + alpha * (tau_target - tau_prev)

其中 alpha 每步增加 1 / ramp_steps。

## 下一步

进入 Stage 7 下一小步：

实现带 ramp 的 contact mode sequence MuJoCo 短时测试。

建议 sequence：

all_stance -> trot_FR_RL -> all_stance -> trot_FL_RR -> all_stance

每段保持 300 steps。

transition ramp_steps = 5。

输出文件：

results/logs_sample/stage07_contact_mode_sequence_ramp_test_summary.csv
