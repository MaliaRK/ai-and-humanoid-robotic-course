#!/bin/bash

# Script to run Docusaurus build process for the digital twin documentation

set -e  # Exit on any error

echo "Starting Docusaurus build process for Digital Twin documentation..."

# Define project directory
PROJECT_DIR="/home/maliaraees/ai-and-humanoid-robotics-course/module2-digital-twin"

# Navigate to the project directory
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Error: Project directory does not exist: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "No package.json found. Creating basic Docusaurus setup..."

    # Initialize npm project if needed
    if [ ! -f "package.json" ]; then
        npm init -y
    fi

    # Install Docusaurus and related packages
    echo "Installing Docusaurus and dependencies..."
    npm install @docusaurus/core@latest @docusaurus/preset-classic@latest @mdx-js/react@latest clsx@latest prism-react-renderer@latest
fi

# Create or update docusaurus.config.js if it doesn't exist
if [ ! -f "docusaurus.config.js" ]; then
    echo "Creating Docusaurus configuration file..."
    cat > docusaurus.config.js << 'EOF'
// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const lightCodeTheme = require('prism-react-renderer/themes/github');
const darkCodeTheme = require('prism-react-renderer/themes/dracula');

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'AI & Humanoid Robotics Course',
  tagline: 'Digital Twin Development for Humanoid Robotics Simulation',
  favicon: 'img/favicon.ico',

  // Set the production url of your site here
  url: 'https://your-website-domain.com',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: '/ai-humanoid-robotics/',

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: 'maliaraees', // Usually your GitHub org/user name.
  projectName: 'ai-and-humanoid-robotics-course', // Usually your repo name.

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internalization, you can use this field to set useful
  // metadata like html lang. For example, if your site is Chinese, you may want
  // to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          editUrl:
            'https://github.com/maliaraees/ai-and-humanoid-robotics-course/tree/main/packages/create-docusaurus/templates/shared/',
        },
        blog: false, // Disable blog if not needed
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // Replace with your project's social card
      image: 'img/docusaurus-social-card.jpg',
      navbar: {
        title: 'AI & Humanoid Robotics',
        logo: {
          alt: 'Robot Logo',
          src: 'img/robot-icon.svg',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'tutorialSidebar',
            position: 'left',
            label: 'Docs',
          },
          {
            href: 'https://github.com/maliaraees/ai-and-humanoid-robotics-course',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Docs',
            items: [
              {
                label: 'Course Overview',
                to: '/docs/intro',
              },
            ],
          },
          {
            title: 'Community',
            items: [
              {
                label: 'Stack Overflow',
                href: 'https://stackoverflow.com/questions/tagged/docusaurus',
              },
              {
                label: 'Discord',
                href: 'https://discordapp.com/invite/docusaurus',
              },
            ],
          },
          {
            title: 'More',
            items: [
              {
                label: 'GitHub',
                href: 'https://github.com/facebook/docusaurus',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} My Project, Inc. Built with Docusaurus.`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
      },
    }),
};

module.exports = config;
EOF
fi

# Create or update sidebars.js if it doesn't exist
if [ ! -f "sidebars.js" ]; then
    echo "Creating sidebars configuration..."
    cat > sidebars.js << 'EOF'
// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  tutorialSidebar: [
    'intro',
    {
      type: 'category',
      label: 'Chapter 1: Digital Twins Fundamentals',
      items: ['chapter1-intro/digital-twins-fundamentals'],
    },
    {
      type: 'category',
      label: 'Chapter 2: Gazebo Simulation',
      items: [
        'chapter2-gazebo/gazebo-setup',
        'chapter2-gazebo/physics-engines',
        'chapter2-gazebo/environment-creation',
        'chapter2-gazebo/ros-bridge'
      ],
    },
    {
      type: 'category',
      label: 'Chapter 3: Unity Visualization',
      items: [
        'chapter3-unity/unity-setup',
        'chapter3-unity/rendering-pipelines',
        'chapter3-unity/robot-importing',
        'chapter3-unity/hri-simulation'
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
        'chapter4-sensors/ros-data-streams'
      ],
    },
    {
      type: 'category',
      label: 'Chapter 5: Validation',
      items: [
        'chapter5-validation/sim-to-real-gap',
        'chapter5-validation/noise-models',
        'chapter5-validation/behavioral-testing',
        'chapter5-validation/benchmarking',
        'chapter5-validation/case-study'
      ],
    },
  ],
};

module.exports = sidebars;
EOF
fi

# Create basic src directory structure if it doesn't exist
mkdir -p src/css
if [ ! -f "src/css/custom.css" ]; then
    echo "Creating custom CSS file..."
    cat > src/css/custom.css << 'EOF'
/**
 * Copyright (c) 2017-present, Facebook, Inc.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

/**
 * Any CSS included here will be global. The classic template
 * bundles Infima by default. Infima is a CSS framework designed to
 * work well for content-centric websites.
 */

/* You can override the default Infima variables here. */
:root {
  --ifm-color-primary: #2e8555;
  --ifm-color-primary-dark: #29784c;
  --ifm-color-primary-darker: #277148;
  --ifm-color-primary-darkest: #205d3b;
  --ifm-color-primary-light: #33925d;
  --ifm-color-primary-lighter: #359962;
  --ifm-color-primary-lightest: #3cad6e;
  --ifm-code-font-size: 95%;
}

/* For readability concerns, you should choose a lighter palette in dark mode. */
[data-theme='dark'] {
  --ifm-color-primary: #25c2a0;
  --ifm-color-primary-dark: #21af90;
  --ifm-color-primary-darker: #1fa588;
  --ifm-color-primary-darkest: #1a8870;
  --ifm-color-primary-light: #29d5b0;
  --ifm-color-primary-lighter: #32d8b4;
  --ifm-color-primary-lightest: #4fddbf;
}
EOF
fi

# Create static directory and basic assets if needed
mkdir -p static/img

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing NPM dependencies..."
    npm install
fi

# Run the Docusaurus build
echo "Running Docusaurus build..."
npm run build

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "Docusaurus build completed successfully!"
    echo "Build output is in the build/ directory"

    # Show the size of the build
    if [ -d "build" ]; then
        echo "Build size:"
        du -sh build/
    fi

    exit 0
else
    echo "Docusaurus build failed!"
    exit 1
fi