#!/usr/bin/env python3
"""
Isaac Sim Scene for Humanoid Robot Navigation Example
This script creates a navigation scene with humanoid robot, obstacles, and human agents
for testing navigation and collision avoidance algorithms.
"""

import argparse
import numpy as np
import omni
from omni.isaac.kit import SimulationApp
from omni.isaac.core import World
from omni.isaac.core.utils.stage import add_reference_to_stage, get_stage_units
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.prims import create_primitive, get_prim_at_path, set_targets
from omni.isaac.core.utils.carb import wait_on_queue
from omni.isaac.core.utils.bounds import compute_aabb
from pxr import Gf, Sdf, UsdGeom, UsdLux, UsdShade, UsdPhysics, PhysxSchema
from omni.physx import get_physx_interface
from omni.isaac.examples.base_sample import BaseSample
from omni.isaac.core.objects import DynamicCuboid, VisualCuboid
from omni.isaac.core.prims import RigidPrim, XFormPrim
from omni.isaac.core.materials import OmniPBR
import carb
import math


class HumanoidNavigationScene(BaseSample):
    def __init__(self):
        super().__init__()
        self.world = None
        self.humanoid_robot = None
        self.humans = []
        self.obstacles = []

        # Scene configuration
        self.scene_scale = 1.0  # Units in meters
        self.room_dimensions = [8.0, 8.0, 3.0]  # width, depth, height
        self.robot_start_position = [0.0, 0.0, 0.0]

        # Humanoid robot specifications
        self.robot_height = 1.6  # meters
        self.robot_radius = 0.3  # meters (approximate cylindrical radius)

        # Navigation goals
        self.navigation_goals = [
            [2.0, 2.0, 0.0],
            [-1.5, 3.0, 0.0],
            [3.0, -2.0, 0.0],
            [-2.5, -3.0, 0.0]
        ]

    def setup_scene(self):
        """Set up the complete humanoid navigation scene"""
        self.world = self.get_world()

        # Set up the stage
        stage = omni.usd.get_context().get_stage()

        # Create ground plane
        self.create_ground_plane()

        # Create room environment
        self.create_room_environment()

        # Create humanoid robot
        self.create_humanoid_robot()

        # Create static obstacles
        self.create_static_obstacles()

        # Create human agents
        self.create_human_agents()

        # Create navigation goals
        self.create_navigation_goals()

        # Set up lighting
        self.setup_lighting()

        # Wait for physics to initialize
        self.world.reset()

    def create_ground_plane(self):
        """Create a ground plane for the scene"""
        # Create ground plane using Isaac's utility
        self.world.scene.add_default_ground_plane(
            "ground_plane",
            size=10.0,
            color=np.array([0.1, 0.1, 0.1])
        )

    def create_room_environment(self):
        """Create room environment with walls and ceiling"""
        # Create walls
        wall_thickness = 0.2
        wall_height = self.room_dimensions[2]

        # Left wall
        left_wall = VisualCuboid(
            prim_path="/World/Room/LeftWall",
            name="left_wall",
            position=np.array([-self.room_dimensions[0]/2 - wall_thickness/2, 0.0, wall_height/2]),
            size=np.array([wall_thickness, self.room_dimensions[1] + 2*wall_thickness, wall_height]),
            color=np.array([0.5, 0.5, 0.5])
        )
        self.world.scene.add_object(left_wall)

        # Right wall
        right_wall = VisualCuboid(
            prim_path="/World/Room/RightWall",
            name="right_wall",
            position=np.array([self.room_dimensions[0]/2 + wall_thickness/2, 0.0, wall_height/2]),
            size=np.array([wall_thickness, self.room_dimensions[1] + 2*wall_thickness, wall_height]),
            color=np.array([0.5, 0.5, 0.5])
        )
        self.world.scene.add_object(right_wall)

        # Front wall
        front_wall = VisualCuboid(
            prim_path="/World/Room/FrontWall",
            name="front_wall",
            position=np.array([0.0, -self.room_dimensions[1]/2 - wall_thickness/2, wall_height/2]),
            size=np.array([self.room_dimensions[0], wall_thickness, wall_height]),
            color=np.array([0.5, 0.5, 0.5])
        )
        self.world.scene.add_object(front_wall)

        # Back wall
        back_wall = VisualCuboid(
            prim_path="/World/Room/BackWall",
            name="back_wall",
            position=np.array([0.0, self.room_dimensions[1]/2 + wall_thickness/2, wall_height/2]),
            size=np.array([self.room_dimensions[0], wall_thickness, wall_height]),
            color=np.array([0.5, 0.5, 0.5])
        )
        self.world.scene.add_object(back_wall)

        # Ceiling
        ceiling = VisualCuboid(
            prim_path="/World/Room/Ceiling",
            name="ceiling",
            position=np.array([0.0, 0.0, wall_height + 0.05]),  # Slightly above to avoid z-fighting
            size=np.array([self.room_dimensions[0], self.room_dimensions[1], 0.1]),
            color=np.array([0.7, 0.7, 0.7])
        )
        self.world.scene.add_object(ceiling)

    def create_humanoid_robot(self):
        """Create humanoid robot model"""
        # For this example, we'll create a simplified humanoid representation
        # In practice, you'd load a proper humanoid robot USD model

        # Create robot body (torso)
        robot_body = VisualCuboid(
            prim_path="/World/HumanoidRobot/Body",
            name="robot_body",
            position=np.array(self.robot_start_position),
            size=np.array([0.4, 0.3, self.robot_height * 0.6]),  # Torso dimensions
            color=np.array([0.2, 0.2, 0.8])  # Blue to distinguish from humans
        )
        self.world.scene.add_object(robot_body)

        # Create robot head
        robot_head = create_primitive(
            prim_path="/World/HumanoidRobot/Head",
            primitive_type="Sphere",
            position=np.array([self.robot_start_position[0],
                              self.robot_start_position[1],
                              self.robot_start_position[2] + self.robot_height * 0.6/2 + 0.15]),
            scale=np.array([0.15, 0.15, 0.15]),
            color=np.array([0.9, 0.9, 0.7])  # Light yellow
        )

        # Create robot limbs (simplified as cylinders)
        # Left arm
        left_upper_arm = create_primitive(
            prim_path="/World/HumanoidRobot/LeftUpperArm",
            primitive_type="Cylinder",
            position=np.array([self.robot_start_position[0] - 0.3,
                              self.robot_start_position[1],
                              self.robot_start_position[2] + 0.3]),
            scale=np.array([0.05, 0.2, 0.05]),
            rotation=np.array([0, 90, 0]),
            color=np.array([0.2, 0.2, 0.8])
        )

        # Right arm
        right_upper_arm = create_primitive(
            prim_path="/World/HumanoidRobot/RightUpperArm",
            primitive_type="Cylinder",
            position=np.array([self.robot_start_position[0] + 0.3,
                              self.robot_start_position[1],
                              self.robot_start_position[2] + 0.3]),
            scale=np.array([0.05, 0.2, 0.05]),
            rotation=np.array([0, 90, 0]),
            color=np.array([0.2, 0.2, 0.8])
        )

        # Legs would be added similarly...

        self.humanoid_robot = robot_body

    def create_static_obstacles(self):
        """Create static obstacles in the scene"""
        # Create various obstacles for navigation challenge

        # Column obstacle
        column = DynamicCuboid(
            prim_path="/World/Obstacles/Column",
            name="column_obstacle",
            position=np.array([1.0, 1.0, 0.5]),
            size=np.array([0.4, 0.4, 1.5]),
            color=np.array([0.8, 0.2, 0.2])  # Red
        )
        self.world.scene.add_object(column)
        self.obstacles.append(column)

        # Table obstacle
        table = DynamicCuboid(
            prim_path="/World/Obstacles/Table",
            name="table_obstacle",
            position=np.array([-2.0, -1.5, 0.4]),
            size=np.array([1.2, 0.8, 0.8]),
            color=np.array([0.6, 0.4, 0.2])  # Brown
        )
        self.world.scene.add_object(table)
        self.obstacles.append(table)

        # Chair obstacle
        chair = DynamicCuboid(
            prim_path="/World/Obstacles/Chair",
            name="chair_obstacle",
            position=np.array([2.5, -2.0, 0.3]),
            size=np.array([0.5, 0.5, 0.6]),
            color=np.array([0.3, 0.6, 0.3])  # Green
        )
        self.world.scene.add_object(chair)
        self.obstacles.append(chair)

    def create_human_agents(self):
        """Create human agents for social navigation testing"""
        human_positions = [
            [1.5, 2.0, 0.0],
            [-1.0, -2.0, 0.0],
            [2.5, 1.0, 0.0],
            [-2.0, 2.5, 0.0],
            [0.0, 3.0, 0.0]
        ]

        for i, pos in enumerate(human_positions):
            # Create human body (torso)
            human_body = VisualCuboid(
                prim_path=f"/World/Humans/Human{i}/Body",
                name=f"human_{i}_body",
                position=np.array([pos[0], pos[1], 0.8]),  # Average human torso height
                size=np.array([0.3, 0.25, 0.8]),  # Human torso approx
                color=np.array([0.9, 0.6, 0.2])  # Orange for humans
            )
            self.world.scene.add_object(human_body)

            # Create human head
            human_head = create_primitive(
                prim_path=f"/World/Humans/Human{i}/Head",
                primitive_type="Sphere",
                position=np.array([pos[0], pos[1], 1.4]),  # Head height
                scale=np.array([0.12, 0.12, 0.12]),
                color=np.array([0.95, 0.9, 0.85])  # Skin tone
            )

            # Create simple limbs
            human_l_arm = create_primitive(
                prim_path=f"/World/Humans/Human{i}/LeftArm",
                primitive_type="Cylinder",
                position=np.array([pos[0] - 0.25, pos[1], 0.9]),
                scale=np.array([0.04, 0.4, 0.04]),
                rotation=np.array([0, 90, 0]),
                color=np.array([0.9, 0.6, 0.2])
            )

            human_r_arm = create_primitive(
                prim_path=f"/World/Humans/Human{i}/RightArm",
                primitive_type="Cylinder",
                position=np.array([pos[0] + 0.25, pos[1], 0.9]),
                scale=np.array([0.04, 0.4, 0.04]),
                rotation=np.array([0, 90, 0]),
                color=np.array([0.9, 0.6, 0.2])
            )

            self.humans.append(human_body)

    def create_navigation_goals(self):
        """Create navigation goal markers"""
        for i, goal_pos in enumerate(self.navigation_goals):
            goal_marker = create_primitive(
                prim_path=f"/World/Goals/Goal{i}",
                primitive_type="Cylinder",
                position=np.array([goal_pos[0], goal_pos[1], 0.1]),  # Slightly above ground
                scale=np.array([0.2, 0.2, 0.2]),
                color=np.array([0.2, 0.8, 0.2])  # Green goal markers
            )

    def setup_lighting(self):
        """Set up lighting for the scene"""
        stage = omni.usd.get_context().get_stage()

        # Create dome light for ambient lighting
        dome_light = UsdLux.DomeLight.Define(stage, Sdf.Path("/World/DomeLight"))
        dome_light.CreateIntensityAttr(3000)
        dome_light.CreateColorAttr(Gf.Vec3f(0.9, 0.9, 0.9))

        # Create key light
        key_light = UsdLux.DistantLight.Define(stage, Sdf.Path("/World/KeyLight"))
        key_light.CreateIntensityAttr(1500)
        key_light.CreateColorAttr(Gf.Vec3f(1.0, 0.95, 0.9))
        # Set rotation to illuminate the scene well
        xform = UsdGeom.Xformable(key_light)
        xform.AddRotateXYZOp().Set(Gf.Vec3f(-30, 45, 0))

    def setup_sensors(self):
        """Set up sensors for the humanoid robot"""
        # This would set up cameras, IMU, etc. for the robot
        # For now, we'll just note that sensors would be configured here
        self.get_logger().info("Setting up robot sensors...")

    def create_social_navigation_scenarios(self):
        """Create scenarios for testing social navigation"""
        # Scenario 1: Human walking across robot's path
        scenario1 = {
            'type': 'crossing',
            'human_path': [[-3, 0, 0], [3, 0, 0]],
            'start_time': 0.0,
            'duration': 10.0
        }

        # Scenario 2: Human approaching robot head-on
        scenario2 = {
            'type': 'approach',
            'human_path': [[2, 2, 0], [-2, -2, 0]],
            'start_time': 5.0,
            'duration': 8.0
        }

        # Scenario 3: Human walking parallel to robot
        scenario3 = {
            'type': 'parallel',
            'human_path': [[-2, 1, 0], [2, 1, 0]],
            'start_time': 2.0,
            'duration': 12.0
        }

        self.social_scenarios = [scenario1, scenario2, scenario3]

    def setup_camera_views(self):
        """Set up camera views for monitoring navigation"""
        # Overhead camera for monitoring navigation
        self.setup_overhead_camera()

        # Robot perspective camera
        self.setup_robot_camera()

    def setup_overhead_camera(self):
        """Set up an overhead camera for monitoring"""
        # This would create an overhead camera view
        # Implementation would depend on Isaac Sim camera setup
        pass

    def setup_robot_camera(self):
        """Set up robot's perspective camera"""
        # This would attach a camera to the robot
        # Implementation would depend on robot model and camera requirements
        pass

    def get_scene_summary(self):
        """Get summary of created scene"""
        summary = {
            'scene_dimensions': self.room_dimensions,
            'robot_count': 1,
            'human_count': len(self.humans),
            'obstacle_count': len(self.obstacles),
            'navigation_goals': len(self.navigation_goals),
            'total_objects': 1 + len(self.humans) + len(self.obstacles) + len(self.navigation_goals)
        }
        return summary

    def print_scene_info(self):
        """Print information about the created scene"""
        summary = self.get_scene_summary()

        print("\n=== Humanoid Navigation Scene Created ===")
        print(f"Room dimensions: {summary['scene_dimensions']} meters")
        print(f"Robot: 1 humanoid robot")
        print(f"Humans: {summary['human_count']} agents")
        print(f"Obstacles: {summary['obstacle_count']} static obstacles")
        print(f"Navigation goals: {summary['navigation_goals']} locations")
        print(f"Total objects: {summary['total_objects']}")
        print("========================================\n")

    def run_scenario(self):
        """Run the navigation scenario"""
        self.get_logger().info("Starting humanoid navigation scenario...")

        # Print scene information
        self.print_scene_info()

        # Main simulation loop
        while simulation_app.is_running():
            # Step the world
            self.world.step(render=True)

            # Check for simulation events or user input
            if self.world.is_playing():
                # Add scenario-specific logic here
                # For example: move humans along predefined paths
                # or trigger navigation tasks
                pass

            # Check for exit condition
            if carb.input.get_keyboard().is_pressed(carb.input.KeyboardInput.ESCAPE):
                break

    def destroy(self):
        """Clean up the scene"""
        super().destroy()


# Main execution
def main():
    # Initialize the simulation application
    global simulation_app
    simulation_app = SimulationApp({"headless": False})

    print("[INFO] Starting Humanoid Navigation Scene Example")

    # Create and run the sample
    sample = HumanoidNavigationScene()

    # Run the setup
    sample.setup_scene()

    # Run the scenario
    sample.run_scenario()

    # Clean up
    sample.destroy()
    simulation_app.close()


if __name__ == "__main__":
    main()