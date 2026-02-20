
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix

class GPSNode(Node):
    def __init__(self):
        super().__init__('gps_node')
        self.publisher_ = self.create_publisher(NavSatFix, '/rover/gps/fix', 10)
        timer_period = 1.0  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.get_logger().info('GPS Node has been started.')

    def timer_callback(self):
        msg = NavSatFix()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "gps_link"
        
        # Simulate GPS coordinates (example: somewhere in San Francisco)
        msg.latitude = 37.7749
        msg.longitude = -122.4194
        msg.altitude = 10.0
        
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing GPS Fix: Lat: {msg.latitude}, Lon: {msg.longitude}')

def main(args=None):
    rclpy.init(args=args)
    node = GPSNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
