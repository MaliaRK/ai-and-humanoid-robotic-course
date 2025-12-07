# VLA ROS2 Action Server Contracts

This document specifies the ROS2 Action Server for direct integration with ROS2-enabled robotics systems, enabling goal-based action execution.

## 1. /vla/execute_plan (Action Server)

**Description**: ROS2 Action Server for executing structured VLA plans on the robot.
**Action Name**: `/vla/execute_plan`
**Action Type**: `vla_msgs/ExecutePlan` (example custom message type)

### Goal (Client to Server)

`vla_msgs/ExecutePlanGoal.msg`
```
std_msgs/Header header
string plan_id
string structured_task_json # JSON string representing the structured task plan (e.g., from Language Core)
```

### Result (Server to Client)

`vla_msgs/ExecutePlanResult.msg`
```
std_msgs/Header header
string plan_id
bool success
string message # "Plan executed successfully" or error details
```

### Feedback (Server to Client)

`vla_msgs/ExecutePlanFeedback.msg`
```
std_msgs/Header header
string plan_id
string current_stage # e.g., "PLANNING", "TRAJECTORY_GENERATION", "EXECUTING", "SAFETY_CHECK"
float32 progress_percentage
string estimated_time_remaining # e.g., "10s"
```
