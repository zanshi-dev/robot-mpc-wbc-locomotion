# robot-mpc-wbc-locomotion

<!-- STAGE15_README_ENTRY_BEGIN -->

## 项目边界与复现入口

本仓库是一个 Go1 风格四足机器人的 simulation-only MPC/WBC 运动控制原型。

当前项目边界：

- MPC 作为 planning layer，用于生成 contact force reference 或 contact force candidate。
- MPC 不直接输出最终 joint torque。
- WBC/QP 或 J^T f 映射层负责把 contact force reference / candidate 转换为 joint torque candidate。
- 当前冻结稳定基线为 mixed_online_control_baseline。
- 当前稳定控制结构为：stance posture PD + scaled stance WBC feedforward + memory-based swing target PD + torque safety filter。

本仓库不声明：

- 已完成真实机器人部署。
- 已完成 actuator enablement。
- 已完成真实机器人 joint torque 执行。
- torque_enable_ready=True。
- 已完成 realtime hardware controller。

当前证据支持：

- MuJoCo / Pinocchio simulation-only locomotion baseline。
- MPC contact-force planning demo。
- WBC/QP 与 J^T f torque-candidate 验证。
- ROS2/C++ disabled-controller dry-run 证据。
- C++ gait scheduler / swing trajectory / torque safety filter 模块测试。
- report-ready 结果日志与 MuJoCo offscreen-rendered demo video 证据。

### 核心复现入口

从仓库根目录运行：

    bash scripts/stage15_3_reproduce_core_results.sh

该脚本复现当前 report-ready 证据链：

    repo hygiene audit
    -> base velocity tracking MPC demo
    -> MPC rollout validation
    -> ROS2/C++ controller validation
    -> summary log

期望最终标志：

    stage15_3_result: pass

关键日志：

    results/logs_sample/stage15_3_reproduce_core_results.log
    results/logs_sample/stage15_3_reproduce_core_results_summary.txt

<!-- STAGE15_README_ENTRY_END -->


Go1 风格四足机器人运动控制仿真项目。项目聚焦 **MuJoCo 仿真、Pinocchio 运动学/动力学、MPC/WBC 候选力矩、ROS2/C++ 工程化测试和结果证据归档**。

本仓库当前定位为：**仅限仿真验证的四足机器人控制链路工程项目**。项目不声明真实机器人部署，不声明已具备力矩使能条件，也不声明完整 MPC-WBC 闭环稳定行走已经完成。

---

## 1. 项目定位

本项目用于学习和展示四足机器人运动控制系统的核心链路：

```text
MuJoCo 仿真状态
-> 状态映射
-> Pinocchio 运动学/动力学计算
-> 步态调度与接触规划
-> PD / WBC / QP / MPC 候选控制链路
-> 接触力到关节力矩候选映射
-> 力矩安全限幅
-> MuJoCo 仿真验证与结果归档
```

当前最稳定的控制基线仍然是 `mixed_online_control_baseline`：

```text
站立腿姿态 PD
+ 缩放后的站立腿 WBC 前馈
+ 基于记忆目标的摆动腿 PD
```

Stage 15/16 新增内容主要是工程证据链：C++ 测试、接触力约束、Pinocchio `J^T f` 候选力矩、MuJoCo joint/actuator 兼容性审计、bounded torque smoke test、公开文档同步和 artifact index。

---

## 2. 当前可以声明的内容

当前仓库支持以下说法：

- 已完成 MuJoCo 四足机器人仿真链路的基础验证；
- 已完成 Pinocchio 运动学/动力学相关候选链路；
- 已完成步态调度、接触规划、摆腿轨迹和力矩安全限幅等控制模块；
- 已完成 ROS2/C++ 控制算法模块的 `colcon build/test` 工程化验证；
- 已完成 C++ contact force QP demo，用于验证接触模式、支撑腿法向力、摆动腿零接触力和摩擦约束；
- 已完成 contact force 到 torque candidate 的 dry-run 和 alpha sweep；
- 已完成 Pinocchio foot Jacobian 下的 `J^T f` torque candidate 验证；
- 已完成 MuJoCo joint/actuator compatibility audit；
- 已完成 bounded MuJoCo torque smoke test 和 short-horizon policy comparison；
- 已完成 Stage 15 总结报告、公开文档同步和 artifact index。

完整证据索引见：

```text
docs/ARTIFACT_INDEX.md
```

---

## 3. 当前不能声明的内容

当前仓库不支持以下说法：

