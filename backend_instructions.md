The "Full-Stack" Backend Architect Prompt
Copy and paste this prompt into an AI tool (or use it as your own project requirements document):

Role: ROS2 Robotics Architect

Task: Create a modular ROS2 Backend (Python-based) for a Rover Robot.

Hardware Specs to Model:

Compute: Raspberry Pi 5

Sensors: GPS (NavSat), Lidar (LaserScan), Temperature (sensor_msgs/Temperature), Camera (Image).

Actuators: 4-Motor Drive (Differential Drive).

Power: Battery (BatteryState).

Architecture Requirements:

Package Separation: Create a separate ROS2 Python package for each sensor/module to ensure a modular backend:

rover_gps

rover_lidar

rover_camera

rover_telemetry (for Battery and Temperature)

rover_control (for the 4-motor driver logic)

The "Master" Node: Create a central package called rover_bringup. Inside this package, write a Raspberry Pi 5 Master Node that:

Subscribes to all individual sensor topics.

Aggregates the data into a single "Robot Status" log or custom message.

Provides a ROS2 Service to "Ping" all sensors and return a health status report.

Standard Messaging: Use standard sensor_msgs types (e.g., NavSatFix for GPS, LaserScan for Lidar, Image for Camera) to ensure compatibility with RViz.

Launch System: Provide a single Python launch file in rover_bringup that starts all sensor nodes and the motor controller simultaneously.

Output Format: Provide the file structure for the workspace and the Python code for the master_node.py and a sample sensor_node.py