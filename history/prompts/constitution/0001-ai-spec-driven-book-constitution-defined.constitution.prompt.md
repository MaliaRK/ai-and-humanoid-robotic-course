---
id: "0001"
title: "AI & Humanoid Robotics Book Constitution Defined"
stage: "constitution"
date: "2025-12-05"
surface: "agent"
model: "claude-sonnet-4-5-20250929"
feature: "none"
branch: "master"
user: "user"
command: "/sp.constitution"
labels: ["constitution"]
links:
  spec: "null"
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - .specify/memory/constitution.md
tests:
- N/A
---

## Prompt

project: AI/Spec-Driven Book - Physical AI, Humanoid Robotics, and Agentic Engineering
platform: Docusaurus documentationsite deployed to github pages
Tooling: Spec-kit Plus + Claude Code

Module 1 Constitution: Robotic Nervous System (ROS 2)
1. Writing & Documentation Standards

All ROS 2 explanations must follow Flesch-Kincaid Grade 8–10 readability.

Use consistent terminology:

Node, Topic, Service, Parameter, Launch File

URDF, Joint, Link, Transform (TF2)

Each concept must include:

A definition

A real-world humanoid example

A code snippet using rclpy

A diagram (Docusaurus-friendly)

2. Technical Standards

ROS 2 version must be Humble or later.

Code must follow:

PEP8

ROS 2 Python conventions

Correct message types (e.g., geometry_msgs/Twist, sensor_msgs/Imu)

URDF examples must be mechanically accurate (no impossible joints).

3. Citation Standards

Use APA 7 for:

ROS documentation

Robotics textbooks

Peer-reviewed robot control papers

Minimum 2 peer-reviewed citations per chapter.

4. Safety Standards

Robot control examples must include:

Safety stop

Rate limiting

Speed caps

Joint limit enforcement

Module 2 Constitution: Digital Twin (Gazebo & Unity)
1. Writing & Clarity Rules

Concepts must be explained with:

Physics analogies

Simple diagrams

Clear step-by-step setup instructions

All simulation examples must be reproducible in:

Gazebo Fortress/Ignition

Unity HDRP or URP

2. Technical Standards

Physics parameters must be accurate:

mass, inertia, friction, restitution

Sensor simulation accuracy:

LiDAR (range, resolution)

IMU (noise models)

Depth cams (FOV, clipping planes)

World building must include:

lighting

materials

collision shapes

3. Citation Standards

Cite Gazebo, Unity, and physics references using APA7.

Minimum 1 simulation paper + 1 physics source per chapter.

4. Safety & Ethics

No simulation examples involving unsafe or unethical robot behavior.

No humanoid actions that mimic harmful real-world behavior.

Module 3 Constitution: AI-Robot Brain (NVIDIA Isaac)
1. Writing & Documentation

Must simplify complex AI concepts:

VSLAM

Navigation2

Perception pipelines

Synthetic data generation

Each sub-topic includes:

A flow diagram

A code snippet (Isaac Python or ROS bridge)

A dataset example

2. Technical Requirements

Use Isaac Sim 4.0+

Describe GPU requirements clearly.

VSLAM examples must follow Isaac ROS hardware-accelerated standards.

Nav2 examples must use:

maps

costmaps

planners

controllers

3. Source Standards

Must cite:

NVIDIA documentation

Robotics AI papers

Perception & navigation research

4. Safety Constraints

Navigation examples must:

avoid collisions

include safety zones

respect real-world robot constraints

Module 4 Constitution: VLA – Vision-Language-Action
1. Writing Standards

All LLM-related explanations must be simple:

Break down “Language → Action → Motor Command”

Use step diagrams

Provide before/after examples (“Clean the room” → steps)

2. Technical Requirements

Whisper for voice → text

LLM for text → plan

ROS 2 action server for plan → robot actions

Must include:

Command pipeline diagrams

Safety filters

Allowed vs disallowed actions list

3. Source Requirements

Cite:

OpenAI Whisper documentation

LLM planning research

VLA papers (RT-1, RT-2, etc.)

4. Ethical & Safety Rules

No unsafe autonomous action examples

No manipulation of humans

All robot plans must include:

fail-safes

self-checks

boundary conditions

## Response snapshot

Updated the project constitution at `.specify/memory/constitution.md` with the provided project details, platform, tooling, and core principles for each module (ROS 2, Digital Twin, AI-Robot Brain, VLA). Set the constitution version to 1.0.0 and dates to 2025-12-05.

## Outcome

- ✅ Impact: Constitution document updated.
- 🧪 Tests: N/A
- 📁 Files: .specify/memory/constitution.md
- 🔁 Next prompts: N/A
- 🧠 Reflection: N/A

## Evaluation notes (flywheel)

- Failure modes observed: N/A
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
