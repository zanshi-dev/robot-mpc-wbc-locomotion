# Stage 7：Contact Mode Transition Sanity Check

## 状态

完成。

## 目标

检查 contact schedule-aware WBC/QP 在不同 contact mode 之间切换时的 torque 跳变。

检查对象：

1. all_stance -> trot_FR_RL
2. trot_FR_RL -> all_stance
3. all_stance -> trot_FL_RR
4. trot_FL_RR -> all_stance
5. trot_FR_RL -> trot_FL_RR
6. trot_FL_RR -> trot_FR_RL

## 输入文件

results/logs_sample/stage07_contact_schedule_wbc_qp.csv

## 输出文件

results/logs_sample/stage07_contact_mode_transition_check.csv

## 当前使用的 scale

all_stance scale = 1.0

trot_FR_RL scale = 0.6

trot_FL_RR scale = 1.0

## 判定阈值

torque jump norm warning threshold = 8.0

torque jump max warning threshold = 5.0

只要任一条件触发，即判定需要 smoothing：

1. jump_norm > 8.0
2. jump_max_abs > 5.0

## 检查结果

all_stance -> trot_FR_RL：

jump_norm = 8.327068144804

jump_max_abs = 5.237904619970

need_smoothing = True

trot_FR_RL -> all_stance：

jump_norm = 8.327068144804

jump_max_abs = 5.237904619970

need_smoothing = True

all_stance -> trot_FL_RR：

jump_norm = 11.463539646901

jump_max_abs = 5.356341037477

need_smoothing = True

trot_FL_RR -> all_stance：

jump_norm = 11.463539646901

jump_max_abs = 5.356341037477

need_smoothing = True

trot_FR_RL -> trot_FL_RR：

jump_norm = 18.895751942469

jump_max_abs = 10.594245657447

need_smoothing = True

trot_FL_RR -> trot_FR_RL：

jump_norm = 18.895751942469

jump_max_abs = 10.594245657447

need_smoothing = True

## 结论

所有 contact mode transition 都触发 smoothing 需求。

当前不应直接执行动态 contact switching。

必须先加入 torque ramp 或 low-pass smoothing，再进行动态切换测试。

## 下一步

实现 torque ramp transition 离线检查。

建议文件：

scripts/stage07_contact_mode_torque_ramp_check.py

输出文件：

results/logs_sample/stage07_contact_mode_torque_ramp_check.csv

建议 ramp_steps：

5, 10, 20, 40

检查指标：

1. 每步 torque jump norm
2. 每步 torque jump max abs
3. 是否低于阈值
4. 推荐最小 ramp_steps
