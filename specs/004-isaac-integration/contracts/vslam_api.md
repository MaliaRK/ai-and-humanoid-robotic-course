# Visual SLAM API Contract

## Overview
API for Isaac ROS Visual SLAM functionality, providing localization and mapping services for humanoid robots.

## Endpoints

### `/vslam/start`
- **Method**: POST
- **Description**: Initialize Visual SLAM system
- **Request**:
  ```json
  {
    "camera_config": {
      "resolution": [integer, integer],
      "fov": "float",
      "calibration_file": "string"
    },
    "tracking_config": {
      "feature_detector": "string",
      "matcher": "string",
      "max_features": "integer"
    },
    "mapping_config": {
      "map_resolution": "float",
      "map_size": [float, float, float]
    }
  }
  ```
- **Response**:
  ```json
  {
    "status": "string",
    "session_id": "string",
    "timestamp": "datetime"
  }
  ```

### `/vslam/stop`
- **Method**: POST
- **Description**: Stop Visual SLAM system
- **Request**:
  ```json
  {
    "session_id": "string"
  }
  ```
- **Response**:
  ```json
  {
    "status": "string",
    "timestamp": "datetime"
  }
  ```

### `/vslam/pose`
- **Method**: GET
- **Description**: Retrieve current robot pose estimate
- **Query Parameters**:
  - `session_id`: string
- **Response**:
  ```json
  {
    "pose": {
      "position": {"x": "float", "y": "float", "z": "float"},
      "orientation": {"x": "float", "y": "float", "z": "float", "w": "float"}
    },
    "confidence": "float",
    "tracking_status": "string",
    "timestamp": "datetime"
  }
  ```

### `/vslam/map`
- **Method**: GET
- **Description**: Retrieve current map data
- **Query Parameters**:
  - `session_id`: string
  - `format`: string (pointcloud, occupancy_grid, mesh)
- **Response**:
  ```json
  {
    "map_data": "object",
    "map_type": "string",
    "timestamp": "datetime"
  }
  ```

### `/vslam/reset`
- **Method**: POST
- **Description**: Reset SLAM system to initial state
- **Request**:
  ```json
  {
    "session_id": "string",
    "new_origin": {
      "position": {"x": "float", "y": "float", "z": "float"},
      "orientation": {"x": "float", "y": "float", "z": "float", "w": "float"}
    }
  }
  ```
- **Response**:
  ```json
  {
    "status": "string",
    "timestamp": "datetime"
  }
  ```