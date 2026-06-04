#include <array>
#include <cmath>
#include <iostream>
#include <limits>

#include "robot_mpc_wbc_cpp_controller/torque_safety.hpp"

int main() {
  using robot_mpc_wbc_cpp_controller::TorqueVector;
  using robot_mpc_wbc_cpp_controller::allInputsFresh;
  using robot_mpc_wbc_cpp_controller::allZero;
  using robot_mpc_wbc_cpp_controller::clampTorqueCommand;
  using robot_mpc_wbc_cpp_controller::kGo1NumActuatedJoints;
  using robot_mpc_wbc_cpp_controller::makeUniformTorqueClampConfig;
  using robot_mpc_wbc_cpp_controller::makeZeroTorqueDryRun;
  using robot_mpc_wbc_cpp_controller::watchdogFallbackZeroTorque;

  const auto config = makeUniformTorqueClampConfig(10.0);

  TorqueVector raw{};
  raw[0] = 0.0;
  raw[1] = 5.0;
  raw[2] = -5.0;
  raw[3] = 11.0;
  raw[4] = -11.0;
  raw[5] = std::numeric_limits<double>::quiet_NaN();
  raw[6] = std::numeric_limits<double>::infinity();
  raw[7] = -std::numeric_limits<double>::infinity();
  raw[8] = 10.0;
  raw[9] = -10.0;
  raw[10] = 3.0;
  raw[11] = -3.0;

  const auto clamp_result = clampTorqueCommand(raw, config);

  const bool clamp_output_size_ok = clamp_result.tau.size() == kGo1NumActuatedJoints;
  const bool clamp_output_all_finite = clamp_result.output_all_finite;
  const bool clamp_detected_nonfinite = !clamp_result.input_all_finite;
  const bool clamp_applied = clamp_result.clamp_applied;
  const bool clamp_max_abs_ok = clamp_result.max_abs_after_clamp <= 10.0;

  const bool clamp_expected_values_ok =
    clamp_result.tau[0] == 0.0 &&
    clamp_result.tau[1] == 5.0 &&
    clamp_result.tau[2] == -5.0 &&
    clamp_result.tau[3] == 10.0 &&
    clamp_result.tau[4] == -10.0 &&
    clamp_result.tau[5] == 0.0 &&
    clamp_result.tau[6] == 0.0 &&
    clamp_result.tau[7] == 0.0 &&
    clamp_result.tau[8] == 10.0 &&
    clamp_result.tau[9] == -10.0 &&
    clamp_result.tau[10] == 3.0 &&
    clamp_result.tau[11] == -3.0;

  const auto zero_tau = makeZeroTorqueDryRun();
  const auto zero_clamp = clampTorqueCommand(zero_tau, config);
  const bool zero_clamp_all_zero = allZero(zero_clamp.tau);

  const bool watchdog_fresh_ok = allInputsFresh({0.0, 0.01, 0.02, 0.03, 0.04}, 0.10);
  const bool watchdog_stale_blocks = !allInputsFresh({0.0, 0.01, 0.20, 0.03, 0.04}, 0.10);
  const bool watchdog_nan_blocks = !allInputsFresh(
    {0.0, std::numeric_limits<double>::quiet_NaN(), 0.02, 0.03, 0.04},
    0.10);

  const auto watchdog_zero = watchdogFallbackZeroTorque();
  const bool watchdog_zero_all_zero = allZero(watchdog_zero);

  std::cout << "metric,value\n";
  std::cout << "clamp_output_size," << clamp_result.tau.size() << "\n";
  std::cout << "clamp_expected_size," << kGo1NumActuatedJoints << "\n";
  std::cout << "clamp_output_size_ok," << (clamp_output_size_ok ? "True" : "False") << "\n";
  std::cout << "clamp_output_all_finite," << (clamp_output_all_finite ? "True" : "False") << "\n";
  std::cout << "clamp_detected_nonfinite," << (clamp_detected_nonfinite ? "True" : "False") << "\n";
  std::cout << "clamp_applied," << (clamp_applied ? "True" : "False") << "\n";
  std::cout << "clamp_max_abs_after," << clamp_result.max_abs_after_clamp << "\n";
  std::cout << "clamp_max_abs_ok," << (clamp_max_abs_ok ? "True" : "False") << "\n";
  std::cout << "clamp_expected_values_ok," << (clamp_expected_values_ok ? "True" : "False") << "\n";
  std::cout << "zero_clamp_all_zero," << (zero_clamp_all_zero ? "True" : "False") << "\n";
  std::cout << "watchdog_fresh_ok," << (watchdog_fresh_ok ? "True" : "False") << "\n";
  std::cout << "watchdog_stale_blocks," << (watchdog_stale_blocks ? "True" : "False") << "\n";
  std::cout << "watchdog_nan_blocks," << (watchdog_nan_blocks ? "True" : "False") << "\n";
  std::cout << "watchdog_zero_all_zero," << (watchdog_zero_all_zero ? "True" : "False") << "\n";

  for (std::size_t i = 0; i < clamp_result.tau.size(); ++i) {
    std::cout << "clamped_tau_" << i << "," << clamp_result.tau[i] << "\n";
  }

  const bool pass =
    clamp_output_size_ok &&
    clamp_output_all_finite &&
    clamp_detected_nonfinite &&
    clamp_applied &&
    clamp_max_abs_ok &&
    clamp_expected_values_ok &&
    zero_clamp_all_zero &&
    watchdog_fresh_ok &&
    watchdog_stale_blocks &&
    watchdog_nan_blocks &&
    watchdog_zero_all_zero;

  return pass ? 0 : 2;
}
