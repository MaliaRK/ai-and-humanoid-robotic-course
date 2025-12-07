---
id: chapter3-rclpy
title: Chapter 3 - Programming ROS 2 with Python (rclpy)
sidebar_label: Chapter 3 - Programming with rclpy
description: Learning how to program ROS 2 nodes using Python and the rclpy client library.
---

# Chapter 3 - Programming ROS 2 with Python (rclpy)

## Introduction

In this chapter, we'll explore how to program ROS 2 nodes using Python, which is one of the most popular languages for robotics development. The `rclpy` package provides a Python client library for ROS 2, making it easy to create nodes, publish and subscribe to topics, provide and use services, and work with actions.

## What is rclpy?

`rclpy` is the Python ROS Client Library. It provides a Python API for ROS 2 concepts like:
- Nodes
- Publishers and Subscribers
- Services and Actions
- Parameters
- Timers
- Logging

## Creating Your First Python Node

Let's start by creating a simple ROS 2 node in Python. This will be the foundation for all your future ROS 2 programs.

```python
import rclpy
from rclpy.node import Node

class MyFirstNode(Node):
    def __init__(self):
        super().__init__('my_first_node')
        self.get_logger().info('Hello from my first ROS 2 Python node!')

def main(args=None):
    rclpy.init(args=args)
    node = MyFirstNode()

    # Keep the node running until interrupted
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### Breaking Down the Code

1. **Import statements**: We import `rclpy` and the `Node` class from `rclpy.node`
2. **Node class**: We create a class that inherits from `Node`
3. **Initialization**: In `__init__`, we call the parent's `__init__` with a node name
4. **Logging**: We use `self.get_logger().info()` to print messages
5. **Main function**: This is the entry point where we initialize ROS, create our node, and start spinning

## Creating a ROS 2 Package

A ROS 2 package is the basic unit of organization for ROS 2 code. Here's the typical structure:

```
my_robot_package/
├── CMakeLists.txt
├── package.xml
├── setup.py
├── setup.cfg
├── resource/
│   └── my_robot_package
├── my_robot_package/
│   ├── __init__.py
│   └── my_node.py
└── test/
    └── test_copyright.py
    └── test_flake8.py
    └── test_pep257.py
```

### package.xml

The `package.xml` file contains metadata about your package:

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>my_robot_package</name>
  <version>0.0.0</version>
  <description>Package for my robot functionality</description>
  <maintainer email="user@example.com">User Name</maintainer>
  <license>Apache-2.0</license>

  <depend>rclpy</depend>
  <depend>std_msgs</depend>

  <test_depend>ament_copyright</test_depend>
  <test_depend>ament_flake8</test_depend>
  <test_depend>ament_pep257</test_depend>
  <test_depend>python3-pytest</test_depend>

  <export>
    <build_type>ament_python</build_type>
  </export>
</package>
```

### setup.py

The `setup.py` file defines how to build your Python package:

```python
from setuptools import setup
from glob import glob
import os

package_name = 'my_robot_package'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='User Name',
    maintainer_email='user@example.com',
    description='Package for my robot functionality',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'my_node = my_robot_package.my_node:main',
        ],
    },
)
```

## Working with Parameters

ROS 2 allows nodes to have parameters that can be configured at runtime:

```python
import rclpy
from rclpy.node import Node

class ParameterNode(Node):
    def __init__(self):
        super().__init__('parameter_node')

        # Declare parameters with default values
        self.declare_parameter('robot_name', 'turtlebot')
        self.declare_parameter('max_speed', 1.0)

        # Get parameter values
        robot_name = self.get_parameter('robot_name').value
        max_speed = self.get_parameter('max_speed').value

        self.get_logger().info(f'Robot: {robot_name}, Max Speed: {max_speed}')

def main(args=None):
    rclpy.init(args=args)
    node = ParameterNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## Best Practices

- Always call `rclpy.init()` before creating nodes
- Use try/finally blocks to ensure proper cleanup
- Always call `node.destroy_node()` and `rclpy.shutdown()` for clean shutdown
- Use meaningful node and topic names
- Include logging in your nodes for debugging
- Follow Python PEP 8 style guidelines

## Summary

In this chapter, you learned:
- How to create basic ROS 2 nodes in Python
- The structure of a ROS 2 package
- How to work with parameters
- Best practices for ROS 2 Python development

## References

> (Sharma, 2023). *ROS 2 for Beginners: A Practical Introduction*. Robot Operating System.
> (Quigley et al., 2009). *Programming Robots with ROS: A Practical Introduction to the Robot Operating System*. O'Reilly Media.
> (ROS Wiki). *rclpy Documentation*. Robot Operating System.