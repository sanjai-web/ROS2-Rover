
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import BatteryState, Temperature
import random

class TelemetryNode(Node):
    def __init__(self):
        super().__init__('telemetry_node')
        self.battery_publisher_ = self.create_publisher(BatteryState, '/rover/status/battery', 10)
        self.temp_publisher_ = self.create_publisher(Temperature, '/rover/status/temperature', 10)
        
        timer_period = 1.0  # 1 Hz
        self.timer = self.create_timer(timer_period, self.timer_callback)
        
        self.battery_level = 100.0
        self.get_logger().info('Telemetry Node has been started.')

    def timer_callback(self):
        # Battery State
        batt_msg = BatteryState()
        batt_msg.voltage = 12.0
        batt_msg.percentage = self.battery_level
        batt_msg.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_DISCHARGING
        
        # Simulate battery drain
        if self.battery_level > 0:
            self.battery_level -= 0.1
            
        self.battery_publisher_.publish(batt_msg)

        # Temperature
        temp_msg = Temperature()
        temp_msg.temperature = 45.0 + random.uniform(-2.0, 2.0) # approx 45 degrees Celsius
        temp_msg.variance = 0.1
        
        self.temp_publisher_.publish(temp_msg)
        
        self.get_logger().info(f'Telemetry Update - Battery: {batt_msg.percentage:.1f}%, Temp: {temp_msg.temperature:.1f}C')

def main(args=None):
    rclpy.init(args=args)
    node = TelemetryNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
