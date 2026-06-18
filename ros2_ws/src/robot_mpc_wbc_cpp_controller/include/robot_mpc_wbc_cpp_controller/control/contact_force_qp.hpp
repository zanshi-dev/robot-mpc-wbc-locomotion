#pragma once

#include "robot_mpc_wbc_cpp_controller/control/swing_trajectory.hpp"

#include <array>
#include <string>

namespace robot_mpc_wbc_cpp_controller::control {

struct ContactForceQpConfig {
  double mass_kg{12.7434};
  double gravity{9.81};
  double friction_coefficient{0.5};
  double min_normal_force{1.0};
  double max_normal_force{120.0};
};

struct ContactForceQpInput {
  Vec3 desired_linear_acceleration{0.0, 0.0, 0.0};
  std::array<bool, 4> contact{true, true, true, true};
};

struct ContactForceQpResult {
  bool success{false};
  std::string status{"not_solved"};

  std::array<Vec3, 4> foot_forces{};
  Vec3 desired_net_force{0.0, 0.0, 0.0};
  Vec3 net_force{0.0, 0.0, 0.0};

  double net_force_error_norm{0.0};
  double max_friction_violation{0.0};
  double max_normal_force_violation{0.0};
  double max_swing_force_norm{0.0};
};

class ContactForceQp {
public:
  explicit ContactForceQp(ContactForceQpConfig config = ContactForceQpConfig{});

  [[nodiscard]] ContactForceQpResult solve(const ContactForceQpInput& input) const;

  [[nodiscard]] bool checkConstraints(
    const ContactForceQpInput& input,
    const ContactForceQpResult& result,
    double tolerance = 1e-9) const;

  [[nodiscard]] const ContactForceQpConfig& config() const { return config_; }

private:
  ContactForceQpConfig config_;
};

}  // namespace robot_mpc_wbc_cpp_controller::control
