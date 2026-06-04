#include <array>
#include <chrono>
#include <cstddef>
#include <memory>
#include <string>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/imu.hpp"
#include "sensor_msgs/msg/joint_state.hpp"
#include "std_msgs/msg/float64.hpp"
#include "std_msgs/msg/float64_multi_array.hpp"
#include "std_msgs/msg/int32_multi_array.hpp"

using namespace std::chrono_literals;

class Go1InterfaceMirrorNode final : public rclcpp::Node {
public:
  Go1InterfaceMirrorNode() : Node("go1_interface_mirror_node") {
    joint_state_sub_ = create_subscription<sensor_msgs::msg::JointState>(
      "/go1/joint_states",
      10,
      [this](sensor_msgs::msg::JointState::SharedPtr msg) {
        last_joint_state_ok_ =
          msg->name.size() == kNumJoints &&
          msg->position.size() == kNumJoints &&
          msg->velocity.size() == kNumJoints;

        if (!msg->effort.empty()) {
          last_joint_state_ok_ = last_joint_state_ok_ && msg->effort.size() == kNumJoints;
        }

        if (!last_joint_state_ok_) {
          RCLCPP_WARN_THROTTLE(
            get_logger(),
            *get_clock(),
            2000,
            "joint_states schema mismatch: name=%zu position=%zu velocity=%zu effort=%zu",
            msg->name.size(),
            msg->position.size(),
            msg->velocity.size(),
            msg->effort.size());
        }
      });

    base_state_sub_ = create_subscription<std_msgs::msg::Float64MultiArray>(
      "/go1/base_state",
      10,
      [this](std_msgs::msg::Float64MultiArray::SharedPtr msg) {
        last_base_state_size_ = msg->data.size();
        last_base_state_ok_ = !msg->data.empty();

        if (!last_base_state_ok_) {
          RCLCPP_WARN_THROTTLE(
            get_logger(),
            *get_clock(),
            2000,
            "base_state is empty");
        }
      });

    imu_sub_ = create_subscription<sensor_msgs::msg::Imu>(
      "/go1/imu",
      10,
      [this](sensor_msgs::msg::Imu::SharedPtr msg) {
        const bool finite_orientation =
          std::isfinite(msg->orientation.x) &&
          std::isfinite(msg->orientation.y) &&
          std::isfinite(msg->orientation.z) &&
          std::isfinite(msg->orientation.w);

        const bool finite_angular_velocity =
          std::isfinite(msg->angular_velocity.x) &&
          std::isfinite(msg->angular_velocity.y) &&
          std::isfinite(msg->angular_velocity.z);

        const bool finite_linear_acceleration =
          std::isfinite(msg->linear_acceleration.x) &&
          std::isfinite(msg->linear_acceleration.y) &&
          std::isfinite(msg->linear_acceleration.z);

        last_imu_ok_ = finite_orientation && finite_angular_velocity && finite_linear_acceleration;

        if (!last_imu_ok_) {
          RCLCPP_WARN_THROTTLE(
            get_logger(),
            *get_clock(),
            2000,
            "imu contains non-finite values");
        }
      });

    foot_contacts_sub_ = create_subscription<std_msgs::msg::Int32MultiArray>(
      "/go1/foot_contacts",
      10,
      [this](std_msgs::msg::Int32MultiArray::SharedPtr msg) {
        last_foot_contacts_ok_ = msg->data.size() == kNumLegs;

        if (!last_foot_contacts_ok_) {
          RCLCPP_WARN_THROTTLE(
            get_logger(),
            *get_clock(),
            2000,
            "foot_contacts schema mismatch: size=%zu expected=%zu",
            msg->data.size(),
            kNumLegs);
        }
      });

    sim_time_sub_ = create_subscription<std_msgs::msg::Float64>(
      "/go1/sim_time",
      10,
      [this](std_msgs::msg::Float64::SharedPtr msg) {
        last_sim_time_ok_ = std::isfinite(msg->data);
      });

    torque_cmd_observer_sub_ = create_subscription<std_msgs::msg::Float64MultiArray>(
      "/go1/joint_torque_cmd",
      10,
      [this](std_msgs::msg::Float64MultiArray::SharedPtr msg) {
        last_torque_cmd_ok_ = msg->data.size() == kNumJoints;

        if (!last_torque_cmd_ok_) {
          RCLCPP_WARN_THROTTLE(
            get_logger(),
            *get_clock(),
            2000,
            "joint_torque_cmd schema mismatch: size=%zu expected=%zu",
            msg->data.size(),
            kNumJoints);
        }
      });

    status_timer_ = create_wall_timer(
      1000ms,
      [this]() {
        RCLCPP_INFO_THROTTLE(
          get_logger(),
          *get_clock(),
          5000,
          "mirror status: joint=%d base=%d base_size=%zu imu=%d contacts=%d sim_time=%d torque_cmd=%d. No torque publisher exists.",
          last_joint_state_ok_,
          last_base_state_ok_,
          last_base_state_size_,
          last_imu_ok_,
          last_foot_contacts_ok_,
          last_sim_time_ok_,
          last_torque_cmd_ok_);
      });

    RCLCPP_INFO(
      get_logger(),
      "Go1 C++ interface mirror node started. This node subscribes only and does not publish torque commands.");
  }

private:
  static constexpr std::size_t kNumJoints = 12;
  static constexpr std::size_t kNumLegs = 4;

  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_state_sub_;
  rclcpp::Subscription<std_msgs::msg::Float64MultiArray>::SharedPtr base_state_sub_;
  rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
  rclcpp::Subscription<std_msgs::msg::Int32MultiArray>::SharedPtr foot_contacts_sub_;
  rclcpp::Subscription<std_msgs::msg::Float64>::SharedPtr sim_time_sub_;
  rclcpp::Subscription<std_msgs::msg::Float64MultiArray>::SharedPtr torque_cmd_observer_sub_;

  rclcpp::TimerBase::SharedPtr status_timer_;

  bool last_joint_state_ok_ = false;
  bool last_base_state_ok_ = false;
  bool last_imu_ok_ = false;
  bool last_foot_contacts_ok_ = false;
  bool last_sim_time_ok_ = false;
  bool last_torque_cmd_ok_ = false;
  std::size_t last_base_state_size_ = 0;
};

int main(int argc, char ** argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<Go1InterfaceMirrorNode>());
  rclcpp::shutdown();
  return 0;
}
