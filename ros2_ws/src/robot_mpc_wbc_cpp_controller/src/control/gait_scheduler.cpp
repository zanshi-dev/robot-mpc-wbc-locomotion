#include "robot_mpc_wbc_cpp_controller/control/gait_scheduler.hpp"

#include <stdexcept>

namespace robot_mpc_wbc_cpp_controller::control {

GaitScheduler::GaitScheduler(std::size_t half_period_steps)
: half_period_steps_(half_period_steps)
{
  if (half_period_steps_ == 0) {
    throw std::invalid_argument("half_period_steps must be positive");
  }
}

GaitState GaitScheduler::evaluate(std::size_t step) const
{
  const std::size_t phase = (step / half_period_steps_) % 2;
  const std::size_t phase_step = step % half_period_steps_;

  GaitState state;
  state.step = step;
  state.phase_step = phase_step;

  if (phase == 0) {
    state.mode = ContactMode::TrotFRRL;
    state.contact = {true, false, false, true};
  } else {
    state.mode = ContactMode::TrotFLRR;
    state.contact = {false, true, true, false};
  }

  return state;
}

std::size_t GaitScheduler::half_period_steps() const
{
  return half_period_steps_;
}

std::string GaitScheduler::mode_name(ContactMode mode)
{
  switch (mode) {
    case ContactMode::TrotFRRL:
      return "trot_FR_RL";
    case ContactMode::TrotFLRR:
      return "trot_FL_RR";
  }
  return "unknown";
}

}  // namespace robot_mpc_wbc_cpp_controller::control
