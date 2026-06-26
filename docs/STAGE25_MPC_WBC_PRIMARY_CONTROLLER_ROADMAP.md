# Stage 25：MPC-WBC primary controller closure roadmap

## 1. 背景

Stage 17–24 已完成 simulation-only 证据链，包括：

  * conservative rollout evidence；
  * velocity tracking comparison；
  * velocity-aware scale sweep；
  * recommended scale replay；
  * local perturbation audit；
  * qvel perturbation negative evidence；
  * perturbation observability root-cause audit；
  * short-horizon perturbation-sensitive metric audit。

当前主线推荐仍保持为：

    scale=0.010 是当前 simulation-only 证据下的 local-perturbation-tested recommended candidate scale。

Stage 24 的结论表明：

    qvel 扰动在 injection / mj_forward 阶段可被检测到；
    aligned after_mj_step rows 中没有相对 nominal 的持续 trace separation；
    Stage 22 的长期 summary 指标没有变化是合理的；
    Stage 24 不支持 observable perturbation robustness；
    Stage 24 不支持 scale=0.010 推荐等级升级。

因此，Stage 25 不再继续推进 observable perturbation robustness，也不做真实机器人闭环，而是集中推进 simulation-only MPC-WBC primary controller closure。

## 2. Stage 25 核心目标

Stage 25 的目标是将当前控制结构：

    baseline torque + alpha * MPC/WBC candidate torque

升级为一个新的仿真控制模式：

    MPC/WBC torque as primary stance controller
    + swing leg PD
    + torque safety filter
    + MuJoCo simulation step

该模式称为：

    primary_mpc_wbc

## 3. 当前已有控制结构

当前项目中已有：

  * baseline controller；
  * MPC/WBC candidate torque；
  * candidate scale 注入；
  * swing target / swing leg PD；
  * torque safety filter；
  * MuJoCo simulation loop；
  * OSQP / QP 求解证据；
  * simulation-only rollout evidence。

当前更准确的描述是：

    baseline controller + scaled MPC/WBC candidate injection

还不能描述为：

    MPC-WBC 已经作为最终主控制器直接闭环输出关节力矩。

## 4. Stage 25 要实现的新模式

Stage 25 计划新增一个控制模式：

    --control-mode primary_mpc_wbc

或者等价命名：

    primary_mpc_wbc

该模式的控制结构为：

    read MuJoCo state
    -> compute gait/contact state
    -> compute MPC/WBC candidate torque
    -> use MPC/WBC torque as primary stance torque
    -> add swing leg PD torque for swing legs
    -> pass through torque safety filter
    -> send torque to MuJoCo
    -> MuJoCo step

## 5. Stage 25 不做的事情

Stage 25 不做：

  * 不继续追 observable perturbation robustness；
  * 不做真实机器人闭环；
  * 不做 hardware torque enablement；
  * 不做复杂地形；
  * 不做外力冲击；
  * 不声明 scale=0.010 对所有工况最优；
  * 不声明真实机器人 torque 执行已完成；
  * 不声明已经完成工程级 MPC-WBC 全功能控制器。

## 6. Stage 25 分阶段计划

### Stage 25.0：roadmap

输出 MPC-WBC primary controller closure 路线图和边界。

### Stage 25.1：source audit

检查以下代码入口：

  * baseline torque 生成位置；
  * MPC/WBC candidate torque 生成位置；
  * candidate scale 注入位置；
  * swing leg PD torque 生成位置；
  * safety filter 位置；
  * MuJoCo torque 写入位置；
  * rollout runner 参数入口。

### Stage 25.2：primary_mpc_wbc mode implementation

新增 `primary_mpc_wbc` 控制模式。

原则：

  * 不删除 baseline 模式；
  * 不删除 candidate injection 模式；
  * 新增第三种模式；
  * 保留 safety filter；
  * 保留 swing leg PD；
  * stance torque 主要来自 MPC/WBC candidate torque；
  * 如 QP 失败，允许 fallback 到 safe torque 或 baseline-safe fallback，并记录 failure flag。

### Stage 25.3：primary_mpc_wbc smoke rollout

运行短时 simulation-only rollout，验证：

  * 不崩溃；
  * MuJoCo step 正常推进；
  * torque safety filter 生效；
  * base height 不穿地；
  * roll/pitch 不发散；
  * QP failure 有记录；
  * torque saturation 有记录；
  * 输出 summary json / csv。

### Stage 25.4：baseline / candidate injection / primary_mpc_wbc comparison

对比三种控制模式：

  * baseline；
  * recommended candidate injection，scale=0.010；
  * primary_mpc_wbc。

对比指标：

  * min_z；
  * max_abs_roll；
  * max_abs_pitch；
  * mean_vx；
  * mean_abs_velocity_error；
  * forward_displacement；
  * qp_fail_steps；
  * saturation_steps；
  * max_tau_total_abs。

Stage 25.4 的目标不是证明 primary_mpc_wbc 一定优于 baseline，而是判断它是否已经形成 simulation-only 可运行主控闭环。

### Stage 25.5：evidence freeze

同步 README、PROJECT_STATUS、ARTIFACT_INDEX，冻结 Stage 25 证据。

## 7. Stage 25 成功标准

Stage 25 成功标准分两级。

### 7.1 最低成功标准

可以声明：

    已新增 primary_mpc_wbc 控制模式；
    MPC/WBC torque 已作为 simulation-only primary stance torque 进入 MuJoCo torque loop；
    该模式能完成短时 smoke rollout；
    safety filter 仍然在最终 torque 输出前生效。

### 7.2 更高成功标准

如果 Stage 25.4 对比通过，可以声明：

    primary_mpc_wbc 模式在当前固定仿真设置下完成了与 baseline / candidate injection 的对比 rollout；
    当前结果形成 simulation-only MPC-WBC primary controller closure evidence。

## 8. Stage 25 不支持的表述

Stage 25 不支持：

  * 不支持真实机器人闭环；
  * 不支持 hardware torque enablement；
  * 不支持 observable perturbation robustness；
  * 不支持复杂地形鲁棒性；
  * 不支持外力冲击鲁棒性；
  * 不支持 scale=0.010 是所有工况最优；
  * 不支持工程级 MPC-WBC 控制器完全成熟；
  * 不支持无 fallback 的硬实时控制器已经完成。

## 9. Stage 25 对技术表述的目标

Stage 25 完成后，可以说明：

    原项目最初是 baseline + MPC/WBC candidate injection。
    后续进一步实现了 simulation-only primary_mpc_wbc 模式，
    让 MPC/WBC torque 不再只是小比例 candidate injection，
    而是作为 stance primary torque 进入 MuJoCo torque loop；
    同时保留 swing leg PD 和 torque safety filter，
    并通过 rollout 对比验证该模式是否能稳定运行。

不能说：

    已经完成真实机器人 MPC-WBC 闭环。
    已经完成硬件 torque enablement。
    已经证明所有扰动下鲁棒。
