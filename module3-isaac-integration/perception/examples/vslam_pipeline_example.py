#!/usr/bin/env python3
"""
Example VSLAM pipeline for humanoid robots using Isaac ROS
This example demonstrates the integration of various perception components
for real-time visual SLAM on humanoid platforms.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image, CameraInfo, Imu
from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
import message_filters
import numpy as np
import cv2
from cv_bridge import CvBridge
import time
from typing import Optional, Tuple


class HumanoidVSLAMExample(Node):
    """
    Example implementation of a humanoid-optimized VSLAM pipeline
    using Isaac ROS components
    """

    def __init__(self):
        super().__init__('humanoid_vslam_example')

        # Initialize components
        self.bridge = CvBridge()
        self.tf_broadcaster = TransformBroadcaster(self)

        # Timing and performance
        self.last_process_time = time.time()
        self.fps_counter = 0
        self.fps_timer = self.create_timer(1.0, self.update_fps)

        # Humanoid-specific parameters
        self.declare_parameters()

        # Publishers
        self.pose_pub = self.create_publisher(PoseStamped, 'vslam/pose', 10)
        self.odom_pub = self.create_publisher(Odometry, 'vslam/odometry', 10)
        self.debug_pub = self.create_publisher(Image, 'vslam/debug', 5)

        # Subscribers with QoS profiles optimized for real-time processing
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5
        )

        # Image subscriptions
        self.left_image_sub = message_filters.Subscriber(
            self, Image, '/camera/left/image_rect_color', qos_profile=qos_profile
        )
        self.right_image_sub = message_filters.Subscriber(
            self, Image, '/camera/right/image_rect_color', qos_profile=qos_profile
        )

        # Camera info (for calibration)
        self.left_info_sub = message_filters.Subscriber(
            self, CameraInfo, '/camera/left/camera_info', qos_profile=qos_profile
        )
        self.right_info_sub = message_filters.Subscriber(
            self, CameraInfo, '/camera/right/camera_info', qos_profile=qos_profile
        )

        # IMU for motion compensation
        self.imu_sub = self.create_subscription(
            Imu, '/imu/data', self.imu_callback, 10
        )

        # Synchronize stereo image pairs
        self.stereo_sync = message_filters.ApproximateTimeSynchronizer(
            [self.left_image_sub, self.right_image_sub,
             self.left_info_sub, self.right_info_sub],
            queue_size=10,
            slop=0.1
        )
        self.stereo_sync.registerCallback(self.stereo_callback)

        # Internal state
        self.imu_data = None
        self.current_pose = np.eye(4)  # 4x4 transformation matrix
        self.is_tracking = False
        self.feature_points = []
        self.keyframes = []

        # Performance metrics
        self.processing_times = []
        self.fps_values = []

        self.get_logger().info("Humanoid VSLAM example node initialized")

    def declare_parameters(self):
        """Declare and initialize parameters"""
        self.declare_parameter('enable_balance_compensation', True)
        self.declare_parameter('enable_gait_compensation', True)
        self.declare_parameter('gait_frequency', 2.0)
        self.declare_parameter('max_features', 1500)
        self.declare_parameter('feature_quality', 0.01)
        self.declare_parameter('enable_imu_fusion', True)

    def imu_callback(self, msg: Imu):
        """Handle IMU data for motion compensation"""
        self.imu_data = {
            'linear_acceleration': np.array([
                msg.linear_acceleration.x,
                msg.linear_acceleration.y,
                msg.linear_acceleration.z
            ]),
            'angular_velocity': np.array([
                msg.angular_velocity.x,
                msg.angular_velocity.y,
                msg.angular_velocity.z
            ]),
            'orientation': np.array([
                msg.orientation.x,
                msg.orientation.y,
                msg.orientation.z,
                msg.orientation.w
            ])
        }

    def stereo_callback(self, left_msg: Image, right_msg: Image,
                       left_info: CameraInfo, right_info: CameraInfo):
        """Process synchronized stereo image pair"""
        start_time = time.time()

        try:
            # Convert ROS images to OpenCV
            left_cv = self.bridge.imgmsg_to_cv2(left_msg, desired_encoding='bgr8')
            right_cv = self.bridge.imgmsg_to_cv2(right_msg, desired_encoding='bgr8')

            # Preprocess for humanoid-specific motion
            left_processed = self.preprocess_for_humanoid(left_cv, self.imu_data)
            right_processed = self.preprocess_for_humanoid(right_cv, self.imu_data)

            # Perform VSLAM processing
            pose_update, features = self.process_vslam(
                left_processed, right_processed, left_info, right_info
            )

            # Update current pose
            if pose_update is not None:
                self.current_pose = self.update_pose(self.current_pose, pose_update)

                # Publish results
                self.publish_pose_and_odometry(self.current_pose, left_msg.header)

            # Publish debug visualization
            if len(features) > 0:
                debug_image = self.create_debug_visualization(
                    left_cv, features, self.current_pose
                )
                debug_msg = self.bridge.cv2_to_imgmsg(debug_image, encoding='bgr8')
                debug_msg.header = left_msg.header
                self.debug_pub.publish(debug_msg)

            # Performance tracking
            process_time = time.time() - start_time
            self.processing_times.append(process_time)
            if len(self.processing_times) > 100:
                self.processing_times.pop(0)

        except Exception as e:
            self.get_logger().error(f"Error in stereo callback: {e}")

    def preprocess_for_humanoid(self, image: np.ndarray, imu_data: Optional[dict]):
        """Preprocess image specifically for humanoid motion patterns"""
        # If we have IMU data, compensate for balance-related motion
        if imu_data is not None and self.get_parameter('enable_balance_compensation').value:
            # Apply motion compensation based on IMU
            image = self.compensate_balance_motion(image, imu_data)

        # Stabilize image for head nodding/swaying
        image = self.stabilize_head_motion(image)

        return image

    def compensate_balance_motion(self, image: np.ndarray, imu_data: dict) -> np.ndarray:
        """Compensate for humanoid balance-related motion using IMU"""
        # Extract angular velocity for motion compensation
        angular_vel = imu_data['angular_velocity']

        # Simple motion compensation based on angular velocity
        # In practice, this would use more sophisticated compensation
        dt = 1.0 / 30.0  # Assuming 30 FPS

        # Calculate rotation compensation
        rotation_matrix = np.eye(3)
        rotation_matrix[0, 0] = np.cos(angular_vel[2] * dt)
        rotation_matrix[0, 1] = -np.sin(angular_vel[2] * dt)
        rotation_matrix[1, 0] = np.sin(angular_vel[2] * dt)
        rotation_matrix[1, 1] = np.cos(angular_vel[2] * dt)

        # Apply affine transformation for compensation
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, 0, 1.0)
        rotation_matrix[0, 2] += angular_vel[2] * dt * w * 0.1  # Horizontal compensation
        rotation_matrix[1, 2] += angular_vel[0] * dt * h * 0.1  # Vertical compensation

        compensated_image = cv2.warpAffine(
            image, rotation_matrix, (w, h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE
        )

        return compensated_image

    def stabilize_head_motion(self, image: np.ndarray) -> np.ndarray:
        """Apply simple image stabilization for head motion"""
        # This is a simplified version
        # In practice, this would use more sophisticated stabilization
        # based on neck/head kinematics or IMU data
        return image

    def process_vslam(self, left_img: np.ndarray, right_img: np.ndarray,
                     left_info: CameraInfo, right_info: CameraInfo) -> Tuple[Optional[np.ndarray], list]:
        """Perform VSLAM processing on stereo images"""
        # Feature detection (humanoid-optimized)
        features = self.detect_humanoid_features(left_img)

        # Stereo matching for depth
        disparity = self.compute_stereo_disparity(left_img, right_img)

        # Pose estimation using features and depth
        pose_update = self.estimate_pose_with_features(
            features, disparity, left_info, right_info
        )

        return pose_update, features

    def detect_humanoid_features(self, image: np.ndarray) -> list:
        """Detect features with humanoid-specific optimizations"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Use FAST feature detector with humanoid-specific parameters
        max_features = self.get_parameter('max_features').value
        quality_level = self.get_parameter('feature_quality').value

        # Focus on human-relevant areas (center of image)
        h, w = gray.shape
        center_region = gray[int(h*0.2):int(h*0.8), int(w*0.2):int(w*0.8)]

        # Detect features in center region with higher priority
        center_features = cv2.FastFeatureDetector_create(
            threshold=20,
            nonmaxSuppression=True
        ).detect(center_region)

        # Also detect some features in full image
        all_features = cv2.FastFeatureDetector_create(
            threshold=30,  # Higher threshold for full image
            nonmaxSuppression=True
        ).detect(gray)

        # Combine and limit features
        combined_features = center_features + all_features
        combined_features = sorted(
            combined_features,
            key=lambda x: x.response,
            reverse=True
        )[:max_features]

        # Adjust coordinates for center region features
        for feature in combined_features:
            if hasattr(feature, 'pt'):
                # Add offset for center region features
                if (int(h*0.2) <= feature.pt[1] < int(h*0.8) and
                    int(w*0.2) <= feature.pt[0] < int(w*0.8)):
                    # Already in correct coordinate system

        return combined_features[:max_features]

    def compute_stereo_disparity(self, left_img: np.ndarray, right_img: np.ndarray) -> np.ndarray:
        """Compute stereo disparity map"""
        # Convert to grayscale
        left_gray = cv2.cvtColor(left_img, cv2.COLOR_BGR2GRAY)
        right_gray = cv2.cvtColor(right_img, cv2.COLOR_BGR2GRAY)

        # Create stereo matcher (SGBM for better quality)
        stereo = cv2.StereoSGBM_create(
            minDisparity=0,
            numDisparities=128,
            blockSize=9,
            P1=8 * 3 * 9**2,
            P2=32 * 3 * 9**2,
            disp12MaxDiff=1,
            uniquenessRatio=15,
            speckleWindowSize=0,
            speckleRange=2,
            preFilterCap=63,
            mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
        )

        # Compute disparity
        disparity = stereo.compute(left_gray, right_gray).astype(np.float32) / 16.0

        return disparity

    def estimate_pose_with_features(self, features: list, disparity: np.ndarray,
                                  left_info: CameraInfo, right_info: CameraInfo) -> Optional[np.ndarray]:
        """Estimate pose change using features and stereo information"""
        if len(features) < 10:
            return None

        # This is a simplified pose estimation
        # In practice, this would use full VSLAM pipeline
        pose_change = np.eye(4)
        pose_change[0, 3] = 0.01  # Small forward movement as example

        return pose_change

    def update_pose(self, current_pose: np.ndarray, pose_update: np.ndarray) -> np.ndarray:
        """Update global pose with new pose change"""
        return np.dot(current_pose, pose_update)

    def publish_pose_and_odometry(self, pose: np.ndarray, header):
        """Publish pose and odometry messages"""
        # Create PoseStamped message
        pose_msg = PoseStamped()
        pose_msg.header = header
        pose_msg.header.frame_id = 'map'

        # Extract position and orientation from transformation matrix
        pose_msg.pose.position.x = pose[0, 3]
        pose_msg.pose.position.y = pose[1, 3]
        pose_msg.pose.position.z = pose[2, 3]

        # Convert rotation matrix to quaternion
        rotation_matrix = pose[:3, :3]
        quat = self.rotation_matrix_to_quaternion(rotation_matrix)
        pose_msg.pose.orientation.x = quat[0]
        pose_msg.pose.orientation.y = quat[1]
        pose_msg.pose.orientation.z = quat[2]
        pose_msg.pose.orientation.w = quat[3]

        self.pose_pub.publish(pose_msg)

        # Create Odometry message
        odom_msg = Odometry()
        odom_msg.header = header
        odom_msg.header.frame_id = 'odom'
        odom_msg.child_frame_id = 'base_link'

        odom_msg.pose.pose = pose_msg.pose

        self.odom_pub.publish(odom_msg)

        # Broadcast TF transform
        self.broadcast_transform(pose_msg, header.frame_id)

    def rotation_matrix_to_quaternion(self, R: np.ndarray) -> np.ndarray:
        """Convert 3x3 rotation matrix to quaternion"""
        # Method from: http://www.euclideanspace.com/maths/geometry/rotations/conversions/matrixToQuaternion/
        trace = np.trace(R)

        if trace > 0:
            s = np.sqrt(trace + 1.0) * 2  # s = 4 * qw
            qw = 0.25 * s
            qx = (R[2, 1] - R[1, 2]) / s
            qy = (R[0, 2] - R[2, 0]) / s
            qz = (R[1, 0] - R[0, 1]) / s
        else:
            if R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
                s = np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2
                qw = (R[2, 1] - R[1, 2]) / s
                qx = 0.25 * s
                qy = (R[0, 1] + R[1, 0]) / s
                qz = (R[0, 2] + R[2, 0]) / s
            elif R[1, 1] > R[2, 2]:
                s = np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2
                qw = (R[0, 2] - R[2, 0]) / s
                qx = (R[0, 1] + R[1, 0]) / s
                qy = 0.25 * s
                qz = (R[1, 2] + R[2, 1]) / s
            else:
                s = np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2
                qw = (R[1, 0] - R[0, 1]) / s
                qx = (R[0, 2] + R[2, 0]) / s
                qy = (R[1, 2] + R[2, 1]) / s
                qz = 0.25 * s

        return np.array([qx, qy, qz, qw])

    def broadcast_transform(self, pose_msg: PoseStamped, parent_frame: str):
        """Broadcast transform from map to base_link"""
        from geometry_msgs.msg import TransformStamped

        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = parent_frame
        t.child_frame_id = 'base_link'

        t.transform.translation.x = pose_msg.pose.position.x
        t.transform.translation.y = pose_msg.pose.position.y
        t.transform.translation.z = pose_msg.pose.position.z

        t.transform.rotation = pose_msg.pose.orientation

        self.tf_broadcaster.sendTransform(t)

    def create_debug_visualization(self, image: np.ndarray, features: list, pose: np.ndarray) -> np.ndarray:
        """Create debug visualization with features and pose info"""
        vis_image = image.copy()

        # Draw features
        for feature in features[:100]:  # Limit to 100 features for performance
            pt = (int(feature.pt[0]), int(feature.pt[1]))
            cv2.circle(vis_image, pt, 3, (0, 255, 0), -1)

        # Add pose information text
        cv2.putText(vis_image, f'X: {pose[0,3]:.2f}m', (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(vis_image, f'Y: {pose[1,3]:.2f}m', (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(vis_image, f'Z: {pose[2,3]:.2f}m', (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Add FPS information
        if len(self.processing_times) > 0:
            avg_time = sum(self.processing_times) / len(self.processing_times)
            fps = 1.0 / avg_time if avg_time > 0 else 0
            cv2.putText(vis_image, f'FPS: {fps:.1f}', (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        return vis_image

    def update_fps(self):
        """Update FPS counter"""
        current_time = time.time()
        if current_time > self.last_process_time:
            fps = self.fps_counter / (current_time - self.last_process_time)
            self.fps_values.append(fps)
            if len(self.fps_values) > 10:
                self.fps_values.pop(0)

            avg_fps = sum(self.fps_values) / len(self.fps_values) if self.fps_values else 0
            self.get_logger().info(f'Average FPS: {avg_fps:.1f}')

        self.last_process_time = current_time
        self.fps_counter = 0


def main(args=None):
    """Main function to run the humanoid VSLAM example"""
    rclpy.init(args=args)

    vslam_node = HumanoidVSLAMExample()

    try:
        rclpy.spin(vslam_node)
    except KeyboardInterrupt:
        pass
    finally:
        vslam_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()