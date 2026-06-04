# Stage 12.20A Source Anchor Inspection

- source: `/home/zanshi/robot-mpc-wbc-locomotion/ros2_ws/src/robot_mpc_wbc_cpp_controller/src/disabled_controller_node.cpp`
- pass: `True`
- fail_reasons: `[]`
- source_hash: `1970e55723158545b775a707b99f4e5801f80d96f93cf1f3301f5e27aa15d3e6`
- source_hash_matches_stage1219: `True`
- publish_call_count: `1`
- source_has_no_continuous_streaming_markers: `True`

## Key contexts


### publish_hits


center_line=319

```text
0309:     auto msg = makeStage1214ZeroSafeTorqueCommandMessage();
0310:     if (msg.data.size() != kDormantTorquePayloadLength) {
0311:       return false;
0312:     }
0313:     for (const auto value : msg.data) {
0314:       if (!std::isfinite(value)) {
0315:         return false;
0316:       }
0317:     }
0318: 
0319:     active_torque_cmd_publisher_->publish(msg);
0320:     return true;
0321:   }
0322: 
0323:   rclcpp::TimerBase::SharedPtr stage1214_one_shot_publish_timer_;
0324:   bool stage1214_bounded_publish_invoked_{false};
0325:   static constexpr bool kStage1214BoundedPublishCallImplemented = true;
0326:   static constexpr bool kStage1214ContinuousPublishImplemented = false;
0327: };
0328: 
0329: int main(int argc, char ** argv) {
```

### timer_hits


center_line=36

```text
0026:     declare_parameter<bool>("confirm_torque_publisher_enable", false);
0027: 
0028:     active_torque_cmd_publisher_ =
0029:       this->create_publisher<std_msgs::msg::Float64MultiArray>(
0030:         "/go1/joint_torque_cmd", rclcpp::QoS(1));
0031:     RCLCPP_INFO(
0032:       this->get_logger(),
0033:       "Stage 12.4 active torque publisher constructed without publish call; manual flags remain default false.");
0034: 
0035: 
0036:     stage1214_one_shot_publish_timer_ = this->create_wall_timer(
0037:       std::chrono::milliseconds(2500),
0038:       [this]() {
0039:         if (stage1214_one_shot_publish_timer_) {
0040:           stage1214_one_shot_publish_timer_->cancel();
0041:         }
0042:         const bool stage1214_enable =
0043:           this->get_parameter("enable_torque_publisher").as_bool();
0044:         const bool stage1214_confirm =
0045:           this->get_parameter("confirm_torque_publisher_enable").as_bool();
0046:         const bool stage1214_state_ready = true;
```

center_line=36

```text
0026:     declare_parameter<bool>("confirm_torque_publisher_enable", false);
0027: 
0028:     active_torque_cmd_publisher_ =
0029:       this->create_publisher<std_msgs::msg::Float64MultiArray>(
0030:         "/go1/joint_torque_cmd", rclcpp::QoS(1));
0031:     RCLCPP_INFO(
0032:       this->get_logger(),
0033:       "Stage 12.4 active torque publisher constructed without publish call; manual flags remain default false.");
0034: 
0035: 
0036:     stage1214_one_shot_publish_timer_ = this->create_wall_timer(
0037:       std::chrono::milliseconds(2500),
0038:       [this]() {
0039:         if (stage1214_one_shot_publish_timer_) {
0040:           stage1214_one_shot_publish_timer_->cancel();
0041:         }
0042:         const bool stage1214_enable =
0043:           this->get_parameter("enable_torque_publisher").as_bool();
0044:         const bool stage1214_confirm =
0045:           this->get_parameter("confirm_torque_publisher_enable").as_bool();
0046:         const bool stage1214_state_ready = true;
```

center_line=36

```text
0026:     declare_parameter<bool>("confirm_torque_publisher_enable", false);
0027: 
0028:     active_torque_cmd_publisher_ =
0029:       this->create_publisher<std_msgs::msg::Float64MultiArray>(
0030:         "/go1/joint_torque_cmd", rclcpp::QoS(1));
0031:     RCLCPP_INFO(
0032:       this->get_logger(),
0033:       "Stage 12.4 active torque publisher constructed without publish call; manual flags remain default false.");
0034: 
0035: 
0036:     stage1214_one_shot_publish_timer_ = this->create_wall_timer(
0037:       std::chrono::milliseconds(2500),
0038:       [this]() {
0039:         if (stage1214_one_shot_publish_timer_) {
0040:           stage1214_one_shot_publish_timer_->cancel();
0041:         }
0042:         const bool stage1214_enable =
0043:           this->get_parameter("enable_torque_publisher").as_bool();
0044:         const bool stage1214_confirm =
0045:           this->get_parameter("confirm_torque_publisher_enable").as_bool();
0046:         const bool stage1214_state_ready = true;
```