- 不声明真实机器人部署；
- 不声明已具备力矩使能条件；
- 不声明 `torque_enable_ready=True`；
- 不声明 ROS torque publisher 可以直接用于真实硬件；
- 不声明实时硬件控制器已经完成；
- 不声明完整 MPC-WBC closed-loop locomotion controller 已经完成；
- 不声明 Stage 15 的 bounded torque smoke test 证明了稳定行走；
- 不声明 MPC/WBC 已通过完整 locomotion 对照实验证明优于 baseline。

更准确的表述是：

> 项目完成了仅限仿真验证的四足机器人运动控制链路工程化升级，包括 ROS2/C++ 测试、contact force QP、Pinocchio `J^T f` 候选力矩、MuJoCo actuator compatibility、bounded torque smoke test、结果归档和公开文档同步。

---

## 4. 技术栈

| 模块 | 说明 |
|---|---|
| MuJoCo | 机器人仿真环境和 actuator command smoke test |
| Pinocchio | 运动学、Jacobian 和 `J^T f` 候选力矩计算 |
| OSQP | Python 侧 QP 求解与 MPC/QP 原型验证 |
| NumPy / SciPy sparse | 数值计算与稀疏矩阵处理 |
| ROS2 Jazzy | ROS2/C++ package、节点结构和构建测试 |
| C++17 | 控制算法模块、GTest、contact force QP demo |
| Python | 仿真脚本、验证脚本、日志生成和文档同步 |

---

## 5. 控制链路概览

### 5.1 基础控制链路

```text
MuJoCo 当前状态
-> 状态读取与 MuJoCo-Pinocchio 映射
-> 步态调度器
-> 接触规划器
-> 摆腿轨迹生成器
-> PD / WBC / QP 候选控制
-> 关节力矩候选
-> 力矩安全限幅
-> MuJoCo 推进下一步仿真
```

### 5.2 mixed baseline

当前稳定基线是：

```text
站立腿姿态 PD
+ 小比例站立腿 WBC 前馈
+ 基于记忆目标的摆动腿 PD
```

该基线的作用：

- 站立腿姿态 PD 提供基础稳定性；
- WBC 前馈提供小比例动力学补偿；
- 摆动腿 PD 跟踪记忆摆腿目标；
- 力矩安全限幅避免候选力矩越界；
- 后续 MPC/WBC 候选链路都以该基线作为参照，不直接替代它。

### 5.3 Stage 15 候选力矩链路

Stage 15 新增的候选力矩链路可以概括为：

```text
contact force candidate
-> Pinocchio foot Jacobian
-> J^T f torque candidate
-> MuJoCo joint/actuator mapping
-> bounded low-alpha actuator command
-> short-horizon smoke test
```

这条链路证明候选力矩路径可以被审计和短时域测试，但不等价于完整稳定 locomotion controller。

---

## 6. Stage 15/16 升级摘要

| 阶段 | 内容 | 当前状态 |
|---|---|---|
| Stage 15.1 | ROS2/C++ control algorithms 接入 CMake/GTest | 完成 |
| Stage 15.2 | C++ contact force QP demo | 完成 |
| Stage 15.3 | contact force -> nominal torque candidate dry-run | 完成 |
| Stage 15.4 | Pinocchio Jacobian candidate rollout | 完成 |
| Stage 15.5 | model readiness audit | 完成 |
| Stage 15.6 | real-model / model-metadata Jacobian candidate rollout | 完成 |
| Stage 15.7 | MuJoCo candidate compatibility audit | 完成 |
| Stage 15.8 | bounded MuJoCo torque smoke test | 完成 |
| Stage 15.9 | `J^T f` candidate low-alpha MuJoCo injection | 完成 |
| Stage 15.10 | short-horizon policy comparison | 完成 |
| Stage 15.11 | Stage 15 summary report | 完成 |
| Stage 16.1 | public docs sync | 完成 |
| Stage 16.2 | artifact index | 完成 |


---

## 7. 关键目录

```text
robot-mpc-wbc-locomotion/
├── assets/                         # MuJoCo / robot model assets
├── docs/                           # 技术文档与阶段报告
├── results/logs_sample/            # 验证日志、JSON、CSV 结果
├── ros2_ws/                        # ROS2 工作区
│   └── src/robot_mpc_wbc_cpp_controller/
├── scripts/                        # Python / shell 验证脚本
├── README.md
├── PROJECT_STATUS.md
└── requirements.txt
```

重点文件：

```text
docs/ARTIFACT_INDEX.md
docs/STAGE15_UPGRADE_SUMMARY.md
docs/ONE_PAGE_TECHNICAL_REPORT.md
results/logs_sample/
```

---

