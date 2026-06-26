# Stage 25.7：MPC-WBC primary controller closure evidence freeze

## 1. 目标

Stage 25.7 冻结 Stage 25.0–25.6 的 simulation-only MPC-WBC primary controller closure 证据。

本阶段不新增控制器，不新增 rollout，只汇总证据、冻结边界和生成 manifest / hash。

## 2. 冻结结果

Stage 25.7 result: pass

Failure count: 0

Final claim:

    simulation-only stabilized MPC-WBC primary controller closure smoke evidence

## 3. Direct primary 与 stabilized primary 对比

| 项目 | direct primary_mpc_wbc | stabilized_primary_mpc_wbc |
|---|---:|---:|
| executed | True | True |
| pass | False | True |
| max_abs_roll | 0.488712369676 | 0.088212790238 |
| max_abs_pitch | 0.356235143697 | 0.050696666834 |
| qp_fail_steps | 0 | 0 |
| saturation_steps | 555 | 0 |
| max_tau_total_abs | 23.700000000000 | 10.890608907787 |

## 4. 固定结论

Stage 25 支持以下表述：

    项目已实现并验证 simulation-only stabilized MPC-WBC primary controller closure。
    direct primary_mpc_wbc 已实际进入 MuJoCo torque loop，但未通过稳定性边界。
    stabilized_primary_mpc_wbc 通过了 nominal 2400-step smoke rollout。
    stabilized 版本使用 ramp / scale / posture residual / WBC residual，并保留 swing PD 和 torque safety filter。
    stabilized rollout 中 qp_fail_steps=0，saturation_steps=0。

## 5. 不能说的内容

Stage 25 不支持以下表述：

  * direct primary_mpc_wbc 已稳定；
  * full MPC/WBC torque 已经可以无残差稳定替代 baseline；
  * 已完成真实机器人闭环；
  * 已完成 hardware torque enablement；
  * 已验证复杂地形或外力扰动鲁棒性；
  * 已达到工程级成熟 MPC-WBC 控制器。

## 6. 结论表述建议

可以说：

    项目先把 MPC/WBC candidate torque 接入为 primary stance torque，构成 primary_mpc_wbc 模式。
    直接主控版本确实进入了 MuJoCo torque loop，但 smoke rollout 暴露出姿态超限和力矩饱和问题。
    之后进行了失败诊断，确认不是 QP failure，而是 torque composition 需要稳定化。
    因此实现了 stabilized_primary_mpc_wbc，在 primary candidate torque 外加入 ramp、scale、stance posture residual 和 online WBC residual。
    该稳定化版本在 nominal 2400-step simulation-only smoke rollout 中通过稳定性边界，且没有 QP failure 和 torque saturation。
    这个结果只证明仿真固定场景下的稳定化主控闭环，不代表真实机器人或复杂地形鲁棒性。

## 7. 证据文件

Manifest:

    results/logs_sample/stage25_7_primary_controller_closure_evidence_manifest.json

Hashes:

    results/logs_sample/stage25_7_primary_controller_closure_evidence_hashes.csv

Summary:

    results/logs_sample/stage25_7_primary_controller_closure_evidence_freeze_summary.json
