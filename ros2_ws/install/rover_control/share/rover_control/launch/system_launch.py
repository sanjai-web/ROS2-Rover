
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='rover_gps',
            executable='gps_node',
            name='gps_node'
        ),
        Node(
            package='rover_lidar',
            executable='lidar_node',
            name='lidar_node'
        ),
        Node(
            package='rover_camera',
            executable='camera_node',
            name='camera_node'
        ),
        Node(
            package='rover_telemetry',
            executable='telemetry_node',
            name='telemetry_node'
        ),
        Node(
            package='rover_base',
            executable='base_driver',
            name='base_driver'
        ),
        Node(
            package='rover_control',
            executable='main_brain',
            name='main_brain',
            output='screen'
        )
    ])
