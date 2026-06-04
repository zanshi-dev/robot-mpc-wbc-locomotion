# Stage 7：WBC Variant 对比

## 状态

完成。

## 对比目标

比较 Stage 7 当前两个 WBC/QP variant：

1. base_wrench_qp
2. posture_regularized_qp

判断哪个版本作为后续 Stage 7 的默认基准。

## 对比文件

results/logs_sample/stage07_wbc_variant_comparison.csv

## Variant 1：base_wrench_qp

QP pass = True

support pass = True

margin pass = True

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

## Variant 2：posture_regularized_qp

QP pass = True

support pass = True

margin pass = False

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

## 结论

当前 Stage 7 默认基准选择：

base_wrench_qp

原因：

1. base_wrench_qp 同时通过 QP、support test 和 margin check
2. posture_regularized_qp 虽然 support pass，但 margin_check_failed
3. posture_regularized_qp 的 max_abs_roll 更接近 0.15 阈值
4. posture_regularized_qp 的 max_tau_total_abs 更高
5. 当前没有证据表明 posture regularization 改善支撑稳定性

## 后续约定

后续 Stage 7 默认使用：

results/logs_sample/stage07_wbc_base_wrench_qp.csv

默认 torque source：

stage07_wbc_base_wrench_qp

posture_regularized_qp 暂时保留为实验 variant，不作为默认控制输入。

## 下一步

进入 Stage 7 总结与接口固化。

目标：

1. 整理 Stage 7 已完成内容
2. 明确 base_wrench_qp 为默认基准
3. 明确后续完整 WBC/QP 应从 base wrench tracking 扩展
4. 更新 PROJECT_STATUS.md
