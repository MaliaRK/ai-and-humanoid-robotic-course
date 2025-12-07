# Reinforcement Learning Environment Structure

This directory contains the basic structure for reinforcement learning environments for humanoid locomotion training.

## Environment Components

### Core Environment Files
- `humanoid_env.py` - Base humanoid robot environment
- `humanoid_task_env.py` - Task-specific environment implementations
- `observation_space.py` - Definition of observation spaces
- `action_space.py` - Definition of action spaces

### Reward Functions
- `locomotion_reward.py` - Reward function for basic locomotion
- `balance_reward.py` - Reward function for maintaining balance
- `goal_reaching_reward.py` - Reward function for navigation tasks

### Training Configuration
- `training_params.yaml` - Default training parameters
- `ppo_config.yaml` - PPO algorithm configuration
- `sac_config.yaml` - SAC algorithm configuration

## Simulation Integration

The environments are designed to work with Isaac Sim for:

- Physics simulation
- Sensor data generation
- Visual observation capture
- Realistic humanoid dynamics

## Sim-to-Real Transfer Considerations

The environment structure includes:

- Domain randomization parameters
- Noise models for sensor data
- Dynamics randomization
- Transfer validation tools