center_line=39

```text
0029:       this->create_publisher<std_msgs::msg::Float64MultiArray>(
0030:         "/go1/joint_torque_cmd", rclcpp::QoS(1));
0031:     RCLCPP_INFO(
0032:       this->get_logger(),
0033:       "Stage 12.4 active torque publisher constructed without publish call; manual flags remain default false.");
0034: 
0035: 
0036:     stage1214_one_shot_publish_timer_ = this->create_wall_timer(
0037:       std::chrono::milliseconds(2500),
0038:       [this]() {
0039:         if (stage1214_one_shot_publish_timer_) {
0040:           stage1214_one_shot_publish_timer_->cancel();
0041:         }
0042:         const bool stage1214_enable =
0043:           this->get_parameter("enable_torque_publisher").as_bool();
0044:         const bool stage1214_confirm =
0045:           this->get_parameter("confirm_torque_publisher_enable").as_bool();
0046:         const bool stage1214_state_ready = true;
0047:         stage1214_bounded_publish_invoked_ =
0048:           publishBoundedZeroSafeTorqueOnceIfAllowed(
0049:             stage1214_enable, stage1214_confirm, stage1214_state_ready);
```

### param_hits


center_line=25

```text
0015: #include "std_msgs/msg/int32_multi_array.hpp"
0016: 
0017: #include "robot_mpc_wbc_cpp_controller/torque_safety.hpp"
0018: #include "robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"
0019: 
0020: using namespace std::chrono_literals;
0021: 
0022: class Go1DisabledControllerNode final : public rclcpp::Node {
0023: public:
0024:   Go1DisabledControllerNode() : Node("go1_disabled_controller_node") {
0025:     declare_parameter<bool>("enable_torque_publisher", false);
0026:     declare_parameter<bool>("confirm_torque_publisher_enable", false);
0027: 
0028:     active_torque_cmd_publisher_ =
0029:       this->create_publisher<std_msgs::msg::Float64MultiArray>(
0030:         "/go1/joint_torque_cmd", rclcpp::QoS(1));
0031:     RCLCPP_INFO(
0032:       this->get_logger(),
0033:       "Stage 12.4 active torque publisher constructed without publish call; manual flags remain default false.");
0034: 
0035: 
```

center_line=25

```text
0015: #include "std_msgs/msg/int32_multi_array.hpp"
0016: 
0017: #include "robot_mpc_wbc_cpp_controller/torque_safety.hpp"
0018: #include "robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"
0019: 
0020: using namespace std::chrono_literals;
0021: 
0022: class Go1DisabledControllerNode final : public rclcpp::Node {
0023: public:
0024:   Go1DisabledControllerNode() : Node("go1_disabled_controller_node") {
0025:     declare_parameter<bool>("enable_torque_publisher", false);
0026:     declare_parameter<bool>("confirm_torque_publisher_enable", false);
0027: 
0028:     active_torque_cmd_publisher_ =
0029:       this->create_publisher<std_msgs::msg::Float64MultiArray>(
0030:         "/go1/joint_torque_cmd", rclcpp::QoS(1));
0031:     RCLCPP_INFO(
0032:       this->get_logger(),
0033:       "Stage 12.4 active torque publisher constructed without publish call; manual flags remain default false.");
0034: 
0035: 
```

center_line=26

```text
0016: 
0017: #include "robot_mpc_wbc_cpp_controller/torque_safety.hpp"
0018: #include "robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"
0019: 
0020: using namespace std::chrono_literals;
0021: 
0022: class Go1DisabledControllerNode final : public rclcpp::Node {
0023: public:
0024:   Go1DisabledControllerNode() : Node("go1_disabled_controller_node") {
0025:     declare_parameter<bool>("enable_torque_publisher", false);
0026:     declare_parameter<bool>("confirm_torque_publisher_enable", false);
0027: 
0028:     active_torque_cmd_publisher_ =
0029:       this->create_publisher<std_msgs::msg::Float64MultiArray>(
0030:         "/go1/joint_torque_cmd", rclcpp::QoS(1));
0031:     RCLCPP_INFO(
0032:       this->get_logger(),
0033:       "Stage 12.4 active torque publisher constructed without publish call; manual flags remain default false.");
0034: 
0035: 
0036:     stage1214_one_shot_publish_timer_ = this->create_wall_timer(
```

center_line=26

