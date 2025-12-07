# Quickstart Guide: Module 2: The Digital Twin (Gazebo & Unity)

## Overview

This quickstart guide provides a rapid introduction to the Digital Twin concepts using Gazebo and Unity for humanoid robotics simulation. By the end of this guide, you'll have a basic understanding of how to set up simulation environments and create a simple digital twin workflow.

## Prerequisites

- Ubuntu 22.04 LTS (recommended)
- ROS 2 Humble Hawksbill
- Gazebo Fortress or newer
- Unity LTS (2022.3.x or newer) with Robotics packages
- Python 3.10+
- Git

## Installation Steps

### 1. Install ROS 2 Humble
```bash
# Add ROS 2 repository
sudo apt update && sudo apt install curl gnupg lsb-release
curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros-apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(source /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
sudo apt install ros-humble-desktop
sudo apt install ros-humble-gazebo-ros-pkgs ros-humble-gazebo-ros2-control
```

### 2. Install Gazebo
```bash
sudo apt install gz-fortress
# Or use the ROS 2 bundled version
```

### 3. Set Up Unity Environment
```bash
# Download Unity Hub and install LTS version
# Install Unity Robotics packages through Package Manager:
# - Unity Robotics Hub
# - Unity Machine Learning Agents (ML-Agents)
```

## Basic Digital Twin Workflow

### 1. Create a Simple Robot Model
Create a basic URDF model of a humanoid robot with essential joints and links. This model will be used in both Gazebo and Unity.

### 2. Set Up Gazebo Environment
1. Launch Gazebo with an empty world
2. Spawn your robot model
3. Configure physics properties (gravity, damping, etc.)

### 3. Set Up Unity Visualization
1. Import your robot model into Unity
2. Configure the Unity Robotics Hub for ROS communication
3. Set up rendering pipelines and materials

### 4. Connect with ROS Bridge
1. Use `gazebo_ros_pkgs` to bridge Gazebo and ROS 2
2. Use Unity Robotics Hub to connect Unity and ROS 2
3. Establish communication between all components

## Running Your First Simulation

1. Launch the Gazebo simulation with your robot:
```bash
ros2 launch your_robot_gazebo robot_world.launch.py
```

2. In another terminal, launch the Unity visualization:
```bash
# Start Unity project with ROS connection
```

3. Verify the connection and synchronize the simulation states

## Key Concepts Covered

- **Digital Twin Architecture**: Understanding the relationship between physical systems and their digital counterparts
- **Simulation Fidelity**: Balancing computational efficiency with realism
- **Physics Simulation**: Accurate modeling of real-world forces and interactions
- **Sensor Simulation**: Replicating real sensor behaviors in virtual environments
- **Sim-to-Real Transfer**: Techniques for minimizing the gap between simulation and reality

## Next Steps

1. Complete the full 5-chapter module to gain comprehensive understanding
2. Experiment with different physics parameters to see their effects
3. Add sensor simulation to your digital twin
4. Implement validation techniques to measure sim-to-real transfer effectiveness
5. Explore advanced topics like domain randomization and system identification

## Troubleshooting

- **Simulation Instability**: Check physics parameters (time step, solver settings)
- **Communication Issues**: Verify ROS network configuration and topic mappings
- **Performance Problems**: Adjust rendering quality and simulation complexity
- **Model Errors**: Validate URDF/SDF files for proper joint limits and masses