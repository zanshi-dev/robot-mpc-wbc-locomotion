# Stage 15.1：ROS2/C++ 控制算法构建与测试闭环

## 1. 目标

本阶段目标是把已有 C++ 控制算法模块从“可手动 g++ 编译”升级为“可通过 ROS2/CMake/colcon 构建并测试”的工程化模块。

本阶段不改变真实机器人安全边界：

- 不发布真实机器人关节力矩
- 不接入真实硬件
- 不声明 `torque_enable_ready=True`
- 不声明实时硬件控制器完成
- 仍然只验证控制算法模块和零输出安全路径

## 2. 修改范围

涉及文件：

```text
ros2_ws/src/robot_mpc_wbc_cpp_controller/CMakeLists.txt
ros2_ws/src/robot_mpc_wbc_cpp_controller/package.xml
ros2_ws/src/robot_mpc_wbc_cpp_controller/test/test_control_algorithms.cpp
scripts/stage15_1_validate_ros2_cpp_controller.sh
docs/STAGE15_1_ROS2_CPP_TESTING.md
```

## 3. C++ 控制算法库

新增或规范化 `control_algorithms` 静态库：

```text
src/control/gait_scheduler.cpp
src/control/swing_trajectory.cpp
src/control/torque_safety_filter.cpp
```

对应头文件：

```text
include/robot_mpc_wbc_cpp_controller/control/gait_scheduler.hpp
include/robot_mpc_wbc_cpp_controller/control/swing_trajectory.hpp
include/robot_mpc_wbc_cpp_controller/control/torque_safety_filter.hpp
```

该库只包含纯控制算法，不依赖 ROS topic，不发布 torque，不访问硬件。

## 4. 测试内容

`test/test_control_algorithms.cpp` 覆盖三类基础契约：

1. 步态调度器
   - trot_FR_RL 与 trot_FL_RR 接触模式交替
   - 周期边界行为正确

2. 摆腿轨迹生成器
   - 起点和终点位置正确
   - 中点高度高于起点和终点

3. 力矩安全过滤器
   - 超限力矩被限幅
   - NaN 力矩被替换为 0
   - 过滤后力矩满足有限值和限幅约束

## 5. 验证命令

在仓库根目录执行：

```bash
bash scripts/stage15_1_validate_ros2_cpp_controller.sh
```

等价手动命令：

```bash
source /opt/ros/jazzy/setup.bash
cd ros2_ws
colcon build --packages-select robot_mpc_wbc_cpp_controller --cmake-args -DCMAKE_BUILD_TYPE=RelWithDebInfo
colcon test --packages-select robot_mpc_wbc_cpp_controller --event-handlers console_direct+
colcon test-result --verbose
```

## 6. 结果日志

验证脚本会生成：

```text
results/logs_sample/stage15_1_ros2_cpp_controller_test.log
```

该日志可作为 Stage 15.1 的工程化验证证据。

## 7. 验收标准

本阶段通过标准：

```text
colcon build pass
colcon test pass
colcon test-result pass
stage15_1_result: pass
```

## 8. 后续阶段

Stage 15.1 完成后，下一步建议进入 Stage 15.2：补充 contact force QP 的 C++ demo。

Stage 15.2 的目标不是直接做完整 WBC，而是先验证最小接触力 QP：

```text
输入：质量、期望机身加速度、接触模式、摩擦系数、力约束
输出：四足接触力、约束满足情况、QP 求解状态
```
