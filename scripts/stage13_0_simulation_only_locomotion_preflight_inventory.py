#!/usr/bin/env /usr/bin/python3
from pathlib import Path
import hashlib
import json
import subprocess
from datetime import datetime

ROOT = Path.cwd()
OUT = ROOT / "results/logs_sample"
DOCS = ROOT / "docs"
OUT.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)

SUMMARY = OUT / "stage13_0_simulation_only_locomotion_preflight_inventory_summary.json"
DOC = DOCS / "stage13_0_simulation_only_locomotion_preflight_inventory.md"

FILES = {
    "stage12_22_summary": OUT / "stage12_22_simulation_only_scope_freeze_summary.json",
    "simulation_scope_doc": DOCS / "SIMULATION_ONLY_SCOPE.md",
    "project_status": ROOT / "PROJECT_STATUS.md",
    "stage07_recommended_script": ROOT / "scripts/stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test.py",
    "stage07_input_wbc_script": ROOT / "scripts/stage07_online_full_wbc_scheduler_recommended_run.py",
    "stage07_swing_tracking_csv": OUT / "stage07_online_swing_trajectory_tracking_check.csv",
    "stage07_recommended_log": OUT / "stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test_log.csv",
    "stage07_recommended_summary": OUT / "stage07_online_stance_pd_wbc_plus_swing_pd_recommended_test_summary.csv",
    "go1_mujoco_scene": ROOT / "assets/go1/scene.xml",
    "go1_urdf": ROOT / "assets/go1/urdf/go1.urdf",
    "ros2_cpp_controller_source": ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp",
}

def sha256_file(path: Path):
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))

def run_py_check(code: str):
    p = subprocess.run(
        ["/usr/bin/python3", "-c", code],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return {"returncode": p.returncode, "output": p.stdout.strip()}

stage12_22 = read_json(FILES["stage12_22_summary"])
fail_reasons = []

if stage12_22 is None:
    fail_reasons.append("missing Stage 12.22 summary")
else:
    if stage12_22.get("pass") is not True:
        fail_reasons.append("Stage 12.22 did not pass")
    if stage12_22.get("simulation_only_project") is not True:
        fail_reasons.append("simulation_only_project is not true")
    if stage12_22.get("hardware_deployment_scope") != "out_of_scope_by_user_constraint":
        fail_reasons.append("hardware scope is not frozen as out_of_scope_by_user_constraint")

file_status = {}
for name, path in FILES.items():
    file_status[name] = {
        "path": str(path),
        "exists": path.exists(),
        "size": path.stat().st_size if path.exists() else None,
        "sha256": sha256_file(path),
    }

required_existing = [
    "stage12_22_summary",
    "simulation_scope_doc",
    "project_status",
    "stage07_recommended_script",
    "go1_mujoco_scene",
    "go1_urdf",
]

for name in required_existing:
    if not file_status[name]["exists"]:
        fail_reasons.append(f"missing required file: {name}")

dependency_checks = {
    "numpy": run_py_check("import numpy; print(numpy.__version__)"),
    "mujoco": run_py_check("import mujoco; print(mujoco.__version__ if hasattr(mujoco, '__version__') else 'ok')"),
    "pinocchio": run_py_check("import pinocchio as pin; print(pin.__version__)"),
    "scipy": run_py_check("import scipy; print(scipy.__version__)"),
    "osqp": run_py_check("import osqp; print(osqp.__version__)"),
}

for name, check in dependency_checks.items():
    if check["returncode"] != 0:
        fail_reasons.append(f"missing or broken dependency: {name}")

recommended_next = "Stage 13.1 rerun 1200-step simulation-only mixed baseline regression"
if file_status["stage07_recommended_summary"]["exists"]:
    recommended_next = "Stage 13.1 compare existing Stage 7 baseline summary and optionally rerun 1200-step regression"

summary = {
    "stage": "13.0",
    "name": "simulation_only_locomotion_preflight_inventory",
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "pass": len(fail_reasons) == 0,
    "fail_reasons": fail_reasons,
    "simulation_only_project": True,
    "hardware_deployment_scope": "out_of_scope_by_user_constraint",
    "hardware_deployment_completed": False,
    "torque_enable_ready": False,
    "torque_publisher_enabled": False,
    "control_law_changed": False,
    "baseline_type": "mixed_online_control_baseline",
    "file_status": file_status,
    "dependency_checks": dependency_checks,
    "recommended_next_stage": recommended_next,
}

SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

md = [
    "# Stage 13.0 Simulation-Only Locomotion Preflight Inventory",
    "",
    f"- pass: `{summary['pass']}`",
    f"- fail_reasons: `{summary['fail_reasons']}`",
    f"- simulation_only_project: `{summary['simulation_only_project']}`",
    f"- hardware_deployment_scope: `{summary['hardware_deployment_scope']}`",
    f"- hardware_deployment_completed: `{summary['hardware_deployment_completed']}`",
    f"- torque_enable_ready: `{summary['torque_enable_ready']}`",
    f"- torque_publisher_enabled: `{summary['torque_publisher_enabled']}`",
    f"- control_law_changed: `{summary['control_law_changed']}`",
    f"- baseline_type: `{summary['baseline_type']}`",
    "",
    "## Required files",
]

for name in required_existing:
    st = file_status[name]
    md.append(f"- {name}: exists=`{st['exists']}`, path=`{st['path']}`")

md += ["", "## Dependency checks"]
for name, check in dependency_checks.items():
    md.append(f"- {name}: returncode=`{check['returncode']}`, output=`{check['output']}`")

md += ["", f"Recommended next stage: `{summary['recommended_next_stage']}`"]
DOC.write_text("\n".join(md), encoding="utf-8")

print(json.dumps(summary, indent=2, ensure_ascii=False))
