cmake_minimum_required(VERSION 3.8)
project(robot_mpc_wbc_cpp_controller)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)

add_executable(go1_disabled_controller_node src/disabled_controller_node.cpp)
target_compile_features(go1_disabled_controller_node PUBLIC cxx_std_17)
target_include_directories(
  go1_disabled_controller_node
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

ament_target_dependencies(
  go1_disabled_controller_node
  rclcpp
  sensor_msgs
  std_msgs
)

add_executable(zero_torque_dry_run_contract_check src/zero_torque_dry_run_contract_check.cpp)
target_compile_features(zero_torque_dry_run_contract_check PUBLIC cxx_std_17)
target_include_directories(
  zero_torque_dry_run_contract_check
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

add_executable(torque_safety_contract_check src/torque_safety_contract_check.cpp)
target_compile_features(torque_safety_contract_check PUBLIC cxx_std_17)
target_include_directories(
  torque_safety_contract_check
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

install(TARGETS
  go1_disabled_controller_node
  zero_torque_dry_run_contract_check
  torque_safety_contract_check
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}
)

install(DIRECTORY
  include/
  DESTINATION include
)


# Stage 14.3: clean C++ control algorithm library and tests.
add_library(control_algorithms
  src/control/gait_scheduler.cpp
  src/control/swing_trajectory.cpp
  src/control/torque_safety_filter.cpp
)

target_include_directories(control_algorithms PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

target_compile_features(control_algorithms PUBLIC cxx_std_17)

if(BUILD_TESTING)
  find_package(ament_cmake_gtest QUIET)

  add_executable(test_control_algorithms
    test/test_control_algorithms.cpp
  )

  target_link_libraries(test_control_algorithms
    control_algorithms
  )

  target_compile_features(test_control_algorithms PRIVATE cxx_std_17)

  add_test(NAME test_control_algorithms COMMAND test_control_algorithms)
endif()

ament_package()
