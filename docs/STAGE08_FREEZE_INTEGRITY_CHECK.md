# Stage 8.10 Freeze Integrity Check

## 目标

对 Stage 8 Python runtime-safe frozen baseline 做最终完整性检查。

## 推荐入口

    /usr/bin/python3 scripts/stage08_adapter_backed_stage07_recommended_test.py

## 检查内容

1. 核心冻结文件是否存在；
2. 生成每个冻结文件的 SHA256；
3. 再运行一次推荐入口；
4. 检查 adapter preflight 是否通过；
5. 明确当前仍是 mixed online control baseline。

## 输出

- Hash log: results/logs_sample/stage08_freeze_integrity_hashes.csv
- Summary: results/logs_sample/stage08_freeze_integrity_check_summary.csv
- Stdout: results/logs_sample/stage08_freeze_integrity_recommended_entrypoint_stdout.txt
- Stderr: results/logs_sample/stage08_freeze_integrity_recommended_entrypoint_stderr.txt

## 结果

- pass: True
- all_files_exist: True
- recommended_entrypoint_returncode: 0
- adapter_preflight_stdout_pass: True

## 边界

本阶段不改变控制律，不完成 pure WBC locomotion，不完成 ROS2/C++ real-time controller，不完成 EKF，不完成 full 3D centroidal MPC。
