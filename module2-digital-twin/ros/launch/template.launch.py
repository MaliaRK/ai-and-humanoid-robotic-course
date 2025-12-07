import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """
    Template for a basic ROS 2 launch file for the Digital Twin module.
    This template includes common configurations and can be extended for specific use cases.
    """

    # Declare launch arguments
    ld = LaunchDescription()

    # Launch configuration variables
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    robot_name = LaunchConfiguration('robot_name', default='humanoid_robot')
    world_name = LaunchConfiguration('world_name', default='basic_environment')

    # Declare launch arguments
    ld.add_action(DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    ))

    ld.add_action(DeclareLaunchArgument(
        'robot_name',
        default_value='humanoid_robot',
        description='Name of the robot to spawn'
    ))

    ld.add_action(DeclareLaunchArgument(
        'world_name',
        default_value='basic_environment',
        description='Name of the Gazebo world to load'
    ))

    # Example: Spawn robot in Gazebo
    spawn_robot_node = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', robot_name,
            '-topic', 'robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.5'
        ],
        output='screen',
        condition=IfCondition(use_sim_time)
    )
    ld.add_action(spawn_robot_node)

    # Example: Robot State Publisher
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': '<!-- Robot description would be loaded from URDF -->'
        }]
    )
    ld.add_action(robot_state_publisher_node)

    # Example: Joint State Publisher (for simulation)
    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time
        }]
    )
    ld.add_action(joint_state_publisher_node)

    return ld