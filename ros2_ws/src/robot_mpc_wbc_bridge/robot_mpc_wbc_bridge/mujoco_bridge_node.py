from pathlib import Path

import mujoco
import numpy as np
import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Imu, JointState
from std_msgs.msg import Float64, Float64MultiArray, Int32MultiArray


JOINT_NAMES = [
    "FR_hip_joint", "FR_thigh_joint", "FR_calf_joint",
    "FL_hip_joint", "FL_thigh_joint", "FL_calf_joint",
    "RR_hip_joint", "RR_thigh_joint", "RR_calf_joint",
    "RL_hip_joint", "RL_thigh_joint", "RL_calf_joint",
]


class MujocoBridgeNode(Node):
    def __init__(self):
        super().__init__("mujoco_bridge_node")

        default_model_path = str(
            Path.home()
            / "robot-mpc-wbc-locomotion"
            / "assets"
            / "go1"
            / "scene.xml"
        )

        self.declare_parameter("model_path", default_model_path)
        self.declare_parameter("base_body", "trunk")
        self.declare_parameter("publish_rate_hz", 100.0)

        model_path = self.get_parameter("model_path").value
        base_body = self.get_parameter("base_body").value
        publish_rate_hz = float(self.get_parameter("publish_rate_hz").value)

        self.model = mujoco.MjModel.from_xml_path(model_path)
        self.data = mujoco.MjData(self.model)

        self.base_id = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_BODY, base_body
        )
        if self.base_id < 0:
            raise RuntimeError(f"base body not found: {base_body}")

        if self.model.nu != 12:
            self.get_logger().warn(f"Expected Go1 nu=12, got nu={self.model.nu}")

        self.torque_cmd = np.zeros(self.model.nu)

        self.joint_pub = self.create_publisher(JointState, "/go1/joint_states", 10)
        self.imu_pub = self.create_publisher(Imu, "/go1/imu", 10)
        self.base_pub = self.create_publisher(Float64MultiArray, "/go1/base_state", 10)
        self.contact_pub = self.create_publisher(Int32MultiArray, "/go1/foot_contacts", 10)
        self.time_pub = self.create_publisher(Float64, "/go1/sim_time", 10)

        self.torque_sub = self.create_subscription(
            Float64MultiArray,
            "/go1/joint_torque_cmd",
            self.on_torque_cmd,
            10,
        )

        self.timer = self.create_timer(1.0 / publish_rate_hz, self.on_timer)

        self.get_logger().info(f"Loaded model: {model_path}")
        self.get_logger().info(f"nq={self.model.nq}, nv={self.model.nv}, nu={self.model.nu}")
        self.get_logger().info(f"Using base body: {base_body}, body_id={self.base_id}")

    def on_torque_cmd(self, msg):
        cmd = np.asarray(msg.data, dtype=float)

        if cmd.shape[0] != self.model.nu:
            self.get_logger().warn(
                f"Ignore torque command length {cmd.shape[0]}, expected {self.model.nu}"
            )
            return

        self.torque_cmd[:] = cmd
        self.get_logger().info(
            f"Received torque command: norm={np.linalg.norm(self.torque_cmd):.4f}"
        )

    def on_timer(self):
        self.data.ctrl[:] = self.torque_cmd
        mujoco.mj_step(self.model, self.data)

        stamp = self.get_clock().now().to_msg()

        joint_msg = JointState()
        joint_msg.header.stamp = stamp
        joint_msg.name = JOINT_NAMES
        joint_msg.position = self.data.qpos[7:19].tolist()
        joint_msg.velocity = self.data.qvel[6:18].tolist()
        joint_msg.effort = self.data.ctrl[:12].tolist()
        self.joint_pub.publish(joint_msg)

        base_msg = Float64MultiArray()
        base_msg.data = [
            float(self.data.time),
            float(self.data.xpos[self.base_id, 0]),
            float(self.data.xpos[self.base_id, 1]),
            float(self.data.xpos[self.base_id, 2]),
            float(self.data.qpos[3]),
            float(self.data.qpos[4]),
            float(self.data.qpos[5]),
            float(self.data.qpos[6]),
            float(self.data.qvel[0]),
            float(self.data.qvel[1]),
            float(self.data.qvel[2]),
            float(self.data.qvel[3]),
            float(self.data.qvel[4]),
            float(self.data.qvel[5]),
        ]
        self.base_pub.publish(base_msg)

        imu_msg = Imu()
        imu_msg.header.stamp = stamp
        imu_msg.header.frame_id = "trunk"

        # Minimal Stage 1 IMU placeholder:
        # angular velocity uses MuJoCo floating-base angular velocity.
        imu_msg.angular_velocity.x = float(self.data.qvel[3])
        imu_msg.angular_velocity.y = float(self.data.qvel[4])
        imu_msg.angular_velocity.z = float(self.data.qvel[5])

        # Linear acceleration will be refined later when sensor definitions are added to MJCF.
        imu_msg.linear_acceleration.x = 0.0
        imu_msg.linear_acceleration.y = 0.0
        imu_msg.linear_acceleration.z = 0.0

        imu_msg.orientation.w = float(self.data.qpos[3])
        imu_msg.orientation.x = float(self.data.qpos[4])
        imu_msg.orientation.y = float(self.data.qpos[5])
        imu_msg.orientation.z = float(self.data.qpos[6])

        self.imu_pub.publish(imu_msg)

        contact_msg = Int32MultiArray()
        contact_msg.data = self.compute_foot_contacts()
        self.contact_pub.publish(contact_msg)

        time_msg = Float64()
        time_msg.data = float(self.data.time)
        self.time_pub.publish(time_msg)

    def compute_foot_contacts(self):
        contacts = [0, 0, 0, 0]
        foot_names = ["FR", "FL", "RR", "RL"]

        for i in range(self.data.ncon):
            c = self.data.contact[i]
            g1 = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_GEOM, c.geom1) or ""
            g2 = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_GEOM, c.geom2) or ""
            pair = f"{g1}|{g2}"

            for leg_id, foot_name in enumerate(foot_names):
                if "floor" in pair and foot_name in pair:
                    contacts[leg_id] = 1

        return contacts


def main():
    rclpy.init()
    node = MujocoBridgeNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
