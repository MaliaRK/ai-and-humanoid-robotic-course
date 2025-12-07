# Simulation-to-Reality Validation Framework

This directory contains scripts for validating that simulated robot data matches real-world characteristics, enabling effective sim-to-real transfer.

## Overview

The validation framework includes several tools for comparing simulation and reality:

1. **Sim-Real Comparison Tool**: Compares synchronized data from simulation and real robots
2. **Sensor Stream Validator**: Validates that sensor data streams match expected characteristics
3. **Comprehensive Validation Framework**: End-to-end validation with reporting and visualization

## Scripts

### 1. sim_real_comparison.py

Compares simulation and real-world robot data to validate sim-to-real transfer quality.

**Features:**
- Synchronizes data based on timestamps
- Calculates comparison metrics for poses, velocities, scans, and IMU data
- Generates comprehensive reports and visualizations
- Saves results to JSON and CSV formats

**Usage:**
```bash
rosrun your_package sim_real_comparison.py _output_dir:=/path/to/output
```

**Parameters:**
- `output_dir`: Directory to save results (default: `/tmp/sim_real_comparison`)
- `sync_tolerance`: Timestamp tolerance for synchronization (default: 0.1 seconds)

### 2. validate_sensor_streams.py

Validates that sensor data streams match expected characteristics and identifies potential issues.

**Features:**
- Monitors LiDAR, IMU, odometry, joint states, and image data
- Validates data ranges and consistency
- Detects anomalies and potential sensor issues
- Logs validation results continuously

**Usage:**
```bash
rosrun your_package validate_sensor_streams.py _validation_frequency:=0.1
```

**Parameters:**
- `window_size`: Size of data window for analysis (default: 1000)
- `validation_frequency`: How often to validate (default: 1.0 Hz)
- `output_dir`: Directory to save validation logs (default: `/tmp/sensor_validation`)

### 3. validation_framework.py

Comprehensive framework for end-to-end validation with data collection, comparison, and reporting.

**Features:**
- Collects data from both simulation and real systems
- Performs comprehensive metric calculations
- Generates detailed reports and visualizations
- Assesses overall validation quality

**Usage:**
```bash
rosrun your_package validation_framework.py _collection_duration:=60.0
```

**Parameters:**
- `collection_duration`: Duration to collect data (default: 60.0 seconds)
- `validation_frequency`: Validation frequency (default: 0.1 Hz)
- `output_dir`: Output directory (default: `/tmp/validation_framework`)
- `sim_prefix`: Topic prefix for simulation data (default: `/sim`)
- `real_prefix`: Topic prefix for real data (default: `/real`)

## Topics Monitored

The validation tools monitor these standard ROS topics:

- **LiDAR**: `/scan`, `/sim/scan`, `/real/scan`
- **IMU**: `/imu/data`, `/sim/imu/data`, `/real/imu/data`
- **Odometry**: `/odom`, `/sim/odom`, `/real/odom`
- **Joint States**: `/joint_states`, `/sim/joint_states`, `/real/joint_states`
- **Images**: `/camera/image_raw`, `/sim/camera/image_raw`, `/real/camera/image_raw`
- **Commands**: `/cmd_vel`, `/sim/cmd_vel`, `/real/cmd_vel`

## Metrics Calculated

The framework calculates various metrics for validation:

### Position Metrics
- Mean Squared Error (MSE)
- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- Correlation coefficient
- Position accuracy

### Velocity Metrics
- Linear velocity error
- Angular velocity error
- Speed consistency

### Sensor Metrics
- LiDAR scan similarity
- IMU correlation
- Image quality metrics
- Data consistency

### Statistical Tests
- Kolmogorov-Smirnov test
- Pearson correlation
- Chi-square tests
- Distribution comparison

## Output Files

Validation results are saved in the specified output directory:

- `comparison_report.json`: Detailed comparison metrics
- `comparison_summary.txt`: Human-readable summary
- `comparison_visualizations.png`: Visual comparison plots
- `validation_metrics.json`: Calculated metrics
- `comprehensive_report.json`: Full validation report
- `validation_visualizations.png`: Validation plots
- `raw_validation_data.pkl`: Raw collected data
- `validation_log_*.json`: Continuous validation logs

## Quality Assessment

The framework assesses validation quality based on:

- **Excellent**: Correlation > 0.9 or MSE < 0.01
- **Good**: Correlation > 0.8 or MSE < 0.1
- **Fair**: Correlation > 0.6 or MSE < 1.0
- **Poor**: Lower correlation or higher MSE

## Integration with ROS Launch

Example launch file for running validation:

```xml
<launch>
  <!-- Simulation data validation -->
  <node name="sim_real_comparison" pkg="your_package" type="sim_real_comparison.py" output="screen">
    <param name="output_dir" value="/home/user/validation_results"/>
  </node>

  <!-- Continuous sensor validation -->
  <node name="sensor_validator" pkg="your_package" type="validate_sensor_streams.py" output="screen">
    <param name="validation_frequency" value="0.5"/>
    <param name="output_dir" value="/home/user/sensor_validation"/>
  </node>

  <!-- Comprehensive validation framework -->
  <node name="validation_framework" pkg="your_package" type="validation_framework.py" output="screen">
    <param name="collection_duration" value="120.0"/>
    <param name="output_dir" value="/home/user/comprehensive_validation"/>
    <param name="sim_prefix" value="/gazebo"/>
    <param name="real_prefix" value="/robot"/>
  </node>
</launch>
```

## Best Practices

1. **Run validation regularly** during development to catch issues early
2. **Use representative scenarios** that match your intended use cases
3. **Validate multiple metrics**, not just one aspect
4. **Compare against baselines** to understand improvement
5. **Document validation results** for reproducibility
6. **Monitor continuously** in production systems

## Troubleshooting

### Common Issues

1. **No data collected**: Check topic names and prefixes
2. **Synchronization issues**: Adjust sync_tolerance parameter
3. **Memory issues**: Reduce window_size for continuous validation
4. **High CPU usage**: Reduce validation_frequency

### Debugging Tips

- Check ROS topics with `rostopic list`
- Verify message types with `rostopic type /topic`
- Monitor data flow with `rostopic echo /topic`
- Check node status with `rosnode info node_name`

## Customization

The validation framework can be customized for specific robot types and validation requirements:

1. Add custom sensor types by extending the callback methods
2. Modify validation thresholds for your specific requirements
3. Add new metrics by extending the metric calculation functions
4. Customize visualization plots for your specific use case