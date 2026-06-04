#include "robot_mpc_wbc_cpp_controller/control/swing_trajectory.hpp"

#include <cmath>
#include <stdexcept>

namespace robot_mpc_wbc_cpp_controller::control {

SwingTrajectory::SwingTrajectory(double clearance)
: clearance_(clearance)
{
  if (clearance_ < 0.0) {
    throw std::invalid_argument("clearance must be non-negative");
  }
}

Vec3 SwingTrajectory::sample(const Vec3& start, const Vec3& target, double phase) const
{
  const double s = std::clamp(phase, 0.0, 1.0);
  const double smooth = s * s * (3.0 - 2.0 * s);

  Vec3 out;
  out.x = start.x + (target.x - start.x) * smooth;
  out.y = start.y + (target.y - start.y) * smooth;
  out.z = start.z + (target.z - start.z) * smooth + clearance_ * std::sin(M_PI * s);
  return out;
}

double SwingTrajectory::clearance() const
{
  return clearance_;
}

}  // namespace robot_mpc_wbc_cpp_controller::control
