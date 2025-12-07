---
id: chapter2-nodes-topics-services
title: Chapter 2 - ROS 2 Nodes, Topics & Services
sidebar_label: Chapter 2 - Nodes, Topics & Services
description: Understanding the core communication patterns in ROS 2 - Nodes, Topics, Services, and Actions.
---

# Chapter 2 - ROS 2 Nodes, Topics & Services

## Introduction

In the previous chapter, we learned about the foundations of ROS 2. Now, we'll dive deeper into the core communication patterns that make ROS 2 powerful for robotics applications. Understanding Nodes, Topics, Services, and Actions is crucial for building distributed robotic systems.

## What is a Node?

A **Node** is the fundamental unit of computation in ROS 2. Think of it as a process that performs a specific task. In a humanoid robot, you might have nodes for:
- Vision processing
- Path planning
- Motor control
- Sensor fusion

### Creating a Node in Python (rclpy)

Here's a minimal example of creating a node in Python:

```python
import rclpy
from rclpy.node import Node

class MinimalNode(Node):
    def __init__(self):
        super().__init__('minimal_node')
        self.get_logger().info('Hello from my minimal node!')

def main(args=None):
    rclpy.init(args=args)
    node = MinimalNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## Topics - Publisher & Subscriber Pattern

Topics enable asynchronous communication between nodes using a publish-subscribe model. This is perfect for continuous data streams like sensor readings, camera feeds, or robot pose information.

### Publishers and Subscribers

- **Publisher**: Sends messages to a topic
- **Subscriber**: Receives messages from a topic

The communication is decoupled - publishers don't need to know who subscribes, and subscribers don't need to know who publishes.

### Minimal Publisher/Subscriber Example

Here's a complete example of a publisher and subscriber working together. This can be found in `module1-ros2-nervous-system/examples/ch2_pubsub.py`:

```python
#!/usr/bin/env python3
"""
Minimal Publisher/Subscriber Example for Chapter 2

This example demonstrates the basic Publisher/Subscriber pattern in ROS 2.
It includes both a publisher that sends messages and a subscriber that receives them.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MinimalPublisher(Node):
    """
    A minimal publisher node that sends "Hello World" messages.
    """

    def __init__(self):
        super().__init__('minimal_publisher')
        self.publisher_ = self.create_publisher(String, 'topic', 10)
        timer_period = 0.5  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0

    def timer_callback(self):
        """Callback function that publishes a message every timer tick."""
        msg = String()
        msg.data = f'Hello World: {self.i}'
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing: "{msg.data}"')
        self.i += 1


class MinimalSubscriber(Node):
    """
    A minimal subscriber node that listens to messages.
    """

    def __init__(self):
        super().__init__('minimal_subscriber')
        self.subscription = self.create_subscription(
            String,
            'topic',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning

    def listener_callback(self, msg):
        """Callback function that processes received messages."""
        self.get_logger().info(f'I heard: "{msg.data}"')


def main(args=None):
    rclpy.init(args=args)

    minimal_publisher = MinimalPublisher()
    minimal_subscriber = MinimalSubscriber()

    # Use MultiThreadedExecutor to run both nodes simultaneously
    from rclpy.executors import MultiThreadedExecutor
    executor = MultiThreadedExecutor()
    executor.add_node(minimal_publisher)
    executor.add_node(minimal_subscriber)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        # Shutdown and cleanup
        minimal_publisher.destroy_node()
        minimal_subscriber.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
```

## Services - Request & Response Pattern

Services provide synchronous communication between nodes using a request-response model. This is ideal for operations that require a specific response, like setting parameters, triggering actions, or getting robot status.

### Client-Server Model

- **Service Server**: Provides a service and responds to requests
- **Service Client**: Sends requests to a service and waits for responses

### Example: Robot Arm Control Service

```python
# Service definition (in srv/MoveArm.srv):
# float64 x
# float64 y
# float64 z
# ---
# bool success
# string message
```

```python
# Service Server
import rclpy
from rclpy.node import Node
from example_interfaces.srv import SetBool  # Using example service for demonstration

class MinimalService(Node):
    def __init__(self):
        super().__init__('minimal_service')
        self.srv = self.create_service(
            SetBool,
            'enable_robot',
            self.enable_robot_callback)

    def enable_robot_callback(self, request, response):
        response.success = True
        if request.data:
            response.message = 'Robot enabled'
            self.get_logger().info('Robot enabled')
        else:
            response.message = 'Robot disabled'
            self.get_logger().info('Robot disabled')
        return response

def main(args=None):
    rclpy.init(args=args)
    minimal_service = MinimalService()
    rclpy.spin(minimal_service)
    minimal_service.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## Actions - Long-Running Tasks with Feedback

Actions are designed for long-running tasks that require:
- **Goal**: What to do
- **Feedback**: Progress updates during execution
- **Result**: Final outcome when complete

This is perfect for tasks like navigation, manipulation, or any operation that takes time and needs monitoring.

### Action Client and Server

- **Action Client**: Sends goals, receives feedback and results
- **Action Server**: Receives goals, sends feedback, returns results

## Summary

- **Nodes** are the basic computational units in ROS 2
- **Topics** enable asynchronous pub/sub communication for continuous data
- **Services** provide synchronous request/response communication
- **Actions** handle long-running tasks with feedback

These communication patterns form the backbone of ROS 2 and enable building complex, distributed robotic systems.

## References

> (Sharma, 2023). *ROS 2 for Beginners: A Practical Introduction*. Robot Operating System.
> (Quigley et al., 2009). *Programming Robots with ROS: A Practical Introduction to the Robot Operating System*. O'Reilly Media.
> (ROS Wiki). *ROS 2 Concepts Documentation*. Robot Operating System.
