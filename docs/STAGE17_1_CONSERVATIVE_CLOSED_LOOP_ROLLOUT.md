# Stage 17.1: Conservative Closed-Loop Rollout Evidence

## 1. 目标

Stage 17.1 将已有 Stage 14.5e 的低尺度 MPC-assisted candidate rollout 证据正式封装为 Stage 17 的 conservative closed-loop rollout evidence。

当前采用：

```text
baseline closed-loop runner
+ low-scale MPC/WBC candidate injection
+ torque safety filtering
+ rollout log / summary validation
```

## 2. 证据来源

Stage 17.1 不重新发明控制器，而是复用并验证已有结果：

```text
results/logs_sample/stage14_5e_r1_scale_0p02_candidate_log.csv
results/logs_sample/stage14_5e_r1_scale_0p02_candidate_summary.csv
results/logs_sample/stage14_5e_r1_scale_0p00_baseline_reference_summary.csv
results/logs_sample/stage14_5e_r1_candidate_robustness_scale_sweep_table.csv
results/logs_sample/stage14_5d_r6_closed_loop_ab_mpc_assisted_candidate_summary.csv
```

其中 `scale=0.02` 被定义为 conservative candidate injection。

## 3. 验证指标

Stage 17.1 验证以下内容：

```text
candidate log rows
candidate summary rows
baseline reference summary
sweep table
control mode
simulation-only flag
candidate execution flag
candidate scale
total rollout steps
minimum base height
maximum absolute roll
maximum absolute pitch
QP failure steps
torque saturation steps
torque and candidate torque metrics
```

当前 Stage 14.5e 证据文件不包含 `vx` 或 `mean_vx` 字段，因此 Stage 17.1 不声明速度跟踪性能。

## 4. Stage 17.1 声明边界

可以声明：

- 已完成 simulation-only conservative closed-loop rollout evidence validation；
- 已完成低尺度 MPC/WBC candidate injection 证据封装；
- 已完成 candidate log、summary、baseline reference、sweep table 的一致性检查；
- 已验证低尺度 candidate 注入未破坏高度、姿态、QP 和力矩饱和安全边界；
- 已生成 Stage 17.1 validation CSV 和 summary JSON。

不能声明：

- 已完成真实机器人控制；
- 已完成高性能 MPC-WBC 闭环控制器；
- 已证明 MPC/WBC 全面优于 baseline；
- 已完成硬件实时控制器部署；
- 已完成速度跟踪性能评估。

## 5. 生成文件

```text
scripts/stage17_1_validate_conservative_closed_loop_rollout.py
docs/STAGE17_1_CONSERVATIVE_CLOSED_LOOP_ROLLOUT.md
results/logs_sample/stage17_1_conservative_closed_loop_rollout_validation.csv
results/logs_sample/stage17_1_conservative_closed_loop_rollout_summary.json
results/logs_sample/stage17_1_conservative_closed_loop_rollout_validation.log
```

## 6. 面试表述

推荐表述：

> Stage 17.1 没有直接把 MPC/WBC 候选力矩替换为主控制器，而是采用 conservative low-scale injection，把候选力矩叠加到已有稳定 baseline 上，并通过 MuJoCo simulation-only rollout 日志验证其没有破坏高度、姿态、QP 求解和力矩饱和边界。

