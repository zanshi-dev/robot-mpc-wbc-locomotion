# Stage 12.20B-R1 Source Structure Inspection

- pass: `True`
- fail_reasons: `[]`
- source_hash: `1970e55723158545b775a707b99f4e5801f80d96f93cf1f3301f5e27aa15d3e6`
- source_hash_matches_stage1219: `True`
- publish_call_count: `1`

## Context hits


### zero_safe line 17

```text
0001: #include <array>
0002: #include <chrono>
0003: #include <cmath>
0004: #include <cstddef>
0005: #include <limits>
0006: #include <memory>
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
0028:     active_torque_cmd_publisher_ =
0029:       this->create_publisher<std_msgs::msg::Float64MultiArray>(
0030:         "/go1/joint_torque_cmd", rclcpp::QoS(1));
0031:     RCLCPP_INFO(
0032:       this->get_logger(),
0033:       "Stage 12.4 active torque publisher constructed without publish call; manual flags remain default false.");
```

### zero_safe line 18

```text
0002: #include <chrono>
0003: #include <cmath>
0004: #include <cstddef>
0005: #include <limits>
0006: #include <memory>
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
0028:     active_torque_cmd_publisher_ =
0029:       this->create_publisher<std_msgs::msg::Float64MultiArray>(
0030:         "/go1/joint_torque_cmd", rclcpp::QoS(1));
0031:     RCLCPP_INFO(
0032:       this->get_logger(),
0033:       "Stage 12.4 active torque publisher constructed without publish call; manual flags remain default false.");
0034: 
```

### class_or_struct line 22

```text
0006: #include <memory>
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
```

### rclcpp_node line 22

```text
0006: #include <memory>
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
```

### public line 23

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
```

### constructor_hint line 24

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
```

### publisher_member line 25

```text
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
```

### parameter line 25

```text
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
```

### publisher_member line 26

```text
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
```

### parameter line 26

```text
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
```

### publisher_member line 28

```text
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
```

### zero_safe line 29

```text
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
```

### publisher_member line 30

```text
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

### publisher_member line 33

```text
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

### timer line 36

```text
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
0050:       });
0051: 
0052:     zero_torque_dry_run_ = robot_mpc_wbc_cpp_controller::makeZeroTorqueDryRun();
```

### timer line 39

```text
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
0050:       });
0051: 
0052:     zero_torque_dry_run_ = robot_mpc_wbc_cpp_controller::makeZeroTorqueDryRun();
0053:     safe_torque_dry_run_ = robot_mpc_wbc_cpp_controller::makeZeroTorqueDryRun();
0054:     torque_clamp_config_ = robot_mpc_wbc_cpp_controller::makeUniformTorqueClampConfig(10.0);
0055: 
```

### timer line 40

```text
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
0050:       });
0051: 
0052:     zero_torque_dry_run_ = robot_mpc_wbc_cpp_controller::makeZeroTorqueDryRun();
0053:     safe_torque_dry_run_ = robot_mpc_wbc_cpp_controller::makeZeroTorqueDryRun();
0054:     torque_clamp_config_ = robot_mpc_wbc_cpp_controller::makeUniformTorqueClampConfig(10.0);
0055: 
0056:     joint_state_sub_ = create_subscription<sensor_msgs::msg::JointState>(
```

### publisher_member line 43

```text
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
0047:         stage1214_bounded_publish_invoked_ =
0048:           publishBoundedZeroSafeTorqueOnceIfAllowed(
0049:             stage1214_enable, stage1214_confirm, stage1214_state_ready);
0050:       });
0051: 
0052:     zero_torque_dry_run_ = robot_mpc_wbc_cpp_controller::makeZeroTorqueDryRun();
0053:     safe_torque_dry_run_ = robot_mpc_wbc_cpp_controller::makeZeroTorqueDryRun();
0054:     torque_clamp_config_ = robot_mpc_wbc_cpp_controller::makeUniformTorqueClampConfig(10.0);
0055: 
0056:     joint_state_sub_ = create_subscription<sensor_msgs::msg::JointState>(
0057:       "/go1/joint_states",
0058:       10,
0059:       [this](sensor_msgs::msg::JointState::SharedPtr msg) {
```

### parameter line 43

```text
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
0047:         stage1214_bounded_publish_invoked_ =
0048:           publishBoundedZeroSafeTorqueOnceIfAllowed(
0049:             stage1214_enable, stage1214_confirm, stage1214_state_ready);
0050:       });
0051: 
0052:     zero_torque_dry_run_ = robot_mpc_wbc_cpp_controller::makeZeroTorqueDryRun();
0053:     safe_torque_dry_run_ = robot_mpc_wbc_cpp_controller::makeZeroTorqueDryRun();
0054:     torque_clamp_config_ = robot_mpc_wbc_cpp_controller::makeUniformTorqueClampConfig(10.0);
0055: 
0056:     joint_state_sub_ = create_subscription<sensor_msgs::msg::JointState>(
0057:       "/go1/joint_states",
0058:       10,
0059:       [this](sensor_msgs::msg::JointState::SharedPtr msg) {
```

