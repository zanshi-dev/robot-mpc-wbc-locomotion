#include "robot_mpc_wbc_cpp_controller/control/torque_safety_filter.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace robot_mpc_wbc_cpp_controller::control {

TorqueSafetyFilter::TorqueSafetyFilter(double torque_limit)
: torque_limit_(torque_limit)
{
  if (!(torque_limit_ > 0.0)) {
    throw std::invalid_argument("torque_limit must be positive");
  }
}

std::array<double, 12> TorqueSafetyFilter::clamp(const std::array<double, 12>& tau) const
{
  std::array<double, 12> out{};
  for (std::size_t i = 0; i < tau.size(); ++i) {
    if (!std::isfinite(tau[i])) {
      out[i] = 0.0;
    } else {
      out[i] = std::clamp(tau[i], -torque_limit_, torque_limit_);
    }
  }
  return out;
}

bool TorqueSafetyFilter::isFiniteAndWithinLimit(const std::array<double, 12>& tau) const
{
  for (const double value : tau) {
    if (!std::isfinite(value)) {
      return false;
    }
    if (std::abs(value) > torque_limit_) {
      return false;
    }
  }
  return true;
}

double TorqueSafetyFilter::torque_limit() const
{
  return torque_limit_;
}

}  // namespace robot_mpc_wbc_cpp_controller::control
