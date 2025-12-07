---
id: language-core
title: Language Core
sidebar_label: Language Core
description: Details the Language Core component of the VLA module.
---

## Overview

The Language Core is the component responsible for interpreting natural language instructions from the user and translating them into structured, machine-readable task plans. It serves as the bridge between human intent and robot executability, leveraging advanced Large Language Models (LLMs) for robust understanding.

## LLM Planner

At the heart of the Language Core is an LLM-based planner. This LLM is fine-tuned or prompted to understand various natural language commands and to reason about the steps required to achieve the user's goal within the robot's operational context.

-   **Role**: The LLM acts as a high-level cognitive engine, taking in a user's instruction and potentially visual context (e.g., detected objects from the Vision Encoder) to formulate a coherent plan.
-   **Capabilities**: It can handle synonyms, infer implicit steps, and resolve ambiguities by leveraging its vast linguistic knowledge.

## Structured Task Format

The output of the LLM planner is a `Structured_Task_Plan` in JSON format. This structured format ensures that the Action Policy Engine receives clear, unambiguous instructions that can be directly mapped to robot actions.

-   **Schema**: The JSON schema for task plans is designed to be flexible yet prescriptive, supporting a variety of robot tasks (e.g., `pick_and_place`, `navigate_to`, `interact_with`).
-   **Intent to JSON Mapping**: The Language Core maps the inferred user intent from natural language to specific JSON fields, ensuring all necessary parameters for the action are present and correctly formatted.

## Example JSON for a `pick_and_place` Task

Consider the natural language instruction: "Pick up the red block from the table and place it on the shelf." The Language Core would translate this into a structured JSON plan like this:

```json
{
  "task": "pick_and_place",
  "object": {
    "label": "red_block",
    "attributes": ["red", "block"],
    "location": "table"
  },
  "target_location": {
    "label": "shelf_A",
    "position": [0.5, 1.2, 0.8] // Example: XYZ coordinates in robot's frame
  },
  "parameters": {
    "grasp_type": "power_grasp",
    "approach_distance": 0.1
  }
}
```

This structured format provides the Action Policy Engine with all the necessary details to execute the task.

## Error Handling for Ambiguous or Malformed Natural Language Instructions

Effective error handling within the Language Core is crucial for graceful degradation and reliable operation when faced with ambiguous or malformed natural language instructions. The system should aim to resolve ambiguities or provide clear feedback to the user or upstream components.

### Detection Mechanisms

-   **Confidence Scoring**: The LLM can be configured to provide a confidence score for its interpretation of an instruction. Low confidence indicates potential ambiguity.
-   **Schema Validation**: After generating a `Structured_Task_Plan` (JSON), it must be rigorously validated against a predefined schema. Any deviations indicate a malformed instruction.
-   **Contextual Checks**: Cross-referencing the interpreted instruction with the current visual context from the Vision Encoder can help identify inconsistencies (e.g., user asks to "pick up the red cube" but no red cubes are detected).

### Recovery Strategies

-   **Clarification Dialogue**: For ambiguous instructions, the system should initiate a clarification dialogue with the user (if an interactive interface is available) to gather more information. For example: "I detected multiple red objects. Which one would you like me to pick up?"
-   **Default Actions/Parameters**: In cases of minor ambiguities or missing parameters, the system might default to a safe or commonly used option, while logging the assumption.
-   **Error Propagation**: For unresolvable or severely malformed instructions, the Language Core should propagate an error to the Action Policy Engine or back to the user interface, preventing the execution of an incorrect or unsafe action. The error message should be clear and descriptive.
-   **Logging**: Detailed logging of ambiguous or malformed inputs and the system's response is essential for auditing and improving the LLM planner over time.

## References

-   \[1] Wei, J., Tay, Y., Bommasani, R., Raffel, C., Zoph, B., Roberts, K., ... & Le, Q. V. (2022). *Emergent abilities of large language models*. arXiv preprint arXiv:2206.07682.
-   \[2] Huang, W., et al. (2023). *Language Models as Robotic Manipulators: A Survey*. arXiv preprint arXiv:2308.14533.
-   \[3] Mialon, G., et al. (2023). *Demystifying GPT Self-Correction: An In-depth Analysis of Errors and Mechanisms*. arXiv preprint arXiv:2305.12270.

