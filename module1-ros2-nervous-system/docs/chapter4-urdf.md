---
id: chapter4-urdf
title: Chapter 4 - URDF & Robot Modeling
sidebar_label: Chapter 4 - URDF & Robot Modeling
description: Learning how to model robots using Unified Robot Description Format (URDF) in ROS 2.
---

# Chapter 4 - URDF & Robot Modeling

## Introduction

Unified Robot Description Format (URDF) is an XML-based format used in ROS to describe robot models. With URDF, you can define the physical and visual properties of a robot, including its links, joints, and how they connect. This is essential for robot simulation, visualization, and kinematic analysis.

## What is URDF?

URDF (Unified Robot Description Format) is a robot modeling format that allows you to define:
- **Links**: Rigid bodies of the robot (like arms, base, wheels)
- **Joints**: Connections between links (like hinges, sliders)
- **Visual properties**: How the robot looks in simulation
- **Collision properties**: How the robot interacts with its environment
- **Inertial properties**: Mass, center of mass, and inertia for physics simulation

## Basic URDF Structure

A basic URDF file has the following structure:

```xml
<?xml version="1.0"?>
<robot name="my_robot">
  <!-- Define links -->
  <link name="base_link">
    <visual>
      <geometry>
        <box size="0.5 0.5 0.2"/>
      </geometry>
    </visual>
    <collision>
      <geometry>
        <box size="0.5 0.5 0.2"/>
      </geometry>
    </collision>
    <inertial>
      <mass value="1.0"/>
      <inertia ixx="0.1" ixy="0.0" ixz="0.0" iyy="0.1" iyz="0.0" izz="0.1"/>
    </inertial>
  </link>

  <!-- Define joints -->
  <joint name="base_to_wheel" type="continuous">
    <parent link="base_link"/>
    <child link="wheel_link"/>
    <origin xyz="0.2 0 0" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
  </joint>

  <link name="wheel_link">
    <visual>
      <geometry>
        <cylinder radius="0.1" length="0.05"/>
      </geometry>
    </visual>
  </link>
</robot>
```

### Links

Links represent rigid bodies of the robot. Each link has:
- **Visual**: How the link appears in visualization
- **Collision**: How the link interacts with other objects in collision detection
- **Inertial**: Physical properties for dynamics simulation

### Joints

Joints connect links together and define how they can move relative to each other. Common joint types:
- **fixed**: No movement (rigid connection)
- **revolute**: Rotational movement around an axis
- **continuous**: Like revolute but unlimited rotation
- **prismatic**: Linear sliding movement
- **floating**: 6 degrees of freedom

## URDF for Humanoid Robots

Humanoid robots have a specific structure with a body, head, arms, and legs. Here's a simplified humanoid structure:

```
base_link (torso)
├── head_link
├── left_upper_arm
│   └── left_lower_arm
│       └── left_hand
├── right_upper_arm
│   └── right_lower_arm
│       └── right_hand
├── left_upper_leg
│   └── left_lower_leg
│       └── left_foot
└── right_upper_leg
    └── right_lower_leg
        └── right_foot
```

## Creating Your First URDF

Let's create a simple mobile robot base:

```xml
<?xml version="1.0"?>
<robot name="simple_robot">
  <!-- Robot base -->
  <link name="base_link">
    <visual>
      <geometry>
        <box size="0.5 0.3 0.1"/>
      </geometry>
      <material name="blue">
        <color rgba="0 0 1 1"/>
      </material>
    </visual>
    <collision>
      <geometry>
        <box size="0.5 0.3 0.1"/>
      </geometry>
    </collision>
    <inertial>
      <mass value="1.0"/>
      <inertia ixx="0.01" ixy="0.0" ixz="0.0" iyy="0.01" iyz="0.0" izz="0.01"/>
    </inertial>
  </link>

  <!-- Left wheel -->
  <joint name="left_wheel_joint" type="continuous">
    <parent link="base_link"/>
    <child link="left_wheel"/>
    <origin xyz="0 0.2 -0.05" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
  </joint>

  <link name="left_wheel">
    <visual>
      <geometry>
        <cylinder radius="0.1" length="0.05"/>
      </geometry>
      <material name="black">
        <color rgba="0 0 0 1"/>
      </material>
    </visual>
    <collision>
      <geometry>
        <cylinder radius="0.1" length="0.05"/>
      </geometry>
    </collision>
    <inertial>
      <mass value="0.2"/>
      <inertia ixx="0.001" ixy="0.0" ixz="0.0" iyy="0.001" iyz="0.0" izz="0.002"/>
    </inertial>
  </link>

  <!-- Right wheel -->
  <joint name="right_wheel_joint" type="continuous">
    <parent link="base_link"/>
    <child link="right_wheel"/>
    <origin xyz="0 -0.2 -0.05" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
  </joint>

  <link name="right_wheel">
    <visual>
      <geometry>
        <cylinder radius="0.1" length="0.05"/>
      </geometry>
      <material name="black">
        <color rgba="0 0 0 1"/>
      </material>
    </visual>
    <collision>
      <geometry>
        <cylinder radius="0.1" length="0.05"/>
      </geometry>
    </collision>
    <inertial>
      <mass value="0.2"/>
      <inertia ixx="0.001" ixy="0.0" ixz="0.0" iyy="0.001" iyz="0.0" izz="0.002"/>
    </inertial>
  </link>
</robot>
```

## Visualizing URDF in RViz2

Once you have created your URDF file, you can visualize it in RViz2. Here's how to do it with the simple humanoid model we created:

### Launching RViz2 with URDF

1. First, make sure your URDF is loaded into a robot_state_publisher node. Create a launch file or run the following commands:

```bash
# Terminal 1: Start the robot_state_publisher with your URDF
ros2 run robot_state_publisher robot_state_publisher --ros-args -p robot_description:=$(cat /path/to/ch4_humanoid.urdf)

# Alternative: Use xacro if your URDF is in xacro format
ros2 run xacro xacro /path/to/ch4_humanoid.urdf.xacro | ros2 run robot_state_publisher robot_state_publisher --ros-args -p robot_description:=$(cat /path/to/ch4_humanoid.urdf)
```

2. In another terminal, launch RViz2:

```bash
ros2 run rviz2 rviz2
```

3. In RViz2, add a RobotModel display:
   - Click "Add" in the bottom left
   - Go to "RobotModel"
   - Select it and click "OK"

4. Set the "Robot Description" field in the RobotModel display to "robot_description" (or whatever parameter name you used)

### Using the Provided Example

The simple humanoid URDF file is located at:
`module1-ros2-nervous-system/examples/ch4_humanoid.urdf`

To visualize it:
1. Make sure you have the `robot_state_publisher` and `rviz2` packages installed
2. Launch the robot state publisher with the URDF file
3. Launch RViz2 and add the RobotModel display

## Best Practices

- Use meaningful names for links and joints
- Keep the URDF hierarchy simple and logical
- Include both visual and collision properties
- Use appropriate inertial values for physics simulation
- Test your URDF in RViz2 and Gazebo simulation
- Organize complex URDFs using xacro macros

## Summary

In this chapter, you learned:
- What URDF is and why it's important for robotics
- The basic structure of URDF files
- How to define links and joints
- How to visualize URDF models in RViz2
- Best practices for creating robot models

## References

> (Lynch & Park, 2017). *Modern Robotics: Mechanics, Planning, and Control*. Cambridge University Press.
> (ROS Wiki). *URDF/XML Format Documentation*. Robot Operating System.
> (Corke, 2017). *Robotics, Vision and Control: Fundamental Algorithms in MATLAB*. Springer.