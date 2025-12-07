---
id: "0001"
title: "Module 1 ROS 2 Nervous System Specification"
stage: "spec"
date: "2025-12-05"
surface: "agent"
model: "claude-sonnet-4-5-20250929"
feature: "001-ros2-nervous-system"
branch: "001-ros2-nervous-system"
user: "user"
command: "/sp.specify"
labels: ["spec"]
links:
  spec: "/home/maliaraees/ai-and-humanoid-robotics-course/specs/001-ros2-nervous-system/spec.md"
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - /home/maliaraees/ai-and-humanoid-robotics-course/specs/001-ros2-nervous-system/spec.md
  - /home/maliaraees/ai-and-humanoid-robotics-course/specs/001-ros2-nervous-system/checklists/requirements.md
tests:
- N/A
---

## Prompt

```text
Book: Physical AI & Humanoid Robotics
Scope: This specification defines the requirements for all content inside Module 1.

1. Module Purpose

Module 1 teaches students how the robotic nervous system works using ROS 2.
Students must understand how signals flow from AI → control nodes → actuators → humanoid body using professional-grade ROS 2 tools.

2. Learning Outcomes (Required)

By the end of this module, the student must be able to:

Create and run ROS 2 nodes in Python (rclpy).

Publish and subscribe to topics.

Use services, parameters, and actions.

Build a humanoid robot description using URDF & XACRO.

Visualize robot transforms using RViz + TF2.

Send movement commands to a humanoid using geometry_msgs/Twist.

Implement basic robot safety controls (rate limiting, joint limits, safe velocity).

Launch multi-node systems using ROS 2 launch files.

These outcomes are mandatory and must appear in the chapter plans.

3. Module Content Requirements

The module must contain 7 chapters:

Chapter 1 — Introduction to ROS 2

What is ROS 2?

Why humanoid robots require middleware

Nodes, topics, services, actions

QoS and reliability basics

Simple diagram of humanoid data flow

Chapter 2 — ROS 2 Nodes (rclpy)

Write, run, and explain a Python node

Example: “Heartbeat Node”

Include Docusaurus-friendly diagram

Chapter 3 — Topics & Messaging

Publisher/subscriber patterns

Example: sending humanoid joint commands

geometry_msgs, sensor_msgs, std_msgs

Chapter 4 — Services & Actions

When to use services vs actions

Example: “Stand Up” action server for humanoid

Chapter 5 — URDF + TF2 + Kinematics

Robot structure (links, joints, inertia)

Writing a humanoid URDF/XACRO

TF2 frames for head, torso, legs, arms

RViz visualization screenshots (description only)

Chapter 6 — Movement Control

Twist commands

PID basics

Safety rules (speed limits, braking, joint limits)

Mini assignment: Move humanoid forward safely

Chapter 7 — Launch Files & Integration

Multi-node launch files

Structured project layout

Humanoid bring-up system

Final “walk cycle” simulation

4. Technical Requirements

All Module 1 content must strictly follow:

ROS 2 Humble or newer

rclpy as the primary development API

All Python code must follow PEP8

URDF must use:

Accurate joint limits

Realistic inertia values

Valid XACRO macros

RViz examples must match actual TF2 tree structure

Every code example must include:

Imports

Node creation

Executor/spin

Shutdown

5. Citation Standards

Every chapter must include:

Minimum 2 APA-format citations

At least 1 official ROS source (docs or REP)

At least 1 peer-reviewed robotics paper

No uncited claims about ROS behavior, humanoid kinematics, or real-world robotics.

6. Diagrams & Visualizations

Each chapter must include at least one diagram, such as:

ROS node graph

Topic flow diagram

TF2 frame tree

Humanoid URDF hierarchy

Data pipeline from AI → ROS → Actuators

All diagrams must be:

Simple

Clean

Docusaurus compatible

Labeled consistently with the Constitution

7. Assignments & Exercises (Required)

Each chapter must end with:

Theory Question

Code Task

Simulation/Visualization Task

Example tasks:

Write a ROS node that prints joint angles

Build a URDF for a 2-link humanoid arm

Visualize TF tree in RViz

Create a launch file that starts 3 nodes

8. Acceptance Criteria (Speckitplus-Style)

Module 1 is considered complete only if:

✔ All 7 chapters exist
✔ All learning outcomes are covered
✔ All code examples run correctly in ROS 2 Humble
✔ All diagrams follow naming + clarity standards
✔ All content respects the Constitution
✔ Each chapter contains citations
✔ Safety constraints are explicitly mentioned
✔ Final integration chapter demonstrates multi-node humanoid control

If any requirement is unmet → Module 1 must return to planning stage.
```

## Response snapshot

Updated the specification for "Module 1: Robotic Nervous System (ROS 2)" with user scenarios, functional requirements, key entities, and measurable success criteria. Added an "Assumptions" section to explicitly state dependencies. Created a specification quality checklist and validated the spec against it, making necessary adjustments to align with the guidelines.

## Outcome

- ✅ Impact: Specification for Module 1 created and validated.
- 🧪 Tests: N/A
- 📁 Files: /home/maliaraees/ai-and-humanoid-robotics-course/specs/001-ros2-nervous-system/spec.md, /home/maliaraees/ai-and-humanoid-robotics-course/specs/001-ros2-nervous-system/checklists/requirements.md
- 🔁 Next prompts: /sp.plan
- 🧠 Reflection: The initial spec had some implementation details and missing assumptions, which were addressed by rephrasing and adding a dedicated section. The validation process helped ensure adherence to spec guidelines.

## Evaluation notes (flywheel)

- Failure modes observed: `create-phr.sh` script failed due to incorrect feature name format.
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
