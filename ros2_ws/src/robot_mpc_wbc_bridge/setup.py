from glob import glob
import os
from setuptools import find_packages, setup

package_name = "robot_mpc_wbc_bridge"

setup(
    name=package_name,
    version="0.0.1",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="zanshi",
    maintainer_email="2645694430@qq.com",
    description="Minimal ROS2-MuJoCo bridge for robot-mpc-wbc-locomotion.",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "mujoco_bridge_node = robot_mpc_wbc_bridge.mujoco_bridge_node:main",
        ],
    },
)
