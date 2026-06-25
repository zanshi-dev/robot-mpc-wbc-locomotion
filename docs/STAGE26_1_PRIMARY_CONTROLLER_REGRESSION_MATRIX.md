# Stage 26.1 Primary Controller Regression Matrix

## 1. 目标

Stage 26.1 用于补充小规模回归证据，验证三种控制模式在固定 MuJoCo 仿真设置下的行为差异：

- baseline
- primary_mpc_wbc
- stabilized_primary_mpc_wbc

本阶段重点不是证明完整鲁棒性，而是证明：

1. baseline 可以稳定通过；
2. primary_mpc_wbc 直接主控能够进入 MuJoCo 力矩闭环，但会稳定性失败；
3. stabilized_primary_mpc_wbc 能在相同测试设置下通过稳定性检查。

## 2. 测试矩阵

| 参数 | 取值 |
|---|---|
| control_mode | baseline / primary_mpc_wbc / stabilized_primary_mpc_wbc |
| target_vx | 0.0 / 0.1 / 0.2 |
| rollout setting | fixed nominal MuJoCo setting |
| total cases | 9 |

## 3. 总体结果

| 控制模式 | case 数 | evidence pass | stability pass |
|---|---:|---:|---:|
| baseline | 3 | 3 | 3 |
| primary_mpc_wbc | 3 | 3 | 0 |
| stabilized_primary_mpc_wbc | 3 | 3 | 3 |

## 4. 关键指标

| run_id | control_mode | target_vx | returncode | stability_pass | qp_fail_steps | saturation_steps | max_abs_roll | max_abs_pitch |
|---|---|---:|---:|---|---:|---:|---:|---:|
| stage26_1_base_vx0p00 | baseline | 0.000 | 0 | True | 0 | 0 | 0.0567 | 0.0483 |
| stage26_1_base_vx0p10 | baseline | 0.100 | 0 | True | 0 | 0 | 0.0567 | 0.0483 |
| stage26_1_base_vx0p20 | baseline | 0.200 | 0 | True | 0 | 0 | 0.0567 | 0.0483 |
| stage26_1_primary_vx0p00 | primary_mpc_wbc | 0.000 | 2 | False | 0 | 555 | 0.4887 | 0.3562 |
| stage26_1_primary_vx0p10 | primary_mpc_wbc | 0.100 | 2 | False | 0 | 555 | 0.4887 | 0.3562 |
| stage26_1_primary_vx0p20 | primary_mpc_wbc | 0.200 | 2 | False | 0 | 555 | 0.4887 | 0.3562 |
| stage26_1_stab_vx0p00 | stabilized_primary_mpc_wbc | 0.000 | 0 | True | 0 | 0 | 0.0882 | 0.0507 |
| stage26_1_stab_vx0p10 | stabilized_primary_mpc_wbc | 0.100 | 0 | True | 0 | 0 | 0.0882 | 0.0507 |
| stage26_1_stab_vx0p20 | stabilized_primary_mpc_wbc | 0.200 | 0 | True | 0 | 0 | 0.0882 | 0.0507 |

## 5. 解释

primary_mpc_wbc 直接主控模式能够进入 MuJoCo 力矩闭环，但没有通过稳定性检查。失败特征是力矩饱和步数较多，并伴随较大的 roll / pitch 姿态偏差。QP failure 步数为 0，说明失败主要不是求解器失败，而是直接主控力矩接管后的稳定性和安全边界问题。

stabilized_primary_mpc_wbc 在相同固定仿真设置下通过全部 3 个 case，且没有 QP failure 和 torque saturation。该结果支持 Stage 25 的结论：稳定化机制可以把直接主控失败链路推进到可运行的主控闭环原型。

## 6. 证据边界

本阶段支持的说法：

- 固定 MuJoCo 仿真设置下，stabilized_primary_mpc_wbc 相比 primary_mpc_wbc 直接主控具有更好的稳定性表现。
- primary_mpc_wbc 的失败可以作为诊断证据，而不是简单实现失败。
- stabilized_primary_mpc_wbc 通过了9-case 控制模式回归矩阵。

本阶段不支持的说法：

- 不支持真实机器人部署结论。
- 不支持硬件 torque enablement。
- 不支持复杂地形鲁棒性。
- 不支持外力扰动鲁棒性。
- 不支持完整工程级 MPC-WBC locomotion controller。
- 不支持严格速度跟踪鲁棒性结论。

注意：三个 target_vx 下的核心指标完全相同，说明当前测试更适合作为控制模式回归证据，而不是速度跟踪性能证据。

## 7. 产物

| 文件 | 说明 |
|---|---|
| scripts/stage26_1_run_primary_controller_regression_matrix.py | Stage 26.1 回归矩阵运行脚本 |
| results/logs_sample/stage26_1_primary_controller_regression_matrix.csv | 9-case 回归矩阵结果 |
| results/logs_sample/stage26_1_primary_controller_regression_summary.json | 回归摘要 |
| results/logs_sample/stage26_1_trace_stage26_1_*.csv | 每个 case 的短 trace |
