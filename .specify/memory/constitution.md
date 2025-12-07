<!--
Sync Impact Report:
Version change: 0.0.0 → 1.0.0 (MAJOR: Initial constitution creation/significant update)
Modified principles: N/A (new principles defined)
Added sections: Module 1 Constitution, Module 2 Constitution, Module 3 Constitution, Module 4 Constitution
Removed sections: N/A
Templates requiring updates:
- .specify/templates/plan-template.md: ⚠ pending
- .specify/templates/spec-template.md: ⚠ pending
- .specify/templates/tasks-template.md: ⚠ pending
- .specify/templates/commands/*.md: ⚠ pending
Follow-up TODOs: N/A
-->
# AI/Spec-Driven Book - Physical AI, Humanoid Robotics, and Agentic Engineering Constitution

## Core Principles

### Module 1 Constitution: Robotic Nervous System (ROS 2)

#### 1. Writing & Documentation Standards
All ROS 2 explanations MUST follow Flesch-Kincaid Grade 8–10 readability.
Use consistent terminology: Node, Topic, Service, Parameter, Launch File, URDF, Joint, Link, Transform (TF2).
Each concept MUST include:
- A definition
- A real-world humanoid example
- A code snippet using rclpy
- A diagram (Docusaurus-friendly)

#### 2. Technical Standards
ROS 2 version MUST be Humble or later.
Code MUST follow:
- PEP8
- ROS 2 Python conventions
- Correct message types (e.g., geometry_msgs/Twist, sensor_msgs/Imu)
URDF examples MUST be mechanically accurate (no impossible joints).

#### 3. Citation Standards
Use APA 7 for:
- ROS documentation
- Robotics textbooks
- Peer-reviewed robot control papers
Minimum 2 peer-reviewed citations per chapter.

#### 4. Safety Standards
Robot control examples MUST include:
- Safety stop
- Rate limiting
- Speed caps
- Joint limit enforcement

### Module 2 Constitution: Digital Twin (Gazebo & Unity)

#### 1. Writing & Clarity Rules
Concepts MUST be explained with:
- Physics analogies
- Simple diagrams
- Clear step-by-step setup instructions
All simulation examples MUST be reproducible in:
- Gazebo Fortress/Ignition
- Unity HDRP or URP

#### 2. Technical Standards
Physics parameters MUST be accurate:
- mass, inertia, friction, restitution
Sensor simulation accuracy:
- LiDAR (range, resolution)
- IMU (noise models)
- Depth cams (FOV, clipping planes)
World building MUST include:
- lighting
- materials
- collision shapes

#### 3. Citation Standards
Cite Gazebo, Unity, and physics references using APA7.
Minimum 1 simulation paper + 1 physics source per chapter.

#### 4. Safety & Ethics
No simulation examples involving unsafe or unethical robot behavior.
No humanoid actions that mimic harmful real-world behavior.

### Module 3 Constitution: AI-Robot Brain (NVIDIA Isaac)

#### 1. Writing & Documentation
MUST simplify complex AI concepts:
- VSLAM
- Navigation2
- Perception pipelines
- Synthetic data generation
Each sub-topic MUST include:
- A flow diagram
- A code snippet (Isaac Python or ROS bridge)
- A dataset example

#### 2. Technical Requirements
Use Isaac Sim 4.0+.
Describe GPU requirements clearly.
VSLAM examples MUST follow Isaac ROS hardware-accelerated standards.
Nav2 examples MUST use:
- maps
- costmaps
- planners
- controllers

#### 3. Source Standards
MUST cite:
- NVIDIA documentation
- Robotics AI papers
- Perception & navigation research

#### 4. Safety Constraints
Navigation examples MUST:
- avoid collisions
- include safety zones
- respect real-world robot constraints

### Module 4 Constitution: VLA – Vision-Language-Action

#### 1. Writing Standards
All LLM-related explanations MUST be simple:
- Break down “Language → Action → Motor Command”
- Use step diagrams
- Provide before/after examples (“Clean the room” → steps)

#### 2. Technical Requirements
Whisper for voice → text.
LLM for text → plan.
ROS 2 action server for plan → robot actions.
MUST include:
- Command pipeline diagrams
- Safety filters
- Allowed vs disallowed actions list

#### 3. Source Requirements
Cite:
- OpenAI Whisper documentation
- LLM planning research
- VLA papers (RT-1, RT-2, etc.)

#### 4. Ethical & Safety Rules
No unsafe autonomous action examples.
No manipulation of humans.
All robot plans MUST include:
- fail-safes
- self-checks
- boundary conditions

## Additional Constraints
**Platform**: Docusaurus documentationsite deployed to github pages
**Tooling**: Spec-kit Plus + Claude Code

## Governance
This constitution supersedes all other practices; Amendments require documentation, approval, and a migration plan. All PRs/reviews MUST verify compliance; Complexity MUST be justified.

**Version**: 1.0.0 | **Ratified**: 2025-12-05 | **Last Amended**: 2025-12-05
