#!/usr/bin/env python3
"""
Isaac ROS Perception Pipeline for Humanoid Navigation
Integrates VSLAM, sensor fusion, and social navigation for humanoid robots
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped, Twist, TransformStamped
from nav_msgs.msg import Odometry, OccupancyGrid
from sensor_msgs.msg import Image, CameraInfo, Imu, PointCloud2
from std_msgs.msg import Bool, Float32MultiArray
from tf2_ros import TransformBroadcaster
from visualization_msgs.msg import MarkerArray, Marker
from builtin_interfaces.msg import Time
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
    Isaac ROS Perception Pipeline for Humanoid Navigation
    Integrates VSLAM, sensor fusion, and social navigation components
    """

    def __init__(self):
        super().__init__('isaac_ros_perception_pipeline')

        # Declare parameters
        self.declare_parameters([
            ('enable_sensor_fusion', True),
            ('vslam_weight', 0.7),
            ('imu_weight', 0.2),
            ('odom_weight', 0.1),
            ('social_zone_radius', 0.8),
            ('personal_space_radius', 0.4),
            ('max_processing_time_ms', 33.0),
            ('balance_threshold', 0.8),
            ('enable_social_navigation', True),
            ('enable_dynamic_obstacle_detection', True)
        ])

        # Initialize components
        self.cv_bridge = CvBridge()
        self.tf_broadcaster = TransformBroadcaster(self)

        # Initialize data containers
        self.current_vslam_pose = None
        self.current_imu_data = None
        self.current_odom_data = None
        self.current_camera_data = None
        self.current_pointcloud_data = None

        # Social navigation containers
        self.detected_humans = []
        self.social_zones = []
        self.dynamic_obstacles = []

        # Processing state
        self.processing_lock = threading.Lock()
        self.last_processing_time = time.time()

        # Initialize subscribers
        self.setup_subscribers()

        # Initialize publishers
        self.setup_publishers()

        # Create processing timer
        self.processing_timer = self.create_timer(0.05, self.process_sensor_data)  # 20 Hz

        self.get_logger().info("Isaac ROS Perception Pipeline initialized")

    def setup_subscribers(self):
        """Set up all subscribers for sensor data"""
        # VSLAM pose from Isaac ROS VSLAM
        self.vslam_pose_sub = self.create_subscription(
            PoseStamped,
            '/isaac_ros/visual_slam/pose',
            self.vslam_pose_callback,
            QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        )

        # IMU data for balance and orientation
        self.imu_sub = self.create_subscription(
            Imu,
            '/imu/data',
            self.imu_callback,
            QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
        )

        # Odometry for motion prediction
        self.odom_sub = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
        )

        # Camera data for human detection
        self.camera_sub = message_filters.Subscriber(
            self,
            Image,
            '/head_camera/image_rect_color',
            qos_profile=QoSProfile(depth=5, reliability=ReliabilityPolicy.BEST_EFFORT)
        )
        self.camera_info_sub = message_filters.Subscriber(
            self,
            CameraInfo,
            '/head_camera/camera_info',
            qos_profile=QoSProfile(depth=5, reliability=ReliabilityPolicy.RELIABLE)
        )

        # Synchronize camera and camera info
        self.camera_sync = message_filters.ApproximateTimeSynchronizer(
            [self.camera_sub, self.camera_info_sub],
            queue_size=10,
            slop=0.1
        )
        self.camera_sync.registerCallback(self.camera_callback)

        # Point cloud for obstacle detection
        self.pointcloud_sub = self.create_subscription(
            PointCloud2,
            '/isaac_ros/pointcloud',
            self.pointcloud_callback,
            QoSProfile(depth=5, reliability=ReliabilityPolicy.BEST_EFFORT)
        )

    def setup_publishers(self):
        """Set up all publishers for perception outputs"""
        # Fused pose publisher
        self.fused_pose_pub = self.create_publisher(
            PoseWithCovarianceStamped,
            '/fused_localization/pose',
            10
        )

        # Social costmap publisher
        self.social_costmap_pub = self.create_publisher(
            OccupancyGrid,
            '/social_navigation/costmap',
            10
        )

        # Detected humans publisher
        self.humans_pub = self.create_publisher(
            PoseArray,
            '/detected_humans',
            10
        )

        # Perception debug visualization
        self.debug_pub = self.create_publisher(
            MarkerArray,
            '/perception/debug',
            10
        )

        # Balance status publisher
        self.balance_status_pub = self.create_publisher(
            Bool,
            '/balance/status',
            10
        )

    def vslam_pose_callback(self, msg: PoseStamped):
        """Handle VSLAM pose updates"""
        with self.processing_lock:
            self.current_vslam_pose = msg

    def imu_callback(self, msg: Imu):
        """Handle IMU data for balance and orientation"""
        with self.processing_lock:
            self.current_imu_data = msg

        # Check balance status
        self.check_balance_status(msg)

    def odom_callback(self, msg: Odometry):
        """Handle odometry data"""
        with self.processing_lock:
            self.current_odom_data = msg

    def camera_callback(self, image_msg: Image, info_msg: CameraInfo):
        """Handle synchronized camera data"""
        with self.processing_lock:
            self.current_camera_data = (image_msg, info_msg)

        # Process image for human detection
        if self.get_parameter('enable_social_navigation').value:
            self.process_image_for_humans(image_msg, info_msg)

    def pointcloud_callback(self, msg: PointCloud2):
        """Handle point cloud data for obstacle detection"""
        with self.processing_lock:
            self.current_pointcloud_data = msg

        # Process point cloud for dynamic obstacle detection
        if self.get_parameter('enable_dynamic_obstacle_detection').value:
            self.process_pointcloud_for_obstacles(msg)

    def process_sensor_data(self):
        """Main processing loop for sensor fusion and perception"""
        start_time = time.time()

        # Perform sensor fusion if all required data is available
        if self.all_sensor_data_available():
            fused_pose = self.fuse_sensor_data()
            if fused_pose:
                self.publish_fused_pose(fused_pose)

        # Update social costmap if humans are detected
        if self.detected_humans:
            social_costmap = self.create_social_costmap()
            if social_costmap:
                self.social_costmap_pub.publish(social_costmap)

        # Create debug visualization
        self.create_debug_visualization()

        # Check processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        if processing_time > self.get_parameter('max_processing_time_ms').value:
            self.get_logger().warn(f"Perception processing took {processing_time:.1f}ms, exceeding budget")

    def all_sensor_data_available(self) -> bool:
        """Check if all required sensor data is available"""
        return all([
            self.current_vslam_pose,
            self.current_imu_data,
            self.current_odom_data
        ])

    def fuse_sensor_data(self) -> Optional[PoseWithCovarianceStamped]:
        """Fuse VSLAM, IMU, and odometry data"""
        if not self.all_sensor_data_available():
            return None

        # Get weights from parameters
        vslam_weight = self.get_parameter('vslam_weight').value
        imu_weight = self.get_parameter('imu_weight').value
        odom_weight = self.get_parameter('odom_weight').value

        # Extract positions from different sources
        vslam_pos = np.array([
            self.current_vslam_pose.pose.position.x,
            self.current_vslam_pose.pose.position.y,
            self.current_vslam_pose.pose.position.z
        ])
        vslam_orient = self.current_vslam_pose.pose.orientation

        odom_pos = np.array([
            self.current_odom_data.pose.pose.position.x,
            self.current_odom_data.pose.pose.position.y,
            self.current_odom_data.pose.pose.position.z
        ])
        odom_orient = self.current_odom_data.pose.pose.orientation

        # Weighted fusion for position
        total_weight = vslam_weight + odom_weight
        fused_pos = (
            vslam_weight * vslam_pos + odom_weight * odom_pos
        ) / total_weight

        # For orientation, use VSLAM with IMU correction
        fused_orient = self.correct_orientation_with_imu(
            vslam_orient, self.current_imu_data
        )

        # Create fused pose message
        fused_pose = PoseWithCovarianceStamped()
        fused_pose.header.stamp = self.get_clock().now().to_msg()
        fused_pose.header.frame_id = "map"
        fused_pose.pose.pose.position.x = fused_pos[0]
        fused_pose.pose.pose.position.y = fused_pos[1]
        fused_pose.pose.pose.position.z = fused_pos[2]
        fused_pose.pose.pose.orientation = fused_orient
        fused_pose.pose.covariance = self.calculate_fused_covariance()

        return fused_pose

    def correct_orientation_with_imu(self, vslam_orientation, imu_data):
        """Correct orientation using IMU data"""
        # Extract roll and pitch from IMU (for gravity compensation)
        # This is a simplified approach - in practice, proper sensor fusion would be used
        imu_roll, imu_pitch, _ = self.quaternion_to_euler(
            imu_data.orientation.x,
            imu_data.orientation.y,
            imu_data.orientation.z,
            imu_data.orientation.w
        )

        # Use VSLAM yaw with IMU roll/pitch correction
        corrected_quat = self.euler_to_quaternion(
            imu_roll, imu_pitch, self.get_yaw_from_quaternion(vslam_orientation)
        )

        return corrected_quat

    def calculate_fused_covariance(self):
        """Calculate covariance for fused pose estimate"""
        # Simplified covariance calculation based on sensor characteristics
        vslam_uncertainty = 0.05  # meters
        imu_uncertainty = 0.02    # meters (for orientation correction)

        covariance = [0.0] * 36  # 6x6 covariance matrix

        # Set diagonal elements
        covariance[0] = vslam_uncertainty**2   # x
        covariance[7] = vslam_uncertainty**2   # y
        covariance[14] = vslam_uncertainty**2  # z
        covariance[21] = imu_uncertainty**2    # roll
        covariance[28] = imu_uncertainty**2    # pitch
        covariance[35] = vslam_uncertainty**2  # yaw (using VSLAM uncertainty)

        return covariance

    def process_image_for_humans(self, image_msg: Image, camera_info: CameraInfo):
        """Process image for human detection"""
        try:
            # Convert ROS image to OpenCV
            cv_image = self.cv_bridge.imgmsg_to_cv2(image_msg, "bgr8")

            # Detect humans in image (placeholder - would use Isaac ROS detection)
            humans_in_image = self.detect_humans_in_image(cv_image)

            # Convert image coordinates to world coordinates
            for human in humans_in_image:
                world_pose = self.image_to_world_coordinates(
                    human.center_x, human.center_y, camera_info
                )

                # Add to detected humans if not already present
                if not self.is_duplicate_human(world_pose):
                    self.detected_humans.append(world_pose)

        except Exception as e:
            self.get_logger().error(f"Error processing image for human detection: {e}")

    def detect_humans_in_image(self, cv_image):
        """Detect humans in image using Isaac ROS components (placeholder)"""
        # This would normally use Isaac ROS vision components
        # For this example, return empty list
        # In practice: use Isaac ROS object detection or human detection
        detected_humans = []

        # Example: Use OpenCV HOG descriptor as placeholder
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

        boxes, weights = hog.detectMultiScale(cv_image, winStride=(8, 8))

        for (x, y, w, h) in boxes:
            center_x = x + w // 2
            center_y = y + h // 2

            # Create human detection object (simplified)
            human = type('HumanDetection', (), {
                'center_x': center_x,
                'center_y': center_y
            })()

            detected_humans.append(human)

        return detected_humans

    def image_to_world_coordinates(self, u, v, camera_info):
        """Convert image coordinates to world coordinates"""
        # Get camera intrinsic parameters
        fx = camera_info.k[0]  # focal length x
        fy = camera_info.k[4]  # focal length y
        cx = camera_info.k[2]  # principal point x
        cy = camera_info.k[5]  # principal point y

        # Convert pixel coordinates to normalized coordinates
        x_norm = (u - cx) / fx
        y_norm = (v - cy) / fy

        # For this example, assume fixed depth (would use depth camera in practice)
        depth = 2.0  # meters (placeholder)

        # Convert to 3D world coordinates relative to camera
        x_cam = x_norm * depth
        y_cam = y_norm * depth
        z_cam = depth

        # Transform from camera frame to robot base frame
        # This would involve TF transforms in practice
        # For now, assume camera is at fixed offset from base
        camera_offset_x = 0.0
        camera_offset_y = 0.0
        camera_offset_z = 1.5  # 1.5m above ground

        x_world = x_cam + camera_offset_x
        y_world = y_cam + camera_offset_y
        z_world = z_cam + camera_offset_z

        # Create pose
        pose = Pose()
        pose.position.x = x_world
        pose.position.y = y_world
        pose.position.z = z_world
        pose.orientation.w = 1.0  # No rotation

        return pose

    def is_duplicate_human(self, new_pose, threshold=0.5):
        """Check if new pose is duplicate of existing human detection"""
        for existing_pose in self.detected_humans:
            distance = math.sqrt(
                (new_pose.position.x - existing_pose.position.x)**2 +
                (new_pose.position.y - existing_pose.position.y)**2
            )
            if distance < threshold:
                return True
        return False

    def process_pointcloud_for_obstacles(self, pointcloud_msg):
        """Process point cloud for dynamic obstacle detection"""
        # This would use Isaac ROS point cloud processing
        # For now, we'll just count points as a placeholder
        # In practice: use Isaac ROS point cloud utilities for clustering and tracking

        # Placeholder: extract some information from point cloud
        # In real implementation, this would use Isaac ROS components
        pass

    def create_social_costmap(self) -> OccupancyGrid:
        """Create social navigation costmap from detected humans"""
        if not self.detected_humans:
            return None

        # Create costmap with social zones around humans
        costmap = OccupancyGrid()
        costmap.header.stamp = self.get_clock().now().to_msg()
        costmap.header.frame_id = "map"
        costmap.info.resolution = 0.05  # 5cm resolution
        costmap.info.width = 200  # 10m x 10m at 5cm resolution
        costmap.info.height = 200
        # Set origin to center around robot
        costmap.info.origin.position.x = -5.0
        costmap.info.origin.position.y = -5.0

        # Initialize with zeros
        costmap.data = [0] * (costmap.info.width * costmap.info.height)

        # Add personal space around each detected human
        personal_space_radius = self.get_parameter('personal_space_radius').value
        personal_space_cells = int(personal_space_radius / costmap.info.resolution)

        for human_pose in self.detected_humans:
            # Convert human pose to map coordinates
            map_x = int((human_pose.position.x - costmap.info.origin.position.x) / costmap.info.resolution)
            map_y = int((human_pose.position.y - costmap.info.origin.position.y) / costmap.info.resolution)

            # Add cost in a radius around the human
            for dx in range(-personal_space_cells, personal_space_cells + 1):
                for dy in range(-personal_space_cells, personal_space_cells + 1):
                    if dx*dx + dy*dy <= personal_space_cells*personal_space_cells:
                        idx_x = map_x + dx
                        idx_y = map_y + dy

                        if (0 <= idx_x < costmap.info.width and
                            0 <= idx_y < costmap.info.height):
                            idx = idx_y * costmap.info.width + idx_x

                            # Calculate cost based on distance from human center
                            dist_from_center = math.sqrt(dx*dx + dy*dy) * costmap.info.resolution
                            cost = int(200 * (1.0 - min(1.0, dist_from_center / personal_space_radius)))

                            # Set cost (higher value = more costly to navigate through)
                            costmap.data[idx] = max(costmap.data[idx], cost)

        return costmap

    def check_balance_status(self, imu_data):
        """Check robot balance status from IMU data"""
        # Calculate tilt angles from IMU
        roll, pitch, _ = self.quaternion_to_euler(
            imu_data.orientation.x,
            imu_data.orientation.y,
            imu_data.orientation.z,
            imu_data.orientation.w
        )

        # Calculate tilt magnitude
        tilt_magnitude = math.sqrt(roll*roll + pitch*pitch)

        # Determine if within balance threshold
        balance_threshold = self.get_parameter('balance_threshold').value
        is_balanced = tilt_magnitude < balance_threshold

        # Publish balance status
        balance_msg = Bool()
        balance_msg.data = is_balanced
        self.balance_status_pub.publish(balance_msg)

        if not is_balanced:
            self.get_logger().warn(f"Robot balance exceeded threshold: {tilt_magnitude:.2f} > {balance_threshold:.2f}")

    def create_debug_visualization(self):
        """Create visualization markers for debugging perception"""
        if not self.detected_humans and not self.dynamic_obstacles:
            return

        markers = MarkerArray()
        marker_id = 0

        # Visualize detected humans
        for i, human_pose in enumerate(self.detected_humans):
            human_marker = Marker()
            human_marker.header.stamp = self.get_clock().now().to_msg()
            human_marker.header.frame_id = "map"
            human_marker.ns = "detected_humans"
            human_marker.id = marker_id
            human_marker.type = Marker.CYLINDER
            human_marker.action = Marker.ADD

            human_marker.pose = human_pose
            human_marker.scale.x = self.get_parameter('personal_space_radius').value * 2  # Diameter
            human_marker.scale.y = self.get_parameter('personal_space_radius').value * 2  # Diameter
            human_marker.scale.z = 1.8  # Human height
            human_marker.color.r = 0.0
            human_marker.color.g = 1.0
            human_marker.color.b = 0.0
            human_marker.color.a = 0.3  # Semi-transparent

            markers.markers.append(human_marker)
            marker_id += 1

        # Visualize social zones
        for i, human_pose in enumerate(self.detected_humans):
            zone_marker = Marker()
            zone_marker.header.stamp = self.get_clock().now().to_msg()
            zone_marker.header.frame_id = "map"
            zone_marker.ns = "social_zones"
            zone_marker.id = marker_id
            zone_marker.type = Marker.SPHERE
            zone_marker.action = Marker.ADD

            zone_marker.pose = human_pose
            social_radius = self.get_parameter('social_zone_radius').value
            zone_marker.scale.x = social_radius * 2
            zone_marker.scale.y = social_radius * 2
            zone_marker.scale.z = 0.1  # Flat circle
            zone_marker.color.r = 1.0
            zone_marker.color.g = 1.0
            zone_marker.color.b = 0.0
            zone_marker.color.a = 0.2  # More transparent

            markers.markers.append(zone_marker)
            marker_id += 1

        # Publish markers
        self.debug_pub.publish(markers)

    def publish_fused_pose(self, fused_pose: PoseWithCovarianceStamped):
        """Publish fused pose estimate"""
        self.fused_pose_pub.publish(fused_pose)

        # Broadcast transform
        self.broadcast_pose_transform(fused_pose)

    def broadcast_pose_transform(self, pose_msg: PoseWithCovarianceStamped):
        """Broadcast pose as transform"""
        t = TransformStamped()
        t.header.stamp = pose_msg.header.stamp
        t.header.frame_id = pose_msg.header.frame_id
        t.child_frame_id = "fused_odom"

        t.transform.translation.x = pose_msg.pose.pose.position.x
        t.transform.translation.y = pose_msg.pose.pose.position.y
        t.transform.translation.z = pose_msg.pose.pose.position.z
        t.transform.rotation = pose_msg.pose.pose.orientation

        self.tf_broadcaster.sendTransform(t)

    def quaternion_to_euler(self, x, y, z, w):
        """Convert quaternion to euler angles (roll, pitch, yaw)"""
        # Roll (x-axis rotation)
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        # Pitch (y-axis rotation)
        sinp = 2 * (w * y - z * x)
        if abs(sinp) >= 1:
            pitch = math.copysign(math.pi / 2, sinp)
        else:
            pitch = math.asin(sinp)

        # Yaw (z-axis rotation)
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        return roll, pitch, yaw

    def euler_to_quaternion(self, roll, pitch, yaw):
        """Convert euler angles to quaternion"""
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)

        w = cy * cr * cp + sy * sr * sp
        x = cy * sr * cp - sy * cr * sp
        y = cy * cr * sp + sy * sr * cp
        z = sy * cr * cp - cy * sr * sp

        # Create and normalize quaternion
        quat = geometry_msgs.msg.Quaternion()
        quat.x = x
        quat.y = y
        quat.z = z
        quat.w = w

        # Normalize
        norm = math.sqrt(x*x + y*y + z*z + w*w)
        if norm > 0:
            quat.x /= norm
            quat.y /= norm
            quat.z /= norm
            quat.w /= norm

        return quat

    def get_yaw_from_quaternion(self, orientation):
        """Extract yaw from quaternion orientation"""
        _, _, yaw = self.quaternion_to_euler(
            orientation.x, orientation.y, orientation.z, orientation.w
        )
        return yaw


def main(args=None):
    """Main function for Isaac ROS Perception Pipeline"""
    rclpy.init(args=args)

    perception_node = IsaacROSPerceptionPipeline()

    try:
        rclpy.spin(perception_node)
    except KeyboardInterrupt:
        perception_node.get_logger().info("Interrupted, shutting down...")
    finally:
        perception_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()