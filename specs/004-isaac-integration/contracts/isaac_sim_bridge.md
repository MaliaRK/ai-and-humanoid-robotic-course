# Isaac Sim ROS Bridge API Contract

## Overview
API for connecting Isaac Sim to ROS 2 systems, enabling data exchange between simulation and real robot control systems.

## Endpoints

### `/isaac_sim/bridge/start`
- **Method**: POST
- **Description**: Initialize the Isaac Sim to ROS 2 bridge connection
- **Request**:
  ```json
  {
    "simulation_config": "string",
    "ros_namespace": "string",
    "connection_params": {
      "host": "string",
      "port": "integer"
    }
  }
  ```
- **Response**:
  ```json
  {
    "status": "string",
    "connection_id": "string",
    "timestamp": "datetime"
  }
  ```

### `/isaac_sim/bridge/stop`
- **Method**: POST
- **Description**: Terminate the Isaac Sim to ROS 2 bridge connection
- **Request**:
  ```json
  {
    "connection_id": "string"
  }
  ```
- **Response**:
  ```json
  {
    "status": "string",
    "timestamp": "datetime"
  }
  ```

### `/isaac_sim/sensors/data`
- **Method**: GET
- **Description**: Retrieve sensor data from Isaac Sim environment
- **Query Parameters**:
  - `sensor_type`: string (camera, lidar, imu, etc.)
  - `robot_name`: string
- **Response**:
  ```json
  {
    "sensor_data": "object",
    "timestamp": "datetime",
    "frame_id": "string"
  }
  ```

### `/isaac_sim/control/robot`
- **Method**: POST
- **Description**: Send control commands to simulated robot
- **Request**:
  ```json
  {
    "robot_name": "string",
    "command": "object",
    "control_type": "string"
  }
  ```
- **Response**:
  ```json
  {
    "status": "string",
    "execution_time": "float"
  }
  ```