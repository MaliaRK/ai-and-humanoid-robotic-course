import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 * - create an ordered group of docs
 * - render a sidebar for each doc of that group
 * - provide next/previous navigation
 *
 * The sidebars can be generated from the filesystem, or explicitly defined here.
 *
 * Create as many sidebars as you want.
 */
const sidebars: SidebarsConfig = {
  // Manual sidebar definition for Module 2
  tutorialSidebar: [
    {
      type: 'category',
      label: 'Module 2: The Digital Twin (Gazebo & Unity)',
      items: [
        'intro',
        {
          type: 'category',
          label: 'Chapter 1: Digital Twin Fundamentals',
          items: [
            'chapter1-intro/digital-twins-fundamentals',
          ],
        },
        {
          type: 'category',
          label: 'Chapter 2: Gazebo Simulation',
          items: [
            'chapter2-gazebo/gazebo-setup',
            'chapter2-gazebo/physics-engines',
            'chapter2-gazebo/environment-creation',
            'chapter2-gazebo/ros-bridge',
          ],
        },
        {
          type: 'category',
          label: 'Chapter 3: Unity Visualization',
          items: [
            'chapter3-unity/unity-setup',
            'chapter3-unity/rendering-pipelines',
            'chapter3-unity/robot-importing',
            'chapter3-unity/hri-simulation',
          ],
        },
        {
          type: 'category',
          label: 'Chapter 4: Sensor Simulation',
          items: [
            'chapter4-sensors/lidar-simulation',
            'chapter4-sensors/depth-cameras',
            'chapter4-sensors/rgb-cameras',
            'chapter4-sensors/imu-simulation',
            'chapter4-sensors/ros-data-streams',
          ],
        },
        {
          type: 'category',
          label: 'Chapter 5: Validation & Reality Gap',
          items: [
            'chapter5-validation/sim-to-real-gap',
            'chapter5-validation/noise-models',
            'chapter5-validation/behavioral-testing',
            'chapter5-validation/benchmarking',
            'chapter5-validation/case-study',
          ],
        },
      ],
    },
  ],
};

export default sidebars;