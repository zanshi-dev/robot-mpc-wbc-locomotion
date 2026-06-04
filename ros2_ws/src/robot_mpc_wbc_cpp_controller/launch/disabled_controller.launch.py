from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="robot_mpc_wbc_cpp_controller",
            executable="go1_disabled_controller_node",
            name="go1_disabled_controller_node",
            output="screen",
        )
    ])
