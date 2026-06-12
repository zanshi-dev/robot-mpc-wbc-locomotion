#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


TARGET_FILES = [
    Path("README.md"),
    Path("docs/ONE_PAGE_TECHNICAL_REPORT.md"),
    Path("docs/CONTROL_ARCHITECTURE_OVERVIEW.md"),
]

INPUT_SUMMARIES = [
    Path("results/logs_sample/stage14_4_base_velocity_tracking_mpc_summary.json"),
    Path("results/logs_sample/stage14_4b_base_velocity_tracking_mpc_validation_summary.json"),
    Path("results/logs_sample/stage14_4c_mpc_scope_explanation_summary.json"),
    Path("results/logs_sample/stage14_4d_document_language_audit_summary.json"),
]

SUMMARY_JSON = Path("results/logs_sample/stage14_4e_entry_docs_update_summary.json")

BEGIN = "<!-- STAGE14_4E_MPC_ENTRY_BEGIN -->"
END = "<!-- STAGE14_4E_MPC_ENTRY_END -->"

README_SECTION = f"""
<!-- STAGE14_4E_MPC_ENTRY_BEGIN -->

## 已补充：MPC 规划层 demo

项目已补充一个仿真内 standalone simplified 3D base velocity tracking receding-horizon MPC demo，用于展示 planning-layer / contact-force MPC 的接触力优化能力。

该模块使用简化质心动力学，状态为 `x = [px, py, pz, vx, vy, vz]`，优化变量为四足三维接触力。每个 rollout step 都会基于当前状态重新求解有限时域 QP，只应用第一帧接触力 `u0`，再推进简化质心状态。

已完成内容：

- standalone Python MPC solver
- 100-step receding-horizon rollout
- rollout CSV 和 summary JSON 记录
- OSQP 求解状态、摆动腿力、支撑腿力、摩擦约束、速度跟踪和高度误差验证
- 与早期 z-MPC prototype、WBC feedforward 的边界关系说明

当前边界：

- MPC 只属于 planning-layer / contact-force MPC demo
- 不是 WBC
- 不直接输出 joint torque
- 不接 ROS torque publisher
- 不接 MuJoCo torque
- 不改变 frozen mixed baseline 控制律
- 项目范围仍保持 simulation-only

相关文件：

- `scripts/stage14_4_base_velocity_tracking_mpc_demo.py`
- `scripts/stage14_4b_validate_base_velocity_mpc_rollout.py`
- `docs/stage14_4_base_velocity_tracking_mpc.md`
- `docs/stage14_4b_base_velocity_tracking_mpc_validation.md`
- `docs/stage14_4c_mpc_scope_explanation.md`

<!-- STAGE14_4E_MPC_ENTRY_END -->
"""

REPORT_SECTION = f"""
<!-- STAGE14_4E_MPC_ENTRY_BEGIN -->

## Stage 14.4：MPC 规划层补充

Stage 14.4 新增的是 standalone simplified 3D base velocity tracking receding-horizon MPC demo。它使用简化质心动力学，把四足三维接触力作为优化变量，在有限时域内同时考虑速度跟踪、高度保持、摆动腿力为零、支撑腿竖直力上下界、摩擦金字塔和总竖直力上界。

该阶段的关键点是 receding-horizon：每一步从当前状态重新求解 QP，只取第一帧接触力 `u0`，然后进入下一步重解。Stage 14.4A 给出实现与 rollout 日志，Stage 14.4B 给出独立验证，Stage 14.4C 给出范围边界说明。

该 MPC 当前只属于 planning-layer / contact-force MPC standalone demo。它不是 WBC，不直接输出 joint torque，不接 ROS torque publisher，不接 MuJoCo torque，不改变 frozen mixed baseline 控制律。项目边界保持为 simulation-only。

<!-- STAGE14_4E_MPC_ENTRY_END -->
"""


def load_json(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(f"missing summary: {path}")
    return json.loads(path.read_text())


def replace_or_append(text: str, section: str) -> str:
    if BEGIN in text and END in text:
        before = text.split(BEGIN, 1)[0].rstrip()
        after = text.split(END, 1)[1].lstrip()
        return before + "\n\n" + section.strip() + "\n\n" + after
    return text.rstrip() + "\n\n" + section.strip() + "\n"


def main() -> None:
    failed_checks: List[str] = []
    updated_files: List[str] = []
    missing_target_files: List[str] = []

    for path in INPUT_SUMMARIES:
        summary = load_json(path)
        if summary.get("pass") is not True:
            failed_checks.append(f"{path}: pass must be true")
        if summary.get("simulation_only_project") is not True:
            failed_checks.append(f"{path}: simulation_only_project must be true")
        for key in [
            "hardware_deployment_completed",
            "torque_enable_ready",
            "torque_publisher_enabled",
            "control_law_changed",
        ]:
            if summary.get(key) is not False:
                failed_checks.append(f"{path}: {key} must be false")

    for path in TARGET_FILES:
        if not path.exists():
            missing_target_files.append(str(path))
            continue

        section = README_SECTION if path.name == "README.md" else REPORT_SECTION
        text = path.read_text()
        path.write_text(replace_or_append(text, section))
        updated_files.append(str(path))

    if not updated_files:
        failed_checks.append("no target entry docs were updated")

    result = {
        "stage": "14.4E",
        "description": "update README and project entry docs with Stage 14.4 MPC summary",
        "pass": len(failed_checks) == 0,
        "failed_checks": failed_checks,
        "simulation_only_project": True,
        "hardware_deployment_completed": False,
        "torque_enable_ready": False,
        "torque_publisher_enabled": False,
        "control_law_changed": False,
        "mixed_baseline_modified": False,
        "mujoco_torque_used": False,
        "ros_publisher_used": False,
        "updated_files": updated_files,
        "missing_target_files": missing_target_files,
        "summary_json": str(SUMMARY_JSON),
        "input_summaries": [str(p) for p in INPUT_SUMMARIES],
    }

    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, indent=2, sort_keys=True))

    if not result["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
