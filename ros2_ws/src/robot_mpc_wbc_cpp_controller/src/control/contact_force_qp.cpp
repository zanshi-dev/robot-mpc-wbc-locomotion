#include "robot_mpc_wbc_cpp_controller/control/contact_force_qp.hpp"

#include <algorithm>
#include <cmath>
#include <limits>

namespace robot_mpc_wbc_cpp_controller::control {
namespace {

[[nodiscard]] double clamp(double value, double lower, double upper)
{
  return std::max(lower, std::min(value, upper));
}

[[nodiscard]] double square(double value)
{
  return value * value;
}

[[nodiscard]] double norm3(const Vec3& v)
{
  return std::sqrt(square(v.x) + square(v.y) + square(v.z));
}

[[nodiscard]] bool isFinite(const Vec3& v)
{
  return std::isfinite(v.x) && std::isfinite(v.y) && std::isfinite(v.z);
}

[[nodiscard]] Vec3 add(const Vec3& a, const Vec3& b)
{
  return Vec3{a.x + b.x, a.y + b.y, a.z + b.z};
}

[[nodiscard]] Vec3 subtract(const Vec3& a, const Vec3& b)
{
  return Vec3{a.x - b.x, a.y - b.y, a.z - b.z};
}

}  // namespace

ContactForceQp::ContactForceQp(ContactForceQpConfig config)
: config_(config)
{
}

ContactForceQpResult ContactForceQp::solve(const ContactForceQpInput& input) const
{
  ContactForceQpResult result;

  if (config_.mass_kg <= 0.0 || !std::isfinite(config_.mass_kg)) {
    result.status = "invalid_mass";
    return result;
  }
  if (config_.gravity <= 0.0 || !std::isfinite(config_.gravity)) {
    result.status = "invalid_gravity";
    return result;
  }
  if (config_.friction_coefficient < 0.0 || !std::isfinite(config_.friction_coefficient)) {
    result.status = "invalid_friction_coefficient";
    return result;
  }
  if (config_.min_normal_force < 0.0 ||
      config_.max_normal_force < config_.min_normal_force ||
      !std::isfinite(config_.min_normal_force) ||
      !std::isfinite(config_.max_normal_force)) {
    result.status = "invalid_normal_force_limits";
    return result;
  }
  if (!isFinite(input.desired_linear_acceleration)) {
    result.status = "invalid_desired_acceleration";
    return result;
  }

  int contact_count = 0;
  for (const bool in_contact : input.contact) {
    if (in_contact) {
      ++contact_count;
    }
  }

  result.desired_net_force = Vec3{
    config_.mass_kg * input.desired_linear_acceleration.x,
    config_.mass_kg * input.desired_linear_acceleration.y,
    config_.mass_kg * (input.desired_linear_acceleration.z + config_.gravity)};

  if (contact_count == 0) {
    result.status = "no_active_contacts";
    return result;
  }

  const Vec3 nominal_per_contact{
    result.desired_net_force.x / static_cast<double>(contact_count),
    result.desired_net_force.y / static_cast<double>(contact_count),
    result.desired_net_force.z / static_cast<double>(contact_count)};

  for (std::size_t leg = 0; leg < result.foot_forces.size(); ++leg) {
    if (!input.contact[leg]) {
      result.foot_forces[leg] = Vec3{0.0, 0.0, 0.0};
      continue;
    }

    const double fz = clamp(
      nominal_per_contact.z,
      config_.min_normal_force,
      config_.max_normal_force);
    const double tangential_limit = config_.friction_coefficient * fz;

    result.foot_forces[leg] = Vec3{
      clamp(nominal_per_contact.x, -tangential_limit, tangential_limit),
      clamp(nominal_per_contact.y, -tangential_limit, tangential_limit),
      fz};
  }

  for (std::size_t leg = 0; leg < result.foot_forces.size(); ++leg) {
    const Vec3& f = result.foot_forces[leg];
    result.net_force = add(result.net_force, f);

    if (input.contact[leg]) {
      const double fx_violation = std::max(0.0, std::abs(f.x) - config_.friction_coefficient * f.z);
      const double fy_violation = std::max(0.0, std::abs(f.y) - config_.friction_coefficient * f.z);
      const double low_fz_violation = std::max(0.0, config_.min_normal_force - f.z);
      const double high_fz_violation = std::max(0.0, f.z - config_.max_normal_force);

      result.max_friction_violation = std::max(
        result.max_friction_violation,
        std::max(fx_violation, fy_violation));
      result.max_normal_force_violation = std::max(
        result.max_normal_force_violation,
        std::max(low_fz_violation, high_fz_violation));
    } else {
      result.max_swing_force_norm = std::max(result.max_swing_force_norm, norm3(f));
    }
  }

  result.net_force_error_norm = norm3(subtract(result.net_force, result.desired_net_force));
  result.success = checkConstraints(input, result);
  result.status = result.success ? "projected_contact_force_solution" : "constraint_violation";
  return result;
}

bool ContactForceQp::checkConstraints(
  const ContactForceQpInput& input,
  const ContactForceQpResult& result,
  double tolerance) const
{
  for (std::size_t leg = 0; leg < result.foot_forces.size(); ++leg) {
    const Vec3& f = result.foot_forces[leg];
    if (!isFinite(f)) {
      return false;
    }

    if (!input.contact[leg]) {
      if (norm3(f) > tolerance) {
        return false;
      }
      continue;
    }

    if (f.z < config_.min_normal_force - tolerance) {
      return false;
    }
    if (f.z > config_.max_normal_force + tolerance) {
      return false;
    }
    if (std::abs(f.x) > config_.friction_coefficient * f.z + tolerance) {
      return false;
    }
    if (std::abs(f.y) > config_.friction_coefficient * f.z + tolerance) {
      return false;
    }
  }

  return true;
}

}  // namespace robot_mpc_wbc_cpp_controller::control
