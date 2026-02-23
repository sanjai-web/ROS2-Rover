#!/usr/bin/env python3
"""
exploration.launch.py — Launches the frontier-based exploration node.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    frontier_explorer = Node(
        package='rover_sim',
        executable='frontier_explorer',
        name='frontier_explorer',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            # min frontier size to reduce noise
            'min_frontier_size': 5,
            # goal tolerance in meters
            'goal_tolerance': 0.3,
            # robot radius for frontier clearance check
            'robot_radius': 0.35,
            # map save path when exploration completes
            'map_save_path': '/tmp/rover_map',
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation clock',
        ),
        frontier_explorer,
    ])
