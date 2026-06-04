#pragma once

#include <array>
#include <cmath>
#include <cstddef>

namespace robot_mpc_wbc_cpp_controller {

constexpr std::size_t kGo1NumActuatedJoints = 12;
using TorqueVector = std::array<double, kGo1NumActuatedJoints>;

inline TorqueVector makeZeroTorqueDryRun() {
  TorqueVector tau{};
  tau.fill(0.0);
  return tau;
}

inline bool allFinite(const TorqueVector & tau) {
  for (const auto value : tau) {
    if (!std::isfinite(value)) {
      return false;
    }
  }
  return true;
}

inline bool allZero(const TorqueVector & tau) {
  for (const auto value : tau) {
    if (std::abs(value) > 0.0) {
      return false;
    }
  }
  return true;
}

inline double maxAbs(const TorqueVector & tau) {
  double max_value = 0.0;
  for (const auto value : tau) {
    const double abs_value = std::abs(value);
    if (abs_value > max_value) {
      max_value = abs_value;
    }
  }
  return max_value;
}

inline double l1Norm(const TorqueVector & tau) {
  double total = 0.0;
  for (const auto value : tau) {
    total += std::abs(value);
  }
  return total;
}

}  // namespace robot_mpc_wbc_cpp_controller
