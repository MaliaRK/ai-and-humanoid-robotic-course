#!/usr/bin/env python3
"""
Isaac ROS Navigation Integration Example
This example demonstrates the integration between Isaac ROS perception components
and Nav2 for humanoid robot navigation.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped, Twist
from nav_msgs.msg import Odometry, OccupancyGrid
from sensor_msgs.msg import Image, CameraInfo, Imu, PointCloud2
from tf2_ros import TransformBroadcaster, Buffer, TransformListener
from visualization_msgs.msg import MarkerArray, Marker
from std_msgs.msg import Bool, Float64MultiArray
import message_filters
import numpy as np
from scipy.spatial.transform import Rotation as R
import threading
import time
from typing import Optional, List, Dict, Tuple
import math


class IsaacROSNav2Integrator(Node):
    """
    Example integration of Isaac ROS perception with Nav2 navigation
    for enhanced humanoid robot navigation capabilities
    """

    def __init__(self):
        super().__init__('isaac_ros_nav2_integrator')

        # Initialize Isaac ROS components
        self.setup_isaac_ros_components()

        # Initialize Nav2 interface
        self.setup_nav2_interface()

        # Initialize fusion components
        self.setup_sensor_fusion()

        # Initialize navigation state
        self.initialize_navigation_state()

        self.get_logger().info("Isaac ROS - Nav2 Integration initialized")

    def setup_isaac_ros_components(self):
        """Set up Isaac ROS perception components"""
        # Isaac ROS VSLAM subscribers
        self.vslam_pose_sub = self.create_subscription(
            PoseStamped,
            '/visual_slam/pose',
            self.vslam_pose_callback,
            QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        )

        self.vslam_map_sub = self.create_subscription(
            OccupancyGrid,
            '/visual_slam/map',
            self.vslam_map_callback,
            QoSProfile(depth=5, reliability=ReliabilityPolicy.RELIABLE)
        )

        # Isaac ROS AprilTag detection (for landmarks and localization)
        self.apriltag_sub = self.create_subscription(
            AprilTagDetectionArray,
            '/isaac_ros/apriltag_detections',
            self.apriltag_callback,
            QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        )

        # Isaac ROS point cloud processing
        self.pointcloud_sub = self.create_subscription(
            PointCloud2,
            '/isaac_ros/pointcloud',
            self.pointcloud_callback,
            QoSProfile(depth=5, reliability=ReliabilityPolicy.BEST_EFFORT)
        )

        # Isaac ROS camera data
        self.rgb_image_sub = message_filters.Subscriber(
            self, Image, '/isaac_ros/camera/rgb',
            qos_profile=QoSProfile(depth=5, reliability=ReliabilityPolicy.BEST_EFFORT)
        )
        self.camera_info_sub = message_filters.Subscriber(
            self, CameraInfo, '/isaac_ros/camera/info',
            qos_profile=QoSProfile(depth=5, reliability=ReliabilityPolicy.RELIABLE)
        )

        # Synchronize camera data
        self.camera_sync = message_filters.ApproximateTimeSynchronizer(
            [self.rgb_image_sub, self.camera_info_sub],
            queue_size=10,
            slop=0.1
        )
        self.camera_sync.registerCallback(self.camera_callback)

    def setup_nav2_interface(self):
        """Set up interface to Nav2 navigation stack"""
        # Nav2 pose estimate (from AMCL or other localizer)
        self.nav2_pose_sub = self.create_subscription(
            PoseWithCovarianceStamped,
            '/amcl_pose',
            self.nav2_pose_callback,
            QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
        )

        # Nav2 costmap updates
        self.nav2_costmap_sub = self.create_subscription(
            OccupancyGrid,
            '/global_costmap/costmap',
            self.nav2_costmap_callback,
            QoSProfile(depth=5, reliability=ReliabilityPolicy.BEST_EFFORT)
        )

        # Navigation goal publisher
        self.nav2_goal_pub = self.create_publisher(
            PoseStamped, '/goal_pose', 10
        )

        # Navigation feedback
        self.nav2_feedback_sub = self.create_subscription(
            String, '/navigation_feedback', self.nav2_feedback_callback, 10
        )

        # Enhanced costmap publisher
        self.enhanced_costmap_pub = self.create_publisher(
            OccupancyGrid, '/isaac_ros/enhanced_costmap', 10
        )

        # Fused pose publisher
        self.fused_pose_pub = self.create_publisher(
            PoseWithCovarianceStamped, '/fused_localization/pose', 10
        )

        # Social navigation overlay
        self.social_costmap_pub = self.create_publisher(
            OccupancyGrid, '/social_navigation_overlay', 10
        )

        # Debug visualization
        self.debug_markers_pub = self.create_publisher(
            MarkerArray, '/isaac_ros_nav_integration/debug', 10
        )

    def initialize_navigation_state(self):
        """Initialize navigation state variables"""
        # Isaac ROS data
        self.vslam_pose = None
        self.vslam_map = None
        self.apriltag_detections = []
        self.pointcloud_data = None
        self.rgb_image = None
        self.camera_info = None

        # Nav2 data
        self.nav2_pose = None
        self.nav2_costmap = None
        self.nav2_goal = None
        self.nav2_status = "IDLE"

        # Fused data
        self.fused_pose = None
        self.enhanced_costmap = None
        self.social_zones = []

        # Integration parameters
        self.vslam_weight = 0.7
        self.nav2_weight = 0.3
        self.confidence_threshold = 0.5
        self.max_pose_difference = 0.5  # meters

        # Threading locks
        self.fusion_lock = threading.Lock()

        # Integration timer
        self.integration_timer = self.create_timer(0.05, self.integrate_navigation_data)  # 20 Hz

    def setup_sensor_fusion(self):
        """Setup sensor fusion for Isaac ROS and Nav2 data"""
        # Initialize Extended Kalman Filter or other fusion algorithm
        self.initialize_fusion_algorithm()

    def initialize_fusion_algorithm(self):
        """Initialize the sensor fusion algorithm"""
        # For this example, we'll use a simple weighted fusion
        # In practice, you might use an EKF or UKF
        self.fusion_initialized = True
        self.get_logger().info("Sensor fusion algorithm initialized")

    def vslam_pose_callback(self, msg: PoseStamped):
        """Handle VSLAM pose updates from Isaac ROS"""
        with self.fusion_lock:
            self.vslam_pose = msg
            self.get_logger().debug(f"Received VSLAM pose: ({msg.pose.position.x:.2f}, {msg.pose.position.y:.2f})")

        # Trigger fusion if Nav2 pose is also available
        if self.nav2_pose:
            self.trigger_pose_fusion()

    def nav2_pose_callback(self, msg: PoseWithCovarianceStamped):
        """Handle Nav2 pose updates"""
        with self.fusion_lock:
            self.nav2_pose = msg
            self.get_logger().debug(f"Received Nav2 pose: ({msg.pose.pose.position.x:.2f}, {msg.pose.pose.position.y:.2f})")

        # Trigger fusion if VSLAM pose is also available
        if self.vslam_pose:
            self.trigger_pose_fusion()

    def vslam_map_callback(self, msg: OccupancyGrid):
        """Handle VSLAM map updates"""
        with self.fusion_lock:
            self.vslam_map = msg
            self.get_logger().debug(f"Received VSLAM map: {msg.info.width}x{msg.info.height}")

        # Enhance Nav2 costmap with VSLAM data
        self.enhance_nav2_costmap_with_vslam()

    def nav2_costmap_callback(self, msg: OccupancyGrid):
        """Handle Nav2 costmap updates"""
        with self.fusion_lock:
            self.nav2_costmap = msg
            self.get_logger().debug(f"Received Nav2 costmap: {msg.info.width}x{msg.info.height}")

    def apriltag_callback(self, msg: AprilTagDetectionArray):
        """Handle AprilTag detections for landmark-based localization"""
        with self.fusion_lock:
            self.apriltag_detections = msg.detections
            self.get_logger().debug(f"Received {len(msg.detections)} AprilTag detections")

        # Process tags for localization improvement
        self.process_apriltags_for_localization()

    def pointcloud_callback(self, msg: PointCloud2):
        """Handle point cloud data for enhanced mapping"""
        with self.fusion_lock:
            self.pointcloud_data = msg
            self.get_logger().debug("Received point cloud data")

        # Process point cloud for obstacle detection and mapping
        self.process_pointcloud_for_navigation()

    def camera_callback(self, image_msg: Image, info_msg: CameraInfo):
        """Handle synchronized camera data"""
        with self.fusion_lock:
            self.rgb_image = image_msg
            self.camera_info = info_msg

        # Process image data for object detection or feature extraction
        self.process_camera_data_for_navigation()

    def integrate_navigation_data(self):
        """Main integration loop - runs periodically to fuse data"""
        with self.fusion_lock:
            # Check if we have enough data to perform fusion
            if not all([self.vslam_pose, self.nav2_pose]):
                return

            # Perform pose fusion
            fused_pose = self.fuse_poses()
            if fused_pose:
                self.fused_pose = fused_pose
                self.publish_fused_pose(fused_pose)

            # Enhance costmap with VSLAM data
            if self.vslam_map and self.nav2_costmap:
                enhanced_map = self.enhance_costmap_with_vslam_data()
                if enhanced_map:
                    self.enhanced_costmap = enhanced_map
                    self.enhanced_costmap_pub.publish(enhanced_map)

            # Create social navigation overlay
            social_overlay = self.create_social_navigation_overlay()
            if social_overlay:
                self.social_costmap_pub.publish(social_overlay)

            # Publish debug visualization
            self.publish_debug_visualization()

    def fuse_poses(self) -> Optional[PoseWithCovarianceStamped]:
        """Fuse VSLAM and Nav2 poses"""
        if not all([self.vslam_pose, self.nav2_pose]):
            return None

        # Check pose consistency
        pose_diff = self.calculate_pose_difference(
            self.vslam_pose.pose,
            self.nav2_pose.pose.pose
        )

        if pose_diff > self.max_pose_difference:
            self.get_logger().warn(f"Pose difference too large: {pose_diff:.2f}m")
            # In case of large difference, trust Nav2 more as it's typically more reliable for navigation
            return self.create_fused_pose(self.nav2_pose.pose.pose, self.nav2_pose.pose.covariance)

        # Perform weighted fusion
        fused_pose = self.weighted_pose_fusion(
            self.vslam_pose.pose,
            self.nav2_pose.pose.pose,
            self.vslam_weight,
            self.nav2_weight
        )

        # Calculate fused covariance
        fused_covariance = self.calculate_fused_covariance(
            self.vslam_pose.pose.covariance,
            self.nav2_pose.pose.covariance
        )

        return self.create_fused_pose(fused_pose, fused_covariance)

    def calculate_pose_difference(self, pose1, pose2) -> float:
        """Calculate spatial difference between two poses"""
        dx = pose1.position.x - pose2.position.x
        dy = pose1.position.y - pose2.position.y
        dz = pose1.position.z - pose2.position.z

        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        return distance

    def weighted_pose_fusion(self, vslam_pose, nav2_pose, vslam_weight, nav2_weight):
        """Perform weighted fusion of two poses"""
        total_weight = vslam_weight + nav2_weight

        # Position fusion
        fused_position = type(vslam_pose.position)()
        fused_position.x = (vslam_weight * vslam_pose.position.x + nav2_weight * nav2_pose.position.x) / total_weight
        fused_position.y = (vslam_weight * vslam_pose.position.y + nav2_weight * nav2_pose.position.y) / total_weight
        fused_position.z = (vslam_weight * vslam_pose.position.z + nav2_weight * nav2_pose.position.z) / total_weight

        # For orientation, we'll use a simple weighted approach
        # In practice, quaternion slerp would be more appropriate
        fused_orientation = self.fuse_quaternions(
            vslam_pose.orientation,
            nav2_pose.orientation,
            vslam_weight,
            nav2_weight
        )

        fused_pose = type(vslam_pose)()
        fused_pose.position = fused_position
        fused_pose.orientation = fused_orientation

        return fused_pose

    def fuse_quaternions(self, quat1, quat2, weight1, weight2):
        """Fuse two quaternions with weights"""
        # Simple weighted averaging (not mathematically optimal, but sufficient for example)
        # For production use, use proper quaternion slerp
        total_weight = weight1 + weight2
        fused_x = (weight1 * quat1.x + weight2 * quat2.x) / total_weight
        fused_y = (weight1 * quat1.y + weight2 * quat2.y) / total_weight
        fused_z = (weight1 * quat1.z + weight2 * quat2.z) / total_weight
        fused_w = (weight1 * quat1.w + weight2 * quat2.w) / total_weight

        # Normalize the quaternion
        norm = math.sqrt(fused_x*fused_x + fused_y*fused_y + fused_z*fused_z + fused_w*fused_w)
        if norm > 0:
            fused_x /= norm
            fused_y /= norm
            fused_z /= norm
            fused_w /= norm

        fused_quat = type(quat1)()
        fused_quat.x = fused_x
        fused_quat.y = fused_y
        fused_quat.z = fused_z
        fused_quat.w = fused_w

        return fused_quat

    def calculate_fused_covariance(self, cov1, cov2):
        """Calculate fused covariance from two covariance matrices"""
        # Simple weighted average of covariance matrices
        fused_cov = [0.0] * 36  # 6x6 covariance matrix as array

        for i in range(36):
            fused_cov[i] = (self.vslam_weight * cov1[i] + self.nav2_weight * cov2[i])

        return fused_cov

    def create_fused_pose(self, pose, covariance) -> PoseWithCovarianceStamped:
        """Create fused pose message"""
        fused_pose_msg = PoseWithCovarianceStamped()
        fused_pose_msg.header.stamp = self.get_clock().now().to_msg()
        fused_pose_msg.header.frame_id = "map"  # Assuming map frame
        fused_pose_msg.pose.pose = pose
        fused_pose_msg.pose.covariance = covariance

        return fused_pose_msg

    def enhance_costmap_with_vslam_data(self) -> Optional[OccupancyGrid]:
        """Enhance Nav2 costmap with VSLAM data"""
        if not all([self.vslam_map, self.nav2_costmap]):
            return None

        # Create enhanced costmap based on both sources
        enhanced_map = OccupancyGrid()
        enhanced_map.header.stamp = self.get_clock().now().to_msg()
        enhanced_map.header.frame_id = self.nav2_costmap.header.frame_id

        # Copy basic map info from Nav2 costmap (which is more navigation-oriented)
        enhanced_map.info = self.nav2_costmap.info

        # Initialize with Nav2 costmap data
        enhanced_map.data = list(self.nav2_costmap.data)

        # Overlay VSLAM features with appropriate weights
        self.overlay_vslam_features_on_costmap(enhanced_map)

        return enhanced_map

    def overlay_vslam_features_on_costmap(self, costmap: OccupancyGrid):
        """Overlay VSLAM features onto costmap"""
        # This would involve projecting VSLAM features into the costmap frame
        # and adjusting costs based on feature density or semantic information

        # For this example, we'll add some cost based on feature density
        # (in practice, this would be more sophisticated)

        # Get VSLAM features that correspond to obstacles
        obstacle_features = self.extract_obstacle_features_from_vslam()

        for feature in obstacle_features:
            # Convert feature position to costmap coordinates
            map_x, map_y = self.world_to_map_coords(
                feature.position.x, feature.position.y, costmap
            )

            # Check bounds
            if 0 <= map_x < costmap.info.width and 0 <= map_y < costmap.info.height:
                # Increase cost around this feature
                self.increase_cost_around_point(map_x, map_y, costmap, cost_increase=50)

    def extract_obstacle_features_from_vslam(self):
        """Extract obstacle-related features from VSLAM data"""
        # This would interface with VSLAM system to extract obstacle information
        # For now, return empty list
        return []

    def world_to_map_coords(self, x, y, costmap):
        """Convert world coordinates to map coordinates"""
        map_x = int((x - costmap.info.origin.position.x) / costmap.info.resolution)
        map_y = int((y - costmap.info.origin.position.y) / costmap.info.resolution)
        return map_x, map_y

    def increase_cost_around_point(self, center_x, center_y, costmap, cost_increase, radius=2):
        """Increase cost in a radius around a point"""
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx*dx + dy*dy <= radius*radius:
                    x = center_x + dx
                    y = center_y + dy

                    if 0 <= x < costmap.info.width and 0 <= y < costmap.info.height:
                        idx = y * costmap.info.width + x
                        new_cost = min(254, costmap.data[idx] + cost_increase)
                        costmap.data[idx] = new_cost

    def create_social_navigation_overlay(self) -> Optional[OccupancyGrid]:
        """Create social navigation overlay based on human detection"""
        # Create costmap overlay for social navigation
        # This uses AprilTag detections to identify humans and create social zones

        if not self.apriltag_detections:
            # Return empty costmap if no humans detected
            social_map = OccupancyGrid()
            social_map.header.stamp = self.get_clock().now().to_msg()
            social_map.header.frame_id = "map"
            social_map.info.resolution = 0.05
            social_map.info.width = 100
            social_map.info.height = 100
            social_map.info.origin.position.x = -2.5
            social_map.info.origin.position.y = -2.5
            social_map.data = [0] * (100 * 100)  # Initialize with zeros
            return social_map

        # Create costmap with social zones around detected humans
        social_map = OccupancyGrid()
        social_map.header.stamp = self.get_clock().now().to_msg()
        social_map.header.frame_id = "map"
        social_map.info.resolution = 0.05
        social_map.info.width = 100
        social_map.info.height = 100
        social_map.info.origin.position.x = -2.5
        social_map.info.origin.position.y = -2.5

        # Initialize with zeros
        social_map.data = [0] * (social_map.info.width * social_map.info.height)

        # Create personal space around each detected human
        for detection in self.apriltag_detections:
            # Assuming the tag is on or near a human
            tag_x = detection.pose.position.x
            tag_y = detection.pose.position.y

            # Convert to map coordinates
            map_x = int((tag_x - social_map.info.origin.position.x) / social_map.info.resolution)
            map_y = int((tag_y - social_map.info.origin.position.y) / social_map.info.resolution)

            # Add cost in personal space radius (0.8m = 16 cells at 0.05m resolution)
            personal_space_radius = int(0.8 / social_map.info.resolution)

            for dx in range(-personal_space_radius, personal_space_radius + 1):
                for dy in range(-personal_space_radius, personal_space_radius + 1):
                    if dx*dx + dy*dy <= personal_space_radius*personal_space_radius:
                        x_idx = map_x + dx
                        y_idx = map_y + dy

                        if (0 <= x_idx < social_map.info.width and
                            0 <= y_idx < social_map.info.height):
                            # Calculate cost based on distance from center (higher cost closer to human)
                            dist_from_center = math.sqrt(dx*dx + dy*dy) * social_map.info.resolution
                            cost = int(200 * (1.0 - min(1.0, dist_from_center / 0.8)))
                            current_cost = social_map.data[y_idx * social_map.info.width + x_idx]
                            social_map.data[y_idx * social_map.info.width + x_idx] = max(current_cost, cost)

        return social_map

    def process_apriltags_for_localization(self):
        """Process AprilTags for improved localization"""
        if not self.apriltag_detections:
            return

        for detection in self.apriltag_detections:
            tag_id = detection.id
            tag_pose = detection.pose.pose

            # If this is a known landmark, use for localization correction
            if self.is_known_landmark(tag_id):
                self.correct_localization_with_landmark(tag_id, tag_pose)

            # Use tag for mapping reference
            self.add_tag_to_map(tag_id, tag_pose)

    def is_known_landmark(self, tag_id: int) -> bool:
        """Check if tag ID corresponds to a known landmark"""
        # This would check against a database of known landmark positions
        known_tags = [1, 2, 3, 4, 5]  # Example known landmark IDs
        return tag_id in known_tags

    def correct_localization_with_landmark(self, tag_id: int, tag_pose):
        """Correct robot localization using known landmark"""
        # Calculate expected tag pose based on current estimated robot pose
        # Compare with actual detected pose to correct localization
        pass

    def add_tag_to_map(self, tag_id: int, tag_pose):
        """Add tag to map as a landmark"""
        # This would add the tag to the SLAM map as a permanent landmark
        pass

    def process_pointcloud_for_navigation(self):
        """Process point cloud data for navigation"""
        if self.pointcloud_data is None:
            return

        # Use Isaac ROS point cloud processing to detect obstacles
        obstacles = self.detect_obstacles_from_pointcloud(self.pointcloud_data)

        # Update costmap with detected obstacles
        if obstacles:
            self.update_costmap_with_obstacles(obstacles)

    def detect_obstacles_from_pointcloud(self, pointcloud_msg):
        """Detect obstacles from point cloud data using Isaac ROS tools"""
        # This would use Isaac ROS point cloud processing
        # For now, return a placeholder
        obstacles = []
        # In practice: use Isaac ROS point cloud processing to detect obstacles
        return obstacles

    def update_costmap_with_obstacles(self, obstacles):
        """Update costmap with detected obstacles"""
        # This would update the navigation costmap with obstacle information
        pass

    def process_camera_data_for_navigation(self):
        """Process camera data for navigation enhancements"""
        if not all([self.rgb_image, self.camera_info]):
            return

        # Use Isaac ROS image processing for object detection or semantic mapping
        # This could identify dynamic obstacles, stairs, or other navigation-relevant features
        pass

    def publish_fused_pose(self, fused_pose_msg: PoseWithCovarianceStamped):
        """Publish fused pose estimate"""
        self.fused_pose_pub.publish(fused_pose_msg)

        # Also broadcast transform for TF tree
        self.broadcast_fused_transform(fused_pose_msg)

    def broadcast_fused_transform(self, pose_msg: PoseWithCovarianceStamped):
        """Broadcast fused pose as transform"""
        from geometry_msgs.msg import TransformStamped

        t = TransformStamped()
        t.header.stamp = pose_msg.header.stamp
        t.header.frame_id = pose_msg.header.frame_id
        t.child_frame_id = "fused_odom"

        t.transform.translation.x = pose_msg.pose.pose.position.x
        t.transform.translation.y = pose_msg.pose.pose.position.y
        t.transform.translation.z = pose_msg.pose.pose.position.z
        t.transform.rotation = pose_msg.pose.pose.orientation

        # Publish transform
        if not hasattr(self, 'tf_broadcaster'):
            self.tf_broadcaster = TransformBroadcaster(self)
        self.tf_broadcaster.sendTransform(t)

    def publish_debug_visualization(self):
        """Publish debug visualization for integration state"""
        markers = MarkerArray()

        # Visualize VSLAM pose
        if self.vslam_pose:
            vslam_marker = Marker()
            vslam_marker.header.stamp = self.get_clock().now().to_msg()
            vslam_marker.header.frame_id = "map"
            vslam_marker.ns = "vslam_pose"
            vslam_marker.id = 0
            vslam_marker.type = Marker.SPHERE
            vslam_marker.action = Marker.ADD
            vslam_marker.pose = self.vslam_pose.pose
            vslam_marker.scale.x = 0.2
            vslam_marker.scale.y = 0.2
            vslam_marker.scale.z = 0.2
            vslam_marker.color.r = 0.0
            vslam_marker.color.g = 1.0
            vslam_marker.color.b = 0.0
            vslam_marker.color.a = 0.8
            markers.markers.append(vslam_marker)

        # Visualize Nav2 pose
        if self.nav2_pose:
            nav2_marker = Marker()
            nav2_marker.header.stamp = self.get_clock().now().to_msg()
            nav2_marker.header.frame_id = "map"
            nav2_marker.ns = "nav2_pose"
            nav2_marker.id = 1
            nav2_marker.type = Marker.CUBE
            nav2_marker.action = Marker.ADD
            nav2_marker.pose = self.nav2_pose.pose.pose
            nav2_marker.scale.x = 0.25
            nav2_marker.scale.y = 0.25
            nav2_marker.scale.z = 0.25
            nav2_marker.color.r = 0.0
            nav2_marker.color.g = 0.0
            nav2_marker.color.b = 1.0
            nav2_marker.color.a = 0.8
            markers.markers.append(nav2_marker)

        # Visualize fused pose
        if self.fused_pose:
            fused_marker = Marker()
            fused_marker.header.stamp = self.get_clock().now().to_msg()
            fused_marker.header.frame_id = "map"
            fused_marker.ns = "fused_pose"
            fused_marker.id = 2
            fused_marker.type = Marker.ARROW
            fused_marker.action = Marker.ADD
            fused_marker.pose = self.fused_pose.pose.pose
            fused_marker.scale.x = 0.3
            fused_marker.scale.y = 0.1
            fused_marker.scale.z = 0.1
            fused_marker.color.r = 1.0
            fused_marker.color.g = 0.0
            fused_marker.color.b = 0.0
            fused_marker.color.a = 1.0
            markers.markers.append(fused_marker)

        # Visualize AprilTag detections
        if self.apriltag_detections:
            for i, detection in enumerate(self.apriltag_detections):
                tag_marker = Marker()
                tag_marker.header.stamp = self.get_clock().now().to_msg()
                tag_marker.header.frame_id = "map"
                tag_marker.ns = "apriltags"
                tag_marker.id = i + 10
                tag_marker.type = Marker.CUBE
                tag_marker.action = Marker.ADD
                tag_marker.pose = detection.pose.pose
                tag_marker.scale.x = 0.1
                tag_marker.scale.y = 0.1
                tag_marker.scale.z = 0.1
                tag_marker.color.r = 1.0
                tag_marker.color.g = 1.0
                tag_marker.color.b = 0.0
                tag_marker.color.a = 1.0
                markers.markers.append(tag_marker)

        self.debug_markers_pub.publish(markers)

    def trigger_pose_fusion(self):
        """Manually trigger pose fusion"""
        # This could be called when specific conditions are met
        # (e.g., significant pose difference detected)
        pass

    def nav2_feedback_callback(self, msg):
        """Handle Nav2 feedback"""
        self.nav2_status = msg.data
        self.get_logger().debug(f"Nav2 status: {self.nav2_status}")

    def get_current_fused_pose(self) -> Optional[PoseWithCovarianceStamped]:
        """Get the current fused pose estimate"""
        return self.fused_pose

    def get_enhanced_costmap(self) -> Optional[OccupancyGrid]:
        """Get the enhanced costmap with VSLAM data"""
        return self.enhanced_costmap

    def get_social_zones(self) -> List:
        """Get current social zones for navigation planning"""
        return self.social_zones

    def enable_integration(self, enable: bool):
        """Enable or disable the Isaac ROS - Nav2 integration"""
        self.integration_enabled = enable
        status = "enabled" if enable else "disabled"
        self.get_logger().info(f"Isaac ROS - Nav2 integration {status}")

    def get_integration_status(self) -> Dict:
        """Get current status of the integration"""
        return {
            'vslam_available': self.vslam_pose is not None,
            'nav2_available': self.nav2_pose is not None,
            'apriltag_detections': len(self.apriltag_detections),
            'integration_enabled': getattr(self, 'integration_enabled', True),
            'last_update_time': self.get_clock().now().seconds_nanoseconds(),
            'pose_difference': self.calculate_pose_difference(
                self.vslam_pose.pose if self.vslam_pose else None,
                self.nav2_pose.pose.pose if self.nav2_pose else None
            ) if all([self.vslam_pose, self.nav2_pose]) else None
        }


class IsaacROSNav2IntegrationManager:
    """
    Manager class to coordinate Isaac ROS and Nav2 integration
    """
    def __init__(self):
        self.integration_node = None
        self.is_initialized = False

    def initialize_integration(self, node_handle):
        """Initialize Isaac ROS - Nav2 integration"""
        try:
            self.integration_node = IsaacROSNav2Integrator()
            self.is_initialized = True
            node_handle.get_logger().info("Isaac ROS - Nav2 Integration initialized successfully")
            return True
        except Exception as e:
            node_handle.get_logger().error(f"Failed to initialize Isaac ROS - Nav2 integration: {e}")
            return False

    def get_integration_data(self):
        """Get current integration data"""
        if not self.is_initialized or not self.integration_node:
            return None

        return {
            'fused_pose': self.integration_node.get_current_fused_pose(),
            'enhanced_costmap': self.integration_node.get_enhanced_costmap(),
            'social_zones': self.integration_node.get_social_zones(),
            'status': self.integration_node.get_integration_status()
        }

    def enable_integration(self, enable: bool):
        """Enable/disable integration"""
        if self.integration_node:
            self.integration_node.enable_integration(enable)


def main(args=None):
    """Main function to run the Isaac ROS - Nav2 integration example"""
    rclpy.init(args=args)

    # Create the integration node
    integration_node = IsaacROSNav2Integrator()

    try:
        # Spin the node
        rclpy.spin(integration_node)
    except KeyboardInterrupt:
        integration_node.get_logger().info("Interrupted, shutting down...")
    finally:
        integration_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()