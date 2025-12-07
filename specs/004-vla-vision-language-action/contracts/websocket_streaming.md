# VLA WebSocket Streaming Contracts

This document defines the WebSocket interface for real-time streaming of VLA status, robot feedback, and potentially action updates.

## 1. /vla/live

**Description**: Provides a real-time stream of VLA system status and robot feedback.
**Endpoint**: `/vla/live`
**Connection**: WebSocket
**Sent Messages (Client to Server)**:
- `ping`: Keep-alive message.
- `subscribe_status`: Request for VLA status updates.
- `subscribe_feedback`: Request for robot feedback.

**Received Messages (Server to Client)**:
- `vla_status`: `application/json`
```json
{
  "type": "vla_status",
  "timestamp": "ISO_8601_string",
  "state": "string", // e.g., "IDLE", "PROCESSING_INSTRUCTION", "EXECUTING_ACTION", "ERROR"
  "current_action_id": "string", // ID of the currently active action
  "safety_status": "string" // e.g., "SAFE", "WARNING", "VIOLATION"
}
```
- `robot_feedback`: `application/json`
```json
{
  "type": "robot_feedback",
  "timestamp": "ISO_8601_string",
  "joint_states": {
    "joint_name_1": "float", // current joint position
    "joint_name_2": "float"
  },
  "end_effector_pose": {
    "x": "float", "y": "float", "z": "float",
    "qx": "float", "qy": "float", "qz": "float", "qw": "float"
  },
  "sensor_data": {
    "lidar_ranges": "array_of_floats",
    "imu_data": {}
  }
}
```
