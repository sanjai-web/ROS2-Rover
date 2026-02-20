
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import math

class LidarNode(Node):
    def __init__(self):
        super().__init__('lidar_node')
        self.publisher_ = self.create_publisher(LaserScan, '/rover/lidar/scan', 10)
        timer_period = 0.2  # 0.2 seconds = 5Hz
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.get_logger().info('Lidar Node has been started.')

    def timer_callback(self):
        msg = LaserScan()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'lidar_link'
        msg.angle_min = -1.57
        msg.angle_max = 1.57
        msg.angle_increment = 0.0175 # 1 degree
        msg.range_min = 0.1
        msg.range_max = 10.0
        
        # Simulate 180 readings (approx 180 degrees)
        msg.ranges = [2.0 + 0.1 * math.sin(i * 0.1) for i in range(180)]
        
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing Lidar Scan with {len(msg.ranges)} points')

def main(args=None):
    rclpy.init(args=args)
    node = LidarNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
