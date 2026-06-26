# robot-mpc-wbc-locomotion

四足机器人 MPC-WBC 运动控制仿真项目。项目基于 MuJoCo 和 Pinocchio 搭建四足机器人仿真控制链路，围绕步态调度、接触规划、摆腿轨迹、接触力规划、WBC/QP、`J^T f` 力矩映射和力矩安全限幅进行验证。

本项目将四足机器人运动控制链路拆解为若干可验证模块，并在 MuJoCo 仿真环境中逐步验证各模块之间的数据流、力矩生成路径、稳定性边界和问题来源。

目前项目已经完成从基础 PD/WBC 仿真控制，到 MPC/WBC 候选力矩接入，再到稳定化主控模式的仿真验证。

---

## 1. 项目内容

项目主要包含以下部分：

* MuJoCo 四足机器人仿真；
* Pinocchio 运动学与动力学计算；
* 步态调度与接触规划；
* 摆腿轨迹生成；
* 接触力 QP；
* WBC/QP 候选力矩计算；
* `J^T f` 接触力到关节力矩映射；
* 力矩限幅和安全过滤；
* 多阶段仿真运行、指标统计和证据归档。

整体控制链路可以概括为：

```text
MuJoCo 当前状态
-> 状态映射
-> Pinocchio 计算运动学 / 动力学量
-> 步态调度与接触规划
-> PD / WBC / QP / MPC 候选控制
-> 力矩安全限幅
-> MuJoCo 执行器输入
-> 下一步仿真状态
```

项目的核心亮点是：没有直接将 MPC/WBC 候选力矩包装为稳定主控结论，而是先记录 `primary_mpc_wbc` 直接主控模式的失败，再通过失败诊断引入斜坡过渡、尺度限制、站立腿姿态残差和在线 WBC 残差，最终得到 `stabilized_primary_mpc_wbc` 在固定仿真场景下的闭环运行证据。

---

## 2. 控制链路演进

### 2.1 基线控制

项目早期使用较保守的仿真控制结构：

```text
站立腿姿态 PD
+ 站立腿 WBC 前馈力矩
+ 摆动腿轨迹 PD
+ 力矩安全限幅
```

该结构作为后续 MPC/WBC 候选力矩接入的稳定基线。

---

### 2.2 MPC/WBC 候选力矩辅助注入

在候选力矩阶段，MPC/WBC 不直接接管整机控制，而是作为辅助项注入：

```text
基线力矩
+ 注入尺度 * MPC/WBC 候选力矩
-> 力矩安全过滤
-> MuJoCo
```

这一阶段主要验证：

* MPC/WBC 候选力矩能否生成；
* `J^T f` 映射是否合理；
* 候选力矩能否进入 MuJoCo 执行器；
* 不同注入尺度对稳定性和速度跟踪有什么影响。

在这一阶段，`scale=0.010` 是当前仿真设置下较合理的低尺度候选项，但它只代表固定仿真条件下的推荐结果，不代表真实机器人鲁棒性。

---

### 2.3 primary_mpc_wbc 直接主控尝试

阶段 25 中，项目进一步把 MPC/WBC 候选力矩从“辅助注入”推进到“主控链路”。

直接主控形式为：

```text
primary_mpc_wbc =
    stance_mask * tau_candidate
    + 摆动腿 PD
    + 力矩安全限幅
```

该模式已经实际进入 MuJoCo 力矩闭环，但标称 2400 步冒烟测试没有通过稳定性边界。

主要现象是：

```text
qp_fail_steps = 0
saturation_steps = 555
max_abs_roll = 0.4887
max_abs_pitch = 0.3562
```

这说明问题不是 QP 求解失败，而是直接把候选力矩作为主控力矩后，姿态控制和力矩饱和没有处理好。

---

### 2.4 stabilized_primary_mpc_wbc 稳定化主控

针对直接主控失败的问题，项目实现了稳定化主控模式：

```text
stabilized_primary_mpc_wbc =
    带斜坡过渡和尺度限制的站立腿候选力矩
    + 站立腿姿态残差
    + 在线 WBC 残差
    + 摆动腿 PD
    + 力矩安全限幅
```

默认参数为：

```text
stabilized_primary_scale = 0.05
stabilized_primary_ramp_steps = 600
stabilized_posture_residual_scale = 1.0
stabilized_wbc_residual_scale = 1.0
```

在标称 2400 步仿真中，该模式通过了冒烟测试：

```text
pass = True
qp_fail_steps = 0
saturation_steps = 0
max_abs_roll = 0.0882
max_abs_pitch = 0.0507
max_tau_total_abs = 10.8906
torque_limit = 23.7
```

