from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="robot_mpc_wbc_bridge",
            executable="mujoco_bridge_node",
            name="mujoco_bridge_node",
            output="screen",
            parameters=[{
                "model_path": "/home/zanshi/robot-mpc-wbc-locomotion/assets/go1/scene.xml",
                "base_body": "trunk",
                "publish_rate_hz": 100.0,
            }],
        )
    ])
