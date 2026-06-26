#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
FENCE = chr(96) * 3


def replace_once(text: str, old: str, new: str) -> str:
    if old not in text:
        return text
    return text.replace(old, new, 1)


def insert_before_once(text: str, marker: str, block: str) -> str:
    if block.strip() in text:
        return text
    if marker not in text:
        raise RuntimeError(f"marker not found: {marker}")
    return text.replace(marker, block.rstrip() + "\n\n" + marker, 1)


def main() -> int:
    text = README.read_text(encoding="utf-8")

    old_intro = (
        "目前项目已经完成从基础 PD/WBC 仿真控制，到 MPC/WBC 候选力矩接入，"
        "再到稳定化主控模式的仿真验证。"
    )
    new_intro = (
        "目前项目已经完成从基础 PD/WBC 仿真控制，到 MPC/WBC 候选力矩接入，"
        "再到稳定化主控模式的仿真验证；并进一步补充 Stage 27.1 命令速度与初始 qvel/yawrate "
        "扰动回归矩阵，用于记录不同控制模式在固定 MuJoCo 仿真设置下的行为差异。"
    )
    text = replace_once(text, old_intro, new_intro)

    old_stage_row = (
        "| 阶段 25 | 稳定化 MPC-WBC 主控闭环 | `stabilized_primary_mpc_wbc` 通过标称冒烟仿真 |"
    )
    new_stage_rows = (
        "| 阶段 25 | 稳定化 MPC-WBC 主控闭环 | `stabilized_primary_mpc_wbc` 通过标称冒烟仿真 |\n"
        "| 阶段 26.1 | 控制模式小规模回归矩阵 | 9-case 矩阵记录 baseline、direct primary 和 stabilized primary 的行为差异 |\n"
        "| 阶段 27.1 | 命令速度与初始速度扰动回归矩阵 | 75-case 矩阵补充速度命令、初始 qvel/yawrate 扰动和接触切换窗口审计 |"
    )
    if "| 阶段 27.1 | 命令速度与初始速度扰动回归矩阵 |" not in text:
        text = replace_once(text, old_stage_row, new_stage_rows)

    stage27_key_result = (
        "### 4.5 Stage 27.1 命令速度与初始速度扰动回归矩阵\n\n"
        "在 Stage 26.1 的控制模式回归基础上，项目进一步补充 75-case 命令速度与初始 qvel/yawrate 扰动回归矩阵。\n\n"
        "测试维度包括：\n\n"
        + FENCE + "text\n"
        "target_vx = 0.0, 0.1, 0.2, 0.3, 0.4\n"
        "perturbation = nominal, vx_plus_0p05, vx_minus_0p05, vy_plus_0p03, yaw_plus_0p10\n"
        "control_mode = baseline, primary_mpc_wbc, stabilized_primary_mpc_wbc\n"
        + FENCE + "\n\n"
        "汇总结果：\n\n"
        "| 控制模式 | case 数 | evidence generated | stability pass | regression evidence pass |\n"
        "|---|---:|---:|---:|---:|\n"
        "| baseline | 25 | 25 | 25 | 25 |\n"
        "| `primary_mpc_wbc` | 25 | 25 | 0 | 25 |\n"
        "| `stabilized_primary_mpc_wbc` | 25 | 25 | 25 | 25 |\n\n"
        "该阶段的判断方式是：\n\n"
        "* baseline 和 `stabilized_primary_mpc_wbc` 需要生成 summary/log，且通过稳定性检查；\n"
        "* `primary_mpc_wbc` 是直接主控诊断对照组，只要求生成闭环执行证据，稳定性失败作为失败诊断证据保留。\n\n"
        "Stage 27.1 进一步说明：在固定 MuJoCo 仿真设置下，项目已经不只验证单一标称场景，而是补充了速度命令变化、初始速度扰动和接触切换窗口指标下的控制模式回归证据。\n\n"
        "该阶段仍然不支持真实机器人部署、复杂地形鲁棒性、外力扰动鲁棒性或工程级成熟控制器结论。\n"
    )
    text = insert_before_once(text, "## 5. 快速复现", stage27_key_result)

    stage27_reproduce = (
        "### 5.4 Stage 27.1 命令速度与初始速度扰动回归矩阵\n\n"
        "运行默认小矩阵：\n\n"
        + FENCE + "bash\n"
        "python3 scripts/stage27_1_run_command_and_qvel_perturbation_regression.py\n"
        + FENCE + "\n\n"
        "运行完整 75-case 矩阵：\n\n"
        + FENCE + "bash\n"
        "python3 scripts/stage27_1_run_command_and_qvel_perturbation_regression.py --full\n"
        + FENCE + "\n\n"
        "主要结果文件：\n\n"
        + FENCE + "text\n"
        "results/logs_sample/stage27_1_command_qvel_regression_matrix.csv\n"
        "results/logs_sample/stage27_1_command_qvel_regression_summary.json\n"
        "docs/STAGE27_1_COMMAND_AND_QVEL_PERTURBATION_REGRESSION.md\n"
        + FENCE + "\n"
    )
    text = insert_before_once(text, "## 6. 目录结构", stage27_reproduce)

    old_can_say = (
        "* 已完成 `stabilized_primary_mpc_wbc` 的标称 2400 步冒烟仿真；\n"
        "* 稳定化主控版本中记录到 `qp_fail_steps = 0`、`saturation_steps = 0`。"
    )
    new_can_say = (
        "* 已完成 `stabilized_primary_mpc_wbc` 的标称 2400 步冒烟仿真；\n"
        "* 稳定化主控版本中记录到 `qp_fail_steps = 0`、`saturation_steps = 0`；\n"
        "* 已完成 Stage 26.1 控制模式小规模回归矩阵；\n"
        "* 已完成 Stage 27.1 命令速度与初始 qvel/yawrate 扰动回归矩阵；\n"
        "* 已记录 baseline、`primary_mpc_wbc` 和 `stabilized_primary_mpc_wbc` 在多组速度命令和初始速度扰动下的行为差异。"
    )
    text = replace_once(text, old_can_say, new_can_say)

    old_cannot_say = (
        "* 不说明 MPC/WBC 已通过复杂地形、外力扰动或真实机器人实验验证；\n"
        "* 不说明 `stabilized_primary_mpc_wbc` 已达到工程级成熟控制器。"
    )
    new_cannot_say = (
        "* 不说明 MPC/WBC 已通过复杂地形、外力扰动或真实机器人实验验证；\n"
        "* 不说明 Stage 27.1 的初始 qvel/yawrate 扰动矩阵等价于外力扰动鲁棒性验证；\n"
        "* 不说明 Stage 27.1 的速度命令扫描等价于完整速度跟踪控制器验证；\n"
        "* 不说明 `stabilized_primary_mpc_wbc` 已达到工程级成熟控制器。"
    )
    text = replace_once(text, old_cannot_say, new_cannot_say)

    old_boundary = (
        "当前最重要的结论是：\n\n"
        + FENCE + 'text id="c45dd5"\n'
        "stabilized_primary_mpc_wbc 在固定 MuJoCo 仿真设置下通过标称 2400 步冒烟仿真。\n"
        + FENCE + "\n\n"
        "这个结果说明稳定化后的 MPC-WBC 主控链路在当前仿真条件下可运行，但不等价于真实机器人闭环，也不等价于复杂地形或外力扰动鲁棒性。\n"
    )
    new_boundary = (
        "当前最重要的结论是：\n\n"
        + FENCE + "text\n"
        "stabilized_primary_mpc_wbc 在固定 MuJoCo 仿真设置下通过标称 2400 步冒烟仿真，并在 Stage 27.1 的 75-case 命令速度与初始 qvel/yawrate 扰动回归矩阵中生成进一步对比证据。\n"
        + FENCE + "\n\n"
        "这个结果说明稳定化后的 MPC-WBC 主控链路在当前仿真条件下可运行，并且已经补充多组速度命令和初始速度扰动下的回归证据。但它仍然不等价于真实机器人闭环，也不等价于复杂地形、外力扰动或硬件部署鲁棒性。\n"
    )
    text = replace_once(text, old_boundary, new_boundary)

    README.write_text(text, encoding="utf-8")
    print("updated README.md with Stage 27.1 summary and boundary notes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
