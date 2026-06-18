#!/usr/bin/env python3
"""Stage 16.1 public documentation sync.

This script upserts Stage 15 evidence into public-facing docs without deleting
existing sections. It is deliberately conservative: marker blocks are used for
idempotent updates.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

START = "<!-- STAGE16_1_PUBLIC_DOCS_SYNC_START -->"
END = "<!-- STAGE16_1_PUBLIC_DOCS_SYNC_END -->"


def read_or_default(path: Path, default: str) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return default


def upsert_marker_block(text: str, block: str) -> str:
    if START in text and END in text:
        before = text.split(START, 1)[0].rstrip()
        after = text.split(END, 1)[1].lstrip()
        return before + "\n\n" + block.strip() + "\n\n" + after
    return text.rstrip() + "\n\n" + block.strip() + "\n"


def stage16_block(title_level: int = 2) -> str:
    h = "#" * title_level
    return f"""{START}
{h} Stage 15 工程化升级证据

Stage 15 的目标不是直接宣称稳定行走或真实机器人部署，而是把控制链路中的工程证据逐层补齐。当前已完成的证据包括：

| 阶段 | 结果 | 边界 |
|---|---|---|
| Stage 15.1 | ROS2/C++ control algorithms 接入 CMake/GTest，支持 `colcon build/test` | 不发布 torque，不接硬件 |
| Stage 15.2 | C++ contact force QP demo，验证接触模式、法向力和摩擦约束 | 不引入 OSQP C++ 依赖，不执行机器人 torque |
| Stage 15.3 | contact force 到 nominal torque candidate 的 dry-run 和 alpha sweep | 不使用真实 Pinocchio Jacobian，不接 MuJoCo torque |
| Stage 15.4 | Pinocchio Jacobian 下的 `J^T f` torque candidate dry-run | 不接 MuJoCo torque，不接 ROS torque |
| Stage 15.5 | 模型资源 readiness audit，审计 MJCF/URDF/Xacro、关节名和足端 frame 候选 | 只做模型审计 |
| Stage 15.6 | real-model metadata / URDF 路径下的 Pinocchio Jacobian candidate rollout | 若使用 MJCF fallback，不声明完整真实几何模型 |
| Stage 15.7 | MuJoCo joint/actuator compatibility audit | 只调用 `mj_forward`，不执行 torque |
| Stage 15.8 | bounded MuJoCo torque smoke test | 短时域、低幅值，只验证 actuator command path |
| Stage 15.9 | Stage 15.6 `J^T f` torque candidate 低 alpha 注入 MuJoCo smoke test | 不声明稳定行走或 MPC-WBC 闭环成功 |
| Stage 15.10 | zero ctrl / deterministic waveform / `J^T f` candidate 的短时域 safety comparison | 只比较安全和兼容性指标 |
| Stage 15.11 | Stage 15 总结报告 | 整理证据与边界，不新增控制功能 |

可声明内容：

- ROS2/C++ 控制算法模块已具备构建和单元测试证据；
- 接触力约束、候选力矩、Pinocchio Jacobian、MuJoCo joint/actuator 映射已经形成分阶段验证链路；
- MuJoCo 中已经完成 bounded actuator command smoke test 和 short-horizon comparison；
- 所有 Stage 15 结果均有日志或 JSON/CSV 结果归档到 `results/logs_sample/`。

不能声明内容：

- 不声明稳定行走；
- 不声明完整 MPC-WBC closed-loop locomotion controller；
- 不声明真实机器人部署；
- 不声明 ROS torque publisher 可直接用于硬件；
- 不声明 `torque_enable_ready=True`；
- 不声明实时硬件控制器完成。

完整 Stage 15 总结见：`docs/STAGE15_UPGRADE_SUMMARY.md`。
{END}"""


def one_page_block() -> str:
    return f"""{START}
## Stage 15 工程化证据摘要

Stage 15 将项目从纯 Python/MuJoCo 控制演示推进到可审计的工程证据链：ROS2/C++ 单元测试、C++ contact force QP demo、Pinocchio `J^T f` torque candidate、模型资源 readiness audit、MuJoCo joint/actuator compatibility audit，以及 bounded MuJoCo torque smoke test。

当前 Stage 15 证据只能支持 simulation-only 和 short-horizon smoke-test 结论。项目不声明稳定行走、不声明真实机器人部署、不声明 `torque_enable_ready=True`，也不声明完整 MPC-WBC closed-loop controller 已完成。

报告级总结见：`docs/STAGE15_UPGRADE_SUMMARY.md`。
{END}"""


def status_block() -> str:
    return f"""{START}
## Stage 16.1 Public Documentation Sync

Public-facing docs have been synced with Stage 15 evidence.

Current accurate status:

- Stage 15.1 - 15.11 completed and archived.
- ROS2/C++ control modules are buildable and testable.
- Contact-force QP, Pinocchio `J^T f` candidate generation, MuJoCo compatibility audit and bounded torque smoke tests have report artifacts.
- The project remains simulation-only.
- Stable locomotion from the Stage 15 candidate path is not claimed.
- Full MPC-WBC closed-loop locomotion is not claimed.
- Hardware deployment and `torque_enable_ready=True` are not claimed.
{END}"""


def sync(repo_root: Path) -> Dict[str, Any]:
    readme = repo_root / "README.md"
    one_page = repo_root / "docs/ONE_PAGE_TECHNICAL_REPORT.md"
    status = repo_root / "PROJECT_STATUS.md"
    doc = repo_root / "docs/STAGE16_1_PUBLIC_DOCS_SYNC.md"

    readme.write_text(upsert_marker_block(read_or_default(readme, "# robot-mpc-wbc-locomotion\n"), stage16_block(2)), encoding="utf-8")
    one_page.write_text(upsert_marker_block(read_or_default(one_page, "# One Page Technical Report\n"), one_page_block()), encoding="utf-8")
    status.write_text(upsert_marker_block(read_or_default(status, "# Project Status\n"), status_block()), encoding="utf-8")
    doc.write_text(
        "# Stage 16.1 Public Documentation Sync\n\n"
        "This stage syncs README, the one-page technical report and PROJECT_STATUS with Stage 15 evidence.\n\n"
        "Run validation with:\n\n"
        "```bash\n"
        "bash scripts/stage16_1_validate_public_docs_sync.sh\n"
        "```\n\n"
        "Expected marker:\n\n"
        "```text\n"
        "stage16_1_result: pass\n"
        "```\n",
        encoding="utf-8",
    )

    return {
        "stage": "16.1",
        "name": "public_docs_sync",
        "files_synced": [str(readme.relative_to(repo_root)), str(one_page.relative_to(repo_root)), str(status.relative_to(repo_root)), str(doc.relative_to(repo_root))],
        "readme_marker_present": START in readme.read_text(encoding="utf-8"),
        "one_page_marker_present": START in one_page.read_text(encoding="utf-8"),
        "status_marker_present": START in status.read_text(encoding="utf-8"),
        "boundary": {
            "stable_locomotion_claimed": False,
            "full_mpc_wbc_closed_loop_claimed": False,
            "hardware_deployment_claimed": False,
            "torque_enable_ready_claimed": False,
        },
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    output_json = args.output_json or repo_root / "results/logs_sample/stage16_1_public_docs_sync_summary.json"
    summary = sync(repo_root)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("stage16_1_sync_completed: true")
    for item in summary["files_synced"]:
        print(f"synced: {item}")
    print(f"output_json: {output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
