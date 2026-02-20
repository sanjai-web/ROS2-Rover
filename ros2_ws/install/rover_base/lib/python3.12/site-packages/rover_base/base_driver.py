
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class BaseDriver(Node):
    def __init__(self):
        super().__init__('base_driver')
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.listener_callback,
            10)
        self.get_logger().info('Base Driver Node has been started.')

    def listener_callback(self, msg):
        # Differential drive kinematic model (simplified)
        # v = (v_right + v_left) / 2
        # omega = (v_right - v_left) / L
        
        linear_x = msg.linear.x
        angular_z = msg.angular.z
        
        # Calculate left and right wheel speeds (assuming robot width L = 0.5m)
        L = 0.5
        v_left = linear_x - (angular_z * L / 2.0)
        v_right = linear_x + (angular_z * L / 2.0)
        
        self.get_logger().info(f'Set Motors - Left: {v_left:.2f}, Right: {v_right:.2f}')

def main(args=None):
    rclpy.init(args=args)
    node = BaseDriver()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
