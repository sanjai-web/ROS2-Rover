
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, LaserScan, Image, BatteryState, Temperature
import time

class MainBrain(Node):
    def __init__(self):
        super().__init__('main_brain')
        
        # Subscriptions
        self.create_subscription(NavSatFix, '/rover/gps/fix', self.gps_callback, 10)
        self.create_subscription(LaserScan, '/rover/lidar/scan', self.lidar_callback, 10)
        self.create_subscription(Image, '/rover/camera/image_raw', self.camera_callback, 10)
        self.create_subscription(BatteryState, '/rover/status/battery', self.battery_callback, 10)
        self.create_subscription(Temperature, '/rover/status/temperature', self.temp_callback, 10)
        
        # Data storage
        self.latest_gps = None
        self.latest_lidar_points = 0
        self.latest_image_ts = None
        self.battery_level = 0.0
        self.temperature = 0.0
        
        # Reporter Timer
        self.create_timer(1.0, self.report_callback)
        self.get_logger().info('Main Brain Node has been started.')

    def gps_callback(self, msg):
        self.latest_gps = f"Lat: {msg.latitude:.4f}, Lon: {msg.longitude:.4f}"

    def lidar_callback(self, msg):
        self.latest_lidar_points = len(msg.ranges)

    def camera_callback(self, msg):
        self.latest_image_ts = msg.header.stamp.sec

    def battery_callback(self, msg):
        self.battery_level = msg.percentage

    def temp_callback(self, msg):
        self.temperature = msg.temperature

    def report_callback(self):
        report = f"""
        ================ SYSTEM STATUS REPORT ================
        Timestamp: {time.strftime('%H:%M:%S')}
        GPS Position: {self.latest_gps if self.latest_gps else 'Waiting...'}
        Lidar Status: {self.latest_lidar_points} points per scan
        Camera: {f'Active (Last frame: {self.latest_image_ts})' if self.latest_image_ts else 'Waiting...'}
        Battery Level: {self.battery_level:.1f}%
        Temperature: {self.temperature:.1f}C
        ======================================================
        """
        print(report)
        # self.get_logger().info(report) # Also log to ROS logger

def main(args=None):
    rclpy.init(args=args)
    node = MainBrain()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
