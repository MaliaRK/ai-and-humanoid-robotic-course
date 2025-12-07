import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """
    Launch file for demonstrating sensor simulation in Gazebo with ROS 2.
    This launch file shows how to integrate various sensors with the simulation.
    """

    # Launch configuration variables
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    robot_name = LaunchConfiguration('robot_name', default='sensor_demo_robot')

    # Declare launch arguments
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )

    declare_robot_name = DeclareLaunchArgument(
        'robot_name',
        default_value='sensor_demo_robot',
        description='Name of the robot with sensors to spawn'
    )

    # Start Gazebo with empty world
    start_gazebo_cmd = ExecuteProcess(
        cmd=['gz', 'sim', '-r', '-v', '0', PathJoinSubstitution([
            FindPackageShare('gazebo_ros'),
            'worlds',
            'empty.sdf'
        ])],
        output='screen'
    )

    # Robot State Publisher with sensor-equipped robot
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': '<robot name="sensor_demo_robot">' +
                               '<link name="base_link">' +
                               '<visual><geometry><box size="0.5 0.5 0.2"/></geometry></visual>' +
                               '<collision><geometry><box size="0.5 0.5 0.2"/></geometry></collision>' +
                               '</link>' +
                               '<link name="camera_link">' +
                               '<visual><geometry><box size="0.05 0.05 0.05"/></geometry></visual>' +
                               '</link>' +
                               '<joint name="camera_joint" type="fixed">' +
                               '<parent link="base_link"/><child link="camera_link"/>' +
                               '<origin xyz="0.2 0 0.1" rpy="0 0 0"/></joint>' +
                               '</robot>'
        }]
    )

    # Spawn robot in Gazebo
    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', robot_name,
            '-topic', 'robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.1'
        ],
        output='screen'
    )

    # Example sensor data processing node
    sensor_processor_node = Node(
        package='your_sensor_package',
        executable='sensor_processor',
        name='sensor_processor',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time
        }],
        remappings=[
            ('/camera/image_raw', '/sensor_demo_robot/camera/image_raw'),
            ('/scan', '/sensor_demo_robot/scan'),
            ('/imu/data', '/sensor_demo_robot/imu/data')
        ]
    )

    # Create launch description
    ld = LaunchDescription()

    # Add launch arguments
    ld.add_action(declare_use_sim_time)
    ld.add_action(declare_robot_name)

    # Add launch actions
    ld.add_action(start_gazebo_cmd)
    ld.add_action(robot_state_publisher_node)
    ld.add_action(spawn_robot)
    ld.add_action(sensor_processor_node)

    return ld