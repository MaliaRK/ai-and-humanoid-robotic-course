// Minimal docusaurus.config.js for module 3
// @ts-check

const lightCodeTheme = require('@docusaurus/theme-classic').themes.prism.light;
const darkCodeTheme = require('@docusaurus/theme-classic').themes.prism.dark;

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Module 3: The AI-Robot Brain (NVIDIA Isaac™)',
  tagline: 'Advanced perception, VSLAM, navigation, synthetic data, and AI-driven control',
  favicon: 'img/favicon.ico',

  // Set the production url of your site here
  url: 'https://your-organization.github.io',
  // Set the /<base>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<org-name>/<repo-name>/'
  baseUrl: '/ai-and-humanoid-robotics-course/',

  // GitHub pages deployment config.
  organizationName: 'your-organization', // Usually your GitHub org/user name.
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
            'https://github.com/your-organization/your-repo/edit/main/module3-isaac-integration/docs/',
        },
        blog: false, // Optional: disable the blog plugin
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
        title: 'AI & Humanoid Robotics Course',
        logo: {
          alt: 'Course Logo',
          src: 'img/logo.svg',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'module3Sidebar',
            position: 'left',
            label: 'Module 3 Docs',
          },
          {
            href: 'https://github.com/your-organization/your-repo',
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
                label: 'Module 3 Introduction',
                to: '/docs/category/introduction',
              },
            ],
          },
          {
            title: 'Community',
            items: [
              {
                label: 'Stack Overflow',
                href: 'https://stackoverflow.com/questions/tagged/isaac-sim',
              },
              {
                label: 'Robotics Stack Exchange',
                href: 'https://robotics.stackexchange.com/',
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
        copyright: `Copyright © ${new Date().getFullYear()} AI & Humanoid Robotics Course. Built with Docusaurus.`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
      },
    }),
};

module.exports = config;