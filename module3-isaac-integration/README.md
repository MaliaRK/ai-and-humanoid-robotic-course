# Isaac Integration Module for Humanoid Robot Navigation

This module implements Isaac Sim and Isaac ROS integration for humanoid robot navigation, including Visual SLAM, Navigation2 integration, and safety validation.

## Features

- GPU-accelerated Visual SLAM using Isaac ROS
- Navigation2 integration optimized for humanoid robots
- Social navigation with human awareness
- Balance-constrained path planning and execution
- Isaac Sim scene for humanoid navigation testing
- Comprehensive safety validation framework

## Prerequisites

- Ubuntu 22.04 LTS
- ROS 2 Humble Hawksbill
- Isaac Sim 4.0+
- Isaac ROS packages
- NVIDIA GPU with RTX capability
- CUDA 11.8+

## Installation

1. Install Isaac Sim and Isaac ROS packages following NVIDIA's documentation
2. Clone this repository
3. Install Python dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

## Usage

### Launch Isaac Sim Navigation Scene
```bash
ros2 launch module3_isaac_integration humanoid_navigation_isaac_sim.launch.py
```

### Run Navigation with Isaac ROS Integration
```bash
# Terminal 1: Start Isaac Sim
ros2 launch module3_isaac_integration isaac_sim_scene.launch.py

# Terminal 2: Start Isaac ROS perception pipeline
ros2 launch module3_isaac_integration isaac_ros_perception_pipeline.launch.py

# Terminal 3: Start Nav2 with humanoid parameters
ros2 launch nav2_bringup navigation_launch.py params_file:=./config/nav2_params_humanoid.yaml
```

## Configuration

The module includes several configuration files:

- `config/nav2_params_humanoid.yaml` - Navigation2 parameters optimized for humanoid robots
- `sim/config/humanoid_navigation_scene.yaml` - Isaac Sim scene configuration
- `launch/humanoid_navigation_isaac_sim.launch.py` - Main launch file

## Documentation

Full documentation is available in the `docs/` directory:
- Chapter 4 covers Isaac Sim scene setup
- VSLAM-Nav2 integration guide
- Biped controllers documentation
- Navigation performance and safety validation

## Architecture

The module implements a layered architecture:
1. Isaac Sim provides photorealistic simulation
2. Isaac ROS components provide GPU-accelerated perception
3. Navigation2 provides path planning and execution
4. Safety layer ensures safe operation in human environments

## Validation

The system has been validated with:
- Static and dynamic obstacle avoidance
- Social navigation scenarios
- Balance-aware navigation
- Performance benchmarks
- Safety validation tests

## License

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.