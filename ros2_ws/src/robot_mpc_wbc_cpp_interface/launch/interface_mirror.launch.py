from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="robot_mpc_wbc_cpp_interface",
            executable="go1_interface_mirror_node",
            name="go1_interface_mirror_node",
            output="screen",
        )
    ])