## 8. ROS2/C++ 控制算法模块

ROS2/C++ package：

```text
ros2_ws/src/robot_mpc_wbc_cpp_controller/
```

已纳入 CMake/GTest 的模块包括：

- gait scheduler；
- swing trajectory；
- torque safety filter；
- contact force QP demo。

验证命令：

```bash
bash scripts/stage15_1_validate_ros2_cpp_controller.sh
bash scripts/stage15_2_validate_contact_force_qp.sh
```

验证目标：

```text
colcon build pass
colcon test pass
GTest pass
validation log archived
```

---

## 9. MuJoCo / Pinocchio 候选链路

Stage 15 中，项目逐步验证了：

```text
contact force candidate
-> Pinocchio foot Jacobian
-> J^T f torque candidate
-> MuJoCo joint/actuator compatibility
-> bounded MuJoCo actuator command smoke test
```

相关验证脚本：

```text
scripts/stage15_4_validate_pinocchio_jacobian_candidate_rollout.sh
scripts/stage15_5_validate_model_readiness_audit.sh
scripts/stage15_6_validate_real_model_jacobian_candidate_rollout.sh
scripts/stage15_7_validate_mujoco_candidate_compatibility_audit.sh
scripts/stage15_8_validate_mujoco_torque_smoke_test.sh
scripts/stage15_9_validate_mujoco_jtf_candidate_injection.sh
scripts/stage15_10_validate_mujoco_torque_smoke_policy_comparison.sh
```

这些脚本只支持短时域、低幅值、工程验证性质的结论，不支持稳定行走结论。

---

## 10. 结果与日志

所有阶段性结果归档在：

```text
results/logs_sample/
```

主要结果类型：

- `.log`：终端验证日志；
- `.json`：机器可读 summary / validation summary；
- `.csv`：rollout 或 validation 表格结果。

证据索引：

```bash
bash scripts/stage16_2_validate_artifact_index.sh
```

通过标志：

```text
stage16_2_result: pass
```

---

## 11. 推荐审阅顺序

建议按以下顺序查看项目：

1. `README.md`
2. `docs/ONE_PAGE_TECHNICAL_REPORT.md`
3. `docs/STAGE15_UPGRADE_SUMMARY.md`
4. `docs/ARTIFACT_INDEX.md`
5. `docs/CONTROL_ARCHITECTURE_OVERVIEW.md`
6. `docs/WBC_QP_EXPLAINED.md`
7. `results/logs_sample/`
8. `ros2_ws/src/robot_mpc_wbc_cpp_controller/`
9. `scripts/`

---

## 12. 复现与验证

### 12.1 ROS2/C++ 测试

```bash
bash scripts/stage15_1_validate_ros2_cpp_controller.sh
bash scripts/stage15_2_validate_contact_force_qp.sh
```

### 12.2 Pinocchio / MuJoCo 候选链路验证

```bash
bash scripts/stage15_6_validate_real_model_jacobian_candidate_rollout.sh
bash scripts/stage15_7_validate_mujoco_candidate_compatibility_audit.sh
bash scripts/stage15_8_validate_mujoco_torque_smoke_test.sh
bash scripts/stage15_9_validate_mujoco_jtf_candidate_injection.sh
bash scripts/stage15_10_validate_mujoco_torque_smoke_policy_comparison.sh
```

### 12.3 文档和证据索引验证

```bash
bash scripts/stage15_11_validate_stage15_summary_report.sh
bash scripts/stage16_1_validate_public_docs_sync.sh
bash scripts/stage16_2_validate_artifact_index.sh
```

---

## 13. 面试表述建议

推荐表述：

> 这个项目是一个仅限仿真验证的四足机器人运动控制链路工程项目。我主要完成了 MuJoCo/Pinocchio 控制链路、ROS2/C++ 控制算法测试、contact force QP、Pinocchio `J^T f` torque candidate、MuJoCo actuator compatibility audit 和 bounded torque smoke test。当前结果证明的是控制链路和工程验证能力，不声明真实机器人部署，也不声明完整 MPC-WBC 闭环稳定行走已经完成。

不推荐表述：

> 我已经完成了真实机器人部署。  
> MPC-WBC 已经完整闭环稳定行走。  
> ROS torque publisher 可以直接用于硬件。  
> `torque_enable_ready=True`。

---

## 14. 术语规范

本仓库采用以下写法：

- 正文以中文技术叙述为主；
- 标准英文缩写保留，例如 MPC、WBC、QP、PD、EKF、ROS2；
- 工具和库名保留英文，例如 MuJoCo、Pinocchio、OSQP、CMake、GTest；
- 代码标识符、路径、脚本名、类名和函数名不翻译；
- 首次出现的重要术语使用“中文名 + 英文全称 + 缩写”；
- 避免在同一句话内无必要混用中英文。

