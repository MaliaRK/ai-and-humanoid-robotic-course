// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  module1Sidebar: [
    {
      type: 'category',
      label: 'Module 1 – The Robotic Nervous System (ROS 2)',
      items: [
        'chapter1-foundations',
        'chapter2-nodes-topics-services',
        'chapter3-rclpy',
        'chapter4-urdf',
        'chapter5-middleware-in-action',
      ],
    },
  ],
};

module.exports = sidebars;