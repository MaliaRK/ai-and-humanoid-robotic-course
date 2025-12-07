#!/usr/bin/env python3
"""
Sensor Data Validation Example

This script demonstrates how to validate that simulated sensor data
matches real-world characteristics for various sensor types.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import math

class SensorValidator:
    def __init__(self):
        self.validation_results = {}

    def validate_lidar_data(self, ranges, expected_range=10.0, tolerance=0.1):
        """
        Validate LiDAR data against expected real-world characteristics
        """
        print("Validating LiDAR data...")

        # Check for valid range values
        valid_ranges = [r for r in ranges if not (math.isinf(r) or math.isnan(r))]

        if len(valid_ranges) == 0:
            print("❌ No valid LiDAR ranges found")
            return False

        # Check if ranges are within expected bounds
        range_min = min(valid_ranges)
        range_max = max(valid_ranges)

        print(f"  Range: {range_min:.2f}m - {range_max:.2f}m")

        # Check for realistic values (not too close to sensor, not too far)
        if range_min < 0.05:  # Too close (below typical min range)
            print("  ❌ Range too close - possible sensor clipping")
            return False

        if range_max > 100.0:  # Too far (beyond typical range)
            print("  ❌ Range too far - possible invalid measurements")
            return False

        # Check for realistic noise characteristics
        if len(valid_ranges) > 1:
            range_std = np.std(valid_ranges)
            if range_std > 5.0:  # High variance might indicate noise issues
                print("  ⚠️  High variance in ranges - check for noise")
            else:
                print("  ✅ Range variance within acceptable limits")

        print("  ✅ LiDAR data validation passed")
        return True

    def validate_camera_data(self, image_data, width, height, encoding):
        """
        Validate camera data against expected real-world characteristics
        """
        print(f"\nValidating Camera data...")

        print(f"  Resolution: {width}x{height}")
        print(f"  Encoding: {encoding}")

        # Check if image dimensions are reasonable
        if width < 64 or height < 64:
            print("  ❌ Image resolution too low for practical use")
            return False

        if width > 4096 or height > 4096:
            print("  ❌ Image resolution unrealistically high")
            return False

        # Check if image data size matches dimensions
        expected_size = width * height
        if encoding == 'rgb8':
            expected_size *= 3  # 3 channels
        elif encoding == 'mono8':
            pass  # 1 channel
        elif encoding == 'bgr8':
            expected_size *= 3  # 3 channels

        if len(image_data) != expected_size:
            print(f"  ❌ Image data size mismatch: expected {expected_size}, got {len(image_data)}")
            return False

        # Check for realistic pixel values (0-255 for 8-bit)
        pixel_values = np.array(image_data)
        if np.any(pixel_values < 0) or np.any(pixel_values > 255):
            print("  ❌ Pixel values outside valid range [0, 255]")
            return False

        print("  ✅ Camera data validation passed")
        return True

    def validate_imu_data(self, linear_accel, angular_vel, orientation):
        """
        Validate IMU data against expected real-world characteristics
        """
        print(f"\nValidating IMU data...")

        # Check linear acceleration (should include gravity when stationary)
        acc_magnitude = np.sqrt(linear_accel[0]**2 + linear_accel[1]**2 + linear_accel[2]**2)
        print(f"  Linear acceleration magnitude: {acc_magnitude:.2f} m/s²")

        # When stationary, acceleration should be close to 9.81 m/s² (gravity)
        if abs(acc_magnitude - 9.81) > 2.0:  # Allow for motion
            print("  ⚠️  Acceleration not consistent with gravity (may be moving)")
        else:
            print("  ✅ Acceleration consistent with gravity (stationary)")

        # Check angular velocity (should be low when not rotating)
        ang_vel_magnitude = np.sqrt(angular_vel[0]**2 + angular_vel[1]**2 + angular_vel[2]**2)
        print(f"  Angular velocity magnitude: {ang_vel_magnitude:.3f} rad/s")

        if ang_vel_magnitude > 1.0:  # 1 rad/s = ~57 deg/s
            print("  ⚠️  High angular velocity detected (rapid rotation)")
        else:
            print("  ✅ Angular velocity within normal range")

        # Check orientation quaternion normalization
        quat_norm = np.sqrt(orientation[0]**2 + orientation[1]**2 + orientation[2]**2 + orientation[3]**2)
        print(f"  Quaternion norm: {quat_norm:.3f}")

        if abs(quat_norm - 1.0) > 0.01:
            print("  ❌ Orientation quaternion not normalized")
            return False
        else:
            print("  ✅ Orientation quaternion properly normalized")

        print("  ✅ IMU data validation passed")
        return True

    def validate_sensor_fusion(self, lidar_ranges, imu_linear_acc, camera_width, camera_height):
        """
        Validate consistency between different sensor types
        """
        print(f"\nValidating sensor fusion consistency...")

        # Example: Check if IMU suggests robot is moving rapidly when LiDAR is stable
        valid_ranges = [r for r in lidar_ranges if not (math.isinf(r) or math.isnan(r))]
        if len(valid_ranges) > 1:
            range_variance = np.var(valid_ranges)
            acc_magnitude = np.sqrt(sum(x**2 for x in imu_linear_acc))

            # If acceleration is high but LiDAR variance is low, might indicate inconsistency
            if acc_magnitude > 5.0 and range_variance < 0.01:
                print("  ⚠️  High acceleration but stable LiDAR - possible inconsistency")
            else:
                print("  ✅ Sensor data consistent across modalities")

        print("  ✅ Sensor fusion validation passed")
        return True

    def run_comprehensive_validation(self, sensor_data):
        """
        Run comprehensive validation on all sensor data
        """
        print("="*50)
        print("COMPREHENSIVE SENSOR VALIDATION")
        print("="*50)

        all_passed = True

        # Validate LiDAR if present
        if 'lidar' in sensor_data:
            lidar_result = self.validate_lidar_data(
                sensor_data['lidar']['ranges'],
                sensor_data['lidar'].get('expected_range', 10.0)
            )
            all_passed = all_passed and lidar_result

        # Validate Camera if present
        if 'camera' in sensor_data:
            camera_result = self.validate_camera_data(
                sensor_data['camera']['data'],
                sensor_data['camera']['width'],
                sensor_data['camera']['height'],
                sensor_data['camera']['encoding']
            )
            all_passed = all_passed and camera_result

        # Validate IMU if present
        if 'imu' in sensor_data:
            imu_result = self.validate_imu_data(
                sensor_data['imu']['linear_acceleration'],
                sensor_data['imu']['angular_velocity'],
                sensor_data['imu']['orientation']
            )
            all_passed = all_passed and imu_result

        # Validate sensor fusion if multiple sensors present
        if len(sensor_data) > 1:
            fusion_result = self.validate_sensor_fusion(
                sensor_data.get('lidar', {}).get('ranges', []),
                sensor_data.get('imu', {}).get('linear_acceleration', [0, 0, 0]),
                sensor_data.get('camera', {}).get('width', 0),
                sensor_data.get('camera', {}).get('height', 0)
            )
            all_passed = all_passed and fusion_result

        print("\n" + "="*50)
        if all_passed:
            print("🎉 ALL VALIDATIONS PASSED!")
            print("Sensor data matches real-world characteristics")
        else:
            print("❌ SOME VALIDATIONS FAILED!")
            print("Sensor data may not match real-world characteristics")
        print("="*50)

        return all_passed

def generate_example_sensor_data():
    """
    Generate example sensor data that matches real-world characteristics
    """
    # Simulated LiDAR data: mostly empty space with some obstacles
    lidar_ranges = []
    for i in range(360):  # 360 degree scan
        angle = i * math.pi / 180
        if 80 <= i <= 100:  # Obstacle at ~90 degrees
            lidar_ranges.append(2.0 + np.random.normal(0, 0.01))  # 2m obstacle with noise
        elif 260 <= i <= 280:  # Another obstacle at ~270 degrees
            lidar_ranges.append(1.5 + np.random.normal(0, 0.01))  # 1.5m obstacle with noise
        else:
            lidar_ranges.append(20.0 + np.random.normal(0, 0.05))  # Empty space with noise

    # Simulated Camera data: simple pattern
    camera_width, camera_height = 640, 480
    camera_data = []
    for y in range(camera_height):
        for x in range(camera_width):
            # Create a simple pattern: red on left, blue on right
            if x < camera_width / 2:
                camera_data.extend([255, 0, 0])  # Red
            else:
                camera_data.extend([0, 0, 255])  # Blue

    # Simulated IMU data: robot is mostly stationary
    imu_linear_accel = [0.1, 0.05, 9.82]  # Close to gravity
    imu_angular_vel = [0.01, -0.02, 0.005]  # Very slight rotation
    imu_orientation = [0.0, 0.0, 0.0, 1.0]  # Mostly upright

    return {
        'lidar': {
            'ranges': lidar_ranges,
            'expected_range': 10.0
        },
        'camera': {
            'data': camera_data,
            'width': camera_width,
            'height': camera_height,
            'encoding': 'rgb8'
        },
        'imu': {
            'linear_acceleration': imu_linear_accel,
            'angular_velocity': imu_angular_vel,
            'orientation': imu_orientation
        }
    }

def main():
    """
    Main function to run sensor validation example
    """
    print("Digital Twin Sensor Validation Example")
    print("This script demonstrates how to validate that simulated sensor data")
    print("matches real-world characteristics for humanoid robotics applications.\n")

    # Create validator instance
    validator = SensorValidator()

    # Generate example sensor data
    print("Generating example sensor data...")
    example_data = generate_example_sensor_data()

    # Run validation
    validation_passed = validator.run_comprehensive_validation(example_data)

    # Show summary
    print(f"\nValidation Summary:")
    print(f"- LiDAR points: {len(example_data['lidar']['ranges'])}")
    print(f"- Camera resolution: {example_data['camera']['width']}x{example_data['camera']['height']}")
    print(f"- IMU linear acceleration: [{example_data['imu']['linear_acceleration'][0]:.2f}, {example_data['imu']['linear_acceleration'][1]:.2f}, {example_data['imu']['linear_acceleration'][2]:.2f}]")

    if validation_passed:
        print("\n✅ Sensor validation successful!")
        print("The simulated sensor data exhibits realistic characteristics.")
    else:
        print("\n❌ Sensor validation failed!")
        print("The simulated sensor data may need adjustment to match real-world characteristics.")

if __name__ == "__main__":
    main()