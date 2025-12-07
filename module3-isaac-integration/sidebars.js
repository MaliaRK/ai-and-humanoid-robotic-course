// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  module3Sidebar: [
    {
      type: 'category',
      label: 'Introduction',
      items: [
        'chapter1-intro/ai-role-in-humanoid-robotics',
        'chapter1-intro/isaac-ecosystem-overview',
        'chapter1-intro/perception-planning-control-pipeline'
      ],
      link: {
        type: 'generated-index',
        title: 'Introduction to AI-Robot Brain',
        description: 'Learn about the role of AI in humanoid robotics and the Isaac ecosystem',
        slug: '/category/introduction',
      },
    },
    {
      type: 'category',
      label: 'Isaac Sim',
      items: [
        'chapter2-simulation/photorealistic-simulation',
        'chapter2-simulation/omniverse-kit-usd',
        'chapter2-simulation/synthetic-data-generation',
        'chapter2-simulation/domain-randomization',
        'chapter2-simulation/ros2-bridge'
      ],
      link: {
        type: 'generated-index',
        title: 'NVIDIA Isaac Sim',
        description: 'Master photorealistic simulation with Isaac Sim',
        slug: '/category/isaac-sim',
      },
    },
    {
      type: 'category',
      label: 'Perception & VSLAM',
      items: [
        'chapter3-perception/isaac-ros-gems',
        'chapter3-perception/vslam-fundamentals',
        'chapter3-perception/gpu-acceleration',
        'chapter3-perception/ros2-integration',
        'chapter3-perception/vslam-pipeline-humanoids'
      ],
      link: {
        type: 'generated-index',
        title: 'Perception & VSLAM',
        description: 'Implement Visual SLAM with Isaac ROS',
        slug: '/category/perception',
      },
    },
    {
      type: 'category',
      label: 'Navigation with Nav2',
      items: [
        'chapter4-navigation/nav2-architecture',
        'chapter4-navigation/mapping-localization',
        'chapter4-navigation/global-local-planners',
        'chapter4-navigation/biped-controllers',
        'chapter4-navigation/vslam-nav2-integration'
      ],
      link: {
        type: 'generated-index',
        title: 'Navigation with Nav2',
        description: 'Configure Nav2 for humanoid robot navigation',
        slug: '/category/navigation',
      },
    },
    {
      type: 'category',
      label: 'AI Training & Behaviors',
      items: [
        'chapter5-ai/reinforcement-learning',
        'chapter5-ai/behavior-trees',
        'chapter5-ai/humanoid-locomotion-training',
        'chapter5-ai/sim-to-real-transfer',
        'chapter5-ai/case-study'
      ],
      link: {
        type: 'generated-index',
        title: 'AI Training & Behaviors',
        description: 'Implement AI behaviors and training systems',
        slug: '/category/ai-behaviors',
      },
    },
  ],
};

module.exports = sidebars;