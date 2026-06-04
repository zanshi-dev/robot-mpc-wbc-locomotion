#pragma once

#include <array>
#include <algorithm>

namespace robot_mpc_wbc_cpp_controller::control {

struct Vec3 {
  double x{0.0};
  double y{0.0};
  double z{0.0};
};

class SwingTrajectory {
public:
  SwingTrajectory(double clearance = 0.06);

  Vec3 sample(const Vec3& start, const Vec3& target, double phase) const;

  double clearance() const;

private:
  double clearance_;
};

}  // namespace robot_mpc_wbc_cpp_controller::control
