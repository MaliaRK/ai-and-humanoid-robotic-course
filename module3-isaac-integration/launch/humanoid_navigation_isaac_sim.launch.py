<launch>
  <!-- Isaac Sim Humanoid Navigation Scene Launch File -->

  <!-- Arguments -->
  <arg name="headless" default="False" description="Run in headless mode"/>
  <arg name="enable_cameras" default="True" description="Enable camera sensors"/>
  <arg name="enable_lidar" default="True" description="Enable LiDAR sensors"/>
  <arg name="enable_imu" default="True" description="Enable IMU sensors"/>
  <arg name="scene_config" default="$(find-pkg-share module3_isaac_integration)/config/humanoid_navigation_scene.yaml" description="Path to scene configuration file"/>
  <arg name="robot_model" default="humanoid" description="Robot model to use"/>
  <arg name="map_frame" default="map" description="Map frame name"/>
  <arg name="odom_frame" default="odom" description="Odometry frame name"/>
  <arg name="base_frame" default="base_link" description="Base frame name"/>

  <!-- Set environment variables -->
  <env name="ISAAC_ROS_PATH" value="$(env ISAAC_ROS_PATH)" />
  <env name="OMNIVERSE_HEADLESS" value="$(var headless)" />

  <!-- Isaac Sim Application -->
  <node
    pkg="isaac_ros_sim"
    exec="isaac_ros_sim_entrypoint"
    name="isaac_ros_sim"
    output="screen">

    <param name="headless" value="$(var headless)"/>
    <param name="enable_cameras" value="$(var enable_cameras)"/>
    <param name="enable_lidar" value="$(var enable_lidar)"/>
    <param name="enable_imu" value="$(var enable_imu)"/>
    <param name="scene_config" value="$(var scene_config)"/>
    <param name="robot_model" value="$(var robot_model)"/>

    <!-- ROS Bridge parameters -->
    <param name="ros_bridge.enable" value="true"/>
    <param name="ros_bridge.namespace" value=""/>
    <param name="ros_bridge.clock_publish_frequency" value="60.0"/>
    <param name="ros_bridge.publish_robot_description" value="true"/>
    <param name="ros_bridge.publish_tf" value="true"/>
    <param name="ros_bridge.tf_publish_frequency" value="50.0"/>

    <!-- Isaac ROS extensions -->
    <param name="extensions.visual_slam.enable" value="true"/>
    <param name="extensions.visual_slam.input_camera" value="head_camera"/>
    <param name="extensions.visual_slam.publish_map" value="true"/>
    <param name="extensions.visual_slam.map_frame" value="vslam_map"/>
    <param name="extensions.visual_slam.pose_frame" value="vslam_odom"/>

    <param name="extensions.apriltag.enable" value="true"/>
    <param name="extensions.apriltag.input_camera" value="head_camera"/>
    <param name="extensions.apriltag.family" value="36h11"/>

    <param name="extensions.pointcloud.enable" value="true"/>
    <param name="extensions.pointcloud.input_lidar" value="navigation_lidar"/>
    <param name="extensions.pointcloud.publish_pointcloud" value="true"/>
  </node>

  <!-- Isaac ROS Visual SLAM Node -->
  <node
    pkg="isaac_ros_visual_slam"
    exec="visual_slam_node"
    name="visual_slam"
    namespace="isaac_ros"
    output="screen"
    respawn="false">

    <param name="enable_rectified_edge" value="true"/>
    <param name="enable_debug" value="false"/>
    <param name="input_camera_matrix_topic_name" value="/head_camera/camera_info"/>
    <param name="input_image_topic_name" value="/head_camera/image_rect_color"/>
    <param name="map_frame" value="$(var map_frame)"/>
    <param name="odom_frame" value="$(var odom_frame)"/>
    <param name="base_frame" value="$(var base_frame)"/>
    <param name="publish_odom_tf" value="true"/>
    <param name="publish_map_tf" value="true"/>
    <param name="min_num_features" value="1000"/>
    <param name="max_num_features" value="2000"/>
    <param name="enable_localization" value="true"/>
    <param name="enable_mapping" value="true"/>
  </node>

  <!-- Isaac ROS AprilTag Node -->
  <node
    pkg="isaac_ros_apriltag"
    exec="apriltag_node"
    name="apriltag"
    namespace="isaac_ros"
    output="screen"
    respawn="false">

    <param name="family" value="36h11"/>
    <param name="max_tags" value="10"/>
    <param name="tag36h11_size" value="0.166"/>
    <param name="camera_frame" value="head_camera"/>
    <param name="input_image_width" value="640"/>
    <param name="input_image_height" value="480"/>
  </node>

  <!-- Isaac ROS PointCloud Node -->
  <node
    pkg="isaac_ros_pointcloud_utils"
    exec="pointcloud"
    name="pointcloud"
    namespace="isaac_ros"
    output="screen"
    respawn="false">

    <param name="input_topic_pointcloud" value="/navigation_lidar/point_cloud"/>
    <param name="output_topic_pointcloud" value="/isaac_ros/pointcloud"/>
    <param name="queue_size" value="1"/>
  </node>

  <!-- TF Static Transforms -->
  <!-- Robot base to camera -->
  <node
    pkg="tf2_ros"
    exec="static_transform_publisher"
    name="base_to_head_camera"
    args="0.0 0.0 1.5 0.0 0.0 0.0 $(var base_frame) head_camera" />

  <!-- Robot base to IMU -->
  <node
    pkg="tf2_ros"
    exec="static_transform_publisher"
    name="base_to_imu"
    args="0.0 0.0 0.8 0.0 0.0 0.0 $(var base_frame) torso_imu" />

  <!-- Robot base to LiDAR -->
  <node
    pkg="tf2_ros"
    exec="static_transform_publisher"
    name="base_to_lidar"
    args="0.0 0.0 1.0 0.0 0.0 0.0 $(var base_frame) navigation_lidar" />

  <!-- Navigation2 Stack -->
  <include file="$(find-pkg-share nav2_bringup)/launch/navigation_launch.py">
    <arg name="use_sim_time" value="True"/>
    <arg name="params_file" value="$(find-pkg-share module3_isaac_integration)/config/nav2_params_humanoid.yaml"/>
  </include>

  <!-- AMCL Localization -->
  <node
    pkg="nav2_amcl"
    exec="amcl"
    name="amcl"
    output="screen">

    <param name="use_sim_time" value="True"/>
    <param name="set_initial_pose" value="True"/>
    <param name="initial_pose_x" value="0.0"/>
    <param name="initial_pose_y" value="0.0"/>
    <param name="initial_pose_z" value="0.0"/>
    <param name="initial_pose_yaw" value="0.0"/>
    <param name="global_frame_id" value="$(var map_frame)"/>
    <param name="odom_frame_id" value="$(var odom_frame)"/>
    <param name="base_frame_id" value="$(var base_frame)"/>
  </node>

  <!-- Map Server -->
  <node
    pkg="nav2_map_server"
    exec="map_server"
    name="map_server"
    output="screen">

    <param name="use_sim_time" value="True"/>
    <param name="yaml_filename" value="$(find-pkg-share module3_isaac_integration)/maps/humanoid_navigation_map.yaml"/>
  </node>

  <!-- Lifecycle Manager -->
  <node
    pkg="nav2_lifecycle_manager"
    exec="lifecycle_manager"
    name="lifecycle_manager"
    output="screen">

    <param name="use_sim_time" value="True"/>
    <param name="autostart" value="True"/>
    <param name="node_names" value="[map_server, amcl, controller_server, planner_server, behavior_server, bt_navigator]"/>
  </node>

  <!-- Isaac ROS Perception Integration Node -->
  <node
    pkg="module3_isaac_integration"
    exec="isaac_ros_perception_pipeline"
    name="isaac_ros_perception_integration"
    output="screen">

    <param name="enable_sensor_fusion" value="True"/>
    <param name="vslam_weight" value="0.7"/>
    <param name="imu_weight" value="0.2"/>
    <param name="odom_weight" value="0.1"/>
    <param name="social_zone_radius" value="0.8"/>
    <param name="personal_space_radius" value="0.4"/>
    <param name="max_processing_time_ms" value="33.0"/>
  </node>

</launch>