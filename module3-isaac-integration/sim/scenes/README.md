# Isaac Sim USD Scenes

This directory contains USD scene files for humanoid robotics simulation.

## Scene Structure

Each scene follows the standard USD format with:

- Root stage containing world elements
- Robot definition with appropriate joints and links
- Environment assets
- Lighting configuration
- Physics properties

## Scene Files

- `humanoid_basic.usd` - Basic humanoid robot in simple environment
- `humanoid_indoor.usd` - Humanoid robot in indoor environment
- `humanoid_outdoor.usd` - Humanoid robot in outdoor environment

## Robot Model Standards

The humanoid robot models follow these standards:

- Proper joint definitions for locomotion
- Realistic physical properties
- Appropriate collision geometries
- Compatible with Isaac ROS perception pipelines