#include "robot_mpc_wbc_cpp_controller/control/gait_scheduler.hpp"
#include "robot_mpc_wbc_cpp_controller/control/swing_trajectory.hpp"
#include "robot_mpc_wbc_cpp_controller/control/torque_safety_filter.hpp"

#include <array>
#include <cassert>
#include <cmath>
#include <iostream>
#include <limits>

using robot_mpc_wbc_cpp_controller::control::GaitScheduler;
using robot_mpc_wbc_cpp_controller::control::SwingTrajectory;
using robot_mpc_wbc_cpp_controller::control::TorqueSafetyFilter;
using robot_mpc_wbc_cpp_controller::control::Vec3;

int main()
{
  {
    GaitScheduler scheduler(200);

    const auto s0 = scheduler.evaluate(0);
    assert(s0.contact[0] == true);
    assert(s0.contact[1] == false);
    assert(s0.contact[2] == false);
    assert(s0.contact[3] == true);
    assert(GaitScheduler::mode_name(s0.mode) == "trot_FR_RL");

    const auto s200 = scheduler.evaluate(200);
    assert(s200.contact[0] == false);
    assert(s200.contact[1] == true);
    assert(s200.contact[2] == true);
    assert(s200.contact[3] == false);
    assert(GaitScheduler::mode_name(s200.mode) == "trot_FL_RR");

    const auto s400 = scheduler.evaluate(400);
    assert(s400.contact[0] == true);
    assert(s400.contact[3] == true);
    assert(GaitScheduler::mode_name(s400.mode) == "trot_FR_RL");
  }

  {
    SwingTrajectory swing(0.06);
    Vec3 start{0.0, 0.0, 0.0};
    Vec3 target{0.2, 0.0, 0.0};

    const auto p0 = swing.sample(start, target, 0.0);
    const auto pm = swing.sample(start, target, 0.5);
    const auto p1 = swing.sample(start, target, 1.0);

    assert(std::abs(p0.x - 0.0) < 1e-12);
    assert(std::abs(p1.x - 0.2) < 1e-12);
    assert(pm.z > p0.z);
    assert(pm.z > p1.z);
  }

  {
    TorqueSafetyFilter filter(23.7);

    std::array<double, 12> tau{};
    tau[0] = 30.0;
    tau[1] = -30.0;
    tau[2] = 1.0;
    tau[3] = std::numeric_limits<double>::quiet_NaN();

    const auto clamped = filter.clamp(tau);

    assert(std::abs(clamped[0] - 23.7) < 1e-12);
    assert(std::abs(clamped[1] + 23.7) < 1e-12);
    assert(std::abs(clamped[2] - 1.0) < 1e-12);
    assert(std::abs(clamped[3] - 0.0) < 1e-12);
    assert(filter.isFiniteAndWithinLimit(clamped));
    assert(!filter.isFiniteAndWithinLimit(tau));
  }

  std::cout << "C++ control algorithm tests passed" << std::endl;
  return 0;
}
