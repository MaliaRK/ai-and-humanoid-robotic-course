# Data Model for Module 1: The Robotic Nervous System (ROS 2)

This document defines the key educational entities and their relationships for the ROS 2 module.

## 1. Core ROS 2 Entities

-   **Node**: The fundamental unit of computation in ROS 2.
    -   **Attributes**: Name, Namespace.
    -   **Relationships**: A Node contains Publishers, Subscribers, Service Servers, Service Clients, Action Servers, Action Clients.
-   **Topic**: A named bus for messages.
    -   **Attributes**: Name, Message Type.
    -   **Relationships**: Publishers send messages to a Topic. Subscribers receive messages from a Topic.
-   **Service**: A request/reply communication pattern.
    -   **Attributes**: Name, Service Type.
    -   **Relationships**: A Service Client sends a request to a Service. A Service Server receives the request and sends a response.
-   **Action**: For long-running, feedback-providing tasks.
    -   **Attributes**: Name, Action Type.
    -   **Relationships**: An Action Client sends a goal to an Action Server. The Action Server provides feedback and a final result.
-   **Message**: The data structure for Topics.
    -   **Attributes**: Fields with specific data types (e.g., `string`, `int32`, `float64`).
-   **Package**: The unit of organization for ROS 2 code.
    -   **Attributes**: Name, Dependencies.
    -   **Relationships**: A Package contains Nodes and launch files.

## 2. URDF Entities

-   **Link**: A rigid body of the robot.
    -   **Attributes**: Name, Inertial properties (mass, inertia), Visual properties (geometry, material), Collision properties (geometry).
-   - **Joint**: Connects two Links.
    -   **Attributes**: Name, Type (e.g., `revolute`, `continuous`, `prismatic`, `fixed`), Parent Link, Child Link, Axis, Limits (effort, velocity).

## 3. Docusaurus Entities

-   **Chapter**: A Markdown file representing a chapter of the module.
    -   **Attributes**: Title, Front-matter.
-   **Section**: A heading within a Chapter.
-   **Code Snippet**: A fenced code block within a Section.
-   **Diagram**: A Mermaid.js diagram within a Section.