因此，当前项目可以说明：在固定仿真设置下，`stabilized_primary_mpc_wbc` 已经形成一条可运行的仅仿真 MPC-WBC 主控闭环。

---

## 3. 主要验证过程

| 阶段    | 内容               | 结论                                    |
| ----- | ---------------- | ------------------------------------- |
| 阶段 13 | 在线 WBC 与摆腿轨迹验证   | 形成后续仿真运行所需的基础控制数据                     |
| 阶段 14 | MPC/WBC 候选力矩接入   | 候选力矩路径可以进入 MuJoCo 执行器                 |
| 阶段 15 | 工程化整理与证据归档       | 补充文档、日志和复现入口                          |
| 阶段 16 | README 与公开材料同步   | 整理仓库入口和证据索引                           |
| 阶段 17 | 保守仿真运行审计         | 候选路径可在保守设置下运行                         |
| 阶段 18 | 速度跟踪指标补齐         | 基线控制器在当前设置下速度跟踪更好                     |
| 阶段 19 | 候选力矩尺度扫描         | `scale=0.010` 是较合理的低尺度候选项             |
| 阶段 20 | 推荐尺度可复现性审计       | `scale=0.010` 的结果可重复                  |
| 阶段 21 | 局部扰动审计           | 推荐关系在局部扰动下保持                          |
| 阶段 22 | qvel 初始速度扰动尝试    | 长期汇总指标未形成可观测变化                        |
| 阶段 23 | 扰动不可观测原因分析       | 问题来自汇总指标不敏感                           |
| 阶段 24 | 短时扰动敏感指标审计       | 短时指标能看到扰动，但不能升级鲁棒性结论                  |
| 阶段 25 | 稳定化 MPC-WBC 主控闭环 | `stabilized_primary_mpc_wbc` 通过标称冒烟仿真 |

---

## 4. 关键结果

### 4.1 候选力矩辅助注入阶段

MPC/WBC 候选力矩可以进入 MuJoCo 仿真链路，并通过不同注入尺度进行稳定性和速度跟踪审计。

当前固定仿真设置下：

* 低尺度候选力矩注入可以稳定运行；
* `scale=0.010` 是较合理的低尺度候选项；
* 该结论只适用于当前仿真设置；
* 不能据此声明真实机器人鲁棒性。

---

### 4.2 直接主控阶段

`primary_mpc_wbc` 已经进入 MuJoCo 力矩闭环，但没有通过稳定性边界。

诊断结果：

```text
failure_class = posture_limit_violation_with_torque_saturation_no_qp_failure
qp_fail_steps = 0
saturation_steps = 555
```

结论是：直接主控失败不是因为 QP 求解失败，而是力矩组合缺少稳定化机制。

---

### 4.3 稳定化主控阶段

`stabilized_primary_mpc_wbc` 在标称 2400 步仿真中通过冒烟测试。

关键指标：

```text
pass = True
qp_fail_steps = 0
saturation_steps = 0
max_abs_roll = 0.0882
max_abs_pitch = 0.0507
max_tau_total_abs = 10.8906
torque_limit = 23.7
```

该结果说明稳定化后的 MPC-WBC 主控链路在当前仿真条件下可运行。

---

### 4.4 Stage 26.1 控制模式小规模回归矩阵

在 Stage 25 的基础上，项目补充 9-case 控制模式回归矩阵，用于比较 baseline、`primary_mpc_wbc` 和 `stabilized_primary_mpc_wbc` 在固定 MuJoCo 仿真设置下的行为差异。

| 控制模式 | case 数 | evidence pass | stability pass |
|---|---:|---:|---:|
| baseline | 3 | 3 | 3 |
| `primary_mpc_wbc` | 3 | 3 | 0 |
| `stabilized_primary_mpc_wbc` | 3 | 3 | 3 |

`primary_mpc_wbc` 直接主控能够进入 MuJoCo 力矩闭环，但未通过稳定性检查；典型指标为 `saturation_steps = 555`、`max_abs_roll = 0.4887`、`max_abs_pitch = 0.3562`，且 `qp_fail_steps = 0`。这说明失败主要来自姿态边界和力矩安全边界，而不是 QP 求解失败。

`stabilized_primary_mpc_wbc` 在相同测试设置下全部通过，`qp_fail_steps = 0`、`saturation_steps = 0`、`max_abs_roll = 0.0882`、`max_abs_pitch = 0.0507`。

该阶段只支持固定 MuJoCo 仿真设置下的控制模式回归结论，不支持真实机器人部署、复杂地形鲁棒性、外力扰动鲁棒性或完整工程级 MPC-WBC locomotion controller 结论。

