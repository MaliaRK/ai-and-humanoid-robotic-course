# Simulation API Contracts: Module 2 - Digital Twin (Gazebo & Unity)

This document outlines the API endpoints for the simulation components of the Digital Twin system, detailing their functionality, request formats, and response schemas.

## 1. POST /sim/robot/spawn

**Description**: Spawns a robot model into the simulation environment.
**Method**: `POST`
**Endpoint**: `/sim/robot/spawn`
**Request Body**: `application/json`
```json
{
  "robot_name": "string",      // Name of the robot to spawn
  "robot_model": "string",     // URDF/SDF model file path
  "initial_position": {        // Initial pose in the simulation
    "x": "number",             // X coordinate in meters
    "y": "number",             // Y coordinate in meters
    "z": "number",             // Z coordinate in meters
    "roll": "number",          // Roll angle in radians
    "pitch": "number",         // Pitch angle in radians
    "yaw": "number"            // Yaw angle in radians
  },
  "simulation_engine": "string" // Target engine ("gazebo" or "unity")
}
```
**Response Body**: `application/json` (HTTP 200 OK)
```json
{
  "status": "success",
  "robot_id": "string",        // Unique identifier for the spawned robot
  "message": "string"          // Confirmation message
}
```
**Error Response**: `application/json` (HTTP 4xx/5xx)
```json
{
  "status": "error",
  "code": "string",            // Error code (e.g., "MODEL_NOT_FOUND", "INVALID_POSE")
  "message": "string"          // Detailed error message
}
```

## 2. PUT /sim/robot/{robot_id}/pose

**Description**: Updates the pose of a robot in the simulation.
**Method**: `PUT`
**Endpoint**: `/sim/robot/{robot_id}/pose`
**Path Parameters**:
- `robot_id`: Unique identifier of the robot
**Request Body**: `application/json`
```json
{
  "target_pose": {             // Target pose for the robot
    "x": "number",             // X coordinate in meters
    "y": "number",             // Y coordinate in meters
    "z": "number",             // Z coordinate in meters
    "roll": "number",          // Roll angle in radians
    "pitch": "number",         // Pitch angle in radians
    "yaw": "number"            // Yaw angle in radians
  },
  "interpolation_time": "number" // Time to reach target pose in seconds
}
```
**Response Body**: `application/json` (HTTP 200 OK)
```json
{
  "status": "success",
  "robot_id": "string",        // Robot ID for confirmation
  "message": "string"          // Confirmation message
}
```

## 3. GET /sim/sensor/{sensor_type}/data

**Description**: Retrieves sensor data from the simulation environment.
**Method**: `GET`
**Endpoint**: `/sim/sensor/{sensor_type}/data`
**Path Parameters**:
- `sensor_type`: Type of sensor ("lidar", "camera", "imu", "depth_camera")
**Query Parameters**:
- `robot_id`: ID of the robot carrying the sensor (optional)
- `timestamp`: Specific timestamp for data retrieval (optional)
**Response Body**: `application/json` (HTTP 200 OK)
```json
{
  "status": "success",
  "sensor_data": {},           // Sensor-specific data format
  "timestamp": "string",       // ISO 8601 timestamp
  "frame_id": "string"         // Coordinate frame identifier
}
```
**Example Response for LiDAR**:
```json
{
  "status": "success",
  "sensor_data": {
    "ranges": [1.2, 1.5, 1.8, 2.1, 2.4], // Distances in meters
    "intensities": [0.8, 0.7, 0.6, 0.5, 0.4], // Intensity values
    "angle_min": -1.57,        // Minimum angle in radians
    "angle_max": 1.57,         // Maximum angle in radians
    "angle_increment": 0.0174  // Angle increment in radians
  },
  "timestamp": "2025-12-07T10:00:00Z",
  "frame_id": "lidar_link"
}
```

## 4. POST /sim/environment/load

**Description**: Loads a simulation environment/world.
**Method**: `POST`
**Endpoint**: `/sim/environment/load`
**Request Body**: `application/json`
```json
{
  "world_name": "string",      // Name of the world file to load
  "world_file_path": "string", // Path to the world file
  "physics_config": {          // Physics engine configuration
    "gravity_x": "number",     // Gravity in X direction
    "gravity_y": "number",     // Gravity in Y direction
    "gravity_z": -9.81,        // Gravity in Z direction (m/s^2)
    "real_time_factor": "number" // Real-time update rate
  },
  "simulation_engine": "string" // Target engine ("gazebo" or "unity")
}
```
**Response Body**: `application/json` (HTTP 200 OK)
```json
{
  "status": "success",
  "world_id": "string",        // Unique identifier for the loaded world
  "message": "string"          // Confirmation message
}
```

## 5. GET /sim/validation/compare

**Description**: Compares simulation results with real-world data for validation.
**Method**: `GET`
**Endpoint**: `/sim/validation/compare`
**Query Parameters**:
- `simulation_id`: ID of the simulation run
- `real_data_id`: ID of the real-world data to compare against
- `metric_types`: Comma-separated list of metrics to calculate (e.g., "rmse,positional_error,orientation_error")
**Response Body**: `application/json` (HTTP 200 OK)
```json
{
  "status": "success",
  "validation_results": {
    "sim_to_real_gap_metrics": {
      "positional_accuracy_rmse": "number",    // RMSE of positional accuracy in meters
      "orientation_accuracy_rmse": "number",   // RMSE of orientation accuracy in radians
      "timing_consistency": "number",          // Consistency of timing between sim and real
      "behavior_similarity_score": "number"    // Similarity score of behaviors (0-1 scale)
    },
    "confidence_interval": {
      "lower_bound": "number",                 // Lower bound of confidence interval
      "upper_bound": "number"                  // Upper bound of confidence interval
    }
  },
  "recommendations": ["string"]               // Recommendations for improving sim-to-real transfer
}
```