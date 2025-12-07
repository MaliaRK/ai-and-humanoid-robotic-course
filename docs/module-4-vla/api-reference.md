{/* ---
id: api-reference
title: API Reference
sidebar_label: API Reference
description: Provides a comprehensive API reference for the VLA module.
*/}

This document details the API endpoints for the Vision-Language-Action (VLA) module, including REST, WebSocket, and ROS2 interfaces.

## REST API

### POST /vla/act

**Description**: Initiates a VLA action based on natural language instructions and visual context.

**Method**: `POST`
**Endpoint**: `/vla/act`

**Request Body**: `application/json`

```json
{
  "instruction": "string",
  "context_image_rgb": "string",
  "context_image_depth": "string"
}
```

- `instruction` — Natural-language command.
- `context_image_rgb` — Base64 RGB image.
- `context_image_depth` — Base64 Depth image.

**Response Body** (200 OK):

```json
{
  "status": "success",
  "action_id": "string",
  "message": "string"
}
```

**Error Response**:

```json
{
  "status": "error",
  "code": "string",
  "message": "string"
}
```

## WebSocket API

### /vla/live

Real-time VLA status and robot feedback stream.

**Client → Server messages:**

```json
{ "type": "ping" }
```

```json
{ "type": "subscribe_status" }
```

```json
{ "type": "subscribe_feedback" }
```

---

### Server → Client messages:

#### `vla_status`

```json
{
  "type": "vla_status",
  "timestamp": "ISO_8601_string",
  "state": "string",
  "current_action_id": "string",
  "safety_status": "string"
}
```

#### `robot_feedback`

```json
{
  "type": "robot_feedback",
  "timestamp": "ISO_8601_string",
  "joint_states": {
    "joint_name_1": 0.0,
    "joint_name_2": 0.0
  },
  "end_effector_pose": {
    "x": 0.0, "y": 0.0, "z": 0.0,
    "qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0
  },
  "sensor_data": {
    "lidar_ranges": [0.0, 0.0],
    "imu_data": {}
  }
}
```

---

## ROS2 Action Server

### `/vla/execute_plan`

ROS2 Action server for executing structured plans.

---

### Goal (Client → Server)

```
std_msgs/Header header
string plan_id
string structured_task_json
```

---

### Result (Server → Client)

```
std_msgs/Header header
string plan_id
bool success
string message
```

---

### Feedback (Server → Client)

```
std_msgs/Header header
string plan_id
string current_stage
float32 progress_percentage
string estimated_time_remaining
```

## References

1.  Richardson, L., & Amundsen, M. (2013). *RESTful Web APIs*. O'Reilly Media.
2.  Palma, L. (2020). *API Design Patterns*. Manning Publications.
