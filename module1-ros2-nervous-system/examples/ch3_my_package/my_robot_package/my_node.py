import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MyRobotNode(Node):
    """
    Example robot node that demonstrates basic ROS 2 concepts.
    """

    def __init__(self):
        super().__init__('my_robot_node')

        # Create a publisher
        self.publisher_ = self.create_publisher(String, 'robot_status', 10)

        # Create a timer to publish messages periodically
        timer_period = 1.0  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)

        # Declare and get a parameter
        self.declare_parameter('robot_name', 'my_robot')
        self.robot_name = self.get_parameter('robot_name').value

        self.get_logger().info(f'Hello from {self.robot_name}!')

        # Counter for messages
        self.i = 0

    def timer_callback(self):
        """Callback function that publishes robot status messages."""
        msg = String()
        msg.data = f'{self.robot_name} status: operational - message #{self.i}'

        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing: "{msg.data}"')

        self.i += 1


def main(args=None):
    """
    Main function that initializes ROS 2, creates the node, and spins it.
    """
    rclpy.init(args=args)

    my_robot_node = MyRobotNode()

    try:
        rclpy.spin(my_robot_node)
    except KeyboardInterrupt:
        pass
    finally:
        # Clean up
        my_robot_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()