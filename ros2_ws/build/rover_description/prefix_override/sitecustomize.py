import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/sanjai/Documents/First_Robot/ros2_ws/install/rover_description'
