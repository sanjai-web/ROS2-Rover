# 🤖 4-Wheeled Rover — ROS2 Project

A modular ROS2 (Jazzy) project for a 4-wheeled rover built on a **Raspberry Pi 5**, featuring sensor simulation nodes, a master brain aggregator, URDF visualization, and Gazebo plugin support.

---

## 📁 Project Structure

```
ros2_ws/
├── src/
│   ├── rover_gps/              # GPS sensor node
│   ├── rover_lidar/            # LiDAR sensor node
│   ├── rover_camera/           # Camera sensor node
│   ├── rover_telemetry/        # Battery & Temperature node
│   ├── rover_base/             # Motor controller (cmd_vel subscriber)
│   ├── rover_control/          # Master brain aggregator + system launch
│   └── rover_description/      # URDF model + RViz visualization
│       ├── urdf/rover.urdf
│       ├── launch/display.launch.py
│       └── rviz/default.rviz
└── Readme.md
```

---

## 🧩 Packages & Features

| Package | Node | Topic | Description |
|---|---|---|---|
| `rover_gps` | `gps_node` | `/rover/gps/fix` | Publishes `NavSatFix` at 1 Hz |
| `rover_lidar` | `lidar_node` | `/rover/lidar/scan` | Publishes `LaserScan` (180 pts) at 5 Hz |
| `rover_camera` | `camera_node` | `/rover/camera/image_raw` | Publishes `Image` frames at 10 Hz |
| `rover_telemetry` | `telemetry_node` | `/rover/battery`, `/rover/temperature` | Publishes battery & temperature at 1 Hz |
| `rover_base` | `base_driver` | Subscribes `/cmd_vel` | Differential drive motor simulator |
| `rover_control` | `main_brain` | All sensor topics | Aggregates data, prints system report |
| `rover_description` | — | — | URDF + RViz + Gazebo plugins |

---

## 🤖 URDF / Robot Model

The rover is defined in `rover.urdf` with:

- **Chassis** — Blue box (0.5 × 0.3 × 0.1 m)
- **4 Wheels** — Black cylinders, `continuous` joints (front_left, front_right, rear_left, rear_right)
- **LiDAR** — Red cylinder on top of chassis
- **GPS** — White box, rear of chassis
- **Camera** — Black box, front of chassis, tilted down
- **Temperature Sensor** — Small red box on chassis

### Gazebo Plugins
- `libgazebo_ros_diff_drive.so` — 4-wheel differential drive (`/cmd_vel` → `/odom`)
- `libgazebo_ros_ray_sensor.so` — LiDAR ray sensor
- `libgazebo_ros_camera.so` — Camera image publisher
- `libgazebo_ros_gps_sensor.so` — GPS fix publisher

---

## 🛠️ Prerequisites

```bash
# ROS2 Jazzy (Ubuntu 24.04 Noble)
sudo apt install ros-jazzy-desktop

# Required packages
sudo apt install ros-jazzy-joint-state-publisher
sudo apt install ros-jazzy-joint-state-publisher-gui   # optional GUI
sudo apt install ros-jazzy-robot-state-publisher
```

---

## ⚙️ Build

```bash
cd ~/Documents/First_Robot/ros2_ws
colcon build
source install/setup.bash
```

---

## 🚀 Running the Project

### 1. Launch all sensor nodes + master brain

```bash
cd ~/Documents/First_Robot/ros2_ws
source install/setup.bash
ros2 launch rover_control system_launch.py
```

**Expected output (every second):**
```
================ SYSTEM STATUS REPORT ================
Timestamp: 15:30:45
GPS Position: Lat: 37.7749, Lon: -122.4194
Lidar Status: 180 points per scan
Camera: Active (Last frame: 1234567890)
Battery Level: 99.9%
Temperature: 45.1C
======================================================
```

---

### 2. Visualize the rover in RViz

```bash
cd ~/Documents/First_Robot/ros2_ws
source install/setup.bash
ros2 launch rover_description display.launch.py
```

Opens RViz with the full 3D rover model (chassis + 4 wheels + sensors).

---

### 3. Run individual nodes

```bash
ros2 run rover_gps gps_node
ros2 run rover_lidar lidar_node
ros2 run rover_camera camera_node
ros2 run rover_telemetry telemetry_node
ros2 run rover_base base_driver
ros2 run rover_control main_brain
```

---

### 4. Send velocity commands (test motor control)

```bash
# Drive forward
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.5}, angular: {z: 0.0}}"

# Turn in place
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0}, angular: {z: 1.0}}"
```

---

## 📡 ROS2 Topics

| Topic | Type | Publisher |
|---|---|---|
| `/rover/gps/fix` | `sensor_msgs/NavSatFix` | `gps_node` |
| `/rover/lidar/scan` | `sensor_msgs/LaserScan` | `lidar_node` |
| `/rover/camera/image_raw` | `sensor_msgs/Image` | `camera_node` |
| `/rover/battery` | `sensor_msgs/BatteryState` | `telemetry_node` |
| `/rover/temperature` | `sensor_msgs/Temperature` | `telemetry_node` |
| `/cmd_vel` | `geometry_msgs/Twist` | External / Navigation |
| `/odom` | `nav_msgs/Odometry` | Gazebo diff_drive plugin |
| `/robot_description` | `std_msgs/String` | `robot_state_publisher` |
| `/joint_states` | `sensor_msgs/JointState` | `joint_state_publisher` |

---

## 🔧 Technical Stack

| Component | Technology |
|---|---|
| OS | Ubuntu 24.04 (Noble) |
| ROS2 Distribution | Jazzy |
| Language | Python 3.12 |
| Robot Description | URDF (XML) |
| Visualizer | RViz2 |
| Simulator | Gazebo (Classic) |
| Target Hardware | Raspberry Pi 5 |
| Drive System | Differential Drive (4-wheel) |

---

## 📝 Notes

- Always run `source install/setup.bash` from **inside `ros2_ws/`** after building.
- The sensor nodes simulate data — replace callbacks with real hardware drivers for physical deployment.
- Gazebo plugins are configured in `rover.urdf` under `<gazebo>` tags and only activate in Gazebo simulation.
