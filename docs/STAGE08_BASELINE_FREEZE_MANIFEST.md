# Stage 8.9 Python Runtime-safe Baseline Freeze Manifest

## 一、冻结结论

Stage 8.0–8.8 已完成 Python runtime interface hardening 第一轮闭环。

当前冻结 baseline：

    Stage 8 runtime-safe adapter-backed Stage 7 mixed online control baseline

推荐运行入口：

    /usr/bin/python3 scripts/stage08_adapter_backed_stage07_recommended_test.py

## 二、冻结范围

本次冻结包含：

- runtime interface contract check
- runtime adapter module
- zero-control-change regression guard
- adapter-backed Stage 7 A/B regression
- runtime mapping duplication audit
- active dependency path triage
- active-path hard-coded leg order refactor
- recommended runtime-safe entrypoint promotion
- Stage 8.0–8.7 中文汇总文档

## 三、核心文件

### 推荐入口

- scripts/stage08_adapter_backed_stage07_recommended_test.py

### 原始 Stage 7 baseline 参考入口

- scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py

### Runtime adapter

- scripts/common/go1_runtime_interface.py

### Stage 8 汇总文档

- docs/STAGE08_0_7_RUNTIME_INTERFACE_HARDENING_SUMMARY.md
- docs/STAGE08_RECOMMENDED_RUNTIME_SAFE_ENTRYPOINT.md

### Stage 8 冻结 manifest

- docs/STAGE08_BASELINE_FREEZE_MANIFEST.md

## 四、关键验证结果

- qpos_roundtrip_max_abs = 0.0
- qvel_roundtrip_max_abs = 0.0
- torque_roundtrip_max_abs = 0.0
- Stage 8.3 A/B regression pass = True
- Stage 8.6 active high-severity findings after refactor = 0
- Stage 8.7 recommended entrypoint pass = True
- Stage 8.8 summary pass = True

## 五、控制边界

当前控制律没有改变。

当前控制器仍是 Stage 7 mixed online control baseline：

1. stance legs 使用 posture PD；
2. stance legs 叠加 scaled stance WBC feedforward；
3. swing legs 使用 online swing target PD；
4. WBC torque 不直接作用 swing legs；
5. swing PD 不直接作用 stance legs。

## 六、明确未完成项

本 baseline freeze 不代表以下内容完成：

- pure full WBC locomotion
- WBC QP 内部直接接入 online swing target task
- swing target 到 acceleration reference 的在线转换
- touchdown / liftoff contact feedback
- base velocity tracking
- forward velocity command
- full 3D centroidal MPC
- EKF
- ROS2/C++ real-time controller
- OSQP warm-start / real-time timing guarantee
- hardware deployment

## 七、后续使用规则

后续 Stage 8 或 Stage 9 工作默认从该入口开始：

    /usr/bin/python3 scripts/stage08_adapter_backed_stage07_recommended_test.py

若要进入 ROS2/C++，第一步应做 interface mirror，不改控制律。

若要继续优化 locomotion，必须先保持该 frozen baseline 可回归。
