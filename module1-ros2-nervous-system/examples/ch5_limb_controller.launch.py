from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """
    Launch file for the humanoid limb controller case study.

    This launch file starts all the necessary nodes for the humanoid limb control system,
    including perception, planning, control, and safety components.
    """

    # Declare launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')

    # Create launch description
    ld = LaunchDescription()

    # Add launch arguments
    ld.add_action(
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'
        )
    )

    # Camera node (simulated or real)
    camera_node = Node(
        package='image_publisher',
        executable='image_publisher_node',
        name='camera_node',
        parameters=[
            {'filename': '/path/to/test_image.jpg'},
            {'publish_rate': 30.0},
            {'camera_info_url': 'package://my_robot_description/cameras/camera.yaml'}
        ],
        remappings=[
            ('image_raw', '/camera/image_raw'),
            ('camera_info', '/camera/camera_info')
        ],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # IMU node
    imu_node = Node(
        package='imu_tools',
        executable='imu_filter_node',
        name='imu_node',
        parameters=[
            {'use_mag': False},
            {'publish_tf': False}
        ],
        remappings=[
            ('imu/data_raw', '/imu/data_raw'),
            ('imu/data', '/imu/data')
        ],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # Object detection node
    object_detection_node = Node(
        package='vision_perception',
        executable='object_detection_node',
        name='object_detection_node',
        parameters=[
            {'detection_model': 'yolov5'},
            {'confidence_threshold': 0.7}
        ],
        remappings=[
            ('/camera/image_raw', '/camera/image_raw'),
            ('/detected_objects', '/detected_objects'),
            ('/object_pose', '/detected_object')
        ],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # Path planning node
    path_planner_node = Node(
        package='path_planning',
        executable='path_planner_node',
        name='path_planner_node',
        parameters=[
            {'planning_algorithm': 'rrt'},
            {'collision_checking': True},
            {'max_planning_time': 5.0}
        ],
        remappings=[
            ('/detected_object', '/detected_object'),
            ('/robot_state', '/joint_states'),
            ('/planned_trajectory', '/planned_trajectory')
        ],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # Inverse kinematics node
    ik_node = Node(
        package='kinematics',
        executable='inverse_kinematics_node',
        name='inverse_kinematics_node',
        parameters=[
            {'robot_description': 'robot_description'},
            {'kinematics_solver': 'kdl'}
        ],
        remappings=[
            ('/target_pose', '/planned_trajectory'),
            ('/joint_trajectory', '/joint_trajectory_command')
        ],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # Limb controller node (the main controller from our case study)
    limb_controller_node = Node(
        package='my_robot_control',
        executable='humanoid_limb_controller',
        name='left_arm_controller',
        parameters=[
            {'joint_names': ['joint_1', 'joint_2', 'joint_3', 'joint_4', 'joint_5', 'joint_6']},
            {'action_ns': 'follow_joint_trajectory'},
            {'default_goal_time_tolerance': 0.5},
            {'default_tolerances': {'position': [0.01, 0.01, 0.01, 0.01, 0.01, 0.01]}}
        ],
        remappings=[
            ('/left_arm/joint_commands', '/left_arm/joint_commands'),
            ('/left_arm/joint_states', '/joint_states')
        ],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # Joint state publisher (for visualization)
    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        parameters=[
            {'rate': 50},
            {'source_list': ['/joint_states']}
        ],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # Robot state publisher (to publish TFs)
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[
            {'robot_description': 'robot_description'}
        ],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # Collision detection node (safety)
    collision_detector = Node(
        package='collision_detection',
        executable='collision_detector_node',
        name='collision_detector',
        parameters=[
            {'robot_description': 'robot_description'},
            {'safety_margin': 0.1},
            {'check_self_collision': True}
        ],
        remappings=[
            ('/robot_state', '/joint_states'),
            ('/environment', '/detected_objects'),
            ('/collision_warning', '/collision_warning')
        ],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # Emergency stop node (safety)
    emergency_stop = Node(
        package='safety_system',
        executable='emergency_stop_node',
        name='emergency_stop',
        parameters=[
            {'stop_distance': 0.3},
            {'enable_collisions': True}
        ],
        remappings=[
            ('/collision_warning', '/collision_warning'),
            ('/emergency_stop', '/emergency_stop_command')
        ],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # Add all nodes to the launch description
    ld.add_action(camera_node)
    ld.add_action(imu_node)
    ld.add_action(object_detection_node)
    ld.add_action(path_planner_node)
    ld.add_action(ik_node)
    ld.add_action(limb_controller_node)
    ld.add_action(joint_state_publisher)
    ld.add_action(robot_state_publisher)
    ld.add_action(collision_detector)
    ld.add_action(emergency_stop)

    return ld