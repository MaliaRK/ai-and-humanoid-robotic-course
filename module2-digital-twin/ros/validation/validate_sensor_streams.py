#!/usr/bin/env python3
"""
Sensor Stream Validation Tool

This script validates that sensor data streams from simulation match real-world characteristics
and identifies potential issues with the sim-to-real transfer.
"""

import rospy
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from sensor_msgs.msg import LaserScan, Image, Imu, JointState
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Float64, String
import csv
import json
import os
from datetime import datetime
from collections import deque, defaultdict
import threading
import time


class SensorStreamValidator:
    def __init__(self):
        rospy.init_node('sensor_stream_validator')

        # Configuration parameters
        self.window_size = rospy.get_param('~window_size', 1000)
        self.validation_frequency = rospy.get_param('~validation_frequency', 1.0)  # Hz
        self.output_dir = rospy.get_param('~output_dir', '/tmp/sensor_validation')

        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)

        # Data storage with circular buffers
        self.data_buffers = {
            'lidar': deque(maxlen=self.window_size),
            'imu': deque(maxlen=self.window_size),
            'odometry': deque(maxlen=self.window_size),
            'joint_states': deque(maxlen=self.window_size),
            'image_stats': deque(maxlen=self.window_size)
        }

        # Validation results
        self.validation_results = defaultdict(list)

        # Publishers for validation status
        self.status_pub = rospy.Publisher('/sensor_validation/status', String, queue_size=10)
        self.metrics_pub = rospy.Publisher('/sensor_validation/metrics', String, queue_size=10)

        # Lock for thread safety
        self.lock = threading.Lock()

        # Validation timers
        self.last_validation_time = rospy.Time.now()
        self.validation_timer = rospy.Timer(
            rospy.Duration(1.0/self.validation_frequency),
            self.validate_current_data
        )

    def lidar_callback(self, msg):
        """Process LiDAR data"""
        with self.lock:
            self.data_buffers['lidar'].append({
                'timestamp': rospy.Time.now(),
                'ranges': np.array(msg.ranges),
                'intensities': np.array(msg.intensities) if msg.intensities else None,
                'stats': self.calculate_lidar_stats(msg)
            })

    def imu_callback(self, msg):
        """Process IMU data"""
        with self.lock:
            self.data_buffers['imu'].append({
                'timestamp': rospy.Time.now(),
                'linear_acceleration': [
                    msg.linear_acceleration.x,
                    msg.linear_acceleration.y,
                    msg.linear_acceleration.z
                ],
                'angular_velocity': [
                    msg.angular_velocity.x,
                    msg.angular_velocity.y,
                    msg.angular_velocity.z
                ],
                'orientation': [
                    msg.orientation.x,
                    msg.orientation.y,
                    msg.orientation.z,
                    msg.orientation.w
                ],
                'stats': self.calculate_imu_stats(msg)
            })

    def odometry_callback(self, msg):
        """Process odometry data"""
        with self.lock:
            self.data_buffers['odometry'].append({
                'timestamp': rospy.Time.now(),
                'pose': msg.pose.pose,
                'twist': msg.twist.twist,
                'stats': self.calculate_odometry_stats(msg)
            })

    def joint_states_callback(self, msg):
        """Process joint states data"""
        with self.lock:
            self.data_buffers['joint_states'].append({
                'timestamp': rospy.Time.now(),
                'positions': list(msg.position),
                'velocities': list(msg.velocity),
                'efforts': list(msg.effort),
                'stats': self.calculate_joint_stats(msg)
            })

    def image_callback(self, msg):
        """Process image data statistics"""
        # Calculate image statistics without storing full images
        stats = self.calculate_image_stats(msg)
        with self.lock:
            self.data_buffers['image_stats'].append({
                'timestamp': rospy.Time.now(),
                'stats': stats
            })

    def calculate_lidar_stats(self, scan_msg):
        """Calculate statistics for LiDAR data"""
        ranges = np.array(scan_msg.ranges)
        valid_ranges = ranges[np.isfinite(ranges)]

        if len(valid_ranges) == 0:
            return {
                'mean_range': float('inf'),
                'std_range': 0.0,
                'min_range': float('inf'),
                'max_range': 0.0,
                'valid_points': 0,
                'density': 0.0
            }

        return {
            'mean_range': float(np.mean(valid_ranges)),
            'std_range': float(np.std(valid_ranges)),
            'min_range': float(np.min(valid_ranges)),
            'max_range': float(np.max(valid_ranges)),
            'valid_points': int(len(valid_ranges)),
            'density': float(len(valid_ranges) / len(scan_msg.ranges)) if len(scan_msg.ranges) > 0 else 0.0
        }

    def calculate_imu_stats(self, imu_msg):
        """Calculate statistics for IMU data"""
        linear_acc = np.array([
            imu_msg.linear_acceleration.x,
            imu_msg.linear_acceleration.y,
            imu_msg.linear_acceleration.z
        ])
        angular_vel = np.array([
            imu_msg.angular_velocity.x,
            imu_msg.angular_velocity.y,
            imu_msg.angular_velocity.z
        ])

        return {
            'linear_acceleration_magnitude': float(np.linalg.norm(linear_acc)),
            'angular_velocity_magnitude': float(np.linalg.norm(angular_vel)),
            'orientation_norm': float(np.linalg.norm([
                imu_msg.orientation.x,
                imu_msg.orientation.y,
                imu_msg.orientation.z,
                imu_msg.orientation.w
            ]))
        }

    def calculate_odometry_stats(self, odom_msg):
        """Calculate statistics for odometry data"""
        linear_vel = np.array([
            odom_msg.twist.twist.linear.x,
            odom_msg.twist.twist.linear.y,
            odom_msg.twist.twist.linear.z
        ])
        angular_vel = np.array([
            odom_msg.twist.twist.angular.x,
            odom_msg.twist.twist.angular.y,
            odom_msg.twist.twist.angular.z
        ])

        return {
            'linear_speed': float(np.linalg.norm(linear_vel)),
            'angular_speed': float(np.linalg.norm(angular_vel)),
            'position_change': float(np.sqrt(
                odom_msg.pose.pose.position.x**2 +
                odom_msg.pose.pose.position.y**2 +
                odom_msg.pose.pose.position.z**2
            ))
        }

    def calculate_joint_stats(self, joint_msg):
        """Calculate statistics for joint states data"""
        if len(joint_msg.position) == 0:
            return {
                'mean_position': 0.0,
                'std_position': 0.0,
                'mean_velocity': 0.0,
                'std_velocity': 0.0
            }

        return {
            'mean_position': float(np.mean(joint_msg.position)),
            'std_position': float(np.std(joint_msg.position)),
            'mean_velocity': float(np.mean(joint_msg.velocity)) if len(joint_msg.velocity) > 0 else 0.0,
            'std_velocity': float(np.std(joint_msg.velocity)) if len(joint_msg.velocity) > 0 else 0.0
        }

    def calculate_image_stats(self, img_msg):
        """Calculate statistics for image data (without storing full image)"""
        # This is a simplified version - in practice, you'd want to analyze image content
        # but not store the full image data in memory

        # Calculate basic statistics
        total_pixels = img_msg.width * img_msg.height
        expected_size = total_pixels

        if img_msg.encoding in ['rgb8', 'bgr8']:
            expected_size *= 3  # 3 channels
        elif img_msg.encoding in ['mono8', '8UC1']:
            pass  # 1 channel
        elif img_msg.encoding in ['rgb16', 'bgr16']:
            expected_size *= 6  # 3 channels * 2 bytes
        elif img_msg.encoding in ['mono16', '16UC1']:
            expected_size *= 2  # 2 bytes per pixel

        return {
            'width': img_msg.width,
            'height': img_msg.height,
            'encoding': img_msg.encoding,
            'data_size': len(img_msg.data),
            'expected_size': expected_size,
            'size_match': len(img_msg.data) == expected_size
        }

    def validate_current_data(self, event):
        """Validate current data against expected characteristics"""
        with self.lock:
            # Create copies of current data to avoid lock contention during analysis
            current_data = {}
            for key, buffer in self.data_buffers.items():
                current_data[key] = list(buffer)

        # Perform validations
        validation_results = {}

        # Validate LiDAR data
        if 'lidar' in current_data and len(current_data['lidar']) > 0:
            lidar_results = self.validate_lidar_stream(current_data['lidar'])
            validation_results['lidar'] = lidar_results

        # Validate IMU data
        if 'imu' in current_data and len(current_data['imu']) > 0:
            imu_results = self.validate_imu_stream(current_data['imu'])
            validation_results['imu'] = imu_results

        # Validate Odometry data
        if 'odometry' in current_data and len(current_data['odometry']) > 0:
            odom_results = self.validate_odometry_stream(current_data['odometry'])
            validation_results['odometry'] = odom_results

        # Validate Joint States data
        if 'joint_states' in current_data and len(current_data['joint_states']) > 0:
            joint_results = self.validate_joint_stream(current_data['joint_states'])
            validation_results['joint_states'] = joint_results

        # Validate Image data
        if 'image_stats' in current_data and len(current_data['image_stats']) > 0:
            image_results = self.validate_image_stream(current_data['image_stats'])
            validation_results['image'] = image_results

        # Store validation results
        for sensor_type, results in validation_results.items():
            self.validation_results[sensor_type].append({
                'timestamp': rospy.Time.now(),
                'results': results
            })

        # Publish status
        status_msg = String()
        status_msg.data = json.dumps({
            'timestamp': rospy.Time.now().to_sec(),
            'validation_results': validation_results
        })
        self.status_pub.publish(status_msg)

        # Log results
        self.log_validation_results(validation_results)

    def validate_lidar_stream(self, lidar_data):
        """Validate LiDAR stream characteristics"""
        if len(lidar_data) < 10:  # Need sufficient data for meaningful validation
            return {'status': 'insufficient_data', 'message': 'Not enough data points'}

        # Calculate recent statistics
        recent_stats = [item['stats'] for item in lidar_data[-50:]]  # Last 50 points

        # Expected ranges for LiDAR data
        expected_mean_range = (1.0, 20.0)  # 1-20 meters typical
        expected_valid_density = 0.8  # At least 80% valid points

        # Check mean range
        mean_ranges = [stat['mean_range'] for stat in recent_stats if stat['mean_range'] != float('inf')]
        if len(mean_ranges) > 0:
            current_mean = np.mean(mean_ranges)
            range_valid = expected_mean_range[0] <= current_mean <= expected_mean_range[1]
        else:
            range_valid = False

        # Check valid point density
        densities = [stat['density'] for stat in recent_stats]
        if len(densities) > 0:
            avg_density = np.mean(densities)
            density_valid = avg_density >= expected_valid_density
        else:
            density_valid = False

        # Check for sudden changes (could indicate sensor malfunction)
        if len(mean_ranges) > 1:
            range_changes = np.diff(mean_ranges)
            sudden_change = np.any(np.abs(range_changes) > 5.0)  # More than 5m change
        else:
            sudden_change = False

        return {
            'status': 'warning' if not range_valid or not density_valid or sudden_change else 'ok',
            'mean_range_valid': range_valid,
            'density_valid': density_valid,
            'sudden_changes_detected': sudden_change,
            'current_mean_range': current_mean if len(mean_ranges) > 0 else float('inf'),
            'current_density': avg_density if len(densities) > 0 else 0.0
        }

    def validate_imu_stream(self, imu_data):
        """Validate IMU stream characteristics"""
        if len(imu_data) < 10:
            return {'status': 'insufficient_data', 'message': 'Not enough data points'}

        # Calculate recent statistics
        recent_stats = [item['stats'] for item in imu_data[-50:]]

        # Expected ranges for IMU data
        expected_linear_accel = (8.0, 12.0)  # Should include gravity (9.81 m/s²)
        expected_angular_vel = (0.0, 10.0)  # Up to 10 rad/s is reasonable

        # Check linear acceleration (should include gravity when stationary)
        linear_accs = [stat['linear_acceleration_magnitude'] for stat in recent_stats]
        if len(linear_accs) > 0:
            current_mean = np.mean(linear_accs)
            acc_valid = expected_linear_accel[0] <= current_mean <= expected_linear_accel[1]
        else:
            acc_valid = False

        # Check angular velocity
        angular_vels = [stat['angular_velocity_magnitude'] for stat in recent_stats]
        if len(angular_vels) > 0:
            current_mean = np.mean(angular_vels)
            vel_valid = current_mean <= expected_angular_vel[1]
        else:
            vel_valid = False

        return {
            'status': 'warning' if not acc_valid or not vel_valid else 'ok',
            'linear_acceleration_valid': acc_valid,
            'angular_velocity_valid': vel_valid,
            'current_mean_acceleration': current_mean if len(linear_accs) > 0 else 0.0,
            'current_mean_angular_velocity': current_mean if len(angular_vels) > 0 else 0.0
        }

    def validate_odometry_stream(self, odom_data):
        """Validate odometry stream characteristics"""
        if len(odom_data) < 10:
            return {'status': 'insufficient_data', 'message': 'Not enough data points'}

        # Calculate recent statistics
        recent_stats = [item['stats'] for item in odom_data[-50:]]

        # Expected ranges for odometry data
        expected_linear_speed = (0.0, 2.0)  # Reasonable walking speed for humanoid
        expected_angular_speed = (0.0, 2.0)  # Reasonable turning speed

        # Check speeds
        linear_speeds = [stat['linear_speed'] for stat in recent_stats]
        angular_speeds = [stat['angular_speed'] for stat in recent_stats]

        if len(linear_speeds) > 0:
            current_mean_linear = np.mean(linear_speeds)
            linear_valid = current_mean_linear <= expected_linear_speed[1]
        else:
            linear_valid = False

        if len(angular_speeds) > 0:
            current_mean_angular = np.mean(angular_speeds)
            angular_valid = current_mean_angular <= expected_angular_speed[1]
        else:
            angular_valid = False

        return {
            'status': 'warning' if not linear_valid or not angular_valid else 'ok',
            'linear_speed_valid': linear_valid,
            'angular_speed_valid': angular_valid,
            'current_mean_linear_speed': current_mean_linear if len(linear_speeds) > 0 else 0.0,
            'current_mean_angular_speed': current_mean_angular if len(angular_speeds) > 0 else 0.0
        }

    def validate_joint_stream(self, joint_data):
        """Validate joint states stream characteristics"""
        if len(joint_data) < 10:
            return {'status': 'insufficient_data', 'message': 'Not enough data points'}

        # Calculate recent statistics
        recent_stats = [item['stats'] for item in joint_data[-50:]]

        # Expected ranges for joint data
        expected_position_range = (-10.0, 10.0)  # Reasonable joint limits
        expected_velocity_range = (-10.0, 10.0)  # Reasonable velocity limits

        # Check positions and velocities
        mean_positions = [stat['mean_position'] for stat in recent_stats]
        mean_velocities = [stat['mean_velocity'] for stat in recent_stats]

        if len(mean_positions) > 0:
            current_mean_pos = np.mean(mean_positions)
            pos_valid = expected_position_range[0] <= current_mean_pos <= expected_position_range[1]
        else:
            pos_valid = False

        if len(mean_velocities) > 0:
            current_mean_vel = np.mean(mean_velocities)
            vel_valid = expected_velocity_range[0] <= current_mean_vel <= expected_velocity_range[1]
        else:
            vel_valid = False

        return {
            'status': 'warning' if not pos_valid or not vel_valid else 'ok',
            'position_valid': pos_valid,
            'velocity_valid': vel_valid,
            'current_mean_position': current_mean_pos if len(mean_positions) > 0 else 0.0,
            'current_mean_velocity': current_mean_vel if len(mean_velocities) > 0 else 0.0
        }

    def validate_image_stream(self, image_data):
        """Validate image stream characteristics"""
        if len(image_data) < 10:
            return {'status': 'insufficient_data', 'message': 'Not enough data points'}

        # Calculate recent statistics
        recent_stats = [item['stats'] for item in image_data[-50:]]

        # Check for consistent image properties
        widths = [stat['width'] for stat in recent_stats]
        heights = [stat['height'] for stat in recent_stats]
        encodings = [stat['encoding'] for stat in recent_stats]
        size_matches = [stat['size_match'] for stat in recent_stats]

        # Validate consistency
        width_consistent = len(set(widths)) <= 1 if widths else False
        height_consistent = len(set(heights)) <= 1 if heights else False
        encoding_consistent = len(set(encodings)) <= 1 if encodings else False
        size_match_rate = np.mean(size_matches) if size_matches else 0.0
        size_match_valid = size_match_rate >= 0.95  # 95% of images should have correct size

        return {
            'status': 'warning' if not (width_consistent and height_consistent and
                                       encoding_consistent and size_match_valid) else 'ok',
            'width_consistent': width_consistent,
            'height_consistent': height_consistent,
            'encoding_consistent': encoding_consistent,
            'size_match_valid': size_match_valid,
            'current_width': widths[0] if widths else 0,
            'current_height': heights[0] if heights else 0,
            'current_encoding': encodings[0] if encodings else 'unknown'
        }

    def log_validation_results(self, validation_results):
        """Log validation results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.output_dir, f'validation_log_{timestamp}.json')

        log_entry = {
            'timestamp': rospy.Time.now().to_sec(),
            'results': validation_results
        }

        # Append to log file
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def save_comprehensive_report(self):
        """Save comprehensive validation report"""
        report = {
            'validation_session': {
                'start_time': rospy.Time.now().to_sec(),
                'output_dir': self.output_dir
            },
            'sensor_validation_results': dict(self.validation_results),
            'data_buffer_sizes': {
                sensor: len(buffer) for sensor, buffer in self.data_buffers.items()
            }
        }

        report_file = os.path.join(self.output_dir, 'comprehensive_validation_report.json')
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        rospy.loginfo(f"Comprehensive validation report saved to: {report_file}")

    def run(self):
        """Main run loop"""
        rospy.loginfo("Sensor stream validator started")
        rospy.loginfo(f"Output directory: {self.output_dir}")
        rospy.loginfo(f"Validation frequency: {self.validation_frequency} Hz")

        # Set up subscribers
        rospy.Subscriber('/scan', LaserScan, self.lidar_callback)
        rospy.Subscriber('/imu/data', Imu, self.imu_callback)
        rospy.Subscriber('/odom', Odometry, self.odometry_callback)
        rospy.Subscriber('/joint_states', JointState, self.joint_states_callback)
        rospy.Subscriber('/camera/image_raw', Image, self.image_callback)

        # Run until shutdown
        rospy.spin()

        # Save final report
        self.save_comprehensive_report()


def main():
    """Main function to run the sensor validator"""
    validator = SensorStreamValidator()

    rospy.loginfo("Sensor Stream Validation Tool initialized")
    rospy.loginfo("This tool validates that sensor data streams match expected characteristics")
    rospy.loginfo("Monitoring topics: /scan, /imu/data, /odom, /joint_states, /camera/image_raw")

    try:
        validator.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("Sensor validator interrupted")
    except KeyboardInterrupt:
        rospy.loginfo("Sensor validator interrupted by user")


if __name__ == '__main__':
    main()