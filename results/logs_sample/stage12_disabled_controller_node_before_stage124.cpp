#include <array>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <limits>
#include <memory>
#include <string>
#include <vector>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/imu.hpp"
#include "sensor_msgs/msg/joint_state.hpp"
#include "std_msgs/msg/float64.hpp"
#include "std_msgs/msg/float64_multi_array.hpp"
#include "std_msgs/msg/int32_multi_array.hpp"

#include "robot_mpc_wbc_cpp_controller/torque_safety.hpp"
#include "robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

using namespace std::chrono_literals;

class Go1DisabledControllerNode final : public rclcpp::Node {
public:
  Go1DisabledControllerNode() : Node("go1_disabled_controller_node") {
    declare_parameter<bool>("enable_torque_publisher", false);
    declare_parameter<bool>("confirm_torque_publisher_enable", false);

    zero_torque_dry_run_ = robot_mpc_wbc_cpp_controller::makeZeroTorqueDryRun();
    safe_torque_dry_run_ = robot_mpc_wbc_cpp_controller::makeZeroTorqueDryRun();
    torque_clamp_config_ = robot_mpc_wbc_cpp_controller::makeUniformTorqueClampConfig(10.0);

    joint_state_sub_ = create_subscription<sensor_msgs::msg::JointState>(
      "/go1/joint_states",
      10,
      [this](sensor_msgs::msg::JointState::SharedPtr msg) {
        joint_state_valid_ =
          msg->name.size() == kNumJoints &&
          msg->position.size() == kNumJoints &&
          msg->velocity.size() == kNumJoints;

        if (!msg->effort.empty()) {
          joint_state_valid_ = joint_state_valid_ && msg->effort.size() == kNumJoints;
        }

        if (joint_state_valid_) {
          joint_names_ = msg->name;
          joint_position_ = msg->position;
          joint_velocity_ = msg->velocity;
          joint_effort_ = msg->effort;
          last_joint_state_time_ = now();
        }
      });

    base_state_sub_ = create_subscription<std_msgs::msg::Float64MultiArray>(
      "/go1/base_state",
      10,
      [this](std_msgs::msg::Float64MultiArray::SharedPtr msg) {
        base_state_ = msg->data;
        base_state_valid_ = !base_state_.empty();
        if (base_state_valid_) {
          last_base_state_time_ = now();
        }
      });

    imu_sub_ = create_subscription<sensor_msgs::msg::Imu>(
      "/go1/imu",
      10,
      [this](sensor_msgs::msg::Imu::SharedPtr msg) {
        imu_valid_ =
          std::isfinite(msg->orientation.x) &&
          std::isfinite(msg->orientation.y) &&
          std::isfinite(msg->orientation.z) &&
          std::isfinite(msg->orientation.w) &&
          std::isfinite(msg->angular_velocity.x) &&
          std::isfinite(msg->angular_velocity.y) &&
          std::isfinite(msg->angular_velocity.z) &&
          std::isfinite(msg->linear_acceleration.x) &&
          std::isfinite(msg->linear_acceleration.y) &&
          std::isfinite(msg->linear_acceleration.z);

        if (imu_valid_) {
          last_imu_time_ = now();
        }
      });

    foot_contacts_sub_ = create_subscription<std_msgs::msg::Int32MultiArray>(
      "/go1/foot_contacts",
      10,
      [this](std_msgs::msg::Int32MultiArray::SharedPtr msg) {
        foot_contacts_valid_ = msg->data.size() == kNumLegs;
        if (foot_contacts_valid_) {
          for (std::size_t i = 0; i < kNumLegs; ++i) {
            foot_contacts_[i] = msg->data[i];
          }
          last_foot_contacts_time_ = now();
        }
      });

    sim_time_sub_ = create_subscription<std_msgs::msg::Float64>(
      "/go1/sim_time",
      10,
      [this](std_msgs::msg::Float64::SharedPtr msg) {
        sim_time_ = msg->data;
        sim_time_valid_ = std::isfinite(sim_time_);
        if (sim_time_valid_) {
          last_sim_time_msg_time_ = now();
        }
      });

    status_timer_ = create_wall_timer(
      1000ms,
      [this]() {
        updateManualEnableState();
        updateInternalSafeDryRunCommand();

        const bool state_ready =
          joint_state_valid_ &&
          base_state_valid_ &&
          imu_valid_ &&
          foot_contacts_valid_ &&
          sim_time_valid_;

        const auto dormant_msg = makeDormantSafeTorqueCommandMessage();
        const bool construct_allowed = dormantPublisherConstructAllowed();
        const bool publish_allowed = dormantPublishAllowed(state_ready);

        RCLCPP_INFO_THROTTLE(
          get_logger(),
          *get_clock(),
          5000,
          "disabled controller skeleton: state_ready=%d inputs_fresh=%d internal_safe_tau_size=%zu dormant_payload_size=%zu internal_safe_tau_max_abs=%.6f clamp_applied=%d enable_torque_publisher=%d confirm_torque_publisher_enable=%d manual_enable_active=%d dormant_publisher_path_skeleton_present=%d dormant_construct_allowed=%d dormant_publish_allowed=%d torque_publisher_enabled=0 uses_safety_utilities=1",
          state_ready,
          inputs_fresh_,
          safe_torque_dry_run_.size(),
          dormant_msg.data.size(),
          last_clamp_result_.max_abs_after_clamp,
          last_clamp_result_.clamp_applied,
          enable_torque_publisher_param_,
          confirm_torque_publisher_enable_param_,
          manual_enable_active_,
          dormantPublisherPathSkeletonPresent(),
          construct_allowed,
          publish_allowed);
      });

    RCLCPP_INFO(
      get_logger(),
      "Go1 disabled C++ controller skeleton started with dormant publisher-path skeleton. No ROS torque publisher is constructed.");
  }

private:
  static constexpr std::size_t kNumJoints = 12;
  static constexpr std::size_t kNumLegs = 4;
  static constexpr std::size_t kDormantTorquePayloadLength = 12;
  static constexpr bool kDormantPublisherPathSkeletonPresent = true;
  static constexpr bool kDormantPublisherConstructionAllowed = false;
  static constexpr bool kDormantPublishCallAllowed = false;
  static constexpr double kInputFreshnessTimeoutSeconds = 0.50;

