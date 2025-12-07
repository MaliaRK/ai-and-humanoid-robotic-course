# Digital Twin Sensor Validation Examples

This directory contains examples and tools for validating that simulated sensor data matches real-world characteristics in the digital twin system.

## Sensor Validation Scripts

### sensor_validation_example.py

This script demonstrates how to validate different types of sensor data:

- **LiDAR Data Validation**: Checks range values, noise characteristics, and realistic measurements
- **Camera Data Validation**: Validates image dimensions, encoding, and pixel values
- **IMU Data Validation**: Verifies acceleration, angular velocity, and orientation values
- **Sensor Fusion Validation**: Checks consistency between different sensor modalities

## Running the Validation Example

```bash
# Make the script executable
chmod +x sensor_validation_example.py

# Run the validation example
python3 sensor_validation_example.py
```

## Validation Criteria

### LiDAR Validation
- Range values within realistic bounds (0.05m to 100m typical)
- Noise characteristics matching real sensors
- Absence of invalid values (NaN, infinity)

### Camera Validation
- Resolution within reasonable range (64x64 to 4096x4096)
- Correct data size matching dimensions and encoding
- Pixel values in valid range [0, 255] for 8-bit

### IMU Validation
- Acceleration magnitude including gravity when stationary (~9.81 m/s²)
- Angular velocity within expected ranges
- Orientation quaternion normalization

### Sensor Fusion Validation
- Consistency checks between different sensor modalities
- Cross-validation of motion detection across sensors

## Integration with Simulation

To integrate validation into your simulation workflow:

1. **During Simulation**: Continuously validate sensor streams
2. **Post-Simulation**: Analyze sensor data quality
3. **Calibration**: Use validation results to improve sensor models

## Real-World Comparison

The validation scripts compare simulated data against real-world characteristics:

- **LiDAR**: Compare with specifications of sensors like Hokuyo URG-04LX or Velodyne Puck
- **Cameras**: Match resolution and noise characteristics of RGB-D sensors
- **IMU**: Validate against specifications of sensors like MPU6050 or ADIS16470

## Customization

You can customize the validation scripts for your specific robot and sensors:

1. Adjust tolerance values based on your sensor specifications
2. Add validation for additional sensor types
3. Modify validation criteria based on your application requirements

## Quality Metrics

The validation process generates quality metrics including:

- Sensor data accuracy
- Noise level assessment
- Temporal consistency
- Cross-sensor agreement