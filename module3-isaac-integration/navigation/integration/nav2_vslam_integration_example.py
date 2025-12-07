#!/usr/bin/env python3
"""
Example integration of Nav2 with VSLAM for humanoid robot navigation
This example demonstrates how to combine visual SLAM with Nav2 for enhanced navigation
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav_msgs.msg import Odometry, Path
from sensor_msgs.msg import Image, Imu
from tf2_ros import TransformListener, Buffer
import numpy as np
import threading
import time
from collections import deque


class Nav2VSLAMIntegrationExample(Node):
    """
    Example node demonstrating integration between Nav2 and VSLAM
    for enhanced humanoid robot navigation
    """

    def __init__(self):
        super().__init__('nav2_vslam_integration_example')

        # Initialize components
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Navigation state
        self.current_pose = None
        self.vslam_pose = None
        self.nav2_pose = None
        self.fused_pose = None

        # Integration parameters
        self.vslam_weight = 0.7
        self.nav2_weight = 0.3
        self.max_pose_difference = 0.5  # meters
        self.enable_sensor_fusion = True

        # Data queues for synchronization
        self.vslam_queue = deque(maxlen=10)
        self.nav2_queue = deque(maxlen=10)
        self.imu_queue = deque(maxlen=10)

        # Publishers
        self.fused_pose_pub = self.create_publisher(
            PoseWithCovarianceStamped, '/fused_localization/pose', 10
        )
        self.debug_path_pub = self.create_publisher(
            Path, '/integration_debug/path', 10
        )

        # Subscribers with appropriate QoS for real-time data
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5
        )

        # VSLAM pose subscription
        self.vslam_pose_sub = self.create_subscription(
            PoseStamped, '/vslam/pose', self.vslam_pose_callback, 10
        )

        # Nav2 pose subscription (could be from AMCL or other localizer)
        self.nav2_pose_sub = self.create_subscription(
            PoseWithCovarianceStamped, '/amcl_pose', self.nav2_pose_callback, 10
        )

        # IMU for additional sensor fusion
        self.imu_sub = self.create_subscription(
            Imu, '/imu/data', self.imu_callback, 10
        )

        # Robot odometry
        self.odom_sub = self.create_subscription(
            Odometry, '/odom', self.odom_callback, 10
        )

        # Integration timer
        self.integration_timer = self.create_timer(0.05, self.integrate_poses)  # 20 Hz

        # Path recording for debugging
        self.recorded_path = []
        self.path_timer = self.create_timer(0.1, self.record_path)

        self.get_logger().info("Nav2-VSLAM Integration Example node initialized")

    def vslam_pose_callback(self, msg):
        """Handle VSLAM pose updates"""
        self.vslam_pose = msg
        self.vslam_queue.append(msg)

        # Store for fusion
        self.get_logger().debug(f"Received VSLAM pose: ({msg.pose.position.x:.2f}, {msg.pose.position.y:.2f})")

    def nav2_pose_callback(self, msg):
        """Handle Nav2 pose updates (e.g., from AMCL)"""
        self.nav2_pose = msg
        self.nav2_queue.append(msg)

        # Store for fusion
        self.get_logger().debug(f"Received Nav2 pose: ({msg.pose.pose.position.x:.2f}, {msg.pose.pose.position.y:.2f})")

    def imu_callback(self, msg):
        """Handle IMU data for additional sensor fusion"""
        self.imu_queue.append(msg)

    def odom_callback(self, msg):
        """Handle odometry data"""
        self.current_pose = msg.pose.pose
        self.odom_stamp = msg.header.stamp

    def integrate_poses(self):
        """Integrate VSLAM and Nav2 poses"""
        if not self.vslam_pose or not self.nav2_pose:
            return

        # Check if poses are reasonably consistent
        vslam_pos = np.array([
            self.vslam_pose.pose.position.x,
            self.vslam_pose.pose.position.y,
            self.vslam_pose.pose.position.z
        ])

        nav2_pos = np.array([
            self.nav2_pose.pose.pose.position.x,
            self.nav2_pose.pose.pose.position.y,
            self.nav2_pose.pose.pose.position.z
        ])

        distance_diff = np.linalg.norm(vslam_pos - nav2_pos)

        if distance_diff > self.max_pose_difference:
            self.get_logger().warn(
                f"Pose difference too large: {distance_diff:.2f}m, "
                f"VSLAM:({vslam_pos}), Nav2:({nav2_pos})"
            )
            # Use Nav2 pose as fallback since it's typically more reliable for navigation
            fused_pose = self.nav2_pose.pose.pose
        else:
            # Fuse poses using weighted average
            fused_pose = self.fuse_poses_weighted(
                self.vslam_pose.pose,
                self.nav2_pose.pose.pose,
                self.vslam_weight,
                self.nav2_weight
            )

        # Create and publish fused pose
        fused_pose_msg = PoseWithCovarianceStamped()
        fused_pose_msg.header.stamp = self.get_clock().now().to_msg()
        fused_pose_msg.header.frame_id = "map"
        fused_pose_msg.pose.pose = fused_pose
        fused_pose_msg.pose.covariance = self.calculate_fused_covariance()

        self.fused_pose = fused_pose_msg
        self.fused_pose_pub.publish(fused_pose_msg)

        self.get_logger().debug(f"Fused pose published: ({fused_pose.position.x:.2f}, {fused_pose.position.y:.2f})")

    def fuse_poses_weighted(self, vslam_pose, nav2_pose, vslam_weight, nav2_weight):
        """Fuse two poses using weighted average"""
        fused_pose = PoseStamped().pose  # Create empty pose

        # Weighted average for position
        total_weight = vslam_weight + nav2_weight
        fused_pose.position.x = (
            vslam_weight * vslam_pose.position.x +
            nav2_weight * nav2_pose.position.x
        ) / total_weight

        fused_pose.position.y = (
            vslam_weight * vslam_pose.position.y +
            nav2_weight * nav2_pose.position.y
        ) / total_weight

        fused_pose.position.z = (
            vslam_weight * vslam_pose.position.z +
            nav2_weight * nav2_pose.position.z
        ) / total_weight

        # For orientation, use slerp (spherical linear interpolation)
        # For simplicity, we'll use VSLAM orientation since it's typically more accurate for visual features
        fused_pose.orientation = vslam_pose.orientation

        return fused_pose

    def calculate_fused_covariance(self):
        """Calculate covariance for fused pose"""
        # This would be more sophisticated in practice
        # For now, use a conservative estimate
        covariance = [0.0] * 36  # 6x6 covariance matrix as array

        # Set diagonal elements for position uncertainty
        pos_uncertainty = 0.1  # meters
        covariance[0] = pos_uncertainty**2  # x
        covariance[7] = pos_uncertainty**2  # y
        covariance[14] = pos_uncertainty**2  # z

        # Set diagonal elements for orientation uncertainty
        rot_uncertainty = 0.1  # radians
        covariance[21] = rot_uncertainty**2  # rx
        covariance[28] = rot_uncertainty**2  # ry
        covariance[35] = rot_uncertainty**2  # rz

        return covariance

    def record_path(self):
        """Record path for debugging visualization"""
        if self.fused_pose:
            # Add current fused pose to recorded path
            path_point = PoseStamped()
            path_point.header = self.fused_pose.header
            path_point.pose = self.fused_pose.pose.pose

            self.recorded_path.append(path_point)

            # Limit path length to prevent memory issues
            if len(self.recorded_path) > 1000:
                self.recorded_path = self.recorded_path[-500:]  # Keep last 500 points

            # Publish path for visualization
            self.publish_path_for_visualization()

    def publish_path_for_visualization(self):
        """Publish recorded path for RViz visualization"""
        if not self.recorded_path:
            return

        path_msg = Path()
        path_msg.header.stamp = self.get_clock().now().to_msg()
        path_msg.header.frame_id = "map"
        path_msg.poses = self.recorded_path[-50:]  # Last 50 poses for performance

        self.debug_path_pub.publish(path_msg)

    def get_current_fused_pose(self):
        """Get the current fused pose"""
        return self.fused_pose

    def set_integration_weights(self, vslam_weight, nav2_weight):
        """Adjust the weights for VSLAM and Nav2 in the fusion"""
        if vslam_weight + nav2_weight != 1.0:
            self.get_logger().warn("Weights should sum to 1.0 for proper fusion")

        self.vslam_weight = vslam_weight
        self.nav2_weight = nav2_weight

    def enable_fusion(self, enable):
        """Enable or disable sensor fusion"""
        self.enable_sensor_fusion = enable
        status = "enabled" if enable else "disabled"
        self.get_logger().info(f"Sensor fusion {status}")


class NavigationIntegrationManager:
    """
    Manager class to coordinate Nav2-VSLAM integration
    """
    def __init__(self, node):
        self.node = node
        self.integration_node = Nav2VSLAMIntegrationExample()

        # Initialize navigation components
        self.initialize_navigation_components()

    def initialize_navigation_components(self):
        """Initialize all navigation and perception components"""
        self.get_logger().info("Initializing navigation and perception components...")

        # This would initialize:
        # - VSLAM pipeline
        # - Nav2 stack
        # - TF broadcasters
        # - Sensor synchronizers
        pass

    def start_navigation_with_vslam(self, goal_pose):
        """Start navigation with VSLAM integration"""
        self.get_logger().info("Starting navigation with VSLAM integration...")

        # Use the fused pose for navigation
        fused_pose = self.integration_node.get_current_fused_pose()

        if fused_pose is None:
            self.get_logger().warn("No fused pose available, using initial estimate")
            fused_pose = self.create_initial_pose_estimate()

        # Set up navigation with fused localization
        self.setup_navigation_with_fused_localization(fused_pose, goal_pose)

    def create_initial_pose_estimate(self):
        """Create initial pose estimate when no fused pose is available"""
        # This would use other sensors or manual initialization
        pass

    def setup_navigation_with_fused_localization(self, start_pose, goal_pose):
        """Set up navigation using fused localization"""
        # This would interface with Nav2's navigation action
        pass


def main(args=None):
    """Main function to run the Nav2-VSLAM integration example"""
    rclpy.init(args=args)

    # Create the integration example node
    integration_node = Nav2VSLAMIntegrationExample()

    try:
        # Run the node
        rclpy.spin(integration_node)
    except KeyboardInterrupt:
        pass
    finally:
        integration_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()