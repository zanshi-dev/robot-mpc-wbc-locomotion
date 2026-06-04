#pragma once

#include <array>
#include <cstddef>
#include <string>

namespace robot_mpc_wbc_cpp_controller::control {

enum class LegIndex : std::size_t {
  FR = 0,
  FL = 1,
  RR = 2,
  RL = 3
};

enum class ContactMode {
  TrotFRRL,
  TrotFLRR
};

struct GaitState {
  std::array<bool, 4> contact{};
  ContactMode mode{ContactMode::TrotFRRL};
  std::size_t step{0};
  std::size_t phase_step{0};
};

class GaitScheduler {
public:
  explicit GaitScheduler(std::size_t half_period_steps = 200);

  GaitState evaluate(std::size_t step) const;

  std::size_t half_period_steps() const;

  static std::string mode_name(ContactMode mode);

private:
  std::size_t half_period_steps_;
};

}  // namespace robot_mpc_wbc_cpp_controller::control
