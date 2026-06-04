#!/usr/bin/env /usr/bin/python3
from pathlib import Path
import json
import subprocess
from datetime import datetime

ROOT = Path.cwd()
PKG = ROOT / "ros2_ws/src/robot_mpc_wbc_cpp_controller"
CMAKE = PKG / "CMakeLists.txt"
OUT = ROOT / "results/logs_sample"
DOCS = ROOT / "docs"
OUT.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)

SUMMARY = OUT / "stage14_3_colcon_cpp_control_tests_summary.json"
DOC = DOCS / "stage14_3_colcon_cpp_control_tests.md"

fail_reasons = []

if not CMAKE.exists():
    fail_reasons.append("missing CMakeLists.txt")

original = CMAKE.read_text(encoding="utf-8", errors="replace") if CMAKE.exists() else ""

required_sources = [
    "src/control/gait_scheduler.cpp",
    "src/control/swing_trajectory.cpp",
    "src/control/torque_safety_filter.cpp",
    "test/test_control_algorithms.cpp",
]

for rel in required_sources:
    if not (PKG / rel).exists():
        fail_reasons.append(f"missing required source: {rel}")

patch = r'''
# Stage 14.3: clean C++ control algorithm library and tests.
add_library(control_algorithms
  src/control/gait_scheduler.cpp
  src/control/swing_trajectory.cpp
  src/control/torque_safety_filter.cpp
)

target_include_directories(control_algorithms PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

target_compile_features(control_algorithms PUBLIC cxx_std_17)

if(BUILD_TESTING)
  find_package(ament_cmake_gtest QUIET)

  add_executable(test_control_algorithms
    test/test_control_algorithms.cpp
  )

  target_link_libraries(test_control_algorithms
    control_algorithms
  )

  target_compile_features(test_control_algorithms PRIVATE cxx_std_17)

  add_test(NAME test_control_algorithms COMMAND test_control_algorithms)
endif()
'''

if CMAKE.exists() and "Stage 14.3: clean C++ control algorithm library and tests." not in original:
    insert_before = "ament_package()"
    if insert_before in original:
        updated = original.replace(insert_before, patch + "\n" + insert_before)
    else:
        updated = original.rstrip() + "\n\n" + patch + "\n"
    CMAKE.write_text(updated, encoding="utf-8")

build_cmd = [
    "bash",
    "-lc",
    "source /opt/ros/jazzy/setup.bash && colcon build --base-paths ros2_ws/src --packages-select robot_mpc_wbc_cpp_controller --cmake-args -DBUILD_TESTING=ON"
]

test_cmd = [
    "bash",
    "-lc",
    "source /opt/ros/jazzy/setup.bash && colcon test --base-paths ros2_ws/src --packages-select robot_mpc_wbc_cpp_controller --event-handlers console_direct+ && colcon test-result --test-result-base build/robot_mpc_wbc_cpp_controller --verbose"
]

build = subprocess.run(build_cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
test = None

if build.returncode != 0:
    fail_reasons.append(f"colcon build failed: {build.returncode}")
else:
    test = subprocess.run(test_cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if test.returncode != 0:
        fail_reasons.append(f"colcon test failed: {test.returncode}")

summary = {
    "stage": "14.3",
    "name": "integrate_cpp_control_algorithm_tests_into_colcon",
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "pass": len(fail_reasons) == 0,
    "fail_reasons": fail_reasons,
    "simulation_only_project": True,
    "hardware_deployment_completed": False,
    "torque_enable_ready": False,
    "torque_publisher_enabled": False,
    "control_law_changed": False,
    "cmake_updated": CMAKE.exists() and "Stage 14.3: clean C++ control algorithm library and tests." in CMAKE.read_text(encoding="utf-8", errors="replace"),
    "build_returncode": build.returncode,
    "test_returncode": None if test is None else test.returncode,
    "build_stdout_tail": build.stdout[-5000:],
    "test_stdout_tail": None if test is None else test.stdout[-5000:],
    "test_target": "test_control_algorithms"
}

SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

DOC.write_text(
    "\n".join([
        "# Stage 14.3 Colcon C++ Control Algorithm Tests",
        "",
        f"- pass: `{summary['pass']}`",
        f"- fail_reasons: `{summary['fail_reasons']}`",
        f"- cmake_updated: `{summary['cmake_updated']}`",
        f"- build_returncode: `{summary['build_returncode']}`",
        f"- test_returncode: `{summary['test_returncode']}`",
        f"- test_target: `{summary['test_target']}`",
        f"- simulation_only_project: `{summary['simulation_only_project']}`",
        f"- hardware_deployment_completed: `{summary['hardware_deployment_completed']}`",
        f"- torque_enable_ready: `{summary['torque_enable_ready']}`",
        f"- torque_publisher_enabled: `{summary['torque_publisher_enabled']}`",
        f"- control_law_changed: `{summary['control_law_changed']}`",
        "",
        "This stage only integrates clean C++ control algorithm modules into the ROS2/colcon test workflow. It does not publish torque and does not change the locomotion control law.",
    ]),
    encoding="utf-8",
)

print(json.dumps(summary, indent=2, ensure_ascii=False))
