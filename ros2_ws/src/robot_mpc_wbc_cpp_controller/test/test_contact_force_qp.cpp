#include "robot_mpc_wbc_cpp_controller/control/contact_force_qp.hpp"

#include <cmath>

#include <gtest/gtest.h>

using robot_mpc_wbc_cpp_controller::control::ContactForceQp;
using robot_mpc_wbc_cpp_controller::control::ContactForceQpConfig;
using robot_mpc_wbc_cpp_controller::control::ContactForceQpInput;
using robot_mpc_wbc_cpp_controller::control::Vec3;

TEST(ContactForceQpTest, FourStanceHoverForceMatchesWeight)
{
  ContactForceQpConfig config;
  config.mass_kg = 12.7434;
  config.gravity = 9.81;
  config.friction_coefficient = 0.6;
  config.min_normal_force = 1.0;
  config.max_normal_force = 100.0;

  ContactForceQp solver(config);
  ContactForceQpInput input;
  input.desired_linear_acceleration = Vec3{0.0, 0.0, 0.0};
  input.contact = {true, true, true, true};

  const auto result = solver.solve(input);

  ASSERT_TRUE(result.success) << result.status;
  EXPECT_EQ(result.status, "projected_contact_force_solution");
  EXPECT_TRUE(solver.checkConstraints(input, result));
  EXPECT_NEAR(result.net_force.x, 0.0, 1e-12);
  EXPECT_NEAR(result.net_force.y, 0.0, 1e-12);
  EXPECT_NEAR(result.net_force.z, config.mass_kg * config.gravity, 1e-9);
  EXPECT_NEAR(result.net_force_error_norm, 0.0, 1e-9);

  const double expected_fz = config.mass_kg * config.gravity / 4.0;
  for (const auto& force : result.foot_forces) {
    EXPECT_NEAR(force.x, 0.0, 1e-12);
    EXPECT_NEAR(force.y, 0.0, 1e-12);
    EXPECT_NEAR(force.z, expected_fz, 1e-9);
  }
}

TEST(ContactForceQpTest, SwingLegForcesAreZeroInTrotContactMode)
{
  ContactForceQpConfig config;
  config.mass_kg = 12.7434;
  config.gravity = 9.81;
  config.friction_coefficient = 0.6;
  config.min_normal_force = 1.0;
  config.max_normal_force = 100.0;

  ContactForceQp solver(config);
  ContactForceQpInput input;
  input.desired_linear_acceleration = Vec3{0.0, 0.0, 0.0};
  input.contact = {true, false, false, true};

  const auto result = solver.solve(input);

  ASSERT_TRUE(result.success) << result.status;
  EXPECT_TRUE(solver.checkConstraints(input, result));
  EXPECT_NEAR(result.foot_forces[1].x, 0.0, 1e-12);
  EXPECT_NEAR(result.foot_forces[1].y, 0.0, 1e-12);
  EXPECT_NEAR(result.foot_forces[1].z, 0.0, 1e-12);
  EXPECT_NEAR(result.foot_forces[2].x, 0.0, 1e-12);
  EXPECT_NEAR(result.foot_forces[2].y, 0.0, 1e-12);
  EXPECT_NEAR(result.foot_forces[2].z, 0.0, 1e-12);

  const double expected_fz = config.mass_kg * config.gravity / 2.0;
  EXPECT_NEAR(result.foot_forces[0].z, expected_fz, 1e-9);
  EXPECT_NEAR(result.foot_forces[3].z, expected_fz, 1e-9);
}

TEST(ContactForceQpTest, LargeTangentialDemandIsProjectedIntoFrictionPyramid)
{
  ContactForceQpConfig config;
  config.mass_kg = 12.7434;
  config.gravity = 9.81;
  config.friction_coefficient = 0.2;
  config.min_normal_force = 1.0;
  config.max_normal_force = 100.0;

  ContactForceQp solver(config);
  ContactForceQpInput input;
  input.desired_linear_acceleration = Vec3{10.0, 0.0, 0.0};
  input.contact = {true, true, true, true};

  const auto result = solver.solve(input);

  ASSERT_TRUE(result.success) << result.status;
  EXPECT_TRUE(solver.checkConstraints(input, result));
  EXPECT_NEAR(result.max_friction_violation, 0.0, 1e-12);
  EXPECT_GT(result.net_force_error_norm, 1.0);

  for (const auto& force : result.foot_forces) {
    EXPECT_LE(std::abs(force.x), config.friction_coefficient * force.z + 1e-12);
    EXPECT_LE(std::abs(force.y), config.friction_coefficient * force.z + 1e-12);
  }
}

TEST(ContactForceQpTest, NoActiveContactFailsSafely)
{
  ContactForceQp solver;
  ContactForceQpInput input;
  input.desired_linear_acceleration = Vec3{0.0, 0.0, 0.0};
  input.contact = {false, false, false, false};

  const auto result = solver.solve(input);

  EXPECT_FALSE(result.success);
  EXPECT_EQ(result.status, "no_active_contacts");
}
