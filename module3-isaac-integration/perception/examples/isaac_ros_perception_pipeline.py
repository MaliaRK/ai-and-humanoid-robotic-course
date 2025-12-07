#!/usr/bin/env python3
"""
Isaac ROS Perception Pipeline Example
This example demonstrates the integration of Isaac ROS perception components
for humanoid robot navigation, including visual SLAM, object detection, and
sensor fusion for enhanced navigation capabilities.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

# Isaac ROS packages
try:
    from isaac_ros_apriltag_interfaces.msg import AprilTagDetectionArray
    from isaac_ros_visual_slam_msgs.msg import TfArray
    from isaac_ros_pointcloud_utils_msgs.msg import PointCloud2Accumulator
    from isaac_ros_visual_slam_msgs.srv import ResetPose
    from isaac_ros_managed_nitros_msgs.msg import ManagedImageMessage
except ImportError:
    print("Isaac ROS packages not available. Some functionality may be limited.")

# Standard ROS 2 packages
from sensor_msgs.msg import Image, CameraInfo, Imu, PointCloud2, LaserScan
from geometry_msgs.msg import PoseStamped, Twist, TransformStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import Bool, Float32MultiArray
from tf2_ros import TransformBroadcaster
from visualization_msgs.msg import MarkerArray, Marker
import message_filters
import numpy as np
import time
from typing import Optional, Dict, List, Tuple
import threading
import cv2
from cv_bridge import CvBridge
import math


class IsaacROSPerceptionPipeline(Node):
    """
    Example implementation of an Isaac ROS perception pipeline
    for humanoid robot navigation with VSLAM, object detection, and sensor fusion
    """

    def __init__(self):
        super().__init__('isaac_ros_perception_pipeline')

        # Initialize parameters
        self.declare_parameters([
            ('enable_vslam', True),
            ('enable_apriltag', True),
            ('enable_pointcloud_processing', True),
            ('enable_social_navigation', True),
            ('vslam_weight', 0.7),
            ('imu_weight', 0.2),
            ('odom_weight', 0.1),
            ('social_zone_radius', 0.8),  # meters
            ('personal_space_radius', 0.4),  # meters
            ('balance_threshold', 0.8),
            ('max_processing_time_ms', 33.0)  # 30 FPS
        ])

        # Initialize Isaac ROS components
        self.setup_isaac_ros_components()

        # Initialize standard ROS 2 components
        self.setup_standard_ros_components()

        # Initialize perception pipeline state
        self.initialize_pipeline_state()

        # Initialize Isaac ROS-specific components
        self.setup_isaac_ros_nodes()

        # Create timers for periodic processing
        self.processing_timer = self.create_timer(0.05, self.periodic_processing)  # 20 Hz

        self.get_logger().info("Isaac ROS Perception Pipeline initialized")

    def setup_isaac_ros_components(self):
        """Set up Isaac ROS specific components"""
        # Isaac ROS Visual SLAM components
        if self.get_parameter('enable_vslam').value:
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

        # Isaac ROS AprilTag detection
        if self.get_parameter('enable_apriltag').value:
            self.apriltag_sub = self.create_subscription(
                AprilTagDetectionArray,
                '/isaac_ros/apriltag_detections',
                self.apriltag_callback,
                QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
            )

        # Isaac ROS PointCloud processing
        if self.get_parameter('enable_pointcloud_processing').value:
            self.pointcloud_sub = self.create_subscription(
                PointCloud2,
                '/isaac_ros/pointcloud',
                self.pointcloud_callback,
                QoSProfile(depth=5, reliability=ReliabilityPolicy.BEST_EFFORT)
            )

        # Isaac ROS Image processing (using managed NITROS)
        self.image_sub = message_filters.Subscriber(
            self,
            ManagedImageMessage,
            '/isaac_ros/camera/image_rect_color',
            qos_profile=QoSProfile(depth=5, reliability=ReliabilityPolicy.BEST_EFFORT)
        )

        self.camera_info_sub = message_filters.Subscriber(
            self,
            CameraInfo,
            '/isaac_ros/camera/camera_info',
            qos_profile=QoSProfile(depth=5, reliability=ReliabilityPolicy.RELIABLE)
        )

        # Synchronize Isaac ROS camera data
        self.camera_sync = message_filters.ApproximateTimeSynchronizer(
            [self.image_sub, self.camera_info_sub],
            queue_size=10,
            slop=0.1
        )
        self.camera_sync.registerCallback(self.camera_callback)

    def setup_standard_ros_components(self):
        """Set up standard ROS 2 components"""
        # Standard sensor inputs
        self.imu_sub = self.create_subscription(
            Imu, '/imu/data', self.imu_callback,
            QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
        )

        self.odom_sub = self.create_subscription(
            Odometry, '/odom', self.odom_callback,
            QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
        )

        # Publishers
        self.fused_pose_pub = self.create_publisher(
            PoseWithCovarianceStamped, '/fused_localization/pose', 10
        )
        self.enhanced_map_pub = self.create_publisher(
            OccupancyGrid, '/isaac_ros/enhanced_navigation_map', 10
        )
        self.social_costmap_pub = self.create_publisher(
            OccupancyGrid, '/isaac_ros/social_costmap_overlay', 10
        )
        self.perception_debug_pub = self.create_publisher(
            MarkerArray, '/isaac_ros/perception_debug', 10
        )
        self.human_detection_pub = self.create_publisher(
            PoseArray, '/isaac_ros/detected_humans', 10
        )

        # TF broadcaster
        self.tf_broadcaster = TransformBroadcaster(self)

        # Service clients
        self.vslam_reset_client = self.create_client(
            ResetPose, '/visual_slam/reset_pose'
        )

    def initialize_pipeline_state(self):
        """Initialize perception pipeline state"""
        # Initialize CV bridge for image processing
        self.cv_bridge = CvBridge()

        # Sensor data storage
        self.current_rgb_image = None
        self.current_camera_info = None
        self.current_imu_data = None
        self.current_odom_data = None

        # Isaac ROS data
        self.vslam_pose = None
        self.vslam_map = None
        self.apriltag_detections = []
        self.pointcloud_data = None

        # Fusion state
        self.fused_pose = None
        self.social_zones = []
        self.dynamic_objects = []
        self.human_poses = []

        # Processing parameters
        self.vslam_weight = self.get_parameter('vslam_weight').value
        self.imu_weight = self.get_parameter('imu_weight').value
        self.odom_weight = self.get_parameter('odom_weight').value
        self.confidence_threshold = 0.5

        # Threading for parallel processing
        self.processing_lock = threading.Lock()
        self.perception_ready = False

        # Social navigation parameters
        self.social_zone_radius = self.get_parameter('social_zone_radius').value
        self.personal_space_radius = self.get_parameter('personal_space_radius').value
        self.balance_threshold = self.get_parameter('balance_threshold').value

    def setup_isaac_ros_nodes(self):
        """Setup Isaac ROS perception nodes"""
        # This would typically involve launching Isaac ROS nodes
        # For this example, we assume they're already running and we're just
        # interfacing with their outputs

        self.get_logger().info("Isaac ROS perception nodes configured")

    def camera_callback(self, image_msg: ManagedImageMessage, info_msg: CameraInfo):
        """Handle synchronized camera data from Isaac ROS"""
        with self.processing_lock:
            # Convert Isaac ROS managed image to OpenCV format if needed
            try:
                # In Isaac ROS, images might come in managed format
                # For this example, we'll assume standard conversion
                cv_image = self.cv_bridge.imgmsg_to_cv2(image_msg.image, "bgr8")
                self.current_rgb_image = cv_image
                self.current_camera_info = info_msg
            except Exception as e:
                self.get_logger().error(f"Error converting image: {e}")

        # Process image with Isaac ROS computer vision components
        self.process_camera_data_isaac(cv_image, info_msg)

    def vslam_pose_callback(self, msg: PoseStamped):
        """Handle Isaac ROS VSLAM pose updates"""
        with self.processing_lock:
            self.vslam_pose = msg

        # Update fused localization
        self.update_fused_localization()

    def vslam_map_callback(self, msg: OccupancyGrid):
        """Handle Isaac ROS VSLAM map updates"""
        with self.processing_lock:
            self.vslam_map = msg

        # Enhance navigation map with VSLAM data
        self.enhance_navigation_map()

    def apriltag_callback(self, msg: AprilTagDetectionArray):
        """Handle Isaac ROS AprilTag detections"""
        with self.processing_lock:
            self.apriltag_detections = msg.detections

        # Process tag detections for localization or mapping
        self.process_apriltags()

    def pointcloud_callback(self, msg: PointCloud2):
        """Handle Isaac ROS point cloud data"""
        with self.processing_lock:
            self.pointcloud_data = msg

        # Process point cloud for obstacle detection or mapping
        self.process_pointcloud_data()

    def imu_callback(self, msg: Imu):
        """Handle IMU data for sensor fusion"""
        with self.processing_lock:
            self.current_imu_data = msg

        # Use IMU for pose prediction and sensor fusion
        self.update_pose_prediction_with_imu(msg)

    def odom_callback(self, msg: Odometry):
        """Handle odometry data for sensor fusion"""
        with self.processing_lock:
            self.current_odom_data = msg

        # Use odometry for pose prediction and sensor fusion
        self.update_pose_prediction_with_odom(msg)

    def process_camera_data_isaac(self, cv_image, camera_info):
        """Process camera data using Isaac ROS components"""
        # This is where Isaac ROS would process the camera data
        # For example, feeding it into VSLAM or object detection nodes
        self.get_logger().debug(f"Processing camera data: {cv_image.shape}")

        # Detect humans in the image using Isaac ROS components
        # In practice, this would call Isaac ROS object detection nodes
        humans_in_image = self.detect_humans_in_image(cv_image)

        # If humans detected, process for social navigation
        if humans_in_image:
            self.process_human_detections(humans_in_image, camera_info)

    def detect_humans_in_image(self, image):
        """Detect humans in image using Isaac ROS vision components"""
        # Placeholder for Isaac ROS human detection
        # In practice, this would use Isaac ROS object detection or
        # specialized human detection components
        detected_humans = []

        # Example: Use Isaac ROS vision components for human detection
        # This would involve calling Isaac ROS vision nodes
        # For now, return empty list
        return detected_humans

    def process_human_detections(self, humans, camera_info):
        """Process human detections for social navigation"""
        for human in humans:
            # Convert 2D image coordinates to 3D world coordinates
            world_pose = self.image_to_world_coordinates(
                human.bounding_box.center_x,
                human.bounding_box.center_y,
                camera_info
            )

            # Add to detected humans list
            self.human_poses.append(world_pose)

            # Create social zone around human
            social_zone = {
                'center': world_pose.position,
                'radius': self.social_zone_radius,
                'type': 'social_zone'
            }
            self.social_zones.append(social_zone)

    def image_to_world_coordinates(self, u, v, camera_info):
        """Convert image coordinates to world coordinates"""
        # Use camera intrinsic parameters to convert image coordinates to world coordinates
        # This would involve depth information and camera calibration
        # For now, return a placeholder pose
        pose = Pose()
        pose.position.x = u * 0.01  # Placeholder conversion
        pose.position.y = v * 0.01  # Placeholder conversion
        pose.position.z = 0.0
        pose.orientation.w = 1.0
        return pose

    def update_fused_localization(self):
        """Update fused localization using multiple sensors"""
        if not all([self.vslam_pose, self.current_imu_data, self.current_odom_data]):
            return

        start_time = time.time()

        # Perform sensor fusion to get improved pose estimate
        fused_pose = self.fuse_vslam_imu_odom()

        if fused_pose:
            # Publish fused pose
            fused_pose_msg = PoseWithCovarianceStamped()
            fused_pose_msg.header.stamp = self.get_clock().now().to_msg()
            fused_pose_msg.header.frame_id = "map"
            fused_pose_msg.pose.pose = fused_pose
            fused_pose_msg.pose.covariance = self.calculate_fused_covariance()

            self.fused_pose = fused_pose_msg
            self.fused_pose_pub.publish(fused_pose_msg)

            # Broadcast transform
            self.broadcast_fused_transform(fused_pose_msg)

        # Check processing time
        processing_time = (time.time() - start_time) * 1000  # ms
        if processing_time > self.get_parameter('max_processing_time_ms').value:
            self.get_logger().warn(f"Localization fusion took {processing_time:.1f}ms, exceeding budget")

    def fuse_vslam_imu_odom(self) -> Optional[Pose]:
        """Fuse VSLAM, IMU, and odometry data"""
        if not all([self.vslam_pose, self.current_imu_data, self.current_odom_data]):
            return None

        # Get current poses from different sources
        vslam_position = np.array([
            self.vslam_pose.pose.position.x,
            self.vslam_pose.pose.position.y,
            self.vslam_pose.pose.position.z
        ])
        vslam_orientation = self.vslam_pose.pose.orientation

        # Extract odometry pose
        odom_position = np.array([
            self.current_odom_data.pose.pose.position.x,
            self.current_odom_data.pose.pose.position.y,
            self.current_odom_data.pose.pose.position.z
        ])
        odom_orientation = self.current_odom_data.pose.pose.orientation

        # Extract IMU orientation (simplified)
        imu_orientation = self.current_imu_data.orientation

        # Calculate fused pose using weighted averages
        fused_pose = Pose()

        # Weighted average for position (based on reliability)
        total_weight = self.vslam_weight + self.odom_weight
        fused_pose.position.x = (
            self.vslam_weight * vslam_position[0] +
            self.odom_weight * odom_position[0]
        ) / total_weight

        fused_pose.position.y = (
            self.vslam_weight * vslam_position[1] +
            self.odom_weight * odom_position[1]
        ) / total_weight

        fused_pose.position.z = (
            self.vslam_weight * vslam_position[2] +
            self.odom_weight * odom_position[2]
        ) / total_weight

        # For orientation, use VSLAM with IMU correction
        fused_pose.orientation = self.correct_orientation_with_imu(
            vslam_orientation, self.current_imu_data
        )

        return fused_pose

    def correct_orientation_with_imu(self, vslam_orientation, imu_data):
        """Correct orientation using IMU data"""
        # This would implement proper sensor fusion for orientation
        # For now, we'll return the VSLAM orientation
        return vslam_orientation

    def calculate_fused_covariance(self):
        """Calculate covariance for fused pose estimate"""
        # Simplified covariance calculation
        # In practice, this would come from the actual fusion algorithm
        covariance = [0.0] * 36  # 6x6 covariance matrix

        # Set position uncertainties based on sensor fusion
        pos_uncertainty = 0.05  # meters
        covariance[0] = pos_uncertainty**2  # x
        covariance[7] = pos_uncertainty**2  # y
        covariance[14] = pos_uncertainty**2  # z

        # Set orientation uncertainties
        rot_uncertainty = 0.02  # radians
        covariance[21] = rot_uncertainty**2  # rx
        covariance[28] = rot_uncertainty**2  # ry
        covariance[35] = rot_uncertainty**2  # rz

        return covariance

    def enhance_navigation_map(self):
        """Enhance navigation map with VSLAM data"""
        if not self.vslam_map:
            return

        start_time = time.time()

        # Combine VSLAM map with standard navigation map
        enhanced_map = self.combine_vslam_nav_maps()

        # Add social navigation overlays
        social_overlay = self.create_social_navigation_overlay()

        # Publish enhanced maps
        if enhanced_map:
            self.enhanced_map_pub.publish(enhanced_map)
        if social_overlay:
            self.social_costmap_pub.publish(social_overlay)

        # Check processing time
        processing_time = (time.time() - start_time) * 1000  # ms
        if processing_time > self.get_parameter('max_processing_time_ms').value:
            self.get_logger().warn(f"Map enhancement took {processing_time:.1f}ms, exceeding budget")

    def combine_vslam_nav_maps(self):
        """Combine VSLAM map with navigation map"""
        # In practice, this would involve proper map fusion techniques
        # For now, we'll return the VSLAM map as-is
        if self.vslam_map:
            return self.vslam_map
        return None

    def create_social_navigation_overlay(self):
        """Create social navigation costmap overlay"""
        if not self.human_poses:
            return None

        # Create costmap based on human detections and social norms
        social_map = OccupancyGrid()
        social_map.header.stamp = self.get_clock().now().to_msg()
        social_map.header.frame_id = "map"
        social_map.info.resolution = 0.05  # 5cm resolution
        social_map.info.width = 200  # 10m x 10m at 5cm resolution
        social_map.info.height = 200
        # Set origin to center around robot
        social_map.info.origin.position.x = -5.0
        social_map.info.origin.position.y = -5.0

        # Initialize with zeros
        social_map.data = [0] * (social_map.info.width * social_map.info.height)

        # Add personal space around each detected human
        for human_pose in self.human_poses:
            # Convert human pose to map coordinates
            map_x = int((human_pose.position.x - social_map.info.origin.position.x) / social_map.info.resolution)
            map_y = int((human_pose.position.y - social_map.info.origin.position.y) / social_map.info.resolution)

            # Add cost in a radius around the human
            personal_space_radius_cells = int(self.personal_space_radius / social_map.info.resolution)

            for dx in range(-personal_space_radius_cells, personal_space_radius_cells + 1):
                for dy in range(-personal_space_radius_cells, personal_space_radius_cells + 1):
                    if dx*dx + dy*dy <= personal_space_radius_cells*personal_space_radius_cells:
                        idx_x = map_x + dx
                        idx_y = map_y + dy

                        if (0 <= idx_x < social_map.info.width and
                            0 <= idx_y < social_map.info.height):
                            idx = idx_y * social_map.info.width + idx_x
                            # Calculate cost based on distance (higher cost closer to person)
                            dist_from_center = math.sqrt(dx*dx + dy*dy) * social_map.info.resolution
                            cost = int(200 * (1.0 - min(1.0, dist_from_center / self.personal_space_radius)))
                            social_map.data[idx] = max(social_map.data[idx], cost)

        return social_map

    def process_apriltags(self):
        """Process AprilTag detections for localization and mapping"""
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

    def process_pointcloud_data(self):
        """Process point cloud data for obstacle detection"""
        if self.pointcloud_data is None:
            return

        start_time = time.time()

        # Use Isaac ROS point cloud utilities for processing
        obstacles = self.detect_obstacles_from_pointcloud(self.pointcloud_data)

        # Update costmap with detected obstacles
        if obstacles:
            self.update_costmap_with_obstacles(obstacles)

        # Check processing time
        processing_time = (time.time() - start_time) * 1000  # ms
        if processing_time > self.get_parameter('max_processing_time_ms').value:
            self.get_logger().warn(f"Point cloud processing took {processing_time:.1f}ms, exceeding budget")

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

    def broadcast_fused_transform(self, pose_msg: PoseWithCovarianceStamped):
        """Broadcast fused pose as transform"""
        t = TransformStamped()
        t.header.stamp = pose_msg.header.stamp
        t.header.frame_id = pose_msg.header.frame_id
        t.child_frame_id = "fused_odom"

        t.transform.translation.x = pose_msg.pose.pose.position.x
        t.transform.translation.y = pose_msg.pose.pose.position.y
        t.transform.translation.z = pose_msg.pose.pose.position.z
        t.transform.rotation = pose_msg.pose.pose.orientation

        self.tf_broadcaster.sendTransform(t)

    def periodic_processing(self):
        """Periodic processing callback"""
        # Perform any periodic perception tasks
        self.create_perception_visualization()

    def create_perception_visualization(self):
        """Create visualization for perception pipeline"""
        if not self.human_poses and not self.apriltag_detections:
            return

        markers = MarkerArray()

        # Visualize detected humans
        for i, human_pose in enumerate(self.human_poses):
            human_marker = Marker()
            human_marker.header.stamp = self.get_clock().now().to_msg()
            human_marker.header.frame_id = "map"
            human_marker.ns = "detected_humans"
            human_marker.id = i
            human_marker.type = Marker.CYLINDER
            human_marker.action = Marker.ADD

            human_marker.pose.position = human_pose.position
            human_marker.pose.orientation.w = 1.0
            human_marker.scale.x = self.personal_space_radius * 2  # Diameter
            human_marker.scale.y = self.personal_space_radius * 2  # Diameter
            human_marker.scale.z = 1.0  # Height
            human_marker.color.r = 0.0
            human_marker.color.g = 1.0
            human_marker.color.b = 0.0
            human_marker.color.a = 0.3  # Semi-transparent

            markers.markers.append(human_marker)

        # Visualize AprilTag detections
        for i, tag_detection in enumerate(self.apriltag_detections):
            tag_marker = Marker()
            tag_marker.header.stamp = self.get_clock().now().to_msg()
            tag_marker.header.frame_id = "map"
            tag_marker.ns = "apriltags"
            tag_marker.id = i + 1000  # Offset ID to avoid conflict
            tag_marker.type = Marker.CUBE
            tag_marker.action = Marker.ADD

            tag_marker.pose = tag_detection.pose.pose
            tag_marker.scale.x = 0.1
            tag_marker.scale.y = 0.1
            tag_marker.scale.z = 0.1
            tag_marker.color.r = 1.0
            tag_marker.color.g = 0.0
            tag_marker.color.b = 0.0
            tag_marker.color.a = 1.0

            markers.markers.append(tag_marker)

        # Visualize social zones
        for i, zone in enumerate(self.social_zones):
            zone_marker = Marker()
            zone_marker.header.stamp = self.get_clock().now().to_msg()
            zone_marker.header.frame_id = "map"
            zone_marker.ns = "social_zones"
            zone_marker.id = i + 2000  # Offset ID to avoid conflict
            zone_marker.type = Marker.SPHERE
            zone_marker.action = Marker.ADD

            zone_marker.pose.position.x = zone['center'].x
            zone_marker.pose.position.y = zone['center'].y
            zone_marker.pose.position.z = zone['center'].z
            zone_marker.pose.orientation.w = 1.0
            zone_marker.scale.x = zone['radius'] * 2
            zone_marker.scale.y = zone['radius'] * 2
            zone_marker.scale.z = 0.1  # Flat circle
            zone_marker.color.r = 1.0
            zone_marker.color.g = 1.0
            zone_marker.color.b = 0.0
            zone_marker.color.a = 0.2  # More transparent

            markers.markers.append(zone_marker)

        self.perception_debug_pub.publish(markers)

    def get_current_fused_pose(self) -> Optional[PoseWithCovarianceStamped]:
        """Get the current fused pose estimate"""
        return self.fused_pose

    def get_social_zones(self) -> List:
        """Get current social zones for navigation planning"""
        return self.social_zones

    def get_dynamic_objects(self) -> List:
        """Get currently detected dynamic objects"""
        return self.dynamic_objects

    def enable_perception_pipeline(self, enable: bool):
        """Enable or disable the perception pipeline"""
        self.perception_enabled = enable
        status = "enabled" if enable else "disabled"
        self.get_logger().info(f"Perception pipeline {status}")

    def get_pipeline_status(self) -> Dict:
        """Get current status of perception pipeline"""
        return {
            'vslam_available': self.vslam_pose is not None,
            'imu_available': self.current_imu_data is not None,
            'camera_available': all([self.current_rgb_image, self.current_camera_info]),
            'apriltag_detections': len(self.apriltag_detections),
            'detected_humans': len(self.human_poses),
            'last_update_time': self.get_clock().now().seconds_nanoseconds(),
            'pipeline_enabled': getattr(self, 'perception_enabled', True),
            'processing_time_avg': getattr(self, 'avg_processing_time', 0.0)
        }

    def reset_vslam(self):
        """Reset VSLAM system"""
        if self.vslam_reset_client.wait_for_service(timeout_sec=1.0):
            request = ResetPose.Request()
            future = self.vslam_reset_client.call_async(request)
            self.get_logger().info("VSLAM reset requested")
        else:
            self.get_logger().error("VSLAM reset service not available")


class IsaacROSPerceptionManager:
    """
    Manager class to coordinate Isaac ROS perception components
    """
    def __init__(self):
        self.pipeline = None
        self.is_initialized = False

    def initialize_perception_pipeline(self, node_handle):
        """Initialize Isaac ROS perception pipeline"""
        try:
            self.pipeline = IsaacROSPerceptionPipeline()
            self.is_initialized = True
            node_handle.get_logger().info("Isaac ROS Perception Pipeline initialized successfully")
            return True
        except Exception as e:
            node_handle.get_logger().error(f"Failed to initialize perception pipeline: {e}")
            return False

    def get_perception_data(self):
        """Get current perception data from pipeline"""
        if not self.is_initialized or not self.pipeline:
            return None

        return {
            'fused_pose': self.pipeline.get_current_fused_pose(),
            'social_zones': self.pipeline.get_social_zones(),
            'dynamic_objects': self.pipeline.get_dynamic_objects(),
            'status': self.pipeline.get_pipeline_status()
        }

    def enable_perception(self, enable: bool):
        """Enable/disable perception pipeline"""
        if self.pipeline:
            self.pipeline.enable_perception_pipeline(enable)

    def reset_perception_systems(self):
        """Reset perception systems"""
        if self.pipeline:
            self.pipeline.reset_vslam()


def main(args=None):
    """Main function to run the Isaac ROS perception pipeline example"""
    rclpy.init(args=args)

    # Create the perception pipeline node
    perception_node = IsaacROSPerceptionPipeline()

    try:
        # Spin the node
        rclpy.spin(perception_node)
    except KeyboardInterrupt:
        perception_node.get_logger().info("Interrupted, shutting down...")
    finally:
        perception_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()