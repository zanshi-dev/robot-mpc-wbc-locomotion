# Stage 7：Contact Schedule WBC/QP Scaled Support Test

## 状态

通过。

## 背景

原始 contact schedule-aware WBC/QP 静态支撑测试中：

all_stance 通过。

trot_FL_RR 通过。

trot_FR_RL 失败。

失败原因：

trot_FR_RL 在 scale = 1.0 时 max_abs_roll = 0.156525005128，超过阈值 0.15。

## 调参结果

对 trot_FR_RL 进行 WBC torque scale sweep：

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

推荐 scale：

trot_FR_RL scale = 0.6

## Scaled Support Test 设置

模式缩放：

all_stance scale = 1.0

trot_FR_RL scale = 0.6

trot_FL_RR scale = 1.0

控制形式：

tau_total = tau_pd + scale * tau_wbc

控制参数：

kp = 80.0

kd = 2.0

torque_limit = 23.7

sim_steps = 1000

## Scaled Support Test 结果

### all_stance

final_z = 0.290673824396

min_z = 0.284805846483

max_abs_roll = 0.053689475648

roll_margin_to_0p15 = 0.096310524352

max_abs_pitch = 0.029696786699

max_tau_total_abs = 8.858349940928

saturation_steps = 0

pass = True

pass_margin = True

### trot_FR_RL

wbc_scale = 0.6

final_z = 0.295056299833

min_z = 0.284715134142

max_abs_roll = 0.110752061094

roll_margin_to_0p15 = 0.039247938906

max_abs_pitch = 0.052921077590

max_tau_total_abs = 9.331342107139

saturation_steps = 0

pass = True

pass_margin = True

### trot_FL_RR

wbc_scale = 1.0

final_z = 0.300769804656

min_z = 0.284805846483

max_abs_roll = 0.133384221160

roll_margin_to_0p15 = 0.016615778840

max_abs_pitch = 0.070571666592

max_tau_total_abs = 11.454092417624

saturation_steps = 0

pass = True

pass_margin = True

## 结论

Scaled contact schedule WBC support test 已通过。

当前静态单模式建议使用：

all_stance scale = 1.0

trot_FR_RL scale = 0.6

trot_FL_RR scale = 1.0

三种模式均满足：

1. pass = True
2. pass_margin = True
3. saturation_steps = 0
4. max_abs_roll < 0.15
5. max_abs_pitch < 0.15
6. min_z > 0.22

## 当前边界

该测试仍是静态单模式测试，不是动态步态切换。

当前不能宣称已经完成 trot closed-loop locomotion。

## 下一步

进入 Stage 7 下一小步：

实现 contact mode transition sanity check。

目标：

1. 在离线层面检查 all_stance、trot_FR_RL、trot_FL_RR 三种 torque 之间的切换跳变
2. 输出相邻模式 torque jump norm
3. 检查是否需要 torque ramp / smoothing
4. 保存到 results/logs_sample/stage07_contact_mode_transition_check.csv