## 5. 快速复现

### 5.1 环境准备

建议使用 Python 3.10 或更高版本。

```bash
python3 --version
pip install -r requirements.txt
```

如果本地已经安装 MuJoCo、Pinocchio 和 OSQP，可以直接运行对应脚本。

---

### 5.2 阶段 25 稳定化主控验证

实现 stabilized primary 控制模式：

```bash
python3 scripts/stage25_5_implement_stabilized_primary_mpc_wbc_mode.py
```

运行 stabilized primary 冒烟仿真：

```bash
python3 scripts/stage25_6_run_stabilized_primary_mpc_wbc_smoke_rollout.py
python3 scripts/stage25_6_validate_stabilized_primary_mpc_wbc_smoke_rollout.py
```

冻结阶段 25 证据：

```bash
python3 scripts/stage25_7_freeze_primary_controller_closure_evidence.py
```

关键输出文件：

```text
results/logs_sample/stage25_5_stabilized_primary_mpc_wbc_mode_summary.json
results/logs_sample/stage25_6_stabilized_primary_mpc_wbc_smoke_summary.json
results/logs_sample/stage25_7_primary_controller_closure_evidence_freeze_summary.json
docs/STAGE25_7_PRIMARY_CONTROLLER_CLOSURE_EVIDENCE_FREEZE.md
```

---

### 5.3 Stage 26.1 控制模式小规模回归矩阵

运行回归矩阵：

    python3 scripts/stage26_1_run_primary_controller_regression_matrix.py

主要结果文件：

    results/logs_sample/stage26_1_primary_controller_regression_matrix.csv
    results/logs_sample/stage26_1_primary_controller_regression_summary.json
    docs/STAGE26_1_PRIMARY_CONTROLLER_REGRESSION_MATRIX.md

## 6. 目录结构

```text
robot-mpc-wbc-locomotion/
├── docs/
│   ├── ARTIFACT_INDEX.md
│   └── STAGE25_7_PRIMARY_CONTROLLER_CLOSURE_EVIDENCE_FREEZE.md
├── results/
│   └── logs_sample/
├── scripts/
│   ├── stage25_5_stabilized_primary_mpc_wbc_runner.py
│   ├── stage25_6_run_stabilized_primary_mpc_wbc_smoke_rollout.py
│   └── stage25_7_freeze_primary_controller_closure_evidence.py
├── src/
├── README.md
└── requirements.txt
```

---

## 7. 当前可以说明的内容

当前仓库支持以下结论：

* 已完成 MuJoCo 四足机器人仿真控制链路；
* 已完成 Pinocchio 运动学 / 动力学候选链路；
* 已完成步态调度、接触规划、摆腿轨迹和力矩安全限幅模块；
* 已完成接触力 QP 和 `J^T f` 候选力矩验证；
* 已完成 MPC/WBC 候选力矩辅助注入验证；
* 已完成候选力矩尺度扫描和推荐尺度可复现性审计；
* 已完成局部扰动和扰动可观测性审计；
* 已完成 direct `primary_mpc_wbc` 的执行验证和失败诊断；
* 已完成 `stabilized_primary_mpc_wbc` 的标称 2400 步冒烟仿真；
* 稳定化主控版本中记录到 `qp_fail_steps = 0`、`saturation_steps = 0`。

---

## 8. 当前不能说明的内容

当前仓库不支持以下结论：

* 不说明真实机器人部署已经完成；
* 不说明硬件力矩使能已经完成；
* 不说明 ROS torque publisher 可以直接用于真实硬件；
* 不说明 direct/full `primary_mpc_wbc` 已经稳定；
* 不说明 full MPC/WBC torque 可以无残差替代基线控制器；
* 不说明 `scale=0.010` 已通过可观测扰动鲁棒性验证；
* 不说明 MPC/WBC 已通过复杂地形、外力扰动或真实机器人实验验证；
* 不说明 `stabilized_primary_mpc_wbc` 已达到工程级成熟控制器。

---

## 9. 项目边界

本项目完成的是一条仅仿真的四足机器人运动控制验证链路。项目从基础 PD/WBC 控制出发，逐步接入 MPC/WBC 候选力矩，并进一步推进到 stabilized primary 控制模式。

当前最重要的结论是：

```text
stabilized_primary_mpc_wbc 在固定 MuJoCo 仿真设置下通过标称 2400 步冒烟仿真。
```

这个结果说明稳定化后的 MPC-WBC 主控链路在当前仿真条件下可运行，但不等价于真实机器人闭环，也不等价于复杂地形或外力扰动鲁棒性。
