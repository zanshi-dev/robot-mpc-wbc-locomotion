# Stage 15.2：Contact Force QP C++ Demo

## 1. 目标

本阶段补充一个最小 C++ 接触力 QP demo，用于验证接触力规划中的基本约束建模。

本阶段重点不是完整 WBC，也不是引入 OSQP C++ 依赖，而是先建立一个可构建、可测试、可回归的接触力求解模块。

## 2. 安全边界

本阶段不改变项目安全边界：

- 不发布真实机器人关节力矩
- 不接入真实硬件
- 不声明硬件力矩使能完成
- 不声明实时硬件控制器完成
- 不把 MPC/WBC 直接接入真实机器人

该模块只属于 simulation-only / planning-layer / algorithm-demo 证据。

## 3. 新增文件

```text
ros2_ws/src/robot_mpc_wbc_cpp_controller/include/robot_mpc_wbc_cpp_controller/control/contact_force_qp.hpp
ros2_ws/src/robot_mpc_wbc_cpp_controller/src/control/contact_force_qp.cpp
ros2_ws/src/robot_mpc_wbc_cpp_controller/test/test_contact_force_qp.cpp
scripts/stage15_2_validate_contact_force_qp.sh
docs/STAGE15_2_CONTACT_FORCE_QP_CPP.md
```

## 4. 输入与输出

输入：

```text
mass_kg
gravity
friction_coefficient
min_normal_force
max_normal_force
desired_linear_acceleration
contact[4]
```

输出：

```text
foot_forces[4]
desired_net_force
net_force
net_force_error_norm
max_friction_violation
max_normal_force_violation
max_swing_force_norm
success/status
```

## 5. 方法说明

当前实现是解析投影式接触力求解器：

1. 根据期望机身线加速度计算期望合力；
2. 将期望合力平均分配到支撑腿；
3. 摆动腿接触力强制为 0；
4. 支撑腿法向力投影到 `[min_normal_force, max_normal_force]`；
5. 切向力投影到摩擦金字塔约束：

```text
|fx| <= mu * fz
|fy| <= mu * fz
```

该实现不是完整数值 QP solver，也不替代 OSQP。它用于验证接触力约束建模、C++ 接口和测试链路。

## 6. 测试覆盖

`test_contact_force_qp.cpp` 覆盖：

1. 四腿支撑静止悬停：合力匹配重力补偿；
2. 对角小跑接触模式：摆动腿接触力为 0，支撑腿承担重量；
3. 大切向加速度需求：切向力被投影进摩擦金字塔；
4. 无支撑腿：安全失败并返回 `no_active_contacts`。

## 7. 验证命令

```bash
bash scripts/stage15_2_validate_contact_force_qp.sh
```

等价手动命令：

```bash
source /opt/ros/jazzy/setup.bash
cd ros2_ws
colcon build --packages-select robot_mpc_wbc_cpp_controller --cmake-args -DCMAKE_BUILD_TYPE=RelWithDebInfo
colcon test --packages-select robot_mpc_wbc_cpp_controller --event-handlers console_direct+
colcon test-result --verbose
```

## 8. 验证日志

验证脚本会生成：

```text
results/logs_sample/stage15_2_contact_force_qp_cpp_test.log
```

通过标志：

```text
stage15_2_result: pass
```

## 9. 后续方向

Stage 15.2 通过后，下一步可以进入 Stage 15.3：

```text
MuJoCo 当前状态
-> 接触模式
-> contact force QP / MPC force candidate
-> J^T f 关节力矩候选
-> 小比例混合进入 frozen mixed baseline
-> safety filter
-> MuJoCo rollout
```

在 Stage 15.3 之前，不建议引入真实机器人 torque publisher。
