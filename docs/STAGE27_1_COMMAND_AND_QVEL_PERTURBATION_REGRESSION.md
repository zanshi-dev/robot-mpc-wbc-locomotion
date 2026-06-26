# Stage 27.1 命令速度与初始速度扰动回归矩阵

本阶段在 Stage 26.1 控制模式回归矩阵基础上，扩展速度命令与初始 qvel/yawrate 扰动组合。

该阶段目标是记录三种控制模式在固定 MuJoCo 仿真设置下的行为差异：

- baseline
- `primary_mpc_wbc`
- `stabilized_primary_mpc_wbc`

## 1. 验证范围

- 速度命令变化：`target_vx` 小范围扫描；
- 初始速度扰动：`perturb_vx`、`perturb_vy`、`perturb_yawrate`；
- 接触切换窗口审计：统计接触模式切换前后 torque jump、roll、pitch、base_z 和 saturation。

本阶段不修改底层控制律，不新增真实机器人接口，不声明复杂地形、外力扰动或硬件部署鲁棒性。

## 2. 汇总结果

- result: `pass`
- total_cases: `75`
- matrix_csv: `results/logs_sample/stage27_1_command_qvel_regression_matrix.csv`
- summary_json: `results/logs_sample/stage27_1_command_qvel_regression_summary.json`

| control_mode | cases | evidence_generated | stability_pass | regression_evidence_pass |
|---|---:|---:|---:|---:|
| `baseline` | 25 | 25 | 25 | 25 |
| `primary_mpc_wbc` | 25 | 25 | 0 | 25 |
| `stabilized_primary_mpc_wbc` | 25 | 25 | 25 | 25 |

## 3. 判断规则

- `baseline` 和 `stabilized_primary_mpc_wbc`：需要生成 summary/log，且稳定性检查通过。
- `primary_mpc_wbc`：直接主控已知可能不稳定，因此只要求生成闭环执行证据；稳定性失败作为诊断证据保留。

## 4. 结论边界

本阶段只能说明：在固定 MuJoCo 仿真设置下，项目已经补充速度命令与初始速度扰动维度下的控制模式回归证据。

不能说明：

- 真实机器人部署完成；
- 硬件力矩使能安全；
- 复杂地形鲁棒；
- 外力扰动鲁棒；
- `stabilized_primary_mpc_wbc` 已经达到工程级成熟 locomotion controller。
