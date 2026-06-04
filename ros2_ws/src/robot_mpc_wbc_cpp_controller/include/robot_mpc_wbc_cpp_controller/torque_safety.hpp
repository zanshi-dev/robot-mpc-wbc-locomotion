#pragma once

#include <array>
#include <cmath>
#include <cstddef>

#include "robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

namespace robot_mpc_wbc_cpp_controller {

struct TorqueClampConfig {
  TorqueVector max_abs_torque{};
};

struct TorqueClampResult {
  TorqueVector tau{};
  bool input_all_finite = true;
  bool output_all_finite = true;
  bool clamp_applied = false;
  double max_abs_after_clamp = 0.0;
};

inline TorqueClampConfig makeUniformTorqueClampConfig(const double max_abs_value) {
  TorqueClampConfig config{};
  for (auto & value : config.max_abs_torque) {
    value = std::abs(max_abs_value);
  }
  return config;
}

inline TorqueClampResult clampTorqueCommand(
  const TorqueVector & raw_tau,
  const TorqueClampConfig & config) {
  TorqueClampResult result{};

  for (std::size_t i = 0; i < kGo1NumActuatedJoints; ++i) {
    const double raw_value = raw_tau[i];
    const double limit = std::abs(config.max_abs_torque[i]);

    double safe_value = 0.0;

    if (std::isfinite(raw_value)) {
      safe_value = raw_value;
    } else {
      result.input_all_finite = false;
      result.clamp_applied = true;
    }

    if (safe_value > limit) {
      safe_value = limit;
      result.clamp_applied = true;
    }

    if (safe_value < -limit) {
      safe_value = -limit;
      result.clamp_applied = true;
    }

    result.tau[i] = safe_value;

    if (!std::isfinite(result.tau[i])) {
      result.output_all_finite = false;
    }

    const double abs_value = std::abs(result.tau[i]);
    if (abs_value > result.max_abs_after_clamp) {
      result.max_abs_after_clamp = abs_value;
    }
  }

  return result;
}

inline bool isFresh(const double age_seconds, const double timeout_seconds) {
  return std::isfinite(age_seconds) &&
         std::isfinite(timeout_seconds) &&
         age_seconds >= 0.0 &&
         timeout_seconds > 0.0 &&
         age_seconds <= timeout_seconds;
}

inline bool allInputsFresh(
  const std::array<double, 5> & input_ages_seconds,
  const double timeout_seconds) {
  for (const auto age : input_ages_seconds) {
    if (!isFresh(age, timeout_seconds)) {
      return false;
    }
  }
  return true;
}

inline TorqueVector watchdogFallbackZeroTorque() {
  return makeZeroTorqueDryRun();
}

}  // namespace robot_mpc_wbc_cpp_controller
