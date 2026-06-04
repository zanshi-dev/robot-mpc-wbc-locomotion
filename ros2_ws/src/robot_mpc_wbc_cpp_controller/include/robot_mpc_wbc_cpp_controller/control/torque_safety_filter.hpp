#pragma once

#include <array>
#include <cstddef>

namespace robot_mpc_wbc_cpp_controller::control {

class TorqueSafetyFilter {
public:
  explicit TorqueSafetyFilter(double torque_limit = 23.7);

  std::array<double, 12> clamp(const std::array<double, 12>& tau) const;

  bool isFiniteAndWithinLimit(const std::array<double, 12>& tau) const;

  double torque_limit() const;

private:
  double torque_limit_;
};

}  // namespace robot_mpc_wbc_cpp_controller::control