### publisher_member line 45

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
0050:       });
0051: 
0052:     zero_torque_dry_run_ = robot_mpc_wbc_cpp_controller::makeZeroTorqueDryRun();
0053:     safe_torque_dry_run_ = robot_mpc_wbc_cpp_controller::makeZeroTorqueDryRun();
0054:     torque_clamp_config_ = robot_mpc_wbc_cpp_controller::makeUniformTorqueClampConfig(10.0);
0055: 
0056:     joint_state_sub_ = create_subscription<sensor_msgs::msg::JointState>(
0057:       "/go1/joint_states",
0058:       10,
0059:       [this](sensor_msgs::msg::JointState::SharedPtr msg) {
0060:         joint_state_valid_ =
0061:           msg->name.size() == kNumJoints &&
```

### parameter line 45

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
0050:       });
0051: 
0052:     zero_torque_dry_run_ = robot_mpc_wbc_cpp_controller::makeZeroTorqueDryRun();
0053:     safe_torque_dry_run_ = robot_mpc_wbc_cpp_controller::makeZeroTorqueDryRun();
0054:     torque_clamp_config_ = robot_mpc_wbc_cpp_controller::makeUniformTorqueClampConfig(10.0);
0055: 
0056:     joint_state_sub_ = create_subscription<sensor_msgs::msg::JointState>(
0057:       "/go1/joint_states",
0058:       10,
0059:       [this](sensor_msgs::msg::JointState::SharedPtr msg) {
0060:         joint_state_valid_ =
0061:           msg->name.size() == kNumJoints &&
```

### zero_safe line 47

```text
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
0050:       });
0051: 
0052:     zero_torque_dry_run_ = robot_mpc_wbc_cpp_controller::makeZeroTorqueDryRun();
0053:     safe_torque_dry_run_ = robot_mpc_wbc_cpp_controller::makeZeroTorqueDryRun();
0054:     torque_clamp_config_ = robot_mpc_wbc_cpp_controller::makeUniformTorqueClampConfig(10.0);
0055: 
0056:     joint_state_sub_ = create_subscription<sensor_msgs::msg::JointState>(
0057:       "/go1/joint_states",
0058:       10,
0059:       [this](sensor_msgs::msg::JointState::SharedPtr msg) {
0060:         joint_state_valid_ =
0061:           msg->name.size() == kNumJoints &&
0062:           msg->position.size() == kNumJoints &&
0063:           msg->velocity.size() == kNumJoints;
```

### zero_safe line 52

```text
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
0050:       });
0051: 
0052:     zero_torque_dry_run_ = robot_mpc_wbc_cpp_controller::makeZeroTorqueDryRun();
0053:     safe_torque_dry_run_ = robot_mpc_wbc_cpp_controller::makeZeroTorqueDryRun();
0054:     torque_clamp_config_ = robot_mpc_wbc_cpp_controller::makeUniformTorqueClampConfig(10.0);
0055: 
0056:     joint_state_sub_ = create_subscription<sensor_msgs::msg::JointState>(
0057:       "/go1/joint_states",
0058:       10,
0059:       [this](sensor_msgs::msg::JointState::SharedPtr msg) {
0060:         joint_state_valid_ =
0061:           msg->name.size() == kNumJoints &&
0062:           msg->position.size() == kNumJoints &&
0063:           msg->velocity.size() == kNumJoints;
0064: 
0065:         if (!msg->effort.empty()) {
0066:           joint_state_valid_ = joint_state_valid_ && msg->effort.size() == kNumJoints;
0067:         }
0068: 
```

### zero_safe line 53

```text
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
0050:       });
0051: 
0052:     zero_torque_dry_run_ = robot_mpc_wbc_cpp_controller::makeZeroTorqueDryRun();
0053:     safe_torque_dry_run_ = robot_mpc_wbc_cpp_controller::makeZeroTorqueDryRun();
0054:     torque_clamp_config_ = robot_mpc_wbc_cpp_controller::makeUniformTorqueClampConfig(10.0);
0055: 
0056:     joint_state_sub_ = create_subscription<sensor_msgs::msg::JointState>(
0057:       "/go1/joint_states",
0058:       10,
0059:       [this](sensor_msgs::msg::JointState::SharedPtr msg) {
0060:         joint_state_valid_ =
0061:           msg->name.size() == kNumJoints &&
0062:           msg->position.size() == kNumJoints &&
0063:           msg->velocity.size() == kNumJoints;
0064: 
0065:         if (!msg->effort.empty()) {
0066:           joint_state_valid_ = joint_state_valid_ && msg->effort.size() == kNumJoints;
0067:         }
0068: 
0069:         if (joint_state_valid_) {
```

### zero_safe line 78

```text
0062:           msg->position.size() == kNumJoints &&
0063:           msg->velocity.size() == kNumJoints;
0064: 
0065:         if (!msg->effort.empty()) {
0066:           joint_state_valid_ = joint_state_valid_ && msg->effort.size() == kNumJoints;
0067:         }
0068: 
0069:         if (joint_state_valid_) {
0070:           joint_names_ = msg->name;
0071:           joint_position_ = msg->position;
0072:           joint_velocity_ = msg->velocity;
0073:           joint_effort_ = msg->effort;
0074:           last_joint_state_time_ = now();
0075:         }
0076:       });
0077: 
0078:     base_state_sub_ = create_subscription<std_msgs::msg::Float64MultiArray>(
0079:       "/go1/base_state",
0080:       10,
0081:       [this](std_msgs::msg::Float64MultiArray::SharedPtr msg) {
0082:         base_state_ = msg->data;
0083:         base_state_valid_ = !base_state_.empty();
0084:         if (base_state_valid_) {
0085:           last_base_state_time_ = now();
0086:         }
0087:       });
0088: 
0089:     imu_sub_ = create_subscription<sensor_msgs::msg::Imu>(
0090:       "/go1/imu",
0091:       10,
0092:       [this](sensor_msgs::msg::Imu::SharedPtr msg) {
0093:         imu_valid_ =
0094:           std::isfinite(msg->orientation.x) &&
```

### zero_safe line 81

```text
0065:         if (!msg->effort.empty()) {
0066:           joint_state_valid_ = joint_state_valid_ && msg->effort.size() == kNumJoints;
0067:         }
0068: 
0069:         if (joint_state_valid_) {
0070:           joint_names_ = msg->name;
0071:           joint_position_ = msg->position;
0072:           joint_velocity_ = msg->velocity;
0073:           joint_effort_ = msg->effort;
0074:           last_joint_state_time_ = now();
0075:         }
0076:       });
0077: 
0078:     base_state_sub_ = create_subscription<std_msgs::msg::Float64MultiArray>(
0079:       "/go1/base_state",
0080:       10,
0081:       [this](std_msgs::msg::Float64MultiArray::SharedPtr msg) {
0082:         base_state_ = msg->data;
0083:         base_state_valid_ = !base_state_.empty();
0084:         if (base_state_valid_) {
0085:           last_base_state_time_ = now();
0086:         }
0087:       });
0088: 
0089:     imu_sub_ = create_subscription<sensor_msgs::msg::Imu>(
0090:       "/go1/imu",
0091:       10,
0092:       [this](sensor_msgs::msg::Imu::SharedPtr msg) {
0093:         imu_valid_ =
0094:           std::isfinite(msg->orientation.x) &&
0095:           std::isfinite(msg->orientation.y) &&
0096:           std::isfinite(msg->orientation.z) &&
0097:           std::isfinite(msg->orientation.w) &&
```

### timer line 134

```text
0118:           }
0119:           last_foot_contacts_time_ = now();
0120:         }
0121:       });
0122: 
0123:     sim_time_sub_ = create_subscription<std_msgs::msg::Float64>(
0124:       "/go1/sim_time",
0125:       10,
0126:       [this](std_msgs::msg::Float64::SharedPtr msg) {
0127:         sim_time_ = msg->data;
0128:         sim_time_valid_ = std::isfinite(sim_time_);
0129:         if (sim_time_valid_) {
0130:           last_sim_time_msg_time_ = now();
0131:         }
0132:       });
0133: 
0134:     status_timer_ = create_wall_timer(
0135:       1000ms,
0136:       [this]() {
0137:         updateManualEnableState();
0138:         updateInternalSafeDryRunCommand();
0139: 
0140:         const bool state_ready =
0141:           joint_state_valid_ &&
0142:           base_state_valid_ &&
0143:           imu_valid_ &&
0144:           foot_contacts_valid_ &&
0145:           sim_time_valid_;
0146: 
0147:         const auto dormant_msg = makeDormantSafeTorqueCommandMessage();
0148:         const bool construct_allowed = dormantPublisherConstructAllowed();
0149:         const bool publish_allowed = dormantPublishAllowed(state_ready);
0150: 
```

### publisher_member line 155

```text
0139: 
0140:         const bool state_ready =
0141:           joint_state_valid_ &&
0142:           base_state_valid_ &&
0143:           imu_valid_ &&
0144:           foot_contacts_valid_ &&
0145:           sim_time_valid_;
0146: 
0147:         const auto dormant_msg = makeDormantSafeTorqueCommandMessage();
0148:         const bool construct_allowed = dormantPublisherConstructAllowed();
0149:         const bool publish_allowed = dormantPublishAllowed(state_ready);
0150: 
0151:         RCLCPP_INFO_THROTTLE(
0152:           get_logger(),
0153:           *get_clock(),
0154:           5000,
0155:           "disabled controller skeleton: state_ready=%d inputs_fresh=%d internal_safe_tau_size=%zu dormant_payload_size=%zu internal_safe_tau_max_abs=%.6f clamp_applied=%d enable_torque_publisher=%d confirm_torque_publisher_enable=%d manual_enable_active=%d dormant_publisher_path_skeleton_present=%d dormant_construct_allowed=%d dormant_publish_allowed=%d torque_publisher_enabled=0 uses_safety_utilities=1",
0156:           state_ready,
0157:           inputs_fresh_,
0158:           safe_torque_dry_run_.size(),
0159:           dormant_msg.data.size(),
0160:           last_clamp_result_.max_abs_after_clamp,
0161:           last_clamp_result_.clamp_applied,
0162:           enable_torque_publisher_param_,
0163:           confirm_torque_publisher_enable_param_,
0164:           manual_enable_active_,
0165:           dormantPublisherPathSkeletonPresent(),
0166:           construct_allowed,
0167:           publish_allowed);
0168:       });
0169: 
0170:     RCLCPP_INFO(
0171:       get_logger(),
```

### parameter line 155

```text
0139: 
0140:         const bool state_ready =
0141:           joint_state_valid_ &&
0142:           base_state_valid_ &&
0143:           imu_valid_ &&
0144:           foot_contacts_valid_ &&
0145:           sim_time_valid_;
0146: 
0147:         const auto dormant_msg = makeDormantSafeTorqueCommandMessage();
0148:         const bool construct_allowed = dormantPublisherConstructAllowed();
0149:         const bool publish_allowed = dormantPublishAllowed(state_ready);
0150: 
0151:         RCLCPP_INFO_THROTTLE(
0152:           get_logger(),
0153:           *get_clock(),
0154:           5000,
0155:           "disabled controller skeleton: state_ready=%d inputs_fresh=%d internal_safe_tau_size=%zu dormant_payload_size=%zu internal_safe_tau_max_abs=%.6f clamp_applied=%d enable_torque_publisher=%d confirm_torque_publisher_enable=%d manual_enable_active=%d dormant_publisher_path_skeleton_present=%d dormant_construct_allowed=%d dormant_publish_allowed=%d torque_publisher_enabled=0 uses_safety_utilities=1",
0156:           state_ready,
0157:           inputs_fresh_,
0158:           safe_torque_dry_run_.size(),
0159:           dormant_msg.data.size(),
0160:           last_clamp_result_.max_abs_after_clamp,
0161:           last_clamp_result_.clamp_applied,
0162:           enable_torque_publisher_param_,
0163:           confirm_torque_publisher_enable_param_,
0164:           manual_enable_active_,
0165:           dormantPublisherPathSkeletonPresent(),
0166:           construct_allowed,
0167:           publish_allowed);
0168:       });
0169: 
0170:     RCLCPP_INFO(
0171:       get_logger(),
```

### zero_safe line 155

```text
0139: 
0140:         const bool state_ready =
0141:           joint_state_valid_ &&
0142:           base_state_valid_ &&
0143:           imu_valid_ &&
0144:           foot_contacts_valid_ &&
0145:           sim_time_valid_;
0146: 
0147:         const auto dormant_msg = makeDormantSafeTorqueCommandMessage();
0148:         const bool construct_allowed = dormantPublisherConstructAllowed();
0149:         const bool publish_allowed = dormantPublishAllowed(state_ready);
0150: 
0151:         RCLCPP_INFO_THROTTLE(
0152:           get_logger(),
0153:           *get_clock(),
0154:           5000,
0155:           "disabled controller skeleton: state_ready=%d inputs_fresh=%d internal_safe_tau_size=%zu dormant_payload_size=%zu internal_safe_tau_max_abs=%.6f clamp_applied=%d enable_torque_publisher=%d confirm_torque_publisher_enable=%d manual_enable_active=%d dormant_publisher_path_skeleton_present=%d dormant_construct_allowed=%d dormant_publish_allowed=%d torque_publisher_enabled=0 uses_safety_utilities=1",
0156:           state_ready,
0157:           inputs_fresh_,
0158:           safe_torque_dry_run_.size(),
0159:           dormant_msg.data.size(),
0160:           last_clamp_result_.max_abs_after_clamp,
0161:           last_clamp_result_.clamp_applied,
0162:           enable_torque_publisher_param_,
0163:           confirm_torque_publisher_enable_param_,
0164:           manual_enable_active_,
0165:           dormantPublisherPathSkeletonPresent(),
0166:           construct_allowed,
0167:           publish_allowed);
0168:       });
0169: 
0170:     RCLCPP_INFO(
0171:       get_logger(),
```

### zero_safe line 158

```text
0142:           base_state_valid_ &&
0143:           imu_valid_ &&
0144:           foot_contacts_valid_ &&
0145:           sim_time_valid_;
0146: 
0147:         const auto dormant_msg = makeDormantSafeTorqueCommandMessage();
0148:         const bool construct_allowed = dormantPublisherConstructAllowed();
0149:         const bool publish_allowed = dormantPublishAllowed(state_ready);
0150: 
0151:         RCLCPP_INFO_THROTTLE(
0152:           get_logger(),
0153:           *get_clock(),
0154:           5000,
0155:           "disabled controller skeleton: state_ready=%d inputs_fresh=%d internal_safe_tau_size=%zu dormant_payload_size=%zu internal_safe_tau_max_abs=%.6f clamp_applied=%d enable_torque_publisher=%d confirm_torque_publisher_enable=%d manual_enable_active=%d dormant_publisher_path_skeleton_present=%d dormant_construct_allowed=%d dormant_publish_allowed=%d torque_publisher_enabled=0 uses_safety_utilities=1",
0156:           state_ready,
0157:           inputs_fresh_,
0158:           safe_torque_dry_run_.size(),
0159:           dormant_msg.data.size(),
0160:           last_clamp_result_.max_abs_after_clamp,
0161:           last_clamp_result_.clamp_applied,
0162:           enable_torque_publisher_param_,
0163:           confirm_torque_publisher_enable_param_,
0164:           manual_enable_active_,
0165:           dormantPublisherPathSkeletonPresent(),
0166:           construct_allowed,
0167:           publish_allowed);
0168:       });
0169: 
0170:     RCLCPP_INFO(
0171:       get_logger(),
0172:       "Go1 disabled C++ controller skeleton started with dormant publisher-path skeleton. No ROS torque publisher is constructed.");
0173:   }
0174: 
```

### publisher_member line 162

```text
0146: 
0147:         const auto dormant_msg = makeDormantSafeTorqueCommandMessage();
0148:         const bool construct_allowed = dormantPublisherConstructAllowed();
0149:         const bool publish_allowed = dormantPublishAllowed(state_ready);
0150: 
0151:         RCLCPP_INFO_THROTTLE(
0152:           get_logger(),
0153:           *get_clock(),
0154:           5000,
0155:           "disabled controller skeleton: state_ready=%d inputs_fresh=%d internal_safe_tau_size=%zu dormant_payload_size=%zu internal_safe_tau_max_abs=%.6f clamp_applied=%d enable_torque_publisher=%d confirm_torque_publisher_enable=%d manual_enable_active=%d dormant_publisher_path_skeleton_present=%d dormant_construct_allowed=%d dormant_publish_allowed=%d torque_publisher_enabled=0 uses_safety_utilities=1",
0156:           state_ready,
0157:           inputs_fresh_,
0158:           safe_torque_dry_run_.size(),
0159:           dormant_msg.data.size(),
0160:           last_clamp_result_.max_abs_after_clamp,
0161:           last_clamp_result_.clamp_applied,
0162:           enable_torque_publisher_param_,
0163:           confirm_torque_publisher_enable_param_,
0164:           manual_enable_active_,
0165:           dormantPublisherPathSkeletonPresent(),
0166:           construct_allowed,
0167:           publish_allowed);
0168:       });
0169: 
0170:     RCLCPP_INFO(
0171:       get_logger(),
0172:       "Go1 disabled C++ controller skeleton started with dormant publisher-path skeleton. No ROS torque publisher is constructed.");
0173:   }
0174: 
0175: private:
0176:   static constexpr std::size_t kNumJoints = 12;
0177:   static constexpr std::size_t kNumLegs = 4;
0178:   static constexpr std::size_t kDormantTorquePayloadLength = 12;
```

### parameter line 162

```text
0146: 
0147:         const auto dormant_msg = makeDormantSafeTorqueCommandMessage();
0148:         const bool construct_allowed = dormantPublisherConstructAllowed();
0149:         const bool publish_allowed = dormantPublishAllowed(state_ready);
0150: 
0151:         RCLCPP_INFO_THROTTLE(
0152:           get_logger(),
0153:           *get_clock(),
0154:           5000,
0155:           "disabled controller skeleton: state_ready=%d inputs_fresh=%d internal_safe_tau_size=%zu dormant_payload_size=%zu internal_safe_tau_max_abs=%.6f clamp_applied=%d enable_torque_publisher=%d confirm_torque_publisher_enable=%d manual_enable_active=%d dormant_publisher_path_skeleton_present=%d dormant_construct_allowed=%d dormant_publish_allowed=%d torque_publisher_enabled=0 uses_safety_utilities=1",
0156:           state_ready,
0157:           inputs_fresh_,
0158:           safe_torque_dry_run_.size(),
0159:           dormant_msg.data.size(),
0160:           last_clamp_result_.max_abs_after_clamp,
0161:           last_clamp_result_.clamp_applied,
0162:           enable_torque_publisher_param_,
0163:           confirm_torque_publisher_enable_param_,
0164:           manual_enable_active_,
0165:           dormantPublisherPathSkeletonPresent(),
0166:           construct_allowed,
0167:           publish_allowed);
0168:       });
0169: 
0170:     RCLCPP_INFO(
0171:       get_logger(),
0172:       "Go1 disabled C++ controller skeleton started with dormant publisher-path skeleton. No ROS torque publisher is constructed.");
0173:   }
0174: 
0175: private:
0176:   static constexpr std::size_t kNumJoints = 12;
0177:   static constexpr std::size_t kNumLegs = 4;
0178:   static constexpr std::size_t kDormantTorquePayloadLength = 12;
```

### publisher_member line 163

```text
0147:         const auto dormant_msg = makeDormantSafeTorqueCommandMessage();
0148:         const bool construct_allowed = dormantPublisherConstructAllowed();
0149:         const bool publish_allowed = dormantPublishAllowed(state_ready);
0150: 
0151:         RCLCPP_INFO_THROTTLE(
0152:           get_logger(),
0153:           *get_clock(),
0154:           5000,
0155:           "disabled controller skeleton: state_ready=%d inputs_fresh=%d internal_safe_tau_size=%zu dormant_payload_size=%zu internal_safe_tau_max_abs=%.6f clamp_applied=%d enable_torque_publisher=%d confirm_torque_publisher_enable=%d manual_enable_active=%d dormant_publisher_path_skeleton_present=%d dormant_construct_allowed=%d dormant_publish_allowed=%d torque_publisher_enabled=0 uses_safety_utilities=1",
0156:           state_ready,
0157:           inputs_fresh_,
0158:           safe_torque_dry_run_.size(),
0159:           dormant_msg.data.size(),
0160:           last_clamp_result_.max_abs_after_clamp,
0161:           last_clamp_result_.clamp_applied,
0162:           enable_torque_publisher_param_,
0163:           confirm_torque_publisher_enable_param_,
0164:           manual_enable_active_,
0165:           dormantPublisherPathSkeletonPresent(),
0166:           construct_allowed,
0167:           publish_allowed);
0168:       });
0169: 
0170:     RCLCPP_INFO(
0171:       get_logger(),
0172:       "Go1 disabled C++ controller skeleton started with dormant publisher-path skeleton. No ROS torque publisher is constructed.");
0173:   }
0174: 
0175: private:
0176:   static constexpr std::size_t kNumJoints = 12;
0177:   static constexpr std::size_t kNumLegs = 4;
0178:   static constexpr std::size_t kDormantTorquePayloadLength = 12;
0179:   static constexpr bool kDormantPublisherPathSkeletonPresent = true;
```

### parameter line 163

```text
0147:         const auto dormant_msg = makeDormantSafeTorqueCommandMessage();
0148:         const bool construct_allowed = dormantPublisherConstructAllowed();
0149:         const bool publish_allowed = dormantPublishAllowed(state_ready);
0150: 
0151:         RCLCPP_INFO_THROTTLE(
0152:           get_logger(),
0153:           *get_clock(),
0154:           5000,
0155:           "disabled controller skeleton: state_ready=%d inputs_fresh=%d internal_safe_tau_size=%zu dormant_payload_size=%zu internal_safe_tau_max_abs=%.6f clamp_applied=%d enable_torque_publisher=%d confirm_torque_publisher_enable=%d manual_enable_active=%d dormant_publisher_path_skeleton_present=%d dormant_construct_allowed=%d dormant_publish_allowed=%d torque_publisher_enabled=0 uses_safety_utilities=1",
0156:           state_ready,
0157:           inputs_fresh_,
0158:           safe_torque_dry_run_.size(),
0159:           dormant_msg.data.size(),
0160:           last_clamp_result_.max_abs_after_clamp,
0161:           last_clamp_result_.clamp_applied,
0162:           enable_torque_publisher_param_,
0163:           confirm_torque_publisher_enable_param_,
0164:           manual_enable_active_,
0165:           dormantPublisherPathSkeletonPresent(),
0166:           construct_allowed,
0167:           publish_allowed);
0168:       });
0169: 
0170:     RCLCPP_INFO(
0171:       get_logger(),
0172:       "Go1 disabled C++ controller skeleton started with dormant publisher-path skeleton. No ROS torque publisher is constructed.");
0173:   }
0174: 
0175: private:
0176:   static constexpr std::size_t kNumJoints = 12;
0177:   static constexpr std::size_t kNumLegs = 4;
0178:   static constexpr std::size_t kDormantTorquePayloadLength = 12;
0179:   static constexpr bool kDormantPublisherPathSkeletonPresent = true;
```

### publisher_member line 172

```text
0156:           state_ready,
0157:           inputs_fresh_,
0158:           safe_torque_dry_run_.size(),
0159:           dormant_msg.data.size(),
0160:           last_clamp_result_.max_abs_after_clamp,
0161:           last_clamp_result_.clamp_applied,
0162:           enable_torque_publisher_param_,
0163:           confirm_torque_publisher_enable_param_,
0164:           manual_enable_active_,
0165:           dormantPublisherPathSkeletonPresent(),
0166:           construct_allowed,
0167:           publish_allowed);
0168:       });
0169: 
0170:     RCLCPP_INFO(
0171:       get_logger(),
0172:       "Go1 disabled C++ controller skeleton started with dormant publisher-path skeleton. No ROS torque publisher is constructed.");
0173:   }
0174: 
0175: private:
0176:   static constexpr std::size_t kNumJoints = 12;
0177:   static constexpr std::size_t kNumLegs = 4;
0178:   static constexpr std::size_t kDormantTorquePayloadLength = 12;
0179:   static constexpr bool kDormantPublisherPathSkeletonPresent = true;
0180:   static constexpr bool kDormantPublisherConstructionAllowed = false;
0181:   static constexpr bool kDormantPublishCallAllowed = false;
0182:   static constexpr double kInputFreshnessTimeoutSeconds = 0.50;
0183: 
0184:   void updateManualEnableState() {
0185:     enable_torque_publisher_param_ =
0186:       get_parameter("enable_torque_publisher").as_bool();
0187: 
0188:     confirm_torque_publisher_enable_param_ =
```

### private line 175

```text
0159:           dormant_msg.data.size(),
0160:           last_clamp_result_.max_abs_after_clamp,
0161:           last_clamp_result_.clamp_applied,
0162:           enable_torque_publisher_param_,
0163:           confirm_torque_publisher_enable_param_,
0164:           manual_enable_active_,
0165:           dormantPublisherPathSkeletonPresent(),
0166:           construct_allowed,
0167:           publish_allowed);
0168:       });
0169: 
0170:     RCLCPP_INFO(
0171:       get_logger(),
0172:       "Go1 disabled C++ controller skeleton started with dormant publisher-path skeleton. No ROS torque publisher is constructed.");
0173:   }
0174: 
0175: private:
0176:   static constexpr std::size_t kNumJoints = 12;
0177:   static constexpr std::size_t kNumLegs = 4;
0178:   static constexpr std::size_t kDormantTorquePayloadLength = 12;
0179:   static constexpr bool kDormantPublisherPathSkeletonPresent = true;
0180:   static constexpr bool kDormantPublisherConstructionAllowed = false;
0181:   static constexpr bool kDormantPublishCallAllowed = false;
0182:   static constexpr double kInputFreshnessTimeoutSeconds = 0.50;
0183: 
0184:   void updateManualEnableState() {
0185:     enable_torque_publisher_param_ =
0186:       get_parameter("enable_torque_publisher").as_bool();
0187: 
0188:     confirm_torque_publisher_enable_param_ =
0189:       get_parameter("confirm_torque_publisher_enable").as_bool();
0190: 
0191:     manual_enable_active_ =
```

### publisher_member line 185

```text
0169: 
0170:     RCLCPP_INFO(
0171:       get_logger(),
0172:       "Go1 disabled C++ controller skeleton started with dormant publisher-path skeleton. No ROS torque publisher is constructed.");
0173:   }
0174: 
0175: private:
0176:   static constexpr std::size_t kNumJoints = 12;
0177:   static constexpr std::size_t kNumLegs = 4;
0178:   static constexpr std::size_t kDormantTorquePayloadLength = 12;
0179:   static constexpr bool kDormantPublisherPathSkeletonPresent = true;
0180:   static constexpr bool kDormantPublisherConstructionAllowed = false;
0181:   static constexpr bool kDormantPublishCallAllowed = false;
0182:   static constexpr double kInputFreshnessTimeoutSeconds = 0.50;
0183: 
0184:   void updateManualEnableState() {
0185:     enable_torque_publisher_param_ =
0186:       get_parameter("enable_torque_publisher").as_bool();
0187: 
0188:     confirm_torque_publisher_enable_param_ =
0189:       get_parameter("confirm_torque_publisher_enable").as_bool();
0190: 
0191:     manual_enable_active_ =
0192:       enable_torque_publisher_param_ &&
0193:       confirm_torque_publisher_enable_param_;
0194:   }
0195: 
0196:   double messageAgeSeconds(const bool valid, const rclcpp::Time & stamp) const {
0197:     if (!valid) {
0198:       return std::numeric_limits<double>::infinity();
0199:     }
0200:     return (now() - stamp).seconds();
0201:   }
```

### parameter line 185

```text
0169: 
0170:     RCLCPP_INFO(
0171:       get_logger(),
0172:       "Go1 disabled C++ controller skeleton started with dormant publisher-path skeleton. No ROS torque publisher is constructed.");
0173:   }
0174: 
0175: private:
0176:   static constexpr std::size_t kNumJoints = 12;
0177:   static constexpr std::size_t kNumLegs = 4;
0178:   static constexpr std::size_t kDormantTorquePayloadLength = 12;
0179:   static constexpr bool kDormantPublisherPathSkeletonPresent = true;
0180:   static constexpr bool kDormantPublisherConstructionAllowed = false;
0181:   static constexpr bool kDormantPublishCallAllowed = false;
0182:   static constexpr double kInputFreshnessTimeoutSeconds = 0.50;
0183: 
0184:   void updateManualEnableState() {
0185:     enable_torque_publisher_param_ =
0186:       get_parameter("enable_torque_publisher").as_bool();
0187: 
0188:     confirm_torque_publisher_enable_param_ =
0189:       get_parameter("confirm_torque_publisher_enable").as_bool();
0190: 
0191:     manual_enable_active_ =
0192:       enable_torque_publisher_param_ &&
0193:       confirm_torque_publisher_enable_param_;
0194:   }
0195: 
0196:   double messageAgeSeconds(const bool valid, const rclcpp::Time & stamp) const {
0197:     if (!valid) {
0198:       return std::numeric_limits<double>::infinity();
0199:     }
0200:     return (now() - stamp).seconds();
0201:   }
```

### publisher_member line 186

```text
0170:     RCLCPP_INFO(
0171:       get_logger(),
0172:       "Go1 disabled C++ controller skeleton started with dormant publisher-path skeleton. No ROS torque publisher is constructed.");
0173:   }
0174: 
0175: private:
0176:   static constexpr std::size_t kNumJoints = 12;
0177:   static constexpr std::size_t kNumLegs = 4;
0178:   static constexpr std::size_t kDormantTorquePayloadLength = 12;
0179:   static constexpr bool kDormantPublisherPathSkeletonPresent = true;
0180:   static constexpr bool kDormantPublisherConstructionAllowed = false;
0181:   static constexpr bool kDormantPublishCallAllowed = false;
0182:   static constexpr double kInputFreshnessTimeoutSeconds = 0.50;
0183: 
0184:   void updateManualEnableState() {
0185:     enable_torque_publisher_param_ =
0186:       get_parameter("enable_torque_publisher").as_bool();
0187: 
0188:     confirm_torque_publisher_enable_param_ =
0189:       get_parameter("confirm_torque_publisher_enable").as_bool();
0190: 
0191:     manual_enable_active_ =
0192:       enable_torque_publisher_param_ &&
0193:       confirm_torque_publisher_enable_param_;
0194:   }
0195: 
0196:   double messageAgeSeconds(const bool valid, const rclcpp::Time & stamp) const {
0197:     if (!valid) {
0198:       return std::numeric_limits<double>::infinity();
0199:     }
0200:     return (now() - stamp).seconds();
0201:   }
0202: 
```

### parameter line 186

```text
0170:     RCLCPP_INFO(
0171:       get_logger(),
0172:       "Go1 disabled C++ controller skeleton started with dormant publisher-path skeleton. No ROS torque publisher is constructed.");
0173:   }
0174: 
0175: private:
0176:   static constexpr std::size_t kNumJoints = 12;
0177:   static constexpr std::size_t kNumLegs = 4;
0178:   static constexpr std::size_t kDormantTorquePayloadLength = 12;
0179:   static constexpr bool kDormantPublisherPathSkeletonPresent = true;
0180:   static constexpr bool kDormantPublisherConstructionAllowed = false;
0181:   static constexpr bool kDormantPublishCallAllowed = false;
0182:   static constexpr double kInputFreshnessTimeoutSeconds = 0.50;
0183: 
0184:   void updateManualEnableState() {
0185:     enable_torque_publisher_param_ =
0186:       get_parameter("enable_torque_publisher").as_bool();
0187: 
0188:     confirm_torque_publisher_enable_param_ =
0189:       get_parameter("confirm_torque_publisher_enable").as_bool();
0190: 
0191:     manual_enable_active_ =
0192:       enable_torque_publisher_param_ &&
0193:       confirm_torque_publisher_enable_param_;
0194:   }
0195: 
0196:   double messageAgeSeconds(const bool valid, const rclcpp::Time & stamp) const {
0197:     if (!valid) {
0198:       return std::numeric_limits<double>::infinity();
0199:     }
0200:     return (now() - stamp).seconds();
0201:   }
0202: 
```

### publisher_member line 188

```text
0172:       "Go1 disabled C++ controller skeleton started with dormant publisher-path skeleton. No ROS torque publisher is constructed.");
0173:   }
0174: 
0175: private:
0176:   static constexpr std::size_t kNumJoints = 12;
0177:   static constexpr std::size_t kNumLegs = 4;
0178:   static constexpr std::size_t kDormantTorquePayloadLength = 12;
0179:   static constexpr bool kDormantPublisherPathSkeletonPresent = true;
0180:   static constexpr bool kDormantPublisherConstructionAllowed = false;
0181:   static constexpr bool kDormantPublishCallAllowed = false;
0182:   static constexpr double kInputFreshnessTimeoutSeconds = 0.50;
0183: 
0184:   void updateManualEnableState() {
0185:     enable_torque_publisher_param_ =
0186:       get_parameter("enable_torque_publisher").as_bool();
0187: 
0188:     confirm_torque_publisher_enable_param_ =
0189:       get_parameter("confirm_torque_publisher_enable").as_bool();
0190: 
0191:     manual_enable_active_ =
0192:       enable_torque_publisher_param_ &&
0193:       confirm_torque_publisher_enable_param_;
0194:   }
0195: 
0196:   double messageAgeSeconds(const bool valid, const rclcpp::Time & stamp) const {
0197:     if (!valid) {
0198:       return std::numeric_limits<double>::infinity();
0199:     }
0200:     return (now() - stamp).seconds();
0201:   }
0202: 
0203:   void updateInternalSafeDryRunCommand() {
0204:     const std::array<double, 5> ages{
```

### parameter line 188

```text
0172:       "Go1 disabled C++ controller skeleton started with dormant publisher-path skeleton. No ROS torque publisher is constructed.");
0173:   }
0174: 
0175: private:
0176:   static constexpr std::size_t kNumJoints = 12;
0177:   static constexpr std::size_t kNumLegs = 4;
0178:   static constexpr std::size_t kDormantTorquePayloadLength = 12;
0179:   static constexpr bool kDormantPublisherPathSkeletonPresent = true;
0180:   static constexpr bool kDormantPublisherConstructionAllowed = false;
0181:   static constexpr bool kDormantPublishCallAllowed = false;
0182:   static constexpr double kInputFreshnessTimeoutSeconds = 0.50;
0183: 
0184:   void updateManualEnableState() {
0185:     enable_torque_publisher_param_ =
0186:       get_parameter("enable_torque_publisher").as_bool();
0187: 
0188:     confirm_torque_publisher_enable_param_ =
0189:       get_parameter("confirm_torque_publisher_enable").as_bool();
0190: 
0191:     manual_enable_active_ =
0192:       enable_torque_publisher_param_ &&
0193:       confirm_torque_publisher_enable_param_;
0194:   }
0195: 
0196:   double messageAgeSeconds(const bool valid, const rclcpp::Time & stamp) const {
0197:     if (!valid) {
0198:       return std::numeric_limits<double>::infinity();
0199:     }
0200:     return (now() - stamp).seconds();
0201:   }
0202: 
0203:   void updateInternalSafeDryRunCommand() {
0204:     const std::array<double, 5> ages{
```

### publisher_member line 189

```text
0173:   }
0174: 
0175: private:
0176:   static constexpr std::size_t kNumJoints = 12;
0177:   static constexpr std::size_t kNumLegs = 4;
0178:   static constexpr std::size_t kDormantTorquePayloadLength = 12;
0179:   static constexpr bool kDormantPublisherPathSkeletonPresent = true;
0180:   static constexpr bool kDormantPublisherConstructionAllowed = false;
0181:   static constexpr bool kDormantPublishCallAllowed = false;
0182:   static constexpr double kInputFreshnessTimeoutSeconds = 0.50;
0183: 
0184:   void updateManualEnableState() {
0185:     enable_torque_publisher_param_ =
0186:       get_parameter("enable_torque_publisher").as_bool();
0187: 
0188:     confirm_torque_publisher_enable_param_ =
0189:       get_parameter("confirm_torque_publisher_enable").as_bool();
0190: 
0191:     manual_enable_active_ =
0192:       enable_torque_publisher_param_ &&
0193:       confirm_torque_publisher_enable_param_;
0194:   }
0195: 
0196:   double messageAgeSeconds(const bool valid, const rclcpp::Time & stamp) const {
0197:     if (!valid) {
0198:       return std::numeric_limits<double>::infinity();
0199:     }
0200:     return (now() - stamp).seconds();
0201:   }
0202: 
0203:   void updateInternalSafeDryRunCommand() {
0204:     const std::array<double, 5> ages{
0205:       messageAgeSeconds(joint_state_valid_, last_joint_state_time_),
```

### parameter line 189

```text
0173:   }
0174: 
0175: private:
0176:   static constexpr std::size_t kNumJoints = 12;
0177:   static constexpr std::size_t kNumLegs = 4;
0178:   static constexpr std::size_t kDormantTorquePayloadLength = 12;
0179:   static constexpr bool kDormantPublisherPathSkeletonPresent = true;
0180:   static constexpr bool kDormantPublisherConstructionAllowed = false;
0181:   static constexpr bool kDormantPublishCallAllowed = false;
0182:   static constexpr double kInputFreshnessTimeoutSeconds = 0.50;
0183: 
0184:   void updateManualEnableState() {
0185:     enable_torque_publisher_param_ =
0186:       get_parameter("enable_torque_publisher").as_bool();
0187: 
0188:     confirm_torque_publisher_enable_param_ =
0189:       get_parameter("confirm_torque_publisher_enable").as_bool();
0190: 
0191:     manual_enable_active_ =
0192:       enable_torque_publisher_param_ &&
0193:       confirm_torque_publisher_enable_param_;
0194:   }
0195: 
0196:   double messageAgeSeconds(const bool valid, const rclcpp::Time & stamp) const {
0197:     if (!valid) {
0198:       return std::numeric_limits<double>::infinity();
0199:     }
0200:     return (now() - stamp).seconds();
0201:   }
0202: 
0203:   void updateInternalSafeDryRunCommand() {
0204:     const std::array<double, 5> ages{
0205:       messageAgeSeconds(joint_state_valid_, last_joint_state_time_),
```

### publisher_member line 192

```text
0176:   static constexpr std::size_t kNumJoints = 12;
0177:   static constexpr std::size_t kNumLegs = 4;
0178:   static constexpr std::size_t kDormantTorquePayloadLength = 12;
0179:   static constexpr bool kDormantPublisherPathSkeletonPresent = true;
0180:   static constexpr bool kDormantPublisherConstructionAllowed = false;
0181:   static constexpr bool kDormantPublishCallAllowed = false;
0182:   static constexpr double kInputFreshnessTimeoutSeconds = 0.50;
0183: 
0184:   void updateManualEnableState() {
0185:     enable_torque_publisher_param_ =
0186:       get_parameter("enable_torque_publisher").as_bool();
0187: 
0188:     confirm_torque_publisher_enable_param_ =
0189:       get_parameter("confirm_torque_publisher_enable").as_bool();
0190: 
0191:     manual_enable_active_ =
0192:       enable_torque_publisher_param_ &&
0193:       confirm_torque_publisher_enable_param_;
0194:   }
0195: 
0196:   double messageAgeSeconds(const bool valid, const rclcpp::Time & stamp) const {
0197:     if (!valid) {
0198:       return std::numeric_limits<double>::infinity();
0199:     }
0200:     return (now() - stamp).seconds();
0201:   }
0202: 
0203:   void updateInternalSafeDryRunCommand() {
0204:     const std::array<double, 5> ages{
0205:       messageAgeSeconds(joint_state_valid_, last_joint_state_time_),
0206:       messageAgeSeconds(base_state_valid_, last_base_state_time_),
0207:       messageAgeSeconds(imu_valid_, last_imu_time_),
0208:       messageAgeSeconds(foot_contacts_valid_, last_foot_contacts_time_),
```

### parameter line 192

```text
0176:   static constexpr std::size_t kNumJoints = 12;
0177:   static constexpr std::size_t kNumLegs = 4;
0178:   static constexpr std::size_t kDormantTorquePayloadLength = 12;
0179:   static constexpr bool kDormantPublisherPathSkeletonPresent = true;
0180:   static constexpr bool kDormantPublisherConstructionAllowed = false;
0181:   static constexpr bool kDormantPublishCallAllowed = false;
0182:   static constexpr double kInputFreshnessTimeoutSeconds = 0.50;
0183: 
0184:   void updateManualEnableState() {
0185:     enable_torque_publisher_param_ =
0186:       get_parameter("enable_torque_publisher").as_bool();
0187: 
0188:     confirm_torque_publisher_enable_param_ =
0189:       get_parameter("confirm_torque_publisher_enable").as_bool();
0190: 
0191:     manual_enable_active_ =
0192:       enable_torque_publisher_param_ &&
0193:       confirm_torque_publisher_enable_param_;
0194:   }
0195: 
0196:   double messageAgeSeconds(const bool valid, const rclcpp::Time & stamp) const {
0197:     if (!valid) {
0198:       return std::numeric_limits<double>::infinity();
0199:     }
0200:     return (now() - stamp).seconds();
0201:   }
0202: 
0203:   void updateInternalSafeDryRunCommand() {
0204:     const std::array<double, 5> ages{
0205:       messageAgeSeconds(joint_state_valid_, last_joint_state_time_),
0206:       messageAgeSeconds(base_state_valid_, last_base_state_time_),
0207:       messageAgeSeconds(imu_valid_, last_imu_time_),
0208:       messageAgeSeconds(foot_contacts_valid_, last_foot_contacts_time_),
```

### publisher_member line 193

```text
0177:   static constexpr std::size_t kNumLegs = 4;
0178:   static constexpr std::size_t kDormantTorquePayloadLength = 12;
0179:   static constexpr bool kDormantPublisherPathSkeletonPresent = true;
0180:   static constexpr bool kDormantPublisherConstructionAllowed = false;
0181:   static constexpr bool kDormantPublishCallAllowed = false;
0182:   static constexpr double kInputFreshnessTimeoutSeconds = 0.50;
0183: 
0184:   void updateManualEnableState() {
0185:     enable_torque_publisher_param_ =
0186:       get_parameter("enable_torque_publisher").as_bool();
0187: 
0188:     confirm_torque_publisher_enable_param_ =
0189:       get_parameter("confirm_torque_publisher_enable").as_bool();
0190: 
0191:     manual_enable_active_ =
0192:       enable_torque_publisher_param_ &&
0193:       confirm_torque_publisher_enable_param_;
0194:   }
0195: 
0196:   double messageAgeSeconds(const bool valid, const rclcpp::Time & stamp) const {
0197:     if (!valid) {
0198:       return std::numeric_limits<double>::infinity();
0199:     }
0200:     return (now() - stamp).seconds();
0201:   }
0202: 
0203:   void updateInternalSafeDryRunCommand() {
0204:     const std::array<double, 5> ages{
0205:       messageAgeSeconds(joint_state_valid_, last_joint_state_time_),
0206:       messageAgeSeconds(base_state_valid_, last_base_state_time_),
0207:       messageAgeSeconds(imu_valid_, last_imu_time_),
0208:       messageAgeSeconds(foot_contacts_valid_, last_foot_contacts_time_),
0209:       messageAgeSeconds(sim_time_valid_, last_sim_time_msg_time_),
```

### parameter line 193

```text
0177:   static constexpr std::size_t kNumLegs = 4;
0178:   static constexpr std::size_t kDormantTorquePayloadLength = 12;
0179:   static constexpr bool kDormantPublisherPathSkeletonPresent = true;
0180:   static constexpr bool kDormantPublisherConstructionAllowed = false;
0181:   static constexpr bool kDormantPublishCallAllowed = false;
0182:   static constexpr double kInputFreshnessTimeoutSeconds = 0.50;
0183: 
0184:   void updateManualEnableState() {
0185:     enable_torque_publisher_param_ =
0186:       get_parameter("enable_torque_publisher").as_bool();
0187: 
0188:     confirm_torque_publisher_enable_param_ =
0189:       get_parameter("confirm_torque_publisher_enable").as_bool();
0190: 
0191:     manual_enable_active_ =
0192:       enable_torque_publisher_param_ &&
0193:       confirm_torque_publisher_enable_param_;
0194:   }
0195: 
0196:   double messageAgeSeconds(const bool valid, const rclcpp::Time & stamp) const {
0197:     if (!valid) {
0198:       return std::numeric_limits<double>::infinity();
0199:     }
0200:     return (now() - stamp).seconds();
0201:   }
0202: 
0203:   void updateInternalSafeDryRunCommand() {
0204:     const std::array<double, 5> ages{
0205:       messageAgeSeconds(joint_state_valid_, last_joint_state_time_),
0206:       messageAgeSeconds(base_state_valid_, last_base_state_time_),
0207:       messageAgeSeconds(imu_valid_, last_imu_time_),
0208:       messageAgeSeconds(foot_contacts_valid_, last_foot_contacts_time_),
0209:       messageAgeSeconds(sim_time_valid_, last_sim_time_msg_time_),
```

### zero_safe line 217

```text
0201:   }
0202: 
0203:   void updateInternalSafeDryRunCommand() {
0204:     const std::array<double, 5> ages{
0205:       messageAgeSeconds(joint_state_valid_, last_joint_state_time_),
0206:       messageAgeSeconds(base_state_valid_, last_base_state_time_),
0207:       messageAgeSeconds(imu_valid_, last_imu_time_),
0208:       messageAgeSeconds(foot_contacts_valid_, last_foot_contacts_time_),
0209:       messageAgeSeconds(sim_time_valid_, last_sim_time_msg_time_),
0210:     };
0211: 
0212:     inputs_fresh_ =
0213:       robot_mpc_wbc_cpp_controller::allInputsFresh(ages, kInputFreshnessTimeoutSeconds);
0214: 
0215:     const auto raw_command =
0216:       inputs_fresh_
0217:         ? zero_torque_dry_run_
0218:         : robot_mpc_wbc_cpp_controller::watchdogFallbackZeroTorque();
0219: 
0220:     last_clamp_result_ =
0221:       robot_mpc_wbc_cpp_controller::clampTorqueCommand(raw_command, torque_clamp_config_);
0222: 
0223:     safe_torque_dry_run_ = last_clamp_result_.tau;
0224:   }
0225: 
0226:   bool dormantPublisherPathSkeletonPresent() const {
0227:     return kDormantPublisherPathSkeletonPresent;
0228:   }
0229: 
0230:   bool dormantPublisherConstructAllowed() const {
0231:     return kDormantPublisherConstructionAllowed;
0232:   }
0233: 
```

### zero_safe line 223

```text
0207:       messageAgeSeconds(imu_valid_, last_imu_time_),
0208:       messageAgeSeconds(foot_contacts_valid_, last_foot_contacts_time_),
0209:       messageAgeSeconds(sim_time_valid_, last_sim_time_msg_time_),
0210:     };
0211: 
0212:     inputs_fresh_ =
0213:       robot_mpc_wbc_cpp_controller::allInputsFresh(ages, kInputFreshnessTimeoutSeconds);
0214: 
0215:     const auto raw_command =
0216:       inputs_fresh_
0217:         ? zero_torque_dry_run_
0218:         : robot_mpc_wbc_cpp_controller::watchdogFallbackZeroTorque();
0219: 
0220:     last_clamp_result_ =
0221:       robot_mpc_wbc_cpp_controller::clampTorqueCommand(raw_command, torque_clamp_config_);
0222: 
0223:     safe_torque_dry_run_ = last_clamp_result_.tau;
0224:   }
0225: 
0226:   bool dormantPublisherPathSkeletonPresent() const {
0227:     return kDormantPublisherPathSkeletonPresent;
0228:   }
0229: 
0230:   bool dormantPublisherConstructAllowed() const {
0231:     return kDormantPublisherConstructionAllowed;
0232:   }
0233: 
0234:   bool dormantPublishAllowed(const bool state_ready) const {
0235:     (void)state_ready;
0236:     return kDormantPublishCallAllowed;
0237:   }
0238: 
0239:   std_msgs::msg::Float64MultiArray makeDormantSafeTorqueCommandMessage() const {
```

### zero_safe line 239

```text
0223:     safe_torque_dry_run_ = last_clamp_result_.tau;
0224:   }
0225: 
0226:   bool dormantPublisherPathSkeletonPresent() const {
0227:     return kDormantPublisherPathSkeletonPresent;
0228:   }
0229: 
0230:   bool dormantPublisherConstructAllowed() const {
0231:     return kDormantPublisherConstructionAllowed;
0232:   }
0233: 
0234:   bool dormantPublishAllowed(const bool state_ready) const {
0235:     (void)state_ready;
0236:     return kDormantPublishCallAllowed;
0237:   }
0238: 
0239:   std_msgs::msg::Float64MultiArray makeDormantSafeTorqueCommandMessage() const {
0240:     std_msgs::msg::Float64MultiArray msg;
0241:     msg.data.reserve(kDormantTorquePayloadLength);
0242:     msg.data.assign(safe_torque_dry_run_.begin(), safe_torque_dry_run_.end());
0243:     return msg;
0244:   }
0245: 
0246:   rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_state_sub_;
0247:   rclcpp::Subscription<std_msgs::msg::Float64MultiArray>::SharedPtr base_state_sub_;
0248:   rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
0249:   rclcpp::Subscription<std_msgs::msg::Int32MultiArray>::SharedPtr foot_contacts_sub_;
0250:   rclcpp::Subscription<std_msgs::msg::Float64>::SharedPtr sim_time_sub_;
0251: 
0252:   rclcpp::TimerBase::SharedPtr status_timer_;
0253: 
0254:   bool joint_state_valid_ = false;
0255:   bool base_state_valid_ = false;
```

### zero_safe line 240

```text
0224:   }
0225: 
0226:   bool dormantPublisherPathSkeletonPresent() const {
0227:     return kDormantPublisherPathSkeletonPresent;
0228:   }
0229: 
0230:   bool dormantPublisherConstructAllowed() const {
0231:     return kDormantPublisherConstructionAllowed;
0232:   }
0233: 
0234:   bool dormantPublishAllowed(const bool state_ready) const {
0235:     (void)state_ready;
0236:     return kDormantPublishCallAllowed;
0237:   }
0238: 
0239:   std_msgs::msg::Float64MultiArray makeDormantSafeTorqueCommandMessage() const {
0240:     std_msgs::msg::Float64MultiArray msg;
0241:     msg.data.reserve(kDormantTorquePayloadLength);
0242:     msg.data.assign(safe_torque_dry_run_.begin(), safe_torque_dry_run_.end());
0243:     return msg;
0244:   }
0245: 
0246:   rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_state_sub_;
0247:   rclcpp::Subscription<std_msgs::msg::Float64MultiArray>::SharedPtr base_state_sub_;
0248:   rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
0249:   rclcpp::Subscription<std_msgs::msg::Int32MultiArray>::SharedPtr foot_contacts_sub_;
0250:   rclcpp::Subscription<std_msgs::msg::Float64>::SharedPtr sim_time_sub_;
0251: 
0252:   rclcpp::TimerBase::SharedPtr status_timer_;
0253: 
0254:   bool joint_state_valid_ = false;
0255:   bool base_state_valid_ = false;
0256:   bool imu_valid_ = false;
```

### zero_safe line 242

```text
0226:   bool dormantPublisherPathSkeletonPresent() const {
0227:     return kDormantPublisherPathSkeletonPresent;
0228:   }
0229: 
0230:   bool dormantPublisherConstructAllowed() const {
0231:     return kDormantPublisherConstructionAllowed;
0232:   }
0233: 
0234:   bool dormantPublishAllowed(const bool state_ready) const {
0235:     (void)state_ready;
0236:     return kDormantPublishCallAllowed;
0237:   }
0238: 
0239:   std_msgs::msg::Float64MultiArray makeDormantSafeTorqueCommandMessage() const {
0240:     std_msgs::msg::Float64MultiArray msg;
0241:     msg.data.reserve(kDormantTorquePayloadLength);
0242:     msg.data.assign(safe_torque_dry_run_.begin(), safe_torque_dry_run_.end());
0243:     return msg;
0244:   }
0245: 
0246:   rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_state_sub_;
0247:   rclcpp::Subscription<std_msgs::msg::Float64MultiArray>::SharedPtr base_state_sub_;
0248:   rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
0249:   rclcpp::Subscription<std_msgs::msg::Int32MultiArray>::SharedPtr foot_contacts_sub_;
0250:   rclcpp::Subscription<std_msgs::msg::Float64>::SharedPtr sim_time_sub_;
0251: 
0252:   rclcpp::TimerBase::SharedPtr status_timer_;
0253: 
0254:   bool joint_state_valid_ = false;
0255:   bool base_state_valid_ = false;
0256:   bool imu_valid_ = false;
0257:   bool foot_contacts_valid_ = false;
0258:   bool sim_time_valid_ = false;
```

### zero_safe line 247

```text
0231:     return kDormantPublisherConstructionAllowed;
0232:   }
0233: 
0234:   bool dormantPublishAllowed(const bool state_ready) const {
0235:     (void)state_ready;
0236:     return kDormantPublishCallAllowed;
0237:   }
0238: 
0239:   std_msgs::msg::Float64MultiArray makeDormantSafeTorqueCommandMessage() const {
0240:     std_msgs::msg::Float64MultiArray msg;
0241:     msg.data.reserve(kDormantTorquePayloadLength);
0242:     msg.data.assign(safe_torque_dry_run_.begin(), safe_torque_dry_run_.end());
0243:     return msg;
0244:   }
0245: 
0246:   rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_state_sub_;
0247:   rclcpp::Subscription<std_msgs::msg::Float64MultiArray>::SharedPtr base_state_sub_;
0248:   rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
0249:   rclcpp::Subscription<std_msgs::msg::Int32MultiArray>::SharedPtr foot_contacts_sub_;
0250:   rclcpp::Subscription<std_msgs::msg::Float64>::SharedPtr sim_time_sub_;
0251: 
0252:   rclcpp::TimerBase::SharedPtr status_timer_;
0253: 
0254:   bool joint_state_valid_ = false;
0255:   bool base_state_valid_ = false;
0256:   bool imu_valid_ = false;
0257:   bool foot_contacts_valid_ = false;
0258:   bool sim_time_valid_ = false;
0259:   bool inputs_fresh_ = false;
0260: 
0261:   bool enable_torque_publisher_param_ = false;
0262:   bool confirm_torque_publisher_enable_param_ = false;
0263:   bool manual_enable_active_ = false;
```

### timer line 252

```text
0236:     return kDormantPublishCallAllowed;
0237:   }
0238: 
0239:   std_msgs::msg::Float64MultiArray makeDormantSafeTorqueCommandMessage() const {
0240:     std_msgs::msg::Float64MultiArray msg;
0241:     msg.data.reserve(kDormantTorquePayloadLength);
0242:     msg.data.assign(safe_torque_dry_run_.begin(), safe_torque_dry_run_.end());
0243:     return msg;
0244:   }
0245: 
0246:   rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_state_sub_;
0247:   rclcpp::Subscription<std_msgs::msg::Float64MultiArray>::SharedPtr base_state_sub_;
0248:   rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
0249:   rclcpp::Subscription<std_msgs::msg::Int32MultiArray>::SharedPtr foot_contacts_sub_;
0250:   rclcpp::Subscription<std_msgs::msg::Float64>::SharedPtr sim_time_sub_;
0251: 
0252:   rclcpp::TimerBase::SharedPtr status_timer_;
0253: 
0254:   bool joint_state_valid_ = false;
0255:   bool base_state_valid_ = false;
0256:   bool imu_valid_ = false;
0257:   bool foot_contacts_valid_ = false;
0258:   bool sim_time_valid_ = false;
0259:   bool inputs_fresh_ = false;
0260: 
0261:   bool enable_torque_publisher_param_ = false;
0262:   bool confirm_torque_publisher_enable_param_ = false;
0263:   bool manual_enable_active_ = false;
0264: 
0265:   rclcpp::Time last_joint_state_time_{0, 0, RCL_ROS_TIME};
0266:   rclcpp::Time last_base_state_time_{0, 0, RCL_ROS_TIME};
0267:   rclcpp::Time last_imu_time_{0, 0, RCL_ROS_TIME};
0268:   rclcpp::Time last_foot_contacts_time_{0, 0, RCL_ROS_TIME};
```

### publisher_member line 261

```text
0245: 
0246:   rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_state_sub_;
0247:   rclcpp::Subscription<std_msgs::msg::Float64MultiArray>::SharedPtr base_state_sub_;
0248:   rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
0249:   rclcpp::Subscription<std_msgs::msg::Int32MultiArray>::SharedPtr foot_contacts_sub_;
0250:   rclcpp::Subscription<std_msgs::msg::Float64>::SharedPtr sim_time_sub_;
0251: 
0252:   rclcpp::TimerBase::SharedPtr status_timer_;
0253: 
0254:   bool joint_state_valid_ = false;
0255:   bool base_state_valid_ = false;
0256:   bool imu_valid_ = false;
0257:   bool foot_contacts_valid_ = false;
0258:   bool sim_time_valid_ = false;
0259:   bool inputs_fresh_ = false;
0260: 
0261:   bool enable_torque_publisher_param_ = false;
0262:   bool confirm_torque_publisher_enable_param_ = false;
0263:   bool manual_enable_active_ = false;
0264: 
0265:   rclcpp::Time last_joint_state_time_{0, 0, RCL_ROS_TIME};
0266:   rclcpp::Time last_base_state_time_{0, 0, RCL_ROS_TIME};
0267:   rclcpp::Time last_imu_time_{0, 0, RCL_ROS_TIME};
0268:   rclcpp::Time last_foot_contacts_time_{0, 0, RCL_ROS_TIME};
0269:   rclcpp::Time last_sim_time_msg_time_{0, 0, RCL_ROS_TIME};
0270: 
0271:   double sim_time_ = 0.0;
0272: 
0273:   std::vector<std::string> joint_names_;
0274:   std::vector<double> joint_position_;
0275:   std::vector<double> joint_velocity_;
0276:   std::vector<double> joint_effort_;
0277:   std::vector<double> base_state_;
```

### parameter line 261

```text
0245: 
0246:   rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_state_sub_;
0247:   rclcpp::Subscription<std_msgs::msg::Float64MultiArray>::SharedPtr base_state_sub_;
0248:   rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
0249:   rclcpp::Subscription<std_msgs::msg::Int32MultiArray>::SharedPtr foot_contacts_sub_;
0250:   rclcpp::Subscription<std_msgs::msg::Float64>::SharedPtr sim_time_sub_;
0251: 
0252:   rclcpp::TimerBase::SharedPtr status_timer_;
0253: 
0254:   bool joint_state_valid_ = false;
0255:   bool base_state_valid_ = false;
0256:   bool imu_valid_ = false;
0257:   bool foot_contacts_valid_ = false;
0258:   bool sim_time_valid_ = false;
0259:   bool inputs_fresh_ = false;
0260: 
0261:   bool enable_torque_publisher_param_ = false;
0262:   bool confirm_torque_publisher_enable_param_ = false;
0263:   bool manual_enable_active_ = false;
0264: 
0265:   rclcpp::Time last_joint_state_time_{0, 0, RCL_ROS_TIME};
0266:   rclcpp::Time last_base_state_time_{0, 0, RCL_ROS_TIME};
0267:   rclcpp::Time last_imu_time_{0, 0, RCL_ROS_TIME};
0268:   rclcpp::Time last_foot_contacts_time_{0, 0, RCL_ROS_TIME};
0269:   rclcpp::Time last_sim_time_msg_time_{0, 0, RCL_ROS_TIME};
0270: 
0271:   double sim_time_ = 0.0;
0272: 
0273:   std::vector<std::string> joint_names_;
0274:   std::vector<double> joint_position_;
0275:   std::vector<double> joint_velocity_;
0276:   std::vector<double> joint_effort_;
0277:   std::vector<double> base_state_;
```

### publisher_member line 262

```text
0246:   rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_state_sub_;
0247:   rclcpp::Subscription<std_msgs::msg::Float64MultiArray>::SharedPtr base_state_sub_;
0248:   rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
0249:   rclcpp::Subscription<std_msgs::msg::Int32MultiArray>::SharedPtr foot_contacts_sub_;
0250:   rclcpp::Subscription<std_msgs::msg::Float64>::SharedPtr sim_time_sub_;
0251: 
0252:   rclcpp::TimerBase::SharedPtr status_timer_;
0253: 
0254:   bool joint_state_valid_ = false;
0255:   bool base_state_valid_ = false;
0256:   bool imu_valid_ = false;
0257:   bool foot_contacts_valid_ = false;
0258:   bool sim_time_valid_ = false;
0259:   bool inputs_fresh_ = false;
0260: 
0261:   bool enable_torque_publisher_param_ = false;
0262:   bool confirm_torque_publisher_enable_param_ = false;
0263:   bool manual_enable_active_ = false;
0264: 
0265:   rclcpp::Time last_joint_state_time_{0, 0, RCL_ROS_TIME};
0266:   rclcpp::Time last_base_state_time_{0, 0, RCL_ROS_TIME};
0267:   rclcpp::Time last_imu_time_{0, 0, RCL_ROS_TIME};
0268:   rclcpp::Time last_foot_contacts_time_{0, 0, RCL_ROS_TIME};
0269:   rclcpp::Time last_sim_time_msg_time_{0, 0, RCL_ROS_TIME};
0270: 
0271:   double sim_time_ = 0.0;
0272: 
0273:   std::vector<std::string> joint_names_;
0274:   std::vector<double> joint_position_;
0275:   std::vector<double> joint_velocity_;
0276:   std::vector<double> joint_effort_;
0277:   std::vector<double> base_state_;
0278:   std::array<int32_t, kNumLegs> foot_contacts_{};
```

### parameter line 262

```text
0246:   rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_state_sub_;
0247:   rclcpp::Subscription<std_msgs::msg::Float64MultiArray>::SharedPtr base_state_sub_;
0248:   rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
0249:   rclcpp::Subscription<std_msgs::msg::Int32MultiArray>::SharedPtr foot_contacts_sub_;
0250:   rclcpp::Subscription<std_msgs::msg::Float64>::SharedPtr sim_time_sub_;
0251: 
0252:   rclcpp::TimerBase::SharedPtr status_timer_;
0253: 
0254:   bool joint_state_valid_ = false;
0255:   bool base_state_valid_ = false;
0256:   bool imu_valid_ = false;
0257:   bool foot_contacts_valid_ = false;
0258:   bool sim_time_valid_ = false;
0259:   bool inputs_fresh_ = false;
0260: 
0261:   bool enable_torque_publisher_param_ = false;
0262:   bool confirm_torque_publisher_enable_param_ = false;
0263:   bool manual_enable_active_ = false;
0264: 
0265:   rclcpp::Time last_joint_state_time_{0, 0, RCL_ROS_TIME};
0266:   rclcpp::Time last_base_state_time_{0, 0, RCL_ROS_TIME};
0267:   rclcpp::Time last_imu_time_{0, 0, RCL_ROS_TIME};
0268:   rclcpp::Time last_foot_contacts_time_{0, 0, RCL_ROS_TIME};
0269:   rclcpp::Time last_sim_time_msg_time_{0, 0, RCL_ROS_TIME};
0270: 
0271:   double sim_time_ = 0.0;
0272: 
0273:   std::vector<std::string> joint_names_;
0274:   std::vector<double> joint_position_;
0275:   std::vector<double> joint_velocity_;
0276:   std::vector<double> joint_effort_;
0277:   std::vector<double> base_state_;
0278:   std::array<int32_t, kNumLegs> foot_contacts_{};
```

### zero_safe line 280

```text
0264: 
0265:   rclcpp::Time last_joint_state_time_{0, 0, RCL_ROS_TIME};
0266:   rclcpp::Time last_base_state_time_{0, 0, RCL_ROS_TIME};
0267:   rclcpp::Time last_imu_time_{0, 0, RCL_ROS_TIME};
0268:   rclcpp::Time last_foot_contacts_time_{0, 0, RCL_ROS_TIME};
0269:   rclcpp::Time last_sim_time_msg_time_{0, 0, RCL_ROS_TIME};
0270: 
0271:   double sim_time_ = 0.0;
0272: 
0273:   std::vector<std::string> joint_names_;
0274:   std::vector<double> joint_position_;
0275:   std::vector<double> joint_velocity_;
0276:   std::vector<double> joint_effort_;
0277:   std::vector<double> base_state_;
0278:   std::array<int32_t, kNumLegs> foot_contacts_{};
0279: 
0280:   robot_mpc_wbc_cpp_controller::TorqueVector zero_torque_dry_run_{};
0281:   robot_mpc_wbc_cpp_controller::TorqueVector safe_torque_dry_run_{};
0282:   robot_mpc_wbc_cpp_controller::TorqueClampConfig torque_clamp_config_{};
0283:   robot_mpc_wbc_cpp_controller::TorqueClampResult last_clamp_result_{};
0284: 
0285:   rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr active_torque_cmd_publisher_;
0286:   static constexpr bool kStage124PublisherConstructionImplemented = true;
0287:   static constexpr bool kStage124PublishCallImplemented = false;
0288: 
0289: 
0290:   std_msgs::msg::Float64MultiArray makeStage1214ZeroSafeTorqueCommandMessage() const
0291:   {
0292:     std_msgs::msg::Float64MultiArray msg;
0293:     msg.data.assign(12, 0.0);
0294:     return msg;
0295:   }
0296: 
```

### zero_safe line 281

```text
0265:   rclcpp::Time last_joint_state_time_{0, 0, RCL_ROS_TIME};
0266:   rclcpp::Time last_base_state_time_{0, 0, RCL_ROS_TIME};
0267:   rclcpp::Time last_imu_time_{0, 0, RCL_ROS_TIME};
0268:   rclcpp::Time last_foot_contacts_time_{0, 0, RCL_ROS_TIME};
0269:   rclcpp::Time last_sim_time_msg_time_{0, 0, RCL_ROS_TIME};
0270: 
0271:   double sim_time_ = 0.0;
0272: 
0273:   std::vector<std::string> joint_names_;
0274:   std::vector<double> joint_position_;
0275:   std::vector<double> joint_velocity_;
0276:   std::vector<double> joint_effort_;
0277:   std::vector<double> base_state_;
0278:   std::array<int32_t, kNumLegs> foot_contacts_{};
0279: 
0280:   robot_mpc_wbc_cpp_controller::TorqueVector zero_torque_dry_run_{};
0281:   robot_mpc_wbc_cpp_controller::TorqueVector safe_torque_dry_run_{};
0282:   robot_mpc_wbc_cpp_controller::TorqueClampConfig torque_clamp_config_{};
0283:   robot_mpc_wbc_cpp_controller::TorqueClampResult last_clamp_result_{};
0284: 
0285:   rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr active_torque_cmd_publisher_;
0286:   static constexpr bool kStage124PublisherConstructionImplemented = true;
0287:   static constexpr bool kStage124PublishCallImplemented = false;
0288: 
0289: 
0290:   std_msgs::msg::Float64MultiArray makeStage1214ZeroSafeTorqueCommandMessage() const
0291:   {
0292:     std_msgs::msg::Float64MultiArray msg;
0293:     msg.data.assign(12, 0.0);
0294:     return msg;
0295:   }
0296: 
0297:   bool publishBoundedZeroSafeTorqueOnceIfAllowed(
```

### publisher_member line 285

```text
0269:   rclcpp::Time last_sim_time_msg_time_{0, 0, RCL_ROS_TIME};
0270: 
0271:   double sim_time_ = 0.0;
0272: 
0273:   std::vector<std::string> joint_names_;
0274:   std::vector<double> joint_position_;
0275:   std::vector<double> joint_velocity_;
0276:   std::vector<double> joint_effort_;
0277:   std::vector<double> base_state_;
0278:   std::array<int32_t, kNumLegs> foot_contacts_{};
0279: 
0280:   robot_mpc_wbc_cpp_controller::TorqueVector zero_torque_dry_run_{};
0281:   robot_mpc_wbc_cpp_controller::TorqueVector safe_torque_dry_run_{};
0282:   robot_mpc_wbc_cpp_controller::TorqueClampConfig torque_clamp_config_{};
0283:   robot_mpc_wbc_cpp_controller::TorqueClampResult last_clamp_result_{};
0284: 
0285:   rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr active_torque_cmd_publisher_;
0286:   static constexpr bool kStage124PublisherConstructionImplemented = true;
0287:   static constexpr bool kStage124PublishCallImplemented = false;
0288: 
0289: 
0290:   std_msgs::msg::Float64MultiArray makeStage1214ZeroSafeTorqueCommandMessage() const
0291:   {
0292:     std_msgs::msg::Float64MultiArray msg;
0293:     msg.data.assign(12, 0.0);
0294:     return msg;
0295:   }
0296: 
0297:   bool publishBoundedZeroSafeTorqueOnceIfAllowed(
0298:     const bool manual_enable,
0299:     const bool manual_confirm,
0300:     const bool state_ready)
0301:   {
```

### zero_safe line 285

```text
0269:   rclcpp::Time last_sim_time_msg_time_{0, 0, RCL_ROS_TIME};
0270: 
0271:   double sim_time_ = 0.0;
0272: 
0273:   std::vector<std::string> joint_names_;
0274:   std::vector<double> joint_position_;
0275:   std::vector<double> joint_velocity_;
0276:   std::vector<double> joint_effort_;
0277:   std::vector<double> base_state_;
0278:   std::array<int32_t, kNumLegs> foot_contacts_{};
0279: 
0280:   robot_mpc_wbc_cpp_controller::TorqueVector zero_torque_dry_run_{};
0281:   robot_mpc_wbc_cpp_controller::TorqueVector safe_torque_dry_run_{};
0282:   robot_mpc_wbc_cpp_controller::TorqueClampConfig torque_clamp_config_{};
0283:   robot_mpc_wbc_cpp_controller::TorqueClampResult last_clamp_result_{};
0284: 
0285:   rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr active_torque_cmd_publisher_;
0286:   static constexpr bool kStage124PublisherConstructionImplemented = true;
0287:   static constexpr bool kStage124PublishCallImplemented = false;
0288: 
0289: 
0290:   std_msgs::msg::Float64MultiArray makeStage1214ZeroSafeTorqueCommandMessage() const
0291:   {
0292:     std_msgs::msg::Float64MultiArray msg;
0293:     msg.data.assign(12, 0.0);
0294:     return msg;
0295:   }
0296: 
0297:   bool publishBoundedZeroSafeTorqueOnceIfAllowed(
0298:     const bool manual_enable,
0299:     const bool manual_confirm,
0300:     const bool state_ready)
0301:   {
```

### zero_safe line 290

```text
0274:   std::vector<double> joint_position_;
0275:   std::vector<double> joint_velocity_;
0276:   std::vector<double> joint_effort_;
0277:   std::vector<double> base_state_;
0278:   std::array<int32_t, kNumLegs> foot_contacts_{};
0279: 
0280:   robot_mpc_wbc_cpp_controller::TorqueVector zero_torque_dry_run_{};
0281:   robot_mpc_wbc_cpp_controller::TorqueVector safe_torque_dry_run_{};
0282:   robot_mpc_wbc_cpp_controller::TorqueClampConfig torque_clamp_config_{};
0283:   robot_mpc_wbc_cpp_controller::TorqueClampResult last_clamp_result_{};
0284: 
0285:   rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr active_torque_cmd_publisher_;
0286:   static constexpr bool kStage124PublisherConstructionImplemented = true;
0287:   static constexpr bool kStage124PublishCallImplemented = false;
0288: 
0289: 
0290:   std_msgs::msg::Float64MultiArray makeStage1214ZeroSafeTorqueCommandMessage() const
0291:   {
0292:     std_msgs::msg::Float64MultiArray msg;
0293:     msg.data.assign(12, 0.0);
0294:     return msg;
0295:   }
0296: 
0297:   bool publishBoundedZeroSafeTorqueOnceIfAllowed(
0298:     const bool manual_enable,
0299:     const bool manual_confirm,
0300:     const bool state_ready)
0301:   {
0302:     if (!manual_enable || !manual_confirm || !state_ready) {
0303:       return false;
0304:     }
0305:     if (active_torque_cmd_publisher_ == nullptr) {
0306:       return false;
```

### zero_safe line 292

```text
0276:   std::vector<double> joint_effort_;
0277:   std::vector<double> base_state_;
0278:   std::array<int32_t, kNumLegs> foot_contacts_{};
0279: 
0280:   robot_mpc_wbc_cpp_controller::TorqueVector zero_torque_dry_run_{};
0281:   robot_mpc_wbc_cpp_controller::TorqueVector safe_torque_dry_run_{};
0282:   robot_mpc_wbc_cpp_controller::TorqueClampConfig torque_clamp_config_{};
0283:   robot_mpc_wbc_cpp_controller::TorqueClampResult last_clamp_result_{};
0284: 
0285:   rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr active_torque_cmd_publisher_;
0286:   static constexpr bool kStage124PublisherConstructionImplemented = true;
0287:   static constexpr bool kStage124PublishCallImplemented = false;
0288: 
0289: 
0290:   std_msgs::msg::Float64MultiArray makeStage1214ZeroSafeTorqueCommandMessage() const
0291:   {
0292:     std_msgs::msg::Float64MultiArray msg;
0293:     msg.data.assign(12, 0.0);
0294:     return msg;
0295:   }
0296: 
0297:   bool publishBoundedZeroSafeTorqueOnceIfAllowed(
0298:     const bool manual_enable,
0299:     const bool manual_confirm,
0300:     const bool state_ready)
0301:   {
0302:     if (!manual_enable || !manual_confirm || !state_ready) {
0303:       return false;
0304:     }
0305:     if (active_torque_cmd_publisher_ == nullptr) {
0306:       return false;
0307:     }
0308: 
```

### publisher_member line 305

```text
0289: 
0290:   std_msgs::msg::Float64MultiArray makeStage1214ZeroSafeTorqueCommandMessage() const
0291:   {
0292:     std_msgs::msg::Float64MultiArray msg;
0293:     msg.data.assign(12, 0.0);
0294:     return msg;
0295:   }
0296: 
0297:   bool publishBoundedZeroSafeTorqueOnceIfAllowed(
0298:     const bool manual_enable,
0299:     const bool manual_confirm,
0300:     const bool state_ready)
0301:   {
0302:     if (!manual_enable || !manual_confirm || !state_ready) {
0303:       return false;
0304:     }
0305:     if (active_torque_cmd_publisher_ == nullptr) {
0306:       return false;
0307:     }
0308: 
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
```

### publisher_member line 319

```text
0303:       return false;
0304:     }
0305:     if (active_torque_cmd_publisher_ == nullptr) {
0306:       return false;
0307:     }
0308: 
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
0330:   rclcpp::init(argc, argv);
0331:   rclcpp::spin(std::make_shared<Go1DisabledControllerNode>());
0332:   rclcpp::shutdown();
0333:   return 0;
0334: }
```

### publish_call line 319

```text
0303:       return false;
0304:     }
0305:     if (active_torque_cmd_publisher_ == nullptr) {
0306:       return false;
0307:     }
0308: 
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
0330:   rclcpp::init(argc, argv);
0331:   rclcpp::spin(std::make_shared<Go1DisabledControllerNode>());
0332:   rclcpp::shutdown();
0333:   return 0;
0334: }
```

### timer line 323

```text
0307:     }
0308: 
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
0330:   rclcpp::init(argc, argv);
0331:   rclcpp::spin(std::make_shared<Go1DisabledControllerNode>());
0332:   rclcpp::shutdown();
0333:   return 0;
0334: }
```

### zero_safe line 324

```text
0308: 
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
0330:   rclcpp::init(argc, argv);
0331:   rclcpp::spin(std::make_shared<Go1DisabledControllerNode>());
0332:   rclcpp::shutdown();
0333:   return 0;
0334: }
```