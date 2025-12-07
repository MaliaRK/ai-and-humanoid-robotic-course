# Data Model for Module 2: The Digital Twin (Gazebo & Unity)

## 1. Core Digital Twin Entities

### Digital Twin Model
- **Description**: The virtual representation of a physical robot system
- **Attributes**:
  - `physical_robot_reference`: Reference to the real robot counterpart
  - `synchronization_frequency`: Frequency of data synchronization between sim and real
  - `fidelity_level`: Level of detail in the simulation (low, medium, high, photorealistic)
  - `validation_metrics`: Metrics for measuring sim-to-real gap
- **Relationships**: Associated with Physics Simulation, Sensor Simulation, and Validation components

### Physics Simulation Model
- **Description**: Computational model of real-world physical forces and interactions
- **Attributes**:
  - `engine_type`: Physics engine used (ODE, Bullet, DART)
  - `gravity_settings`: Gravity vector and magnitude
  - `collision_properties`: Material properties, friction coefficients, restitution
  - `integration_parameters`: Time step, solver type, constraint settings
- **Relationships**: Connected to Simulation Environment and Robot Model

### Sensor Simulation Model
- **Description**: Computational model of real-world sensor outputs with noise and limitations
- **Attributes**:
  - `sensor_type`: Type of sensor (LiDAR, Camera, IMU, etc.)
  - `noise_parameters`: Noise model parameters (Gaussian, salt-and-pepper, etc.)
  - `accuracy_specifications`: Range, resolution, field of view, etc.
  - `update_rate`: Frequency of sensor data updates
- **Relationships**: Connected to Robot Model and Data Streams

### Simulation Environment Model
- **Description**: Virtual space containing objects, physics parameters, and environmental conditions
- **Attributes**:
  - `environment_type`: Indoor, outdoor, laboratory, etc.
  - `lighting_conditions`: Lighting parameters for rendering
  - `obstacles`: Static and dynamic objects in the environment
  - `materials`: Surface properties and physical characteristics
- **Relationships**: Contains Physics Simulation and Robot Model

## 2. ROS 2 Integration Entities

### ROS 2 Bridge Model
- **Description**: Middleware connection between simulation environments and ROS 2 nodes
- **Attributes**:
  - `connection_protocol`: Communication protocol used (TCP, UDP, shared memory)
  - `topic_mappings`: Mappings between simulation and ROS 2 topics
  - `message_formats`: Types and structures of exchanged messages
  - `synchronization_settings`: Timing and frequency configurations
- **Relationships**: Connects Simulation Environment to ROS 2 ecosystem

### Data Stream Model
- **Description**: Flow of sensor and control data between simulation and ROS 2
- **Attributes**:
  - `stream_type`: Type of data (sensor, control, state)
  - `message_frequency`: Rate of data transmission
  - `buffer_size`: Size of data buffers
  - `compression`: Data compression settings if applicable
- **Relationships**: Part of ROS 2 Bridge and connected to Sensor Simulation

## 3. Validation and Testing Entities

### Validation Scenario Model
- **Description**: Specific test scenario for evaluating sim-to-real transfer
- **Attributes**:
  - `scenario_type`: Type of test (locomotion, manipulation, perception)
  - `environment_conditions`: Environmental parameters for the test
  - `success_criteria`: Quantitative measures of success
  - `metrics_collected`: Performance metrics to be measured
- **Relationships**: Associated with Digital Twin Model and Validation Metrics

### Validation Metrics Model
- **Description**: Quantitative measures for assessing simulation quality and sim-to-real gap
- **Attributes**:
  - `metric_type`: Type of metric (accuracy, precision, timing, etc.)
  - `measurement_unit`: Units for the metric
  - `threshold_values`: Acceptable ranges for the metric
  - `comparison_basis`: What the metric compares against (real data, baseline, etc.)
- **Relationships**: Connected to Validation Scenario and Digital Twin Model

## 4. Educational Content Entities

### Chapter Model
- **Description**: Educational content segment covering specific digital twin concepts
- **Attributes**:
  - `chapter_title`: Title of the chapter
  - `learning_objectives`: Educational goals for the chapter
  - `technical_content`: Core technical information covered
  - `practical_exercises`: Hands-on activities for students
- **Relationships**: Contains Sections and Examples

### Example Model
- **Description**: Practical demonstration of concepts through code or simulation
- **Attributes**:
  - `example_type`: Type of example (code snippet, simulation, configuration)
  - `complexity_level`: Difficulty level (beginner, intermediate, advanced)
  - `dependencies`: Prerequisites for running the example
  - `expected_outcome`: What the example should demonstrate
- **Relationships**: Belongs to Chapter and uses Digital Twin Components