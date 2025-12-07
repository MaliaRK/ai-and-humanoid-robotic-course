# Nav2 Integration API Contract

## Overview
API for Nav2 navigation stack integration with Isaac ROS and VSLAM systems, enabling humanoid robot navigation.

## Endpoints

### `/nav2/start`
- **Method**: POST
- **Description**: Initialize Nav2 navigation system
- **Request**:
  ```json
  {
    "config_file": "string",
    "robot_type": "string",
    "map_file": "string"
  }
  ```
- **Response**:
  ```json
  {
    "status": "string",
    "navigation_id": "string",
    "timestamp": "datetime"
  }
  ```

### `/nav2/stop`
- **Method**: POST
- **Description**: Stop Nav2 navigation system
- **Request**:
  ```json
  {
    "navigation_id": "string"
  }
  ```
- **Response**:
  ```json
  {
    "status": "string",
    "timestamp": "datetime"
  }
  ```

### `/nav2/navigate_to_pose`
- **Method**: POST
- **Description**: Navigate to specified pose
- **Request**:
  ```json
  {
    "navigation_id": "string",
    "pose": {
      "position": {"x": "float", "y": "float", "z": "float"},
      "orientation": {"x": "float", "y": "float", "z": "float", "w": "float"}
    },
    "behavior_tree": "string"
  }
  ```
- **Response**:
  ```json
  {
    "status": "string",
    "task_id": "string",
    "timestamp": "datetime"
  }
  ```

### `/nav2/navigate_through_poses`
- **Method**: POST
- **Description**: Navigate through a sequence of poses
- **Request**:
  ```json
  {
    "navigation_id": "string",
    "poses": [
      {
        "position": {"x": "float", "y": "float", "z": "float"},
        "orientation": {"x": "float", "y": "float", "z": "float", "w": "float"}
      }
    ],
    "behavior_tree": "string"
  }
  ```
- **Response**:
  ```json
  {
    "status": "string",
    "task_id": "string",
    "timestamp": "datetime"
  }
  ```

### `/nav2/cancel`
- **Method**: POST
- **Description**: Cancel current navigation task
- **Request**:
  ```json
  {
    "navigation_id": "string",
    "task_id": "string"
  }
  ```
- **Response**:
  ```json
  {
    "status": "string",
    "timestamp": "datetime"
  }
  ```

### `/nav2/status`
- **Method**: GET
- **Description**: Get current navigation status
- **Query Parameters**:
  - `navigation_id`: string
  - `task_id`: string
- **Response**:
  ```json
  {
    "status": "string",
    "current_pose": {
      "position": {"x": "float", "y": "float", "z": "float"},
      "orientation": {"x": "float", "y": "float", "z": "float", "w": "float"}
    },
    "distance_remaining": "float",
    "time_remaining": "float",
    "timestamp": "datetime"
  }
  ```

### `/nav2/update_map`
- **Method**: POST
- **Description**: Update navigation map with new information
- **Request**:
  ```json
  {
    "navigation_id": "string",
    "map_data": "object",
    "update_type": "string"
  }
  ```
- **Response**:
  ```json
  {
    "status": "string",
    "timestamp": "datetime"
  }
  ```