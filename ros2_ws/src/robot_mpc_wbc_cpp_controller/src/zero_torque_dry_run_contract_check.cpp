#include <iostream>

#include "robot_mpc_wbc_cpp_controller/zero_torque_dry_run.hpp"

int main() {
  const auto tau = robot_mpc_wbc_cpp_controller::makeZeroTorqueDryRun();

  const bool size_ok = tau.size() == robot_mpc_wbc_cpp_controller::kGo1NumActuatedJoints;
  const bool all_finite = robot_mpc_wbc_cpp_controller::allFinite(tau);
  const bool all_zero = robot_mpc_wbc_cpp_controller::allZero(tau);
  const double max_abs = robot_mpc_wbc_cpp_controller::maxAbs(tau);
  const double l1 = robot_mpc_wbc_cpp_controller::l1Norm(tau);

  std::cout << "metric,value\n";
  std::cout << "zero_torque_size," << tau.size() << "\n";
  std::cout << "zero_torque_expected_size," << robot_mpc_wbc_cpp_controller::kGo1NumActuatedJoints << "\n";
  std::cout << "zero_torque_size_ok," << (size_ok ? "True" : "False") << "\n";
  std::cout << "zero_torque_all_finite," << (all_finite ? "True" : "False") << "\n";
  std::cout << "zero_torque_all_zero," << (all_zero ? "True" : "False") << "\n";
  std::cout << "zero_torque_max_abs," << max_abs << "\n";
  std::cout << "zero_torque_l1," << l1 << "\n";

  for (std::size_t i = 0; i < tau.size(); ++i) {
    std::cout << "tau_" << i << "," << tau[i] << "\n";
  }

  return (size_ok && all_finite && all_zero && max_abs == 0.0 && l1 == 0.0) ? 0 : 2;
}