示例：

```text
模型预测控制（Model Predictive Control, MPC）用于生成接触力候选。
全身控制（Whole-Body Control, WBC）和二次规划（Quadratic Programming, QP）用于构造候选力矩或约束优化问题。
比例-微分控制（Proportional-Derivative Control, PD）用于基础姿态和摆腿跟踪。
```

---

## 15. 项目当前结论

当前项目已经完成本轮面向实习面试的升级。

准确结论：

```text
完成了 simulation-only 四足机器人控制链路的工程化升级：
ROS2/C++ 测试、contact force QP、Pinocchio J^T f candidate、MuJoCo actuator compatibility、bounded torque smoke test、结果归档、公开文档同步和 artifact index。
```

边界结论：

```text
尚未完成真实机器人部署；
尚未完成完整 MPC-WBC closed-loop 稳定行走；
尚未声明 torque_enable_ready=True。
```

<!-- STAGE17_ENTRY_DOCS_SYNC_START -->
## Stage 17 — Conservative MPC/WBC Closed-Loop Rollout Evidence

Stage 17 packages the existing simulation-only MPC/WBC candidate path into conservative closed-loop rollout evidence.

Current evidence chain:

- **Stage 17.0**: closed-loop rollout roadmap and claim boundaries. See `docs/STAGE17_CLOSED_LOOP_ROADMAP.md`.
- **Stage 17.1**: conservative `scale=0.02` MPC/WBC candidate injection validation. See `docs/STAGE17_1_CONSERVATIVE_CLOSED_LOOP_ROLLOUT.md`.
- **Stage 17.2**: readable rollout metrics table for `scale=0.00 / 0.02 / 0.05 / 0.10`. See `docs/STAGE17_2_CONSERVATIVE_ROLLOUT_METRICS_TABLE.md`.

Current Stage 17 status:

```text
Stage 17.0 result: pass
Stage 17.1 result: pass
Stage 17.2 result: pass
```

Claim boundary:

- Simulation-only evidence.
- Conservative low-scale candidate injection.
- No real robot torque command.
- No hardware torque enablement claim.
- No velocity tracking metric in the Stage 14.5e evidence table.
- No claim that MPC/WBC comprehensively outperforms the baseline.
<!-- STAGE17_ENTRY_DOCS_SYNC_END -->

<!-- STAGE18_ENTRY_DOCS_SYNC_START -->
## Stage 18：速度跟踪证据补齐

Stage 18 用于补齐 Stage 17 的主要边界：此前已有高度、姿态、QP failure 和 torque saturation 证据，但缺少速度跟踪指标。

当前证据支持：

  * 已在 simulation-only rollout 中新增 `base_x`、`base_y`、`base_vx_fd`、`target_vx`、`velocity_error`、`mean_vx`、`mean_abs_velocity_error` 和 `forward_displacement` 等速度相关指标。
  * 已完成 baseline 与低尺度 MPC/WBC candidate 注入工况的速度指标对照。
  * 已确认两组工况均通过高度、姿态、QP failure 和 torque saturation 安全边界。
  * 已明确当前低尺度 MPC/WBC candidate 不改善速度跟踪，baseline 速度跟踪优于 candidate。

阶段结果：

    Stage 18.0 result: pass
    Stage 18.1 result: pass
    Stage 18.2a result: pass
    Stage 18.2 result: pass
    Stage 18.3 result: pass

关键结论：

    Stage 18.2 的低尺度 MPC/WBC candidate 注入工况保持稳定，但不改善速度跟踪。在 target_vx=0.2 m/s 的当前测试中，baseline 的 mean_vx 更高、mean_abs_velocity_error 更低、forward_displacement 更大。

当前不能声明：

  * 不声明低尺度 MPC/WBC candidate 改善了速度跟踪；
  * 不声明已完成完整 MPC-WBC 速度控制器；
  * 不声明真实机器人 torque 执行；
  * 不声明已具备硬件 torque enablement 条件；
  * 不声明 MPC/WBC 已全面优于 baseline。

更准确的表述是：

> Stage 18 补齐了仅限仿真的速度跟踪证据。在当前 target_vx=0.2 m/s 测试中，baseline 与低尺度 MPC/WBC candidate 注入均通过稳定性和安全边界，但 baseline 的前向速度跟踪更好。
<!-- STAGE18_ENTRY_DOCS_SYNC_END -->