```text
0016: 
0017: #include "robot_mpc_wbc_cpp_controller/torque_safety.hpp"
0018: #include "robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"
0019: 
0020: using namespace std::chrono_literals;
0021: 
0022: class Go1DisabledControllerNode final : public rclcpp::Node {
0023: public:
0024:   Go1DisabledControllerNode() : Node("go1_disabled_controller_node") {
0025:     declare_parameter<bool>("enable_torque_publisher", false);
0026:     declare_parameter<bool>("confirm_torque_publisher_enable", false);
0027: 
0028:     active_torque_cmd_publisher_ =
0029:       this->create_publisher<std_msgs::msg::Float64MultiArray>(
0030:         "/go1/joint_torque_cmd", rclcpp::QoS(1));
0031:     RCLCPP_INFO(
0032:       this->get_logger(),
0033:       "Stage 12.4 active torque publisher constructed without publish call; manual flags remain default false.");
0034: 
0035: 
0036:     stage1214_one_shot_publish_timer_ = this->create_wall_timer(
```

### helper_hits


center_line=17

```text
0007: #include <string>
0008: #include <vector>
0009: 
0010: #include "rclcpp/rclcpp.hpp"
0011: #include "sensor_msgs/msg/imu.hpp"
0012: #include "sensor_msgs/msg/joint_state.hpp"
0013: #include "std_msgs/msg/float64.hpp"
0014: #include "std_msgs/msg/float64_multi_array.hpp"
0015: #include "std_msgs/msg/int32_multi_array.hpp"
0016: 
0017: #include "robot_mpc_wbc_cpp_controller/torque_safety.hpp"
0018: #include "robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"
0019: 
0020: using namespace std::chrono_literals;
0021: 
0022: class Go1DisabledControllerNode final : public rclcpp::Node {
0023: public:
0024:   Go1DisabledControllerNode() : Node("go1_disabled_controller_node") {
0025:     declare_parameter<bool>("enable_torque_publisher", false);
0026:     declare_parameter<bool>("confirm_torque_publisher_enable", false);
0027: 
```

center_line=18

```text
0008: #include <vector>
0009: 
0010: #include "rclcpp/rclcpp.hpp"
0011: #include "sensor_msgs/msg/imu.hpp"
0012: #include "sensor_msgs/msg/joint_state.hpp"
0013: #include "std_msgs/msg/float64.hpp"
0014: #include "std_msgs/msg/float64_multi_array.hpp"
0015: #include "std_msgs/msg/int32_multi_array.hpp"
0016: 
0017: #include "robot_mpc_wbc_cpp_controller/torque_safety.hpp"
0018: #include "robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"
0019: 
0020: using namespace std::chrono_literals;
0021: 
0022: class Go1DisabledControllerNode final : public rclcpp::Node {
0023: public:
0024:   Go1DisabledControllerNode() : Node("go1_disabled_controller_node") {
0025:     declare_parameter<bool>("enable_torque_publisher", false);
0026:     declare_parameter<bool>("confirm_torque_publisher_enable", false);
0027: 
0028:     active_torque_cmd_publisher_ =
```

center_line=25

```text
0015: #include "std_msgs/msg/int32_multi_array.hpp"
0016: 
0017: #include "robot_mpc_wbc_cpp_controller/torque_safety.hpp"
0018: #include "robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"
0019: 
0020: using namespace std::chrono_literals;
0021: 
0022: class Go1DisabledControllerNode final : public rclcpp::Node {
0023: public:
0024:   Go1DisabledControllerNode() : Node("go1_disabled_controller_node") {
0025:     declare_parameter<bool>("enable_torque_publisher", false);
0026:     declare_parameter<bool>("confirm_torque_publisher_enable", false);
0027: 
0028:     active_torque_cmd_publisher_ =
0029:       this->create_publisher<std_msgs::msg::Float64MultiArray>(
0030:         "/go1/joint_torque_cmd", rclcpp::QoS(1));
0031:     RCLCPP_INFO(
0032:       this->get_logger(),
0033:       "Stage 12.4 active torque publisher constructed without publish call; manual flags remain default false.");
0034: 
0035: 
```

center_line=26

```text
0016: 
0017: #include "robot_mpc_wbc_cpp_controller/torque_safety.hpp"
0018: #include "robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"
0019: 
0020: using namespace std::chrono_literals;
0021: 
0022: class Go1DisabledControllerNode final : public rclcpp::Node {
0023: public:
0024:   Go1DisabledControllerNode() : Node("go1_disabled_controller_node") {
0025:     declare_parameter<bool>("enable_torque_publisher", false);
0026:     declare_parameter<bool>("confirm_torque_publisher_enable", false);
0027: 
0028:     active_torque_cmd_publisher_ =
0029:       this->create_publisher<std_msgs::msg::Float64MultiArray>(
0030:         "/go1/joint_torque_cmd", rclcpp::QoS(1));
0031:     RCLCPP_INFO(
0032:       this->get_logger(),
0033:       "Stage 12.4 active torque publisher constructed without publish call; manual flags remain default false.");
0034: 
0035: 
0036:     stage1214_one_shot_publish_timer_ = this->create_wall_timer(
```

### continuous_hits
