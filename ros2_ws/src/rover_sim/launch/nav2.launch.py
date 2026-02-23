#!/usr/bin/env python3
"""
nav2.launch.py — Launches individual Nav2 nodes for Jazzy.
- Excludes docking_server and route_server (Jazzy-new, need extra config)
- Excludes velocity_smoother (wrong remaps cause cmd_vel loop)
- controller_server publishes directly to /cmd_vel
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_rover_sim = get_package_share_directory('rover_sim')
    nav2_params_file = os.path.join(pkg_rover_sim, 'config', 'nav2_params.yaml')
    use_sim_time = True

    nav2_params = [nav2_params_file, {'use_sim_time': True}]

    # ── Controller server — publishes directly to /cmd_vel ────────────────────
    controller_server = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=nav2_params,
        remappings=[('cmd_vel', '/cmd_vel')],
    )

    # ── Smoother server ───────────────────────────────────────────────────────
    smoother_server = Node(
        package='nav2_smoother',
        executable='smoother_server',
        name='smoother_server',
        output='screen',
        parameters=nav2_params,
    )

    # ── Planner server ────────────────────────────────────────────────────────
    planner_server = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=nav2_params,
    )

    # ── Behavior (recoveries) server ──────────────────────────────────────────
    behavior_server = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',
        output='screen',
        parameters=nav2_params,
        remappings=[('cmd_vel', '/cmd_vel')],
    )

    # ── BT Navigator ──────────────────────────────────────────────────────────
    bt_navigator = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=nav2_params,
    )

    # ── Waypoint follower ─────────────────────────────────────────────────────
    waypoint_follower = Node(
        package='nav2_waypoint_follower',
        executable='waypoint_follower',
        name='waypoint_follower',
        output='screen',
        parameters=nav2_params,
    )

    # ── Lifecycle manager ─────────────────────────────────────────────────────
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'autostart': True,
            'bond_timeout': 10.0,
            'attempt_respawn_reconnection': True,
            'node_names': [
                'controller_server',
                'smoother_server',
                'planner_server',
                'behavior_server',
                'bt_navigator',
                'waypoint_follower',
            ],
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation clock',
        ),
        controller_server,
        smoother_server,
        planner_server,
        behavior_server,
        bt_navigator,
        waypoint_follower,
        lifecycle_manager,
    ])
