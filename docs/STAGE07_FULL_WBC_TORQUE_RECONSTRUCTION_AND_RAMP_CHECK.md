# Stage 7：Full WBC Torque Reconstruction and Ramp Check

## 状态

通过。

## 目标

检查 full WBC swing acceleration task QP 输出的 torque 是否满足：

1. torque limit
2. 与 contact schedule WBC torque 的差异是否可控
3. 两种 trot mode 之间直接切换是否需要 smoothing
4. ramp 后单步 torque jump 是否满足阈值

## 输入文件

results/logs_sample/stage07_full_wbc_torque_reconstruction_check.csv

## 输出文件

results/logs_sample/stage07_full_wbc_torque_ramp_check.csv

## Torque Reconstruction Check

### trot_FR_RL

max_abs_tau_full_wbc = 10.545880364253

max_abs_tau_contact_wbc = 10.638319002741

tau_diff_norm_vs_contact_wbc = 1.390773536447

tau_diff_max_abs_vs_contact_wbc = 0.732158458909

torque_limit_pass = True

### trot_FL_RR

max_abs_tau_full_wbc = 10.480313206115

max_abs_tau_contact_wbc = 10.594245657447

tau_diff_norm_vs_contact_wbc = 1.375153606606

tau_diff_max_abs_vs_contact_wbc = 0.729723929991

torque_limit_pass = True

## Direct Mode Transition Jump

trot_FR_RL -> trot_FL_RR:

jump_norm = 23.730004894309

jump_max_abs = 10.823012441254

need_smoothing = True

trot_FL_RR -> trot_FR_RL:

jump_norm = 23.730004894309

jump_max_abs = 10.823012441254

need_smoothing = True

## Ramp Check

阈值：

step_jump_norm <= 8.0

step_jump_max_abs <= 5.0

### ramp_steps = 3

ramp_all_pass = True

max_step_jump_norm = 7.910001631436

max_step_jump_abs = 3.607670813751

### ramp_steps = 5

ramp_all_pass = True

max_step_jump_norm = 4.746000978862

max_step_jump_abs = 2.164602488251

### ramp_steps = 10

ramp_all_pass = True

max_step_jump_norm = 2.373000489431

max_step_jump_abs = 1.082301244125

### ramp_steps = 20

ramp_all_pass = True

max_step_jump_norm = 1.186500244715

max_step_jump_abs = 0.541150622063

### ramp_steps = 40

ramp_all_pass = True

max_step_jump_norm = 0.593250122358

max_step_jump_abs = 0.270575311031

## 推荐配置

recommended_ramp_steps = 3

## 结论

full WBC 单模式 torque 合法：

1. torque 未超过 23.7 Nm
2. 与 contact schedule WBC torque 差异较小
3. dynamics / stance / swing task 残差在前序 QP 中已通过

但两种 trot mode 之间直接切换 torque jump 过大，必须使用 ramp smoothing。

推荐最小 ramp_steps = 3。

如果进入 MuJoCo 闭环，建议优先使用更保守的：

ramp_steps = 5

原因：

ramp_steps = 3 虽然通过阈值，但 step_jump_norm = 7.91，接近阈值 8.0。

ramp_steps = 5 的 step_jump_norm = 4.746，更稳妥。

## 下一步

进入 full WBC torque closed-loop 前置测试。

建议脚本：

scripts/stage07_full_wbc_torque_sequence_support_test.py

目标：

1. 使用 full WBC torque
2. sequence = trot_FR_RL -> trot_FL_RR -> trot_FR_RL
3. 使用 ramp_steps = 5
4. MuJoCo 中做短时 torque support test
5. 检查 base_z、roll、pitch、torque saturation

输出文件：

results/logs_sample/stage07_full_wbc_torque_sequence_support_test_log.csv

results/logs_sample/stage07_full_wbc_torque_sequence_support_test_summary.csv
