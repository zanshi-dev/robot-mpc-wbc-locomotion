#!/usr/bin/env /usr/bin/python3
from pathlib import Path
import re
import shutil
import datetime

repo = Path.cwd()
readme = repo / "README.md"

if not readme.exists():
    raise SystemExit("README.md not found")

backup_dir = Path("/tmp") / f"robot-mpc-wbc-stage15_4-readme-backup-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(readme, backup_dir / "README.md")

text = readme.read_text()

block = """<!-- STAGE15_README_ENTRY_BEGIN -->

## 项目边界与复现入口

本仓库是一个 Go1 风格四足机器人的 simulation-only MPC/WBC 运动控制原型。

当前项目边界：

- MPC 作为 planning layer，用于生成 contact force reference 或 contact force candidate。
- MPC 不直接输出最终 joint torque。
- WBC/QP 或 J^T f 映射层负责把 contact force reference / candidate 转换为 joint torque candidate。
- 当前冻结稳定基线为 mixed_online_control_baseline。
- 当前稳定控制结构为：stance posture PD + scaled stance WBC feedforward + memory-based swing target PD + torque safety filter。

本仓库不声明：

- 已完成真实机器人部署。
- 已完成 actuator enablement。
- 已完成真实机器人 joint torque 执行。
- torque_enable_ready=True。
- 已完成 realtime hardware controller。

当前证据支持：

- MuJoCo / Pinocchio simulation-only locomotion baseline。
- MPC contact-force planning demo。
- WBC/QP 与 J^T f torque-candidate 验证。
- ROS2/C++ disabled-controller dry-run 证据。
- C++ gait scheduler / swing trajectory / torque safety filter 模块测试。
- report-ready 结果日志与 MuJoCo offscreen-rendered demo video 证据。

### 核心复现入口

从仓库根目录运行：

    bash scripts/stage15_3_reproduce_core_results.sh

该脚本复现当前 report-ready 证据链：

    repo hygiene audit
    -> base velocity tracking MPC demo
    -> MPC rollout validation
    -> ROS2/C++ controller validation
    -> summary log

期望最终标志：

    stage15_3_result: pass

关键日志：

    results/logs_sample/stage15_3_reproduce_core_results.log
    results/logs_sample/stage15_3_reproduce_core_results_summary.txt

<!-- STAGE15_README_ENTRY_END -->
"""

text = re.sub(
    r"\n?<!-- STAGE15_README_ENTRY_BEGIN -->.*?<!-- STAGE15_README_ENTRY_END -->\n?",
    "\n",
    text,
    flags=re.S,
)

lines = text.splitlines()

if not lines:
    raise SystemExit("README.md is empty")

insert_idx = 0
if lines[0].startswith("# "):
    insert_idx = 1

new_lines = lines[:insert_idx] + ["", block.strip(), ""] + lines[insert_idx:]
new_text = "\n".join(new_lines).rstrip() + "\n"

readme.write_text(new_text)

print("patched README.md")
print(f"backup_dir={backup_dir}")
