#!/usr/bin/env python3
"""
gazebo.launch.py — Launches Gazebo Harmonic with the indoor world,
spawns the rover, runs robot_state_publisher + joint_state_publisher,
ros_gz_bridge, and static TF publishers to fix Gazebo Harmonic's
scoped frame names.

TF chain produced:
  odom (Gazebo DiffDrive)
    └─ rover/base_link (Gazebo DiffDrive publishes this)
         └─ base_link  ← static TF (identity remap)
              └─ chassis, lidar_link, camera_link, wheels…  ← robot_state_publisher
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_rover_sim         = get_package_share_directory('rover_sim')
    pkg_rover_description = get_package_share_directory('rover_description')
    pkg_ros_gz_sim        = get_package_share_directory('ros_gz_sim')

    world_file = os.path.join(pkg_rover_sim, 'worlds', 'indoor_world.sdf')
    urdf_file  = os.path.join(pkg_rover_description, 'urdf', 'rover_gz.urdf')

    with open(urdf_file, 'r') as f:
        robot_description = f.read()

    use_sim_time = True

    # ── Gazebo Harmonic ────────────────────────────────────────────────────────
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': f'-r {world_file}',
            'on_exit_shutdown': 'true',
        }.items(),
    )

    # ── Robot State Publisher ──────────────────────────────────────────────────
    # Publishes: base_link → chassis → lidar_link, camera_link, wheels, etc.
    # Requires /joint_states for the 4 continuously-rotating wheel joints.
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
            'ignore_timestamp': True,
        }],
    )





    # ── Spawn rover ────────────────────────────────────────────────────────────
    spawn_rover = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_rover',
        output='screen',
        arguments=[
            '-name', 'rover',
            '-topic', 'robot_description',
            '-x', '0.0', '-y', '0.0', '-z', '0.15',
        ],
    )

    # ── ROS-GZ Bridge ─────────────────────────────────────────────────────────
    ros_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_bridge',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'config_file': os.path.join(pkg_rover_sim, 'config', 'ros_gz_bridge.yaml'),
            'expand_gz_topic_names': True,
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation (Gazebo) clock if true',
        ),
        # t=0: Robot state publisher needs robot_description immediately
        robot_state_publisher,
        # t=0: Gazebo sim world
        gz_sim,
        # t=3: Spawn rover (Gazebo needs a few seconds to initialize the world)
        TimerAction(period=3.0, actions=[spawn_rover]),
        # t=4.5: ROS-GZ Bridge (after rover is spawned and Gazebo topics exist)
        TimerAction(period=4.5, actions=[ros_gz_bridge]),
    ])
