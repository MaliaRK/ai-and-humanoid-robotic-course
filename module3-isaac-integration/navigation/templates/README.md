# Nav2 Navigation Stack Templates

This directory contains template configuration files for Nav2 navigation stack adapted for humanoid robots.

## Configuration Structure

The navigation configuration follows the standard Nav2 structure with humanoid-specific adaptations:

### Global Planner Configuration
- `global_costmap_params.yaml` - Global costmap for path planning
- `planner_server_params.yaml` - Global planner parameters

### Local Planner Configuration
- `local_costmap_params.yaml` - Local costmap for obstacle avoidance
- `controller_server_params.yaml` - Local planner for trajectory following

### Behavior Trees
- `bt_navigator_params.yaml` - Behavior tree configuration
- `humanoid_navigate_to_pose_w_replanning_and_recovery.xml` - Custom behavior tree for humanoid navigation

### Recovery Behaviors
- `recoveries_params.yaml` - Recovery behavior configuration

## Humanoid-Specific Adaptations

The configurations include parameters specific to humanoid locomotion:

- Adjusted footprint for bipedal robots
- Specialized controller parameters for balance
- Custom costmap layers for humanoid-specific obstacles
- Adapted velocity limits for walking gaits