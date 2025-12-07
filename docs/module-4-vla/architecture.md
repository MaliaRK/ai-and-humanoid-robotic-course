---
id: architecture
title: VLA Architecture
sidebar_label: Architecture
description: Overview of the Vision-Language-Action (VLA) module architecture.
---

## Overview

The Vision-Language-Action (VLA) module is designed to enable humanoid robots to understand natural language instructions, perceive their environment, and execute complex actions. It integrates several core components to achieve this, facilitating a seamless flow from human intent to robot motion.

## Architecture Diagram

The following diagram illustrates the high-level architecture of the VLA module:

```mermaid
graph TD
    A[User Instruction] --> B(Language Core);
    V[RGB + Depth Sensor Data] --> C(Vision Encoder);
    B --> D(Action Policy Engine);
    C --> D;
    D --> E(Safety Supervisor);
    E --> F{Execution Layer};
    F --> G[Robot (Real/Simulated)];
    G --> V;
    G --> H[Feedback Loop];
    H --> F;

    subgraph VLA Module
        B -- Natural Language --> D;
        C -- Visual Embeddings --> D;
        D -- Action Tokens/Trajectory --> E;
        E -- Safe Trajectory --> F;
    end
```

## Data Flow and Core Components

The VLA module operates on a closed-loop principle, continuously taking in environmental data and user commands to inform its actions.

### 1. Vision Encoder

-   **Input**: Raw `RGB_Frame` (color image) and `Depth_Map` (depth information) from the robot's sensors.
-   **Output**: `Vision_Embeddings` (latent space representation of the visual scene, e.g., CLIP/SigLIP features) and `Object_Detections` (bounding boxes, class labels).
-   **Function**: Processes visual data to provide context about the environment, objects, and their spatial relationships.

### 2. Language Core

-   **Input**: `Natural_Language_Instruction` (user command, e.g., "Pick up the red block").
-   **Output**: `Structured_Task_Plan` (a machine-readable JSON plan detailing actions, parameters, and conditions).
-   **Function**: Interprets human language, translates it into actionable plans, and queries visual context if necessary for disambiguation.

### 3. Action Policy Engine

-   **Input**: `Vision_Embeddings` from the Vision Encoder and `Structured_Task_Plan` from the Language Core.
-   **Output**: `Action_Tokens` (discrete representation of robot actions) and `Robot_Trajectory` (a sequence of poses, joint angles, or end-effector commands).
-   **Function**: Generates the specific robot movements and actions required to fulfill the task plan, informed by the current visual state.

### 4. Safety Supervisor

-   **Input**: Proposed `Robot_Trajectory` from the Action Policy Engine and `Current_Robot_State` (real-time joint positions, velocities, sensor data).
-   **Output**: `Safety_Verdict` (True for safe, False for unsafe) and `Rejection_Reason` (details of violation).
-   **Function**: Acts as a critical safeguard, continuously monitoring and evaluating generated actions against predefined safety constraints (speed limits, joint boundaries, collision prediction). Unsafe actions are prevented or modified.

### 5. Execution Layer

-   **Input**: Approved `Robot_Trajectory` from the Safety Supervisor and `Robot_Feedback` (real-time status from the robot).
-   **Output**: `ROS2_Commands` (commands published to ROS2 topics/action servers) or `Isaac_Sim_Bridge_Commands` (API calls to Isaac Sim).
-   **Function**: Translates high-level trajectories into low-level robot commands, manages the interface with both real robots and the Isaac Sim environment, and handles the feedback loop from the robot.

## Real Robot vs. Simulated Environment Loop

The VLA module is designed to operate seamlessly across both real and simulated robotics environments, primarily utilizing the **ROS2 (Robot Operating System 2)** framework for consistent communication.

-   **Isaac Sim Integration**: In a simulated environment (NVIDIA Isaac Sim), the Execution Layer interfaces with the Isaac Sim ROS2 bridge. This bridge allows the VLA module to control simulated robots and receive sensor data as if it were interacting with a physical robot. This enables rapid prototyping, testing, and data generation in a safe, reproducible virtual space.
-   **Real Robot Execution**: For real humanoid robots, the Execution Layer publishes `ROS2_Commands` to the robot's `ros2_control` framework. This framework manages the robot's hardware interfaces and controllers, translating the VLA's high-level trajectories into physical movements.
-   **Feedback Loop**: Both real and simulated robots provide `Robot_Feedback` (e.g., joint states, end-effector poses, sensor data) back to the Execution Layer. This feedback is crucial for closing the control loop, allowing the VLA module to adapt to changes in the environment and verify successful task execution.

## Responsibilities Table

| Component           | Primary Responsibility                                     | Key Inputs                                     | Key Outputs                                       | Error Handling Focus                                          |
| :------------------ | :--------------------------------------------------------- | :--------------------------------------------- | :------------------------------------------------ | :------------------------------------------------------------ |
| **Vision Encoder**  | Visual perception and feature extraction                   | RGB/Depth Sensor Data                          | Vision Embeddings, Object Detections              | Corrupted/unreadable sensor data                              |
| **Language Core**   | Natural language understanding and task planning           | Natural Language Instruction                   | Structured Task Plan                              | Ambiguous/malformed instructions                              |
| **Action Policy Engine** | Action generation and trajectory planning             | Vision Embeddings, Structured Task Plan        | Action Tokens, Robot Trajectory                   | Actions violating safety/physical constraints                 |
| **Safety Supervisor** | Real-time safety monitoring and constraint enforcement     | Robot Trajectory, Current Robot State          | Safety Verdict, Rejection Reason                  | Conflicting commands, imminent collision detection            |
| **Execution Layer** | Robot interface, command execution, feedback management    | Approved Robot Trajectory, Robot Feedback      | ROS2 Commands, Isaac Sim Bridge Commands          | Communication failures, execution discrepancies               |

***

## References

-   [1] OpenAI. (n.d.). *OpenAI Whisper*. Retrieved from [https://openai.com/research/whisper](https://openai.com/research/whisper)
-   [2] Robotics Transformer (RT-1) and Robotics Transformer 2 (RT-2) research papers (specific citations to be added upon detailed content drafting for each component).
-   [3] Google DeepMind. (n.d.). *Gemini Robotics*. Retrieved from [https://deepmind.google/technologies/gemini/robotics/](https://deepmind.google/technologies/gemini/robotics/)

***