  void updateManualEnableState() {
    enable_torque_publisher_param_ =
      get_parameter("enable_torque_publisher").as_bool();

    confirm_torque_publisher_enable_param_ =
      get_parameter("confirm_torque_publisher_enable").as_bool();

    manual_enable_active_ =
      enable_torque_publisher_param_ &&
      confirm_torque_publisher_enable_param_;
  }

  double messageAgeSeconds(const bool valid, const rclcpp::Time & stamp) const {
    if (!valid) {
      return std::numeric_limits<double>::infinity();
    }
    return (now() - stamp).seconds();
  }

  void updateInternalSafeDryRunCommand() {
    const std::array<double, 5> ages{
      messageAgeSeconds(joint_state_valid_, last_joint_state_time_),
      messageAgeSeconds(base_state_valid_, last_base_state_time_),
      messageAgeSeconds(imu_valid_, last_imu_time_),
      messageAgeSeconds(foot_contacts_valid_, last_foot_contacts_time_),
      messageAgeSeconds(sim_time_valid_, last_sim_time_msg_time_),
    };

    inputs_fresh_ =
      robot_mpc_wbc_cpp_controller::allInputsFresh(ages, kInputFreshnessTimeoutSeconds);

    const auto raw_command =
      inputs_fresh_
        ? zero_torque_dry_run_
        : robot_mpc_wbc_cpp_controller::watchdogFallbackZeroTorque();

    last_clamp_result_ =
      robot_mpc_wbc_cpp_controller::clampTorqueCommand(raw_command, torque_clamp_config_);

    safe_torque_dry_run_ = last_clamp_result_.tau;
  }

  bool dormantPublisherPathSkeletonPresent() const {
    return kDormantPublisherPathSkeletonPresent;
  }

  bool dormantPublisherConstructAllowed() const {
    return kDormantPublisherConstructionAllowed;
  }

  bool dormantPublishAllowed(const bool state_ready) const {
    (void)state_ready;
    return kDormantPublishCallAllowed;
  }

  std_msgs::msg::Float64MultiArray makeDormantSafeTorqueCommandMessage() const {
    std_msgs::msg::Float64MultiArray msg;
    msg.data.reserve(kDormantTorquePayloadLength);
    msg.data.assign(safe_torque_dry_run_.begin(), safe_torque_dry_run_.end());
    return msg;
  }

  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_state_sub_;
  rclcpp::Subscription<std_msgs::msg::Float64MultiArray>::SharedPtr base_state_sub_;
  rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
  rclcpp::Subscription<std_msgs::msg::Int32MultiArray>::SharedPtr foot_contacts_sub_;
  rclcpp::Subscription<std_msgs::msg::Float64>::SharedPtr sim_time_sub_;

  rclcpp::TimerBase::SharedPtr status_timer_;

  bool joint_state_valid_ = false;
  bool base_state_valid_ = false;
  bool imu_valid_ = false;
  bool foot_contacts_valid_ = false;
  bool sim_time_valid_ = false;
  bool inputs_fresh_ = false;

  bool enable_torque_publisher_param_ = false;
  bool confirm_torque_publisher_enable_param_ = false;
  bool manual_enable_active_ = false;

  rclcpp::Time last_joint_state_time_{0, 0, RCL_ROS_TIME};
  rclcpp::Time last_base_state_time_{0, 0, RCL_ROS_TIME};
  rclcpp::Time last_imu_time_{0, 0, RCL_ROS_TIME};
  rclcpp::Time last_foot_contacts_time_{0, 0, RCL_ROS_TIME};
  rclcpp::Time last_sim_time_msg_time_{0, 0, RCL_ROS_TIME};

  double sim_time_ = 0.0;

  std::vector<std::string> joint_names_;
  std::vector<double> joint_position_;
  std::vector<double> joint_velocity_;
  std::vector<double> joint_effort_;
  std::vector<double> base_state_;
  std::array<int32_t, kNumLegs> foot_contacts_{};

  robot_mpc_wbc_cpp_controller::TorqueVector zero_torque_dry_run_{};
  robot_mpc_wbc_cpp_controller::TorqueVector safe_torque_dry_run_{};
  robot_mpc_wbc_cpp_controller::TorqueClampConfig torque_clamp_config_{};
  robot_mpc_wbc_cpp_controller::TorqueClampResult last_clamp_result_{};
};

int main(int argc, char ** argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<Go1DisabledControllerNode>());
  rclcpp::shutdown();
  return 0;
}
