import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """
    Launch file for demonstrating physics concepts in Gazebo with ROS 2.
    This launch file loads a world with physics demonstrations and interacts with them.
    """

    # Launch configuration variables
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    world_name = LaunchConfiguration('world_name', default='physics_gravity_demo.world')

    # Declare launch arguments
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )

    declare_world_name = DeclareLaunchArgument(
        'world_name',
        default_value='physics_gravity_demo.world',
        description='Name of the Gazebo world to load for physics demonstration'
    )

    # Start Gazebo with physics demo world
    start_gazebo_cmd = ExecuteProcess(
        cmd=['gz', 'sim', '-r', '-v', '0', PathJoinSubstitution([
            FindPackageShare('your_simulation_package'),
            'worlds',
            world_name
        ])],
        output='screen'
    )

    # Example: Node that publishes to simulation topics to interact with physics
    physics_demo_node = Node(
        package='your_simulation_package',
        executable='physics_demo_node',
        name='physics_demo_node',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time
        }],
        remappings=[
            ('/cmd_vel', '/demo_robot/cmd_vel'),
            ('/joint_commands', '/demo_robot/joint_commands')
        ]
    )

    # TF broadcaster for demonstration
    tf_broadcaster_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='physics_demo_tf_broadcaster',
        arguments=['0', '0', '0', '0', '0', '0', 'world', 'physics_demo_frame'],
        parameters=[{
            'use_sim_time': use_sim_time
        }]
    )

    # Create launch description
    ld = LaunchDescription()

    # Add launch arguments
    ld.add_action(declare_use_sim_time)
    ld.add_action(declare_world_name)

    # Add launch actions
    ld.add_action(start_gazebo_cmd)
    ld.add_action(physics_demo_node)
    ld.add_action(tf_broadcaster_node)

    return ld