#include "robot_mpc_wbc_cpp_controller/control/gait_scheduler.hpp"
#include "robot_mpc_wbc_cpp_controller/control/swing_trajectory.hpp"
#include "robot_mpc_wbc_cpp_controller/control/torque_safety_filter.hpp"

#include <array>
#include <cmath>
#include <limits>
#include <string>

#include <gtest/gtest.h>

using robot_mpc_wbc_cpp_controller::control::GaitScheduler;
using robot_mpc_wbc_cpp_controller::control::SwingTrajectory;
using robot_mpc_wbc_cpp_controller::control::TorqueSafetyFilter;
using robot_mpc_wbc_cpp_controller::control::Vec3;

TEST(GaitSchedulerTest, AlternatesTrotContacts)
{
  GaitScheduler scheduler(200);

  const auto s0 = scheduler.evaluate(0);
  EXPECT_TRUE(s0.contact[0]);
  EXPECT_FALSE(s0.contact[1]);
  EXPECT_FALSE(s0.contact[2]);
  EXPECT_TRUE(s0.contact[3]);
  EXPECT_EQ(GaitScheduler::mode_name(s0.mode), std::string("trot_FR_RL"));

  const auto s200 = scheduler.evaluate(200);
  EXPECT_FALSE(s200.contact[0]);
  EXPECT_TRUE(s200.contact[1]);
  EXPECT_TRUE(s200.contact[2]);
  EXPECT_FALSE(s200.contact[3]);
  EXPECT_EQ(GaitScheduler::mode_name(s200.mode), std::string("trot_FL_RR"));

  const auto s400 = scheduler.evaluate(400);
  EXPECT_TRUE(s400.contact[0]);
  EXPECT_TRUE(s400.contact[3]);
  EXPECT_EQ(GaitScheduler::mode_name(s400.mode), std::string("trot_FR_RL"));
}

TEST(SwingTrajectoryTest, GeneratesLiftedMidpoint)
{
  SwingTrajectory swing(0.06);
  const Vec3 start{0.0, 0.0, 0.0};
  const Vec3 target{0.2, 0.0, 0.0};

  const auto p0 = swing.sample(start, target, 0.0);
  const auto pm = swing.sample(start, target, 0.5);
  const auto p1 = swing.sample(start, target, 1.0);

  EXPECT_NEAR(p0.x, 0.0, 1e-12);
  EXPECT_NEAR(p1.x, 0.2, 1e-12);
  EXPECT_GT(pm.z, p0.z);
  EXPECT_GT(pm.z, p1.z);
}

TEST(TorqueSafetyFilterTest, ClampsAndRejectsInvalidTorque)
{
  TorqueSafetyFilter filter(23.7);

  std::array<double, 12> tau{};
  tau[0] = 30.0;
  tau[1] = -30.0;
  tau[2] = 1.0;
  tau[3] = std::numeric_limits<double>::quiet_NaN();

  const auto clamped = filter.clamp(tau);

  EXPECT_NEAR(clamped[0], 23.7, 1e-12);
  EXPECT_NEAR(clamped[1], -23.7, 1e-12);
  EXPECT_NEAR(clamped[2], 1.0, 1e-12);
  EXPECT_NEAR(clamped[3], 0.0, 1e-12);

  EXPECT_TRUE(filter.isFiniteAndWithinLimit(clamped));
  EXPECT_FALSE(filter.isFiniteAndWithinLimit(tau));
}
