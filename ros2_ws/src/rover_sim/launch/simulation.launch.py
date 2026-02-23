#!/usr/bin/env python3
"""
simulation.launch.py — Top-level launch file.

Starts the full simulation stack with timed sequencing:
  t= 0s : Gazebo Harmonic + rover spawn + ros_gz_bridge
  t= 5s : RViz2
  t= 6s : SLAM Toolbox (async)
  t=10s : Nav2 stack
  t=15s : Frontier exploration node
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
    pkg_rover_sim = get_package_share_directory('rover_sim')
    rviz_config = os.path.join(pkg_rover_sim, 'rviz', 'rviz_config.rviz')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    # ── Sub-launch helper ──────────────────────────────────────────────────────
    def include(launch_file, args=None):
        return IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_rover_sim, 'launch', launch_file)
            ),
            launch_arguments=(args or {}).items(),
        )

    # ── Gazebo + Bridge (t=0) ──────────────────────────────────────────────────
    gazebo_launch = include('gazebo.launch.py', {'use_sim_time': 'true'})

    # ── RViz2 (t=5s) ──────────────────────────────────────────────────────────
    rviz2_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )

    # ── SLAM Toolbox (t=6s) ────────────────────────────────────────────────────
    slam_launch = include('slam.launch.py', {'use_sim_time': 'true'})

    # ── Nav2 (t=10s) ──────────────────────────────────────────────────────────
    nav2_launch = include('nav2.launch.py', {'use_sim_time': 'true'})

    # ── Frontier Explorer (t=15s) ──────────────────────────────────────────────
    exploration_launch = include('exploration.launch.py', {'use_sim_time': 'true'})

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use Gazebo simulation time',
        ),
        # t=0: Start Gazebo world + rover spawn + bridge
        gazebo_launch,
        # t=7: Start RViz2
        TimerAction(period=7.0, actions=[rviz2_node]),
        # t=8: Start SLAM Toolbox (give Gazebo enough time to publish /clock + LiDAR)
        TimerAction(period=8.0, actions=[slam_launch]),
        # t=15: Start Nav2 (give SLAM time to publish first /map)
        TimerAction(period=15.0, actions=[nav2_launch]),
        # t=25: Start frontier explorer (Nav2 must be fully activated)
        TimerAction(period=25.0, actions=[exploration_launch]),
    ])
