---
id: examples
title: Examples
sidebar_label: Examples
description: Provides examples of how to use the VLA module.
---

This document provides a series of examples demonstrating how to use the Vision-Language-Action (VLA) module to perform various robotics tasks.

## 1. Pick the Object

This example demonstrates how to instruct the VLA module to pick up a specific object. The VLA system will use its vision capabilities to locate the object and its action policy to execute the grasping motion.

```python
from vla_client import VLAClient

client = VLAClient()
instruction = "Pick up the blue cube from the table."
response = client.send_instruction(instruction)

if response.status == "SUCCESS":
    print(f"Robot successfully executed: {instruction}")
else:
    print(f"Failed to execute '{instruction}': {response.error_message}")
```

## 2. Follow this Person

This example illustrates how to command the VLA module to follow a designated person. The vision encoder will identify the person, and the action policy will generate a continuous trajectory to maintain a safe following distance.

```python
from vla_client import VLAClient

client = VLAClient()
instruction = "Follow the person wearing a red shirt."
response = client.send_instruction(instruction)

if response.status == "SUCCESS":
    print(f"Robot is now following the person: {instruction}")
else:
    print(f"Failed to initiate following '{instruction}': {response.error_message}")
```

## 3. Place Object on Shelf

This example shows how to instruct the VLA module to place a previously picked object onto a specified shelf. The system will leverage its spatial understanding and manipulation skills.

```python
from vla_client import VLAClient

client = VLAClient()
instruction = "Place the object I just picked on the top shelf."
response = client.send_instruction(instruction)

if response.status == "SUCCESS":
    print(f"Robot successfully placed the object: {instruction}")
else:
    print(f"Failed to place object '{instruction}': {response.error_message}")
```

## 4. Walk to the Door

This example demonstrates a navigation task, where the VLA module is commanded to walk to a specific location, in this case, a door. The system will plan a path and execute the necessary locomotion.

```python
from vla_client import VLAClient

client = VLAClient()
instruction = "Walk to the door on the left."
response = client.send_instruction(instruction)

if response.status == "SUCCESS":
    print(f"Robot is walking to the door: {instruction}")
else:
    print(f"Failed to initiate walking '{instruction}': {response.error_message}")
```

## 5. Hackathon Quick Example: Pick a Water Bottle

This step-by-step example demonstrates a common "pick and place" task, where the robot is instructed to pick up a water bottle. This scenario is ideal for quickly showcasing the VLA module's capabilities in a hackathon setting.

**Goal**: Robot identifies and picks up a water bottle.

**Steps**:

1.  **Initialize VLA Client**:

    First, establish a connection to the VLA module.

    ```python
    from vla_client import VLAClient

    vla_client = VLAClient()
    ```

2.  **Provide Instruction**:

    Send a natural language command to the VLA module.

    ```python
    instruction = "Pick up the water bottle."
    response = vla_client.send_instruction(instruction)
    ```

3.  **Monitor Execution (Optional)**:

    You can monitor the robot's progress and VLA status via the WebSocket stream.

    ```python
    # Conceptual: In a real scenario, you'd subscribe to the WebSocket
    # and process real-time feedback.
    if response.status == "SUCCESS":
        print(f"Instruction '{instruction}' sent. Robot executing...")
    else:
        print(f"Error sending instruction: {response.error_message}")
    ```

4.  **Observe Robot Action**:

    The robot will use its vision system to locate the water bottle, plan a grasping trajectory, and execute the pick action. In a simulated environment like Isaac Sim, you would observe the virtual robot performing this action. On a physical robot, you would see the actual robot arm moving to grasp the bottle.

**Expected Outcome**: The robot successfully picks up the water bottle.

## References

1.  Murphy, R. R. (2019). *Introduction to AI Robotics* (3rd ed.). MIT Press.
2.  Siciliano, B., Khatib, O. (Eds.). (2016). *Springer Handbook of Robotics* (2nd ed.). Springer.
