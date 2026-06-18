cmake_minimum_required(VERSION 3.8)
project(robot_mpc_wbc_cpp_controller)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)

# -----------------------------------------------------------------------------
# Stage 15.1: reusable C++ control algorithm library
# -----------------------------------------------------------------------------
add_library(control_algorithms STATIC
  src/control/gait_scheduler.cpp
  src/control/swing_trajectory.cpp
  src/control/torque_safety_filter.cpp
  src/control/contact_force_qp.cpp
)

target_compile_features(control_algorithms PUBLIC cxx_std_17)

target_include_directories(control_algorithms
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  target_compile_options(control_algorithms PRIVATE -Wall -Wextra -Wpedantic -Werror)
endif()

# -----------------------------------------------------------------------------
# Disabled-by-default ROS2 controller node.
# It must stay safe: no hardware torque execution is claimed by this package.
# -----------------------------------------------------------------------------
add_executable(go1_disabled_controller_node
  src/disabled_controller_node.cpp
)

target_compile_features(go1_disabled_controller_node PUBLIC cxx_std_17)

target_include_directories(go1_disabled_controller_node
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

ament_target_dependencies(go1_disabled_controller_node
  rclcpp
  sensor_msgs
  std_msgs
)

add_executable(zero_torque_dry_run_contract_check
  src/zero_torque_dry_run_contract_check.cpp
)

target_compile_features(zero_torque_dry_run_contract_check PUBLIC cxx_std_17)

target_include_directories(zero_torque_dry_run_contract_check
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

ament_target_dependencies(zero_torque_dry_run_contract_check
  rclcpp
  sensor_msgs
  std_msgs
)

add_executable(torque_safety_contract_check
  src/torque_safety_contract_check.cpp
)

target_compile_features(torque_safety_contract_check PUBLIC cxx_std_17)

target_include_directories(torque_safety_contract_check
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

ament_target_dependencies(torque_safety_contract_check
  rclcpp
  sensor_msgs
  std_msgs
)

# -----------------------------------------------------------------------------
# Install rules
# -----------------------------------------------------------------------------
install(
  TARGETS control_algorithms
  EXPORT export_control_algorithms
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
  INCLUDES DESTINATION include
)

install(
  TARGETS
    go1_disabled_controller_node
    zero_torque_dry_run_contract_check
    torque_safety_contract_check
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY include/ DESTINATION include)
install(DIRECTORY launch DESTINATION share/${PROJECT_NAME})

ament_export_include_directories(include)
ament_export_libraries(control_algorithms)
ament_export_targets(export_control_algorithms HAS_LIBRARY_TARGET)

# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------
if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)

  ament_add_gtest(test_control_algorithms
    test/test_control_algorithms.cpp
  )

  if(TARGET test_control_algorithms)
    target_link_libraries(test_control_algorithms
      control_algorithms
    )

    target_compile_features(test_control_algorithms PRIVATE cxx_std_17)

    target_include_directories(test_control_algorithms
      PRIVATE
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    )
  endif()

  ament_add_gtest(test_contact_force_qp
    test/test_contact_force_qp.cpp
  )

  if(TARGET test_contact_force_qp)
    target_link_libraries(test_contact_force_qp
      control_algorithms
    )

    target_compile_features(test_contact_force_qp PRIVATE cxx_std_17)

    target_include_directories(test_contact_force_qp
      PRIVATE
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    )
  endif()

endif()

ament_package()
