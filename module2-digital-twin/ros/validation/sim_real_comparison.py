#!/usr/bin/env python3
"""
Simulation vs Reality Comparison Framework

This script provides tools for comparing simulation and real-world robot data
to validate the sim-to-real transfer quality.
"""

import rospy
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from geometry_msgs.msg import PoseStamped, Twist
from sensor_msgs.msg import LaserScan, Image, Imu
from nav_msgs.msg import Odometry
from std_msgs.msg import Float64MultiArray
import csv
import json
from datetime import datetime
import os


class SimRealComparator:
    def __init__(self):
        rospy.init_node('sim_real_comparator')

        # Storage for data
        self.sim_data = {
            'poses': [],
            'twists': [],
            'scans': [],
            'images': [],
            'imus': [],
            'timestamps': []
        }

        self.real_data = {
            'poses': [],
            'twists': [],
            'scans': [],
            'images': [],
            'imus': [],
            'timestamps': []
        }

        # Parameters
        self.sync_tolerance = rospy.Duration(0.1)  # 100ms tolerance for sync
        self.output_dir = rospy.get_param('~output_dir', '/tmp/sim_real_comparison')

        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)

        # Publishers for comparison results
        self.comparison_pub = rospy.Publisher('/sim_real_comparison', Float64MultiArray, queue_size=10)

    def add_simulation_data(self, data_type, data, timestamp):
        """Add simulation data point"""
        self.sim_data[data_type].append(data)
        self.sim_data['timestamps'].append(timestamp)

    def add_real_data(self, data_type, data, timestamp):
        """Add real-world data point"""
        self.real_data[data_type].append(data)
        self.real_data['timestamps'].append(timestamp)

    def synchronize_data(self):
        """Synchronize simulation and real data based on timestamps"""
        synced_data = {}

        for data_type in ['poses', 'twists', 'scans', 'imus']:
            if len(self.sim_data[data_type]) > 0 and len(self.real_data[data_type]) > 0:
                # Find matching timestamps
                sim_ts = self.sim_data['timestamps']
                real_ts = self.real_data['timestamps']

                # Create synced pairs
                synced_pairs = []
                sim_idx = 0
                real_idx = 0

                while sim_idx < len(sim_ts) and real_idx < len(real_ts):
                    sim_time = sim_ts[sim_idx]
                    real_time = real_ts[real_idx]

                    # Find closest timestamps within tolerance
                    if abs(sim_time - real_time) <= self.sync_tolerance.to_sec():
                        synced_pairs.append({
                            'sim': self.sim_data[data_type][sim_idx],
                            'real': self.real_data[data_type][real_idx],
                            'timestamp': (sim_time + real_time) / 2
                        })
                        sim_idx += 1
                        real_idx += 1
                    elif sim_time < real_time:
                        sim_idx += 1
                    else:
                        real_idx += 1

                synced_data[data_type] = synced_pairs

        return synced_data

    def calculate_comparison_metrics(self, synced_data):
        """Calculate comparison metrics between sim and real data"""
        metrics = {}

        # Pose comparison
        if 'poses' in synced_data and len(synced_data['poses']) > 0:
            pos_errors = []
            orient_errors = []

            for pair in synced_data['poses']:
                sim_pose = pair['sim']
                real_pose = pair['real']

                # Position error
                pos_err = np.sqrt(
                    (sim_pose.position.x - real_pose.position.x)**2 +
                    (sim_pose.position.y - real_pose.position.y)**2 +
                    (sim_pose.position.z - real_pose.position.z)**2
                )
                pos_errors.append(pos_err)

                # Orientation error (using quaternion distance)
                orient_err = self.quaternion_distance(
                    sim_pose.orientation, real_pose.orientation
                )
                orient_errors.append(orient_err)

            metrics['pose'] = {
                'position_error_mean': np.mean(pos_errors),
                'position_error_std': np.std(pos_errors),
                'position_error_max': np.max(pos_errors),
                'orientation_error_mean': np.mean(orient_errors),
                'orientation_error_std': np.std(orient_errors)
            }

        # Twist comparison
        if 'twists' in synced_data and len(synced_data['twists']) > 0:
            lin_vel_errors = []
            ang_vel_errors = []

            for pair in synced_data['twists']:
                sim_twist = pair['sim']
                real_twist = pair['real']

                # Linear velocity error
                lin_err = np.sqrt(
                    (sim_twist.linear.x - real_twist.linear.x)**2 +
                    (sim_twist.linear.y - real_twist.linear.y)**2 +
                    (sim_twist.linear.z - real_twist.linear.z)**2
                )
                lin_vel_errors.append(lin_err)

                # Angular velocity error
                ang_err = np.sqrt(
                    (sim_twist.angular.x - real_twist.angular.x)**2 +
                    (sim_twist.angular.y - real_twist.angular.y)**2 +
                    (sim_twist.angular.z - real_twist.angular.z)**2
                )
                ang_vel_errors.append(ang_err)

            metrics['twist'] = {
                'linear_velocity_error_mean': np.mean(lin_vel_errors),
                'angular_velocity_error_mean': np.mean(ang_vel_errors),
                'linear_velocity_error_std': np.std(lin_vel_errors),
                'angular_velocity_error_std': np.std(ang_vel_errors)
            }

        # LiDAR scan comparison
        if 'scans' in synced_data and len(synced_data['scans']) > 0:
            scan_errors = []

            for pair in synced_data['scans']:
                sim_scan = pair['sim']
                real_scan = pair['real']

                # Calculate scan similarity (Hausdorff distance or similar)
                error = self.scan_similarity(sim_scan, real_scan)
                scan_errors.append(error)

            metrics['scan'] = {
                'scan_similarity_mean': np.mean(scan_errors),
                'scan_similarity_std': np.std(scan_errors)
            }

        # IMU comparison
        if 'imus' in synced_data and len(synced_data['imus']) > 0:
            accel_errors = []
            gyro_errors = []

            for pair in synced_data['imus']:
                sim_imu = pair['sim']
                real_imu = pair['real']

                # Acceleration error
                accel_err = np.sqrt(
                    (sim_imu.linear_acceleration.x - real_imu.linear_acceleration.x)**2 +
                    (sim_imu.linear_acceleration.y - real_imu.linear_acceleration.y)**2 +
                    (sim_imu.linear_acceleration.z - real_imu.linear_acceleration.z)**2
                )
                accel_errors.append(accel_err)

                # Angular velocity error
                gyro_err = np.sqrt(
                    (sim_imu.angular_velocity.x - real_imu.angular_velocity.x)**2 +
                    (sim_imu.angular_velocity.y - real_imu.angular_velocity.y)**2 +
                    (sim_imu.angular_velocity.z - real_imu.angular_velocity.z)**2
                )
                gyro_errors.append(gyro_err)

            metrics['imu'] = {
                'acceleration_error_mean': np.mean(accel_errors),
                'gyro_error_mean': np.mean(gyro_errors),
                'acceleration_error_std': np.std(accel_errors),
                'gyro_error_std': np.std(gyro_errors)
            }

        return metrics

    def quaternion_distance(self, q1, q2):
        """Calculate distance between two quaternions"""
        # Dot product
        dot_product = (q1.w * q2.w + q1.x * q2.x + q1.y * q2.y + q1.z * q2.z)
        # Distance (smaller is closer)
        return 1 - abs(dot_product)

    def scan_similarity(self, scan1, scan2):
        """Calculate similarity between two LiDAR scans"""
        # This is a simplified version - in practice, you'd use more sophisticated methods
        # like Hausdorff distance, Chamfer distance, or ICP-based comparison

        # For now, calculate simple point-wise distance
        if len(scan1.ranges) != len(scan2.ranges):
            return float('inf')

        differences = []
        for r1, r2 in zip(scan1.ranges, scan2.ranges):
            if np.isfinite(r1) and np.isfinite(r2):
                differences.append(abs(r1 - r2))

        if differences:
            return np.mean(differences)
        else:
            return 0.0

    def run_comparison(self):
        """Run the complete comparison process"""
        rospy.loginfo("Starting simulation vs reality comparison...")

        # Synchronize data
        rospy.loginfo("Synchronizing simulation and real data...")
        synced_data = self.synchronize_data()

        # Calculate metrics
        rospy.loginfo("Calculating comparison metrics...")
        metrics = self.calculate_comparison_metrics(synced_data)

        # Generate reports
        rospy.loginfo("Generating reports...")
        self.generate_report(metrics, synced_data)

        # Publish results
        self.publish_results(metrics)

        rospy.loginfo("Comparison completed. Results saved to: {}".format(self.output_dir))

        return metrics

    def generate_report(self, metrics, synced_data):
        """Generate comprehensive comparison report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'data_counts': {
                'sim': {k: len(v) for k, v in self.sim_data.items()},
                'real': {k: len(v) for k, v in self.real_data.items()}
            },
            'synced_pairs': {k: len(v) for k, v in synced_data.items() if isinstance(v, list)}
        }

        # Save detailed report
        report_path = os.path.join(self.output_dir, 'comparison_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        # Generate summary statistics
        summary_path = os.path.join(self.output_dir, 'comparison_summary.txt')
        with open(summary_path, 'w') as f:
            f.write("SIMULATION vs REALITY COMPARISON REPORT\n")
            f.write("=" * 50 + "\n")
            f.write(f"Timestamp: {report['timestamp']}\n\n")

            f.write("POSE COMPARISON:\n")
            if 'pose' in metrics:
                pose_metrics = metrics['pose']
                f.write(f"  Position Error - Mean: {pose_metrics['position_error_mean']:.3f}m, "
                        f"Std: {pose_metrics['position_error_std']:.3f}m, "
                        f"Max: {pose_metrics['position_error_max']:.3f}m\n")
                f.write(f"  Orientation Error - Mean: {pose_metrics['orientation_error_mean']:.3f}, "
                        f"Std: {pose_metrics['orientation_error_std']:.3f}\n")
            else:
                f.write("  No pose data available\n")

            f.write("\nTWIST COMPARISON:\n")
            if 'twist' in metrics:
                twist_metrics = metrics['twist']
                f.write(f"  Linear Velocity Error - Mean: {twist_metrics['linear_velocity_error_mean']:.3f}m/s\n")
                f.write(f"  Angular Velocity Error - Mean: {twist_metrics['angular_velocity_error_mean']:.3f}rad/s\n")
            else:
                f.write("  No twist data available\n")

            f.write("\nSCAN COMPARISON:\n")
            if 'scan' in metrics:
                scan_metrics = metrics['scan']
                f.write(f"  Scan Similarity - Mean: {scan_metrics['scan_similarity_mean']:.3f}m\n")
            else:
                f.write("  No scan data available\n")

            f.write("\nIMU COMPARISON:\n")
            if 'imu' in metrics:
                imu_metrics = metrics['imu']
                f.write(f"  Acceleration Error - Mean: {imu_metrics['acceleration_error_mean']:.3f}m/s²\n")
                f.write(f"  Gyro Error - Mean: {imu_metrics['gyro_error_mean']:.3f}rad/s\n")
            else:
                f.write("  No IMU data available\n")

            f.write(f"\nDATA SUMMARY:\n")
            f.write(f"  Simulation: {report['data_counts']['sim']}\n")
            f.write(f"  Real: {report['data_counts']['real']}\n")
            f.write(f"  Synced: {report['synced_pairs']}\n")

        # Generate visualizations
        self.generate_visualizations(synced_data)

    def generate_visualizations(self, synced_data):
        """Generate visualizations of the comparison"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))

        # Plot 1: Position errors over time (if poses are available)
        if 'poses' in synced_data and len(synced_data['poses']) > 0:
            pos_errors = []
            timestamps = []

            for pair in synced_data['poses']:
                sim_pose = pair['sim']
                real_pose = pair['real']

                pos_err = np.sqrt(
                    (sim_pose.position.x - real_pose.position.x)**2 +
                    (sim_pose.position.y - real_pose.position.y)**2 +
                    (sim_pose.position.z - real_pose.position.z)**2
                )
                pos_errors.append(pos_err)
                timestamps.append(pair['timestamp'])

            axes[0, 0].plot(timestamps, pos_errors)
            axes[0, 0].set_title('Position Error Over Time')
            axes[0, 0].set_xlabel('Time')
            axes[0, 0].set_ylabel('Position Error (m)')
            axes[0, 0].grid(True)

        # Plot 2: Velocity errors (if twists are available)
        if 'twists' in synced_data and len(synced_data['twists']) > 0:
            lin_vel_errors = []
            ang_vel_errors = []
            timestamps = []

            for pair in synced_data['twists']:
                sim_twist = pair['sim']
                real_twist = pair['real']

                lin_err = np.sqrt(
                    (sim_twist.linear.x - real_twist.linear.x)**2 +
                    (sim_twist.linear.y - real_twist.linear.y)**2 +
                    (sim_twist.linear.z - real_twist.linear.z)**2
                )
                ang_err = np.sqrt(
                    (sim_twist.angular.x - real_twist.angular.x)**2 +
                    (sim_twist.angular.y - real_twist.angular.y)**2 +
                    (sim_twist.angular.z - real_twist.angular.z)**2
                )
                lin_vel_errors.append(lin_err)
                ang_vel_errors.append(ang_err)
                timestamps.append(pair['timestamp'])

            axes[0, 1].plot(timestamps, lin_vel_errors, label='Linear', alpha=0.7)
            axes[0, 1].plot(timestamps, ang_vel_errors, label='Angular', alpha=0.7)
            axes[0, 1].set_title('Velocity Errors Over Time')
            axes[0, 1].set_xlabel('Time')
            axes[0, 1].set_ylabel('Velocity Error (m/s, rad/s)')
            axes[0, 1].legend()
            axes[0, 1].grid(True)

        # Plot 3: Error distributions
        if 'poses' in synced_data and len(synced_data['poses']) > 0:
            pos_errors = []
            for pair in synced_data['poses']:
                sim_pose = pair['sim']
                real_pose = pair['real']
                pos_err = np.sqrt(
                    (sim_pose.position.x - real_pose.position.x)**2 +
                    (sim_pose.position.y - real_pose.position.y)**2 +
                    (sim_pose.position.z - real_pose.position.z)**2
                )
                pos_errors.append(pos_err)

            axes[1, 0].hist(pos_errors, bins=50, alpha=0.7)
            axes[1, 0].set_title('Position Error Distribution')
            axes[1, 0].set_xlabel('Position Error (m)')
            axes[1, 0].set_ylabel('Frequency')
            axes[1, 0].grid(True)

        # Plot 4: Correlation plot (if enough data)
        if 'poses' in synced_data and len(synced_data['poses']) > 10:
            sim_pos_x = [pair['sim'].position.x for pair in synced_data['poses']]
            real_pos_x = [pair['real'].position.x for pair in synced_data['poses']]

            axes[1, 1].scatter(sim_pos_x, real_pos_x, alpha=0.5)
            min_val = min(min(sim_pos_x), min(real_pos_x))
            max_val = max(max(sim_pos_x), max(real_pos_x))
            axes[1, 1].plot([min_val, max_val], [min_val, max_val], 'r--', label='Perfect Match')
            axes[1, 1].set_title('X Position Correlation: Sim vs Real')
            axes[1, 1].set_xlabel('Simulation X (m)')
            axes[1, 1].set_ylabel('Reality X (m)')
            axes[1, 1].legend()
            axes[1, 1].grid(True)

        plt.tight_layout()
        viz_path = os.path.join(self.output_dir, 'comparison_visualizations.png')
        plt.savefig(viz_path)
        plt.close()

    def publish_results(self, metrics):
        """Publish comparison results"""
        result_msg = Float64MultiArray()

        # Flatten metrics into array for publication
        flat_metrics = []
        for category, values in metrics.items():
            for key, value in values.items():
                if isinstance(value, (int, float)):
                    flat_metrics.append(float(value))

        result_msg.data = flat_metrics
        self.comparison_pub.publish(result_msg)


def main():
    """Main function to run the comparator"""
    comparator = SimRealComparator()

    # In a real scenario, you would subscribe to both simulation and real topics
    # For this example, we'll simulate data collection

    # Example: Add some simulated data
    # In practice, this would come from subscribing to ROS topics

    rospy.loginfo("Sim-to-real comparison node initialized")
    rospy.loginfo("This node compares simulation and real-world robot data")
    rospy.loginfo("Results will be saved to: {}".format(comparator.output_dir))

    # Wait for data (in a real scenario, you'd collect data for some time)
    rospy.sleep(5.0)

    # Run comparison
    try:
        results = comparator.run_comparison()
        rospy.loginfo("Comparison completed successfully")
    except Exception as e:
        rospy.logerr("Error during comparison: {}".format(str(e)))


if __name__ == '__main__':
    main()