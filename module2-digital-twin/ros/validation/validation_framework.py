#!/usr/bin/env python3
"""
Comprehensive Validation Framework for Sim-to-Real Transfer

This script provides a complete framework for validating simulation-to-reality transfer
including data collection, comparison, and comprehensive reporting.
"""

import rospy
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy import stats
from geometry_msgs.msg import PoseStamped, Twist
from sensor_msgs.msg import LaserScan, Image, Imu
from nav_msgs.msg import Odometry
from std_msgs.msg import Float64MultiArray, String
import json
import csv
import os
from datetime import datetime
import pickle
from sklearn.metrics import mean_squared_error, mean_absolute_error
from collections import defaultdict
import threading
import time


class ValidationFramework:
    def __init__(self):
        rospy.init_node('validation_framework')

        # Configuration
        self.config = {
            'collection_duration': rospy.get_param('~collection_duration', 60.0),  # seconds
            'validation_frequency': rospy.get_param('~validation_frequency', 0.1),  # Hz
            'output_dir': rospy.get_param('~output_dir', '/tmp/validation_framework'),
            'sim_prefix': rospy.get_param('~sim_prefix', '/sim'),
            'real_prefix': rospy.get_param('~real_prefix', '/real'),
            'metrics': [
                'mse', 'mae', 'rmse', 'correlation', 'kl_divergence',
                'ks_test', 'dtw_distance', 'cosine_similarity'
            ]
        }

        # Create output directory
        os.makedirs(self.config['output_dir'], exist_ok=True)

        # Data storage
        self.data = {
            'sim': defaultdict(list),
            'real': defaultdict(list)
        }

        # Validation results
        self.results = {
            'metrics': defaultdict(dict),
            'plots': [],
            'reports': []
        }

        # Publishers
        self.status_pub = rospy.Publisher('/validation/status', String, queue_size=10)
        self.results_pub = rospy.Publisher('/validation/results', String, queue_size=10)

        # Threading lock
        self.lock = threading.Lock()

        # Timers
        self.collection_start_time = None
        self.collection_timer = None

    def start_data_collection(self):
        """Start collecting data from both simulation and real systems"""
        rospy.loginfo("Starting data collection...")

        self.collection_start_time = rospy.Time.now()

        # Set up subscribers for simulation data
        rospy.Subscriber(f"{self.config['sim_prefix']}/scan", LaserScan, self.sim_lidar_callback)
        rospy.Subscriber(f"{self.config['sim_prefix']}/imu/data", Imu, self.sim_imu_callback)
        rospy.Subscriber(f"{self.config['sim_prefix']}/odom", Odometry, self.sim_odom_callback)
        rospy.Subscriber(f"{self.config['sim_prefix']}/cmd_vel", Twist, self.sim_cmd_vel_callback)

        # Set up subscribers for real data
        rospy.Subscriber(f"{self.config['real_prefix']}/scan", LaserScan, self.real_lidar_callback)
        rospy.Subscriber(f"{self.config['real_prefix']}/imu/data", Imu, self.real_imu_callback)
        rospy.Subscriber(f"{self.config['real_prefix']}/odom", Odometry, self.real_odom_callback)
        rospy.Subscriber(f"{self.config['real_prefix']}/cmd_vel", Twist, self.real_cmd_vel_callback)

        # Set up collection timer
        self.collection_timer = rospy.Timer(
            rospy.Duration(self.config['collection_duration']),
            self.stop_data_collection,
            oneshot=True
        )

    def stop_data_collection(self, event):
        """Stop data collection and start validation"""
        rospy.loginfo("Data collection completed. Starting validation...")

        # Unsubscribe from all topics
        self.unsubscribe_all()

        # Run validation
        self.run_validation()

    def unsubscribe_all(self):
        """Unsubscribe from all validation topics"""
        # This would involve unsubscribing from all subscribers
        # For simplicity, we'll just stop the timer
        if self.collection_timer:
            self.collection_timer.shutdown()

    def sim_lidar_callback(self, msg):
        """Process simulation LiDAR data"""
        with self.lock:
            self.data['sim']['lidar'].append({
                'timestamp': rospy.Time.now(),
                'ranges': np.array(msg.ranges),
                'intensities': np.array(msg.intensities) if msg.intensities else None
            })

    def real_lidar_callback(self, msg):
        """Process real LiDAR data"""
        with self.lock:
            self.data['real']['lidar'].append({
                'timestamp': rospy.Time.now(),
                'ranges': np.array(msg.ranges),
                'intensities': np.array(msg.intensities) if msg.intensities else None
            })

    def sim_imu_callback(self, msg):
        """Process simulation IMU data"""
        with self.lock:
            self.data['sim']['imu'].append({
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
                ]
            })

    def real_imu_callback(self, msg):
        """Process real IMU data"""
        with self.lock:
            self.data['real']['imu'].append({
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
                ]
            })

    def sim_odom_callback(self, msg):
        """Process simulation odometry data"""
        with self.lock:
            self.data['sim']['odometry'].append({
                'timestamp': rospy.Time.now(),
                'position': [
                    msg.pose.pose.position.x,
                    msg.pose.pose.position.y,
                    msg.pose.pose.position.z
                ],
                'orientation': [
                    msg.pose.pose.orientation.x,
                    msg.pose.pose.orientation.y,
                    msg.pose.pose.orientation.z,
                    msg.pose.pose.orientation.w
                ],
                'linear_velocity': [
                    msg.twist.twist.linear.x,
                    msg.twist.twist.linear.y,
                    msg.twist.twist.linear.z
                ],
                'angular_velocity': [
                    msg.twist.twist.angular.x,
                    msg.twist.twist.angular.y,
                    msg.twist.twist.angular.z
                ]
            })

    def real_odom_callback(self, msg):
        """Process real odometry data"""
        with self.lock:
            self.data['real']['odometry'].append({
                'timestamp': rospy.Time.now(),
                'position': [
                    msg.pose.pose.position.x,
                    msg.pose.pose.position.y,
                    msg.pose.pose.position.z
                ],
                'orientation': [
                    msg.pose.pose.orientation.x,
                    msg.pose.pose.orientation.y,
                    msg.pose.pose.orientation.z,
                    msg.pose.pose.orientation.w
                ],
                'linear_velocity': [
                    msg.twist.twist.linear.x,
                    msg.twist.twist.linear.y,
                    msg.twist.twist.linear.z
                ],
                'angular_velocity': [
                    msg.twist.twist.angular.x,
                    msg.twist.twist.angular.y,
                    msg.twist.twist.angular.z
                ]
            })

    def sim_cmd_vel_callback(self, msg):
        """Process simulation command velocity"""
        with self.lock:
            self.data['sim']['cmd_vel'].append({
                'timestamp': rospy.Time.now(),
                'linear': msg.linear.x,
                'angular': msg.angular.z
            })

    def real_cmd_vel_callback(self, msg):
        """Process real command velocity"""
        with self.lock:
            self.data['real']['cmd_vel'].append({
                'timestamp': rospy.Time.now(),
                'linear': msg.linear.x,
                'angular': msg.angular.z
            })

    def run_validation(self):
        """Run comprehensive validation on collected data"""
        rospy.loginfo("Running comprehensive validation...")

        # Calculate metrics for each data type
        for data_type in self.data['sim'].keys():
            if data_type in self.data['real'] and len(self.data['sim'][data_type]) > 0 and len(self.data['real'][data_type]) > 0:
                self.validate_data_type(data_type)

        # Generate reports and visualizations
        self.generate_comprehensive_report()
        self.generate_visualizations()

        # Save results
        self.save_results()

        # Publish final status
        self.publish_final_results()

        rospy.loginfo("Validation completed successfully!")

    def validate_data_type(self, data_type):
        """Validate a specific data type"""
        sim_data = self.data['sim'][data_type]
        real_data = self.data['real'][data_type]

        # Align data by timestamps
        aligned_sim, aligned_real = self.align_data_by_time(sim_data, real_data)

        if len(aligned_sim) == 0 or len(aligned_real) == 0:
            rospy.logwarn(f"No aligned data for {data_type}, skipping validation")
            return

        # Calculate various metrics
        metrics = {}

        # Calculate metrics for different fields in the data
        for field in aligned_sim[0].keys():
            if field != 'timestamp':  # Skip timestamp field
                sim_values = [item[field] for item in aligned_sim]
                real_values = [item[field] for item in aligned_real]

                # Convert to numpy arrays for processing
                if isinstance(sim_values[0], (list, tuple)):
                    # Handle vector fields
                    sim_array = np.array(sim_values)
                    real_array = np.array(real_values)

                    if sim_array.shape == real_array.shape:
                        metrics[field] = self.calculate_vector_metrics(sim_array, real_array)
                    else:
                        rospy.logwarn(f"Shape mismatch for {data_type}.{field}: {sim_array.shape} vs {real_array.shape}")
                        continue
                else:
                    # Handle scalar fields
                    sim_array = np.array(sim_values)
                    real_array = np.array(real_values)

                    metrics[field] = self.calculate_scalar_metrics(sim_array, real_array)

        self.results['metrics'][data_type] = metrics

    def align_data_by_time(self, sim_data, real_data, max_time_diff=0.1):
        """Align simulation and real data by timestamps"""
        aligned_sim = []
        aligned_real = []

        sim_idx = 0
        real_idx = 0

        while sim_idx < len(sim_data) and real_idx < len(real_data):
            sim_time = sim_data[sim_idx]['timestamp']
            real_time = real_data[real_idx]['timestamp']

            time_diff = abs(sim_time.to_sec() - real_time.to_sec())

            if time_diff <= max_time_diff:
                # Times are close enough, align them
                aligned_sim.append(sim_data[sim_idx])
                aligned_real.append(real_data[real_idx])
                sim_idx += 1
                real_idx += 1
            elif sim_time < real_time:
                sim_idx += 1
            else:
                real_idx += 1

        return aligned_sim, aligned_real

    def calculate_scalar_metrics(self, sim_values, real_values):
        """Calculate metrics for scalar values"""
        if len(sim_values) != len(real_values):
            rospy.logwarn(f"Length mismatch in scalar metrics: {len(sim_values)} vs {len(real_values)}")
            return {}

        # Ensure we have valid values
        mask = ~(np.isnan(sim_values) | np.isnan(real_values) | np.isinf(sim_values) | np.isinf(real_values))
        sim_filtered = sim_values[mask]
        real_filtered = real_values[mask]

        if len(sim_filtered) == 0:
            return {'error': 'no_valid_data'}

        metrics = {}

        # MSE and RMSE
        mse = mean_squared_error(real_filtered, sim_filtered)
        rmse = np.sqrt(mse)

        # MAE
        mae = mean_absolute_error(real_filtered, sim_filtered)

        # Correlation
        if len(sim_filtered) > 1:
            correlation, p_value = stats.pearsonr(sim_filtered, real_filtered)
        else:
            correlation = 0.0
            p_value = 1.0

        # KS test for distribution similarity
        ks_stat, ks_p_value = stats.ks_2samp(sim_filtered, real_filtered)

        # Cosine similarity
        cosine_sim = np.dot(sim_filtered, real_filtered) / (
            np.linalg.norm(sim_filtered) * np.linalg.norm(real_filtered)
        )

        metrics.update({
            'mse': float(mse),
            'rmse': float(rmse),
            'mae': float(mae),
            'correlation': float(correlation),
            'correlation_p_value': float(p_value),
            'ks_statistic': float(ks_stat),
            'ks_p_value': float(ks_p_value),
            'cosine_similarity': float(cosine_sim),
            'sample_size': int(len(sim_filtered))
        })

        return metrics

    def calculate_vector_metrics(self, sim_vectors, real_vectors):
        """Calculate metrics for vector values"""
        if sim_vectors.shape != real_vectors.shape:
            return {'error': 'shape_mismatch'}

        metrics = {}

        # Calculate metrics for each component
        for i in range(sim_vectors.shape[1]):  # Assuming 2nd dimension is vector components
            comp_sim = sim_vectors[:, i]
            comp_real = real_vectors[:, i]

            comp_metrics = self.calculate_scalar_metrics(comp_sim, comp_real)
            metrics[f'component_{i}'] = comp_metrics

        # Calculate overall vector metrics
        if sim_vectors.ndim == 2:  # Multiple vectors
            # MSE of vector magnitudes
            sim_magnitudes = np.linalg.norm(sim_vectors, axis=1)
            real_magnitudes = np.linalg.norm(real_vectors, axis=1)

            magnitude_mse = mean_squared_error(real_magnitudes, sim_magnitudes)
            metrics['magnitude_mse'] = float(magnitude_mse)

        return metrics

    def generate_comprehensive_report(self):
        """Generate comprehensive validation report"""
        report = {
            'validation_summary': {
                'timestamp': datetime.now().isoformat(),
                'duration': (rospy.Time.now() - self.collection_start_time).to_sec() if self.collection_start_time else 0,
                'data_types': list(self.results['metrics'].keys()),
                'total_sim_data_points': sum(len(self.data['sim'][dt]) for dt in self.data['sim'].keys()),
                'total_real_data_points': sum(len(self.data['real'][dt]) for dt in self.data['real'].keys())
            },
            'detailed_metrics': dict(self.results['metrics']),
            'validation_quality': self.assess_validation_quality()
        }

        self.results['reports'].append(report)

    def assess_validation_quality(self):
        """Assess overall validation quality"""
        quality_assessment = {}

        for data_type, metrics in self.results['metrics'].items():
            if 'error' in metrics:
                quality_assessment[data_type] = 'failed'
                continue

            # Assess quality based on correlation and error metrics
            overall_quality = 'unknown'

            # Look for correlation metric
            correlation = None
            mse = None

            for field, field_metrics in metrics.items():
                if isinstance(field_metrics, dict):
                    if 'correlation' in field_metrics:
                        correlation = field_metrics['correlation']
                    if 'mse' in field_metrics:
                        mse = field_metrics['mse']

            if correlation is not None:
                if correlation > 0.9:
                    overall_quality = 'excellent'
                elif correlation > 0.8:
                    overall_quality = 'good'
                elif correlation > 0.6:
                    overall_quality = 'fair'
                else:
                    overall_quality = 'poor'
            elif mse is not None:
                # Assess based on MSE (lower is better)
                if mse < 0.01:
                    overall_quality = 'excellent'
                elif mse < 0.1:
                    overall_quality = 'good'
                elif mse < 1.0:
                    overall_quality = 'fair'
                else:
                    overall_quality = 'poor'

            quality_assessment[data_type] = overall_quality

        return quality_assessment

    def generate_visualizations(self):
        """Generate validation visualizations"""
        # Create figure with subplots
        n_plots = len(self.results['metrics'])
        if n_plots == 0:
            return

        fig, axes = plt.subplots(n_plots, 2, figsize=(15, 5*n_plots))
        if n_plots == 1:
            axes = axes.reshape(1, -1)

        for idx, (data_type, metrics) in enumerate(self.results['metrics'].items()):
            # Plot 1: Time series comparison
            if data_type in self.data['sim'] and data_type in self.data['real']:
                sim_data = self.data['sim'][data_type]
                real_data = self.data['real'][data_type]

                # Align data for plotting
                aligned_sim, aligned_real = self.align_data_by_time(sim_data, real_data)

                if len(aligned_sim) > 0:
                    # Extract a representative field for plotting (first non-timestamp field)
                    plot_fields = [f for f in aligned_sim[0].keys() if f != 'timestamp']

                    if plot_fields:
                        field_to_plot = plot_fields[0]

                        # Handle vector fields by plotting first component
                        if isinstance(aligned_sim[0][field_to_plot], (list, tuple)):
                            sim_values = [item[field_to_plot][0] if len(item[field_to_plot]) > 0 else 0 for item in aligned_sim]
                            real_values = [item[field_to_plot][0] if len(item[field_to_plot]) > 0 else 0 for item in aligned_real]
                        else:
                            sim_values = [item[field_to_plot] for item in aligned_sim]
                            real_values = [item[field_to_plot] for item in aligned_real]

                        # Convert to numpy arrays and handle NaN/infs
                        sim_values = np.array(sim_values)
                        real_values = np.array(real_values)
                        mask = ~(np.isnan(sim_values) | np.isnan(real_values) | np.isinf(sim_values) | np.isinf(real_values))
                        sim_clean = sim_values[mask]
                        real_clean = real_values[mask]
                        time_stamps = [aligned_sim[i]['timestamp'].to_sec() for i in range(len(aligned_sim)) if mask[i]]

                        axes[idx, 0].plot(time_stamps, sim_clean, label=f'{data_type} Sim', alpha=0.7)
                        axes[idx, 0].plot(time_stamps, real_clean, label=f'{data_type} Real', alpha=0.7)
                        axes[idx, 0].set_title(f'{data_type} - Time Series Comparison')
                        axes[idx, 0].set_xlabel('Time (s)')
                        axes[idx, 0].set_ylabel(field_to_plot)
                        axes[idx, 0].legend()
                        axes[idx, 0].grid(True)

            # Plot 2: Scatter plot showing correlation
            if len(sim_clean) > 0 and len(real_clean) > 0:
                axes[idx, 1].scatter(sim_clean, real_clean, alpha=0.5)

                # Add identity line
                min_val = min(min(sim_clean), min(real_clean))
                max_val = max(max(sim_clean), max(real_clean))
                axes[idx, 1].plot([min_val, max_val], [min_val, max_val], 'r--', label='Perfect Match')

                axes[idx, 1].set_title(f'{data_type} - Correlation Plot')
                axes[idx, 1].set_xlabel(f'Simulation {field_to_plot}')
                axes[idx, 1].set_ylabel(f'Real {field_to_plot}')
                axes[idx, 1].legend()
                axes[idx, 1].grid(True)

        plt.tight_layout()

        # Save plot
        plot_path = os.path.join(self.config['output_dir'], 'validation_visualizations.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()

        self.results['plots'].append(plot_path)

    def save_results(self):
        """Save validation results to files"""
        # Save metrics
        metrics_path = os.path.join(self.config['output_dir'], 'validation_metrics.json')
        with open(metrics_path, 'w') as f:
            json.dump(dict(self.results['metrics']), f, indent=2, default=float)

        # Save comprehensive report
        report_path = os.path.join(self.config['output_dir'], 'comprehensive_report.json')
        with open(report_path, 'w') as f:
            json.dump(self.results['reports'][-1] if self.results['reports'] else {}, f, indent=2)

        # Save raw data (careful with large datasets)
        data_path = os.path.join(self.config['output_dir'], 'raw_validation_data.pkl')
        with open(data_path, 'wb') as f:
            pickle.dump(dict(self.data), f)

        rospy.loginfo(f"Results saved to: {self.config['output_dir']}")

    def publish_final_results(self):
        """Publish final validation results"""
        results_msg = String()
        results_msg.data = json.dumps({
            'timestamp': rospy.Time.now().to_sec(),
            'summary': self.results['reports'][-1]['validation_summary'] if self.results['reports'] else {},
            'quality_assessment': self.results['reports'][-1]['validation_quality'] if self.results['reports'] else {}
        })
        self.results_pub.publish(results_msg)

        # Publish status
        status_msg = String()
        overall_quality = 'unknown'
        if self.results['reports']:
            quality_counts = {}
            for dt, quality in self.results['reports'][-1]['validation_quality'].items():
                quality_counts[quality] = quality_counts.get(quality, 0) + 1

            if quality_counts.get('poor', 0) > 0:
                overall_quality = 'poor'
            elif quality_counts.get('fair', 0) > 0:
                overall_quality = 'fair'
            elif quality_counts.get('good', 0) > 0:
                overall_quality = 'good'
            elif quality_counts.get('excellent', 0) > 0:
                overall_quality = 'excellent'

        status_msg.data = f"VALIDATION_COMPLETE:{overall_quality}"
        self.status_pub.publish(status_msg)

    def run_validation_cycle(self):
        """Run a complete validation cycle"""
        rospy.loginfo("Starting validation framework...")

        # Start data collection
        self.start_data_collection()

        # Wait for collection to complete
        collection_duration = self.config['collection_duration']
        rospy.sleep(collection_duration + 5)  # Extra time for processing

        # If validation hasn't run automatically, run it now
        if not self.results['metrics']:
            self.run_validation()


def main():
    """Main function to run the validation framework"""
    framework = ValidationFramework()

    rospy.loginfo("Comprehensive Validation Framework initialized")
    rospy.loginfo(f"Collection duration: {framework.config['collection_duration']} seconds")
    rospy.loginfo(f"Output directory: {framework.config['output_dir']}")
    rospy.loginfo(f"Simulation prefix: {framework.config['sim_prefix']}")
    rospy.loginfo(f"Real prefix: {framework.config['real_prefix']}")

    try:
        framework.run_validation_cycle()
    except rospy.ROSInterruptException:
        rospy.loginfo("Validation framework interrupted")
    except KeyboardInterrupt:
        rospy.loginfo("Validation framework interrupted by user")
    except Exception as e:
        rospy.logerr(f"Error in validation framework: {e}")


if __name__ == '__main__':
    main()