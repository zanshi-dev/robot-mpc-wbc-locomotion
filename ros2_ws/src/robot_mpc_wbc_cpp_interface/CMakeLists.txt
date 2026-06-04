cmake_minimum_required(VERSION 3.8)
project(robot_mpc_wbc_cpp_interface)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)

add_executable(go1_interface_mirror_node src/interface_mirror_node.cpp)
target_compile_features(go1_interface_mirror_node PUBLIC cxx_std_17)

ament_target_dependencies(
  go1_interface_mirror_node
  rclcpp
  sensor_msgs
  std_msgs
)

install(TARGETS
  go1_interface_mirror_node
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
