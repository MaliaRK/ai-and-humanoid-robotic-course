---
id: intro
title: Introduction to VLA
sidebar_label: Introduction
description: An introduction to the Vision-Language-Action (VLA) module.
---

# Introduction to the Vision-Language-Action (VLA) Module

## What is the VLA Module?

The Vision-Language-Action (VLA) module is a major step forward in our humanoid robotics course. It builds on what we learned in the first three modules. This module teaches our humanoid robot how to understand and do complex tasks from spoken or written commands, while also seeing and understanding the world around it in real time. This helps the robot work with people in a more natural and flexible way.

## Why is VLA Important?

In the real world, robots need to work in places that are always changing. Old ways of programming robots use strict, pre-written instructions that don't work well when things change. VLA models solve this problem by letting robots:

-   **Learn new tasks**: Instead of being programmed for just a few actions, VLA robots can learn to do many different things.
-   **See and react to the world**: By using cameras, the robot can see what's around it and change its actions as needed.
-   **Talk with people naturally**: You can give the robot commands in plain English, which makes it easier for everyone to use.

## How it Connects to Other Modules

The VLA module brings together everything we've learned so far:

-   **Module 1: ROS2 Nervous System**: We'll use ROS2 to send messages between the VLA system and the robot's body.
-   **Module 2: Digital Twin (Gazebo/Unity)**: We'll test the VLA system in a simulation first to make sure it's safe before using it on a real robot.
-   **Module 3: NVIDIA Isaac Integration**: We'll use NVIDIA's tools, like Isaac Sim, to help us build and train our VLA models faster.

## How it Works

The VLA module works by following these steps:

```mermaid
graph TD;
    A[User Instruction] --> B{The robot thinks about it (LLM)};
    B --> C{The robot decides what to do};
    D[The robot sees the world] --> C;
    C --> E{The robot checks if it's safe};
    E --> F[The robot sends commands to its body];
    F --> G[The robot moves];
```

## Key Parts of the VLA Module

-   **Vision Encoder**: Takes in video from the robot's cameras.
-   **Language Core**: Understands your commands using a Large Language Model (LLM).
-   **Action Policy Engine**: Decides what the robot should do.
-   **Safety Supervisor**: Makes sure the robot's actions are safe.
-   **Execution Layer**: Sends the final commands to the robot's motors.

## References

1.  Brohan, A., et al. (2023). RT-2: Vision-Language-Action Models Transfer Web-Scale Knowledge to Real-World Robots. *arXiv preprint arXiv:2307.15818*.
2.  Chen, Y., et al. (2023). A Survey on Vision-Language-Action Models in Robotics. *arXiv preprint arXiv:2303.07229*.
